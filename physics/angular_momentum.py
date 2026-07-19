"""Angular-momentum bookkeeping for simplified momentum-exchange studies.

Purpose
-------
Provide deterministic helpers for point-mass angular momentum accounting in
software-only research simulations.

Assumptions
-----------
* Bodies are represented as point masses.
* Vectors are inertial Cartesian coordinates in SI units.
* Angular momentum is computed about the supplied origin, normally Earth center
  for current orbital studies.

Equations
---------
For each point mass, ``H = m * (r x v)``.  System angular momentum is the vector
sum over modeled endpoint masses.

Limitations
-----------
This module does not model flexible tether modes, external torques, reels,
attitude dynamics, or validated momentum-exchange operations.

Future improvements
-------------------
Add frame metadata, torque integration, uncertainty propagation, and coupling to
higher-fidelity tether dynamics after assumptions are reviewed.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def angular_momentum_vector(
    position_m: ArrayLike, velocity_m_s: ArrayLike, mass_kg: float
) -> NDArray[np.float64]:
    """Return point-mass angular momentum ``m * (r x v)`` in kg m^2 / s."""
    if mass_kg <= 0.0:
        raise ValueError("mass_kg must be positive")
    r = np.asarray(position_m, dtype=float).reshape(3)
    v = np.asarray(velocity_m_s, dtype=float).reshape(3)
    return mass_kg * np.cross(r, v)


def total_angular_momentum(
    positions_m: ArrayLike, velocities_m_s: ArrayLike, masses_kg: ArrayLike
) -> NDArray[np.float64]:
    """Return summed angular momentum for matching position, velocity, and mass arrays."""
    positions = np.asarray(positions_m, dtype=float)
    velocities = np.asarray(velocities_m_s, dtype=float)
    masses = np.asarray(masses_kg, dtype=float)
    if positions.shape != velocities.shape or positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError("positions_m and velocities_m_s must both have shape (N, 3)")
    if masses.shape != (positions.shape[0],):
        raise ValueError("masses_kg must have shape (N,)")
    if np.any(masses <= 0.0):
        raise ValueError("all masses must be positive")
    return np.sum(np.cross(positions, velocities) * masses[:, np.newaxis], axis=0)
