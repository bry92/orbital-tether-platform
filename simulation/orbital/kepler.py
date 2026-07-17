"""Keplerian / two-body scalar diagnostics."""

from __future__ import annotations

import numpy as np


def circular_speed(radius_m: float, mu_m3_s2: float) -> float:
    """Circular orbit speed \(v = \\sqrt{\\mu / r}\)."""
    if radius_m <= 0.0:
        raise ValueError("radius_m must be positive")
    if mu_m3_s2 <= 0.0:
        raise ValueError("mu_m3_s2 must be positive")
    return float(np.sqrt(mu_m3_s2 / radius_m))


def orbital_period(radius_m: float, mu_m3_s2: float) -> float:
    """Circular orbit period \(T = 2\\pi\\sqrt{r^3 / \\mu}\)."""
    if radius_m <= 0.0:
        raise ValueError("radius_m must be positive")
    if mu_m3_s2 <= 0.0:
        raise ValueError("mu_m3_s2 must be positive")
    return float(2.0 * np.pi * np.sqrt(radius_m**3 / mu_m3_s2))


def specific_energy(position_m: np.ndarray, velocity_m_s: np.ndarray, mu_m3_s2: float) -> float:
    """Specific mechanical energy \(\\varepsilon = v^2/2 - \\mu/r\)."""
    r = float(np.linalg.norm(position_m))
    v = float(np.linalg.norm(velocity_m_s))
    if r <= 0.0:
        raise ValueError("position magnitude must be positive")
    return 0.5 * v * v - mu_m3_s2 / r


def angular_momentum(position_m: np.ndarray, velocity_m_s: np.ndarray) -> np.ndarray:
    """Specific angular momentum \(\\mathbf{h} = \\mathbf{r} \\times \\mathbf{v}\)."""
    return np.cross(np.asarray(position_m, dtype=float), np.asarray(velocity_m_s, dtype=float))


def semi_major_axis_from_energy(energy_j_kg: float, mu_m3_s2: float) -> float | None:
    """Semi-major axis from energy; None if parabolic/hyperbolic (\(\\varepsilon \\ge 0\))."""
    if energy_j_kg >= 0.0:
        return None
    return float(-mu_m3_s2 / (2.0 * energy_j_kg))


def altitude_from_radius(radius_m: float, earth_radius_m: float) -> float:
    return float(radius_m - earth_radius_m)
