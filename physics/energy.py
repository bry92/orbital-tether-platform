"""Energy bookkeeping for simplified momentum-exchange studies.

Purpose
-------
Provide deterministic mechanical-energy helpers for point-mass endpoint models.

Assumptions
-----------
* Bodies are point masses in inertial Cartesian coordinates.
* Energies are bookkeeping diagnostics, not validation evidence.
* Optional gravitational potential uses a central-body ``mu`` only.

Equations
---------
Kinetic energy is ``0.5 * m * dot(v, v)``. Two-body specific potential is
``-mu * m / norm(r)`` when a central gravitational parameter is supplied.

Limitations
-----------
No strain energy, motor/reel work, dissipation, flexible dynamics, impact/capture
physics, or electrodynamic work terms are represented.

Future improvements
-------------------
Add explicit work terms for modeled deployment actuators and higher-fidelity
potential models after verification cases are defined.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike


def kinetic_energy_j(velocity_m_s: ArrayLike, mass_kg: float) -> float:
    """Return point-mass kinetic energy in joules."""
    if mass_kg <= 0.0:
        raise ValueError("mass_kg must be positive")
    v = np.asarray(velocity_m_s, dtype=float).reshape(3)
    return float(0.5 * mass_kg * np.dot(v, v))


def gravitational_potential_energy_j(position_m: ArrayLike, mass_kg: float, mu_m3_s2: float) -> float:
    """Return central two-body gravitational potential energy in joules."""
    if mass_kg <= 0.0:
        raise ValueError("mass_kg must be positive")
    if mu_m3_s2 <= 0.0:
        raise ValueError("mu_m3_s2 must be positive")
    r = np.asarray(position_m, dtype=float).reshape(3)
    radius = float(np.linalg.norm(r))
    if radius <= 0.0:
        raise ValueError("position radius must be positive")
    return float(-mu_m3_s2 * mass_kg / radius)


def mechanical_energy_j(
    position_m: ArrayLike, velocity_m_s: ArrayLike, mass_kg: float, *, mu_m3_s2: float | None = None
) -> float:
    """Return kinetic energy plus optional central gravitational potential energy."""
    total = kinetic_energy_j(velocity_m_s, mass_kg)
    if mu_m3_s2 is not None:
        total += gravitational_potential_energy_j(position_m, mass_kg, mu_m3_s2)
    return float(total)
