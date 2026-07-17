"""Two-body Cartesian propagator (verification-grade, not ephemeris-grade)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from simulation.orbital.state import SpacecraftState


@dataclass(frozen=True, slots=True)
class PropagationResult:
    times_s: np.ndarray
    positions_m: np.ndarray  # shape (N, 3)
    velocities_m_s: np.ndarray  # shape (N, 3)
    final_state: SpacecraftState


def _two_body_ode(_t: float, y: np.ndarray, mu: float) -> np.ndarray:
    r = y[0:3]
    v = y[3:6]
    r_norm = np.linalg.norm(r)
    acc = -mu * r / (r_norm**3)
    return np.hstack((v, acc))


def propagate_two_body(
    state: SpacecraftState,
    duration_s: float,
    mu_m3_s2: float,
    *,
    rtol: float = 1e-10,
    atol: float = 1e-10,
    max_step: float | None = None,
) -> PropagationResult:
    """Propagate a point mass under two-body gravity (Assumption A-001).

    Uses SciPy RK45. Intended for short verification arcs, not long-term products.
    """
    if duration_s < 0.0:
        raise ValueError("duration_s must be non-negative")
    if duration_s == 0.0:
        return PropagationResult(
            times_s=np.array([0.0]),
            positions_m=state.position_m.reshape(1, 3),
            velocities_m_s=state.velocity_m_s.reshape(1, 3),
            final_state=state,
        )

    y0 = np.hstack((state.position_m, state.velocity_m_s))
    kwargs: dict = {"rtol": rtol, "atol": atol, "dense_output": False}
    if max_step is not None:
        kwargs["max_step"] = max_step

    sol = solve_ivp(
        fun=lambda t, y: _two_body_ode(t, y, mu_m3_s2),
        t_span=(0.0, duration_s),
        y0=y0,
        method="RK45",
        **kwargs,
    )
    if not sol.success:
        raise RuntimeError(f"Propagation failed: {sol.message}")

    positions = sol.y[0:3, :].T
    velocities = sol.y[3:6, :].T
    final = SpacecraftState(
        position_m=positions[-1],
        velocity_m_s=velocities[-1],
        mass_kg=state.mass_kg,
    )
    return PropagationResult(
        times_s=sol.t,
        positions_m=positions,
        velocities_m_s=velocities,
        final_state=final,
    )
