"""Simulated telemetry structures (no spacecraft interface in v0.1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class TelemetryFrame:
    time_s: float
    channel: str
    value: float
    unit: str
    quality: str = "simulated"

    def as_dict(self) -> dict:
        return {
            "time_s": self.time_s,
            "channel": self.channel,
            "value": self.value,
            "unit": self.unit,
            "quality": self.quality,
        }


@dataclass
class TelemetryBuffer:
    """In-memory telemetry buffer for future anomaly-detection work."""

    frames: list[TelemetryFrame] = field(default_factory=list)

    def ingest(self, frame: TelemetryFrame) -> None:
        self.frames.append(frame)

    def latest(self, channel: str) -> TelemetryFrame | None:
        for frame in reversed(self.frames):
            if frame.channel == channel:
                return frame
        return None

    def as_dict(self) -> dict[str, Any]:
        return {"frames": [f.as_dict() for f in self.frames]}
