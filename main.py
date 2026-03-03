"""
QPOCS Main Entry Point

Quantum Pulse Optimization & Crosstalk Simulator

Usage:
    python main.py jitter          # Run jitter analysis
    python main.py crosstalk       # Run crosstalk analysis
    python main.py optimize-1d     # Run 1D optimization
    python main.py optimize-2d     # Run 2D optimization
    python main.py all             # Run all analyses
"""

import sys
import numpy as np
import argparse


def run_jitter_analysis():
    """Run Phase 1 & 1.5: Jitter analysis."""
    print("="*70)
    print(" " * 20 + "JITTER ANALYSIS")
    print("="*70)
    
    from analysis import (
        generate_jitter_samples,
        simulate_jitter_fidelity,
        analytical_fidelity,
        compute_sensitivity,
        compute_robustness_score
    )
    
    # Parameters
    THETA_IDEAL = np.pi / 2
    N_SAMPLES = 200
    
    print(f"\nParameters:")
    print(f"  Target rotation: θ = π/2 rad")
    print(f"  Samples: {N_SAMPLES}")
    
    # Generate jitter
    print("\n[1/3] Generating jitter samples...")
    jitter = generate_jitter_samples(N_SAMPLES)
    
    # Simulate
    print("[2/3] Simulating fidelity degradation...")
    fidelity_uniform = simulate_jitter_fidelity(THETA_IDEAL, jitter['uniform'])
    fidelity_gaussian = simulate_jitter_fidelity(THETA_IDEAL, jitter['gaussian'])
    
    # Compute metrics
    print("[3/3] Computing robustness metrics...")
    sensitivity = compute_sensitivity(THETA_IDEAL)
    robustness_uniform = compute_robustness_score(fidelity_uniform)
    robustness_gaussian = compute_robustness_score(fidelity_gaussian)
    
    # Results
    print(f"\nResults:")
    print(f"  Uniform - Mean fidelity: {np.mean(fidelity_uniform):.6f}")
    print(f"  Uniform - Robustness: {robustness_uniform:.4f}")
    print(f"  Gaussian - Mean fidelity: {np.mean(fidelity_gaussian):.6f}")
    print(f"  Gaussian - Robustness: {robustness_gaussian:.4f}")
    print(f"  Sensitivity: {sensitivity:.8f}")
    
    print("\n✓ Jitter analysis complete!")


def run_crosstalk_analysis():
    """Run Phase 2 & 2.5: Crosstalk analysis."""
    print("="*70)
    print(" " * 20 + "CROSSTALK ANALYSIS")
    print("="*70)
    
    from analysis import (
        simulate_crosstalk,
        sweep_coupling_strength,
        sweep_pulse_duration
    )
    
    # Parameters
    OMEGA = np.pi
    T_NOMINAL = 0.5
    J_NOMINAL = 0.05
    
    print(f"\nParameters:")
    print(f"  Rabi frequency: Ω = {OMEGA:.6f} rad/s")
    print(f"  Pulse duration: t = {T_NOMINAL:.6f} s")
    print(f"  ZZ coupling: J = {J_NOMINAL:.6f} rad/s")
    
    # Single point
    print("\n[1/3] Simulating nominal parameters...")
    _, _, _, _, fidelities = simulate_crosstalk(OMEGA, J_NOMINAL, T_NOMINAL)
    
    print(f"  State fidelity: {fidelities['state']:.8f}")
    print(f"  Process fidelity: {fidelities['process']:.8f}")
    print(f"  Avg gate fidelity: {fidelities['average_gate']:.8f}")
    
    # Sweep J
    print("[2/3] Sweeping coupling strength...")
    J_values = np.linspace(0, 0.2, 50)
    results_J = sweep_coupling_strength(OMEGA, T_NOMINAL, J_values)
    
    print(f"  Min fidelity: {np.min(results_J['average_gate_fidelity']):.8f}")
    print(f"  Max fidelity: {np.max(results_J['average_gate_fidelity']):.8f}")
    
    # Sweep t
    print("[3/3] Sweeping pulse duration...")
    t_values = np.linspace(T_NOMINAL * 0.8, T_NOMINAL * 1.2, 50)
    results_t = sweep_pulse_duration(OMEGA, J_NOMINAL, t_values)
    
    print(f"  Min fidelity: {np.min(results_t['average_gate_fidelity']):.8f}")
    print(f"  Max fidelity: {np.max(results_t['average_gate_fidelity']):.8f}")
    
    print("\n✓ Crosstalk analysis complete!")


