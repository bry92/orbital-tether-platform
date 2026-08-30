"""Scenario orchestration and evidence writing for v0.2 finite deployment."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from simulation.orbital.constants import DEFAULT_ASSUMPTION_IDS, EarthModel
from simulation.orbital.state import circular_equatorial_state
from simulation.scenarios.config import FiniteDeploymentScenarioConfig
from simulation.tether.finite_deployment import simulate_finite_deployment
from simulation.tether.reel import ReelSchedule
from verification.checks import run_finite_deployment_checks
from verification.records import ExperimentRecord, build_experiment_record
from verification.reports import write_experiment_report


@dataclass(frozen=True, slots=True)
class FiniteScenarioResult:
    config: FiniteDeploymentScenarioConfig
    record: ExperimentRecord
    validation_passed: bool
    report_paths: dict[str, Path]


def run_finite_deployment_scenario(config: FiniteDeploymentScenarioConfig | None = None, *, output_dir: str | Path | None = None) -> FiniteScenarioResult:
    """Run the v0.2 prescribed finite-time radial deployment pipeline."""
    config = config or FiniteDeploymentScenarioConfig()
    config.validate()
    earth = EarthModel(config.earth_mu_m3_s2, config.earth_radius_m)
    initial = circular_equatorial_state(config.orbit_altitude_m, config.spacecraft_mass_kg, earth)
    schedule = ReelSchedule(config.final_length_m, config.reel_rate_m_s, config.initial_length_m, config.coast_after_deploy_s)
    trajectory = simulate_finite_deployment(initial_cm_state=initial, schedule=schedule, upper_mass_fraction=config.upper_mass_fraction, linear_density_kg_m=config.linear_density_kg_m, mu_m3_s2=earth.mu_m3_s2, sample_step_s=config.sample_step_s)
    validation = run_finite_deployment_checks(trajectory)
    record = build_experiment_record(
        scenario_id=config.scenario_id,
        parameters=config.as_dict(),
        assumption_ids=sorted(set(DEFAULT_ASSUMPTION_IDS) | set(trajectory.assumption_ids)),
        outputs={"finite_deployment": trajectory.as_dict()},
        validation=validation.as_dict(),
        limitations=["Prescribed radial kinematics; no libration, elasticity, drag, or electrodynamics.", "Tension is a scalar engineering estimate, not a structural allowable or flight load case."],
        expert_review_flags=["AEROSPACE EXPERT REVIEW REQUIRED before using tension or tip histories for mechanism sizing, timelines, or safety thresholds."],
    )
    paths = write_experiment_report(record, Path(output_dir) if output_dir else Path("data/experiments"))
    return FiniteScenarioResult(config, record, validation.all_passed, paths)
