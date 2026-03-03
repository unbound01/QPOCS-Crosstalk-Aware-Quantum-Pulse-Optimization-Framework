# Quantum Pulse Optimization & Crosstalk Simulator (QPOCS)

Research-grade simulation framework for quantum gate fidelity under timing jitter and crosstalk.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run analyses via command-line interface
python main.py jitter          # Jitter analysis (Phase 1 & 1.5)
python main.py crosstalk       # Crosstalk analysis (Phase 2 & 2.5)
python main.py optimize-1d     # 1D optimization (Phase 3)
python main.py optimize-2d     # 2D optimization (Phase 3.5)
python main.py all             # Run everything
```

## Modular Architecture

QPOCS uses a clean modular design for research and development:

```
qpocs/
├── core/           # Core physics (operators, Hamiltonians, fidelity)
├── analysis/       # Jitter and crosstalk analysis
├── optimization/   # 1D and 2D pulse optimization
├── experiments/    # Legacy standalone scripts
└── main.py         # Command-line interface
```

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for detailed documentation.

## Programmatic Usage

```python
# Import modules
from core import construct_hamiltonian, compute_average_gate_fidelity
from analysis import simulate_crosstalk
from optimization import optimize_pulse_duration

# Run optimization
result = optimize_pulse_duration(J=0.05, theta_target=np.pi/2)
print(f"Optimal fidelity: {result['fidelity_optimal']:.8f}")
```

## Features by Phase

### Phase 1 & 1.5: Jitter Analysis
- Single-qubit rotation under timing jitter
- Uniform and Gaussian noise models
- Analytical fidelity models
- Sensitivity and robustness metrics

### Phase 2 & 2.5: Crosstalk Analysis
- Two-qubit ZZ coupling crosstalk
- State, process, and average gate fidelity
- Parameter sweeps (J, t, 2D)
- Entanglement leakage measurement

### Phase 3: 1D Optimization
- Optimize pulse duration with θ = Ωt constraint
- Grid search and scipy optimization
- Robustness across coupling strengths

### Phase 3.5: 2D Optimization
- Joint (Ω, t) optimization without constraints
- 2D parameter space exploration
- Rotation angle flexibility

## Legacy Scripts

Original standalone scripts are in `experiments/`:

```bash
python experiments/qpocs_phase1.py       # Phase 1
python experiments/qpocs_phase2.py       # Phase 2 & 2.5
python experiments/qpocs_phase3.py       # Phase 3
python experiments/qpocs_phase3_5.py     # Phase 3.5
```

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Modular design and usage
- **[GETTING_STARTED.md](GETTING_STARTED.md)**: Tutorials and examples
- **[PHASE2_NOTES.md](PHASE2_NOTES.md)**: Phase 2 implementation details
- **[PHASE2_5_NOTES.md](PHASE2_5_NOTES.md)**: Gate fidelity metrics explained
- **[PHASE3_NOTES.md](PHASE3_NOTES.md)**: 1D optimization guide
- **[PHASE3_5_NOTES.md](PHASE3_5_NOTES.md)**: 2D optimization guide

## Requirements

- Python 3.7+
- NumPy >= 1.21.0
- SciPy >= 1.7.0
- Matplotlib >= 3.4.0

## Project Structure

```
qpocs/
├── core/                      # Core physics modules
│   ├── operators.py           # Pauli matrices, tensor products
│   ├── hamiltonians.py        # Hamiltonian construction
│   ├── evolution.py           # Time evolution
│   └── fidelity.py            # Fidelity metrics
│
├── analysis/                  # Analysis modules
│   ├── jitter.py              # Jitter analysis
│   └── crosstalk.py           # Crosstalk analysis
│
├── optimization/              # Optimization modules
│   ├── optimize_1d.py         # 1D optimization
│   └── optimize_2d.py         # 2D optimization
│
├── experiments/               # Legacy scripts
│   ├── qpocs_phase1.py
│   ├── qpocs_phase2.py
│   ├── qpocs_phase3.py
│   └── qpocs_phase3_5.py
│
├── main.py                    # CLI entry point
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## Key Advantages

### Modular Design
- Clean separation of physics, analysis, and optimization
- No code duplication
- Easy to test and maintain

### Reusable Components
- Import only what you need
- Build custom experiments
- Extend with new features

### Research-Ready
- Publication-quality code
- Comprehensive documentation
- Validated physics

## Citation

If you use QPOCS in your research, please cite:

```
@software{qpocs2026,
  title={QPOCS: Quantum Pulse Optimization \& Crosstalk Simulator},
  author={Your Name},
  year={2026},
  url={https://github.com/yourusername/qpocs}
}
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

## Contact

For questions or issues, please open a GitHub issue or contact [your email].
