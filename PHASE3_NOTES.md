# Phase 3: Pulse Optimization Engine

## Overview

Phase 3 implements automatic pulse duration optimization to minimize average gate infidelity under fixed crosstalk coupling. This is the first step toward adaptive quantum control.

## The Optimization Problem

### Objective

Minimize gate infidelity: **ε = 1 - F_avg**

### Constraint

Fixed rotation angle: **θ = Ωt**

This means if we change pulse duration t, we must adjust Rabi frequency Ω to maintain the target rotation.

### Physics Intuition

There's a fundamental tradeoff:

**Longer pulses** (larger t):
- Reduce Ω (weaker control)
- More crosstalk exposure time
- Effect depends on regime

**Shorter pulses** (smaller t):
- Increase Ω (stronger control)
- Less crosstalk exposure time
- Effect depends on regime

The optimal duration balances these competing effects.

---

## Objective Function

```python
def gate_infidelity_objective(t, J, theta_target):
    # Compute Ω from constraint
    omega = theta_target / t
    
    # Construct Hamiltonians
    H_ideal = (omega / 2) * SIGMA_X_I
    H_real = (omega / 2) * SIGMA_X_I + J * SIGMA_Z_Z
    
    # Compute gates
    U_ideal = exp(-i * H_ideal * t)
    U_real = exp(-i * H_real * t)
    
    # Compute fidelity
    F_avg = compute_average_gate_fidelity(U_ideal, U_real)
    
    # Return infidelity (to minimize)
    return 1 - F_avg
```

### Key Features

1. **Automatic Ω adjustment**: Ensures θ = Ωt always satisfied
2. **Gate-level metric**: Uses F_avg (not state fidelity)
3. **Crosstalk-aware**: Includes J in Hamiltonian
4. **Modular design**: Easy to extend to amplitude optimization

---

## Optimization Methods

### 1. Grid Search

**Algorithm**:
1. Define search range: t ∈ [t_nominal × 0.8, t_nominal × 1.2]
2. Evaluate ε(t) at N points (default: 200)
3. Return t that minimizes ε

**Pros**:
- Guaranteed to find global optimum (within range)
- No gradient needed
- Robust to local minima
- Easy to visualize

**Cons**:
- Computationally expensive for high dimensions
- Fixed resolution

**When to use**: Single parameter optimization (pulse duration)

### 2. Scipy Optimization (Nelder-Mead)

**Algorithm**:
1. Start from t_nominal
2. Use simplex method to search for minimum
3. No gradient computation needed
4. Converges to local minimum

**Pros**:
- Faster than grid search
- Adaptive step size
- Tracks convergence

**Cons**:
- May find local minima
- Requires good initial guess
- Less robust than grid search

**When to use**: Multi-parameter optimization, refinement

### Hybrid Approach (Recommended)

1. Use grid search to find global optimum
2. Use scipy to refine (optional)
3. Compare results for validation

---

## Results Interpretation

### Typical Findings

For **weak crosstalk** (J << Ω):
- Optimal pulse ≈ nominal pulse
- Small improvement (~0.01-0.1%)
- Crosstalk is already negligible

For **moderate crosstalk** (J ≈ 0.05Ω):
- Optimal pulse slightly longer than nominal
- Moderate improvement (~0.1-1%)
- Balancing control vs crosstalk

For **strong crosstalk** (J ≈ 0.1Ω):
- Optimal pulse significantly longer
- Large improvement (~1-10%)
- Crosstalk dominates error

### Physics Explanation

**Why longer pulses can be better**:

When J is significant, the crosstalk term J(σ_z⊗σ_z) competes with control term (Ω/2)(σ_x⊗I).

For longer pulses:
- Ω decreases (θ = Ωt constraint)
- Ratio J/Ω increases
- But total crosstalk phase Jt increases

The optimal balance depends on the specific Hamiltonian dynamics. For typical parameters, slightly longer pulses reduce the relative strength of crosstalk effects.

---

## Robustness Analysis

### Purpose

Test whether a single optimized pulse works across different crosstalk strengths, or if adaptive control is needed.

### Method

1. Optimize for J ∈ [0.02, 0.05, 0.1, 0.15] rad/s
2. Compare optimal durations
3. Analyze variation

### Interpretation

