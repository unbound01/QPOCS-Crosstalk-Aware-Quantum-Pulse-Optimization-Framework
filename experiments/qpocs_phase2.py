"""
Quantum Pulse Optimization & Crosstalk Simulator (QPOCS)
Phase 2: Dynamic Two-Qubit Crosstalk During Active Pulse

Simulates crosstalk effects during single-qubit control pulses via ZZ coupling.
Models realistic hardware scenario where control on one qubit induces unwanted
entanglement with neighboring qubits.

Usage:
    python qpocs_phase2.py
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.linalg import expm
from typing import Tuple, Dict
from dataclasses import dataclass


# ============================================================================
# Single-Qubit Pauli Matrices
# ============================================================================

SIGMA_X = np.array([[0, 1], 
                     [1, 0]], dtype=complex)

SIGMA_Z = np.array([[1, 0], 
                     [0, -1]], dtype=complex)

IDENTITY_2 = np.eye(2, dtype=complex)


# ============================================================================
# Two-Qubit Operators (Tensor Products)
# ============================================================================

def tensor_product(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Compute tensor product (Kronecker product) of two matrices.
    
    Physics: Tensor products construct operators for composite quantum systems.
    For two qubits, the Hilbert space is H₁ ⊗ H₂ (dimension 2×2 = 4).
    
    Args:
        A: First matrix (typically 2×2)
        B: Second matrix (typically 2×2)
    
    Returns:
        Tensor product A ⊗ B (typically 4×4 for two qubits)
    """
    return np.kron(A, B)


# Two-qubit operators
SIGMA_X_I = tensor_product(SIGMA_X, IDENTITY_2)  # σ_x ⊗ I (acts on qubit 1)
SIGMA_Z_Z = tensor_product(SIGMA_Z, SIGMA_Z)     # σ_z ⊗ σ_z (ZZ coupling)
IDENTITY_4 = np.eye(4, dtype=complex)            # 4×4 identity


# ============================================================================
# Quantum States
# ============================================================================

# Computational basis states for two qubits
STATE_00 = np.array([[1], [0], [0], [0]], dtype=complex)  # |00⟩
STATE_01 = np.array([[0], [1], [0], [0]], dtype=complex)  # |01⟩
STATE_10 = np.array([[0], [0], [1], [0]], dtype=complex)  # |10⟩
STATE_11 = np.array([[0], [0], [0], [1]], dtype=complex)  # |11⟩


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class CrosstalkMetrics:
    """Container for crosstalk analysis metrics."""
    state_fidelity: float
    process_fidelity: float
    average_gate_fidelity: float
    gate_infidelity: float
    entanglement_leakage: float
    J_coupling: float
    pulse_duration: float



# ============================================================================
# Hamiltonian Construction
# ============================================================================

def construct_hamiltonian(omega: float, J: float) -> np.ndarray:
    """
    Construct two-qubit Hamiltonian with control and crosstalk terms.
    
    H = (Ω/2)(σ_x ⊗ I) + J(σ_z ⊗ σ_z)
    
    Physics:
    - First term: Single-qubit X-rotation on qubit 1 (control pulse)
    - Second term: ZZ coupling (crosstalk between qubits)
    
    The factor Ω/2 ensures that for time t, the rotation angle is θ = Ωt.
    J represents the strength of unwanted ZZ interaction during the pulse.
    
    Args:
        omega: Rabi frequency of control pulse (rad/s)
        J: ZZ coupling strength (rad/s)
    
    Returns:
        4×4 Hamiltonian matrix
    """
    H_control = (omega / 2) * SIGMA_X_I
    H_crosstalk = J * SIGMA_Z_Z
    return H_control + H_crosstalk


def time_evolution_operator(H: np.ndarray, t: float) -> np.ndarray:
    """
    Compute time evolution operator U(t) = exp(-iHt).
    
    Physics: Solves the Schrödinger equation for time-independent Hamiltonian.
    The unitary operator U(t) evolves quantum states: |ψ(t)⟩ = U(t)|ψ(0)⟩
    
    Args:
        H: Hamiltonian matrix
        t: Evolution time
    
    Returns:
        Unitary time evolution operator
    """
    return expm(-1j * H * t)


# ============================================================================
# Fidelity and Entanglement Measures
# ============================================================================

