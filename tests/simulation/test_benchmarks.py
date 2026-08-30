from __future__ import annotations

from simulation.scenarios.benchmarks import BENCHMARKS
from simulation.scenarios.finite_runner import run_finite_deployment_scenario


def test_v02_benchmarks_write_evidence_and_run_structural_checks(tmp_path) -> None:
    """Benchmarks are smoke/regression cases, not validated physical thresholds."""
    for config in BENCHMARKS.values():
        result = run_finite_deployment_scenario(config, output_dir=tmp_path)
        checks = result.record.payload["validation"]["checks"]
        assert result.report_paths["json"].is_file()
        assert {check["name"] for check in checks} >= {
            "trajectory_mass_conservation",
            "trajectory_cm_position",
            "trajectory_tether_length",
            "trajectory_radial_alignment",
            "trajectory_angular_momentum",
        }
