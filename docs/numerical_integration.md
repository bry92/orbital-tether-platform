# Numerical Integration

## Purpose

The integration utilities provide deterministic fixed-step methods with a shared interface for the research simulator.

## Mathematical assumptions

- State derivatives are deterministic functions of time and state.
- Fixed time steps are used.
- No adaptive step-size control or certified error bounds are provided.
- The user is responsible for choosing a stable time step for the model stiffness.

## Methods and equations

### Explicit Euler

`y[n+1] = y[n] + dt*f(t[n], y[n])`

- Cost: one derivative evaluation per step.
- Use case: simple smoke tests and highly damped, non-stiff exploratory cases.
- Stability: weakest of the included methods.

### Semi-Implicit Euler

Velocity-like states are updated before position-like states.

- Cost: one acceleration evaluation per step.
- Use case: simple second-order oscillator problems where qualitative energy behavior matters more than local accuracy.
- Stability: often better than explicit Euler for oscillators, but still first order.

### Runge-Kutta 4

Classical four-stage weighted slope average.

- Cost: four derivative evaluations per step.
- Use case: default deterministic research simulations where accuracy matters more than minimal cost.
- Stability: better accuracy for smooth systems, but not a substitute for step-size analysis.

## Known limitations

These utilities are not validated numerical flight software. Stiff systems can still diverge with inappropriate time steps.

## Future improvements

- Add step rejection and adaptive methods for research comparison.
- Add conserved-quantity diagnostics for orbital propagation.
- Add formal convergence tests for selected reference problems.

## Literature context

The methods are standard numerical integration schemes discussed in engineering computation and astrodynamics references such as Curtis's *Orbital Mechanics for Engineering Students*.
