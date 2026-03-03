"""
QPOCS Core Module

Fundamental quantum operations, operators, and physics calculations.
"""

from .operators import *
from .hamiltonians import *
from .evolution import *
from .fidelity import *

__all__ = [
    # Operators
    'SIGMA_X', 'SIGMA_Z', 'IDENTITY_2',
    'SIGMA_X_I', 'SIGMA_Z_Z', 'IDENTITY_4',
    'STATE_00', 'STATE_01', 'STATE_10', 'STATE_11',
    'tensor_product',
    
    # Hamiltonians
    'construct_hamiltonian',
    'construct_ideal_hamiltonian',
    
    # Evolution
    'time_evolution_operator',
    
    # Fidelity
    'compute_state_fidelity',
    'compute_process_fidelity',
    'compute_average_gate_fidelity',
    'compute_entanglement_leakage',
]
