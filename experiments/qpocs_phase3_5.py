"""
Quantum Pulse Optimization & Crosstalk Simulator (QPOCS)
Phase 3.5: 2D Pulse Parameter Optimization (Ω and t)

Jointly optimizes drive amplitude Ω and pulse duration t to minimize
average gate infidelity under fixed crosstalk coupling. Removes the
constraint θ = Ωt, allowing exploration of full parameter space.

Usage:
    python qpocs_phase3_5.py
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from scipy.optimize import minimize
from typing import Tuple, Dict
from dataclasses import dataclass
import time


# ============================================================================
# Core Quantum Operations
# ============================================================================

SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
IDENTITY_2 = np.eye(2, dtype=complex)

SIGMA_X_I = np.kron(SIGMA_X, IDENTITY_2)
SIGMA_Z_Z = np.kron(SIGMA_Z, SIGMA_Z)
IDENTITY_4 = np.eye(4, dtype=complex)

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
class Optimization2DResult:
    """Container for 2D optimization results."""
    J_coupling: float
    omega_nominal: float
    t_nominal: float
    omega_optimal: float
    t_optimal: float
    theta_nominal: float
    theta_optimal: float
    fidelity_nominal: float
    fidelity_optimal: float
    infidelity_nominal: float
    infidelity_optimal: float
    improvement_percent: float
    infidelity_reduction: float
    reduction_factor: float
    method: str
    grid_points: int
    scipy_iterations: int
    computation_time: float


# ============================================================================
# 2D Objective Function
# ============================================================================

def gate_infidelity_2d(params: np.ndarray, J: float) -> float:
    """
    2D objective function for joint (Ω, t) optimization.
    
    Physics: Unlike Phase 3 where θ = Ωt was constrained, here we
    optimize both Ω and t independently. This allows us to find
    parameter combinations that may not satisfy a specific rotation
    angle but achieve higher fidelity.
    
    Key insight: The "best" gate may not be exactly π/2 rotation.
    Small deviations from π/2 can reduce crosstalk effects while
    still being close enough to the target operation.
    
    Algorithm:
    1. Extract Ω and t from params
    2. Construct Hamiltonians with these parameters
    3. Compute time evolution operators
    4. Compute average gate fidelity
    5. Return gate infidelity
    
    Args:
        params: [Ω, t] array
        J: ZZ coupling strength (rad/s)
    
    Returns:
        Gate infidelity ε = 1 - F_avg
    """
    omega, t = params
    
    # Construct Hamiltonians
    H_ideal = (omega / 2) * SIGMA_X_I
    H_real = (omega / 2) * SIGMA_X_I + J * SIGMA_Z_Z
    
    # Compute time evolution operators
    U_ideal = time_evolution_operator(H_ideal, t)
    U_real = time_evolution_operator(H_real, t)
    
    # Compute average gate fidelity
    F_avg = compute_average_gate_fidelity(U_ideal, U_real)
    
    # Return gate infidelity
    return 1 - F_avg


# ============================================================================
# 2D Grid Search
# ============================================================================

def grid_search_2d(J: float, omega_nominal: float, t_nominal: float,
                   search_range: float = 0.2, n_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Perform 2D grid search over (Ω, t) parameter space.
    
    Physics: Exhaustively evaluates gate infidelity over a 2D grid
    to find the global optimum. This is more expensive than 1D search
    but guarantees finding the best solution within the search range.
    
    Args:
        J: ZZ coupling strength (rad/s)
        omega_nominal: Nominal Rabi frequency (rad/s)
        t_nominal: Nominal pulse duration (s)
        search_range: Search range as fraction of nominal (default: ±20%)
        n_points: Number of grid points per dimension
    
    Returns:
        Tuple of (omega_grid, t_grid, infidelity_grid, optimal_params)
    """
    # Define search ranges
    omega_min = omega_nominal * (1 - search_range)
    omega_max = omega_nominal * (1 + search_range)
    t_min = t_nominal * (1 - search_range)
    t_max = t_nominal * (1 + search_range)
    
    # Create 1D arrays
    omega_values = np.linspace(omega_min, omega_max, n_points)
    t_values = np.linspace(t_min, t_max, n_points)
    
    # Create 2D meshgrid
    omega_grid, t_grid = np.meshgrid(omega_values, t_values)
    
    # Evaluate objective at each grid point
    infidelity_grid = np.zeros_like(omega_grid)
    
    for i in range(n_points):
        for j in range(n_points):
            params = [omega_grid[i, j], t_grid[i, j]]
            infidelity_grid[i, j] = gate_infidelity_2d(params, J)
    
    # Find optimal parameters
    idx_min = np.unravel_index(np.argmin(infidelity_grid), infidelity_grid.shape)
    optimal_params = np.array([omega_grid[idx_min], t_grid[idx_min]])
    
    return omega_grid, t_grid, infidelity_grid, optimal_params