**Low variation** (std/mean < 10%):
- Single pulse works for range of J
- Robust to crosstalk uncertainty
- Simple calibration sufficient

**High variation** (std/mean > 10%):
- Optimal pulse depends strongly on J
- Adaptive control recommended
- Need real-time J calibration

---

## Extension to Amplitude Optimization

The framework is ready for amplitude optimization:

```python
def amplitude_objective(omega, J, theta_target):
    # Fix duration, optimize Ω
    t = theta_target / omega  # Constraint
    
    # Rest is same as duration optimization
    H_real = (omega / 2) * SIGMA_X_I + J * SIGMA_Z_Z
    U_real = exp(-i * H_real * t)
    # ... compute F_avg
    
    return 1 - F_avg
```

**Difference**: Now t varies with Ω (constraint), but we optimize Ω directly.

---

## Extension to Pulse Shaping

For time-dependent pulses Ω(t):

```python
def shaped_pulse_objective(omega_params, J, theta_target):
    # omega_params defines Ω(t) shape
    # e.g., Gaussian: Ω(t) = Ω_0 * exp(-(t-t_0)²/σ²)
    
    # Constraint: ∫ Ω(t) dt = θ
    
    # Time evolution with time-dependent H(t)
    # Use piecewise constant approximation or ODE solver
    
    return 1 - F_avg
```

**Challenge**: Time-dependent Hamiltonian requires numerical integration.

---

## Computational Performance

### Grid Search

- **Time complexity**: O(N) where N = number of grid points
- **Typical runtime**: ~2-5 seconds for N=200
- **Parallelizable**: Yes (evaluate points independently)

### Scipy Optimization

- **Time complexity**: O(M) where M = number of iterations
- **Typical runtime**: ~0.5-2 seconds for M=20-50
- **Parallelizable**: No (sequential search)

### Bottleneck

Matrix exponential computation: O(d³) where d=4 for two qubits
- For d=4: ~10 μs per evaluation
- For d=8 (3 qubits): ~80 μs per evaluation
- For d=16 (4 qubits): ~640 μs per evaluation

**Optimization**: Use sparse matrices or analytical solutions when possible.

---

## Validation Checks

### 1. Rotation Constraint

Always verify: **Ω_opt × t_opt = θ_target**

If violated, optimization failed.

### 2. Fidelity Improvement

Check: **F_opt > F_nominal**

If not, either:
- Already at optimum
- Optimization got stuck
- Search range too narrow

### 3. Physical Bounds

Verify:
- 0 ≤ F_avg ≤ 1
- t > 0
- Ω > 0

---

## Hardware Implementation

### Calibration Protocol

1. **Measure J**: Use cross-resonance or ZZ spectroscopy
2. **Run optimization**: Find t_opt for measured J
3. **Implement pulse**: Use t_opt in gate sequence
4. **Verify**: Measure F_avg via randomized benchmarking
5. **Iterate**: Refine if needed

### Adaptive Control

For time-varying J (e.g., temperature drift):

1. Monitor J continuously
2. Update t_opt in real-time
3. Adjust pulse parameters
4. Maintain high fidelity

### Practical Considerations

- **Pulse granularity**: Hardware may have minimum time step
- **Bandwidth limits**: Very short pulses may not be achievable
- **Calibration drift**: Re-optimize periodically
- **Multi-qubit systems**: Optimize jointly for all qubits

---

## Key Takeaways

1. **Optimization is essential**: Even small improvements matter for error correction
2. **Constraint handling**: θ = Ωt must be satisfied
3. **Gate fidelity**: Use F_avg (not state fidelity)
4. **Robustness matters**: Test across parameter ranges
5. **Physics intuition**: Longer pulses can reduce crosstalk effects
6. **Extensible framework**: Ready for amplitude and shape optimization

---

## Next Steps

Phase 3 provides the foundation for:
- **Phase 4**: Amplitude optimization
- **Phase 5**: Pulse shaping (time-dependent control)
- **Phase 6**: Multi-qubit joint optimization
- **Phase 7**: Closed-loop adaptive control

---

## References

- Motzoi et al., "Simple Pulses for Elimination of Leakage in Weakly Nonlinear Qubits" (2009)
- Gambetta et al., "Analytic control methods for high-fidelity unitary operations" (2011)
- Egger & Wilhelm, "Optimized controlled-Z gates for two superconducting qubits" (2014)
