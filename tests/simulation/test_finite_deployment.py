from __future__ import annotations
import numpy as np
import pytest
from simulation.orbital.constants import EarthModel
from simulation.orbital.state import circular_equatorial_state
from simulation.tether.finite_deployment import simulate_finite_deployment
from simulation.tether.reel import ReelSchedule
from verification.checks import run_finite_deployment_checks


def test_finite_deployment_reaches_length_and_preserves_geometry() -> None:
    earth = EarthModel()
    initial = circular_equatorial_state(400_000.0, 1_000.0, earth)
    schedule = ReelSchedule(final_length_m=100.0, initial_length_m=1.0, reel_rate_m_s=10.0, coast_after_deploy_s=5.0)
    result = simulate_finite_deployment(initial_cm_state=initial, schedule=schedule, upper_mass_fraction=0.5, linear_density_kg_m=0.1, mu_m3_s2=earth.mu_m3_s2, sample_step_s=1.0)
    assert result.samples[-1].mass_map.length_m == pytest.approx(100.0)
    assert result.samples[-1].mass_map.undeployed_mass_kg == pytest.approx(0.0)
    assert run_finite_deployment_checks(result).all_passed
    assert len(result.samples) >= 2


def test_zero_density_final_geometry_matches_v01_mass_split() -> None:
    earth = EarthModel()
    initial = circular_equatorial_state(400_000.0, 1_000.0, earth)
    result = simulate_finite_deployment(initial_cm_state=initial, schedule=ReelSchedule(1_000.0, 1_000.0), upper_mass_fraction=0.25, linear_density_kg_m=0.0, mu_m3_s2=earth.mu_m3_s2, sample_step_s=2.0)
    final = result.samples[-1].mass_map
    assert final.s_upper_m == pytest.approx(750.0)
    assert final.s_lower_m == pytest.approx(250.0)


def test_schedule_hits_analytic_duration_and_holds_final_length() -> None:
    schedule = ReelSchedule(final_length_m=11.0, initial_length_m=1.0, reel_rate_m_s=2.0, coast_after_deploy_s=3.0)
    assert schedule.deploy_duration_s == pytest.approx(5.0)
    assert schedule.length_m(5.0) == pytest.approx(11.0)
    assert schedule.rate_m_s(5.0) == 0.0
    assert schedule.length_m(8.0) == pytest.approx(11.0)


def test_zero_rate_and_zero_duration_hold_initial_final_length() -> None:
    schedule = ReelSchedule(final_length_m=10.0, initial_length_m=10.0, reel_rate_m_s=0.0)
    schedule.validate()
    assert schedule.deploy_duration_s == 0.0
    assert schedule.total_duration_s == 0.0
    assert schedule.length_m(0.0) == pytest.approx(10.0)
    assert schedule.rate_m_s(0.0) == 0.0


def test_finite_trajectory_is_deterministic_and_contains_finite_tension() -> None:
    earth = EarthModel()
    initial = circular_equatorial_state(400_000.0, 1_000.0, earth)
    kwargs = dict(initial_cm_state=initial, schedule=ReelSchedule(100.0, 2.0), upper_mass_fraction=0.5, linear_density_kg_m=0.01, mu_m3_s2=earth.mu_m3_s2, sample_step_s=2.0)
    first = simulate_finite_deployment(**kwargs)
    second = simulate_finite_deployment(**kwargs)
    assert first.as_dict() == second.as_dict()
    for sample in first.samples:
        assert np.isfinite(sample.angular_momentum_kg_m2_s).all()
        assert np.isfinite([sample.tension.static_upper_n, sample.tension.dynamic_upper_n, sample.tension.dynamic_lower_n, sample.tension.gg_approx_n]).all()
        assert sample.tension.static_upper_n > 0.0
