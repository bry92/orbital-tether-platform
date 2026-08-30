"""Scenario configuration dataclasses."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from simulation.orbital.constants import EARTH_MU_M3_S2, EARTH_RADIUS_M


@dataclass(frozen=True, slots=True)
class DeploymentScenarioConfig:
    """Inputs for the v0.1 radial deployment scenario."""

    scenario_id: str = "deploy_radial_v0"
    earth_mu_m3_s2: float = EARTH_MU_M3_S2
    earth_radius_m: float = EARTH_RADIUS_M
    spacecraft_mass_kg: float = 1000.0
    orbit_altitude_m: float = 400_000.0
    tether_length_m: float = 10_000.0
    upper_mass_fraction: float = 0.5
    propagate_seconds: float = 0.0
    min_lower_tip_altitude_m: float = 150_000.0

    def validate(self) -> None:
        if self.spacecraft_mass_kg <= 0.0:
            raise ValueError("spacecraft_mass_kg must be positive")
        if self.orbit_altitude_m <= 0.0:
            raise ValueError("orbit_altitude_m must be positive")
        if self.tether_length_m <= 0.0:
            raise ValueError("tether_length_m must be positive")
        if not (0.0 < self.upper_mass_fraction < 1.0):
            raise ValueError("upper_mass_fraction must be in (0, 1)")
        if self.propagate_seconds < 0.0:
            raise ValueError("propagate_seconds must be non-negative")
        if self.earth_mu_m3_s2 <= 0.0 or self.earth_radius_m <= 0.0:
            raise ValueError("earth model parameters must be positive")

    def as_dict(self) -> dict:
        return asdict(self)

@dataclass(frozen=True, slots=True)
class FiniteDeploymentScenarioConfig:
    """Inputs for the v0.2 prescribed finite-time deployment scenario."""

    scenario_id: str = "finite_deploy_v02"
    earth_mu_m3_s2: float = EARTH_MU_M3_S2
    earth_radius_m: float = EARTH_RADIUS_M
    spacecraft_mass_kg: float = 1000.0
    orbit_altitude_m: float = 400_000.0
    final_length_m: float = 1_000.0
    initial_length_m: float = 1.0
    reel_rate_m_s: float = 0.5
    coast_after_deploy_s: float = 60.0
    linear_density_kg_m: float = 0.0
    upper_mass_fraction: float = 0.5
    sample_step_s: float = 10.0

    def validate(self) -> None:
        if self.spacecraft_mass_kg <= 0.0 or self.orbit_altitude_m <= 0.0:
            raise ValueError("spacecraft_mass_kg and orbit_altitude_m must be positive")
        if not (0.0 < self.initial_length_m <= self.final_length_m):
            raise ValueError("initial_length_m must be in (0, final_length_m]")
        if self.reel_rate_m_s < 0.0 or self.sample_step_s <= 0.0:
            raise ValueError("reel_rate_m_s must be non-negative and sample_step_s positive")
        if self.reel_rate_m_s == 0.0 and self.initial_length_m != self.final_length_m:
            raise ValueError("zero reel_rate_m_s requires initial_length_m == final_length_m")
        if self.coast_after_deploy_s < 0.0 or self.linear_density_kg_m < 0.0:
            raise ValueError("coast duration and linear density must be non-negative")
        if not 0.0 < self.upper_mass_fraction < 1.0:
            raise ValueError("upper_mass_fraction must be in (0, 1)")
        if self.linear_density_kg_m * self.final_length_m >= self.spacecraft_mass_kg:
            raise ValueError("tether mass must leave a positive lower end mass")

    def as_dict(self) -> dict:
        return asdict(self)
