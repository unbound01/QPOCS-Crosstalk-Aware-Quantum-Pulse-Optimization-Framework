# Phase 2.5: Process & Average Gate Fidelity

## Overview

Phase 2.5 upgrades the crosstalk simulation from state-based fidelity to full gate-level characterization using process fidelity and average gate fidelity.

## Fidelity Metrics Explained

### 1. State Fidelity (F_state)

```
F_state = |⟨ψ_ideal | ψ_real⟩|²
```

**What it measures**: Overlap between two quantum states

**Pros**:
- Simple and intuitive
- Easy to compute
- Direct physical meaning

**Cons**:
- Depends on initial state |ψ⟩
- Different inputs give different fidelities
- Not a complete gate characterization

**When to use**: Quick checks for specific input states

---

### 2. Process Fidelity (F_process)

```
F_process = |Tr(U†_ideal U_real)|² / d²
```

where d is the Hilbert space dimension (d=4 for two qubits).

**What it measures**: Average fidelity over all possible input states, weighted by the Haar measure

**Pros**:
- Independent of input state
- Complete gate characterization
- Basis-independent (unitary invariant)
- Theoretical gold standard

**Cons**:
- Less intuitive than state fidelity
- Not directly measurable experimentally
- Requires full gate tomography

**When to use**: Theoretical analysis and gate comparison

---

### 3. Average Gate Fidelity (F_avg)

```
F_avg = (d · F_process + 1) / (d + 1)
```

For two qubits (d=4):
```
F_avg = (4 · F_process + 1) / 5
```

**What it measures**: Average state fidelity over all pure input states (Haar measure)

**Pros**:
- State-independent like F_process
- More intuitive (closer to state fidelity)
- Directly measurable via randomized benchmarking
- Standard metric in experimental quantum computing

**Cons**:
- Slightly more complex formula
- Requires understanding of Haar measure

**When to use**: Hardware characterization and benchmarking (PREFERRED)

---

## Relationship Between Metrics

For **high fidelity** (F > 0.9):
```
F_state ≈ F_avg ≈ F_process
```

For **two qubits** (d=4):
```
F_avg = 0.8 · F_process + 0.2
```

This means:
- If F_process = 1.0, then F_avg = 1.0
- If F_process = 0.9, then F_avg = 0.92
- F_avg is always slightly higher than F_process

---

## Implementation Details

### Process Fidelity Calculation

```python
def compute_process_fidelity(U_ideal, U_real):
    d = U_ideal.shape[0]  # Hilbert space dimension
    trace_value = np.trace(U_ideal.conj().T @ U_real)
    F_process = np.abs(trace_value) ** 2 / (d ** 2)
    return np.real(F_process)
```

**Key steps**:
1. Compute U†_ideal @ U_real
2. Take trace
3. Square absolute value
4. Normalize by d²

**Why it works**: The trace measures the average overlap between the gates across all basis states.

### Average Gate Fidelity Calculation

```python
def compute_average_gate_fidelity(U_ideal, U_real):
    d = U_ideal.shape[0]
    F_process = compute_process_fidelity(U_ideal, U_real)
    F_avg = (d * F_process + 1) / (d + 1)
    return F_avg
```

**Derivation**: This formula comes from averaging state fidelity over the Haar measure on pure states.

---

## Why Gate Fidelity Matters

### State Fidelity Limitations

Consider a gate that works perfectly on |00⟩ but fails on |11⟩:
- State fidelity with |00⟩: F_state = 1.0 ✓
- State fidelity with |11⟩: F_state = 0.0 ✗
- Average gate fidelity: F_avg ≈ 0.5 (reveals the problem!)

**Lesson**: State fidelity can be misleading. Always use gate fidelity for hardware characterization.

### Hardware Benchmarking

Real quantum computers report:
- **Gate infidelity**: ε_gate = 1 - F_avg
- Typical values: ε_gate = 10⁻³ to 10⁻² (0.1% to 1% error)
- Threshold for error correction: ε_gate < 10⁻³

---

## Experimental Measurement

### Randomized Benchmarking

Average gate fidelity can be measured without full tomography:

1. Apply random sequence of gates
2. Measure survival probability
3. Fit exponential decay
4. Extract F_avg from decay rate

**Formula**: 
```
P_survival(m) = A · p^m + B
where p = 1 - (d-1)ε_gate/d
```

For two qubits (d=4):
```
p = 1 - 0.75 · ε_gate
```

---

## Phase 2.5 Enhancements

### New Features

1. **Dual Fidelity Tracking**: Compute both state and gate fidelities
2. **Comparison Plots**: Visualize deviation between metrics
3. **Gate Infidelity**: Report ε_gate = 1 - F_avg
4. **Hardware Summary**: Professional gate characterization report

### Updated Sweeps

All parameter sweeps now compute:
- State fidelity (for comparison)
- Process fidelity (theoretical)
- Average gate fidelity (experimental standard)
- Gate infidelity (error rate)
- Entanglement leakage (crosstalk measure)

### Visualization

New plots show:
- State vs gate fidelity comparison
- Deviation |F_state - F_avg|
- All metrics on same graph for easy comparison

---

## Extension to 3+ Qubits

The formulas generalize naturally:

**For d = 2^n qubits**:
```
F_process = |Tr(U†_ideal U_real)|² / d²
F_avg = (d · F_process + 1) / (d + 1)
```

**Examples**:
- 1 qubit (d=2): F_avg = (2F_p + 1)/3
- 2 qubits (d=4): F_avg = (4F_p + 1)/5
- 3 qubits (d=8): F_avg = (8F_p + 1)/9

**Code is ready**: Just change Hilbert space dimension!

---

## Key Takeaways

1. **State fidelity**: Quick check, but input-dependent
2. **Process fidelity**: Theoretical gold standard, state-independent
3. **Average gate fidelity**: Experimental standard, directly measurable
4. **Use F_avg for hardware**: It's what real quantum computers report
5. **High fidelity regime**: All three metrics agree (F > 0.9)
6. **Low fidelity regime**: Metrics can differ significantly

---

## References

- Nielsen & Chuang, "Quantum Computation and Quantum Information" (2010)
- Knill et al., "Randomized Benchmarking of Quantum Gates" (2008)
- Emerson et al., "Scalable noise estimation with random unitary operators" (2005)
