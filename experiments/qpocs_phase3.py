"""
Quantum Pulse Optimization & Crosstalk Simulator (QPOCS)
Phase 3: Pulse Optimization Engine

Automatically optimizes pulse duration to minimize average gate infidelity
under fixed crosstalk coupling. Implements grid search and scipy optimization.

Usage:
    python qpocs_phase3.py
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from scipy.optimize import minimize
from typing import Tuple, Dict, List
from dataclasses import dataclass
import time


# ============================================================================
# Import Core Functions from Phase 2
# ============================================================================

# Pauli matrices
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
IDENTITY_2 = np.eye(2, dtype=complex)

# Two-qubit operators
SIGMA_X_I = np.kron(SIGMA_X, IDENTITY_2)
SIGMA_Z_Z = np.kron(SIGMA_Z, SIGMA_Z)
IDENTITY_4 = np.eye(4, dtype=complex)

# Initial state
STATE_00 = np.array([[1], [0], [0], [0]], dtype=complex)


def time_evolution_operator(H: np.ndarray, t: float) -> np.ndarray:
    """Compute U(t) = exp(-iHt)."""
    return expm(-1j * H * t)


def compute_process_fidelity(U_ideal: np.ndarray, U_real: np.ndarray) -> float:
    """Compute process fidelity: F_process = |Tr(U†_ideal U_real)|²/d²."""
    d = U_ideal.shape[0]
    trace_value = np.trace(U_ideal.conj().T @ U_real)
    F_process = np.abs(trace_value) ** 2 / (d ** 2)
    return np.real(F_process)


def compute_average_gate_fidelity(U_ideal: np.ndarray, U_real: np.ndarray) -> float:
    """Compute average gate fidelity: F_avg = (d·F_process + 1)/(d+1)."""
    d = U_ideal.shape[0]
    F_process = compute_process_fidelity(U_ideal, U_real)
    F_avg = (d * F_process + 1) / (d + 1)
    return F_avg


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class OptimizationResult:
    """Container for optimization results."""
    J_coupling: float
    theta_target: float
    t_nominal: float
    t_optimal: float
    omega_nominal: float
    omega_optimal: float
    fidelity_nominal: float
    fidelity_optimal: float
    infidelity_nominal: float
    infidelity_optimal: float
    improvement_percent: float
    infidelity_reduction: float
    method: str
    iterations: int
    computation_time: float


# ============================================================================
# Objective Function
# ============================================================================

def gate_infidelity_objective(t: float, J: float, theta_target: float) -> float:
    """
    Objective function for pulse optimization: gate infidelity ε = 1 - F_avg.
    
    Physics: For a fixed target rotation θ and crosstalk coupling J,
    we optimize the pulse duration t to minimize gate errors.
    
    The key insight: Longer pulses reduce Ω (since θ = Ωt), which reduces
    the control term relative to crosstalk. Shorter pulses increase Ω but
    reduce crosstalk exposure time. There's an optimal balance.
    
    Algorithm:
    1. Compute Ω from constraint: θ = Ωt → Ω = θ/t
    2. Construct Hamiltonian: H = (Ω/2)(σ_x⊗I) + J(σ_z⊗σ_z)
    3. Compute time evolution: U_real = exp(-iHt)
    4. Compute ideal gate (no crosstalk): U_ideal = exp(-i(Ω/2)(σ_x⊗I)t)
    5. Compute average gate fidelity F_avg
    6. Return gate infidelity: ε = 1 - F_avg
    
    Args:
        t: Pulse duration (s)
        J: ZZ coupling strength (rad/s)
        theta_target: Target rotation angle (rad)
    
    Returns:
        Gate infidelity ε = 1 - F_avg (to be minimized)
    """
    # Compute Rabi frequency from constraint θ = Ωt
    omega = theta_target / t
    
    # Construct Hamiltonians
    H_ideal = (omega / 2) * SIGMA_X_I
    H_real = (omega / 2) * SIGMA_X_I + J * SIGMA_Z_Z
    
    # Compute time evolution operators
    U_ideal = time_evolution_operator(H_ideal, t)
    U_real = time_evolution_operator(H_real, t)
    
    # Compute average gate fidelity
    F_avg = compute_average_gate_fidelity(U_ideal, U_real)
    
    # Return gate infidelity (objective to minimize)
    gate_infidelity = 1 - F_avg
    
    return gate_infidelity


# ============================================================================
# Optimization Methods
# ============================================================================

def grid_search_optimization(J: float, theta_target: float, 
                             t_nominal: float, search_range: float = 0.2,
                             n_points: int = 200) -> Tuple[float, np.ndarray, np.ndarray]:
    """
    Perform grid search optimization over pulse duration.
    
    Physics: Exhaustively evaluates gate infidelity over a range of
    pulse durations to find the global optimum. Guaranteed to find
    the best solution within the search range.
    
    Args:
        J: ZZ coupling strength (rad/s)
        theta_target: Target rotation angle (rad)
        t_nominal: Nominal pulse duration (s)
        search_range: Search range as fraction of nominal (default: ±20%)
        n_points: Number of grid points
    
    Returns:
        Tuple of (t_optimal, t_values, infidelities)
    """
    # Define search range
    t_min = t_nominal * (1 - search_range)
    t_max = t_nominal * (1 + search_range)
    t_values = np.linspace(t_min, t_max, n_points)
    
    # Evaluate objective at each point
    infidelities = np.array([gate_infidelity_objective(t, J, theta_target) 
                            for t in t_values])
    
    # Find optimal duration
    idx_optimal = np.argmin(infidelities)
    t_optimal = t_values[idx_optimal]
    
    return t_optimal, t_values, infidelities


def scipy_optimization(J: float, theta_target: float, 
                      t_nominal: float, search_range: float = 0.2) -> Tuple[float, List[float]]:
    """
    Perform optimization using scipy.optimize.minimize.
    
    Physics: Uses gradient-free optimization (Nelder-Mead) to find
    the pulse duration that minimizes gate infidelity. More efficient
    than grid search but may find local minima.
    
    Args:
        J: ZZ coupling strength (rad/s)
        theta_target: Target rotation angle (rad)
        t_nominal: Nominal pulse duration (s)
        search_range: Search range as fraction of nominal
    
    Returns:
        Tuple of (t_optimal, convergence_history)
    """
    # Define bounds
    t_min = t_nominal * (1 - search_range)
    t_max = t_nominal * (1 + search_range)
    bounds = [(t_min, t_max)]
    
    # Track convergence
    convergence_history = []
    
    def callback(xk):
        """Store intermediate results."""
        convergence_history.append(gate_infidelity_objective(xk[0], J, theta_target))
    
    # Run optimization
    result = minimize(
        fun=lambda t: gate_infidelity_objective(t[0], J, theta_target),
        x0=[t_nominal],
        method='Nelder-Mead',
        bounds=bounds,
        callback=callback,
        options={'maxiter': 100, 'xatol': 1e-8}
    )
    
    t_optimal = result.x[0]
    
    return t_optimal, convergence_history



# ============================================================================
# Optimization Execution
# ============================================================================

def optimize_pulse_duration(J: float, theta_target: float, 
                           method: str = 'both') -> OptimizationResult:
    """
    Optimize pulse duration to minimize gate infidelity.
    
    Args:
        J: ZZ coupling strength (rad/s)
        theta_target: Target rotation angle (rad)
        method: 'grid', 'scipy', or 'both' (default)
    
    Returns:
        OptimizationResult dataclass with all metrics
    """
    # Compute nominal parameters
    omega_nominal = np.pi  # Arbitrary choice for nominal
    t_nominal = theta_target / omega_nominal
    
    # Compute nominal fidelity
    infidelity_nominal = gate_infidelity_objective(t_nominal, J, theta_target)
    fidelity_nominal = 1 - infidelity_nominal
    
    # Perform optimization
    start_time = time.time()
    
    if method in ['grid', 'both']:
        t_optimal_grid, t_values, infidelities = grid_search_optimization(
            J, theta_target, t_nominal
        )
        t_optimal = t_optimal_grid
        iterations = len(t_values)
    
    if method in ['scipy', 'both']:
        t_optimal_scipy, convergence = scipy_optimization(
            J, theta_target, t_nominal
        )
        if method == 'scipy':
            t_optimal = t_optimal_scipy
            iterations = len(convergence)
        else:
            # Use grid search result (more reliable)
            t_optimal = t_optimal_grid
            iterations = len(t_values)
    
    computation_time = time.time() - start_time
    
    # Compute optimal parameters
    omega_optimal = theta_target / t_optimal
    infidelity_optimal = gate_infidelity_objective(t_optimal, J, theta_target)
    fidelity_optimal = 1 - infidelity_optimal
    
    # Compute improvements
    improvement_percent = ((fidelity_optimal - fidelity_nominal) / fidelity_nominal) * 100
    infidelity_reduction = infidelity_nominal - infidelity_optimal
    
    return OptimizationResult(
        J_coupling=J,
        theta_target=theta_target,
        t_nominal=t_nominal,
        t_optimal=t_optimal,
        omega_nominal=omega_nominal,
        omega_optimal=omega_optimal,
        fidelity_nominal=fidelity_nominal,
        fidelity_optimal=fidelity_optimal,
        infidelity_nominal=infidelity_nominal,
        infidelity_optimal=infidelity_optimal,
        improvement_percent=improvement_percent,
        infidelity_reduction=infidelity_reduction,
        method=method,
        iterations=iterations,
        computation_time=computation_time
    )


# ============================================================================
# Robustness Analysis
# ============================================================================

def robustness_analysis(J_values: np.ndarray, theta_target: float) -> List[OptimizationResult]:
    """
    Perform optimization for multiple coupling strengths.
    
    Physics: Tests how optimal pulse duration depends on crosstalk strength.
    Reveals whether a single pulse duration can work across different
    coupling regimes or if adaptive control is needed.
    
    Args:
        J_values: Array of coupling strengths to test
        theta_target: Target rotation angle (rad)
    
    Returns:
        List of OptimizationResult objects
    """
    results = []
    
    for J in J_values:
        print(f"  Optimizing for J = {J:.4f} rad/s...")
        result = optimize_pulse_duration(J, theta_target, method='grid')
        results.append(result)
    
    return results


# ============================================================================
# Visualization
# ============================================================================

def plot_optimization_results(result: OptimizationResult, 
                              t_values: np.ndarray, 
                              infidelities: np.ndarray,
                              convergence: List[float] = None) -> None:
    """
    Generate comprehensive optimization visualization.
    
    Creates 2-3 subplots:
        1. Gate infidelity vs pulse duration (with optimal point)
        2. Fidelity vs pulse duration (zoomed view)
        3. Convergence curve (if scipy optimization used)
    """
    n_plots = 3 if convergence else 2
    fig = plt.figure(figsize=(16, 5) if n_plots == 2 else (18, 5))
    
    # ========================================================================
    # Plot 1: Gate Infidelity vs Pulse Duration
    # ========================================================================
    ax1 = plt.subplot(1, n_plots, 1)
    ax1.plot(t_values * 1e6, infidelities, 'b-', linewidth=2, label='Gate Infidelity')
    ax1.scatter([result.t_nominal * 1e6], [result.infidelity_nominal], 
                color='orange', s=150, marker='o', edgecolors='black', linewidths=2,
                label=f'Nominal (ε={result.infidelity_nominal:.6f})', zorder=5)
    ax1.scatter([result.t_optimal * 1e6], [result.infidelity_optimal],
                color='green', s=200, marker='*', edgecolors='black', linewidths=2,
                label=f'Optimal (ε={result.infidelity_optimal:.6f})', zorder=5)
    ax1.set_xlabel('Pulse Duration (μs)', fontsize=11)
    ax1.set_ylabel('Gate Infidelity ε', fontsize=11)
    ax1.set_title(f'Pulse Optimization: J={result.J_coupling:.4f} rad/s\n' +
                  f'Improvement: {result.improvement_percent:.3f}%',
                  fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')
    
    # ========================================================================
    # Plot 2: Fidelity vs Pulse Duration (Zoomed)
    # ========================================================================
    ax2 = plt.subplot(1, n_plots, 2)
    fidelities = 1 - infidelities
    ax2.plot(t_values * 1e6, fidelities, 'b-', linewidth=2, label='Avg Gate Fidelity')
    ax2.scatter([result.t_nominal * 1e6], [result.fidelity_nominal],
                color='orange', s=150, marker='o', edgecolors='black', linewidths=2,
                label=f'Nominal (F={result.fidelity_nominal:.8f})', zorder=5)
    ax2.scatter([result.t_optimal * 1e6], [result.fidelity_optimal],
                color='green', s=200, marker='*', edgecolors='black', linewidths=2,
                label=f'Optimal (F={result.fidelity_optimal:.8f})', zorder=5)
    ax2.axhline(y=0.99, color='gray', linestyle=':', linewidth=1, label='99% threshold')
    ax2.set_xlabel('Pulse Duration (μs)', fontsize=11)
    ax2.set_ylabel('Average Gate Fidelity F_avg', fontsize=11)
    ax2.set_title(f'Fidelity Landscape\n(θ={result.theta_target:.4f} rad)',
                  fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # ========================================================================
    # Plot 3: Convergence Curve (if available)
    # ========================================================================
    if convergence:
        ax3 = plt.subplot(1, n_plots, 3)
        ax3.plot(range(len(convergence)), convergence, 'r-', linewidth=2, marker='o', markersize=4)
        ax3.set_xlabel('Iteration', fontsize=11)
        ax3.set_ylabel('Gate Infidelity ε', fontsize=11)
        ax3.set_title('Optimization Convergence\n(scipy.optimize.minimize)',
                      fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.set_yscale('log')
    
    plt.tight_layout()
    plt.savefig(f'qpocs_phase3_optimization_J{result.J_coupling:.4f}.png', 
                dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"✓ Optimization plot saved as 'qpocs_phase3_optimization_J{result.J_coupling:.4f}.png'")


def plot_robustness_analysis(results: List[OptimizationResult]) -> None:
    """
    Plot optimal pulse duration vs coupling strength.
    
    Shows how the optimal pulse duration changes with crosstalk strength.
    """
    J_values = np.array([r.J_coupling for r in results])
    t_optimal_values = np.array([r.t_optimal for r in results]) * 1e6  # Convert to μs
    t_nominal_values = np.array([r.t_nominal for r in results]) * 1e6
    fidelity_optimal = np.array([r.fidelity_optimal for r in results])
    fidelity_nominal = np.array([r.fidelity_nominal for r in results])
    improvement = np.array([r.improvement_percent for r in results])
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # ========================================================================
    # Plot 1: Optimal Duration vs Coupling Strength
    # ========================================================================
    ax1 = axes[0, 0]
    ax1.plot(J_values, t_optimal_values, 'b-', linewidth=2, marker='o', 
             markersize=8, label='Optimal Duration')
    ax1.plot(J_values, t_nominal_values, 'r--', linewidth=2, 
             label='Nominal Duration')
    ax1.set_xlabel('ZZ Coupling Strength J (rad/s)', fontsize=11)
    ax1.set_ylabel('Pulse Duration (μs)', fontsize=11)
    ax1.set_title('Optimal Pulse Duration vs Coupling\n(Robustness Analysis)',
                  fontsize=12, fontweight='bold')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # ========================================================================
    # Plot 2: Fidelity Comparison
    # ========================================================================
    ax2 = axes[0, 1]
    ax2.plot(J_values, fidelity_optimal, 'g-', linewidth=2, marker='o',
             markersize=8, label='Optimal Fidelity')
    ax2.plot(J_values, fidelity_nominal, 'orange', linestyle='--', linewidth=2,
             marker='s', markersize=6, label='Nominal Fidelity')
    ax2.axhline(y=0.99, color='gray', linestyle=':', linewidth=1, label='99% threshold')
    ax2.set_xlabel('ZZ Coupling Strength J (rad/s)', fontsize=11)
    ax2.set_ylabel('Average Gate Fidelity', fontsize=11)
    ax2.set_title('Fidelity: Optimal vs Nominal\n(Optimization Benefit)',
                  fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # ========================================================================
    # Plot 3: Improvement Percentage
    # ========================================================================
    ax3 = axes[1, 0]
    ax3.bar(J_values, improvement, width=0.01, color='green', alpha=0.7, edgecolor='black')
    ax3.set_xlabel('ZZ Coupling Strength J (rad/s)', fontsize=11)
    ax3.set_ylabel('Fidelity Improvement (%)', fontsize=11)
    ax3.set_title('Optimization Improvement\n(Relative Gain)',
                  fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # ========================================================================
    # Plot 4: Infidelity Reduction
    # ========================================================================
    ax4 = axes[1, 1]
    infidelity_reduction = np.array([r.infidelity_reduction for r in results])
    ax4.semilogy(J_values, infidelity_reduction, 'purple', linewidth=2, 
                 marker='D', markersize=8, label='Infidelity Reduction')
    ax4.set_xlabel('ZZ Coupling Strength J (rad/s)', fontsize=11)
    ax4.set_ylabel('Gate Infidelity Reduction Δε', fontsize=11)
    ax4.set_title('Absolute Error Reduction\n(Δε = ε_nominal - ε_optimal)',
                  fontsize=12, fontweight='bold')
    ax4.legend(fontsize=9)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('qpocs_phase3_robustness.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✓ Robustness analysis plot saved as 'qpocs_phase3_robustness.png'")



# ============================================================================
# Hardware Summary Report
# ============================================================================

def print_optimization_summary(result: OptimizationResult) -> None:
    """
    Print hardware-oriented optimization summary.
    """
    print("\n" + "="*75)
    print(" " * 20 + "PULSE OPTIMIZATION SUMMARY")
    print("="*75)
    
    # System Parameters
    print(f"\n{'SYSTEM PARAMETERS':^75}")
    print("-" * 75)
    print(f"  Target Rotation:           θ = {result.theta_target:.6f} rad (π/2)")
    print(f"  ZZ Coupling Strength:      J = {result.J_coupling:.6f} rad/s")
    print(f"  Optimization Method:       {result.method}")
    print(f"  Iterations:                {result.iterations}")
    print(f"  Computation Time:          {result.computation_time:.4f} s")
    
    # Nominal Parameters
    print(f"\n{'NOMINAL PARAMETERS (BEFORE OPTIMIZATION)':^75}")
    print("-" * 75)
    print(f"  Pulse Duration:            t = {result.t_nominal*1e6:.4f} μs")
    print(f"  Rabi Frequency:            Ω = {result.omega_nominal:.6f} rad/s")
    print(f"  Avg Gate Fidelity:         F_avg = {result.fidelity_nominal:.10f}")
    print(f"  Gate Infidelity:           ε = {result.infidelity_nominal:.10e}")
    
    # Optimal Parameters
    print(f"\n{'OPTIMAL PARAMETERS (AFTER OPTIMIZATION)':^75}")
    print("-" * 75)
    print(f"  Pulse Duration:            t = {result.t_optimal*1e6:.4f} μs")
    print(f"  Rabi Frequency:            Ω = {result.omega_optimal:.6f} rad/s")
    print(f"  Avg Gate Fidelity:         F_avg = {result.fidelity_optimal:.10f}")
    print(f"  Gate Infidelity:           ε = {result.infidelity_optimal:.10e}")
    
    # Improvement Metrics
    print(f"\n{'OPTIMIZATION IMPROVEMENT':^75}")
    print("-" * 75)
    print(f"  Duration Change:           Δt = {(result.t_optimal - result.t_nominal)*1e6:.4f} μs")
    print(f"  Duration Ratio:            t_opt/t_nom = {result.t_optimal/result.t_nominal:.6f}")
    print(f"  Fidelity Improvement:      {result.improvement_percent:.6f}%")
    print(f"  Infidelity Reduction:      Δε = {result.infidelity_reduction:.10e}")
    print(f"  Reduction Factor:          ε_nom/ε_opt = {result.infidelity_nominal/result.infidelity_optimal:.4f}×")
    
    # Physics Interpretation
    print(f"\n{'PHYSICS INTERPRETATION':^75}")
    print("-" * 75)
    
    if result.t_optimal > result.t_nominal:
        print(f"  ✓ Optimal pulse is LONGER than nominal")
        print(f"    → Reduces Ω (weaker control)")
        print(f"    → But crosstalk accumulates over longer time")
        print(f"    → Net effect: Improved fidelity (crosstalk-limited regime)")
    else:
        print(f"  ✓ Optimal pulse is SHORTER than nominal")
        print(f"    → Increases Ω (stronger control)")
        print(f"    → Less crosstalk exposure time")
        print(f"    → Net effect: Improved fidelity (control-limited regime)")
    
    # Validation
    print(f"\n{'VALIDATION':^75}")
    print("-" * 75)
    
    # Check rotation angle
    theta_check_nominal = result.omega_nominal * result.t_nominal
    theta_check_optimal = result.omega_optimal * result.t_optimal
    print(f"  Nominal rotation check:    Ωt = {theta_check_nominal:.6f} rad")
    print(f"  Optimal rotation check:    Ωt = {theta_check_optimal:.6f} rad")
    print(f"  Target rotation:           θ = {result.theta_target:.6f} rad")
    
    if np.isclose(theta_check_optimal, result.theta_target, atol=1e-6):
        print(f"  ✓ Rotation constraint satisfied")
    else:
        print(f"  ⚠ Warning: Rotation constraint violated!")
    
    # Check fidelity improvement
    if result.fidelity_optimal > result.fidelity_nominal:
        print(f"  ✓ Optimization successful (fidelity improved)")
    else:
        print(f"  ⚠ Warning: No improvement found (may be at local optimum)")
    
    print("\n" + "="*75)


def print_robustness_summary(results: List[OptimizationResult]) -> None:
    """
    Print summary of robustness analysis across multiple J values.
    """
    print("\n" + "="*75)
    print(" " * 18 + "ROBUSTNESS ANALYSIS SUMMARY")
    print("="*75)
    
    print(f"\n{'OPTIMIZATION ACROSS COUPLING STRENGTHS':^75}")
    print("-" * 75)
    print(f"  Number of J values tested: {len(results)}")
    print(f"  J range: [{results[0].J_coupling:.4f}, {results[-1].J_coupling:.4f}] rad/s")
    
    print(f"\n{'RESULTS TABLE':^75}")
    print("-" * 75)
    print(f"{'J (rad/s)':>12} {'t_opt (μs)':>12} {'F_opt':>12} {'Improve (%)':>14} {'Δε':>14}")
    print("-" * 75)
    
    for r in results:
        print(f"{r.J_coupling:>12.4f} {r.t_optimal*1e6:>12.4f} {r.fidelity_optimal:>12.8f} "
              f"{r.improvement_percent:>14.6f} {r.infidelity_reduction:>14.6e}")
    
    # Statistics
    print(f"\n{'STATISTICS':^75}")
    print("-" * 75)
    
    improvements = [r.improvement_percent for r in results]
    t_optimal_values = [r.t_optimal * 1e6 for r in results]
    
    print(f"  Mean improvement:          {np.mean(improvements):.6f}%")
    print(f"  Max improvement:           {np.max(improvements):.6f}% (at J={results[np.argmax(improvements)].J_coupling:.4f})")
    print(f"  Min improvement:           {np.min(improvements):.6f}% (at J={results[np.argmin(improvements)].J_coupling:.4f})")
    print(f"  Optimal duration range:    [{np.min(t_optimal_values):.4f}, {np.max(t_optimal_values):.4f}] μs")
    print(f"  Duration variation:        {np.std(t_optimal_values):.4f} μs (std)")
    
    # Recommendations
    print(f"\n{'RECOMMENDATIONS':^75}")
    print("-" * 75)
    
    if np.std(t_optimal_values) / np.mean(t_optimal_values) < 0.1:
        print(f"  ✓ Optimal duration is relatively constant across J values")
        print(f"    → Single optimized pulse can work for range of crosstalk strengths")
        print(f"    → Recommended duration: {np.mean(t_optimal_values):.4f} μs")
    else:
        print(f"  ⚠ Optimal duration varies significantly with J")
        print(f"    → Adaptive pulse control recommended")
        print(f"    → Calibrate J and adjust pulse duration accordingly")
    
    print("\n" + "="*75)


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """
    Execute Phase 3: Pulse Optimization Engine.
    """
    print("="*75)
    print(" " * 15 + "QPOCS Phase 3: Pulse Optimization Engine")
    print("="*75)
    
    # ========================================================================
    # Single Optimization Example
    # ========================================================================
    
    print("\n" + "="*75)
    print("PART 1: SINGLE OPTIMIZATION EXAMPLE")
    print("="*75)
    
    # Parameters
    THETA_TARGET = np.pi / 2
    J_NOMINAL = 0.05  # rad/s
    
    print(f"\nOptimizing pulse duration for:")
    print(f"  Target rotation: θ = π/2 rad")
    print(f"  Coupling strength: J = {J_NOMINAL:.4f} rad/s")
    
    # Run optimization
    print("\n[1/3] Running grid search optimization...")
    result = optimize_pulse_duration(J_NOMINAL, THETA_TARGET, method='both')
    
    # Get detailed data for plotting
    t_nominal = result.t_nominal
    t_optimal_grid, t_values, infidelities = grid_search_optimization(
        J_NOMINAL, THETA_TARGET, t_nominal
    )
    
    # Try scipy optimization for convergence plot
    print("[2/3] Running scipy optimization...")
    t_optimal_scipy, convergence = scipy_optimization(
        J_NOMINAL, THETA_TARGET, t_nominal
    )
    
    # Print summary
    print_optimization_summary(result)
    
    # Generate plots
    print("\n[3/3] Generating optimization plots...")
    plot_optimization_results(result, t_values, infidelities, convergence)
    
    # ========================================================================
    # Robustness Analysis
    # ========================================================================
    
    print("\n" + "="*75)
    print("PART 2: ROBUSTNESS ANALYSIS")
    print("="*75)
    
    # Test multiple J values
    J_VALUES = np.array([0.02, 0.05, 0.1, 0.15])
    
    print(f"\nTesting optimization robustness across J values:")
    print(f"  J = {J_VALUES} rad/s")
    
    print("\n[1/2] Running optimizations...")
    results = robustness_analysis(J_VALUES, THETA_TARGET)
    
    # Print summary
    print_robustness_summary(results)
    
    # Generate plots
    print("\n[2/2] Generating robustness plots...")
    plot_robustness_analysis(results)
    
    # ========================================================================
    # Final Summary
    # ========================================================================
    
    print("\n" + "="*75)
    print("PHASE 3 COMPLETE")
    print("="*75)
    
    print("\nGenerated files:")
    print(f"  📊 qpocs_phase3_optimization_J{J_NOMINAL:.4f}.png")
    print(f"  📊 qpocs_phase3_robustness.png")
    
    print("\nKey findings:")
    print(f"  • Optimal pulse duration: {result.t_optimal*1e6:.4f} μs (vs nominal {result.t_nominal*1e6:.4f} μs)")
    print(f"  • Fidelity improvement: {result.improvement_percent:.6f}%")
    print(f"  • Infidelity reduction: {result.infidelity_reduction:.6e}")
    print(f"  • Optimization is {'robust' if np.std([r.t_optimal for r in results]) / np.mean([r.t_optimal for r in results]) < 0.1 else 'sensitive'} to coupling strength")
    
    print("\n✓ Phase 3 pulse optimization complete!")
    print("✓ Ready for Phase 4: Amplitude optimization and advanced control")


if __name__ == "__main__":
    np.random.seed(42)
    main()
