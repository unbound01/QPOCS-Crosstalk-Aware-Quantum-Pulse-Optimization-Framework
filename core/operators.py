"""
Quantum Operators

Pauli matrices, tensor products, and quantum states for two-qubit systems.
"""

import numpy as np


# ============================================================================
# Single-Qubit Pauli Matrices
# ============================================================================

SIGMA_X = np.array([[0, 1], 
                     [1, 0]], dtype=complex)

SIGMA_Z = np.array([[1, 0], 
                     [0, -1]], dtype=complex)

IDENTITY_2 = np.eye(2, dtype=complex)


# ============================================================================
# Tensor Product Operations
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


# ============================================================================
# Two-Qubit Operators
# ============================================================================

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
