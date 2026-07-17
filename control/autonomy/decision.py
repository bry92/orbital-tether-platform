"""Decision logging (no ML / no physics mutation)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    decision_id: str
    timestamp_utc: str
    trigger: str
    action: str
    rationale: str
    requires_expert_review: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "timestamp_utc": self.timestamp_utc,
            "trigger": self.trigger,
            "action": self.action,
            "rationale": self.rationale,
            "requires_expert_review": self.requires_expert_review,
        }


@dataclass
class DecisionLog:
    records: list[DecisionRecord] = field(default_factory=list)

    def append(self, record: DecisionRecord) -> None:
        self.records.append(record)

    def as_dict(self) -> dict[str, Any]:
        return {"records": [r.as_dict() for r in self.records]}


class DecisionEngine:
    """Rule-stub decision engine.

    v0.1 only emits logged recommendations. It does not command the simulator
    or alter physical parameters.
    """

    def __init__(self) -> None:
        self.log = DecisionLog()
        self._counter = 0

    def recommend(self, trigger: str, action: str, rationale: str) -> DecisionRecord:
        self._counter += 1
        record = DecisionRecord(
            decision_id=f"DEC-{self._counter:04d}",
            timestamp_utc=_utc_now(),
            trigger=trigger,
            action=action,
            rationale=rationale,
            requires_expert_review=True,
        )
        self.log.append(record)
        return record
