"""
Quantum Pulse Optimization & Crosstalk Simulator (QPOCS)
Phase 1 & 1.5: Single-Qubit Rotation with Timing Jitter Noise

Phase 1: Basic fidelity analysis under timing jitter
Phase 1.5: Robustness & error budget analysis with analytical models

Usage:
    python qpocs_phase1.py              # Run Phase 1 (basic)
    python qpocs_phase1.py --phase 1.5  # Run Phase 1.5 (robustness)
    python qpocs_phase1.py --both       # Run both phases
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from typing import Tuple, Dict
import argparse
from dataclasses import dataclass


# ============================================================================
# Pauli Matrices and Quantum States
# ============================================================================

# Pauli-X matrix (bit-flip operator)
SIGMA_X = np.array([[0, 1], 
                     [1, 0]], dtype=complex)

# Pauli-Z matrix (phase-flip operator)
SIGMA_Z = np.array([[1, 0], 
                     [0, -1]], dtype=complex)

# Initial state |0⟩
STATE_0 = np.array([[1], 
                     [0]], dtype=complex)


# ============================================================================
# Quantum Gate Operations
# ============================================================================

def rotation_gate(theta: float, axis: np.ndarray = SIGMA_X) -> np.ndarray:
    """
    Generate a rotation gate around a specified Pauli axis.
    
    The rotation gate is defined as:
        U(θ) = exp(-i θ σ / 2)
    
    where σ is a Pauli matrix (default: σ_x for X-rotation).
    
    Physics: This implements a rotation in the Bloch sphere representation
    of a qubit. For σ_x, this rotates around the X-axis.
    
    Args:
        theta: Rotation angle in radians
        axis: Pauli matrix defining rotation axis (default: SIGMA_X)
    
    Returns:
        2x2 complex unitary matrix representing the rotation gate
    """
    # Compute the matrix exponential: U = exp(-i θ σ / 2)
    return expm(-1j * theta * axis / 2)


def apply_gate(gate: np.ndarray, state: np.ndarray) -> np.ndarray:
    """
    Apply a quantum gate to a quantum state.
    
    Args:
        gate: 2x2 unitary matrix
        state: 2x1 state vector
    
    Returns:
        Transformed state vector
    """
    return gate @ state


def compute_fidelity(state_ideal: np.ndarray, state_noisy: np.ndarray) -> float:
    """
    Compute quantum state fidelity between ideal and noisy states.
    
    Fidelity is defined as:
        F = |⟨ψ_ideal | ψ_noisy⟩|²
    
    Physics: Fidelity measures how close two quantum states are.
    F = 1 means identical states, F = 0 means orthogonal states.
    
    Args:
        state_ideal: Ideal target state (2x1 vector)
        state_noisy: Actual noisy state (2x1 vector)
    
    Returns:
        Fidelity value between 0 and 1
    """
    # Compute inner product ⟨ψ_ideal | ψ_noisy⟩
    overlap = np.vdot(state_ideal, state_noisy)
    
    # Return squared magnitude
    return np.abs(overlap) ** 2


# ============================================================================
# Data Structures (Phase 1.5)
# ============================================================================

@dataclass
class RobustnessMetrics:
    """Container for hardware-oriented robustness metrics."""
    mean_fidelity: float
    min_fidelity: float
    std_deviation: float
    variance: float
    robustness_score: float
    sensitivity: float
    noise_type: str


# ============================================================================
# Noise Models
# ============================================================================

def generate_jitter_samples(n_samples: int, 
                           uniform_range: Tuple[float, float] = (-0.2, 0.2),
                           gaussian_std: float = 0.05) -> Dict[str, np.ndarray]:
    """
    Generate timing jitter samples from uniform and Gaussian distributions.
    
    Physics: Timing jitter represents uncertainty in pulse duration,
    which translates to rotation angle errors in quantum gates.
    
    Args:
        n_samples: Number of jitter samples to generate
        uniform_range: (min, max) for uniform distribution
        gaussian_std: Standard deviation for Gaussian distribution (mean=0)
    
    Returns:
        Dictionary with 'uniform' and 'gaussian' jitter arrays
    """
    jitter = {
        'uniform': np.random.uniform(uniform_range[0], uniform_range[1], n_samples),
        'gaussian': np.random.normal(0, gaussian_std, n_samples)
    }
    return jitter


# ============================================================================
# Simulation Core
# ============================================================================

def simulate_jitter_fidelity(theta_ideal: float,
                            jitter_values: np.ndarray,
                            initial_state: np.ndarray = STATE_0) -> np.ndarray:
    """
    Simulate fidelity degradation due to timing jitter.
    
    For each jitter value δθ, compute:
        1. Ideal rotation: U(θ_ideal)
        2. Noisy rotation: U(θ_ideal + δθ)
        3. Fidelity between resulting states
    
    Args:
        theta_ideal: Target rotation angle (radians)
        jitter_values: Array of jitter perturbations (radians)
        initial_state: Starting quantum state (default: |0⟩)
    
    Returns:
        Array of fidelity values corresponding to each jitter
    """
    # Compute ideal target state
    U_ideal = rotation_gate(theta_ideal)
    state_ideal = apply_gate(U_ideal, initial_state)
    
    fidelities = np.zeros(len(jitter_values))
    
    for i, delta_theta in enumerate(jitter_values):
        # Apply noisy rotation: θ_noisy = θ_ideal + δθ
        theta_noisy = theta_ideal + delta_theta
        U_noisy = rotation_gate(theta_noisy)
        state_noisy = apply_gate(U_noisy, initial_state)
        
        # Compute fidelity
        fidelities[i] = compute_fidelity(state_ideal, state_noisy)
    
    return fidelities


# ============================================================================
# Analytical Models (Phase 1.5)
# ============================================================================

def analytical_fidelity(delta_theta: np.ndarray) -> np.ndarray:
    """
    Compute analytical fidelity for small rotation errors.
    
    For a rotation gate with error δθ, the fidelity is:
        F_analytical = cos²(δθ / 2)
    
    Physics: This is the exact analytical solution for fidelity degradation
    due to rotation angle errors in single-qubit gates.
    
    Args:
        delta_theta: Array of rotation angle errors (radians)
    
    Returns:
        Array of analytical fidelity values
    """
    return np.cos(delta_theta / 2) ** 2


def compute_infidelity(fidelity: np.ndarray) -> np.ndarray:
    """
    Compute infidelity (error rate) from fidelity.
    
    Infidelity: ε = 1 - F
    
    Physics: Infidelity represents the probability of error in quantum
    operations. Hardware specs often use error rates rather than fidelity.
    
    Args:
        fidelity: Array of fidelity values
    
    Returns:
        Array of infidelity values
    """
    return 1 - fidelity


# ============================================================================
# Sensitivity Analysis (Phase 1.5)
# ============================================================================

def compute_sensitivity(theta_ideal: float, 
                       delta_theta_range: float = 1e-4,
                       n_points: int = 5) -> float:
    """
    Compute fidelity sensitivity to rotation angle errors using finite differences.
    
    Sensitivity: dF/dθ evaluated near δθ = 0
    
    Physics: Measures how rapidly fidelity degrades with small timing errors.
    High sensitivity means the gate is more vulnerable to control noise.
    Critical for error budget allocation in quantum hardware.
    
    Args:
        theta_ideal: Nominal rotation angle
        delta_theta_range: Range for finite difference calculation
        n_points: Number of points for numerical derivative
    
    Returns:
        Sensitivity coefficient dF/dθ at δθ = 0
    """
    # Generate small perturbations around δθ = 0
    delta_theta_vals = np.linspace(-delta_theta_range, delta_theta_range, n_points)
    
    # Compute fidelities
    fidelities = simulate_jitter_fidelity(theta_ideal, delta_theta_vals)
    
    # Numerical derivative using central difference
    h = delta_theta_vals[1] - delta_theta_vals[0]
    sensitivity = np.gradient(fidelities, h)
    
    # Return sensitivity at δθ = 0 (center point)
    center_idx = len(sensitivity) // 2
    return sensitivity[center_idx]


# ============================================================================
# Robustness Scoring (Phase 1.5)
# ============================================================================

def compute_robustness_score(fidelity: np.ndarray) -> float:
    """
    Compute robustness score from fidelity variance.
    
    Robustness: R = 1 / Var(F)
    
    Physics: Quantifies how stable the gate performance is under noise.
    Higher robustness means more consistent fidelity across noise realizations.
    
    Args:
        fidelity: Array of fidelity values
    
    Returns:
        Robustness score (higher is better)
    """
    variance = np.var(fidelity)
    
    # Avoid division by zero
    if variance < 1e-12:
        return np.inf
    
    return 1.0 / variance


def analyze_robustness(fidelity: np.ndarray, 
                       sensitivity: float,
                       noise_type: str) -> RobustnessMetrics:
    """
    Compute comprehensive robustness metrics for hardware characterization.
    
    Args:
        fidelity: Array of fidelity values
        sensitivity: Fidelity sensitivity coefficient
        noise_type: Description of noise model ('Uniform' or 'Gaussian')
    
    Returns:
        RobustnessMetrics dataclass with all metrics
    """
    return RobustnessMetrics(
        mean_fidelity=np.mean(fidelity),
        min_fidelity=np.min(fidelity),
        std_deviation=np.std(fidelity),
        variance=np.var(fidelity),
        robustness_score=compute_robustness_score(fidelity),
        sensitivity=sensitivity,
        noise_type=noise_type
    )


# ============================================================================
# Visualization
# ============================================================================

def plot_results(jitter_uniform: np.ndarray, 
                fidelity_uniform: np.ndarray,
                jitter_gaussian: np.ndarray,
                fidelity_gaussian: np.ndarray) -> None:
    """
    Generate publication-quality plots of simulation results.
    
    Creates two subplots:
        1. Fidelity vs Jitter (scatter plots for both noise models)
        2. Fidelity distribution histograms
    
    Args:
        jitter_uniform: Uniform jitter samples
        fidelity_uniform: Fidelities for uniform jitter
        jitter_gaussian: Gaussian jitter samples
        fidelity_gaussian: Fidelities for Gaussian jitter
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Fidelity vs Jitter
    ax1 = axes[0]
    ax1.scatter(jitter_uniform, fidelity_uniform, alpha=0.6, s=30, 
                label='Uniform Jitter', color='blue')
    ax1.scatter(jitter_gaussian, fidelity_gaussian, alpha=0.6, s=30,
                label='Gaussian Jitter', color='red')
    ax1.set_xlabel('Jitter δθ (radians)', fontsize=12)
    ax1.set_ylabel('Fidelity F', fontsize=12)
    ax1.set_title('Fidelity vs Timing Jitter', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 1.05])
    
    # Plot 2: Fidelity Distribution
    ax2 = axes[1]
    ax2.hist(fidelity_uniform, bins=30, alpha=0.6, label='Uniform Jitter',
             color='blue', edgecolor='black')
    ax2.hist(fidelity_gaussian, bins=30, alpha=0.6, label='Gaussian Jitter',
             color='red', edgecolor='black')
    ax2.set_xlabel('Fidelity F', fontsize=12)
    ax2.set_ylabel('Count', fontsize=12)
    ax2.set_title('Fidelity Distribution', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('qpocs_phase1_results.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✓ Plot saved as 'qpocs_phase1_results.png'")


def print_statistics(fidelity_uniform: np.ndarray, 
                    fidelity_gaussian: np.ndarray) -> None:
    """
    Print statistical summary of simulation results.
    
    Args:
        fidelity_uniform: Fidelities for uniform jitter
        fidelity_gaussian: Fidelities for Gaussian jitter
    """
    print("\n" + "="*60)
    print("SIMULATION STATISTICS")
    print("="*60)
    
    print("\nUniform Jitter:")
    print(f"  Mean Fidelity:   {np.mean(fidelity_uniform):.6f}")
    print(f"  Std Deviation:   {np.std(fidelity_uniform):.6f}")
    print(f"  Min Fidelity:    {np.min(fidelity_uniform):.6f}")
    print(f"  Max Fidelity:    {np.max(fidelity_uniform):.6f}")
    
    print("\nGaussian Jitter:")
    print(f"  Mean Fidelity:   {np.mean(fidelity_gaussian):.6f}")
    print(f"  Std Deviation:   {np.std(fidelity_gaussian):.6f}")
    print(f"  Min Fidelity:    {np.min(fidelity_gaussian):.6f}")
    print(f"  Max Fidelity:    {np.max(fidelity_gaussian):.6f}")
    
    print("\n" + "="*60)


def plot_comprehensive_analysis(jitter_uniform: np.ndarray,
                                fidelity_uniform: np.ndarray,
                                jitter_gaussian: np.ndarray,
                                fidelity_gaussian: np.ndarray) -> None:
    """
    Generate comprehensive robustness analysis plots (Phase 1.5).
    
    Creates 4 subplots:
        1. Fidelity vs Jitter (simulated + analytical)
        2. Infidelity vs Jitter (error rate comparison)
        3. Fidelity Distribution (histogram)
        4. Infidelity Distribution (log scale)
    
    Args:
        jitter_uniform: Uniform jitter samples
        fidelity_uniform: Simulated fidelities for uniform jitter
        jitter_gaussian: Gaussian jitter samples
        fidelity_gaussian: Simulated fidelities for Gaussian jitter
    """
    fig = plt.figure(figsize=(16, 10))
    
    # Compute analytical fidelities
    jitter_sorted_uniform = np.sort(jitter_uniform)
    jitter_sorted_gaussian = np.sort(jitter_gaussian)
    fidelity_analytical_uniform = analytical_fidelity(jitter_sorted_uniform)
    fidelity_analytical_gaussian = analytical_fidelity(jitter_sorted_gaussian)
    
    # Compute infidelities
    infidelity_uniform = compute_infidelity(fidelity_uniform)
    infidelity_gaussian = compute_infidelity(fidelity_gaussian)
    
    # Plot 1: Fidelity vs Jitter (Simulated + Analytical)
    ax1 = plt.subplot(2, 2, 1)
    ax1.scatter(jitter_uniform, fidelity_uniform, alpha=0.5, s=25, 
                label='Simulated (Uniform)', color='blue', marker='o')
    ax1.scatter(jitter_gaussian, fidelity_gaussian, alpha=0.5, s=25,
                label='Simulated (Gaussian)', color='red', marker='s')
    ax1.plot(jitter_sorted_uniform, fidelity_analytical_uniform, 
             'b-', linewidth=2, label='Analytical (Uniform)', alpha=0.8)
    ax1.plot(jitter_sorted_gaussian, fidelity_analytical_gaussian,
             'r-', linewidth=2, label='Analytical (Gaussian)', alpha=0.8)
    ax1.set_xlabel('Jitter δθ (radians)', fontsize=11)
    ax1.set_ylabel('Fidelity F', fontsize=11)
    ax1.set_title('Fidelity vs Timing Jitter\n(Simulated + Analytical)', 
                  fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 1.05])
    
    # Plot 2: Infidelity vs Jitter (Error Rate)
    ax2 = plt.subplot(2, 2, 2)
    ax2.scatter(jitter_uniform, infidelity_uniform, alpha=0.5, s=25,
                label='Uniform Jitter', color='blue', marker='o')
    ax2.scatter(jitter_gaussian, infidelity_gaussian, alpha=0.5, s=25,
                label='Gaussian Jitter', color='red', marker='s')
    ax2.set_xlabel('Jitter δθ (radians)', fontsize=11)
    ax2.set_ylabel('Infidelity ε = 1 - F', fontsize=11)
    ax2.set_title('Infidelity vs Timing Jitter\n(Hardware Error Rate)', 
                  fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, max(np.max(infidelity_uniform), np.max(infidelity_gaussian)) * 1.1])
    
    # Plot 3: Fidelity Distribution
    ax3 = plt.subplot(2, 2, 3)
    ax3.hist(fidelity_uniform, bins=30, alpha=0.6, label='Uniform Jitter',
             color='blue', edgecolor='black', density=True)
    ax3.hist(fidelity_gaussian, bins=30, alpha=0.6, label='Gaussian Jitter',
             color='red', edgecolor='black', density=True)
    ax3.axvline(np.mean(fidelity_uniform), color='blue', linestyle='--', 
                linewidth=2, label=f'Mean (Uniform): {np.mean(fidelity_uniform):.4f}')
    ax3.axvline(np.mean(fidelity_gaussian), color='red', linestyle='--',
                linewidth=2, label=f'Mean (Gaussian): {np.mean(fidelity_gaussian):.4f}')
    ax3.set_xlabel('Fidelity F', fontsize=11)
    ax3.set_ylabel('Probability Density', fontsize=11)
    ax3.set_title('Fidelity Distribution\n(Normalized Histogram)', 
                  fontsize=12, fontweight='bold')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Infidelity Distribution (Log Scale)
    ax4 = plt.subplot(2, 2, 4)
    ax4.hist(infidelity_uniform, bins=30, alpha=0.6, label='Uniform Jitter',
             color='blue', edgecolor='black', density=True)
    ax4.hist(infidelity_gaussian, bins=30, alpha=0.6, label='Gaussian Jitter',
             color='red', edgecolor='black', density=True)
    ax4.set_xlabel('Infidelity ε', fontsize=11)
    ax4.set_ylabel('Probability Density', fontsize=11)
    ax4.set_title('Infidelity Distribution\n(Error Rate Analysis)', 
                  fontsize=12, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.set_yscale('log')
    
    plt.tight_layout()
    plt.savefig('qpocs_phase1_5_robustness.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✓ Robustness analysis plot saved as 'qpocs_phase1_5_robustness.png'")


def print_hardware_summary(metrics_uniform: RobustnessMetrics,
                          metrics_gaussian: RobustnessMetrics) -> None:
    """
    Print hardware-oriented summary report with robustness metrics (Phase 1.5).
    
    Args:
        metrics_uniform: Robustness metrics for uniform jitter
        metrics_gaussian: Robustness metrics for Gaussian jitter
    """
    print("\n" + "="*70)
    print(" " * 15 + "HARDWARE ROBUSTNESS SUMMARY REPORT")
    print("="*70)
    
    # Uniform Jitter Section
    print(f"\n{'UNIFORM JITTER NOISE MODEL':^70}")
    print("-" * 70)
    print(f"  Mean Fidelity:          {metrics_uniform.mean_fidelity:.8f}")
    print(f"  Min Fidelity:           {metrics_uniform.min_fidelity:.8f}")
    print(f"  Std Deviation:          {metrics_uniform.std_deviation:.8f}")
    print(f"  Variance:               {metrics_uniform.variance:.10f}")
    print(f"  Robustness Score (R):   {metrics_uniform.robustness_score:.4f}")
    print(f"  Sensitivity (dF/dθ):    {metrics_uniform.sensitivity:.8f}")
    
    # Gaussian Jitter Section
    print(f"\n{'GAUSSIAN JITTER NOISE MODEL':^70}")
    print("-" * 70)
    print(f"  Mean Fidelity:          {metrics_gaussian.mean_fidelity:.8f}")
    print(f"  Min Fidelity:           {metrics_gaussian.min_fidelity:.8f}")
    print(f"  Std Deviation:          {metrics_gaussian.std_deviation:.8f}")
    print(f"  Variance:               {metrics_gaussian.variance:.10f}")
    print(f"  Robustness Score (R):   {metrics_gaussian.robustness_score:.4f}")
    print(f"  Sensitivity (dF/dθ):    {metrics_gaussian.sensitivity:.8f}")
    
    # Comparative Analysis
    print(f"\n{'COMPARATIVE ANALYSIS':^70}")
    print("-" * 70)
    
    better_fidelity = "Uniform" if metrics_uniform.mean_fidelity > metrics_gaussian.mean_fidelity else "Gaussian"
    better_robustness = "Uniform" if metrics_uniform.robustness_score > metrics_gaussian.robustness_score else "Gaussian"
    
    print(f"  Higher Mean Fidelity:   {better_fidelity}")
    print(f"  Higher Robustness:      {better_robustness}")
    print(f"  Fidelity Difference:    {abs(metrics_uniform.mean_fidelity - metrics_gaussian.mean_fidelity):.8f}")
    print(f"  Robustness Ratio:       {metrics_uniform.robustness_score / metrics_gaussian.robustness_score:.4f}")
    
    # Error Budget Recommendations
    print(f"\n{'ERROR BUDGET RECOMMENDATIONS':^70}")
    print("-" * 70)
    
    avg_sensitivity = (abs(metrics_uniform.sensitivity) + abs(metrics_gaussian.sensitivity)) / 2
    print(f"  Average Sensitivity:    {avg_sensitivity:.8f}")
    print(f"  Recommended δθ Budget:  ±{0.01 / avg_sensitivity if avg_sensitivity > 0 else 0:.6f} rad (for 1% error)")
    
    print("\n" + "="*70)


# ============================================================================
# Main Execution
# ============================================================================

def run_phase1():
    """
    Execute Phase 1 simulation: Single-qubit rotation with timing jitter.
    """
    print("="*60)
    print("QPOCS Phase 1: Single-Qubit Rotation with Timing Jitter")
    print("="*60)
    
    # Simulation parameters
    THETA_IDEAL = np.pi / 2
    N_SAMPLES = 200
    
    print(f"\nSimulation Parameters:")
    print(f"  Ideal rotation angle: π/2 radians")
    print(f"  Number of samples: {N_SAMPLES}")
    print(f"  Uniform jitter range: [-0.2, 0.2] radians")
    print(f"  Gaussian jitter std: 0.05 radians")
    
    # Generate jitter samples
    print("\n[1/4] Generating jitter samples...")
    jitter = generate_jitter_samples(N_SAMPLES)
    
    # Run simulations
    print("[2/4] Simulating uniform jitter...")
    fidelity_uniform = simulate_jitter_fidelity(THETA_IDEAL, jitter['uniform'])
    
    print("[3/4] Simulating Gaussian jitter...")
    fidelity_gaussian = simulate_jitter_fidelity(THETA_IDEAL, jitter['gaussian'])
    
    # Display results
    print_statistics(fidelity_uniform, fidelity_gaussian)
    
    # Generate plots
    print("\n[4/4] Generating plots...")
    plot_results(jitter['uniform'], fidelity_uniform,
                jitter['gaussian'], fidelity_gaussian)
    
    print("\n✓ Phase 1 simulation complete!")


def run_phase1_5():
    """
    Execute Phase 1.5: Robustness & Error Budget Analysis.
    """
    print("="*70)
    print(" " * 10 + "QPOCS Phase 1.5: Robustness & Error Budget Module")
    print("="*70)
    
    # Simulation parameters
    THETA_IDEAL = np.pi / 2
    N_SAMPLES = 200
    
    print(f"\nSimulation Configuration:")
    print(f"  Ideal rotation angle:   π/2 radians")
    print(f"  Number of samples:      {N_SAMPLES}")
    print(f"  Uniform jitter range:   [-0.2, 0.2] radians")
    print(f"  Gaussian jitter std:    0.05 radians")
    
    # Generate jitter samples
    print("\n[1/6] Generating jitter samples...")
    jitter = generate_jitter_samples(N_SAMPLES)
    
    # Run simulations
    print("[2/6] Simulating uniform jitter...")
    fidelity_uniform = simulate_jitter_fidelity(THETA_IDEAL, jitter['uniform'])
    
    print("[3/6] Simulating Gaussian jitter...")
    fidelity_gaussian = simulate_jitter_fidelity(THETA_IDEAL, jitter['gaussian'])
    
    # Sensitivity analysis
    print("[4/6] Computing sensitivity coefficients...")
    sensitivity_uniform = compute_sensitivity(THETA_IDEAL)
    sensitivity_gaussian = compute_sensitivity(THETA_IDEAL)
    
    # Robustness analysis
    print("[5/6] Analyzing robustness metrics...")
    metrics_uniform = analyze_robustness(fidelity_uniform, sensitivity_uniform, "Uniform")
    metrics_gaussian = analyze_robustness(fidelity_gaussian, sensitivity_gaussian, "Gaussian")
    
    # Display hardware summary
    print_hardware_summary(metrics_uniform, metrics_gaussian)
    
    # Generate comprehensive plots
    print("\n[6/6] Generating robustness analysis plots...")
    plot_comprehensive_analysis(jitter['uniform'], fidelity_uniform,
                               jitter['gaussian'], fidelity_gaussian)
    
    print("\n✓ Phase 1.5 robustness analysis complete!")
    print("✓ Ready for Phase 2: 2-qubit Hamiltonian extension")


def main():
    """
    Main entry point with command-line argument parsing.
    """
    parser = argparse.ArgumentParser(
        description='QPOCS: Quantum Pulse Optimization & Crosstalk Simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python qpocs_phase1.py              # Run Phase 1 (basic analysis)
  python qpocs_phase1.py --phase 1.5  # Run Phase 1.5 (robustness analysis)
  python qpocs_phase1.py --both       # Run both phases sequentially
        """
    )
    
    parser.add_argument(
        '--phase',
        type=str,
        choices=['1', '1.5'],
        default='1',
        help='Phase to run: 1 (basic) or 1.5 (robustness)'
    )
    
    parser.add_argument(
        '--both',
        action='store_true',
        help='Run both Phase 1 and Phase 1.5'
    )
    
    args = parser.parse_args()
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    if args.both:
        run_phase1()
        print("\n" + "="*70 + "\n")
        run_phase1_5()
    elif args.phase == '1.5':
        run_phase1_5()
    else:
        run_phase1()


if __name__ == "__main__":
    main()
