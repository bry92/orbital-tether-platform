"""Autonomous operations layer (stubs only in v0.1).

Physics lives in ``simulation/``. This package must not mutate orbital EOMs,
Earth constants, or tether constitutive models. Decisions are logged, not
executed against a flight vehicle.
"""

from __future__ import annotations

from control.autonomy.decision import DecisionEngine, DecisionLog, DecisionRecord
from control.autonomy.mission import MissionPlan, MissionPhase
from control.autonomy.telemetry import TelemetryFrame, TelemetryBuffer
from control.faults.handler import FaultHandler, FaultResponse

__all__ = [
    "DecisionEngine",
    "DecisionLog",
    "DecisionRecord",
    "FaultHandler",
    "FaultResponse",
    "MissionPhase",
    "MissionPlan",
    "TelemetryBuffer",
    "TelemetryFrame",
]
