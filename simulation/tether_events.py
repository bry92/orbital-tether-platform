"""Simulation event logging for simplified tether length changes.

Purpose
-------
Record deterministic deployment and retraction events for the momentum-exchange
research module without coupling simulation orchestration to control/autonomy.

Assumptions
-----------
Events are kinematic bookkeeping records. They do not imply actuator design,
flight validation, flexible tether dynamics, or closed-loop autonomy.

Equations used
--------------
This module delegates mass, center-of-mass, angular-momentum, and energy
bookkeeping to ``physics.momentum_exchange`` and stores the resulting values.

Limitations
-----------
No event timing dynamics, reel motor model, structural loads, collision checks,
or hardware interfaces are represented.

Future improvements
-------------------
Add validated event schedulers, actuator work terms, uncertainty metadata, and
integration with scenario provenance records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from physics.momentum_exchange import MomentumExchangeSystem, TetherLengthEvent, apply_length_event


@dataclass(frozen=True, slots=True)
class TetherEventRecord:
    """Deterministic log record for one simplified tether event."""

    sequence: int
    event: TetherLengthEvent
    previous_length_m: float
    new_length_m: float
    system_snapshot: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible event record."""
        return {
            "sequence": self.sequence,
            "event": self.event.value,
            "previous_length_m": self.previous_length_m,
            "new_length_m": self.new_length_m,
            "system_snapshot": self.system_snapshot,
        }


def apply_event_with_log(
    system: MomentumExchangeSystem, *, new_length_m: float, event: TetherLengthEvent, sequence: int
) -> tuple[MomentumExchangeSystem, TetherEventRecord]:
    """Apply a length event and return the updated system plus a deterministic log record."""
    if sequence < 0:
        raise ValueError("sequence must be non-negative")
    updated = apply_length_event(system, new_length_m, event)
    record = TetherEventRecord(
        sequence=sequence,
        event=event,
        previous_length_m=system.tether_length_m,
        new_length_m=updated.tether_length_m,
        system_snapshot=updated.as_dict(),
    )
    return updated, record
