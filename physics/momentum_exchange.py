"""Simplified momentum-exchange research model.

Purpose
-------
Model a rigid, massless tether with two point-mass endpoints for deterministic
simulation bookkeeping of center of mass, angular momentum, energy, and length
change events.

Assumptions
-----------
* Software-only research prototype; not flight software and not physically
  validated for mission design.
* Tether is straight, rigid, massless, and aligned with the provided axis.
* Endpoint velocities are inherited from the center of mass unless explicitly
  supplied by a caller.
* Deployment/retraction events are kinematic bookkeeping events and do not model
  actuator work, flexible dynamics, capture shocks, or external torques.

Equations
---------
Center of mass: ``r_cm = sum(m_i r_i) / sum(m_i)``. Angular momentum:
``H = sum(m_i (r_i x v_i))``. Energy uses helpers in ``physics.energy``.

Limitations
-----------
No flexible tether dynamics, electrodynamics, momentum-exchange catch/throw
validation, libration, collision risk, structural loads, or hardware interfaces.

Future improvements
-------------------
Introduce reviewed flexible-body dynamics, actuator work terms, uncertainty
bounds, frame metadata, and verification cases against trusted references.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from physics.angular_momentum import total_angular_momentum
from physics.energy import mechanical_energy_j


class TetherLengthEvent(str, Enum):
    """Supported kinematic tether length event types."""

    DEPLOYMENT = "deployment"
    RETRACTION = "retraction"


@dataclass(frozen=True, slots=True)
class EndpointState:
    """State of one modeled point-mass tether endpoint."""

    name: str
    mass_kg: float
    position_m: NDArray[np.float64]
    velocity_m_s: NDArray[np.float64]

    def __post_init__(self) -> None:
        if self.mass_kg <= 0.0:
            raise ValueError("endpoint mass_kg must be positive")
        object.__setattr__(self, "position_m", np.asarray(self.position_m, dtype=float).reshape(3))
        object.__setattr__(self, "velocity_m_s", np.asarray(self.velocity_m_s, dtype=float).reshape(3))

    def as_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible representation."""
        return {
            "name": self.name,
            "mass_kg": self.mass_kg,
            "position_m": self.position_m.tolist(),
            "velocity_m_s": self.velocity_m_s.tolist(),
        }


