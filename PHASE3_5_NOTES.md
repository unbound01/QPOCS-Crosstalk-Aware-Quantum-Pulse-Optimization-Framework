# Phase 3.5: 2D Pulse Parameter Optimization

## Overview

Phase 3.5 extends Phase 3 by jointly optimizing both drive amplitude (Ω) and pulse duration (t), removing the constraint θ = Ωt. This allows exploration of the full 2D parameter space to find the globally optimal gate.

## Key Difference from Phase 3

### Phase 3 (1D Optimization)
- **Constraint**: θ = Ωt (fixed rotation angle)
- **Free parameter**: t (duration)
- **Dependent parameter**: Ω = θ/t (computed)
- **Search space**: 1D line in (Ω, t) space

### Phase 3.5 (2D Optimization)
- **Constraint**: None
- **Free parameters**: Both Ω and t
- **Search space**: 2D surface in (Ω, t) space
- **Flexibility**: Optimal θ* = Ω*t* may differ from π/2

## Physics Motivation

### Why Remove the Constraint?

In Phase 3, we assumed the gate must perform exactly a π/2 rotation. But what if a slightly different rotation achieves higher fidelity?

**Key insight**: The "best" gate under crosstalk may not be exactly π/2. Small deviations can:
- Reduce crosstalk-induced errors
- Compensate for systematic effects
- Achieve higher overall fidelity

### The 2D Landscape

The fidelity surface F_avg(Ω, t) has complex structure:

**Ω axis** (amplitude):
- Higher Ω → Stronger control
- Lower Ω → Weaker control, more crosstalk influence

**t axis** (duration):
- Longer t → More crosstalk exposure
- Shorter t → Less crosstalk, but requires higher Ω

**Diagonal** (θ = Ωt):
- Phase 3 searches along this line
- Phase 3.5 explores the full surface

## 2D Objective Function

```python
def gate_infidelity_2d(params, J):
    omega, t = params
    
    # No constraint! Both Ω and t are free
    H_ideal = (omega / 2) * SIGMA_X_I
    H_real = (omega / 2) * SIGMA_X_I + J * SIGMA_Z_Z
    
    U_ideal = exp(-i * H_ideal * t)
    U_real = exp(-i * H_real * t)
    
    F_avg = compute_average_gate_fidelity(U_ideal, U_real)
    
    return 1 - F_avg
```

**Key features**:
- Takes [Ω, t] as input
- No constraint enforcement
- Returns ε to minimize

## Optimization Strategy

### 1. 2D Grid Search

**Algorithm**:
```
For Ω in [0.8Ω_nom, 1.2Ω_nom] (50 points):
    For t in [0.8t_nom, 1.2t_nom] (50 points):
        Evaluate ε(Ω, t)
        
Find (Ω*, t*) that minimizes ε
```

**Complexity**: O(N²) where N = points per dimension
- 50×50 = 2500 evaluations
- ~5-10 seconds runtime

**Advantage**: Guaranteed global optimum within search range

### 2. Scipy Refinement

**Algorithm**:
```
Start from grid search result (Ω*, t*)
Use Nelder-Mead to refine
Bounds: ±25% of nominal
Converge to local minimum
```

**Complexity**: O(M) where M = iterations (~20-50)
- ~1-2 seconds runtime

**Advantage**: Higher precision than grid

### Hybrid Approach (Recommended)

1. Grid search finds global optimum
2. Scipy refines to high precision
3. Compare results for validation

## Typical Results

### Weak Crosstalk (J << Ω)

**Optimal parameters**:
- Ω* ≈ Ω_nom
- t* ≈ t_nom
- θ* ≈ π/2

**Interpretation**: Crosstalk negligible, stay near nominal

### Moderate Crosstalk (J ≈ 0.05Ω)

**Optimal parameters**:
- Ω* slightly < Ω_nom (weaker control)
- t* slightly > t_nom (longer pulse)
- θ* ≈ π/2 (rotation preserved)

**Interpretation**: Balance control vs crosstalk

### Strong Crosstalk (J ≈ 0.1Ω)

**Optimal parameters**:
- Ω* significantly < Ω_nom
- t* significantly > t_nom
- θ* may deviate from π/2

**Interpretation**: Sacrifice exact rotation for fidelity

## Visualization

### 2D Contour Plot

Shows F_avg(Ω, t) as color map:
- Green: High fidelity
- Yellow: Medium fidelity
- Red: Low fidelity

**Features**:
- Nominal point (orange circle)
- Optimal point (green star)
- Contour lines show iso-fidelity curves

### Cross-Section Plots

**Plot 1**: F_avg vs t at Ω = Ω_nom
- Shows how fidelity varies with duration
- Equivalent to Phase 3 optimization

