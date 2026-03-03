# Phase 2: Implementation Notes

## Physics Implementation

### Hamiltonian Construction
```
H = (Ω/2)(σ_x ⊗ I) + J(σ_z ⊗ σ_z)
```

- **Control term**: (Ω/2)(σ_x ⊗ I) drives X-rotation on qubit 1
- **Crosstalk term**: J(σ_z ⊗ σ_z) represents ZZ coupling between qubits
- **Factor of 1/2**: Ensures rotation angle θ = Ωt (standard convention)

### Units and Scaling

All quantities use consistent units:
- **Ω (Rabi frequency)**: rad/s
- **J (coupling strength)**: rad/s  
- **t (time)**: seconds
- **θ (angle)**: radians

For π/2 rotation:
- θ = π/2
- t = θ/Ω = (π/2)/Ω
- Verification: Ωt should equal π/2

### Numerical Considerations

1. **Matrix Exponential**: Uses scipy.linalg.expm (stable for Hermitian matrices)
2. **Unitarity**: All evolution operators satisfy U†U = I (verified in validation)
3. **Perturbative Regime**: J << Ω ensures crosstalk is a weak perturbation
4. **Typical Ratio**: J/Ω ≈ 0.05 (5% crosstalk, realistic for superconducting qubits)

## Entanglement Leakage Calculation

Measures unwanted entanglement via reduced density matrix purity:

1. Construct density matrix: ρ = |ψ⟩⟨ψ|
2. Trace out qubit 2: ρ₁ = Tr₂(ρ)
3. Compute purity: P = Tr(ρ₁²)
4. Leakage: L = 1 - P

**Physical Interpretation**:
- L = 0: Pure product state (no entanglement)
- L = 0.5: Maximally entangled (Bell state)
- L ∈ (0, 0.5): Partial entanglement

## Parameter Sweeps

### Coupling Strength (J)
- Range: 0 to 0.2 rad/s
- Shows how crosstalk degrades fidelity
- Identifies J threshold for 99% fidelity

### Pulse Duration (t)
- Range: ±20% around nominal
- Models timing jitter and calibration errors
- Shows sensitivity to pulse length variations

### 2D Landscape
- Explores full (J, t) parameter space
- Identifies optimal operating regions
- Visualizes error budget tradeoffs

## Validation Checks

Run `python validate_phase2.py` to verify:
1. Tensor product dimensions (4×4)
2. State normalization
3. Rotation angle calibration (Ωt = π/2)
4. Unitarity (U†U = I)
5. Zero crosstalk limit (F = 1 at J = 0)
6. Entanglement for product states (L ≈ 0)
7. Entanglement for Bell states (L ≈ 0.5)
8. Hamiltonian Hermiticity (H = H†)

## Expected Results

### Fidelity vs J
- F ≈ 1 at J = 0 (no crosstalk)
- F decreases as J increases
- Approximately quadratic decay for small J

### Fidelity vs t
- Maximum F near nominal t
- Symmetric degradation for ±Δt
- Oscillatory behavior possible for large deviations

### Entanglement Leakage
- Increases with J (stronger coupling → more entanglement)
- Depends on pulse duration (longer pulses → more leakage)
- Should remain < 0.5 (not maximally entangled)

## Troubleshooting

If results look wrong:

1. **Fidelity > 1**: Normalization error (check state vectors)
2. **Fidelity < 0**: Complex phase issue (use |⟨ψ|φ⟩|²)
3. **Non-unitary U**: Hamiltonian not Hermitian (check H = H†)
4. **Ωt ≠ π/2**: Calibration error (verify t = θ/Ω)
5. **Leakage > 0.5**: Calculation error (check partial trace)

## Hardware Relevance

This simulation models:
- **Superconducting qubits**: ZZ coupling from capacitive/inductive crosstalk
- **Ion traps**: Residual spin-spin interactions
- **Neutral atoms**: Rydberg blockade effects

Typical experimental values:
- Ω: 1-100 MHz (2π × 10⁶ to 2π × 10⁸ rad/s)
- J: 10-1000 kHz (2π × 10⁴ to 2π × 10⁶ rad/s)
- J/Ω: 0.01-0.1 (1-10% crosstalk)
