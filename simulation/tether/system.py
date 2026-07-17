"""Diagnostic helpers for tether tip free-orbit interpretation (A-007)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simulation.orbital.constants import EarthModel
from simulation.orbital.kepler import (
    altitude_from_radius,
    angular_momentum,
    semi_major_axis_from_energy,
    specific_energy,
)
from simulation.tether.deployment import TipState


@dataclass(frozen=True, slots=True)
class TipOrbitDiagnostic:
    """Free-Keplerian diagnostics as if the tip were cut free at this instant.

    These values are informational only while the tether remains connected (A-007).
    """

    tip_name: str
    specific_energy_j_kg: float
    specific_angular_momentum_m2_s: list[float]
    specific_angular_momentum_mag_m2_s: float
    semi_major_axis_m: float | None
    radius_m: float
    altitude_m: float
    caveat: str

    def as_dict(self) -> dict:
        return {
            "tip_name": self.tip_name,
            "specific_energy_j_kg": self.specific_energy_j_kg,
            "specific_angular_momentum_m2_s": self.specific_angular_momentum_m2_s,
            "specific_angular_momentum_mag_m2_s": self.specific_angular_momentum_mag_m2_s,
            "semi_major_axis_m": self.semi_major_axis_m,
            "radius_m": self.radius_m,
            "altitude_m": self.altitude_m,
            "caveat": self.caveat,
        }


_CAVEAT = (
    "Diagnostic only (A-007): free-orbit elements assume an instantaneous tether cut. "
    "Connected dumbbell motion is constrained and is not independent Keplerian flight."
)


def diagnostic_tip_orbit(tip: TipState, earth: EarthModel | None = None) -> TipOrbitDiagnostic:
    earth = earth or EarthModel()
    energy = specific_energy(tip.position_m, tip.velocity_m_s, earth.mu_m3_s2)
    h = angular_momentum(tip.position_m, tip.velocity_m_s)
    radius = float(np.linalg.norm(tip.position_m))
    return TipOrbitDiagnostic(
        tip_name=tip.name,
        specific_energy_j_kg=energy,
        specific_angular_momentum_m2_s=h.tolist(),
        specific_angular_momentum_mag_m2_s=float(np.linalg.norm(h)),
        semi_major_axis_m=semi_major_axis_from_energy(energy, earth.mu_m3_s2),
        radius_m=radius,
        altitude_m=altitude_from_radius(radius, earth.radius_m),
        caveat=_CAVEAT,
    )
