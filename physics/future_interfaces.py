"""Documented placeholders for future orbital tether research capabilities.

These interfaces are intentionally unimplemented. They preserve architecture
boundaries while making future responsibilities explicit. None of these classes
represent flight software, validated mission models, certified aerospace systems,
or commercial products.
"""

from __future__ import annotations


class FlexibleTetherModel:
    """Future flexible-body tether dynamics model placeholder."""

    def simulate(self) -> None:
        """Raise until flexible tether dynamics are specified and verified."""
        raise NotImplementedError("FlexibleTetherModel is a documented placeholder only")


class ElectrodynamicTetherModel:
    """Future Lorentz-force and plasma interaction model placeholder."""

    def simulate(self) -> None:
        """Raise until electrodynamic assumptions and verification cases exist."""
        raise NotImplementedError("ElectrodynamicTetherModel is a documented placeholder only")


class LibrationController:
    """Future libration control law placeholder."""

    def command(self) -> None:
        """Raise until control authority and plant models are defined."""
        raise NotImplementedError("LibrationController is a documented placeholder only")


class AutonomousMissionPlanner:
    """Future autonomous mission-planning placeholder."""

    def plan(self) -> None:
        """Raise until autonomy requirements and safety constraints are defined."""
        raise NotImplementedError("AutonomousMissionPlanner is a documented placeholder only")


class CollisionAvoidance:
    """Future conjunction and collision-risk placeholder."""

    def assess(self) -> None:
        """Raise until validated screening methods and data sources are defined."""
        raise NotImplementedError("CollisionAvoidance is a documented placeholder only")


class DigitalTwin:
    """Future digital-twin state-estimation placeholder."""

    def update(self) -> None:
        """Raise until state-estimation interfaces and validation plans exist."""
        raise NotImplementedError("DigitalTwin is a documented placeholder only")


class StructuralHealthMonitor:
    """Future structural-health monitoring placeholder."""

    def evaluate(self) -> None:
        """Raise until sensor models and structural criteria are defined."""
        raise NotImplementedError("StructuralHealthMonitor is a documented placeholder only")
