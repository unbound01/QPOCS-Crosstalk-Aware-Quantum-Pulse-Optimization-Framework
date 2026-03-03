# QPOCS Modular Architecture

## Directory Structure

```
qpocs/
├── core/                   # Core physics modules
│   ├── __init__.py
│   ├── operators.py        # Pauli matrices, tensor products, states
│   ├── hamiltonians.py     # Hamiltonian construction
│   ├── evolution.py        # Time evolution operators
│   └── fidelity.py         # Fidelity metrics
│
├── analysis/               # Analysis modules
│   ├── __init__.py
│   ├── jitter.py           # Jitter analysis (Phase 1 & 1.5)
│   └── crosstalk.py        # Crosstalk analysis (Phase 2 & 2.5)
│
├── optimization/           # Optimization modules
│   ├── __init__.py
│   ├── optimize_1d.py      # 1D optimization (Phase 3)
│   └── optimize_2d.py      # 2D optimization (Phase 3.5)
│
├── experiments/            # Experimental scripts (legacy phases)
│   ├── qpocs_phase1.py     # Original Phase 1 script
│   ├── qpocs_phase2.py     # Original Phase 2 script
│   ├── qpocs_phase3.py     # Original Phase 3 script
│   └── qpocs_phase3_5.py   # Original Phase 3.5 script
│
├── main.py                 # Main entry point
├── requirements.txt        # Dependencies
└── README.md              # Project documentation
```

## Module Organization

### Core (`core/`)

**Purpose**: Fundamental quantum operations and physics calculations

**Modules**:
- `operators.py`: Pauli matrices, tensor products, quantum states
- `hamiltonians.py`: Hamiltonian construction (ideal and with crosstalk)
- `evolution.py`: Time evolution operators, gate application
- `fidelity.py`: State, process, and average gate fidelity metrics

**Key principle**: Pure physics, no plotting or I/O

### Analysis (`analysis/`)

**Purpose**: Jitter and crosstalk analysis functions

**Modules**:
- `jitter.py`: Single-qubit jitter analysis (Phase 1 & 1.5)
  - Jitter sample generation
  - Fidelity simulation
  - Analytical models
  - Sensitivity and robustness metrics

- `crosstalk.py`: Two-qubit crosstalk analysis (Phase 2 & 2.5)
  - Crosstalk simulation
  - Parameter sweeps (J, t, 2D)
  - All fidelity metrics

**Key principle**: Analysis logic, no optimization

### Optimization (`optimization/`)

**Purpose**: Pulse parameter optimization

**Modules**:
- `optimize_1d.py`: 1D optimization (Phase 3)
  - Objective function with θ = Ωt constraint
  - Grid search and scipy optimization
  - Duration optimization

- `optimize_2d.py`: 2D optimization (Phase 3.5)
  - 2D objective function (no constraints)
  - 2D grid search
  - Joint (Ω, t) optimization

**Key principle**: Optimization algorithms, reusable objectives

### Experiments (`experiments/`)

**Purpose**: Legacy standalone scripts (moved from root)

Contains original phase scripts for backward compatibility and reference.

## Usage

### Command-Line Interface

```bash
# Run specific analysis
python main.py jitter          # Jitter analysis
python main.py crosstalk       # Crosstalk analysis
python main.py optimize-1d     # 1D optimization
python main.py optimize-2d     # 2D optimization
python main.py all             # Run everything
```

### Programmatic Usage

```python
# Import core physics
from core import (
    SIGMA_X_I, SIGMA_Z_Z,
    construct_hamiltonian,
    time_evolution_operator,
    compute_average_gate_fidelity
)

# Import analysis functions
from analysis import (
    simulate_crosstalk,
    sweep_coupling_strength
)

# Import optimization
from optimization import (
    optimize_pulse_duration,
    optimize_2d_parameters
)

# Use in your code
result = optimize_pulse_duration(J=0.05, theta_target=np.pi/2)
print(f"Optimal duration: {result['t_optimal']} s")
```

## Design Principles

### 1. Separation of Concerns

- **Physics** (core): Pure quantum mechanics
- **Analysis** (analysis): Simulation and sweeps
- **Optimization** (optimization): Parameter optimization
- **Visualization**: Kept in original scripts or separate

### 2. No Code Duplication

- Common functions in `core/`
- Shared by all modules
- Single source of truth

### 3. Clear Imports

```python
# Good: Explicit imports
from core import compute_average_gate_fidelity

# Avoid: Star imports in production
from core import *  # Only in __init__.py
```

### 4. Modular Objectives

Objective functions are standalone:
```python
# Can be used independently
infidelity = gate_infidelity_objective(t=0.5, J=0.05, theta=np.pi/2)

# Or in optimization
result = optimize_pulse_duration(J=0.05, theta_target=np.pi/2)
```

### 5. Extensibility

Easy to add new features:
- New fidelity metric → `core/fidelity.py`
- New analysis → `analysis/new_analysis.py`
- New optimization → `optimization/optimize_3d.py`

## Migration from Legacy Scripts

### Old Way (Phase Scripts)

```bash
python qpocs_phase1.py
python qpocs_phase2.py
python qpocs_phase3.py
```

### New Way (Modular)

```bash
python main.py jitter
python main.py crosstalk
python main.py optimize-1d
```

### Backward Compatibility

Original scripts moved to `experiments/` and still work:
```bash
python experiments/qpocs_phase1.py  # Still works
```

## Benefits

### For Development

1. **Easier testing**: Test individual modules
2. **Faster iteration**: Change one module without affecting others
3. **Better organization**: Find code quickly
4. **Reduced bugs**: Less duplication = fewer inconsistencies

### For Users

1. **Simpler imports**: `from core import ...`
2. **Flexible usage**: Use only what you need
3. **Clear documentation**: Each module has specific purpose
4. **Extensible**: Easy to add custom analysis

### For Research

1. **Reusable components**: Build new experiments from modules
2. **Reproducible**: Clear separation of physics and analysis
3. **Maintainable**: Easy to update and improve
4. **Collaborative**: Multiple people can work on different modules

## Future Extensions

### Planned Modules

- `core/noise.py`: Noise models (decoherence, dephasing)
- `analysis/benchmarking.py`: Randomized benchmarking
- `optimization/gradient.py`: Gradient-based optimization
- `optimization/ml.py`: Machine learning optimization
- `visualization/`: Plotting utilities

### Integration

- Jupyter notebooks in `notebooks/`
- Tests in `tests/`
- Documentation in `docs/`

## Testing

```bash
# Test individual modules
python -c "from core import *; print('Core OK')"
python -c "from analysis import *; print('Analysis OK')"
python -c "from optimization import *; print('Optimization OK')"

# Run main
python main.py jitter
```

## Summary

The modular architecture provides:
- ✓ Clean separation of concerns
- ✓ No code duplication
- ✓ Easy to test and maintain
- ✓ Extensible for future features
- ✓ Backward compatible with legacy scripts
- ✓ Professional research framework

All existing functionality preserved, now better organized!
