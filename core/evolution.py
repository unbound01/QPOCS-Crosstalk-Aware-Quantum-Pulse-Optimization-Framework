"""
Time Evolution

Quantum time evolution operators and gate operations.
"""

import numpy as np
from scipy.linalg import expm


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


def apply_gate(gate: np.ndarray, state: np.ndarray) -> np.ndarray:
    """
    Apply a quantum gate to a quantum state.
    
    Args:
        gate: Unitary matrix
        state: State vector
    
    Returns:
        Transformed state vector
    """
    return gate @ state
