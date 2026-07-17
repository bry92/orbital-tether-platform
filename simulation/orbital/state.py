"""Spacecraft / point-mass state representations."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simulation.orbital.constants import EarthModel
from simulation.orbital.kepler import circular_speed


@dataclass(frozen=True, slots=True)
class SpacecraftState:
    """Cartesian ECI state for a point mass.

    Parameters
    ----------
    position_m:
        Position vector [m] in ECI.
    velocity_m_s:
        Velocity vector [m/s] in ECI.
    mass_kg:
        Mass [kg] (> 0).
    """

    position_m: np.ndarray
    velocity_m_s: np.ndarray
    mass_kg: float

    def __post_init__(self) -> None:
        pos = np.asarray(self.position_m, dtype=float).reshape(3)
        vel = np.asarray(self.velocity_m_s, dtype=float).reshape(3)
        object.__setattr__(self, "position_m", pos)
        object.__setattr__(self, "velocity_m_s", vel)
        if self.mass_kg <= 0.0:
            raise ValueError("mass_kg must be positive")

    @property
    def radius_m(self) -> float:
        return float(np.linalg.norm(self.position_m))

    @property
    def speed_m_s(self) -> float:
        return float(np.linalg.norm(self.velocity_m_s))

    def as_dict(self) -> dict:
        return {
            "position_m": self.position_m.tolist(),
            "velocity_m_s": self.velocity_m_s.tolist(),
            "mass_kg": self.mass_kg,
            "radius_m": self.radius_m,
            "speed_m_s": self.speed_m_s,
        }


def circular_equatorial_state(
    altitude_m: float,
    mass_kg: float,
    earth: EarthModel | None = None,
) -> SpacecraftState:
    """Initialize a circular equatorial orbit in the model ECI frame.

    Assumptions: A-001, A-002, A-008.
    """
    earth = earth or EarthModel()
    earth.validate()
    if altitude_m <= 0.0:
        raise ValueError("altitude_m must be positive")
    if mass_kg <= 0.0:
        raise ValueError("mass_kg must be positive")

    radius = earth.radius_m + altitude_m
    speed = circular_speed(radius, earth.mu_m3_s2)
    position = np.array([radius, 0.0, 0.0], dtype=float)
    velocity = np.array([0.0, speed, 0.0], dtype=float)
    return SpacecraftState(position_m=position, velocity_m_s=velocity, mass_kg=mass_kg)
