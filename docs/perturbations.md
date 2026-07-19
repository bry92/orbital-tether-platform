# Orbital Perturbations

## Purpose

The perturbation framework exposes independently enabled acceleration models that can be composed by orbital simulations without coupling perturbations to tether dynamics.

## Mathematical assumptions

- Perturbations return acceleration vectors in inertial Cartesian coordinates.
- J2 uses a simplified oblate-primary acceleration expression.
- Atmospheric drag uses constant density and a velocity-opposing ballistic acceleration.
- Solar radiation pressure and third-body effects are documented zero-output placeholders until reviewed models are added.

## Equations used

### J2

The model uses the standard first-order zonal harmonic acceleration form with `mu`, reference radius, and `J2`.

### Drag

`a_drag = -0.5*rho*Cd*A/m*|v|*v`

### Placeholders

Solar radiation pressure and third-body models currently return zero acceleration by design.

## Known limitations

The implemented perturbations are simplified and not flight validated. Constant-density drag is especially limited and should not be used for mission design. No atmosphere model, attitude model, ephemerides, shadowing, or covariance information is included.

## Future improvements

- Add altitude-dependent atmospheric density.
- Add SRP with attitude, reflectivity, and eclipse handling.
- Add third-body terms backed by deterministic ephemeris inputs.
- Add perturbation-specific verification against trusted references.

## Literature context

J2 and drag are standard topics in astrodynamics references such as Vallado's *Fundamentals of Astrodynamics and Applications* and Curtis's *Orbital Mechanics for Engineering Students*.
