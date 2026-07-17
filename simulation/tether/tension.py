"""Tension estimators for radially constrained deployment (design spec §9).

Assumption A-016: scalar estimates only; not material allowables.
SIMPLIFIED PHYSICS — expert review required before hardware use.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simulation.tether.mass_map import MassMap


@dataclass(frozen=True, slots=True)
class TensionEstimate:
    """Tension estimates at one sample (newtons). Positive => tension."""

    static_upper_n: float
    dynamic_upper_n: float
    dynamic_lower_n: float
    gg_approx_n: float
    slack_warning: bool
    note: str

    def as_dict(self) -> dict:
        return {
            "static_upper_n": self.static_upper_n,
            "dynamic_upper_n": self.dynamic_upper_n,
            "dynamic_lower_n": self.dynamic_lower_n,
            "gg_approx_n": self.gg_approx_n,
            "slack_warning": self.slack_warning,
            "note": self.note,
            "simplified_physics": True,
            "assumption_ids": ["A-016"],
        }


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n <= 0.0:
        raise ValueError("zero vector")
    return v / n


def estimate_tension(
    *,
    mu_m3_s2: float,
    r_cm_m: np.ndarray,
    v_cm_m_s: np.ndarray,
    mass_map: MassMap,
    n_rad_s: float,
) -> TensionEstimate:
    """Compute static and dynamic tension estimates at the current sample.

    Dynamic tension uses the kinematic acceleration of each end mass under the
    radially constrained prescribed-length model and Newton's second law with a
    single radial tether force (A-016).
    """
    r_hat = _unit(r_cm_m)
    r_cm = float(np.linalg.norm(r_cm_m))
    omega = np.cross(r_cm_m, v_cm_m_s) / (r_cm**2)
    n = float(np.linalg.norm(omega))
    # Prefer mean-motion argument for circular CM consistency.
    n_use = n_rad_s if n_rad_s > 0.0 else n

    s_u = mass_map.s_upper_m
    s_l = mass_map.s_lower_m
    s_u_dot = mass_map.s_upper_dot_m_s
    s_l_dot = mass_map.s_lower_dot_m_s
    s_u_ddot = mass_map.s_upper_ddot_m_s2
    s_l_ddot = mass_map.s_lower_ddot_m_s2

    r_u = r_cm_m + s_u * r_hat
    r_l = r_cm_m - s_l * r_hat
    r_u_mag = float(np.linalg.norm(r_u))
    r_l_mag = float(np.linalg.norm(r_l))

    a_cm = -(n_use**2) * r_cm_m  # circular CM

    # Kinematic accelerations (design spec derivation):
    # a = a_cm + 2 ṡ (ω × r̂) - s n² r̂ + s̈ r̂
    # For lower tip ρ = -s_l r̂, carefully apply with signed offset.
    w_cross_rhat = np.cross(omega, r_hat)

    a_u = a_cm + 2.0 * s_u_dot * w_cross_rhat - s_u * (n_use**2) * r_hat + s_u_ddot * r_hat
    # Lower: ρ_l = -s_l r_hat; ρ̇ involves -s_l_dot r_hat - s_l r̂̇
    # Analogous result: a_l = a_cm - 2 s_l_dot (ω×r̂) + s_l n² r̂ - s_l_ddot r̂
    a_l = (
        a_cm
        - 2.0 * s_l_dot * w_cross_rhat
        + s_l * (n_use**2) * r_hat
        - s_l_ddot * r_hat
    )

    g_u = -mu_m3_s2 * r_u / (r_u_mag**3)
    g_l = -mu_m3_s2 * r_l / (r_l_mag**3)

    # Upper: F_T = -T r̂  =>  T = m (g - a) · r̂
    t_dyn_u = float(mass_map.upper_mass_kg * np.dot(g_u - a_u, r_hat))
    # Lower: F_T = +T r̂  =>  T = m (a - g) · r̂
    t_dyn_l = float(mass_map.lower_effective_mass_kg * np.dot(a_l - g_l, r_hat))

    # Static (ṡ=0, s̈=0) upper free-body: T = m_u (n² r_u - μ/r_u²)
    t_static = float(mass_map.upper_mass_kg * (n_use**2 * r_u_mag - mu_m3_s2 / (r_u_mag**2)))

    mu_red = (
        mass_map.upper_mass_kg
        * mass_map.lower_effective_mass_kg
        / (mass_map.upper_mass_kg + mass_map.lower_effective_mass_kg)
    )
    t_gg = float(3.0 * (n_use**2) * mu_red * mass_map.length_m)

    slack = bool(t_dyn_u < 0.0 or t_dyn_l < 0.0)
    note = (
        "SIMPLIFIED (A-016): scalar tension from end-mass free bodies under prescribed "
        "radial kinematics. Not a structural allowable. "
        "dynamic_upper vs dynamic_lower may differ when tether mass is present."
    )
    return TensionEstimate(
        static_upper_n=t_static,
        dynamic_upper_n=t_dyn_u,
        dynamic_lower_n=t_dyn_l,
        gg_approx_n=t_gg,
        slack_warning=slack,
        note=note,
    )
