"""Physics validation checks for simulation outputs."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from simulation.orbital.kepler import angular_momentum
from simulation.orbital.state import SpacecraftState
from simulation.tether.deployment import (
    DeployedTetherSystem,
    system_angular_momentum,
    system_mass,
)


@dataclass(frozen=True, slots=True)
class ValidationCheck:
    name: str
    passed: bool
    residual: float
    tolerance: float
    detail: str

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "residual": self.residual,
            "tolerance": self.tolerance,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class ValidationResult:
    checks: tuple[ValidationCheck, ...]

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def as_dict(self) -> dict:
        return {
            "all_passed": self.all_passed,
            "checks": [c.as_dict() for c in self.checks],
        }


def _check(name: str, residual: float, tolerance: float, detail: str) -> ValidationCheck:
    return ValidationCheck(
        name=name,
        passed=bool(residual <= tolerance),
        residual=float(residual),
        tolerance=float(tolerance),
        detail=detail,
    )


def run_deployment_checks(
    pre_state: SpacecraftState,
    system: DeployedTetherSystem,
    *,
    mass_tol: float = 0.0,
    cm_pos_rel_tol: float = 1e-12,
    cm_pos_abs_tol: float = 1e-9,
    ang_mom_rel_tol: float = 1e-9,
    ang_mom_abs_tol: float = 1e-6,
) -> ValidationResult:
    """Validate mass, CM placement, and angular momentum bookkeeping after deploy.

    Angular momentum about Earth is required to match the pre-deploy state for the
    default velocity-inheritance model (A-011). Co-rotating diagnostic deployments
    are expected to fail this check; callers should not use that mode for PASS gates.
    """
    checks: list[ValidationCheck] = []

    mass_residual = abs(system_mass(system) - pre_state.mass_kg)
    checks.append(
        _check(
            "mass_conservation",
            mass_residual,
            mass_tol,
            "Sum of tip masses must equal pre-deployment mass",
        )
    )

    # Reconstruct CM from tips and compare to declared CM state.
    m = system_mass(system)
    r_cm_recon = (
        system.upper.mass_kg * system.upper.position_m
        + system.lower.mass_kg * system.lower.position_m
    ) / m
    cm_err = float(np.linalg.norm(r_cm_recon - system.cm_state.position_m))
    cm_tol = max(cm_pos_abs_tol, cm_pos_rel_tol * float(np.linalg.norm(system.cm_state.position_m)))
    checks.append(
        _check(
            "cm_position_consistency",
            cm_err,
            cm_tol,
            "Mass-weighted tip positions must recover CM position",
        )
    )

    # Pre-deployment system angular momentum (single body).
    h_pre = pre_state.mass_kg * angular_momentum(pre_state.position_m, pre_state.velocity_m_s)
    h_post = system_angular_momentum(system)
    h_err = float(np.linalg.norm(h_post - h_pre))
    h_tol = max(ang_mom_abs_tol, ang_mom_rel_tol * float(np.linalg.norm(h_pre)))
    checks.append(
        _check(
            "angular_momentum_about_earth",
            h_err,
            h_tol,
            "Under A-011 velocity inheritance, total m(r×v) must match pre-deploy state",
        )
    )

    # Tether length consistency.
    tip_sep = float(np.linalg.norm(system.upper.position_m - system.lower.position_m))
    length_err = abs(tip_sep - system.length_m)
    checks.append(
        _check(
            "tether_length",
            length_err,
            max(1e-9, 1e-12 * system.length_m),
            "Tip separation must equal commanded tether length",
        )
    )

    # Radial alignment: tip separation vector parallel to CM radius.
    sep = system.upper.position_m - system.lower.position_m
    r_hat = system.cm_state.position_m / np.linalg.norm(system.cm_state.position_m)
    cross_mag = float(np.linalg.norm(np.cross(sep / np.linalg.norm(sep), r_hat)))
    checks.append(
        _check(
            "radial_alignment",
            cross_mag,
            1e-12,
            "Tether must align with local vertical (A-006)",
        )
    )

    return ValidationResult(checks=tuple(checks))