def run_1d_optimization():
    """Run Phase 3: 1D pulse optimization."""
    print("="*70)
    print(" " * 20 + "1D PULSE OPTIMIZATION")
    print("="*70)
    
    from optimization import optimize_pulse_duration
    
    # Parameters
    J = 0.05
    THETA_TARGET = np.pi / 2
    
    print(f"\nParameters:")
    print(f"  ZZ coupling: J = {J:.6f} rad/s")
    print(f"  Target rotation: θ = π/2 rad")
    
    # Optimize
    print("\n[1/1] Running optimization...")
    result = optimize_pulse_duration(J, THETA_TARGET, method='both')
    
    # Results
    print(f"\nResults:")
    print(f"  Nominal duration: {result['t_nominal']*1e6:.4f} μs")
    print(f"  Optimal duration: {result['t_optimal']*1e6:.4f} μs")
    print(f"  Nominal fidelity: {result['fidelity_nominal']:.8f}")
    print(f"  Optimal fidelity: {result['fidelity_optimal']:.8f}")
    print(f"  Improvement: {result['improvement_percent']:.6f}%")
    
    print("\n✓ 1D optimization complete!")


def run_2d_optimization():
    """Run Phase 3.5: 2D parameter optimization."""
    print("="*70)
    print(" " * 20 + "2D PARAMETER OPTIMIZATION")
    print("="*70)
    
    from optimization import optimize_2d_parameters
    
    # Parameters
    J = 0.05
    OMEGA_NOMINAL = np.pi
    T_NOMINAL = 0.5
    
    print(f"\nParameters:")
    print(f"  ZZ coupling: J = {J:.6f} rad/s")
    print(f"  Nominal Ω: {OMEGA_NOMINAL:.6f} rad/s")
    print(f"  Nominal t: {T_NOMINAL:.6f} s")
    
    # Optimize
    print("\n[1/1] Running 2D optimization...")
    result = optimize_2d_parameters(J, OMEGA_NOMINAL, T_NOMINAL, method='both')
    
    # Results
    print(f"\nResults:")
    print(f"  Nominal Ω: {result['omega_nominal']:.6f} rad/s")
    print(f"  Optimal Ω: {result['omega_optimal']:.6f} rad/s")
    print(f"  Nominal t: {result['t_nominal']*1e6:.4f} μs")
    print(f"  Optimal t: {result['t_optimal']*1e6:.4f} μs")
    print(f"  Nominal θ: {result['theta_nominal']:.6f} rad")
    print(f"  Optimal θ: {result['theta_optimal']:.6f} rad")
    print(f"  Nominal fidelity: {result['fidelity_nominal']:.8f}")
    print(f"  Optimal fidelity: {result['fidelity_optimal']:.8f}")
    print(f"  Improvement: {result['improvement_percent']:.6f}%")
    
    print("\n✓ 2D optimization complete!")


def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(
        description='QPOCS: Quantum Pulse Optimization & Crosstalk Simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py jitter          # Run jitter analysis
  python main.py crosstalk       # Run crosstalk analysis  
  python main.py optimize-1d     # Run 1D optimization
  python main.py optimize-2d     # Run 2D optimization
  python main.py all             # Run all analyses
        """
    )
    
    parser.add_argument(
        'mode',
        choices=['jitter', 'crosstalk', 'optimize-1d', 'optimize-2d', 'all'],
        help='Analysis mode to run'
    )
    
    args = parser.parse_args()
    
    # Set random seed
    np.random.seed(42)
    
    # Run requested analysis
    if args.mode == 'jitter':
        run_jitter_analysis()
    elif args.mode == 'crosstalk':
        run_crosstalk_analysis()
    elif args.mode == 'optimize-1d':
        run_1d_optimization()
    elif args.mode == 'optimize-2d':
        run_2d_optimization()
    elif args.mode == 'all':
        run_jitter_analysis()
        print("\n" + "="*70 + "\n")
        run_crosstalk_analysis()
        print("\n" + "="*70 + "\n")
        run_1d_optimization()
        print("\n" + "="*70 + "\n")
        run_2d_optimization()
    
    print("\n" + "="*70)
    print("QPOCS ANALYSIS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