# ============================================================================
# Scipy 2D Optimization
# ============================================================================

def scipy_optimization_2d(J: float, omega_nominal: float, t_nominal: float,
                         initial_guess: np.ndarray = None,
                         search_range: float = 0.25) -> Tuple[np.ndarray, list]:
    """
    Perform 2D optimization using scipy.optimize.minimize.
    
    Physics: Uses gradient-free optimization to refine the solution
    found by grid search. The Nelder-Mead method is robust for
    non-smooth objective functions like gate fidelity.
    
    Args:
        J: ZZ coupling strength (rad/s)
        omega_nominal: Nominal Rabi frequency (rad/s)
        t_nominal: Nominal pulse duration (s)
        initial_guess: Starting point [Ω, t] (if None, uses nominal)
        search_range: Search range as fraction of nominal (default: ±25%)
    
    Returns:
        Tuple of (optimal_params, convergence_history)
    """
    # Set initial guess
    if initial_guess is None:
        initial_guess = np.array([omega_nominal, t_nominal])
    
    # Define bounds
    omega_min = omega_nominal * (1 - search_range)
    omega_max = omega_nominal * (1 + search_range)
    t_min = t_nominal * (1 - search_range)
    t_max = t_nominal * (1 + search_range)
    bounds = [(omega_min, omega_max), (t_min, t_max)]
    
    # Track convergence
    convergence_history = []
    
    def callback(xk):
        """Store intermediate results."""
        convergence_history.append(gate_infidelity_2d(xk, J))
    
    # Run optimization
    result = minimize(
        fun=lambda params: gate_infidelity_2d(params, J),
        x0=initial_guess,
        method='Nelder-Mead',
        bounds=bounds,
        callback=callback,
        options={'maxiter': 200, 'xatol': 1e-8, 'fatol': 1e-10}
    )
    
    optimal_params = result.x
    
    return optimal_params, convergence_history


# ============================================================================
# Full 2D Optimization Pipeline
# ============================================================================

