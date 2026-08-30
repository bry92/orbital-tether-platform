# Assumptions Register

**Document ID:** OTDT-AR-001  
**Revision:** A  
**Date:** 2026-07-16

Each assumption has an ID referenced by experiment records.  
Status: `ACTIVE` | `SUPERSEDED` | `REJECTED`

Severity: `MODELING` (affects physics) | `NUMERICAL` | `OPERATIONAL` | `CLAIM_BOUNDARY`

Expert review: `NONE` | `RECOMMENDED` | `REQUIRED`

---

## A-001 — Two-body point-mass gravity

| Field | Value |
|-------|-------|
| Statement | Earth gravity is represented solely by \(\ddot{r} = -\mu r / \|r\|^3\). |
| Status | ACTIVE |
| Severity | MODELING |
| Uncertainty | Neglects J2 (~1e-3 relative perturbation in LEO), drag, third body, SRP. |
| Expert review | RECOMMENDED for any LEO mission-duration claim |
| Impact if wrong | Secular nodal/argument drift; altitude decay not captured |

## A-002 — Circular equatorial initial orbit

| Field | Value |
|-------|-------|
| Statement | Initial orbit is exactly circular and equatorial in the model ECI frame. |
| Status | ACTIVE |
| Severity | MODELING |
| Uncertainty | Real insertion errors and inclination are ignored. |
| Expert review | NONE for prototype |

## A-003 — Instantaneous quasi-static deployment

| Field | Value |
|-------|-------|
| Statement | Tether reaches length \(L\) instantly; no reel dynamics, no transient tension spikes. |
| Status | ACTIVE (v0.1 only; SUPERSEDED for v0.2 finite-time path) |
| Severity | MODELING |
| Uncertainty | **High.** Real deployments are the dominant mission risk. |
| Expert review | **REQUIRED** before any deployment timeline or tension claim |
| Impact if wrong | Misses snag, recoil, and control interaction |

## A-004 — Massless rigid tether

| Field | Value |
|-------|-------|
| Statement | Tether has zero mass and infinite stiffness (fixed length after deploy). |
| Status | ACTIVE (v0.1 only; PARTIALLY SUPERSEDED for v0.2 by A-013) |
| Severity | MODELING |
| Uncertainty | Real tethers have linear density, elasticity, and thermal expansion. |
| Expert review | **REQUIRED** for tension, boom, or material selection studies |

## A-005 — Gravity-gradient co-rotation lock (diagnostic only)

| Field | Value |
|-------|-------|
| Statement | Optional kinematic state with tip velocities \(\mathbf{v}_i = \boldsymbol{\omega}\times\mathbf{r}_i\), \(\boldsymbol{\omega}=\mathbf{r}_{cm}\times\mathbf{v}_{cm}/r_{cm}^2\). Not the default deployment map. |
| Status | ACTIVE (diagnostic) |
| Severity | MODELING |
| Uncertainty | **High.** This state has angular momentum about Earth larger than the undeployed craft by \(\approx \omega(m_u\ell_u^2+m_l\ell_l^2)\); it is not a free instantaneous outcome. Librations omitted. |
| Expert review | **REQUIRED** for stability or MET performance estimates |

## A-006 — Radial alignment only

| Field | Value |
|-------|-------|
| Statement | Tether is aligned with local vertical at the deployment instant. |
| Status | ACTIVE |
| Severity | MODELING |
| Uncertainty | Off-vertical deployment changes tip velocities substantially. |
| Expert review | RECOMMENDED |

## A-007 — Tip free-orbit elements are diagnostic

| Field | Value |
|-------|-------|
| Statement | Keplerian elements computed for each tip assume an instantaneous cut; connected motion differs. |
| Status | ACTIVE |
| Severity | CLAIM_BOUNDARY |
| Uncertainty | Misuse risk: treating diagnostic SMA as a delivered orbit. |
| Expert review | REQUIRED if used in customer-facing performance charts |

