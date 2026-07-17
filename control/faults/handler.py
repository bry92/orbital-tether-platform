"""Fault handling stubs for simulated anomaly responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from control.autonomy.decision import DecisionEngine


@dataclass(frozen=True, slots=True)
class FaultResponse:
    fault_code: str
    severity: str
    recommended_action: str
    simulated_only: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "fault_code": self.fault_code,
            "severity": self.severity,
            "recommended_action": self.recommended_action,
            "simulated_only": self.simulated_only,
            "claim_boundary": (
                "Canned simulation response — not a certified FDIR procedure."
            ),
        }


# Intentionally small canned set for prototype wiring only.
_CANNED: dict[str, FaultResponse] = {
    "TETHER_LENGTH_INCONSISTENT": FaultResponse(
        fault_code="TETHER_LENGTH_INCONSISTENT",
        severity="high",
        recommended_action="Halt further simulated deployment; flag verification failure",
    ),
    "ANGULAR_MOMENTUM_RESIDUAL": FaultResponse(
        fault_code="ANGULAR_MOMENTUM_RESIDUAL",
        severity="high",
        recommended_action="Invalidate experiment record; do not use outputs for design",
    ),
    "LOWER_TIP_ALTITUDE_LOW": FaultResponse(
        fault_code="LOWER_TIP_ALTITUDE_LOW",
        severity="medium",
        recommended_action="Reduce tether length in scenario config; expert review required",
    ),
}


class FaultHandler:
    """Maps fault codes to canned responses and decision-log entries."""

    def __init__(self, decision_engine: DecisionEngine | None = None) -> None:
        self.decision_engine = decision_engine or DecisionEngine()

    def handle(self, fault_code: str) -> FaultResponse:
        response = _CANNED.get(
            fault_code,
            FaultResponse(
                fault_code=fault_code,
                severity="unknown",
                recommended_action="Log only; no automated recovery in v0.1",
            ),
        )
        self.decision_engine.recommend(
            trigger=fault_code,
            action=response.recommended_action,
            rationale="Canned fault table lookup (control stub)",
        )
        return response
