"""First-order longitudinal tether dynamics for research simulations.

Purpose
-------
Represent a straight tether as a one-dimensional spring-damper connecting two
endpoint masses. The model increases fidelity beyond kinematic bookkeeping while
remaining conservative and independently testable.

Assumptions
-----------
* Tether motion is longitudinal only along a fixed tether axis.
* The tether is represented by a linear spring and linear viscous damper.
* Endpoint masses reduce to one relative coordinate with reduced mass
  ``m_r = m1*m2/(m1+m2)``.
* No bending modes, transverse waves, libration coupling, reels, thermal effects,
  electrodynamics, capture shocks, or external validation are included.

Equations
---------
Let ``x`` be extension from equilibrium length and ``v = dx/dt``. Then
``x_dot = v`` and ``v_dot = -(c/m_r)*v - (k/m_r)*x``. Tension is
``max(0, k*x + c*v)`` because this simplified tether does not carry compression.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from physics.integrators import IntegrationResult, IntegratorMethod, integrate_fixed_step


@dataclass(frozen=True, slots=True)
class TetherDynamicsConfig:
    """Configuration for a longitudinal spring-damper tether model."""

    stiffness_n_m: float
    damping_n_s_m: float
    equilibrium_length_m: float
    primary_mass_kg: float
    secondary_mass_kg: float

    def __post_init__(self) -> None:
        if self.stiffness_n_m <= 0.0:
            raise ValueError("stiffness_n_m must be positive")
        if self.damping_n_s_m < 0.0:
            raise ValueError("damping_n_s_m must be non-negative")
        if self.equilibrium_length_m < 0.0:
            raise ValueError("equilibrium_length_m must be non-negative")
        if self.primary_mass_kg <= 0.0 or self.secondary_mass_kg <= 0.0:
            raise ValueError("endpoint masses must be positive")

    @property
    def reduced_mass_kg(self) -> float:
        """Return two-body reduced mass for longitudinal relative motion."""
        total = self.primary_mass_kg + self.secondary_mass_kg
        return self.primary_mass_kg * self.secondary_mass_kg / total

    @property
    def natural_frequency_rad_s(self) -> float:
        """Return undamped longitudinal natural frequency in radians per second."""
        return float(np.sqrt(self.stiffness_n_m / self.reduced_mass_kg))

    @property
    def damping_ratio(self) -> float:
        """Return classical viscous damping ratio for the reduced-mass oscillator."""
        return float(self.damping_n_s_m / (2.0 * np.sqrt(self.stiffness_n_m * self.reduced_mass_kg)))


def equilibrium_length_m(reference_length_m: float, static_force_n: float, stiffness_n_m: float) -> float:
    """Return linear spring equilibrium length under an optional static load."""
    if reference_length_m < 0.0:
        raise ValueError("reference_length_m must be non-negative")
    if stiffness_n_m <= 0.0:
        raise ValueError("stiffness_n_m must be positive")
    return float(reference_length_m + static_force_n / stiffness_n_m)


def tension_n(config: TetherDynamicsConfig, length_m: float, relative_rate_m_s: float) -> float:
    """Return non-compressive spring-damper tension for the current length and rate."""
    extension = length_m - config.equilibrium_length_m
    return float(max(0.0, config.stiffness_n_m * extension + config.damping_n_s_m * relative_rate_m_s))


def longitudinal_energy_j(config: TetherDynamicsConfig, extension_m: float, relative_rate_m_s: float) -> float:
    """Return modeled longitudinal kinetic plus spring potential energy."""
    kinetic = 0.5 * config.reduced_mass_kg * relative_rate_m_s**2
    potential = 0.5 * config.stiffness_n_m * extension_m**2
    return float(kinetic + potential)


def _derivative(config: TetherDynamicsConfig):
    def derivative(_time_s: float, state: NDArray[np.float64]) -> NDArray[np.float64]:
        extension, rate = state
        acceleration = -(
            config.damping_n_s_m * rate + config.stiffness_n_m * extension
        ) / config.reduced_mass_kg
        return np.array([rate, acceleration], dtype=float)

    return derivative


def _acceleration(config: TetherDynamicsConfig):
    def acceleration(
        _time_s: float, position: NDArray[np.float64], velocity: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        return -(
            config.damping_n_s_m * velocity + config.stiffness_n_m * position
        ) / config.reduced_mass_kg

    return acceleration


@dataclass(frozen=True, slots=True)
class TetherDynamicsSimulation:
    """Structured time history for longitudinal tether dynamics."""

    config: TetherDynamicsConfig
    result: IntegrationResult

    def amplitudes_m(self) -> NDArray[np.float64]:
        """Return absolute extension amplitude time series in meters."""
        return np.abs(self.result.states[:, 0])

    def lengths_m(self) -> NDArray[np.float64]:
        """Return physical tether length time series in meters."""
        return self.config.equilibrium_length_m + self.result.states[:, 0]

    def tensions_n(self) -> NDArray[np.float64]:
        """Return non-compressive tension time series in newtons."""
        return np.array(
            [tension_n(self.config, length, rate) for length, rate in zip(self.lengths_m(), self.result.states[:, 1])]
        )

    def energies_j(self) -> NDArray[np.float64]:
        """Return modeled longitudinal energy time series in joules."""
        return np.array(
            [longitudinal_energy_j(self.config, extension, rate) for extension, rate in self.result.states]
        )

    def as_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible output for replay or visualization."""
        return {
            "config": {
                "stiffness_n_m": self.config.stiffness_n_m,
                "damping_n_s_m": self.config.damping_n_s_m,
                "equilibrium_length_m": self.config.equilibrium_length_m,
                "primary_mass_kg": self.config.primary_mass_kg,
                "secondary_mass_kg": self.config.secondary_mass_kg,
                "reduced_mass_kg": self.config.reduced_mass_kg,
                "natural_frequency_rad_s": self.config.natural_frequency_rad_s,
                "damping_ratio": self.config.damping_ratio,
            },
            "times_s": self.result.times_s.tolist(),
            "extension_m": self.result.states[:, 0].tolist(),
            "relative_rate_m_s": self.result.states[:, 1].tolist(),
            "length_m": self.lengths_m().tolist(),
            "tension_n": self.tensions_n().tolist(),
            "oscillation_amplitude_m": self.amplitudes_m().tolist(),
            "system_energy_j": self.energies_j().tolist(),
            "endpoint_velocity_m_s": self.result.states[:, 1].tolist(),
            "integration_stats": self.result.stats.as_dict(),
        }

    def to_csv_rows(self) -> list[dict[str, float]]:
        """Return CSV-ready rows without requiring plotting or dataframe libraries."""
        return [
            {
                "time_s": float(time_s),
                "extension_m": float(state[0]),
                "relative_rate_m_s": float(state[1]),
                "length_m": float(length),
                "tension_n": float(tension),
                "system_energy_j": float(energy),
            }
            for time_s, state, length, tension, energy in zip(
                self.result.times_s, self.result.states, self.lengths_m(), self.tensions_n(), self.energies_j()
            )
        ]


