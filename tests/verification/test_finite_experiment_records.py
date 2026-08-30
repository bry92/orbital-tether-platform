"""End-to-end evidence coverage for v0.2 finite deployment."""
from __future__ import annotations

import json

from simulation.scenarios.finite_runner import run_finite_deployment_scenario


def test_finite_record_contains_reproducible_trajectory_evidence(tmp_path) -> None:
    result = run_finite_deployment_scenario(output_dir=tmp_path)
    payload = json.loads(result.report_paths["json"].read_text(encoding="utf-8"))["payload"]
    trajectory = payload["outputs"]["finite_deployment"]
    first = trajectory["samples"][0]
    assert {"A-012", "A-013", "A-014", "A-015", "A-016"} <= set(payload["assumption_ids"])
    assert trajectory["schedule"]["deploy_duration_s"] > 0.0
    assert first["time_s"] == 0.0
    assert "s_upper_dot_m_s" in first["mass_map"]
    assert "velocity_m_s" in first["upper"]
    assert "dynamic_upper_n" in first["tension"]
    assert "final_angular_momentum_relative_residual" in trajectory["summary"]
    assert payload["claim_boundary"]
    assert payload["limitations"]