def optimize_2d_parameters(J: float, omega_nominal: float, t_nominal: float,
                          method: str = 'both') -> Optimization2DResult:
    """
    Perform full 2D optimization pipeline: grid search + scipy refinement.
    
    Args:
        J: ZZ coupling strength (rad/s)
        omega_nominal: Nominal Rabi frequency (rad/s)
        t_nominal: Nominal pulse duration (s)
        method: 'grid', 'scipy', or 'both' (default)
    
    Returns:
        Optimization2DResult with all metrics
    """
    start_time = time.time()
    
    # Compute nominal metrics
    params_nominal = np.array([omega_nominal, t_nominal])
    infidelity_nominal = gate_infidelity_2d(params_nominal, J)
    fidelity_nominal = 1 - infidelity_nominal
    theta_nominal = omega_nominal * t_nominal
    
    # Grid search
    print("  [1/2] Running 2D grid search...")
    omega_grid, t_grid, infidelity_grid, params_grid = grid_search_2d(
        J, omega_nominal, t_nominal, search_range=0.2, n_points=50
    )
    grid_points = omega_grid.size
    
    # Scipy refinement
    scipy_iterations = 0
    if method in ['scipy', 'both']:
        print("  [2/2] Refining with scipy optimization...")
        params_scipy, convergence = scipy_optimization_2d(
            J, omega_nominal, t_nominal, 
            initial_guess=params_grid if method == 'both' else None,
            search_range=0.25
        )
        scipy_iterations = len(convergence)
        
        if method == 'scipy':
            params_optimal = params_scipy
        else:
            # Use scipy result (more refined)
            params_optimal = params_scipy
    else:
        params_optimal = params_grid
    
    computation_time = time.time() - start_time
    
    # Extract optimal parameters
    omega_optimal, t_optimal = params_optimal
    
    # Compute optimal metrics
    infidelity_optimal = gate_infidelity_2d(params_optimal, J)
    fidelity_optimal = 1 - infidelity_optimal
    theta_optimal = omega_optimal * t_optimal
    
    # Compute improvements
    improvement_percent = ((fidelity_optimal - fidelity_nominal) / fidelity_nominal) * 100
    infidelity_reduction = infidelity_nominal - infidelity_optimal
    reduction_factor = infidelity_nominal / infidelity_optimal if infidelity_optimal > 0 else np.inf
    
    return Optimization2DResult(
        J_coupling=J,
        omega_nominal=omega_nominal,
        t_nominal=t_nominal,
        omega_optimal=omega_optimal,
        t_optimal=t_optimal,
        theta_nominal=theta_nominal,
        theta_optimal=theta_optimal,
        fidelity_nominal=fidelity_nominal,
        fidelity_optimal=fidelity_optimal,
        infidelity_nominal=infidelity_nominal,
        infidelity_optimal=infidelity_optimal,
        improvement_percent=improvement_percent,
        infidelity_reduction=infidelity_reduction,
        reduction_factor=reduction_factor,
        method=method,
        grid_points=grid_points,
        scipy_iterations=scipy_iterations,
        computation_time=computation_time
    )


# ============================================================================
# Visualization
# ============================================================================

