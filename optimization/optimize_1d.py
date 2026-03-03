"""
1D Pulse Optimization

Optimize pulse duration with constraint θ = Ωt.
"""

import numpy as np
from scipy.optimize import minimize
from typing import Tuple, List
from core import (
    construct_hamiltonian,
    construct_ideal_hamiltonian,
    time_evolution_operator,
    compute_average_gate_fidelity
)


def gate_infidelity_objective(t: float, J: float, theta_target: float) -> float:
    """
    Objective function for 1D pulse optimization: gate infidelity ε = 1 - F_avg.
    
    Constraint: θ = Ωt (fixed rotation angle)
    
    Args:
        t: Pulse duration (s)
        J: ZZ coupling strength (rad/s)
        theta_target: Target rotation angle (rad)
    
    Returns:
        Gate infidelity ε = 1 - F_avg
    """
    # Compute Ω from constraint θ = Ωt
    omega = theta_target / t
    
    # Construct Hamiltonians
    H_ideal = construct_ideal_hamiltonian(omega)
    H_real = construct_hamiltonian(omega, J)
    
    # Compute time evolution operators
    U_ideal = time_evolution_operator(H_ideal, t)
    U_real = time_evolution_operator(H_real, t)
    
    # Compute average gate fidelity
    F_avg = compute_average_gate_fidelity(U_ideal, U_real)
    
    # Return gate infidelity
    return 1 - F_avg


def grid_search_optimization(J: float, theta_target: float, 
                             t_nominal: float, search_range: float = 0.2,
                             n_points: int = 200) -> Tuple[float, np.ndarray, np.ndarray]:
    """
    Perform grid search optimization over pulse duration.
    
    Args:
        J: ZZ coupling strength (rad/s)
        theta_target: Target rotation angle (rad)
        t_nominal: Nominal pulse duration (s)
        search_range: Search range as fraction of nominal
        n_points: Number of grid points
    
    Returns:
        Tuple of (t_optimal, t_values, infidelities)
    """
    t_min = t_nominal * (1 - search_range)
    t_max = t_nominal * (1 + search_range)
    t_values = np.linspace(t_min, t_max, n_points)
    
    infidelities = np.array([gate_infidelity_objective(t, J, theta_target) 
                            for t in t_values])
    
    idx_optimal = np.argmin(infidelities)
    t_optimal = t_values[idx_optimal]
    
    return t_optimal, t_values, infidelities


def scipy_optimization(J: float, theta_target: float, 
                      t_nominal: float, search_range: float = 0.2) -> Tuple[float, List[float]]:
    """
    Perform optimization using scipy.optimize.minimize.
    
    Args:
        J: ZZ coupling strength (rad/s)
        theta_target: Target rotation angle (rad)
        t_nominal: Nominal pulse duration (s)
        search_range: Search range as fraction of nominal
    
    Returns:
        Tuple of (t_optimal, convergence_history)
    """
    t_min = t_nominal * (1 - search_range)
    t_max = t_nominal * (1 + search_range)
    bounds = [(t_min, t_max)]
    
    convergence_history = []
    
    def callback(xk):
        convergence_history.append(gate_infidelity_objective(xk[0], J, theta_target))
    
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


def optimize_pulse_duration(J: float, theta_target: float, 
                           omega_nominal: float = np.pi,
                           method: str = 'both') -> dict:
    """
    Optimize pulse duration to minimize gate infidelity.
    
    Args:
        J: ZZ coupling strength (rad/s)
        theta_target: Target rotation angle (rad)
        omega_nominal: Nominal Rabi frequency (rad/s)
        method: 'grid', 'scipy', or 'both'
    
    Returns:
        Dictionary with optimization results
    """
    t_nominal = theta_target / omega_nominal
    
    # Compute nominal fidelity
    infidelity_nominal = gate_infidelity_objective(t_nominal, J, theta_target)
    fidelity_nominal = 1 - infidelity_nominal
    
    # Perform optimization
    if method in ['grid', 'both']:
        t_optimal_grid, t_values, infidelities = grid_search_optimization(
            J, theta_target, t_nominal
        )
        t_optimal = t_optimal_grid
    
    if method in ['scipy', 'both']:
        t_optimal_scipy, convergence = scipy_optimization(
            J, theta_target, t_nominal
        )
        if method == 'scipy':
            t_optimal = t_optimal_scipy
    
    # Compute optimal parameters
    omega_optimal = theta_target / t_optimal
    infidelity_optimal = gate_infidelity_objective(t_optimal, J, theta_target)
    fidelity_optimal = 1 - infidelity_optimal
    
    improvement_percent = ((fidelity_optimal - fidelity_nominal) / fidelity_nominal) * 100
    
    return {
        'J': J,
        'theta_target': theta_target,
        't_nominal': t_nominal,
        't_optimal': t_optimal,
        'omega_nominal': omega_nominal,
        'omega_optimal': omega_optimal,
        'fidelity_nominal': fidelity_nominal,
        'fidelity_optimal': fidelity_optimal,
        'improvement_percent': improvement_percent,
        'method': method
    }
