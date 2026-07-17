"""Tether deployment consistency tests."""

from __future__ import annotations

import numpy as np
import pytest

from simulation.orbital.constants import EarthModel
from simulation.orbital.kepler import angular_momentum
from simulation.orbital.state import circular_equatorial_state
from simulation.tether.deployment import (
    TipVelocityModel,
    deploy_radial_tether,
    dumbbell_inertia_about_cm,
    system_angular_momentum,
    system_mass,
)
from simulation.tether.system import diagnostic_tip_orbit
from verification.checks import run_deployment_checks


@pytest.fixture
def leo_state():
    earth = EarthModel()
    return earth, circular_equatorial_state(400_000.0, 1000.0, earth)


@pytest.mark.physics
def test_mass_conserved_on_deploy(leo_state) -> None:
    _earth, pre = leo_state
    system = deploy_radial_tether(pre, tether_length_m=10_000.0, upper_mass_fraction=0.4)
    assert system_mass(system) == pytest.approx(pre.mass_kg)
    assert system.upper.mass_kg == pytest.approx(400.0)
    assert system.lower.mass_kg == pytest.approx(600.0)


@pytest.mark.physics
def test_cm_unchanged_by_construction(leo_state) -> None:
    _earth, pre = leo_state
    system = deploy_radial_tether(pre, tether_length_m=20_000.0, upper_mass_fraction=0.5)
    m = system_mass(system)
    r_cm = (
        system.upper.mass_kg * system.upper.position_m
        + system.lower.mass_kg * system.lower.position_m
    ) / m
    assert np.linalg.norm(r_cm - pre.position_m) < 1e-9


@pytest.mark.physics
def test_angular_momentum_conserved_under_velocity_inheritance(leo_state) -> None:
    _earth, pre = leo_state
    system = deploy_radial_tether(pre, tether_length_m=15_000.0, upper_mass_fraction=0.3)
    h_pre = pre.mass_kg * angular_momentum(pre.position_m, pre.velocity_m_s)
    h_post = system_angular_momentum(system)
    rel = np.linalg.norm(h_post - h_pre) / np.linalg.norm(h_pre)
    assert rel < 1e-12


@pytest.mark.physics
def test_corotating_diagnostic_increases_angular_momentum_by_inertia_term(leo_state) -> None:
    """Documents why co-rotation is diagnostic-only: ΔH ≈ ω * I_cm."""
    _earth, pre = leo_state
    system = deploy_radial_tether(
        pre,
        tether_length_m=15_000.0,
        upper_mass_fraction=0.3,
        velocity_model=TipVelocityModel.CO_ROTATING_DIAGNOSTIC,
    )
    h_pre = pre.mass_kg * angular_momentum(pre.position_m, pre.velocity_m_s)
    h_post = system_angular_momentum(system)
    delta_h = h_post - h_pre
    omega = system.omega_orbital_rad_s
    predicted = omega * dumbbell_inertia_about_cm(system)
    assert np.linalg.norm(delta_h - predicted) / np.linalg.norm(h_pre) < 1e-9
    # Must NOT pass the free-system conservation gate
    assert not run_deployment_checks(pre, system).all_passed


@pytest.mark.physics
def test_equal_mass_symmetric_offsets(leo_state) -> None:
    _earth, pre = leo_state
    L = 10_000.0
    system = deploy_radial_tether(pre, tether_length_m=L, upper_mass_fraction=0.5)
    assert system.upper.radial_offset_m == pytest.approx(L / 2.0)
    assert system.lower.radial_offset_m == pytest.approx(-L / 2.0)


@pytest.mark.physics
def test_upper_tip_farther_than_lower(leo_state) -> None:
    earth, pre = leo_state
    system = deploy_radial_tether(pre, tether_length_m=10_000.0, upper_mass_fraction=0.5)
    assert np.linalg.norm(system.upper.position_m) > np.linalg.norm(system.lower.position_m)
    upper = diagnostic_tip_orbit(system.upper, earth)
    lower = diagnostic_tip_orbit(system.lower, earth)
    assert upper.altitude_m > lower.altitude_m


@pytest.mark.physics
def test_velocity_inheritance_equal_tip_speeds(leo_state) -> None:
    _earth, pre = leo_state
    system = deploy_radial_tether(pre, tether_length_m=10_000.0, upper_mass_fraction=0.5)
    assert np.linalg.norm(system.upper.velocity_m_s) == pytest.approx(
        np.linalg.norm(system.lower.velocity_m_s), rel=1e-15
    )
    assert np.allclose(system.upper.velocity_m_s, pre.velocity_m_s)


@pytest.mark.physics
def test_verification_checks_pass(leo_state) -> None:
    _earth, pre = leo_state
    system = deploy_radial_tether(pre, tether_length_m=8_000.0, upper_mass_fraction=0.55)
    result = run_deployment_checks(pre, system)
    assert result.all_passed, result.as_dict()


@pytest.mark.physics
def test_deployment_deterministic(leo_state) -> None:
    _earth, pre = leo_state
    a = deploy_radial_tether(pre, 12_000.0, 0.5)
    b = deploy_radial_tether(pre, 12_000.0, 0.5)
    assert np.allclose(a.upper.position_m, b.upper.position_m)
    assert np.allclose(a.lower.velocity_m_s, b.lower.velocity_m_s)


@pytest.mark.smoke
def test_rejects_excessive_length(leo_state) -> None:
    _earth, pre = leo_state
    with pytest.raises(ValueError, match="Earth center"):
        deploy_radial_tether(pre, tether_length_m=pre.radius_m * 3.0, upper_mass_fraction=0.5)


@pytest.mark.physics
def test_tip_speed_scales_with_radius_under_corotation_diagnostic(leo_state) -> None:
    """Under diagnostic v = ω × r, |v| ∝ |r| for equatorial planar motion."""
    _earth, pre = leo_state
    system = deploy_radial_tether(
        pre,
        tether_length_m=10_000.0,
        upper_mass_fraction=0.5,
        velocity_model=TipVelocityModel.CO_ROTATING_DIAGNOSTIC,
    )
    ratio_r = np.linalg.norm(system.upper.position_m) / np.linalg.norm(system.lower.position_m)
    ratio_v = np.linalg.norm(system.upper.velocity_m_s) / np.linalg.norm(system.lower.velocity_m_s)
    assert ratio_v == pytest.approx(ratio_r, rel=1e-12)