def plot_2d_optimization(result: Optimization2DResult,
                        omega_grid: np.ndarray, t_grid: np.ndarray,
                        infidelity_grid: np.ndarray,
                        convergence: list = None) -> None:
    """
    Generate comprehensive 2D optimization visualization.
    
    Creates 4-5 subplots:
        1. 2D contour plot of F_avg(Ω, t)
        2. Cross-section: F_avg vs t at Ω_nominal
        3. Cross-section: F_avg vs Ω at t_nominal
        4. 2D infidelity contour (log scale)
        5. Convergence curve (if scipy used)
    """
    n_plots = 5 if convergence else 4
    fig = plt.figure(figsize=(18, 10) if n_plots == 4 else (20, 8))
    
    # Convert infidelity to fidelity for plotting
    fidelity_grid = 1 - infidelity_grid
    
    # ========================================================================
    # Plot 1: 2D Fidelity Contour
    # ========================================================================
    ax1 = plt.subplot(2, 3, 1) if n_plots == 5 else plt.subplot(2, 2, 1)
    
    contour = ax1.contourf(omega_grid, t_grid * 1e6, fidelity_grid, 
                           levels=30, cmap='RdYlGn')
    cbar = plt.colorbar(contour, ax=ax1)
    cbar.set_label('Avg Gate Fidelity F_avg', fontsize=10)
    
    # Mark nominal and optimal points
    ax1.scatter([result.omega_nominal], [result.t_nominal * 1e6],
                color='orange', s=200, marker='o', edgecolors='black', linewidths=2,
                label=f'Nominal (F={result.fidelity_nominal:.6f})', zorder=5)
    ax1.scatter([result.omega_optimal], [result.t_optimal * 1e6],
                color='lime', s=300, marker='*', edgecolors='black', linewidths=2,
                label=f'Optimal (F={result.fidelity_optimal:.6f})', zorder=5)
    
    ax1.set_xlabel('Rabi Frequency Ω (rad/s)', fontsize=10)
    ax1.set_ylabel('Pulse Duration t (μs)', fontsize=10)
    ax1.set_title(f'2D Fidelity Landscape\nJ={result.J_coupling:.4f} rad/s',
                  fontsize=11, fontweight='bold')
    ax1.legend(fontsize=8, loc='best')
    ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # ========================================================================
    # Plot 2: Cross-section at Ω_nominal
    # ========================================================================
    ax2 = plt.subplot(2, 3, 2) if n_plots == 5 else plt.subplot(2, 2, 2)
    
    # Find index closest to omega_nominal
    idx_omega = np.argmin(np.abs(omega_grid[0, :] - result.omega_nominal))
    t_slice = t_grid[:, idx_omega] * 1e6
    fidelity_slice = fidelity_grid[:, idx_omega]
    
    ax2.plot(t_slice, fidelity_slice, 'b-', linewidth=2, label=f'F_avg at Ω={result.omega_nominal:.3f}')
    ax2.scatter([result.t_nominal * 1e6], [result.fidelity_nominal],
                color='orange', s=150, marker='o', edgecolors='black', linewidths=2,
                label='Nominal', zorder=5)
    
    # Mark optimal if close to this Ω
    if np.abs(result.omega_optimal - result.omega_nominal) / result.omega_nominal < 0.05:
        ax2.scatter([result.t_optimal * 1e6], [result.fidelity_optimal],
                    color='lime', s=200, marker='*', edgecolors='black', linewidths=2,
                    label='Optimal', zorder=5)
    
    ax2.axhline(y=0.99, color='gray', linestyle=':', linewidth=1, label='99% threshold')
    ax2.set_xlabel('Pulse Duration t (μs)', fontsize=10)
    ax2.set_ylabel('Avg Gate Fidelity F_avg', fontsize=10)
    ax2.set_title('Cross-Section: F_avg vs t\n(at nominal Ω)',
                  fontsize=11, fontweight='bold')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # ========================================================================
    # Plot 3: Cross-section at t_nominal
    # ========================================================================
    ax3 = plt.subplot(2, 3, 3) if n_plots == 5 else plt.subplot(2, 2, 3)
    
    # Find index closest to t_nominal
    idx_t = np.argmin(np.abs(t_grid[:, 0] - result.t_nominal))
    omega_slice = omega_grid[idx_t, :]
    fidelity_slice_omega = fidelity_grid[idx_t, :]
    
    ax3.plot(omega_slice, fidelity_slice_omega, 'r-', linewidth=2, 
             label=f'F_avg at t={result.t_nominal*1e6:.2f} μs')
    ax3.scatter([result.omega_nominal], [result.fidelity_nominal],
                color='orange', s=150, marker='o', edgecolors='black', linewidths=2,
                label='Nominal', zorder=5)
    
    # Mark optimal if close to this t
    if np.abs(result.t_optimal - result.t_nominal) / result.t_nominal < 0.05:
        ax3.scatter([result.omega_optimal], [result.fidelity_optimal],
                    color='lime', s=200, marker='*', edgecolors='black', linewidths=2,
                    label='Optimal', zorder=5)
    
    ax3.axhline(y=0.99, color='gray', linestyle=':', linewidth=1, label='99% threshold')
    ax3.set_xlabel('Rabi Frequency Ω (rad/s)', fontsize=10)
    ax3.set_ylabel('Avg Gate Fidelity F_avg', fontsize=10)
    ax3.set_title('Cross-Section: F_avg vs Ω\n(at nominal t)',
                  fontsize=11, fontweight='bold')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # ========================================================================
    # Plot 4: 2D Infidelity Contour (Log Scale)
    # ========================================================================
    ax4 = plt.subplot(2, 3, 4) if n_plots == 5 else plt.subplot(2, 2, 4)
    
    # Use log scale for infidelity
    infidelity_log = np.log10(infidelity_grid + 1e-12)  # Add small value to avoid log(0)
    
    contour_inf = ax4.contourf(omega_grid, t_grid * 1e6, infidelity_log,
                               levels=30, cmap='RdYlGn_r')
    cbar_inf = plt.colorbar(contour_inf, ax=ax4)
    cbar_inf.set_label('log₁₀(Gate Infidelity ε)', fontsize=10)
    
    ax4.scatter([result.omega_nominal], [result.t_nominal * 1e6],
                color='orange', s=200, marker='o', edgecolors='black', linewidths=2,
                label='Nominal', zorder=5)
    ax4.scatter([result.omega_optimal], [result.t_optimal * 1e6],
                color='lime', s=300, marker='*', edgecolors='black', linewidths=2,
                label='Optimal', zorder=5)
    
    ax4.set_xlabel('Rabi Frequency Ω (rad/s)', fontsize=10)
    ax4.set_ylabel('Pulse Duration t (μs)', fontsize=10)
    ax4.set_title('2D Infidelity Landscape (Log Scale)\n(Lower is Better)',
                  fontsize=11, fontweight='bold')
    ax4.legend(fontsize=8, loc='best')
    ax4.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # ========================================================================
    # Plot 5: Convergence Curve (if available)
    # ========================================================================
    if convergence and n_plots == 5:
        ax5 = plt.subplot(2, 3, 5)
        ax5.semilogy(range(len(convergence)), convergence, 'purple', 
                     linewidth=2, marker='o', markersize=4)
        ax5.set_xlabel('Iteration', fontsize=10)
        ax5.set_ylabel('Gate Infidelity ε', fontsize=10)
        ax5.set_title('Scipy Optimization Convergence\n(Nelder-Mead)',
                      fontsize=11, fontweight='bold')
        ax5.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'qpocs_phase3_5_2d_optimization_J{result.J_coupling:.4f}.png',
                dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"✓ 2D optimization plot saved as 'qpocs_phase3_5_2d_optimization_J{result.J_coupling:.4f}.png'")



