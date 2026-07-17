"""Earth / model constants used by the orbital engine.

Assumption A-008: WGS-84 conventional values unless overridden per experiment.
"""

from __future__ import annotations

from dataclasses import dataclass


# WGS-84 conventional gravitational parameter [m^3/s^2]
EARTH_MU_M3_S2: float = 3.986004418e14

# WGS-84 equatorial radius [m]
EARTH_RADIUS_M: float = 6_378_137.0

# Assumption IDs always active in v0.1 Keplerian runs
DEFAULT_ASSUMPTION_IDS: tuple[str, ...] = (
    "A-001",
    "A-002",
    "A-008",
)


@dataclass(frozen=True, slots=True)
class EarthModel:
    """Central body parameters for an experiment."""

    mu_m3_s2: float = EARTH_MU_M3_S2
    radius_m: float = EARTH_RADIUS_M

    def validate(self) -> None:
        if self.mu_m3_s2 <= 0.0:
            raise ValueError("mu_m3_s2 must be positive")
        if self.radius_m <= 0.0:
            raise ValueError("radius_m must be positive")
