# QPOCS: Getting Started Guide

## Quick Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run all phases**:
```bash
python run_all_phases.py
```

That's it! You'll get three plots and comprehensive console output.

---

## Running Individual Phases

### Phase 1: Basic Jitter Analysis
```bash
python qpocs_phase1.py
```
**Output**: `qpocs_phase1_results.png` (2 plots)
- Fidelity vs jitter scatter
- Fidelity distribution histogram

**What it does**: Simulates single-qubit rotation errors from timing jitter using uniform and Gaussian noise models.

---

### Phase 1.5: Robustness Analysis
```bash
python qpocs_phase1.py --phase 1.5
```
**Output**: `qpocs_phase1_5_robustness.png` (4 plots)
- Fidelity vs jitter (with analytical overlay)
- Infidelity vs jitter
- Fidelity distribution
- Infidelity distribution (log scale)

**What it does**: Adds analytical models (F = cos²(δθ/2)), sensitivity analysis (dF/dθ), and robustness scoring (R = 1/Var).

---

### Phase 2: Crosstalk Analysis
```bash
python qpocs_phase2.py
```
**Output**: `qpocs_phase2_5_gate_fidelity.png` (6 plots)
- Average gate fidelity vs coupling strength
- Average gate fidelity vs pulse duration
- 2D heatmap: F_avg(J, t)
- Entanglement leakage analysis
- State vs gate fidelity comparison (J sweep)
- State vs gate fidelity comparison (t sweep)

**What it does**: Simulates two-qubit crosstalk during single-qubit control pulses via ZZ coupling. Computes state, process, and average gate fidelities.

---

### Phase 3: Pulse Optimization
```bash
python qpocs_phase3.py
```
**Output**: 
- `qpocs_phase3_optimization_J*.png` (2-3 plots per J value)
- `qpocs_phase3_robustness.png` (4 plots)

**What it does**: Automatically optimizes pulse duration to minimize gate infidelity under fixed crosstalk. Tests robustness across multiple J values.

---

## Validation

### Check Phase 2 Physics
```bash
python validate_phase2.py
```

Verifies:
- ✓ Tensor product dimensions
- ✓ State normalization
- ✓ Rotation calibration (Ωt = π/2)
- ✓ Unitarity (U†U = I)
- ✓ Zero crosstalk limit
- ✓ Entanglement calculations
- ✓ Hamiltonian Hermiticity

---

## Understanding the Output

### Console Output

Each phase prints:
1. **Configuration**: Parameters used (Ω, J, t, θ)
2. **Progress**: Step-by-step execution status
3. **Metrics**: Fidelity, infidelity, robustness scores
4. **Validation**: Physics checks and warnings

### Plots

All plots are publication-quality (300 DPI) with:
- Clear axis labels with units
- Legends explaining each curve
- Grid lines for readability
- Professional color schemes

### Key Metrics

**Fidelity (F)**: How close the actual state is to the ideal state
- F = 1: Perfect (no error)
- F = 0.99: 1% error (typical hardware target)
- F < 0.9: Significant degradation

**Infidelity (ε)**: Error rate = 1 - F
- Hardware specs often use infidelity
- Easier to see small errors (log scale)

**Robustness (R)**: Stability under noise = 1/Var(F)
- Higher R = more consistent performance
- Important for error correction thresholds

**Entanglement Leakage (L)**: Unwanted two-qubit correlations
- L = 0: No entanglement (ideal)
- L = 0.5: Maximally entangled (worst case)
- L < 0.1: Acceptable for most applications

---

## Customization

### Change Parameters

Edit the main() function in each script:

**Phase 1/1.5**:
```python
THETA_IDEAL = np.pi / 2  # Target rotation
N_SAMPLES = 200          # Number of jitter samples
```

**Phase 2**:
```python
OMEGA = np.pi            # Rabi frequency
J_NOMINAL = 0.05         # ZZ coupling strength
THETA_TARGET = np.pi / 2 # Target rotation
```

### Modify Sweeps

**Phase 2 coupling sweep**:
```python
J_VALUES = np.linspace(0, 0.2, 100)  # Change range/resolution
```

**Phase 2 timing sweep**:
```python
T_MIN = T_NOMINAL * 0.8  # Change ±20% to ±X%
T_MAX = T_NOMINAL * 1.2
```

---

## Troubleshooting

### Import Errors
```
ModuleNotFoundError: No module named 'scipy'
```
**Fix**: `pip install -r requirements.txt`

### Plot Not Showing
If plots don't display, they're still saved as PNG files. Check your directory.

### Numerical Warnings
```
RuntimeWarning: invalid value encountered
```
**Cause**: Usually from extreme parameter values
**Fix**: Check that J << Ω (perturbative regime)

### Wrong Fidelity Values
Run validation: `python validate_phase2.py`

If validation fails, check:
1. Rotation angle: Ωt should equal π/2
2. Units: All in rad/s and seconds
3. Hamiltonian: Should be Hermitian (H = H†)

---

## Next Steps

1. **Understand the physics**: Read `PHASE2_NOTES.md`
2. **Modify parameters**: Experiment with different Ω, J, θ values
3. **Add features**: Extend to Phase 3 (multi-qubit optimization)
4. **Compare with experiments**: Use real hardware parameters

---

## File Structure

```
qpocs/
├── qpocs_phase1.py              # Phase 1 & 1.5 (merged)
├── qpocs_phase2.py              # Phase 2 crosstalk
├── validate_phase2.py           # Physics validation
├── run_all_phases.py            # Run everything
├── requirements.txt             # Dependencies
├── README.md                    # Project overview
├── PHASE2_NOTES.md             # Implementation details
└── GETTING_STARTED.md          # This file
```

---

## Questions?

Check the docstrings in the code - every function has detailed physics explanations!

```python
help(construct_hamiltonian)
help(compute_entanglement_leakage)
```