def compute_state_fidelity(state_ideal: np.ndarray, state_real: np.ndarray) -> float:
    """
    Compute quantum state fidelity: F = |⟨ψ_ideal | ψ_real⟩|²
    
    Physics: Measures overlap between two pure quantum states.
    This is the most basic fidelity measure, but only applies to
    specific input states. For full gate characterization, use
    process fidelity or average gate fidelity instead.
    
    Args:
        state_ideal: Target state vector
        state_real: Actual state vector
    
    Returns:
        State fidelity (0 to 1)
    """
    overlap = np.vdot(state_ideal, state_real)
    return np.abs(overlap) ** 2


def compute_process_fidelity(U_ideal: np.ndarray, U_real: np.ndarray) -> float:
    """
    Compute process fidelity between two unitary operators.
    
    F_process = |Tr(U_ideal† @ U_real)|² / d²
    
    Physics: Process fidelity measures how close two quantum operations
    (gates) are, independent of the input state. It's the average fidelity
    over all possible input states, weighted by the Haar measure.
    
    Unlike state fidelity (which depends on initial state), process fidelity
    characterizes the gate itself. This is the standard metric for gate
    quality in quantum computing hardware.
    
    Key properties:
    - F_process = 1: Perfect gate (U_real = U_ideal up to global phase)
    - F_process = 0: Maximally different gates
    - Independent of input state choice
    - Basis-independent (unitary invariant)
    
    Args:
        U_ideal: Ideal unitary operator (d×d matrix)
        U_real: Actual unitary operator (d×d matrix)
    
    Returns:
        Process fidelity (0 to 1)
    """
    d = U_ideal.shape[0]  # Hilbert space dimension
    
    # Compute trace of U_ideal† @ U_real
    trace_value = np.trace(U_ideal.conj().T @ U_real)
    
    # Process fidelity: |Tr(U_ideal† @ U_real)|² / d²
    F_process = np.abs(trace_value) ** 2 / (d ** 2)
    
    return np.real(F_process)  # Return real value (imaginary part is numerical noise)


def compute_average_gate_fidelity(U_ideal: np.ndarray, U_real: np.ndarray) -> float:
    """
    Compute average gate fidelity (entanglement fidelity).
    
    F_avg = (d * F_process + 1) / (d + 1)
    
    Physics: Average gate fidelity is the average state fidelity over all
    possible pure input states, uniformly distributed according to the
    Haar measure. It's related to process fidelity by a simple formula.
    
    This metric is widely used in experimental quantum computing because:
    1. It's directly measurable via randomized benchmarking
    2. It has a simple relationship to process fidelity
    3. It's more intuitive than process fidelity (closer to state fidelity)
    
    Relationship between fidelity measures:
    - State fidelity: F_state = |⟨ψ|U†_ideal U_real|ψ⟩|² (depends on |ψ⟩)
    - Process fidelity: F_process = |Tr(U†_ideal U_real)|²/d² (state-independent)
    - Average gate fidelity: F_avg = (d·F_process + 1)/(d+1) (Haar average)
    
    For two qubits (d=4):
    - F_avg = (4·F_process + 1)/5
    - F_process ≈ F_avg for high fidelity
    
    Args:
        U_ideal: Ideal unitary operator (d×d matrix)
        U_real: Actual unitary operator (d×d matrix)
    
    Returns:
        Average gate fidelity (0 to 1)
    """
    d = U_ideal.shape[0]  # Hilbert space dimension
    
    # First compute process fidelity
    F_process = compute_process_fidelity(U_ideal, U_real)
    
    # Convert to average gate fidelity
    F_avg = (d * F_process + 1) / (d + 1)
    
    return F_avg


def compute_entanglement_leakage(state: np.ndarray) -> float:
    """
    Measure entanglement leakage from product state structure.
    
    Physics: For a product state |ψ⟩ = |a⟩⊗|b⟩, the density matrix factorizes.
    Entanglement leakage quantifies deviation from this structure using
    the purity of the reduced density matrix.
    
    For two qubits in state |ψ⟩, we compute:
    1. Reduced density matrix ρ₁ = Tr₂(|ψ⟩⟨ψ|)
    2. Purity P = Tr(ρ₁²)
    3. Leakage = 1 - P
    
    For product states: P = 1 (no entanglement)
    For maximally entangled: P = 0.5
    
    Args:
        state: 4×1 two-qubit state vector
    
    Returns:
        Entanglement leakage (0 = no entanglement, 0.5 = maximal)
    """
    # Construct density matrix ρ = |ψ⟩⟨ψ|
    rho = state @ state.conj().T
    
    # Compute reduced density matrix for qubit 1 by tracing out qubit 2
    # ρ₁ = Tr₂(ρ) where we sum over qubit 2's basis states
    rho_reduced = np.zeros((2, 2), dtype=complex)
    rho_reduced[0, 0] = rho[0, 0] + rho[1, 1]  # ⟨0|ρ₁|0⟩
    rho_reduced[0, 1] = rho[0, 2] + rho[1, 3]  # ⟨0|ρ₁|1⟩
    rho_reduced[1, 0] = rho[2, 0] + rho[3, 1]  # ⟨1|ρ₁|0⟩
    rho_reduced[1, 1] = rho[2, 2] + rho[3, 3]  # ⟨1|ρ₁|1⟩
    
    # Compute purity: P = Tr(ρ₁²)
    purity = np.real(np.trace(rho_reduced @ rho_reduced))
    
    # Entanglement leakage = 1 - purity
    return 1.0 - purity


