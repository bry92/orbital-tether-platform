"""Tether system models (v0.1: rigid massless dumbbell)."""

from __future__ import annotations

from simulation.tether.deployment import (
    DEPLOYMENT_ASSUMPTION_IDS,
    DeployedTetherSystem,
    TipState,
    TipVelocityModel,
    deploy_radial_tether,
    dumbbell_inertia_about_cm,
    system_angular_momentum,
    system_mass,
)
from simulation.tether.system import diagnostic_tip_orbit
from simulation.tether.finite_deployment import FiniteDeploymentResult, simulate_finite_deployment
from simulation.tether.reel import ReelSchedule

__all__ = [
    "DEPLOYMENT_ASSUMPTION_IDS",
    "DeployedTetherSystem",
    "TipState",
    "TipVelocityModel",
    "deploy_radial_tether",
    "diagnostic_tip_orbit",
    "dumbbell_inertia_about_cm",
    "system_angular_momentum",
    "system_mass",
    "FiniteDeploymentResult",
    "ReelSchedule",
    "simulate_finite_deployment",
]
