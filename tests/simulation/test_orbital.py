"""Orbital mechanics consistency tests."""

from __future__ import annotations

import numpy as np
import pytest

from simulation.orbital.constants import EarthModel
from simulation.orbital.kepler import circular_speed, orbital_period, specific_energy
from simulation.orbital.propagate import propagate_two_body
from simulation.orbital.state import circular_equatorial_state


@pytest.mark.physics
def test_circular_speed_matches_vis_viva() -> None:
    earth = EarthModel()
    r = earth.radius_m + 400_000.0
    v = circular_speed(r, earth.mu_m3_s2)
    # Vis-viva for circular: v^2 = μ/r
    assert v**2 == pytest.approx(earth.mu_m3_s2 / r, rel=1e-15)


@pytest.mark.physics
def test_circular_equatorial_state_construction() -> None:
    earth = EarthModel()
    state = circular_equatorial_state(400_000.0, 500.0, earth)
    assert state.mass_kg == 500.0
    assert state.position_m[1] == 0.0
    assert state.position_m[2] == 0.0
    expected_v = circular_speed(state.radius_m, earth.mu_m3_s2)
    assert state.velocity_m_s[1] == pytest.approx(expected_v, rel=1e-15)
    energy = specific_energy(state.position_m, state.velocity_m_s, earth.mu_m3_s2)
    assert energy == pytest.approx(-earth.mu_m3_s2 / (2.0 * state.radius_m), rel=1e-12)


@pytest.mark.physics
def test_two_body_energy_conserved_short_arc() -> None:
    earth = EarthModel()
    state = circular_equatorial_state(400_000.0, 1000.0, earth)
    e0 = specific_energy(state.position_m, state.velocity_m_s, earth.mu_m3_s2)
    # Propagate ~1/20 of an orbit
    period = orbital_period(state.radius_m, earth.mu_m3_s2)
    result = propagate_two_body(state, period / 20.0, earth.mu_m3_s2, rtol=1e-12, atol=1e-12)
    e1 = specific_energy(
        result.final_state.position_m,
        result.final_state.velocity_m_s,
        earth.mu_m3_s2,
    )
    assert abs(e1 - e0) / abs(e0) < 1e-8


@pytest.mark.physics
def test_two_body_angular_momentum_conserved_short_arc() -> None:
    earth = EarthModel()
    state = circular_equatorial_state(500_000.0, 1000.0, earth)
    h0 = np.cross(state.position_m, state.velocity_m_s)
    period = orbital_period(state.radius_m, earth.mu_m3_s2)
    result = propagate_two_body(state, period / 10.0, earth.mu_m3_s2, rtol=1e-12, atol=1e-12)
    h1 = np.cross(result.final_state.position_m, result.final_state.velocity_m_s)
    assert np.linalg.norm(h1 - h0) / np.linalg.norm(h0) < 1e-8


@pytest.mark.smoke
def test_invalid_mass_rejected() -> None:
    with pytest.raises(ValueError):
        circular_equatorial_state(400_000.0, 0.0)
