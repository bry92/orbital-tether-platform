"""Experiment record construction (provenance + parameters + outputs)."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from simulation import __version__ as sim_version


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _try_git_hash() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ExperimentRecord:
    experiment_id: str
    created_at_utc: str
    payload: dict[str, Any]
    content_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "created_at_utc": self.created_at_utc,
            "content_sha256": self.content_sha256,
            "payload": self.payload,
        }


def build_experiment_record(
    *,
    scenario_id: str,
    parameters: dict[str, Any],
    assumption_ids: list[str],
    outputs: dict[str, Any],
    validation: dict[str, Any],
    limitations: list[str],
    expert_review_flags: list[str],
) -> ExperimentRecord:
    """Build a reproducible experiment evidence record."""
    experiment_id = str(uuid.uuid4())
    created_at = _utc_now_iso()
    payload = {
        "schema_version": "0.1.0",
        "scenario_id": scenario_id,
        "software": {
            "package": "orbital-tether-platform",
            "simulation_version": sim_version,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "git_commit": _try_git_hash(),
        },
        "parameters": parameters,
        "assumption_ids": assumption_ids,
        "outputs": outputs,
        "validation": validation,
        "limitations": limitations,
        "expert_review_flags": expert_review_flags,
        "claim_boundary": (
            "This record documents a research prototype run. It is not flight certification "
            "evidence and does not constitute model validation against flight data."
        ),
    }
    digest = sha256_hex(canonical_json(payload))
    return ExperimentRecord(
        experiment_id=experiment_id,
        created_at_utc=created_at,
        payload=payload,
        content_sha256=digest,
    )
