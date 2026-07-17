# Orbital Tether Digital Twin and Autonomous Operations Platform

**Status:** Research prototype (software-only) — v0.1  
**Not flight software. Not a validated mission model. Not a commercial product claim.**

This repository is a technically conservative foundation for exploring orbital tether concepts through:

1. Physics simulation (two-body mechanics + simplified tether deployment)
2. Autonomous operations scaffolding (planning, telemetry, faults — stubs in v0.1)
3. Verification evidence (assumptions, parameters, outputs, reproducible reports)

## What v0.1 actually does

- Propagates Keplerian two-body state for a point-mass spacecraft
- Models a **quasi-static radial tether deployment** about the system center of mass
- Conserves system mass and (under stated assumptions) angular momentum about Earth
- Records experiment provenance for each run
- Provides pytest checks for numerical consistency

## What v0.1 does not do

- Flexible tether dynamics, waves, or libration control
- Electrodynamic tether (EDT) Lorentz force modeling
- Momentum-exchange catch/throw operations
- J2, drag, third-body, or SRP perturbations
- Hardware, GNC, or flight certification artifacts
- AI decision-making that overrides physics

## Repository layout

```
/simulation   orbital mechanics, tether model, scenario runner
/control      autonomous controller stubs (separated from physics)
/verification experiment records, reports, validation checks
/dashboard    placeholder only (no UI in v0.1)
/docs         engineering documentation and assumption registers
/tests        physics consistency and smoke tests
```

## Quick start

```bash
cd orbital-tether-platform
python -m pip install -e ".[dev]"
pytest
python -m simulation.scenarios.run_deployment_demo
```

## Engineering entry points

| Document | Purpose |
|----------|---------|
| `docs/engineering/01_proposal_review.md` | NASA-style technology proposal critique |
| `docs/engineering/02_mvp_definition.md` | Minimum viable technical prototype |
| `docs/engineering/03_engineering_specification.md` | v0.1 engineering specification |
| `docs/assumptions/ASSUMPTIONS_REGISTER.md` | Explicit model assumptions and uncertainty |

## Standards we commit to

- Correctness over speed
- Physics models isolated from AI/control components
- Document assumptions; flag expert-review items
- Never invent scientific results or claim validation we have not performed
