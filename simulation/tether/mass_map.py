"""Radial mass map for finite-time deployment (design spec §6).

Assumption A-013: deployed tether as midpoint point mass; undeployed on lower body.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MassMap:
    """Scalar radial offsets and rates about the CM."""

    length_m: float
    upper_mass_kg: float
    lower_end_mass_kg: float
    lower_effective_mass_kg: float
    tether_deployed_mass_kg: float
    undeployed_mass_kg: float
    total_mass_kg: float
    s_upper_m: float
    s_lower_m: float
    s_tether_m: float
    s_upper_dot_m_s: float
    s_lower_dot_m_s: float
    s_tether_dot_m_s: float
    s_upper_ddot_m_s2: float
    s_lower_ddot_m_s2: float
    s_tether_ddot_m_s2: float

    def as_dict(self) -> dict:
        return {
            "length_m": self.length_m,
            "upper_mass_kg": self.upper_mass_kg,
            "lower_end_mass_kg": self.lower_end_mass_kg,
            "lower_effective_mass_kg": self.lower_effective_mass_kg,
            "tether_deployed_mass_kg": self.tether_deployed_mass_kg,
            "undeployed_mass_kg": self.undeployed_mass_kg,
            "total_mass_kg": self.total_mass_kg,
            "s_upper_m": self.s_upper_m,
            "s_lower_m": self.s_lower_m,
            "s_tether_m": self.s_tether_m,
            "s_upper_dot_m_s": self.s_upper_dot_m_s,
            "s_lower_dot_m_s": self.s_lower_dot_m_s,
            "s_tether_dot_m_s": self.s_tether_dot_m_s,
            "s_upper_ddot_m_s2": self.s_upper_ddot_m_s2,
            "s_lower_ddot_m_s2": self.s_lower_ddot_m_s2,
            "s_tether_ddot_m_s2": self.s_tether_ddot_m_s2,
        }


def compute_mass_map(
    *,
    length_m: float,
    length_rate_m_s: float,
    length_acc_m_s2: float,
    upper_mass_kg: float,
    lower_mass_kg: float,
    linear_density_kg_m: float,
    final_length_m: float,
) -> MassMap:
    """Compute radial offsets and time derivatives for the v0.2 mass map."""
    if length_m <= 0.0:
        raise ValueError("length_m must be positive")
    if upper_mass_kg <= 0.0 or lower_mass_kg <= 0.0:
        raise ValueError("end masses must be positive")
    if linear_density_kg_m < 0.0:
        raise ValueError("linear_density_kg_m must be non-negative")
    if final_length_m < length_m:
        raise ValueError("final_length_m must be >= length_m")

    rho = linear_density_kg_m
    m_t = rho * length_m
    m_und = rho * (final_length_m - length_m)
    m_l_eff = lower_mass_kg + m_und
    m_tot = upper_mass_kg + lower_mass_kg + rho * final_length_m

    # s_u = (m_l_eff * ℓ + m_t * ℓ/2) / m_tot
    s_u = (m_l_eff * length_m + m_t * (length_m / 2.0)) / m_tot
    s_l = length_m - s_u
    s_t = s_u - length_m / 2.0

    # ds_u/dℓ = m_l_eff / m_tot ; d²s_u/dℓ² = -ρ / m_tot
    ds_u_dl = m_l_eff / m_tot
    d2s_u_dl2 = -rho / m_tot

    s_u_dot = ds_u_dl * length_rate_m_s
    s_l_dot = length_rate_m_s - s_u_dot
    s_t_dot = s_u_dot - 0.5 * length_rate_m_s

    s_u_ddot = d2s_u_dl2 * length_rate_m_s**2 + ds_u_dl * length_acc_m_s2
    s_l_ddot = length_acc_m_s2 - s_u_ddot
    s_t_ddot = s_u_ddot - 0.5 * length_acc_m_s2

    if s_u < 0.0 or s_l < 0.0:
        raise ValueError("mass map produced negative radial offsets")

    return MassMap(
        length_m=length_m,
        upper_mass_kg=upper_mass_kg,
        lower_end_mass_kg=lower_mass_kg,
        lower_effective_mass_kg=m_l_eff,
        tether_deployed_mass_kg=m_t,
        undeployed_mass_kg=m_und,
        total_mass_kg=m_tot,
        s_upper_m=s_u,
        s_lower_m=s_l,
        s_tether_m=s_t,
        s_upper_dot_m_s=s_u_dot,
        s_lower_dot_m_s=s_l_dot,
        s_tether_dot_m_s=s_t_dot,
        s_upper_ddot_m_s2=s_u_ddot,
        s_lower_ddot_m_s2=s_l_ddot,
        s_tether_ddot_m_s2=s_t_ddot,
    )
