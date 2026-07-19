# Libration

## Purpose

The libration module provides a conservative small-angle oscillator for tether angular displacement studies. It is intended for deterministic research simulations and structured time-series logging, not operational control.

## Mathematical assumptions

- Small-angle approximation: `sin(theta) ≈ theta`.
- Constant orbital rate.
- Linear damping represented by a damping ratio.
- No nonlinear gravity-gradient dynamics, tether flexibility, active control, or validation against flight data.

## Equations used

The simplified small-angle model is:

- `theta_dot = omega`
- `omega_dot = -2*zeta*w*omega - w^2*theta`
- `w = sqrt(3)*n`
- `period = 2*pi/w`

where `n` is the orbital rate and `zeta` is the damping ratio.

## Known limitations

The model is valid only for small displacements and constant-rate idealized studies. It does not represent nonlinear libration, endpoint mass asymmetry effects, attitude coupling, tether slack, or controller behavior.

## Future improvements

- Add nonlinear gravity-gradient equations after verification cases are selected.
- Couple with flexible tether dynamics through explicit interfaces.
- Add energy diagnostics and damping identification workflows.
- Add comparison cases from standard spacecraft dynamics literature.

## Literature context

The small-angle oscillator form is consistent with standard linearization approaches in spacecraft dynamics texts, including Wie's *Spacecraft Dynamics and Control* and Prussing & Conway's *Orbital Mechanics*.
