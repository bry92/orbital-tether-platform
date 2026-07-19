# Tether Dynamics

## Purpose

This phase introduces a first-order longitudinal tether dynamics model for the software-only research prototype. It improves on purely kinematic deployment by representing the tether as a damped spring connecting two endpoint masses.

## Mathematical assumptions

- Straight tether with longitudinal motion only.
- Linear stiffness and linear viscous damping.
- Endpoint masses are point masses.
- Relative motion is represented by reduced mass `m_r = m1*m2/(m1+m2)`.
- No flexible-body waves, bending modes, libration coupling, reel motor work, capture shock, electrodynamics, or hardware validation.

## Equations used

Let `x` be extension from equilibrium length and `v = dx/dt`:

- `x_dot = v`
- `v_dot = -(c/m_r)v - (k/m_r)x`
- `T = max(0, kx + cv)`
- `E = 0.5*m_r*v^2 + 0.5*k*x^2`

The non-compressive tension clamp reflects that this simplified tether cannot push.

## Known limitations

The model is not experimentally validated, not flight ready, and not suitable for mission design. It is a conservative oscillator useful for deterministic software verification and early sensitivity studies.

## Future improvements

- Add transverse dynamics and flexible tether modes.
- Add deployment actuator work terms.
- Couple to reviewed libration dynamics without merging architecture layers.
- Add uncertainty bounds and benchmark cases from trusted references.

## Literature context

The mass-spring-damper approximation follows standard introductory structural dynamics practice. Future fidelity increases should be checked against aerospace dynamics references such as *Spacecraft Dynamics and Control* by Wie and *Orbital Mechanics for Engineering Students* by Curtis.
