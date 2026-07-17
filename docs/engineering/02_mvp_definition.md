# Minimum Viable Technical Prototype (MVP)

**Document ID:** OTDT-MVP-001  
**Revision:** A  
**Date:** 2026-07-16

## 1. MVP statement

Deliver a **reproducible, tested, two-body Keplerian simulation** with a **quasi-static radial tether deployment event**, plus an **experiment evidence record** for every run.

Anything beyond that is explicitly out of scope for v0.1.

## 2. In scope (v0.1)

| Capability | Acceptance test |
|------------|-----------------|
| Circular orbit initialization from altitude / mass | State matches `v = sqrt(μ/r)` within 1e-9 relative |
| State vector propagation (Keplerian two-body) | Energy conserved within tolerance over short arcs |
| Tether deployment: length L, tip mass split | CM position unchanged by construction |
| Post-deployment tip states (radial, velocity inheritance) | Angular momentum about Earth conserved within tolerance |
| Scenario runner with fixed config | Same config → bit-stable JSON report (float rounding noted) |
| Experiment record (assumptions, params, outputs) | Report written under `data/experiments/` |
| Automated pytest suite | `pytest` exits 0 |

## 3. Explicitly out of scope (v0.1)

- Flexible tether, tension PDE, skip-rope, libration ODE
- Electrodynamic tether forces
- Momentum-exchange catch/throw
- Perturbations (J2, drag, lunisolar, SRP)
- Attitude dynamics / ADCS
- Real telemetry ingestion
- React dashboard / FastAPI product UI
- PostgreSQL persistence (filesystem JSON is sufficient)
- ML / LLM decision making

## 4. Architecture minimal cut

```
simulation/orbital   ← Kepler two-body utilities
simulation/tether    ← deployment model (quasi-static)
simulation/scenarios ← runnable demo + config
verification/        ← records + validation checks
control/             ← stubs only (interfaces, no claims)
dashboard/           ← README placeholder
docs/                ← engineering truth source
tests/               ← proof of consistency
```

## 5. Physics fidelity statement

v0.1 answers only:

> “If a spacecraft on a circular orbit instantaneously deploys a rigid, massless tether radially about its CM with tip velocities equal to the CM velocity, what are the tip states, and do mass and angular momentum bookkeeping remain consistent?”

It does **not** answer mission design questions about real deployment dynamics, stability, or performance.

## 6. Next increments (ordered)

1. **v0.2** — Finite-time deployment with reel rate; mass of tether; tension estimate (static)
2. **v0.3** — Planar libration (dumbbell) ODE; energy exchange between orbit and libration
3. **v0.4** — Tip release / capture (idealized MET) with angular momentum accounting
4. **v0.5** — J2 + atmospheric density table (flagged uncertainty)
5. **v0.6** — EDT Lorentz force *parametric* model with large uncertainty bands
6. **v1.x** — Ops layer: anomaly detection on simulated telemetry; still not flight software

Each increment must add tests and assumption-register updates before new features.

## 7. Definition of done for this repository milestone

- [x] Proposal review document
- [x] MVP definition
- [x] Engineering specification
- [x] Assumptions register
- [x] Working orbital + deployment simulation
- [x] Tests for consistency
- [x] Verification report generation
- [ ] Independent aerospace peer review (external — not claimed complete)
