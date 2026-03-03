"""
Crosstalk Analysis

Two-qubit crosstalk during single-qubit control pulses.
"""

import numpy as np
from typing import Tuple, Dict
from core import (
    STATE_00, 
    construct_hamiltonian, 
    construct_ideal_hamiltonian,
    time_evolution_operator,
    compute_state_fidelity,
    compute_process_fidelity,
    compute_average_gate_fidelity,
    compute_entanglement_leakage
)


def simulate_crosstalk(omega: float, J: float, t: float, 
                      initial_state: np.ndarray = STATE_00) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, float]]:
    """
    Simulate single-qubit pulse with crosstalk effects.
    
    Args:
        omega: Rabi frequency (rad/s)
        J: ZZ coupling strength (rad/s)
        t: Pulse duration (s)
        initial_state: Initial two-qubit state
    
    Returns:
        Tuple of (U_ideal, U_real, state_ideal, state_real, fidelities_dict)
    """
    # Ideal Hamiltonian (no crosstalk)
    H_ideal = construct_ideal_hamiltonian(omega)
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


def sweep_coupling_strength(omega: float, t: float, 
                           J_values: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Sweep over ZZ coupling strengths and compute metrics.
    
    Args:
        omega: Rabi frequency (rad/s)
        t: Pulse duration (s)
        J_values: Array of coupling strengths to sweep
    
    Returns:
        Dictionary containing arrays of fidelity metrics
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
        Dictionary with 2D arrays
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