# ============================================================================
# Simulation Core
# ============================================================================

def simulate_crosstalk(omega: float, J: float, t: float, 
                      initial_state: np.ndarray = STATE_00) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, float]]:
    """
    Simulate single-qubit pulse with crosstalk effects.
    
    Computes:
    1. Ideal evolution (no crosstalk): U_ideal = exp(-i(Ω/2)(σ_x⊗I)t)
    2. Real evolution (with crosstalk): U_real = exp(-i H t)
    3. State fidelity between ideal and real final states
    4. Process fidelity between U_ideal and U_real
    5. Average gate fidelity
    
    Args:
        omega: Rabi frequency (rad/s)
        J: ZZ coupling strength (rad/s)
        t: Pulse duration (s)
        initial_state: Initial two-qubit state (default: |00⟩)
    
    Returns:
        Tuple of (U_ideal, U_real, state_ideal, state_real, fidelities_dict)
        where fidelities_dict contains:
            - 'state': State fidelity
            - 'process': Process fidelity
            - 'average_gate': Average gate fidelity
    """
    # Ideal Hamiltonian (no crosstalk)
    H_ideal = (omega / 2) * SIGMA_X_I
    U_ideal = time_evolution_operator(H_ideal, t)
    state_ideal = U_ideal @ initial_state
    
    # Real Hamiltonian (with crosstalk)
    H_real = construct_hamiltonian(omega, J)
    U_real = time_evolution_operator(H_real, t)
    state_real = U_real @ initial_state
    
    # Compute all fidelity measures
    fidelities = {
        'state': compute_state_fidelity(state_ideal, state_real),
        'process': compute_process_fidelity(U_ideal, U_real),
        'average_gate': compute_average_gate_fidelity(U_ideal, U_real)
    }
    
    return U_ideal, U_real, state_ideal, state_real, fidelities



# ============================================================================
# Parameter Sweeps
# ============================================================================

