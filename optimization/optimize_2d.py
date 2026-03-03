"""
2D Pulse Optimization

Jointly optimize amplitude Ω and duration t without constraints.
"""

import numpy as np
from scipy.optimize import minimize
from typing import Tuple
from core import (
    construct_hamiltonian,
    construct_ideal_hamiltonian,
    time_evolution_operator,
    compute_average_gate_fidelity
)


def gate_infidelity_2d(params: np.ndarray, J: float) -> float:
    """
    2D objective function for joint (Ω, t) optimization.
    
    No constraint - both Ω and t are free parameters.
    
    Args:
        params: [Ω, t] array
        J: ZZ coupling strength (rad/s)
    
    Returns:
        Gate infidelity ε = 1 - F_avg
    """
    omega, t = params
    
    # Construct Hamiltonians
    H_ideal = construct_ideal_hamiltonian(omega)
    H_real = construct_hamiltonian(omega, J)
    
    # Compute time evolution operators
    U_ideal = time_evolution_operator(H_ideal, t)
    U_real = time_evolution_operator(H_real, t)
    
    # Compute average gate fidelity
    F_avg = compute_average_gate_fidelity(U_ideal, U_real)
    
    return 1 - F_avg


def grid_search_2d(J: float, omega_nominal: float, t_nominal: float,
                   search_range: float = 0.2, n_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Perform 2D grid search over (Ω, t) parameter space.
    
    Args:
        J: ZZ coupling strength (rad/s)
        omega_nominal: Nominal Rabi frequency (rad/s)
        t_nominal: Nominal pulse duration (s)
        search_range: Search range as fraction of nominal
        n_points: Number of grid points per dimension
    
    Returns:
        Tuple of (omega_grid, t_grid, infidelity_grid, optimal_params)
    """
    omega_min = omega_nominal * (1 - search_range)
    omega_max = omega_nominal * (1 + search_range)
    t_min = t_nominal * (1 - search_range)
    t_max = t_nominal * (1 + search_range)
    
    omega_values = np.linspace(omega_min, omega_max, n_points)
    t_values = np.linspace(t_min, t_max, n_points)
    
    omega_grid, t_grid = np.meshgrid(omega_values, t_values)
    infidelity_grid = np.zeros_like(omega_grid)
    
    for i in range(n_points):
        for j in range(n_points):
            params = [omega_grid[i, j], t_grid[i, j]]
            infidelity_grid[i, j] = gate_infidelity_2d(params, J)
    
    idx_min = np.unravel_index(np.argmin(infidelity_grid), infidelity_grid.shape)
    optimal_params = np.array([omega_grid[idx_min], t_grid[idx_min]])
    
    return omega_grid, t_grid, infidelity_grid, optimal_params


def scipy_optimization_2d(J: float, omega_nominal: float, t_nominal: float,
                         initial_guess: np.ndarray = None,
                         search_range: float = 0.25) -> Tuple[np.ndarray, list]:
    """
    Perform 2D optimization using scipy.optimize.minimize.
    
    Args:
        J: ZZ coupling strength (rad/s)
        omega_nominal: Nominal Rabi frequency (rad/s)
        t_nominal: Nominal pulse duration (s)
        initial_guess: Starting point [Ω, t]
        search_range: Search range as fraction of nominal
    
    Returns:
        Tuple of (optimal_params, convergence_history)
    """
    if initial_guess is None:
        initial_guess = np.array([omega_nominal, t_nominal])
    
    omega_min = omega_nominal * (1 - search_range)
    omega_max = omega_nominal * (1 + search_range)
    t_min = t_nominal * (1 - search_range)
    t_max = t_nominal * (1 + search_range)
    bounds = [(omega_min, omega_max), (t_min, t_max)]
    
    convergence_history = []
    
    def callback(xk):
        convergence_history.append(gate_infidelity_2d(xk, J))
    
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


def optimize_2d_parameters(J: float, omega_nominal: float, t_nominal: float,
                          method: str = 'both') -> dict:
    """
    Perform full 2D optimization pipeline.
    
    Args:
        J: ZZ coupling strength (rad/s)
        omega_nominal: Nominal Rabi frequency (rad/s)
        t_nominal: Nominal pulse duration (s)
        method: 'grid', 'scipy', or 'both'
    
    Returns:
        Dictionary with optimization results
    """
    # Compute nominal metrics
    params_nominal = np.array([omega_nominal, t_nominal])
    infidelity_nominal = gate_infidelity_2d(params_nominal, J)
    fidelity_nominal = 1 - infidelity_nominal
    
    # Grid search
    omega_grid, t_grid, infidelity_grid, params_grid = grid_search_2d(
        J, omega_nominal, t_nominal
    )
    
    # Scipy refinement
    if method in ['scipy', 'both']:
        params_scipy, convergence = scipy_optimization_2d(
            J, omega_nominal, t_nominal, 
            initial_guess=params_grid if method == 'both' else None
        )
        params_optimal = params_scipy if method == 'scipy' else params_scipy
    else:
        params_optimal = params_grid
    
    # Extract optimal parameters
    omega_optimal, t_optimal = params_optimal
    
    # Compute optimal metrics
    infidelity_optimal = gate_infidelity_2d(params_optimal, J)
    fidelity_optimal = 1 - infidelity_optimal
    
    improvement_percent = ((fidelity_optimal - fidelity_nominal) / fidelity_nominal) * 100
    
    return {
        'J': J,
        'omega_nominal': omega_nominal,
        't_nominal': t_nominal,
        'omega_optimal': omega_optimal,
        't_optimal': t_optimal,
        'theta_nominal': omega_nominal * t_nominal,
        'theta_optimal': omega_optimal * t_optimal,
        'fidelity_nominal': fidelity_nominal,
        'fidelity_optimal': fidelity_optimal,
        'improvement_percent': improvement_percent,
        'method': method,
        'grid_data': (omega_grid, t_grid, infidelity_grid)
    }