## A-008 — Constants are WGS-84 conventional

| Field | Value |
|-------|-------|
| Statement | \(\mu = 3.986004418\times10^{14}\) m³/s², \(R_E = 6378137\) m. |
| Status | ACTIVE |
| Severity | NUMERICAL |
| Uncertainty | Different agencies use slightly different μ; document in each experiment. |
| Expert review | NONE |

## A-009 — Control/AI does not alter physics

| Field | Value |
|-------|-------|
| Statement | Packages under `control/` may log decisions but must not silently mutate μ, masses, or EOMs. |
| Status | ACTIVE |
| Severity | OPERATIONAL |
| Uncertainty | Process risk, not physics. |
| Expert review | RECOMMENDED for autonomy roadmap |

## A-010 — No electrodynamics in v0.1

| Field | Value |
|-------|-------|
| Statement | Plasma, induced EMF, and Lorentz forces are omitted entirely. |
| Status | ACTIVE |
| Severity | MODELING |
| Uncertainty | Complete omission for EDT concepts. |
| Expert review | **REQUIRED** before any EDT product claim |

## A-011 — Velocity inheritance at deployment instant

| Field | Value |
|-------|-------|
| Statement | Default deployment assigns \(\mathbf{v}_u = \mathbf{v}_l = \mathbf{v}_{cm}\) at the instant tips reach radial positions (no relative reel-out velocity profile). |
| Status | ACTIVE |
| Severity | MODELING |
| Uncertainty | **High** for real deployments (Coriolis, control of reel rate, transverse waves). Chosen because it conserves angular momentum about Earth for a free central-force system. |
| Expert review | **REQUIRED** before any claim about post-deploy tip orbits or Δv |
| Impact if wrong | Tip free-orbit elements and subsequent tether dynamics change |

---

## A-012 — Radially constrained finite-time kinematics

| Field | Value |
|-------|-------|
| Statement | The tether remains aligned with the local radial direction during prescribed-length payout. |
| Status | ACTIVE (v0.2) |
| Severity | MODELING |
| Uncertainty | Excludes libration, transverse waves, and Coriolis-driven off-axis motion. |
| Expert review | REQUIRED |

## A-013 — Midpoint tether mass and lower-body reel mass

| Field | Value |
|-------|-------|
| Statement | Deployed tether mass is a midpoint point mass; undeployed mass is collocated with the lower end mass. |
| Status | ACTIVE (v0.2) |
| Severity | MODELING |
| Uncertainty | Does not model distributed load, drum inertia, or thermal mass transfer. |
| Expert review | REQUIRED for load claims |

## A-014 — Piecewise-constant reel rate

| Field | Value |
|-------|-------|
| Statement | Payout has instantaneous start/stop with zero modeled acceleration except at the unmodeled switch. |
| Status | ACTIVE (v0.2) |
| Severity | MODELING |
| Uncertainty | Motor slew and transient reel dynamics are omitted. |
| Expert review | REQUIRED |

## A-015 — Analytic circular CM path during deployment

| Field | Value |
|-------|-------|
| Statement | The center of mass stays on its initial circular two-body orbit during the prescribed deployment. |
| Status | ACTIVE (v0.2) |
| Severity | MODELING |
| Uncertainty | Extended-body and perturbing-force effects are omitted. |
| Expert review | REQUIRED for mission analysis |

## A-016 — Scalar tension estimator

| Field | Value |
|-------|-------|
| Statement | Static and dynamic tension are scalar end-mass estimates under enforced radial kinematics. |
| Status | ACTIVE (v0.2) |
| Severity | MODELING |
| Uncertainty | Not an elasticity, shock, slack-contact, or structural-load model. |
| Expert review | REQUIRED before any hardware use |
---

## Change control

New physics features must:

1. Add or supersede assumption rows
2. Update `OTDT-ES-001`
3. Add tests that would fail if the assumption is violated in code
4. Mark expert-review level honestly

