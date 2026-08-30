# ADR-002 — v0.2 Angular-Momentum Boundary and Kinematics

**Status:** UNRESOLVED — aerospace-dynamics review required before changing v0.2 equations or implementation.  
**Date:** 2026-08-30  
**Scope:** The prescribed finite-time radial deployment model only. This is a design reconciliation, not scientific or flight validation.

## Decision required

v0.2 §7 fixes the center of mass (CM) on its initial circular orbit, while §8 assigns every displaced component the rotating radial-frame velocity

\[
\mathbf v_i=\mathbf v_{cm}+\boldsymbol\omega\times\boldsymbol\rho_i+\dot{s}_i\hat r.
\]

v0.2 §10 simultaneously requires Earth-centered angular momentum to be conserved. These three requirements cannot all be exact for a changing tether length and nonzero radial-frame moment of inertia.

The project must decide which physical system boundary and resulting conservation law v0.2 represents. Until then, retain the existing implementation and report the angular-momentum residual as an exposed specification discrepancy; do not tune a tolerance or alter kinematics to hide it.

## Derivation of the current residual

Let \(M\) be total mass, \(\mathbf R,\mathbf V\) the CM position and velocity, and \(\boldsymbol\rho_i\) each component position relative to the CM. The mass map enforces \(\sum_i m_i\boldsymbol\rho_i=0\). Its imposed relative-rate terms are radial, so their Earth-centered cross-product contribution is zero in this planar radial construction. With \(\boldsymbol\rho_i\perp\boldsymbol\omega\), the implemented field gives

\[
\begin{aligned}
\mathbf H
&=\sum_i m_i(\mathbf R+\boldsymbol\rho_i)\times
(\mathbf V+\boldsymbol\omega\times\boldsymbol\rho_i+\dot{\boldsymbol\rho}_i)\\
&=M\mathbf R\times\mathbf V+I_{cm}(\ell)\boldsymbol\omega,\\
I_{cm}(\ell)&=m_u s_u^2+m_l^{eff}s_l^2+m_t s_t^2.
\end{aligned}
\]

The implementation holds \(R\) and \(\omega=n=\sqrt{\mu/R^3}\) fixed. Consequently,

\[
\Delta \mathbf H=n\,[I_{cm}(\ell)-I_{cm}(\ell_0)]\,\hat z.
\]

The deployed midpoint tether mass changes \(I_{cm}\) through both \(m_t=\rho\ell\) and the offsets dictated by the mass map; undeployed tether mass remains in \(m_l^{eff}\). Thus moving tether mass is included in the residual rather than being a numerical artifact.

## Numerical reconciliation

The following values were produced by the current deterministic benchmark implementation. `ωΔI` is the equation above, evaluated from each first and final mass map. It agrees with the reported `ΔH` to floating-point rounding.

| Benchmark | Relative \(\lVert\Delta H\rVert/\lVert H_0\rVert\) | \(\Delta H\) [kg m²/s] | \(\omega\Delta I\) [kg m²/s] | §11 `1e-8` gate |
|---|---:|---:|---:|---|
| BM-DEP-001 | 5.441503e-09 | 282,841.383 | 282,841.381 | pass |
| BM-DEP-002 | 5.436062e-09 | 282,558.531 | 282,558.539 | pass |
| BM-DEP-003 | 1.360377e-07 | 7,071,041.313 | 7,071,041.302 | fail |
| BM-DEP-004 | 1.632452e-08 | 848,524.789 | 848,524.778 | fail |
| BM-DEP-005 | 5.441509e-07 | 28,284,166.070 | 28,284,166.057 | fail |

The BM-DEP-003/004/005 failures are therefore expected consequences of the stated fixed-CM/co-rotating kinematics, not a coding error in the residual calculation.

## Actuator/reel boundary

A reel that is internal to the modeled spacecraft–tether system cannot change the total Earth-centered angular momentum without an equal and opposite angular-momentum change elsewhere in that complete system. The current model includes undeployed tether mass at the lower body but excludes reel/drum rotational inertia, actuator torque, attitude response, and any CM-orbit response. It therefore has no modeled location for the required \(-\Delta H\).

If prescribed co-rotation is imposed while holding the CM orbit fixed, the missing exchange must be represented explicitly as an externally imposed kinematic torque or an actuator/orbit angular-momentum ledger:

\[
\tau_{\mathrm{imposed},z}=\frac{d}{dt}\left(I_{cm}\omega\right),\qquad
J_{\mathrm{imposed},z}(t)=I_{cm}(t)\omega-I_{cm}(0)\omega.
\]

That would be a different declared system boundary from the current §10 statement that central gravity plus radial internal tension conserves complete-system \(\mathbf H\).

## Candidate consistent formulations

| Formulation | Conservation and CM behavior | §7/§8 compatibility | Tension / benchmark effect |
|---|---|---|---|
| A. Fixed circular CM plus prescribed co-rotating radial frame | Component \(H\) changes by \(\omega\Delta I\); record an imposed external/actuator-orbit ledger rather than assert complete-system conservation | Retains §7 and §8; requires §10 rewrite and an explicit boundary assumption | Existing tension equations remain kinematic estimates; BM failures become expected ledger values, not conservation failures |
| B. Fixed CM radius with \(\omega(t)=H_0/[MR^2+I(t)]\) | Conserves total \(H\), but CM tangential speed no longer equals the circular two-body value; a force/energy mechanism is required | Contradicts §7’s analytic circular velocity and changes §8 | Requires re-derivation of rotating-frame acceleration and tension |
| C. Constrained extended-body dynamics under central gravity | Conserves complete-system \(H\); CM responds to differential gravity at the same order as the discrepancy | Replaces §7’s fixed analytic CM simplification and §8 becomes an ODE result/constraint | Requires a new dynamics integrator and revised tension network; outside current prescribed-kinematic scope |
| D. Fixed CM plus velocity inheritance (omit \(\omega\times\rho\)) | Preserves the v0.1-style Earth-centered \(H\) bookkeeping for radial payout terms | Contradicts §8 and is not a co-rotating static-tension state | Invalidates the stated v0.2 tension/kinematics relationship |

## Proposed specification replacement options — not adopted

The following wording is intentionally offered for aerospace-dynamics review; it is **not** an implementation decision.

### Option A: prescribed kinematics with declared angular-momentum input

Replace §10 angular-momentum row with:

> “The imposed prescribed-length, co-rotating kinematic field is allowed to exchange angular momentum with an unmodeled actuator/orbit boundary. Report \(H_{components}\), \(\Delta H\), and \(J_{imposed}=\Delta H\) as diagnostics. Do not use \(\Delta H\) as a conservation PASS gate.”

Add an assumption identifying the external/actuator-orbit boundary and explicitly state that reel/drum/attitude dynamics are not modeled.

### Option C: closed-system conservation model

Replace §7 and §8 with:

> “Propagate the constrained extended-mass system under central gravity and internal constraint forces. CM motion is not fixed to the initial circular analytic orbit; total Earth-centered angular momentum of all modeled masses is conserved to numerical tolerance.”

Specify the constraint-force/reel torque model, component mass-transfer momentum treatment, integrator, and tension equations before implementation.

## Required review question

An aerospace dynamics reviewer must select the intended system boundary: **is v0.2 a prescribed kinematic visualization with an imposed angular-momentum ledger (Option A), or a closed-system constrained dynamics model (Option C)?** Option B and D are mathematically consistent alternatives but conflict with stated v0.2 assumptions. The repository does not contain a requirements decision, hardware model, or independent dynamics evidence sufficient to make that selection responsibly.
