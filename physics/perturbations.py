"""Expandable orbital perturbation framework.

Purpose
-------
Provide independently enabled acceleration models that can be composed by orbital
simulators without coupling perturbations to tether dynamics.

Assumptions and limitations
---------------------------
The implemented J2 and drag terms are simplified research models. Solar radiation
pressure and third-body terms are documented placeholders returning zero until
reviewed force models and data interfaces are added. None are flight validated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import ArrayLike, NDArray


class Perturbation(Protocol):
    """Protocol for independently enabled perturbation acceleration models."""

    enabled: bool

    def acceleration_m_s2(self, position_m: ArrayLike, velocity_m_s: ArrayLike) -> NDArray[np.float64]:
        """Return perturbing acceleration in meters per second squared."""
        ...


@dataclass(frozen=True, slots=True)
class J2Perturbation:
    """Simplified oblate-primary J2 acceleration model."""

    mu_m3_s2: float
    radius_m: float
    j2: float
    enabled: bool = True

    def acceleration_m_s2(self, position_m: ArrayLike, velocity_m_s: ArrayLike) -> NDArray[np.float64]:
        """Return J2 perturbing acceleration or zero when disabled."""
        del velocity_m_s
        if not self.enabled:
            return np.zeros(3, dtype=float)
        r = np.asarray(position_m, dtype=float).reshape(3)
        radius = float(np.linalg.norm(r))
        if radius <= 0.0:
            raise ValueError("position radius must be positive")
        x, y, z = r
        z2_r2 = (z / radius) ** 2
        factor = 1.5 * self.j2 * self.mu_m3_s2 * self.radius_m**2 / radius**5
        return factor * np.array(
            [x * (5.0 * z2_r2 - 1.0), y * (5.0 * z2_r2 - 1.0), z * (5.0 * z2_r2 - 3.0)],
            dtype=float,
        )


@dataclass(frozen=True, slots=True)
class AtmosphericDragPerturbation:
    """Simplified drag acceleration using constant density and ballistic properties."""

    density_kg_m3: float
    drag_coefficient: float
    area_m2: float
    mass_kg: float
    enabled: bool = True

    def acceleration_m_s2(self, position_m: ArrayLike, velocity_m_s: ArrayLike) -> NDArray[np.float64]:
        """Return drag acceleration opposite inertial velocity or zero when disabled."""
        del position_m
        if not self.enabled:
            return np.zeros(3, dtype=float)
        if self.density_kg_m3 < 0.0 or self.drag_coefficient < 0.0 or self.area_m2 < 0.0:
            raise ValueError("density, drag coefficient, and area must be non-negative")
        if self.mass_kg <= 0.0:
            raise ValueError("mass_kg must be positive")
        v = np.asarray(velocity_m_s, dtype=float).reshape(3)
        speed = float(np.linalg.norm(v))
        if speed == 0.0:
            return np.zeros(3, dtype=float)
        factor = -0.5 * self.density_kg_m3 * self.drag_coefficient * self.area_m2 / self.mass_kg
        return factor * speed * v


@dataclass(frozen=True, slots=True)
class SolarRadiationPressurePerturbation:
    """Placeholder for future solar radiation pressure acceleration."""

    enabled: bool = False

    def acceleration_m_s2(self, position_m: ArrayLike, velocity_m_s: ArrayLike) -> NDArray[np.float64]:
        """Return zero until a reviewed SRP model is implemented."""
        del position_m, velocity_m_s
        return np.zeros(3, dtype=float)


@dataclass(frozen=True, slots=True)
class ThirdBodyPerturbation:
    """Placeholder for future third-body gravitational acceleration."""

    enabled: bool = False

    def acceleration_m_s2(self, position_m: ArrayLike, velocity_m_s: ArrayLike) -> NDArray[np.float64]:
        """Return zero until ephemeris-backed third-body modeling is implemented."""
        del position_m, velocity_m_s
        return np.zeros(3, dtype=float)


def total_perturbing_acceleration_m_s2(
    perturbations: tuple[Perturbation, ...] | list[Perturbation],
    position_m: ArrayLike,
    velocity_m_s: ArrayLike,
) -> NDArray[np.float64]:
    """Return the vector sum of enabled perturbing accelerations."""
    total = np.zeros(3, dtype=float)
    for perturbation in perturbations:
        if perturbation.enabled:
            total += perturbation.acceleration_m_s2(position_m, velocity_m_s)
    return total
