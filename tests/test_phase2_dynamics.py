from __future__ import annotations

import numpy as np
import pytest

from physics.integrators import IntegratorMethod, integrate_fixed_step
from physics.libration import LibrationConfig, estimate_libration_period_s, simulate_libration
from physics.perturbations import (
    AtmosphericDragPerturbation,
    J2Perturbation,
    SolarRadiationPressurePerturbation,
    total_perturbing_acceleration_m_s2,
)
from physics.tether_dynamics import (
    TetherDynamicsConfig,
    equilibrium_length_m,
    replay_tether_simulation,
    simulate_longitudinal_oscillation,
    tension_n,
)


def test_damped_tether_energy_decreases_and_outputs_are_finite() -> None:
    config = TetherDynamicsConfig(
        stiffness_n_m=20.0,
        damping_n_s_m=3.0,
        equilibrium_length_m=100.0,
        primary_mass_kg=100.0,
        secondary_mass_kg=100.0,
    )
    sim = simulate_longitudinal_oscillation(
        config=config,
        initial_extension_m=2.0,
        initial_relative_rate_m_s=0.0,
        duration_s=20.0,
        dt_s=0.05,
    )

    energies = sim.energies_j()
    assert energies[-1] < energies[0]
    assert np.isfinite(sim.tensions_n()).all()
    assert np.isfinite(sim.result.states).all()
    assert sim.as_dict()["integration_stats"]["method"] == "rk4"


def test_tether_frequency_matches_expected_small_oscillation() -> None:
    config = TetherDynamicsConfig(
        stiffness_n_m=50.0,
        damping_n_s_m=0.0,
        equilibrium_length_m=10.0,
        primary_mass_kg=100.0,
        secondary_mass_kg=100.0,
    )
    expected_period = 2.0 * np.pi / config.natural_frequency_rad_s
    sim = simulate_longitudinal_oscillation(
        config=config,
        initial_extension_m=1.0,
        initial_relative_rate_m_s=0.0,
        duration_s=expected_period,
        dt_s=expected_period / 200.0,
    )

    assert sim.result.states[-1, 0] == pytest.approx(1.0, rel=1e-6, abs=1e-6)
    assert sim.result.states[-1, 1] == pytest.approx(0.0, abs=1e-6)


def test_deterministic_tether_replay_round_trips_structured_data() -> None:
    config = TetherDynamicsConfig(10.0, 1.0, 50.0, 20.0, 30.0)
    sim = simulate_longitudinal_oscillation(
        config=config,
        initial_extension_m=0.5,
        initial_relative_rate_m_s=-0.1,
        duration_s=2.0,
        dt_s=0.1,
        method=IntegratorMethod.SEMI_IMPLICIT_EULER,
    )
    replay = replay_tether_simulation(sim.as_dict())

    assert replay.as_dict() == sim.as_dict()
    assert len(sim.to_csv_rows()) == sim.result.times_s.size


def test_integrator_consistency_for_exponential_decay() -> None:
    def derivative(_time_s: float, state: np.ndarray) -> np.ndarray:
        return -state

    initial = np.array([1.0])
    euler = integrate_fixed_step(
        method=IntegratorMethod.EXPLICIT_EULER,
        initial_state=initial,
        duration_s=1.0,
        dt_s=0.001,
        derivative=derivative,
    )
    rk4 = integrate_fixed_step(
        method=IntegratorMethod.RK4,
        initial_state=initial,
        duration_s=1.0,
        dt_s=0.1,
        derivative=derivative,
    )

    assert euler.states[-1, 0] == pytest.approx(np.exp(-1.0), rel=6e-4)
    assert rk4.states[-1, 0] == pytest.approx(np.exp(-1.0), rel=1e-6)


def test_libration_period_and_damping_behavior() -> None:
    config = LibrationConfig(orbital_rate_rad_s=0.001, damping_ratio=0.05)
    assert estimate_libration_period_s(0.001) == pytest.approx(2.0 * np.pi / (np.sqrt(3.0) * 0.001))
    sim = simulate_libration(
        config=config,
        initial_angle_rad=0.05,
        initial_angular_velocity_rad_s=0.0,
        duration_s=config.period_s,
        dt_s=config.period_s / 200.0,
    )

    assert np.isfinite(sim.result.states).all()
    assert sim.amplitudes_rad()[-1] < sim.amplitudes_rad()[0]
    assert sim.as_dict()["config"]["small_angle_assumption"] is True


def test_configurable_perturbations_can_be_enabled_independently() -> None:
    position = np.array([7_000_000.0, 0.0, 1_000_000.0])
    velocity = np.array([0.0, 7_500.0, 0.0])
    j2_on = J2Perturbation(mu_m3_s2=3.986004418e14, radius_m=6_378_137.0, j2=1.08262668e-3)
    j2_off = J2Perturbation(
        mu_m3_s2=3.986004418e14,
        radius_m=6_378_137.0,
        j2=1.08262668e-3,
        enabled=False,
    )
    drag = AtmosphericDragPerturbation(
        density_kg_m3=1e-12,
        drag_coefficient=2.2,
        area_m2=10.0,
        mass_kg=1000.0,
    )
    srp_placeholder = SolarRadiationPressurePerturbation(enabled=True)

    assert np.linalg.norm(j2_on.acceleration_m_s2(position, velocity)) > 0.0
    np.testing.assert_allclose(j2_off.acceleration_m_s2(position, velocity), np.zeros(3))
    assert np.dot(drag.acceleration_m_s2(position, velocity), velocity) < 0.0
    total = total_perturbing_acceleration_m_s2([j2_off, drag, srp_placeholder], position, velocity)
    np.testing.assert_allclose(total, drag.acceleration_m_s2(position, velocity))


def test_equilibrium_length_and_tension_are_configurable() -> None:
    assert equilibrium_length_m(100.0, static_force_n=50.0, stiffness_n_m=25.0) == pytest.approx(102.0)
    config = TetherDynamicsConfig(25.0, 2.0, 100.0, 10.0, 10.0)
    assert tension_n(config, length_m=101.0, relative_rate_m_s=0.5) == pytest.approx(26.0)
    assert tension_n(config, length_m=99.0, relative_rate_m_s=0.0) == 0.0