# ============================================================================
# Hardware Calibration Summary
# ============================================================================

def print_calibration_summary(result: Optimization2DResult) -> None:
    """
    Print hardware-oriented calibration summary for 2D optimization.
    """
    print("\n" + "="*80)
    print(" " * 25 + "2D PULSE CALIBRATION SUMMARY")
    print("="*80)
    
    # System Parameters
    print(f"\n{'SYSTEM PARAMETERS':^80}")
    print("-" * 80)
    print(f"  ZZ Coupling Strength:        J = {result.J_coupling:.6f} rad/s")
    print(f"  Optimization Method:         {result.method}")
    print(f"  Grid Points:                 {result.grid_points} ({int(np.sqrt(result.grid_points))}×{int(np.sqrt(result.grid_points))})")
    print(f"  Scipy Iterations:            {result.scipy_iterations}")
    print(f"  Computation Time:            {result.computation_time:.4f} s")
    
    # Nominal Parameters
    print(f"\n{'NOMINAL PARAMETERS (BEFORE OPTIMIZATION)':^80}")
    print("-" * 80)
    print(f"  Rabi Frequency:              Ω = {result.omega_nominal:.6f} rad/s")
    print(f"  Pulse Duration:              t = {result.t_nominal*1e6:.4f} μs")
    print(f"  Rotation Angle:              θ = Ωt = {result.theta_nominal:.6f} rad")
    print(f"  Target (π/2):                π/2 = {np.pi/2:.6f} rad")
    print(f"  Rotation Error:              |θ - π/2| = {abs(result.theta_nominal - np.pi/2):.6e} rad")
    print(f"  Avg Gate Fidelity:           F_avg = {result.fidelity_nominal:.10f}")
    print(f"  Gate Infidelity:             ε = {result.infidelity_nominal:.10e}")
    
    # Optimal Parameters
    print(f"\n{'OPTIMAL PARAMETERS (AFTER OPTIMIZATION)':^80}")
    print("-" * 80)
    print(f"  Rabi Frequency:              Ω* = {result.omega_optimal:.6f} rad/s")
    print(f"  Pulse Duration:              t* = {result.t_optimal*1e6:.4f} μs")
    print(f"  Rotation Angle:              θ* = Ω*t* = {result.theta_optimal:.6f} rad")
    print(f"  Target (π/2):                π/2 = {np.pi/2:.6f} rad")
    print(f"  Rotation Error:              |θ* - π/2| = {abs(result.theta_optimal - np.pi/2):.6e} rad")
    print(f"  Avg Gate Fidelity:           F_avg* = {result.fidelity_optimal:.10f}")
    print(f"  Gate Infidelity:             ε* = {result.infidelity_optimal:.10e}")
    
    # Parameter Changes
    print(f"\n{'PARAMETER CHANGES':^80}")
    print("-" * 80)
    delta_omega = result.omega_optimal - result.omega_nominal
    delta_t = result.t_optimal - result.t_nominal
    delta_theta = result.theta_optimal - result.theta_nominal
    
    print(f"  ΔΩ = Ω* - Ω:                 {delta_omega:+.6f} rad/s ({delta_omega/result.omega_nominal*100:+.3f}%)")
    print(f"  Δt = t* - t:                 {delta_t*1e6:+.4f} μs ({delta_t/result.t_nominal*100:+.3f}%)")
    print(f"  Δθ = θ* - θ:                 {delta_theta:+.6f} rad ({delta_theta/result.theta_nominal*100:+.3f}%)")
    print(f"  Ω*/Ω ratio:                  {result.omega_optimal/result.omega_nominal:.6f}")
    print(f"  t*/t ratio:                  {result.t_optimal/result.t_nominal:.6f}")
    
    # Improvement Metrics
    print(f"\n{'OPTIMIZATION IMPROVEMENT':^80}")
    print("-" * 80)
    print(f"  Fidelity Improvement:        {result.improvement_percent:.8f}%")
    print(f"  Absolute Infidelity Reduction: Δε = {result.infidelity_reduction:.10e}")
    print(f"  Relative Infidelity Reduction: ε/ε* = {result.reduction_factor:.4f}×")
    print(f"  Error Suppression:           {(1 - 1/result.reduction_factor)*100:.4f}%")
    
    # Physics Interpretation
    print(f"\n{'PHYSICS INTERPRETATION':^80}")
    print("-" * 80)
    
    # Analyze parameter changes
    if abs(delta_omega) / result.omega_nominal > 0.01:
        if delta_omega > 0:
            print(f"  ✓ Optimal Ω is HIGHER than nominal (+{abs(delta_omega/result.omega_nominal)*100:.2f}%)")
            print(f"    → Stronger control field")
        else:
            print(f"  ✓ Optimal Ω is LOWER than nominal (-{abs(delta_omega/result.omega_nominal)*100:.2f}%)")
            print(f"    → Weaker control field")
    else:
        print(f"  ✓ Optimal Ω ≈ nominal (change < 1%)")
    
    if abs(delta_t) / result.t_nominal > 0.01:
        if delta_t > 0:
            print(f"  ✓ Optimal t is LONGER than nominal (+{abs(delta_t/result.t_nominal)*100:.2f}%)")
            print(f"    → More crosstalk exposure time")
        else:
            print(f"  ✓ Optimal t is SHORTER than nominal (-{abs(delta_t/result.t_nominal)*100:.2f}%)")
            print(f"    → Less crosstalk exposure time")
    else:
        print(f"  ✓ Optimal t ≈ nominal (change < 1%)")
    
    # Rotation angle analysis
    if abs(delta_theta) / result.theta_nominal > 0.01:
        print(f"\n  ⚠ Optimal rotation deviates from nominal by {abs(delta_theta/result.theta_nominal)*100:.2f}%")
        print(f"    → Sacrificing exact π/2 rotation for higher fidelity")
        print(f"    → Net effect: {result.improvement_percent:.4f}% fidelity improvement")
    else:
        print(f"\n  ✓ Optimal rotation ≈ nominal (θ* ≈ θ)")
        print(f"    → Maintaining target rotation while improving fidelity")
    
    # Validation
    print(f"\n{'VALIDATION':^80}")
    print("-" * 80)
    
    # Check if optimization improved fidelity
    if result.fidelity_optimal > result.fidelity_nominal:
        print(f"  ✓ Optimization successful (F_avg improved by {result.improvement_percent:.6f}%)")
    else:
        print(f"  ⚠ Warning: No improvement (may be at local optimum)")
    
    # Check if parameters are within reasonable bounds
    if 0.8 <= result.omega_optimal/result.omega_nominal <= 1.2:
        print(f"  ✓ Optimal Ω within ±20% of nominal")
    else:
        print(f"  ⚠ Warning: Optimal Ω outside ±20% range")
    
    if 0.8 <= result.t_optimal/result.t_nominal <= 1.2:
        print(f"  ✓ Optimal t within ±20% of nominal")
    else:
        print(f"  ⚠ Warning: Optimal t outside ±20% range")
    
    # Check rotation angle
    if abs(result.theta_optimal - np.pi/2) < 0.1:
        print(f"  ✓ Optimal rotation close to π/2 (within 0.1 rad)")
    else:
        print(f"  ⚠ Note: Optimal rotation deviates from π/2 by {abs(result.theta_optimal - np.pi/2):.4f} rad")
    
    print("\n" + "="*80)


