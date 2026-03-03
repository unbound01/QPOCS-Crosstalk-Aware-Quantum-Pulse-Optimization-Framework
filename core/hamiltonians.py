"""
Hamiltonian Construction

Functions for building quantum Hamiltonians with control and crosstalk terms.
"""

import numpy as np
from .operators import SIGMA_X_I, SIGMA_Z_Z


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


def construct_ideal_hamiltonian(omega: float) -> np.ndarray:
    """
    Construct ideal Hamiltonian without crosstalk.
    
    H_ideal = (Ω/2)(σ_x ⊗ I)
    
    Args:
        omega: Rabi frequency (rad/s)
    
    Returns:
        4×4 ideal Hamiltonian matrix
    """
    return (omega / 2) * SIGMA_X_I
