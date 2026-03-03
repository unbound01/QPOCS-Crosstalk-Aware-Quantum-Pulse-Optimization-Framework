"""
Fidelity Metrics

State fidelity, process fidelity, average gate fidelity, and entanglement measures.
"""

import numpy as np


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
    
    Args:
        U_ideal: Ideal unitary operator (d×d matrix)
        U_real: Actual unitary operator (d×d matrix)
    
    Returns:
        Process fidelity (0 to 1)
    """
    d = U_ideal.shape[0]
    trace_value = np.trace(U_ideal.conj().T @ U_real)
    F_process = np.abs(trace_value) ** 2 / (d ** 2)
    return np.real(F_process)


def compute_average_gate_fidelity(U_ideal: np.ndarray, U_real: np.ndarray) -> float:
    """
    Compute average gate fidelity (entanglement fidelity).
    
    F_avg = (d * F_process + 1) / (d + 1)
    
    Physics: Average gate fidelity is the average state fidelity over all
    possible pure input states, uniformly distributed according to the
    Haar measure. Standard metric for experimental quantum computing.
    
    Args:
        U_ideal: Ideal unitary operator (d×d matrix)
        U_real: Actual unitary operator (d×d matrix)
    
    Returns:
        Average gate fidelity (0 to 1)
    """
    d = U_ideal.shape[0]
    F_process = compute_process_fidelity(U_ideal, U_real)
    F_avg = (d * F_process + 1) / (d + 1)
    return F_avg


def compute_entanglement_leakage(state: np.ndarray) -> float:
    """
    Measure entanglement leakage from product state structure.
    
    Physics: For a product state |ψ⟩ = |a⟩⊗|b⟩, the density matrix factorizes.
    Entanglement leakage quantifies deviation from this structure using
    the purity of the reduced density matrix.
    
    Leakage = 1 - Purity, where Purity = Tr(ρ₁²)
    
    Args:
        state: 4×1 two-qubit state vector
    
    Returns:
        Entanglement leakage (0 = no entanglement, 0.5 = maximal)
    """
    # Construct density matrix ρ = |ψ⟩⟨ψ|
    rho = state @ state.conj().T
    
    # Compute reduced density matrix for qubit 1 by tracing out qubit 2
    rho_reduced = np.zeros((2, 2), dtype=complex)
    rho_reduced[0, 0] = rho[0, 0] + rho[1, 1]
    rho_reduced[0, 1] = rho[0, 2] + rho[1, 3]
    rho_reduced[1, 0] = rho[2, 0] + rho[3, 1]
    rho_reduced[1, 1] = rho[2, 2] + rho[3, 3]
    
    # Compute purity: P = Tr(ρ₁²)
    purity = np.real(np.trace(rho_reduced @ rho_reduced))
    
    # Entanglement leakage = 1 - purity
    return 1.0 - purity