def simulate_longitudinal_oscillation(
    *,
    config: TetherDynamicsConfig,
    initial_extension_m: float,
    initial_relative_rate_m_s: float,
    duration_s: float,
    dt_s: float,
    method: IntegratorMethod = IntegratorMethod.RK4,
) -> TetherDynamicsSimulation:
    """Simulate a damped longitudinal spring-mass tether oscillator."""
    initial_state = np.array([initial_extension_m, initial_relative_rate_m_s], dtype=float)
    result = integrate_fixed_step(
        method=method,
        initial_state=initial_state,
        duration_s=duration_s,
        dt_s=dt_s,
        derivative=_derivative(config),
        acceleration=_acceleration(config),
    )
    return TetherDynamicsSimulation(config=config, result=result)


def replay_tether_simulation(data: dict[str, Any]) -> TetherDynamicsSimulation:
    """Reconstruct a deterministic tether simulation from ``as_dict`` output."""
    config_data = data["config"]
    config = TetherDynamicsConfig(
        stiffness_n_m=float(config_data["stiffness_n_m"]),
        damping_n_s_m=float(config_data["damping_n_s_m"]),
        equilibrium_length_m=float(config_data["equilibrium_length_m"]),
        primary_mass_kg=float(config_data["primary_mass_kg"]),
        secondary_mass_kg=float(config_data["secondary_mass_kg"]),
    )
    states = np.column_stack((data["extension_m"], data["relative_rate_m_s"])).astype(float)
    from physics.integrators import IntegrationResult, IntegrationStats

    stats_data = data["integration_stats"]
    result = IntegrationResult(
        times_s=np.asarray(data["times_s"], dtype=float),
        states=states,
        stats=IntegrationStats(
            method=IntegratorMethod(stats_data["method"]),
            step_count=int(stats_data["step_count"]),
            dt_s=float(stats_data["dt_s"]),
        ),
    )
    return TetherDynamicsSimulation(config=config, result=result)
