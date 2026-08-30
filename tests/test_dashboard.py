"""Tests for the local evidence dashboard data projection."""

from __future__ import annotations

import json

from dashboard import app


def test_dashboard_data_projects_a_valid_experiment_record(tmp_path, monkeypatch) -> None:
    record = {
        "experiment_id": "evidence-001",
        "created_at_utc": "2026-08-30T12:00:00+00:00",
        "payload": {
            "scenario_id": "deploy_radial_v0",
            "parameters": {"tether_length_m": 10_000.0, "orbit_altitude_m": 400_000.0},
            "validation": {
                "all_passed": True,
                "checks": [{"name": "mass", "passed": True, "residual": 0.0}],
            },
            "limitations": ["Research-only model."],
            "outputs": {
                "tip_diagnostics_free_orbit_if_cut": {
                    "upper": {"altitude_m": 405_000.0},
                    "lower": {"altitude_m": 395_000.0},
                }
            },
        },
    }
    (tmp_path / "record.json").write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(app, "EXPERIMENTS_DIR", tmp_path)

    data = app.dashboard_data()

    assert data["latest"]["experiment_id"] == "evidence-001"
    assert data["latest"]["validation_passed"] is True
    assert data["latest"]["upper_altitude_m"] == 405_000.0
