"""Quasi-static radial tether deployment (v0.1).

Primary event model (A-003 / A-011):
    Instantaneous radial extension with **velocity inheritance**
    ``v_upper = v_lower = v_cm``. This conserves mass and angular momentum
    about Earth for a free system under central gravity.

Diagnostic (A-005):
    Optional co-rotating tip velocities ``v = ω × r`` represent a
    gravity-gradient-locked kinematic state. That state has *higher*
    angular momentum about Earth than the undeployed circular craft by
    ``ω · I_cm`` and is therefore **not** reachable by a free instantaneous
    deployment without external torque or CM-orbit adjustment.

This is NOT a flexible-tether or reel-dynamics simulation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from simulation.orbital.state import SpacecraftState


DEPLOYMENT_ASSUMPTION_IDS: tuple[str, ...] = (
    "A-003",
    "A-004",
    "A-006",
    "A-007",
    "A-011",
)


class TipVelocityModel(str, Enum):
    """How tip inertial velocities are assigned at the deployment instant."""

    VELOCITY_INHERITANCE = "velocity_inheritance"
    CO_ROTATING_DIAGNOSTIC = "co_rotating_diagnostic"


@dataclass(frozen=True, slots=True)
class TipState:
    """Point-mass tip after deployment."""

    name: str
    position_m: np.ndarray
    velocity_m_s: np.ndarray
    mass_kg: float
    radial_offset_m: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "position_m", np.asarray(self.position_m, dtype=float).reshape(3))
        object.__setattr__(
            self, "velocity_m_s", np.asarray(self.velocity_m_s, dtype=float).reshape(3)
        )
        if self.mass_kg <= 0.0:
            raise ValueError("mass_kg must be positive")

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "position_m": self.position_m.tolist(),
            "velocity_m_s": self.velocity_m_s.tolist(),
            "mass_kg": self.mass_kg,
            "radial_offset_m": self.radial_offset_m,
            "radius_m": float(np.linalg.norm(self.position_m)),
            "speed_m_s": float(np.linalg.norm(self.velocity_m_s)),
        }


@dataclass(frozen=True, slots=True)
class DeployedTetherSystem:
    """Rigid massless tether connecting upper and lower tips about a CM state."""

    length_m: float
    cm_state: SpacecraftState
    upper: TipState
    lower: TipState
    omega_orbital_rad_s: np.ndarray
    velocity_model: TipVelocityModel
    assumption_ids: tuple[str, ...]
    angular_momentum_note: str

    def as_dict(self) -> dict:
        return {
            "length_m": self.length_m,
            "cm_state": self.cm_state.as_dict(),
            "upper": self.upper.as_dict(),
            "lower": self.lower.as_dict(),
            "omega_orbital_rad_s": self.omega_orbital_rad_s.tolist(),
            "velocity_model": self.velocity_model.value,
            "assumption_ids": list(self.assumption_ids),
            "angular_momentum_note": self.angular_momentum_note,
        }


def system_mass(system: DeployedTetherSystem) -> float:
    return system.upper.mass_kg + system.lower.mass_kg


def system_angular_momentum(system: DeployedTetherSystem) -> np.ndarray:
    """Total angular momentum about Earth center: sum m (r × v)."""
    h_u = system.upper.mass_kg * np.cross(system.upper.position_m, system.upper.velocity_m_s)
    h_l = system.lower.mass_kg * np.cross(system.lower.position_m, system.lower.velocity_m_s)
    return h_u + h_l


def dumbbell_inertia_about_cm(system: DeployedTetherSystem) -> float:
    """Scalar planar inertia about CM: m_u ell_u^2 + m_l ell_l^2 [kg m^2]."""
    ell_u = abs(system.upper.radial_offset_m)
    ell_l = abs(system.lower.radial_offset_m)
    return system.upper.mass_kg * ell_u**2 + system.lower.mass_kg * ell_l**2


def deploy_radial_tether(
    cm_state: SpacecraftState,
    tether_length_m: float,
    upper_mass_fraction: float = 0.5,
    *,
    velocity_model: TipVelocityModel = TipVelocityModel.VELOCITY_INHERITANCE,
) -> DeployedTetherSystem:
    """Deploy a radial rigid massless tether about the CM (quasi-static event).

    Parameters
    ----------
    cm_state:
        Pre-deployment spacecraft state (becomes the system CM state).
    tether_length_m:
        Fully deployed length L > 0 [m].
    upper_mass_fraction:
        Fraction of mass at the radially outward tip in (0, 1).
    velocity_model:
        ``VELOCITY_INHERITANCE`` (default, conserves H about Earth) or
        ``CO_ROTATING_DIAGNOSTIC`` (GG-lock kinematics; does **not** conserve H).

    Notes
    -----
    Mass balance:

        ell_u = L * m_l / m
        ell_l = L * m_u / m
    """
    if tether_length_m <= 0.0:
        raise ValueError("tether_length_m must be positive")
    if not (0.0 < upper_mass_fraction < 1.0):
        raise ValueError("upper_mass_fraction must be in (0, 1)")

    r_cm = cm_state.position_m
    v_cm = cm_state.velocity_m_s
    r_norm = float(np.linalg.norm(r_cm))
    if r_norm <= 0.0:
        raise ValueError("CM radius must be positive")

    m = cm_state.mass_kg
    m_u = m * upper_mass_fraction
    m_l = m - m_u
    ell_u = tether_length_m * (m_l / m)
    ell_l = tether_length_m * (m_u / m)

    if ell_l >= r_norm:
        raise ValueError(
            "Lower tip would reach or pass through Earth center; reduce tether length "
            f"(ell_l={ell_l:.3f} m, r_cm={r_norm:.3f} m)"
        )

    r_hat = r_cm / r_norm
    omega = np.cross(r_cm, v_cm) / (r_norm**2)

    r_u = r_cm + ell_u * r_hat
    r_l = r_cm - ell_l * r_hat

    assumption_ids = list(DEPLOYMENT_ASSUMPTION_IDS)

    if velocity_model is TipVelocityModel.VELOCITY_INHERITANCE:
        v_u = v_cm.copy()
        v_l = v_cm.copy()
        am_note = (
            "Velocity inheritance: both tips keep v_cm. Angular momentum about Earth "
            "is conserved for this free instantaneous map (A-011)."
        )
    elif velocity_model is TipVelocityModel.CO_ROTATING_DIAGNOSTIC:
        v_u = np.cross(omega, r_u)
        v_l = np.cross(omega, r_l)
        assumption_ids.append("A-005")
        am_note = (
            "DIAGNOSTIC ONLY (A-005): co-rotating v=ω×r. Angular momentum about Earth "
            "exceeds the pre-deploy value by approximately ω * (m_u ell_u^2 + m_l ell_l^2). "
            "Not a free deployment outcome."
        )
    else:
        raise ValueError(f"Unknown velocity_model: {velocity_model}")

    upper = TipState(
        name="upper",
        position_m=r_u,
        velocity_m_s=v_u,
        mass_kg=m_u,
        radial_offset_m=ell_u,
    )
    lower = TipState(
        name="lower",
        position_m=r_l,
        velocity_m_s=v_l,
        mass_kg=m_l,
        radial_offset_m=-ell_l,
    )

    return DeployedTetherSystem(
        length_m=tether_length_m,
        cm_state=cm_state,
        upper=upper,
        lower=lower,
        omega_orbital_rad_s=omega,
        velocity_model=velocity_model,
        assumption_ids=tuple(assumption_ids),
        angular_momentum_note=am_note,
    )
