"""Scenario runner: orbital init → tether deploy → verify → record."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from control.autonomy.decision import DecisionEngine
from control.autonomy.mission import MissionPhase, MissionPlan
from control.autonomy.telemetry import TelemetryBuffer, TelemetryFrame
from control.faults.handler import FaultHandler
from simulation.orbital.constants import DEFAULT_ASSUMPTION_IDS, EarthModel
from simulation.orbital.kepler import angular_momentum, orbital_period, specific_energy
from simulation.orbital.propagate import propagate_two_body
from simulation.orbital.state import circular_equatorial_state
from simulation.scenarios.config import DeploymentScenarioConfig
from simulation.tether.deployment import deploy_radial_tether
from simulation.tether.system import diagnostic_tip_orbit
from verification.checks import run_deployment_checks
from verification.records import ExperimentRecord, build_experiment_record
from verification.reports import write_experiment_report


LIMITATIONS = [
    "Two-body gravity only (A-001); no J2, drag, or third-body forces.",
    "Deployment is instantaneous and quasi-static (A-003); not a reel dynamics model.",
    "Tether is massless and rigid (A-004).",
    "Default tip velocities use inheritance v_tip=v_cm (A-011); no reel-out relative velocity profile.",
    "Gravity-gradient co-rotation (A-005) is diagnostic-only and does not conserve H about Earth.",
    "No libration / skip-rope dynamics.",
    "Tip Keplerian elements are diagnostic only (A-007).",
    "Control layer is stubbed; no closed-loop autonomy.",
]

EXPERT_REVIEW_FLAGS = [
    "EXPERT_REVIEW: Do not use tip free-orbit SMA/altitude deltas for mission design without independent dynamics review (A-003, A-007, A-011).",
    "EXPERT_REVIEW: Tension, flexibility, and deployment failure modes are not modeled.",
    "EXPERT_REVIEW: No collision/debris or regulatory analysis is included.",
]


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    config: DeploymentScenarioConfig
    record: ExperimentRecord
    report_paths: dict[str, Path]
    validation_passed: bool
    decision_log: dict[str, Any]


def run_deployment_scenario(
    config: DeploymentScenarioConfig | None = None,
    *,
    output_dir: str | Path | None = None,
) -> ScenarioResult:
    """Execute the v0.1 deployment scenario and write verification evidence."""
    config = config or DeploymentScenarioConfig()
    config.validate()

    earth = EarthModel(mu_m3_s2=config.earth_mu_m3_s2, radius_m=config.earth_radius_m)
    earth.validate()

    plan = MissionPlan(
        plan_id=f"{config.scenario_id}-plan",
        phases=(
            MissionPhase.ON_ORBIT_IDLE,
            MissionPhase.TETHER_DEPLOY,
            MissionPhase.MONITOR,
        ),
        notes="v0.1 simulated sequence only",
    )

    decisions = DecisionEngine()
    faults = FaultHandler(decisions)
    telemetry = TelemetryBuffer()

    pre = circular_equatorial_state(
        altitude_m=config.orbit_altitude_m,
        mass_kg=config.spacecraft_mass_kg,
        earth=earth,
    )

    if config.propagate_seconds > 0.0:
        prop = propagate_two_body(pre, config.propagate_seconds, earth.mu_m3_s2)
        pre = prop.final_state

    decisions.recommend(
        trigger="scenario_start",
        action="initialize_circular_orbit",
        rationale="Begin deployment scenario from Keplerian circular state",
    )

    system = deploy_radial_tether(
        cm_state=pre,
        tether_length_m=config.tether_length_m,
        upper_mass_fraction=config.upper_mass_fraction,
    )

    decisions.recommend(
        trigger="tether_deploy_event",
        action="apply_quasi_static_radial_deployment",
        rationale="A-003 event model; not a dynamic reel simulation",
    )

    upper_diag = diagnostic_tip_orbit(system.upper, earth)
    lower_diag = diagnostic_tip_orbit(system.lower, earth)

    telemetry.ingest(
        TelemetryFrame(0.0, "tether_length_m", system.length_m, "m")
    )
    telemetry.ingest(
        TelemetryFrame(0.0, "upper_altitude_m", upper_diag.altitude_m, "m")
    )
    telemetry.ingest(
        TelemetryFrame(0.0, "lower_altitude_m", lower_diag.altitude_m, "m")
    )

    if lower_diag.altitude_m < config.min_lower_tip_altitude_m:
        faults.handle("LOWER_TIP_ALTITUDE_LOW")

    validation = run_deployment_checks(pre, system)
    if not validation.all_passed:
        for check in validation.checks:
            if not check.passed:
                if check.name == "tether_length":
                    faults.handle("TETHER_LENGTH_INCONSISTENT")
                elif check.name == "angular_momentum_about_earth":
                    faults.handle("ANGULAR_MOMENTUM_RESIDUAL")

    pre_energy = specific_energy(pre.position_m, pre.velocity_m_s, earth.mu_m3_s2)
    pre_h = angular_momentum(pre.position_m, pre.velocity_m_s)

    assumption_ids = sorted(set(DEFAULT_ASSUMPTION_IDS) | set(system.assumption_ids) | {"A-009", "A-010"})

    outputs = {
        "mission_plan": plan.as_dict(),
        "pre_deployment": {
            **pre.as_dict(),
            "specific_energy_j_kg": pre_energy,
            "specific_angular_momentum_m2_s": pre_h.tolist(),
            "orbital_period_s": orbital_period(pre.radius_m, earth.mu_m3_s2),
        },
        "deployed_system": system.as_dict(),
        "tip_diagnostics_free_orbit_if_cut": {
            "upper": upper_diag.as_dict(),
            "lower": lower_diag.as_dict(),
        },
        "altitude_deltas_m": {
            "upper_minus_cm": upper_diag.altitude_m - config.orbit_altitude_m,
            "lower_minus_cm": lower_diag.altitude_m - config.orbit_altitude_m,
            "note": (
                "Geometric altitude offsets of tips relative to pre-deploy CM altitude; "
                "not a validated mission Δh product."
            ),
        },
        "telemetry_snapshot": telemetry.as_dict(),
        "decision_log": decisions.log.as_dict(),
        "numeric_notes": {
            "velocity_model": system.velocity_model.value,
            "angular_momentum_note": system.angular_momentum_note,
            "omega_orbital_mag_rad_s": float(np.linalg.norm(system.omega_orbital_rad_s)),
            "mean_motion_circular_rad_s": float(
                np.sqrt(earth.mu_m3_s2 / pre.radius_m**3)
            ),
        },
    }

    record = build_experiment_record(
        scenario_id=config.scenario_id,
        parameters=config.as_dict(),
        assumption_ids=assumption_ids,
        outputs=outputs,
        validation=validation.as_dict(),
        limitations=LIMITATIONS,
        expert_review_flags=EXPERT_REVIEW_FLAGS,
    )

    out_dir = Path(output_dir) if output_dir else Path("data/experiments")
    paths = write_experiment_report(record, out_dir)

    return ScenarioResult(
        config=config,
        record=record,
        report_paths=paths,
        validation_passed=validation.all_passed,
        decision_log=decisions.log.as_dict(),
    )