def sweep_coupling_strength(omega: float, t: float, 
                           J_values: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Sweep over ZZ coupling strengths and compute metrics.
    
    Args:
        omega: Rabi frequency (rad/s)
        t: Pulse duration (s)
        J_values: Array of coupling strengths to sweep
    
    Returns:
        Dictionary containing arrays of:
            - 'state_fidelity': State fidelities
            - 'process_fidelity': Process fidelities
            - 'average_gate_fidelity': Average gate fidelities
            - 'gate_infidelity': Gate infidelities (1 - F_avg)
            - 'entanglement_leakage': Entanglement leakages
    """
    n = len(J_values)
    results = {
        'state_fidelity': np.zeros(n),
        'process_fidelity': np.zeros(n),
        'average_gate_fidelity': np.zeros(n),
        'gate_infidelity': np.zeros(n),
        'entanglement_leakage': np.zeros(n)
    }
    
    for i, J in enumerate(J_values):
        _, _, _, state_real, fidelities = simulate_crosstalk(omega, J, t)
        results['state_fidelity'][i] = fidelities['state']
        results['process_fidelity'][i] = fidelities['process']
        results['average_gate_fidelity'][i] = fidelities['average_gate']
        results['gate_infidelity'][i] = 1 - fidelities['average_gate']
        results['entanglement_leakage'][i] = compute_entanglement_leakage(state_real)
    
    return results


def sweep_pulse_duration(omega: float, J: float, 
                        t_values: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Sweep over pulse durations and compute metrics.
    
    Args:
        omega: Rabi frequency (rad/s)
        J: ZZ coupling strength (rad/s)
        t_values: Array of pulse durations to sweep
    
    Returns:
        Dictionary containing arrays of fidelity metrics
    """
    n = len(t_values)
    results = {
        'state_fidelity': np.zeros(n),
        'process_fidelity': np.zeros(n),
        'average_gate_fidelity': np.zeros(n),
        'gate_infidelity': np.zeros(n),
        'entanglement_leakage': np.zeros(n)
    }
    
    for i, t in enumerate(t_values):
        _, _, _, state_real, fidelities = simulate_crosstalk(omega, J, t)
        results['state_fidelity'][i] = fidelities['state']
        results['process_fidelity'][i] = fidelities['process']
        results['average_gate_fidelity'][i] = fidelities['average_gate']
        results['gate_infidelity'][i] = 1 - fidelities['average_gate']
        results['entanglement_leakage'][i] = compute_entanglement_leakage(state_real)
    
    return results


def sweep_2d_parameter_space(omega: float, J_values: np.ndarray, 
                            t_values: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Perform 2D sweep over coupling strength and pulse duration.
    
    Args:
        omega: Rabi frequency (rad/s)
        J_values: Array of coupling strengths
        t_values: Array of pulse durations
    
    Returns:
        Dictionary with 2D arrays (shape: len(J_values) × len(t_values)):
            - 'average_gate_fidelity': Average gate fidelities
            - 'process_fidelity': Process fidelities
    """
    shape = (len(J_values), len(t_values))
    results = {
        'average_gate_fidelity': np.zeros(shape),
        'process_fidelity': np.zeros(shape)
    }
    
    for i, J in enumerate(J_values):
        for j, t in enumerate(t_values):
            _, _, _, _, fidelities = simulate_crosstalk(omega, J, t)
            results['average_gate_fidelity'][i, j] = fidelities['average_gate']
            results['process_fidelity'][i, j] = fidelities['process']
    
    return results


# ============================================================================
# Visualization
# ============================================================================

def plot_crosstalk_analysis(J_values: np.ndarray, results_J: Dict[str, np.ndarray],
                           t_values: np.ndarray, results_t: Dict[str, np.ndarray],
                           fidelity_maps: Dict[str, np.ndarray],
                           J_grid: np.ndarray, t_grid: np.ndarray,
                           omega: float, t_nominal: float, J_nominal: float) -> None:
    """
    Generate comprehensive crosstalk analysis plots with gate fidelity comparison.
    
    Creates 6 subplots:
        1. Average Gate Fidelity vs Coupling Strength J
        2. Average Gate Fidelity vs Pulse Duration
        3. 2D Heatmap: Average Gate Fidelity(J, t)
        4. Entanglement Leakage Analysis
        5. State vs Gate Fidelity Comparison (J sweep)
        6. State vs Gate Fidelity Comparison (t sweep)
    """
    fig = plt.figure(figsize=(18, 12))
    
    # ========================================================================
    # Plot 1: Average Gate Fidelity vs Coupling Strength
    # ========================================================================
    ax1 = plt.subplot(2, 3, 1)
    ax1.plot(J_values, results_J['average_gate_fidelity'], 'b-', linewidth=2, 
             label='Avg Gate Fidelity')
    ax1.plot(J_values, results_J['gate_infidelity'], 'r--', linewidth=2, 
             label='Gate Infidelity ε')
    ax1.axhline(y=0.99, color='gray', linestyle=':', linewidth=1, label='99% threshold')
    ax1.set_xlabel('ZZ Coupling Strength J (rad/s)', fontsize=10)
    ax1.set_ylabel('Fidelity / Infidelity', fontsize=10)
    ax1.set_title(f'Avg Gate Fidelity vs Coupling\n(Ω={omega:.3f} rad/s, t={t_nominal:.4f} s)', 
                  fontsize=11, fontweight='bold')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 1.05])
    
    # ========================================================================
    # Plot 2: Average Gate Fidelity vs Pulse Duration
    # ========================================================================
    ax2 = plt.subplot(2, 3, 2)
    ax2.plot(t_values * 1e6, results_t['average_gate_fidelity'], 'b-', linewidth=2, 
             label='Avg Gate Fidelity')
    ax2.plot(t_values * 1e6, results_t['gate_infidelity'], 'r--', linewidth=2, 
             label='Gate Infidelity ε')
    ax2.axvline(x=t_nominal * 1e6, color='green', linestyle=':', linewidth=2, 
                label=f'Nominal t={t_nominal*1e6:.2f} μs')
    ax2.axhline(y=0.99, color='gray', linestyle=':', linewidth=1, label='99% threshold')
    ax2.set_xlabel('Pulse Duration (μs)', fontsize=10)
    ax2.set_ylabel('Fidelity / Infidelity', fontsize=10)
    ax2.set_title(f'Avg Gate Fidelity vs Duration\n(Ω={omega:.3f} rad/s, J={J_nominal:.4f} rad/s)', 
                  fontsize=11, fontweight='bold')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 1.05])
    
    # ========================================================================
    # Plot 3: 2D Heatmap - Average Gate Fidelity(J, t)
    # ========================================================================
    ax3 = plt.subplot(2, 3, 3)
    im = ax3.contourf(t_grid * 1e6, J_grid, fidelity_maps['average_gate_fidelity'], 
                      levels=20, cmap='RdYlGn')
    cbar = plt.colorbar(im, ax=ax3)
    cbar.set_label('Avg Gate Fidelity', fontsize=9)
    ax3.scatter([t_nominal * 1e6], [J_nominal], color='blue', s=100, 
                marker='*', edgecolors='black', linewidths=2, 
                label='Nominal Point', zorder=5)
    ax3.set_xlabel('Pulse Duration (μs)', fontsize=10)
    ax3.set_ylabel('ZZ Coupling Strength J (rad/s)', fontsize=10)
    ax3.set_title('2D Gate Fidelity Landscape\n(Crosstalk Parameter Space)', 
                  fontsize=11, fontweight='bold')
    ax3.legend(fontsize=8)
    
    # ========================================================================
    # Plot 4: Entanglement Leakage
    # ========================================================================
    ax4 = plt.subplot(2, 3, 4)
    ax4.plot(J_values, results_J['entanglement_leakage'], 'purple', linewidth=2, 
             label='vs Coupling Strength', marker='o', markersize=3)
    ax4_twin = ax4.twinx()
    ax4_twin.plot(t_values * 1e6, results_t['entanglement_leakage'], 'orange', linewidth=2,
                  label='vs Pulse Duration', marker='s', markersize=3)
    ax4.set_xlabel('ZZ Coupling Strength J (rad/s)', fontsize=10)
    ax4.set_ylabel('Entanglement Leakage (vs J)', fontsize=10, color='purple')
    ax4_twin.set_xlabel('Pulse Duration (μs)', fontsize=10)
    ax4_twin.set_ylabel('Entanglement Leakage (vs t)', fontsize=10, color='orange')
    ax4.tick_params(axis='y', labelcolor='purple')
    ax4_twin.tick_params(axis='y', labelcolor='orange')
    ax4.set_title('Entanglement Leakage Analysis\n(Unwanted Two-Qubit Correlations)', 
                  fontsize=11, fontweight='bold')
    ax4.legend(loc='upper left', fontsize=8)
    ax4_twin.legend(loc='upper right', fontsize=8)
    ax4.grid(True, alpha=0.3)
    
    # ========================================================================
    # Plot 5: State vs Gate Fidelity (J sweep)
    # ========================================================================
    ax5 = plt.subplot(2, 3, 5)
    ax5.plot(J_values, results_J['state_fidelity'], 'g-', linewidth=2, 
             label='State Fidelity', alpha=0.7)
    ax5.plot(J_values, results_J['average_gate_fidelity'], 'b-', linewidth=2, 
             label='Avg Gate Fidelity', alpha=0.7)
    ax5.plot(J_values, results_J['process_fidelity'], 'r--', linewidth=2, 
             label='Process Fidelity', alpha=0.7)
    
    # Compute and show deviation
    deviation = np.abs(results_J['state_fidelity'] - results_J['average_gate_fidelity'])
    ax5_twin = ax5.twinx()
    ax5_twin.plot(J_values, deviation, 'k:', linewidth=1.5, label='|State - Gate|', alpha=0.5)
    ax5_twin.set_ylabel('Deviation', fontsize=9, color='black')
    ax5_twin.tick_params(axis='y', labelcolor='black')
    
    ax5.set_xlabel('ZZ Coupling Strength J (rad/s)', fontsize=10)
    ax5.set_ylabel('Fidelity', fontsize=10)
    ax5.set_title('Fidelity Comparison vs Coupling\n(State vs Gate Metrics)', 
                  fontsize=11, fontweight='bold')
    ax5.legend(loc='lower left', fontsize=8)
    ax5_twin.legend(loc='upper right', fontsize=7)
    ax5.grid(True, alpha=0.3)
    ax5.set_ylim([0, 1.05])
    
    # ========================================================================
    # Plot 6: State vs Gate Fidelity (t sweep)
    # ========================================================================
    ax6 = plt.subplot(2, 3, 6)
    ax6.plot(t_values * 1e6, results_t['state_fidelity'], 'g-', linewidth=2, 
             label='State Fidelity', alpha=0.7)
    ax6.plot(t_values * 1e6, results_t['average_gate_fidelity'], 'b-', linewidth=2, 
             label='Avg Gate Fidelity', alpha=0.7)
    ax6.plot(t_values * 1e6, results_t['process_fidelity'], 'r--', linewidth=2, 
             label='Process Fidelity', alpha=0.7)
    
    # Compute and show deviation
    deviation_t = np.abs(results_t['state_fidelity'] - results_t['average_gate_fidelity'])
    ax6_twin = ax6.twinx()
    ax6_twin.plot(t_values * 1e6, deviation_t, 'k:', linewidth=1.5, label='|State - Gate|', alpha=0.5)
    ax6_twin.set_ylabel('Deviation', fontsize=9, color='black')
    ax6_twin.tick_params(axis='y', labelcolor='black')
    
    ax6.set_xlabel('Pulse Duration (μs)', fontsize=10)
    ax6.set_ylabel('Fidelity', fontsize=10)
    ax6.set_title('Fidelity Comparison vs Duration\n(State vs Gate Metrics)', 
                  fontsize=11, fontweight='bold')
    ax6.legend(loc='lower left', fontsize=8)
    ax6_twin.legend(loc='upper right', fontsize=7)
    ax6.grid(True, alpha=0.3)
    ax6.set_ylim([0, 1.05])
    
    plt.tight_layout()
    plt.savefig('qpocs_phase2_5_gate_fidelity.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("✓ Gate fidelity analysis plot saved as 'qpocs_phase2_5_gate_fidelity.png'")



# ============================================================================
# Hardware Summary Report
# ============================================================================

def print_hardware_summary(omega: float, t_nominal: float, J_nominal: float,
                          results_J: Dict[str, np.ndarray], J_values: np.ndarray,
                          results_t: Dict[str, np.ndarray], t_values: np.ndarray) -> None:
    """
    Print hardware-oriented summary of crosstalk analysis with gate fidelity metrics.
    """
    print("\n" + "="*75)
    print(" " * 18 + "PHASE 2.5: GATE FIDELITY ANALYSIS SUMMARY")
    print("="*75)
    
    # System Parameters
    print(f"\n{'SYSTEM PARAMETERS':^75}")
    print("-" * 75)
    theta_target = np.pi / 2
    print(f"  Target Rotation:           θ = π/2 = {theta_target:.6f} rad")
    print(f"  Rabi Frequency:            Ω = {omega:.6f} rad/s")
    print(f"  Nominal Pulse Duration:    t = {t_nominal*1e6:.4f} μs")
    print(f"  Nominal ZZ Coupling:       J = {J_nominal:.6f} rad/s")
    print(f"  Rotation Check:            Ωt = {omega*t_nominal:.6f} rad (should ≈ π/2)")
    print(f"  Hilbert Space Dimension:   d = 4 (two qubits)")
    
    # Fidelity Metrics at Nominal Parameters
    print(f"\n{'FIDELITY METRICS AT NOMINAL PARAMETERS':^75}")
    print("-" * 75)
    
    # Get nominal point values
    idx_nominal_J = np.argmin(np.abs(J_values - J_nominal))
    idx_nominal_t = np.argmin(np.abs(t_values - t_nominal))
    
    state_fid_J = results_J['state_fidelity'][idx_nominal_J]
    process_fid_J = results_J['process_fidelity'][idx_nominal_J]
    avg_gate_fid_J = results_J['average_gate_fidelity'][idx_nominal_J]
    gate_infid_J = results_J['gate_infidelity'][idx_nominal_J]
    
    print(f"  State Fidelity (F_state):        {state_fid_J:.10f}")
    print(f"  Process Fidelity (F_process):    {process_fid_J:.10f}")
    print(f"  Avg Gate Fidelity (F_avg):       {avg_gate_fid_J:.10f}")
    print(f"  Gate Infidelity (ε_gate):        {gate_infid_J:.10e}")
    print(f"  Deviation |F_state - F_avg|:     {abs(state_fid_J - avg_gate_fid_J):.10e}")
    
    # Explain the metrics
    print(f"\n{'FIDELITY METRIC DEFINITIONS':^75}")
    print("-" * 75)
    print("  State Fidelity:     F_state = |⟨ψ_ideal|ψ_real⟩|²")
    print("                      → Depends on initial state |ψ⟩ (here: |00⟩)")
    print("                      → Measures state overlap for specific input")
    print()
    print("  Process Fidelity:   F_process = |Tr(U†_ideal U_real)|²/d²")
    print("                      → Independent of input state")
    print("                      → Measures gate quality averaged over Haar measure")
    print()
    print("  Avg Gate Fidelity:  F_avg = (d·F_process + 1)/(d+1)")
    print("                      → For d=4: F_avg = (4·F_process + 1)/5")
    print("                      → Standard metric for gate characterization")
    print("                      → Directly measurable via randomized benchmarking")
    
    # Coupling Strength Analysis
    print(f"\n{'COUPLING STRENGTH SWEEP (J)':^75}")
    print("-" * 75)
    
    avg_gate_fid_J_arr = results_J['average_gate_fidelity']
    gate_infid_J_arr = results_J['gate_infidelity']
    entanglement_J = results_J['entanglement_leakage']
    
    print(f"  J Range:                   [{J_values[0]:.4f}, {J_values[-1]:.4f}] rad/s")
    print(f"  Avg Gate Fid at Nominal:   {avg_gate_fid_J:.8f}")
    print(f"  Gate Infidelity at Nominal:{gate_infid_J:.8e}")
    print(f"  Min Avg Gate Fidelity:     {np.min(avg_gate_fid_J_arr):.8f} (at J={J_values[np.argmin(avg_gate_fid_J_arr)]:.4f})")
    print(f"  Max Avg Gate Fidelity:     {np.max(avg_gate_fid_J_arr):.8f} (at J={J_values[np.argmax(avg_gate_fid_J_arr)]:.4f})")
    print(f"  Entanglement at Nominal:   {entanglement_J[idx_nominal_J]:.8f}")
    print(f"  Max Entanglement Leakage:  {np.max(entanglement_J):.8f}")
    
    # Pulse Duration Analysis
    print(f"\n{'PULSE DURATION SWEEP (±20%)':^75}")
    print("-" * 75)
    
    avg_gate_fid_t_arr = results_t['average_gate_fidelity']
    gate_infid_t_arr = results_t['gate_infidelity']
    entanglement_t = results_t['entanglement_leakage']
    
    print(f"  Duration Range:            [{t_values[0]*1e6:.4f}, {t_values[-1]*1e6:.4f}] μs")
    print(f"  Avg Gate Fid at Nominal:   {avg_gate_fid_t_arr[idx_nominal_t]:.8f}")
    print(f"  Gate Infidelity at Nominal:{gate_infid_t_arr[idx_nominal_t]:.8e}")
    print(f"  Min Avg Gate Fidelity:     {np.min(avg_gate_fid_t_arr):.8f} (at t={t_values[np.argmin(avg_gate_fid_t_arr)]*1e6:.4f} μs)")
    print(f"  Max Avg Gate Fidelity:     {np.max(avg_gate_fid_t_arr):.8f} (at t={t_values[np.argmax(avg_gate_fid_t_arr)]*1e6:.4f} μs)")
    
    # Error Budget Recommendations
    print(f"\n{'ERROR BUDGET & RECOMMENDATIONS':^75}")
    print("-" * 75)
    
    # Find J value for 99% fidelity threshold
    idx_99 = np.where(avg_gate_fid_J_arr >= 0.99)[0]
    if len(idx_99) > 0:
        J_max_99 = J_values[idx_99[-1]]
        print(f"  Max J for 99% Gate Fid:    {J_max_99:.6f} rad/s")
    else:
        print(f"  Max J for 99% Gate Fid:    Not achievable in sweep range")
    
    # Sensitivity to timing errors
    fidelity_sensitivity = np.gradient(avg_gate_fid_t_arr, t_values)[idx_nominal_t]
    print(f"  Timing Sensitivity dF/dt:  {fidelity_sensitivity:.6e} s⁻¹")
    
    # Crosstalk tolerance
    J_sensitivity = np.gradient(avg_gate_fid_J_arr, J_values)[idx_nominal_J]
    print(f"  Crosstalk Sensitivity:     {J_sensitivity:.6e} (rad/s)⁻¹")
    
    print(f"\n{'PHYSICS VALIDATION':^75}")
    print("-" * 75)
    
    # Check if rotation angle is correct
    rotation_error = abs(omega * t_nominal - np.pi/2)
    print(f"  Rotation Angle Error:      {rotation_error:.8e} rad")
    
    if rotation_error < 1e-6:
        print(f"  ✓ Rotation angle correctly calibrated")
    else:
        print(f"  ⚠ Warning: Rotation angle may be miscalibrated")
    
    # Check Hamiltonian scaling
    if J_nominal < omega:
        print(f"  ✓ Perturbative regime: J << Ω (crosstalk is weak)")
    else:
        print(f"  ⚠ Warning: Strong coupling regime J ≈ Ω (perturbation theory invalid)")
    
    # Check entanglement consistency
    if np.max(entanglement_J) < 0.5:
        print(f"  ✓ Entanglement leakage within physical bounds")
    else:
        print(f"  ⚠ Warning: High entanglement leakage detected")
    
    # Check fidelity relationship
    # For high fidelity, F_avg ≈ F_process ≈ F_state
    if abs(state_fid_J - avg_gate_fid_J) < 0.01:
        print(f"  ✓ State and gate fidelities agree (high fidelity regime)")
    else:
        print(f"  ⚠ Note: State and gate fidelities differ (check initial state dependence)")
    
    print("\n" + "="*75)


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """
    Execute Phase 2.5: Dynamic Two-Qubit Crosstalk with Gate Fidelity Analysis.
    """
    print("="*75)
    print(" " * 10 + "QPOCS Phase 2.5: Crosstalk + Gate Fidelity Analysis")
    print("="*75)
    
    # ========================================================================
    # System Configuration
    # ========================================================================
    
    # Target: π/2 rotation on qubit 1
    THETA_TARGET = np.pi / 2
    
    # Choose Rabi frequency (arbitrary units, but must be consistent)
    OMEGA = np.pi  # rad/s
    
    # Compute pulse duration: t = θ / Ω
    T_NOMINAL = THETA_TARGET / OMEGA
    
    # Nominal ZZ coupling strength (typically J << Ω in real hardware)
    J_NOMINAL = 0.05  # rad/s (5% of Ω)
    
    print(f"\nSystem Configuration:")
    print(f"  Target rotation:        θ = π/2 rad")
    print(f"  Rabi frequency:         Ω = {OMEGA:.6f} rad/s")
    print(f"  Nominal pulse duration: t = {T_NOMINAL:.6f} s = {T_NOMINAL*1e6:.2f} μs")
    print(f"  Nominal ZZ coupling:    J = {J_NOMINAL:.6f} rad/s")
    print(f"  Coupling ratio:         J/Ω = {J_NOMINAL/OMEGA:.4f}")
    print(f"  Hilbert space dim:      d = 4 (two qubits)")
    
    # Verify rotation angle
    print(f"\nRotation Verification:")
    print(f"  Ωt = {OMEGA * T_NOMINAL:.6f} rad")
    print(f"  π/2 = {np.pi/2:.6f} rad")
    print(f"  Match: {np.isclose(OMEGA * T_NOMINAL, np.pi/2)}")
    
    # ========================================================================
    # Parameter Sweeps
    # ========================================================================
    
    print(f"\n[1/4] Sweeping ZZ coupling strength J...")
    J_VALUES = np.linspace(0, 0.2, 100)
    results_J = sweep_coupling_strength(OMEGA, T_NOMINAL, J_VALUES)
    
    print(f"[2/4] Sweeping pulse duration (±20%)...")
    T_MIN = T_NOMINAL * 0.8
    T_MAX = T_NOMINAL * 1.2
    T_VALUES = np.linspace(T_MIN, T_MAX, 100)
    results_t = sweep_pulse_duration(OMEGA, J_NOMINAL, T_VALUES)
    
    print(f"[3/4] Computing 2D parameter space...")
    J_GRID_VALUES = np.linspace(0, 0.2, 50)
    T_GRID_VALUES = np.linspace(T_MIN, T_MAX, 50)
    fidelity_maps = sweep_2d_parameter_space(OMEGA, J_GRID_VALUES, T_GRID_VALUES)
    
    # Create meshgrid for plotting
    T_GRID, J_GRID = np.meshgrid(T_GRID_VALUES, J_GRID_VALUES)
    
    # ========================================================================
    # Results and Visualization
    # ========================================================================
    
    print_hardware_summary(OMEGA, T_NOMINAL, J_NOMINAL,
                          results_J, J_VALUES,
                          results_t, T_VALUES)
    
    print(f"\n[4/4] Generating gate fidelity analysis plots...")
    plot_crosstalk_analysis(J_VALUES, results_J,
                           T_VALUES, results_t,
                           fidelity_maps, J_GRID, T_GRID,
                           OMEGA, T_NOMINAL, J_NOMINAL)
    
    print("\n✓ Phase 2.5 gate fidelity analysis complete!")
    print("✓ Ready for Phase 3: Multi-qubit optimization")


if __name__ == "__main__":
    np.random.seed(42)
    main()