def save_optimization_report(result: Optimization2DResult, filename: str = None) -> None:
    """
    Save optimization results to text file.
    
    Args:
        result: Optimization2DResult object
        filename: Output filename (default: auto-generated)
    """
    if filename is None:
        filename = f'qpocs_phase3_5_report_J{result.J_coupling:.4f}.txt'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write(" " * 20 + "QPOCS PHASE 3.5: 2D OPTIMIZATION REPORT\n")
        f.write("="*80 + "\n\n")
        
        f.write("SYSTEM PARAMETERS\n")
        f.write("-" * 80 + "\n")
        f.write(f"ZZ Coupling Strength:        J = {result.J_coupling:.6f} rad/s\n")
        f.write(f"Optimization Method:         {result.method}\n")
        f.write(f"Grid Points:                 {result.grid_points}\n")
        f.write(f"Scipy Iterations:            {result.scipy_iterations}\n")
        f.write(f"Computation Time:            {result.computation_time:.4f} s\n\n")
        
        f.write("NOMINAL PARAMETERS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Rabi Frequency:              Ω = {result.omega_nominal:.6f} rad/s\n")
        f.write(f"Pulse Duration:              t = {result.t_nominal*1e6:.4f} μs\n")
        f.write(f"Rotation Angle:              θ = {result.theta_nominal:.6f} rad\n")
        f.write(f"Avg Gate Fidelity:           F_avg = {result.fidelity_nominal:.10f}\n")
        f.write(f"Gate Infidelity:             ε = {result.infidelity_nominal:.10e}\n\n")
        
        f.write("OPTIMAL PARAMETERS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Rabi Frequency:              Ω* = {result.omega_optimal:.6f} rad/s\n")
        f.write(f"Pulse Duration:              t* = {result.t_optimal*1e6:.4f} μs\n")
        f.write(f"Rotation Angle:              θ* = {result.theta_optimal:.6f} rad\n")
        f.write(f"Avg Gate Fidelity:           F_avg* = {result.fidelity_optimal:.10f}\n")
        f.write(f"Gate Infidelity:             ε* = {result.infidelity_optimal:.10e}\n\n")
        
        f.write("IMPROVEMENT METRICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Fidelity Improvement:        {result.improvement_percent:.8f}%\n")
        f.write(f"Infidelity Reduction:        Δε = {result.infidelity_reduction:.10e}\n")
        f.write(f"Reduction Factor:            ε/ε* = {result.reduction_factor:.4f}×\n\n")
        
        f.write("="*80 + "\n")
    
    print(f"✓ Optimization report saved as '{filename}'")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """
    Execute Phase 3.5: 2D Pulse Parameter Optimization.
    """
    print("="*80)
    print(" " * 20 + "QPOCS Phase 3.5: 2D Parameter Optimization")
    print("="*80)
    
    # ========================================================================
    # Configuration
    # ========================================================================
    
    # Fixed parameters
    J = 0.05  # rad/s (ZZ coupling strength)
    
    # Nominal parameters (approximately π/2 rotation)
    OMEGA_NOMINAL = np.pi  # rad/s
    T_NOMINAL = 0.5  # s (gives θ ≈ π/2)
    
    print(f"\nOptimization Configuration:")
    print(f"  Fixed coupling:       J = {J:.6f} rad/s")
    print(f"  Nominal Ω:            {OMEGA_NOMINAL:.6f} rad/s")
    print(f"  Nominal t:            {T_NOMINAL*1e6:.4f} μs")
    print(f"  Nominal θ:            {OMEGA_NOMINAL * T_NOMINAL:.6f} rad (≈ π/2 = {np.pi/2:.6f})")
    print(f"  Search range:         ±20% (grid), ±25% (scipy)")
    
    # ========================================================================
    # Run 2D Optimization
    # ========================================================================
    
    print(f"\nRunning 2D optimization...")
    result = optimize_2d_parameters(J, OMEGA_NOMINAL, T_NOMINAL, method='both')
    
    # Get grid data for plotting
    print("\nRegenerating grid for visualization...")
    omega_grid, t_grid, infidelity_grid, _ = grid_search_2d(
        J, OMEGA_NOMINAL, T_NOMINAL, search_range=0.2, n_points=50
    )
    
    # Get convergence data
    _, convergence = scipy_optimization_2d(
        J, OMEGA_NOMINAL, T_NOMINAL,
        initial_guess=np.array([result.omega_optimal, result.t_optimal]),
        search_range=0.25
    )
    
    # ========================================================================
    # Display Results
    # ========================================================================
    
    print_calibration_summary(result)
    
    # ========================================================================
    # Generate Visualizations
    # ========================================================================
    
    print("\nGenerating 2D optimization plots...")
    plot_2d_optimization(result, omega_grid, t_grid, infidelity_grid, convergence)
    
    # ========================================================================
    # Save Report
    # ========================================================================
    
    print("\nSaving optimization report...")
    save_optimization_report(result)
    
    # ========================================================================
    # Summary
    # ========================================================================
    
    print("\n" + "="*80)
    print("PHASE 3.5 COMPLETE")
    print("="*80)
    
    print("\nKey Results:")
    print(f"  • Optimal Ω: {result.omega_optimal:.6f} rad/s (vs nominal {result.omega_nominal:.6f})")
    print(f"  • Optimal t: {result.t_optimal*1e6:.4f} μs (vs nominal {result.t_nominal*1e6:.4f})")
    print(f"  • Optimal θ: {result.theta_optimal:.6f} rad (vs π/2 = {np.pi/2:.6f})")
    print(f"  • Fidelity improvement: {result.improvement_percent:.6f}%")
    print(f"  • Infidelity reduction: {result.reduction_factor:.4f}×")
    
    print("\nGenerated Files:")
    print(f"  📊 qpocs_phase3_5_2d_optimization_J{J:.4f}.png")
    print(f"  📄 qpocs_phase3_5_report_J{J:.4f}.txt")
    
    print("\n✓ Phase 3.5 complete!")
    print("✓ 2D optimization removes θ = Ωt constraint")
    print("✓ Explores full (Ω, t) parameter space for optimal fidelity")


if __name__ == "__main__":
    np.random.seed(42)
    main()
