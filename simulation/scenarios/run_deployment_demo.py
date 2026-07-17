"""CLI demo: run radial tether deployment scenario and print a concise summary."""

from __future__ import annotations

import json
from pathlib import Path

from simulation.scenarios.config import DeploymentScenarioConfig
from simulation.scenarios.runner import run_deployment_scenario


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    out = root / "data" / "experiments"

    config = DeploymentScenarioConfig(
        scenario_id="deploy_radial_v0_demo",
        spacecraft_mass_kg=1000.0,
        orbit_altitude_m=400_000.0,
        tether_length_m=10_000.0,
        upper_mass_fraction=0.5,
    )
    result = run_deployment_scenario(config, output_dir=out)

    outputs = result.record.payload["outputs"]
    print("=== Orbital Tether Deployment Demo (v0.1) ===")
    print(f"Experiment ID : {result.record.experiment_id}")
    print(f"Validation    : {'PASS' if result.validation_passed else 'FAIL'}")
    print(f"JSON report   : {result.report_paths['json']}")
    print(f"Markdown      : {result.report_paths['markdown']}")
    print()
    print("Pre-deploy altitude [m]:", config.orbit_altitude_m)
    print("Tether length     [m]:", config.tether_length_m)
    print(
        "Upper tip altitude [m]:",
        outputs["tip_diagnostics_free_orbit_if_cut"]["upper"]["altitude_m"],
    )
    print(
        "Lower tip altitude [m]:",
        outputs["tip_diagnostics_free_orbit_if_cut"]["lower"]["altitude_m"],
    )
    print()
    print("Altitude deltas (geometric, not mission-certified):")
    print(json.dumps(outputs["altitude_deltas_m"], indent=2))
    print()
    print("LIMITATION: Quasi-static rigid model only. See docs/assumptions/ASSUMPTIONS_REGISTER.md")


if __name__ == "__main__":
    main()
