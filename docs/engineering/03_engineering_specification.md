# Engineering Specification — v0.1

**Document ID:** OTDT-ES-001  
**Revision:** A  
**Date:** 2026-07-16  
**Status:** Active for software prototype only

## 1. Purpose

Specify the physics models, interfaces, verification requirements, and non-goals for the Orbital Tether Digital Twin Platform v0.1.

## 2. Reference frames and constants

| Symbol | Meaning | v0.1 value |
|--------|---------|------------|
| μ | Earth gravitational parameter | `3.986004418e14` m³/s² (WGS-84 conventional) |
| R_E | Earth mean equatorial radius | `6378137.0` m (WGS-84) |
| Frame | Earth-centered inertial (ECI), equatorial | z along Earth rotation axis (unused in planar model) |

**Note:** Constants are configuration inputs. Changing them requires a new experiment ID.

## 3. Spacecraft / system state

### 3.1 Pre-deployment (single body)

State vector in ECI:

\[
\mathbf{x} = [\mathbf{r}, \mathbf{v}, m]
\]

where \(\mathbf{r}, \mathbf{v} \in \mathbb{R}^3\), \(m > 0\).

Circular equatorial orbit initialization:

\[
r = R_E + h,\quad
\mathbf{r} = (r, 0, 0),\quad
\mathbf{v} = (0, \sqrt{\mu/r}, 0)
\]

### 3.2 Post-deployment (dumbbell, rigid, massless tether)

Two point masses \(m_u\) (upper/radial-out), \(m_l\) (lower/radial-in) with:

\[
m_u + m_l = m,\quad L > 0
\]

Center of mass:

\[
\mathbf{r}_{cm} = \frac{m_u \mathbf{r}_u + m_l \mathbf{r}_l}{m}
\]

By construction after deployment, \(\mathbf{r}_{cm}\) equals the pre-deployment \(\mathbf{r}\).

## 4. Orbital mechanics engine

### 4.1 Two-body acceleration

\[
\ddot{\mathbf{r}} = -\mu \frac{\mathbf{r}}{|\mathbf{r}|^3}
\]

### 4.2 Specific energy and angular momentum

\[
\varepsilon = \frac{v^2}{2} - \frac{\mu}{r},\quad
\mathbf{h} = \mathbf{r} \times \mathbf{v}
\]

### 4.3 Propagation (v0.1)

Keplerian two-body propagation via SciPy `solve_ivp` (RK45) on the Cartesian EOMs for verification arcs.

**Limitation:** Not a high-fidelity propagator. Not suitable for long-term ephemeris products.

## 5. Tether dynamics model (v0.1)

### 5.1 Deployment idealization

**Event model:** Instantaneous quasi-static deployment along the local radial unit vector \(\hat{r} = \mathbf{r}_{cm}/|\mathbf{r}_{cm}|\).

Positions:

\[
\mathbf{r}_u = \mathbf{r}_{cm} + \ell_u \hat{r},\quad
\mathbf{r}_l = \mathbf{r}_{cm} - \ell_l \hat{r}
\]

with \(\ell_u + \ell_l = L\) and mass balance:

\[
m_u \ell_u = m_l \ell_l
\]

which yields:

\[
\ell_u = L \frac{m_l}{m},\quad
\ell_l = L \frac{m_u}{m}
\]

### 5.2 Velocity field at deployment

**Default (A-011) — velocity inheritance (verification gate):**

\[
\mathbf{v}_u = \mathbf{v}_l = \mathbf{v}_{cm}
\]

This free instantaneous map conserves angular momentum about Earth:

\[
m_u(\mathbf{r}_u\times\mathbf{v}_{cm}) + m_l(\mathbf{r}_l\times\mathbf{v}_{cm})
= m(\mathbf{r}_{cm}\times\mathbf{v}_{cm})
\]

**Diagnostic only (A-005) — co-rotating / GG-lock kinematics:**

\[
\boldsymbol{\omega} = \frac{\mathbf{r}_{cm} \times \mathbf{v}_{cm}}{|\mathbf{r}_{cm}|^2},\quad
\mathbf{v}_i = \boldsymbol{\omega} \times \mathbf{r}_i
\]

This state does **not** conserve angular momentum relative to the undeployed craft; the excess is approximately \(\omega(m_u\ell_u^2+m_l\ell_l^2)\). It must not be used as a PASS criterion for free-system verification.

**Critical limitation:** Neither map is a dynamic deployment simulation. Real deployment involves Coriolis effects, tether flexibility, residual libration, and control. Expert review required before using tip states for design.

### 5.3 Derived quantities after deployment

For each tip (as if released onto a free Keplerian orbit — informational only):

- Specific energy \(\varepsilon_i\)
- Specific angular momentum \(h_i\)
- Semi-major axis \(a_i = -\mu / (2\varepsilon_i)\) (if \(\varepsilon_i < 0\))
- Radial altitude \(h_i^{alt} = |\mathbf{r}_i| - R_E\)

While tether remains connected, tips are **not** independent Keplerian bodies; free-orbit elements are diagnostic only.

## 6. Scenario runner

Input configuration (JSON-serializable):

```json
{
  "scenario_id": "deploy_radial_v0",
  "earth_mu_m3_s2": 3.986004418e14,
  "earth_radius_m": 6378137.0,
  "spacecraft_mass_kg": 1000.0,
  "orbit_altitude_m": 400000.0,
  "tether_length_m": 10000.0,
  "upper_mass_fraction": 0.5,
  "propagate_seconds": 0.0
}
```

Outputs: experiment record including pre/post states, conservation residuals, assumption IDs.

## 7. Autonomous operations layer (stub)

v0.1 provides **interfaces only**:

- `MissionPlan` dataclass
- `TelemetryFrame` dataclass
- `DecisionLog` append-only log
- `FaultHandler` that records canned responses

No closed-loop control. No ML models. No claim of autonomy maturity.

## 8. Verification system

Every run must produce:

1. Experiment UUID / timestamp
2. Code version / git hash if available
3. Full parameter set
4. Assumption IDs applied
5. Outputs (states, derived elements)
6. Validation check results (pass/fail + residuals)
7. SHA-256 of canonical JSON payload

## 9. Numerical tolerances (v0.1 defaults)

| Check | Relative tolerance | Absolute floor |
|-------|--------------------|----------------|
| Mass conservation | 0 | 0 (exact split) |
| CM position match | 1e-12 | 1e-9 m |
| Angular momentum magnitude | 1e-9 | 1e-6 m²/s (system) |
| Two-body energy (short arc) | 1e-8 | — |

Tolerances are engineering defaults for double-precision unit tests, **not** mission accuracy requirements.

## 10. Safety / ethics of claims

Prohibited statements unless backed by external review:

- “Flight-validated”
- “Ready for orbital demonstration”
- Quantitative commercial throughput / Δv product claims derived solely from this code

## 11. Open items requiring aerospace expert review

See `docs/assumptions/ASSUMPTIONS_REGISTER.md` items marked `EXPERT_REVIEW`.
