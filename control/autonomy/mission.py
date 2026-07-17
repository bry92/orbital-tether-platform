"""Mission planning stubs (no closed-loop execution in v0.1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MissionPhase(str, Enum):
    PRELAUNCH = "prelaunch"
    ON_ORBIT_IDLE = "on_orbit_idle"
    TETHER_DEPLOY = "tether_deploy"
    MONITOR = "monitor"
    SAFE_HOLD = "safe_hold"


@dataclass(frozen=True, slots=True)
class MissionPlan:
    """Declarative mission plan for simulation scenarios.

    This is not a flight plan product. It only sequences simulated events.
    """

    plan_id: str
    phases: tuple[MissionPhase, ...]
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "phases": [p.value for p in self.phases],
            "notes": self.notes,
            "metadata": self.metadata,
            "claim_boundary": (
                "MissionPlan is a simulation orchestration stub, not flight procedures."
            ),
        }