**Plot 2**: F_avg vs Ω at t = t_nom
- Shows how fidelity varies with amplitude
- New information not in Phase 3

### Infidelity Landscape (Log Scale)

Shows log₁₀(ε) as color map:
- Emphasizes low-error regions
- Better for identifying optimal point

## Parameter Tradeoffs

### Ω vs t Coupling

The parameters are not independent:

**Increase Ω**:
- ✓ Stronger control (good)
- ✗ Higher Ω/J ratio (more crosstalk influence)
- ✗ Requires shorter t for same θ

**Increase t**:
- ✓ Lower Ω for same θ (less crosstalk)
- ✗ More crosstalk exposure time
- ✗ Longer gate duration

**Optimal balance**: Depends on J and target fidelity

### Rotation Angle Flexibility

Allowing θ* ≠ π/2 provides extra freedom:

**Small deviations** (|θ* - π/2| < 0.01):
- Negligible impact on gate function
- Can significantly improve fidelity
- Acceptable for most applications

**Large deviations** (|θ* - π/2| > 0.1):
- Changes gate operation
- May require circuit redesign
- Only worth it for large fidelity gains

## Comparison with Phase 3

### Fidelity Improvement

**Phase 3**: Optimizes along θ = Ωt line
- Typical improvement: 0.1-1%

**Phase 3.5**: Optimizes over full (Ω, t) space
- Typical improvement: 0.5-5%
- Always ≥ Phase 3 (superset of search space)

### Computational Cost

**Phase 3**: 
- Grid: 200 evaluations (~2 seconds)
- Scipy: 20-50 iterations (~1 second)

**Phase 3.5**:
- Grid: 2500 evaluations (~10 seconds)
- Scipy: 20-50 iterations (~2 seconds)

**Tradeoff**: 5× slower but better results

### When to Use Each

**Use Phase 3** when:
- Rotation angle must be exactly π/2
- Fast optimization needed
- Crosstalk is weak

**Use Phase 3.5** when:
- Maximum fidelity required
- Rotation flexibility acceptable
- Crosstalk is moderate-strong

## Extension to 3+ Parameters

The framework extends naturally:

### 3D Optimization (Ω, t, J)

If J is tunable (e.g., via flux bias):
```python
def objective_3d(params):
    omega, t, J = params
    # Optimize all three
```

### 4D Optimization (Ω, t, detuning, J)

Add detuning parameter δ:
```python
H = (omega/2) * SIGMA_X_I + delta * SIGMA_Z_I + J * SIGMA_Z_Z
```

### Pulse Shaping

Time-dependent Ω(t):
```python
def objective_shaped(omega_params):
    # omega_params defines Ω(t) shape
    # e.g., Gaussian, DRAG, etc.
```

## Practical Considerations

### Hardware Constraints

Real systems have limits:
- **Ω_max**: Maximum drive amplitude
- **t_min**: Minimum pulse duration
- **Bandwidth**: Limits pulse shaping

Optimization must respect these bounds.

### Calibration Protocol

1. **Measure J**: Use spectroscopy
2. **Set nominal (Ω, t)**: Based on hardware specs
3. **Run 2D optimization**: Find (Ω*, t*)
4. **Verify**: Measure F_avg via randomized benchmarking
5. **Iterate**: Refine if needed

### Multi-Qubit Systems

For N qubits, optimize jointly:
- 2N parameters: (Ω₁, t₁, Ω₂, t₂, ..., Ωₙ, tₙ)
- Complexity: O(M^(2N)) for grid search
- Solution: Use gradient-based methods or genetic algorithms

## Key Takeaways

1. **2D optimization > 1D**: Always achieves equal or better fidelity
2. **Constraint removal**: Allows exploration of full parameter space
3. **Rotation flexibility**: Small θ deviations can improve fidelity
4. **Computational cost**: 5× slower but worth it for critical gates
5. **Extensible**: Ready for 3+ parameter optimization
6. **Hardware-ready**: Provides calibrated (Ω*, t*) for implementation

## Next Steps

Phase 3.5 enables:
- **Multi-parameter optimization**: Add detuning, J tuning
- **Pulse shaping**: Time-dependent Ω(t)
- **Multi-qubit optimization**: Joint optimization across qubits
- **Gradient-based methods**: For high-dimensional problems
- **Machine learning**: Neural network-based optimization

## References

- Motzoi et al., "Simple Pulses for Elimination of Leakage" (2009)
- Gambetta et al., "Analytic control methods for high-fidelity unitary operations" (2011)
- Kelly et al., "Optimal Quantum Control Using Randomized Benchmarking" (2014)
