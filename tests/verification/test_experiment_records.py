"""End-to-end scenario and verification tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from simulation.scenarios.config import DeploymentScenarioConfig
from simulation.scenarios.runner import run_deployment_scenario
from verification.records import build_experiment_record, canonical_json, sha256_hex


@pytest.mark.smoke
def test_scenario_writes_evidence(tmp_path: Path) -> None:
    config = DeploymentScenarioConfig(
        scenario_id="test_deploy",
        tether_length_m=5_000.0,
        spacecraft_mass_kg=800.0,
        orbit_altitude_m=450_000.0,
    )
    result = run_deployment_scenario(config, output_dir=tmp_path)
    assert result.validation_passed
    assert result.report_paths["json"].exists()
    assert result.report_paths["markdown"].exists()

    data = json.loads(result.report_paths["json"].read_text(encoding="utf-8"))
    assert data["experiment_id"] == result.record.experiment_id
    assert "A-003" in data["payload"]["assumption_ids"]
    assert data["payload"]["validation"]["all_passed"] is True
    assert "claim_boundary" in data["payload"]


@pytest.mark.smoke
def test_record_hash_is_stable_for_same_payload() -> None:
    record = build_experiment_record(
        scenario_id="hash_test",
        parameters={"x": 1},
        assumption_ids=["A-001"],
        outputs={"y": 2},
        validation={"all_passed": True, "checks": []},
        limitations=["none"],
        expert_review_flags=[],
    )
    # Recompute hash from stored payload
    assert record.content_sha256 == sha256_hex(canonical_json(record.payload))


@pytest.mark.smoke
def test_low_altitude_tip_flags_fault(tmp_path: Path) -> None:
    # Long tether from low orbit should trip lower-tip altitude monitor.
    config = DeploymentScenarioConfig(
        scenario_id="low_tip",
        orbit_altitude_m=250_000.0,
        tether_length_m=200_000.0,
        upper_mass_fraction=0.5,
        min_lower_tip_altitude_m=200_000.0,
    )
    result = run_deployment_scenario(config, output_dir=tmp_path)
    actions = [r["trigger"] for r in result.decision_log["records"]]
    assert "LOWER_TIP_ALTITUDE_LOW" in actions
