"""Finite-time radial tether deployment with time-series trajectory.

Design spec: v0.2_design_spec.md §11 (numerical method).
Assumptions: A-003 (superseded), A-012, A-013, A-014, A-015, A-016.

Prescribed-length radial deployment: no ODE solver required.
Time-stepping from initial to final length via scheduled reel rate.
Outputs: deterministic time-series trajectory with conservation residuals.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simulation.orbital.constants import EarthModel
from simulation.orbital.kepler import angular_momentum
from simulation.orbital.state import SpacecraftState
from simulation.tether.mass_map import MassMap, compute_mass_map
from simulation.tether.reel import ReelSchedule
from simulation.tether.tension import estimate_tension


@dataclass(frozen=True, slots=True)
class FiniteDeploymentSample:
    """One snapshot of the deployment trajectory."""

    time_s: float
    length_m: float
    reel_rate_m_s: float
    mass_map: MassMap
    upper_position_m: np.ndarray
    upper_velocity_m_s: np.ndarray
    lower_position_m: np.ndarray
    lower_velocity_m_s: np.ndarray
    tether_position_m: np.ndarray
    tether_velocity_m_s: np.ndarray
    tension_static_n: float
    tension_dynamic_upper_n: float
    tension_dynamic_lower_n: float
    angular_momentum_m2_s: np.ndarray
    angular_momentum_residual_mag_m2_s: float
    cm_radius_drift_m: float

    def as_dict(self) -> dict:
        return {
            "time_s": self.time_s,
            "length_m": self.length_m,
            "reel_rate_m_s": self.reel_rate_m_s,
            "mass_map": self.mass_map.as_dict(),
            "upper_position_m": self.upper_position_m.tolist(),
            "upper_velocity_m_s": self.upper_velocity_m_s.tolist(),
            "lower_position_m": self.lower_position_m.tolist(),
            "lower_velocity_m_s": self.lower_velocity_m_s.tolist(),
            "tether_position_m": self.tether_position_m.tolist(),
            "tether_velocity_m_s": self.tether_velocity_m_s.tolist(),
            "tension_static_n": self.tension_static_n,
            "tension_dynamic_upper_n": self.tension_dynamic_upper_n,
            "tension_dynamic_lower_n": self.tension_dynamic_lower_n,
            "angular_momentum_m2_s": self.angular_momentum_m2_s.tolist(),
            "angular_momentum_residual_mag_m2_s": self.angular_momentum_residual_mag_m2_s,
            "cm_radius_drift_m": self.cm_radius_drift_m,
        }


@dataclass(frozen=True, slots=True)
class FiniteDeploymentTrajectory:
    """Complete time-series trajectory of finite-time deployment."""

    samples: tuple[FiniteDeploymentSample, ...]
    final_length_m: float
    total_duration_s: float
    initial_angular_momentum_m2_s: np.ndarray
    max_angular_momentum_residual_m2_s: float
    max_cm_radius_drift_m: float

    def as_dict(self) -> dict:
        return {
            "final_length_m": self.final_length_m,
            "total_duration_s": self.total_duration_s,
            "num_samples": len(self.samples),
            "initial_angular_momentum_m2_s": self.initial_angular_momentum_m2_s.tolist(),
            "max_angular_momentum_residual_m2_s": self.max_angular_momentum_residual_m2_s,
            "max_cm_radius_drift_m": self.max_cm_radius_drift_m,
            "samples": [s.as_dict() for s in self.samples],
        }


def _circular_orbit_state(
    t_s: float,
    cm_state_initial: SpacecraftState,
    earth: EarthModel,
) -> tuple[np.ndarray, np.ndarray]:
    """Analytic circular CM state at time t (A-015).

    Returns position and velocity vectors in ECI.
    """
    r_cm = cm_state_initial.position_m
    v_cm = cm_state_initial.velocity_m_s
    radius = float(np.linalg.norm(r_cm))

    # Orbital angular velocity
    omega = np.cross(r_cm, v_cm) / (radius**2)
    omega_mag = float(np.linalg.norm(omega))

    if omega_mag <= 0.0:
        raise ValueError("CM not in circular orbit (zero angular velocity)")

    # Rotation angle at time t
    theta = omega_mag * t_s

    # Initial angle (assume starts at (r, 0, 0) per initialization)
    # For general case: extract angle from initial position
    theta_0 = float(np.arctan2(r_cm[1], r_cm[0]))
    theta_total = theta_0 + theta

    # Positions and velocity in equatorial plane
    cos_theta = float(np.cos(theta_total))
    sin_theta = float(np.sin(theta_total))

    r_cm_t = radius * np.array([cos_theta, sin_theta, 0.0], dtype=float)
    v_cm_t = (omega_mag * radius) * np.array([-sin_theta, cos_theta, 0.0], dtype=float)

    return r_cm_t, v_cm_t


def finite_deployment(
    cm_state_initial: SpacecraftState,
    reel_schedule: ReelSchedule,
    upper_mass_kg: float,
    lower_mass_kg: float,
    linear_density_kg_m: float,
    earth: EarthModel | None = None,
    *,
    num_samples: int = 100,
    h_residual_rel_tol: float = 1e-8,
    h_residual_abs_tol: float = 1e-6,
    cm_radius_drift_abs_tol: float = 1e-9,
) -> FiniteDeploymentTrajectory:
    """Execute finite-time radial deployment (v0.2).

    Parameters
    ----------
    cm_state_initial:
        Initial circular orbit state (center of mass).
    reel_schedule:
        Reel kinematics (ReelSchedule object).
    upper_mass_kg:
        Upper end mass [kg].
    lower_mass_kg:
        Lower end mass [kg].
    linear_density_kg_m:
        Tether linear density [kg/m].
    earth:
        Earth model (defaults to WGS-84).
    num_samples:
        Time-grid density (default 100 per deployment). Ensures ≥100 over deploy phase.
    h_residual_rel_tol, h_residual_abs_tol:
        Angular momentum residual tolerances (defaults: 1e-8 rel, 1e-6 abs).
    cm_radius_drift_abs_tol:
        CM radius drift tolerance [m] (default 1e-9).

    Returns
    -------
    FiniteDeploymentTrajectory:
        Time-series trajectory with conservation residuals.

    Raises
    ------
    ValueError:
        If schedule is invalid, masses are non-positive, or trajectory becomes non-finite.

    Notes
    -----
    Assumptions: A-012 (radially constrained kinematics), A-013 (midpoint tether mass),
    A-014 (constant reel rate), A-015 (circular CM orbit), A-016 (scalar tension estimates).
    """
    earth = earth or EarthModel()
    earth.validate()
    reel_schedule.validate()

    if upper_mass_kg <= 0.0 or lower_mass_kg <= 0.0:
        raise ValueError("end masses must be positive")
    if linear_density_kg_m < 0.0:
        raise ValueError("linear_density_kg_m must be non-negative")

    # Time grid: ensure at least num_samples over deployment, plus coast phase
    deploy_duration = reel_schedule.deploy_duration_s
    if deploy_duration <= 0.0:
        raise ValueError("deployment duration must be positive")

    # Sample count: ensure 100+ samples over deployment
    samples_deploy = max(num_samples, int(np.ceil(deploy_duration * 100)))
    total_duration = reel_schedule.total_duration_s
    dt_deploy = deploy_duration / samples_deploy
    dt_coast = (
        reel_schedule.coast_after_deploy_s / max(1, int(np.ceil(samples_deploy * 0.5)))
        if reel_schedule.coast_after_deploy_s > 0.0
        else 0.0
    )

    times = []
    t = 0.0
    while t <= total_duration + 1e-12:
        times.append(t)
        if t < deploy_duration - 1e-12:
            t += dt_deploy
        elif t < total_duration - 1e-12:
            t += dt_coast if dt_coast > 0.0 else dt_deploy
        else:
            break

    times.append(total_duration)
    times = sorted(set(times))

    # Record initial state for residual tracking
    r_cm_0 = cm_state_initial.position_m.copy()
    r_cm_0_mag = float(np.linalg.norm(r_cm_0))
    h_0 = cm_state_initial.mass_kg * angular_momentum(
        cm_state_initial.position_m, cm_state_initial.velocity_m_s
    )
    h_0_mag = float(np.linalg.norm(h_0))

    samples_list: list[FiniteDeploymentSample] = []
    max_h_residual = 0.0
    max_cm_drift = 0.0

    for t_s in times:
        # Prescribed length and rate at this time
        ell = reel_schedule.length_m(t_s)
        ell_dot = reel_schedule.rate_m_s(t_s)
        ell_ddot = reel_schedule.acceleration_m_s2(t_s)

        # Analytic circular orbit state
        r_cm_t, v_cm_t = _circular_orbit_state(t_s, cm_state_initial, earth)

        # CM radius drift check
        r_cm_mag = float(np.linalg.norm(r_cm_t))
        cm_drift = abs(r_cm_mag - r_cm_0_mag)
        max_cm_drift = max(max_cm_drift, cm_drift)

        if cm_drift > cm_radius_drift_abs_tol:
            raise ValueError(f"CM radius drifted beyond tolerance at t={t_s}: drift={cm_drift}")

        # Mass map at this deployed length
        mass_map = compute_mass_map(
            length_m=ell,
            length_rate_m_s=ell_dot,
            length_acc_m_s2=ell_ddot,
            upper_mass_kg=upper_mass_kg,
            lower_mass_kg=lower_mass_kg,
            linear_density_kg_m=linear_density_kg_m,
            final_length_m=reel_schedule.final_length_m,
        )

        # Tip positions (radially aligned)
        r_hat = r_cm_t / r_cm_mag
        r_u = r_cm_t + mass_map.s_upper_m * r_hat
        r_l = r_cm_t - mass_map.s_lower_m * r_hat
        r_t = r_cm_t + mass_map.s_tether_m * r_hat

        # Orbital frame angular velocity (design spec §8)
        omega_orb = np.cross(r_cm_t, v_cm_t) / (r_cm_mag**2)

        # Kinematic tip velocities (design spec §8, eq 8.2–8.4)
        # v_i = v_cm + ω × ρ_i + ṡ_i r̂
        omega_cross_rhat = np.cross(omega_orb, r_hat)
        v_u = v_cm_t + 2.0 * mass_map.s_upper_dot_m_s * omega_cross_rhat + mass_map.s_upper_dot_m_s * r_hat
        v_l = v_cm_t - 2.0 * mass_map.s_lower_dot_m_s * omega_cross_rhat - mass_map.s_lower_dot_m_s * r_hat
        v_t = (
            v_cm_t
            + 2.0 * mass_map.s_tether_dot_m_s * omega_cross_rhat
            + mass_map.s_tether_dot_m_s * r_hat
        )

        # Angular momentum check (design spec §10)
        h_t = (
            mass_map.upper_mass_kg * np.cross(r_u, v_u)
            + mass_map.lower_effective_mass_kg * np.cross(r_l, v_l)
            + mass_map.tether_deployed_mass_kg * np.cross(r_t, v_t)
        )
        h_residual = np.linalg.norm(h_t - h_0)
        h_tol = max(h_residual_abs_tol, h_residual_rel_tol * h_0_mag)
        max_h_residual = max(max_h_residual, h_residual)

        if h_residual > h_tol:
            raise ValueError(
                f"Angular momentum residual exceeded tolerance at t={t_s}: "
                f"residual={h_residual}, tol={h_tol}"
            )

        # Finite-check
        if not (np.all(np.isfinite(r_u)) and np.all(np.isfinite(v_u))):
            raise ValueError(f"Non-finite upper tip state at t={t_s}")
        if not (np.all(np.isfinite(r_l)) and np.all(np.isfinite(v_l))):
            raise ValueError(f"Non-finite lower tip state at t={t_s}")

        # Tension estimates (design spec §9, calls existing estimator)
        # Mean motion for consistency
        n_rad_s = float(np.sqrt(earth.mu_m3_s2 / r_cm_mag**3))

        tension_est = estimate_tension(
            mu_m3_s2=earth.mu_m3_s2,
            r_cm_m=r_cm_t,
            v_cm_m_s=v_cm_t,
            mass_map=mass_map,
            n_rad_s=n_rad_s,
        )

        # Build sample
        sample = FiniteDeploymentSample(
            time_s=t_s,
            length_m=ell,
            reel_rate_m_s=ell_dot,
            mass_map=mass_map,
            upper_position_m=r_u,
            upper_velocity_m_s=v_u,
            lower_position_m=r_l,
            lower_velocity_m_s=v_l,
            tether_position_m=r_t,
            tether_velocity_m_s=v_t,
            tension_static_n=tension_est.static_upper_n,
            tension_dynamic_upper_n=tension_est.dynamic_upper_n,
            tension_dynamic_lower_n=tension_est.dynamic_lower_n,
            angular_momentum_m2_s=h_t,
            angular_momentum_residual_mag_m2_s=h_residual,
            cm_radius_drift_m=cm_drift,
        )
        samples_list.append(sample)

    if not samples_list:
        raise ValueError("No samples generated (empty trajectory)")

    return FiniteDeploymentTrajectory(
        samples=tuple(samples_list),
        final_length_m=reel_schedule.final_length_m,
        total_duration_s=total_duration,
        initial_angular_momentum_m2_s=h_0,
        max_angular_momentum_residual_m2_s=max_h_residual,
        max_cm_radius_drift_m=max_cm_drift,
    )
