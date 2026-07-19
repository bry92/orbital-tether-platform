"""Conservative small-angle tether libration model.

Purpose
-------
Model first-order in-plane libration as a damped small-angle oscillator suitable
for deterministic research simulations and structured logging.

Assumptions
-----------
* Angular displacement is small enough that ``sin(theta) ≈ theta``.
* The orbit is represented by a constant mean motion or orbital rate.
* Damping is linear and phenomenological.
* No nonlinear gravity-gradient dynamics, flexible tether coupling, control laws,
  or flight validation are included.

Equations
---------
``theta_dot = omega`` and ``omega_dot = -2*zeta*w*omega - w^2*theta`` where
``w = sqrt(3) * orbital_rate`` for the simplified gravity-gradient analogy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from physics.integrators import IntegrationResult, IntegratorMethod, integrate_fixed_step


@dataclass(frozen=True, slots=True)
class LibrationConfig:
    """Configuration for a damped small-angle libration oscillator."""

    orbital_rate_rad_s: float
    damping_ratio: float = 0.0

    def __post_init__(self) -> None:
        if self.orbital_rate_rad_s <= 0.0:
            raise ValueError("orbital_rate_rad_s must be positive")
        if self.damping_ratio < 0.0:
            raise ValueError("damping_ratio must be non-negative")

    @property
    def natural_frequency_rad_s(self) -> float:
        """Return the simplified small-angle libration frequency."""
        return float(np.sqrt(3.0) * self.orbital_rate_rad_s)

    @property
    def period_s(self) -> float:
        """Return undamped small-angle libration period estimate in seconds."""
        return float(2.0 * np.pi / self.natural_frequency_rad_s)


def estimate_libration_period_s(orbital_rate_rad_s: float) -> float:
    """Estimate small-angle tether libration period from a constant orbital rate."""
    return LibrationConfig(orbital_rate_rad_s=orbital_rate_rad_s).period_s


def _derivative(config: LibrationConfig):
    def derivative(_time_s: float, state: NDArray[np.float64]) -> NDArray[np.float64]:
        theta, theta_rate = state
        w = config.natural_frequency_rad_s
        theta_accel = -2.0 * config.damping_ratio * w * theta_rate - w**2 * theta
        return np.array([theta_rate, theta_accel], dtype=float)

    return derivative


def _acceleration(config: LibrationConfig):
    def acceleration(
        _time_s: float, position: NDArray[np.float64], velocity: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        w = config.natural_frequency_rad_s
        return -2.0 * config.damping_ratio * w * velocity - w**2 * position

    return acceleration


@dataclass(frozen=True, slots=True)
class LibrationSimulation:
    """Structured small-angle libration time history."""

    config: LibrationConfig
    result: IntegrationResult

    def amplitudes_rad(self) -> NDArray[np.float64]:
        """Return absolute angular displacement time series."""
        return np.abs(self.result.states[:, 0])

    def as_dict(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible libration output."""
        return {
            "config": {
                "orbital_rate_rad_s": self.config.orbital_rate_rad_s,
                "damping_ratio": self.config.damping_ratio,
                "natural_frequency_rad_s": self.config.natural_frequency_rad_s,
                "period_s": self.config.period_s,
                "small_angle_assumption": True,
            },
            "times_s": self.result.times_s.tolist(),
            "angular_displacement_rad": self.result.states[:, 0].tolist(),
            "angular_velocity_rad_s": self.result.states[:, 1].tolist(),
            "oscillation_amplitude_rad": self.amplitudes_rad().tolist(),
            "integration_stats": self.result.stats.as_dict(),
        }

    def to_csv_rows(self) -> list[dict[str, float]]:
        """Return CSV-ready libration rows for future visualization."""
        return [
            {
                "time_s": float(time_s),
                "angular_displacement_rad": float(state[0]),
                "angular_velocity_rad_s": float(state[1]),
                "oscillation_amplitude_rad": float(abs(state[0])),
            }
            for time_s, state in zip(self.result.times_s, self.result.states)
        ]


def simulate_libration(
    *,
    config: LibrationConfig,
    initial_angle_rad: float,
    initial_angular_velocity_rad_s: float,
    duration_s: float,
    dt_s: float,
    method: IntegratorMethod = IntegratorMethod.RK4,
) -> LibrationSimulation:
    """Simulate damped small-angle tether libration with a fixed-step integrator."""
    result = integrate_fixed_step(
        method=method,
        initial_state=np.array([initial_angle_rad, initial_angular_velocity_rad_s], dtype=float),
        duration_s=duration_s,
        dt_s=dt_s,
        derivative=_derivative(config),
        acceleration=_acceleration(config),
    )
    return LibrationSimulation(config=config, result=result)
