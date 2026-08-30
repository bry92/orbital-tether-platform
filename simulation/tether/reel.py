"""Commanded tether length schedules (prescribed reel kinematics).

Assumption A-014: piecewise-constant reel rate; no motor slew dynamics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReelSchedule:
    """Constant-rate payout from initial_length_m to final_length_m."""

    final_length_m: float
    reel_rate_m_s: float
    initial_length_m: float = 1.0
    coast_after_deploy_s: float = 0.0

    def validate(self) -> None:
        if self.final_length_m <= 0.0:
            raise ValueError("final_length_m must be positive")
        if self.initial_length_m <= 0.0:
            raise ValueError("initial_length_m must be positive")
        if self.initial_length_m > self.final_length_m:
            raise ValueError("initial_length_m must be <= final_length_m")
        if self.reel_rate_m_s < 0.0:
            raise ValueError("reel_rate_m_s must be non-negative")
        if self.reel_rate_m_s == 0.0 and self.initial_length_m != self.final_length_m:
            raise ValueError("zero reel_rate_m_s requires initial_length_m == final_length_m")
        if self.coast_after_deploy_s < 0.0:
            raise ValueError("coast_after_deploy_s must be non-negative")

    @property
    def deploy_duration_s(self) -> float:
        if self.reel_rate_m_s == 0.0:
            return 0.0
        return (self.final_length_m - self.initial_length_m) / self.reel_rate_m_s

    @property
    def total_duration_s(self) -> float:
        return self.deploy_duration_s + self.coast_after_deploy_s

    def length_m(self, time_s: float) -> float:
        if time_s < 0.0:
            raise ValueError("time_s must be non-negative")
        return min(
            self.final_length_m,
            self.initial_length_m + self.reel_rate_m_s * time_s,
        )

    def rate_m_s(self, time_s: float) -> float:
        if time_s < 0.0:
            raise ValueError("time_s must be non-negative")
        if self.length_m(time_s) >= self.final_length_m - 1e-15:
            return 0.0
        return self.reel_rate_m_s

    def acceleration_m_s2(self, time_s: float) -> float:
        """Idealized schedule uses ¨ℓ = 0 except at an unmodeled rate switch (A-014)."""
        _ = time_s
        return 0.0

    def as_dict(self) -> dict:
        return {
            "final_length_m": self.final_length_m,
            "initial_length_m": self.initial_length_m,
            "reel_rate_m_s": self.reel_rate_m_s,
            "coast_after_deploy_s": self.coast_after_deploy_s,
            "deploy_duration_s": self.deploy_duration_s,
            "total_duration_s": self.total_duration_s,
            "assumption_ids": ["A-014"],
            "simplified_physics": (
                "Piecewise-constant reel rate with instantaneous start/stop; "
                "¨ℓ modeled as 0 (A-014)."
            ),
        }
