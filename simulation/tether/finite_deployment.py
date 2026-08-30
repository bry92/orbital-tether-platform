"""Finite-time, radially constrained tether deployment (v0.2)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simulation.orbital.state import SpacecraftState
from simulation.tether.mass_map import MassMap, compute_mass_map
from simulation.tether.reel import ReelSchedule
from simulation.tether.tension import TensionEstimate, estimate_tension

FINITE_DEPLOYMENT_ASSUMPTION_IDS = ("A-006", "A-012", "A-013", "A-014", "A-015", "A-016")


@dataclass(frozen=True, slots=True)
class FiniteDeploymentSample:
    """One kinematic deployment sample in the ECI frame."""

    time_s: float
    cm_state: SpacecraftState
    mass_map: MassMap
    upper_position_m: np.ndarray
    upper_velocity_m_s: np.ndarray
    lower_position_m: np.ndarray
    lower_velocity_m_s: np.ndarray
    tether_position_m: np.ndarray
    tether_velocity_m_s: np.ndarray
    tension: TensionEstimate
    angular_momentum_kg_m2_s: np.ndarray

    def as_dict(self) -> dict:
        return {
            "time_s": self.time_s,
            "cm_state": self.cm_state.as_dict(),
            "mass_map": self.mass_map.as_dict(),
            "upper": {"position_m": self.upper_position_m.tolist(), "velocity_m_s": self.upper_velocity_m_s.tolist()},
            "lower": {"position_m": self.lower_position_m.tolist(), "velocity_m_s": self.lower_velocity_m_s.tolist()},
            "tether_midpoint": {"position_m": self.tether_position_m.tolist(), "velocity_m_s": self.tether_velocity_m_s.tolist()},
            "tension": self.tension.as_dict(),
            "angular_momentum_kg_m2_s": self.angular_momentum_kg_m2_s.tolist(),
        }


@dataclass(frozen=True, slots=True)
class FiniteDeploymentResult:
    """Complete prescribed-length v0.2 deployment trajectory."""

    schedule: ReelSchedule
    samples: tuple[FiniteDeploymentSample, ...]
    assumption_ids: tuple[str, ...] = FINITE_DEPLOYMENT_ASSUMPTION_IDS

    def as_dict(self) -> dict:
        return {
            "schedule": self.schedule.as_dict(),
            "assumption_ids": list(self.assumption_ids),
            "samples": [sample.as_dict() for sample in self.samples],
            "summary": {
                "sample_count": len(self.samples),
                "final_length_m": self.samples[-1].mass_map.length_m,
                "max_dynamic_upper_tension_n": max(s.tension.dynamic_upper_n for s in self.samples),
                "min_dynamic_upper_tension_n": min(s.tension.dynamic_upper_n for s in self.samples),
                "slack_warning": any(s.tension.slack_warning for s in self.samples),
                "final_angular_momentum_relative_residual": float(
                    np.linalg.norm(self.samples[-1].angular_momentum_kg_m2_s - self.samples[0].angular_momentum_kg_m2_s)
                    / np.linalg.norm(self.samples[0].angular_momentum_kg_m2_s)
                ),
            },
        }


def _circular_cm_state(initial: SpacecraftState, time_s: float, mean_motion_rad_s: float) -> SpacecraftState:
    angle = mean_motion_rad_s * time_s
    c, s = np.cos(angle), np.sin(angle)
    rotation = np.array(((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0)))
    return SpacecraftState(rotation @ initial.position_m, rotation @ initial.velocity_m_s, initial.mass_kg)


def _time_grid(schedule: ReelSchedule, sample_step_s: float) -> np.ndarray:
    if sample_step_s <= 0.0:
        raise ValueError("sample_step_s must be positive")
    count = max(2, int(np.ceil(schedule.total_duration_s / sample_step_s)) + 1)
    return np.linspace(0.0, schedule.total_duration_s, count)


def simulate_finite_deployment(
    *,
    initial_cm_state: SpacecraftState,
    schedule: ReelSchedule,
    upper_mass_fraction: float,
    linear_density_kg_m: float,
    mu_m3_s2: float,
    sample_step_s: float,
) -> FiniteDeploymentResult:
    """Evaluate the v0.2 prescribed radial deployment at a deterministic time grid."""
    schedule.validate()
    if not 0.0 < upper_mass_fraction < 1.0:
        raise ValueError("upper_mass_fraction must be in (0, 1)")
    if linear_density_kg_m < 0.0 or mu_m3_s2 <= 0.0:
        raise ValueError("linear_density_kg_m must be non-negative and mu_m3_s2 positive")

    radius = initial_cm_state.radius_m
    speed = initial_cm_state.speed_m_s
    if not np.isclose(speed**2, mu_m3_s2 / radius, rtol=1e-9):
        raise ValueError("initial_cm_state must be circular for the v0.2 analytic CM path")
    n = float(np.sqrt(mu_m3_s2 / radius**3))
    total_mass = initial_cm_state.mass_kg
    end_mass_total = total_mass - linear_density_kg_m * schedule.final_length_m
    if end_mass_total <= 0.0:
        raise ValueError("linear tether mass leaves no positive end-mass total")
    # The fraction partitions end masses only; tether mass is additional to neither endpoint.
    upper_mass = end_mass_total * upper_mass_fraction
    lower_mass = end_mass_total * (1.0 - upper_mass_fraction)

    samples: list[FiniteDeploymentSample] = []
    for time_s in _time_grid(schedule, sample_step_s):
        length = schedule.length_m(float(time_s))
        mass_map = compute_mass_map(
            length_m=length,
            length_rate_m_s=schedule.rate_m_s(float(time_s)),
            length_acc_m_s2=schedule.acceleration_m_s2(float(time_s)),
            upper_mass_kg=upper_mass,
            lower_mass_kg=lower_mass,
            linear_density_kg_m=linear_density_kg_m,
            final_length_m=schedule.final_length_m,
        )
        cm = _circular_cm_state(initial_cm_state, float(time_s), n)
        r_hat = cm.position_m / cm.radius_m
        omega = np.cross(cm.position_m, cm.velocity_m_s) / cm.radius_m**2
        offsets = ((mass_map.s_upper_m, mass_map.s_upper_dot_m_s), (-mass_map.s_lower_m, -mass_map.s_lower_dot_m_s), (mass_map.s_tether_m, mass_map.s_tether_dot_m_s))
        states = []
        for offset, offset_rate in offsets:
            position = cm.position_m + offset * r_hat
            velocity = cm.velocity_m_s + np.cross(omega, offset * r_hat) + offset_rate * r_hat
            states.append((position, velocity))
        (r_u, v_u), (r_l, v_l), (r_t, v_t) = states
        tension = estimate_tension(mu_m3_s2=mu_m3_s2, r_cm_m=cm.position_m, v_cm_m_s=cm.velocity_m_s, mass_map=mass_map, n_rad_s=n)
        h = upper_mass * np.cross(r_u, v_u) + mass_map.lower_effective_mass_kg * np.cross(r_l, v_l) + mass_map.tether_deployed_mass_kg * np.cross(r_t, v_t)
        samples.append(FiniteDeploymentSample(float(time_s), cm, mass_map, r_u, v_u, r_l, v_l, r_t, v_t, tension, h))
    return FiniteDeploymentResult(schedule=schedule, samples=tuple(samples))
