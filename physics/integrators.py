"""Reusable deterministic numerical integration utilities.

Purpose
-------
Provide a common interface for low-order explicit time integrators used by the
research simulator.

Assumptions
-----------
* State vectors are finite NumPy-compatible one-dimensional arrays.
* Derivative functions are deterministic and side-effect free.
* Fixed time steps are used; adaptive error control is intentionally omitted.

Equations
---------
Explicit Euler: ``y[n+1] = y[n] + dt*f(t[n], y[n])``.
Semi-implicit Euler updates velocity-like components before position-like
components when a split state is provided. RK4 uses the classical fourth-order
weighted slope average.

Limitations
-----------
These utilities are not certified numerical software. Stability depends on the
problem stiffness, time step, and selected method.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

import numpy as np
from numpy.typing import ArrayLike, NDArray

DerivativeFunction = Callable[[float, NDArray[np.float64]], NDArray[np.float64]]
AccelerationFunction = Callable[[float, NDArray[np.float64], NDArray[np.float64]], NDArray[np.float64]]


class IntegratorMethod(str, Enum):
    """Supported fixed-step integration methods."""

    EXPLICIT_EULER = "explicit_euler"
    SEMI_IMPLICIT_EULER = "semi_implicit_euler"
    RK4 = "rk4"


@dataclass(frozen=True, slots=True)
class IntegrationStats:
    """Deterministic metadata describing an integration run."""

    method: IntegratorMethod
    step_count: int
    dt_s: float

    def as_dict(self) -> dict[str, float | int | str]:
        """Return JSON-compatible integration statistics."""
        return {"method": self.method.value, "step_count": self.step_count, "dt_s": self.dt_s}


@dataclass(frozen=True, slots=True)
class IntegrationResult:
    """Time history produced by a fixed-step integrator."""

    times_s: NDArray[np.float64]
    states: NDArray[np.float64]
    stats: IntegrationStats

    def as_dict(self) -> dict[str, object]:
        """Return JSON-compatible arrays and metadata."""
        return {
            "times_s": self.times_s.tolist(),
            "states": self.states.tolist(),
            "stats": self.stats.as_dict(),
        }


def _validate_state(initial_state: ArrayLike) -> NDArray[np.float64]:
    state = np.asarray(initial_state, dtype=float).reshape(-1)
    if state.size == 0 or not np.all(np.isfinite(state)):
        raise ValueError("initial_state must contain finite values")
    return state


def _time_grid(duration_s: float, dt_s: float) -> NDArray[np.float64]:
    if duration_s < 0.0:
        raise ValueError("duration_s must be non-negative")
    if dt_s <= 0.0:
        raise ValueError("dt_s must be positive")
    step_count = int(round(duration_s / dt_s))
    if not np.isclose(step_count * dt_s, duration_s, rtol=0.0, atol=1e-12):
        raise ValueError("duration_s must be an integer multiple of dt_s")
    return np.linspace(0.0, duration_s, step_count + 1)


def explicit_euler_step(
    derivative: DerivativeFunction, time_s: float, state: NDArray[np.float64], dt_s: float
) -> NDArray[np.float64]:
    """Advance one fixed step with explicit Euler integration."""
    return state + dt_s * np.asarray(derivative(time_s, state), dtype=float).reshape(state.shape)


def rk4_step(
    derivative: DerivativeFunction, time_s: float, state: NDArray[np.float64], dt_s: float
) -> NDArray[np.float64]:
    """Advance one fixed step with classical fourth-order Runge-Kutta integration."""
    k1 = np.asarray(derivative(time_s, state), dtype=float).reshape(state.shape)
    k2 = np.asarray(derivative(time_s + 0.5 * dt_s, state + 0.5 * dt_s * k1), dtype=float)
    k3 = np.asarray(derivative(time_s + 0.5 * dt_s, state + 0.5 * dt_s * k2), dtype=float)
    k4 = np.asarray(derivative(time_s + dt_s, state + dt_s * k3), dtype=float)
    return state + (dt_s / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def semi_implicit_euler_step(
    acceleration: AccelerationFunction,
    time_s: float,
    state: NDArray[np.float64],
    dt_s: float,
) -> NDArray[np.float64]:
    """Advance ``[position..., velocity...]`` state with semi-implicit Euler."""
    if state.size % 2 != 0:
        raise ValueError("semi-implicit Euler requires paired position/velocity state")
    half = state.size // 2
    position = state[:half]
    velocity = state[half:]
    accel = np.asarray(acceleration(time_s, position, velocity), dtype=float).reshape(half)
    next_velocity = velocity + dt_s * accel
    next_position = position + dt_s * next_velocity
    return np.concatenate((next_position, next_velocity))


def integrate_fixed_step(
    *,
    method: IntegratorMethod,
    initial_state: ArrayLike,
    duration_s: float,
    dt_s: float,
    derivative: DerivativeFunction | None = None,
    acceleration: AccelerationFunction | None = None,
) -> IntegrationResult:
    """Integrate a deterministic system over a fixed time grid using one interface."""
    state = _validate_state(initial_state)
    times = _time_grid(duration_s, dt_s)
    states = np.empty((times.size, state.size), dtype=float)
    states[0] = state

    for index, time_s in enumerate(times[:-1], start=1):
        if method is IntegratorMethod.EXPLICIT_EULER:
            if derivative is None:
                raise ValueError("derivative is required for explicit Euler")
            state = explicit_euler_step(derivative, float(time_s), state, dt_s)
        elif method is IntegratorMethod.RK4:
            if derivative is None:
                raise ValueError("derivative is required for RK4")
            state = rk4_step(derivative, float(time_s), state, dt_s)
        elif method is IntegratorMethod.SEMI_IMPLICIT_EULER:
            if acceleration is None:
                raise ValueError("acceleration is required for semi-implicit Euler")
            state = semi_implicit_euler_step(acceleration, float(time_s), state, dt_s)
        else:
            raise ValueError(f"unsupported integrator method: {method}")
        if not np.all(np.isfinite(state)):
            raise FloatingPointError("integration produced non-finite state")
        states[index] = state

    return IntegrationResult(
        times_s=times,
        states=states,
        stats=IntegrationStats(method=method, step_count=times.size - 1, dt_s=dt_s),
    )
