"""Documented v0.2 benchmark scenario configurations."""
from __future__ import annotations
from simulation.scenarios.config import FiniteDeploymentScenarioConfig

BENCHMARKS = {
    "BM-DEP-001": FiniteDeploymentScenarioConfig(scenario_id="BM-DEP-001", final_length_m=1_000.0, reel_rate_m_s=0.5),
    "BM-DEP-002": FiniteDeploymentScenarioConfig(scenario_id="BM-DEP-002", final_length_m=1_000.0, reel_rate_m_s=0.5, linear_density_kg_m=0.001),
    "BM-DEP-003": FiniteDeploymentScenarioConfig(scenario_id="BM-DEP-003", final_length_m=5_000.0, reel_rate_m_s=5.0),
    "BM-DEP-004": FiniteDeploymentScenarioConfig(scenario_id="BM-DEP-004", final_length_m=2_000.0, reel_rate_m_s=0.5, upper_mass_fraction=0.25),
    "BM-DEP-005": FiniteDeploymentScenarioConfig(scenario_id="BM-DEP-005", final_length_m=10_000.0, reel_rate_m_s=0.5),
}