@dataclass(frozen=True, slots=True)
class MomentumExchangeSystem:
    """Two-endpoint rigid massless tether model for research bookkeeping."""

    tether_length_m: float
    primary: EndpointState
    secondary: EndpointState
    assumptions: tuple[str, ...] = (
        "rigid massless tether",
        "point-mass endpoints",
        "kinematic length events only",
        "not physically validated for flight or mission design",
    )

    def __post_init__(self) -> None:
        if self.tether_length_m < 0.0:
            raise ValueError("tether_length_m must be non-negative")
        actual = float(np.linalg.norm(self.primary.position_m - self.secondary.position_m))
        if not np.isclose(actual, self.tether_length_m, rtol=0.0, atol=1e-9):
            raise ValueError("endpoint separation must equal tether_length_m")

    @property
    def total_mass_kg(self) -> float:
        """Return total endpoint mass in kilograms."""
        return self.primary.mass_kg + self.secondary.mass_kg

    def center_of_mass_m(self) -> NDArray[np.float64]:
        """Return system center-of-mass position in meters."""
        return (
            self.primary.mass_kg * self.primary.position_m
            + self.secondary.mass_kg * self.secondary.position_m
        ) / self.total_mass_kg

    def center_of_mass_velocity_m_s(self) -> NDArray[np.float64]:
        """Return system center-of-mass velocity in meters per second."""
        return (
            self.primary.mass_kg * self.primary.velocity_m_s
            + self.secondary.mass_kg * self.secondary.velocity_m_s
        ) / self.total_mass_kg

    def angular_momentum_kg_m2_s(self) -> NDArray[np.float64]:
        """Return total angular momentum about the inertial origin."""
        return total_angular_momentum(
            np.vstack((self.primary.position_m, self.secondary.position_m)),
            np.vstack((self.primary.velocity_m_s, self.secondary.velocity_m_s)),
            np.array((self.primary.mass_kg, self.secondary.mass_kg)),
        )

    def mechanical_energy_j(self, *, mu_m3_s2: float | None = None) -> float:
        """Return summed endpoint mechanical energy in joules."""
        return float(
            mechanical_energy_j(
                self.primary.position_m, self.primary.velocity_m_s, self.primary.mass_kg, mu_m3_s2=mu_m3_s2
            )
            + mechanical_energy_j(
                self.secondary.position_m,
                self.secondary.velocity_m_s,
                self.secondary.mass_kg,
                mu_m3_s2=mu_m3_s2,
            )
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible simulation log entry."""
        return {
            "tether_length_m": self.tether_length_m,
            "total_mass_kg": self.total_mass_kg,
            "center_of_mass_m": self.center_of_mass_m().tolist(),
            "center_of_mass_velocity_m_s": self.center_of_mass_velocity_m_s().tolist(),
            "angular_momentum_kg_m2_s": self.angular_momentum_kg_m2_s().tolist(),
            "mechanical_energy_j": self.mechanical_energy_j(),
            "primary": self.primary.as_dict(),
            "secondary": self.secondary.as_dict(),
            "assumptions": list(self.assumptions),
        }


def create_centered_system(
    *,
    tether_length_m: float,
    primary_mass_kg: float,
    secondary_mass_kg: float,
    center_of_mass_m: ArrayLike,
    center_of_mass_velocity_m_s: ArrayLike,
    tether_axis: ArrayLike,
) -> MomentumExchangeSystem:
    """Create a mass-balanced two-endpoint system centered on a specified CM state."""
    if tether_length_m < 0.0:
        raise ValueError("tether_length_m must be non-negative")
    if primary_mass_kg <= 0.0 or secondary_mass_kg <= 0.0:
        raise ValueError("endpoint masses must be positive")
    cm = np.asarray(center_of_mass_m, dtype=float).reshape(3)
    vcm = np.asarray(center_of_mass_velocity_m_s, dtype=float).reshape(3)
    axis = np.asarray(tether_axis, dtype=float).reshape(3)
    norm = float(np.linalg.norm(axis))
    if norm <= 0.0:
        raise ValueError("tether_axis must be non-zero")
    unit = axis / norm
    total_mass = primary_mass_kg + secondary_mass_kg
    primary_offset = tether_length_m * secondary_mass_kg / total_mass
    secondary_offset = tether_length_m * primary_mass_kg / total_mass
    return MomentumExchangeSystem(
        tether_length_m=tether_length_m,
        primary=EndpointState("primary", primary_mass_kg, cm + primary_offset * unit, vcm),
        secondary=EndpointState("secondary", secondary_mass_kg, cm - secondary_offset * unit, vcm),
    )


def apply_length_event(system: MomentumExchangeSystem, new_length_m: float, event: TetherLengthEvent) -> MomentumExchangeSystem:
    """Return a new system after a kinematic deployment or retraction event."""
    if new_length_m < 0.0:
        raise ValueError("new_length_m must be non-negative")
    if event is TetherLengthEvent.DEPLOYMENT and new_length_m < system.tether_length_m:
        raise ValueError("deployment cannot reduce tether length")
    if event is TetherLengthEvent.RETRACTION and new_length_m > system.tether_length_m:
        raise ValueError("retraction cannot increase tether length")
    delta = system.primary.position_m - system.secondary.position_m
    if system.tether_length_m == 0.0:
        axis = np.array([1.0, 0.0, 0.0])
    else:
        axis = delta / float(np.linalg.norm(delta))
    updated = create_centered_system(
        tether_length_m=new_length_m,
        primary_mass_kg=system.primary.mass_kg,
        secondary_mass_kg=system.secondary.mass_kg,
        center_of_mass_m=system.center_of_mass_m(),
        center_of_mass_velocity_m_s=system.center_of_mass_velocity_m_s(),
        tether_axis=axis,
    )
    return replace(updated, assumptions=system.assumptions + (f"{event.value} event applied",))
