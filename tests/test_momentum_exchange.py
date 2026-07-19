from __future__ import annotations

import numpy as np
import pytest

from physics.future_interfaces import FlexibleTetherModel
from physics.momentum_exchange import TetherLengthEvent, create_centered_system
from simulation.tether_events import apply_event_with_log


def test_centered_system_conserves_mass_and_center_of_mass() -> None:
    system = create_centered_system(
        tether_length_m=1000.0,
        primary_mass_kg=300.0,
        secondary_mass_kg=700.0,
        center_of_mass_m=[7_000_000.0, 0.0, 0.0],
        center_of_mass_velocity_m_s=[0.0, 7_500.0, 0.0],
        tether_axis=[1.0, 0.0, 0.0],
    )

    assert system.total_mass_kg == pytest.approx(1000.0)
    np.testing.assert_allclose(system.center_of_mass_m(), [7_000_000.0, 0.0, 0.0])
    np.testing.assert_allclose(system.center_of_mass_velocity_m_s(), [0.0, 7_500.0, 0.0])


def test_angular_momentum_conserved_for_kinematic_length_events() -> None:
    system = create_centered_system(
        tether_length_m=100.0,
        primary_mass_kg=400.0,
        secondary_mass_kg=600.0,
        center_of_mass_m=[7_000_000.0, 0.0, 0.0],
        center_of_mass_velocity_m_s=[0.0, 7_500.0, 0.0],
        tether_axis=[1.0, 0.0, 0.0],
    )
    initial_h = system.angular_momentum_kg_m2_s()

    deployed, deploy_log = apply_event_with_log(
        system, new_length_m=500.0, event=TetherLengthEvent.DEPLOYMENT, sequence=0
    )
    retracted, retract_log = apply_event_with_log(
        deployed, new_length_m=100.0, event=TetherLengthEvent.RETRACTION, sequence=1
    )

    np.testing.assert_allclose(deployed.angular_momentum_kg_m2_s(), initial_h, rtol=1e-14)
    np.testing.assert_allclose(retracted.angular_momentum_kg_m2_s(), initial_h, rtol=1e-14)
    assert deploy_log.as_dict()["event"] == "deployment"
    assert retract_log.as_dict()["event"] == "retraction"


def test_numerical_stability_and_deterministic_output() -> None:
    kwargs = dict(
        tether_length_m=1234.5,
        primary_mass_kg=250.0,
        secondary_mass_kg=750.0,
        center_of_mass_m=[6_900_000.0, 10.0, -5.0],
        center_of_mass_velocity_m_s=[-1.0, 7_610.0, 0.25],
        tether_axis=[0.1, 0.9, 0.3],
    )
    first = create_centered_system(**kwargs)
    second = create_centered_system(**kwargs)

    assert first.as_dict() == second.as_dict()
    assert np.isfinite(first.mechanical_energy_j())
    assert np.isfinite(first.angular_momentum_kg_m2_s()).all()


def test_future_interface_placeholders_raise() -> None:
    with pytest.raises(NotImplementedError):
        FlexibleTetherModel().simulate()
