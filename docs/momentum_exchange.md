# Momentum Exchange Research Module

## Status and claim boundary

This module is part of a **software-only research prototype**. It is **not** flight software, **not** a validated mission model, **not** a certified aerospace system, and **not** a commercial product claim.

The first implementation provides deterministic bookkeeping for a simplified two-endpoint tether. It does **not** validate momentum-exchange catch, throw, capture, or operational concepts.

## Purpose

The module supports early research simulations for:

- configurable tether length;
- configurable endpoint masses;
- center-of-mass calculations;
- angular-momentum bookkeeping;
- energy bookkeeping;
- deployment and retraction event records; and
- deterministic simulation logging.

## Assumptions

1. The tether is straight, rigid, and massless.
2. Endpoint bodies are point masses.
3. Endpoint velocities are inherited from the center-of-mass velocity unless a caller constructs endpoint states directly.
4. Length changes are kinematic bookkeeping events.
5. No actuator work, flexible dynamics, structural loads, collision risk, capture shock, electrodynamic forces, or external torques are modeled.
6. All quantities use SI units and inertial Cartesian vectors.

## Equations used

For endpoint masses `m_i`, positions `r_i`, and velocities `v_i`:

- Total mass: `M = sum(m_i)`
- Center of mass: `r_cm = sum(m_i r_i) / M`
- Center-of-mass velocity: `v_cm = sum(m_i v_i) / M`
- Angular momentum about the inertial origin: `H = sum(m_i (r_i x v_i))`
- Kinetic energy: `K = 0.5 m dot(v, v)`
- Optional central-body potential energy: `U = -mu m / norm(r)`

## Limitations

The implementation does not include flexible tether dynamics, electrodynamic tether modeling, momentum-exchange operations, libration control, AI decision-making, hardware integration, or flight validation. Conservation statements are limited to the modeled assumptions and numerical tolerances covered by tests.

## Future improvements

- Add reviewed flexible tether dynamics.
- Add explicit deployment actuator work terms.
- Add frame metadata and unit validation.
- Add uncertainty propagation and scenario provenance integration.
- Compare selected cases with trusted analytical or published references before expanding claim boundaries.

## Placeholder interfaces

Future work should keep these capabilities separated from the physics bookkeeping layer and raise `NotImplementedError` until reviewed implementations exist:

- `FlexibleTetherModel`
- `ElectrodynamicTetherModel`
- `LibrationController`
- `AutonomousMissionPlanner`
- `CollisionAvoidance`
- `DigitalTwin`
- `StructuralHealthMonitor`
