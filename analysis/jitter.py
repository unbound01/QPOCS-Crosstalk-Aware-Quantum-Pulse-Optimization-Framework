"""
Jitter Analysis

Single-qubit rotation under timing jitter noise.
"""

import numpy as np
from typing import Tuple, Dict
from scipy.linalg import expm
from core import SIGMA_X, IDENTITY_2


def rotation_gate(theta: float, axis: np.ndarray = None) -> np.ndarray:
    """
    Generate a rotation gate around a specified Pauli axis.
    
    U(θ) = exp(-i θ σ / 2)
    
    Args:
        theta: Rotation angle in radians
        axis: Pauli matrix defining rotation axis
    
    Returns:
        2×2 complex unitary matrix
    """
    if axis is None:
        axis = SIGMA_X
    return expm(-1j * theta * axis / 2)


def generate_jitter_samples(n_samples: int, 
                           uniform_range: Tuple[float, float] = (-0.2, 0.2),
                           gaussian_std: float = 0.05) -> Dict[str, np.ndarray]:
    """
    Generate timing jitter samples from uniform and Gaussian distributions.
    
    Args:
        n_samples: Number of jitter samples to generate
        uniform_range: (min, max) for uniform distribution
        gaussian_std: Standard deviation for Gaussian distribution (mean=0)
    
    Returns:
        Dictionary with 'uniform' and 'gaussian' jitter arrays
    """
    jitter = {
        'uniform': np.random.uniform(uniform_range[0], uniform_range[1], n_samples),
        'gaussian': np.random.normal(0, gaussian_std, n_samples)
    }
    return jitter


def simulate_jitter_fidelity(theta_ideal: float,
                            jitter_values: np.ndarray,
                            initial_state: np.ndarray = None) -> np.ndarray:
    """
    Simulate fidelity degradation due to timing jitter.
    
    Args:
        theta_ideal: Target rotation angle (radians)
        jitter_values: Array of jitter perturbations (radians)
        initial_state: Starting quantum state (default: |0⟩)
    
    Returns:
        Array of fidelity values
    """
    if initial_state is None:
        initial_state = np.array([[1], [0]], dtype=complex)
    
    U_ideal = rotation_gate(theta_ideal)
    state_ideal = U_ideal @ initial_state
    
    fidelities = np.zeros(len(jitter_values))
    
    for i, delta_theta in enumerate(jitter_values):
        theta_noisy = theta_ideal + delta_theta
        U_noisy = rotation_gate(theta_noisy)
        state_noisy = U_noisy @ initial_state
        
        # Compute fidelity
        overlap = np.vdot(state_ideal, state_noisy)
        fidelities[i] = np.abs(overlap) ** 2
    
    return fidelities


def analytical_fidelity(delta_theta: np.ndarray) -> np.ndarray:
    """
    Compute analytical fidelity for rotation errors.
    
    F_analytical = cos²(δθ / 2)
    
    Args:
        delta_theta: Array of rotation angle errors (radians)
    
    Returns:
        Array of analytical fidelity values
    """
    return np.cos(delta_theta / 2) ** 2


def compute_infidelity(fidelity: np.ndarray) -> np.ndarray:
    """
    Compute infidelity (error rate) from fidelity.
    
    Infidelity: ε = 1 - F
    
    Args:
        fidelity: Array of fidelity values
    
    Returns:
        Array of infidelity values
    """
    return 1 - fidelity


def compute_sensitivity(theta_ideal: float, 
                       delta_theta_range: float = 1e-4,
                       n_points: int = 5) -> float:
    """
    Compute fidelity sensitivity using finite differences.
    
    Sensitivity: dF/dθ evaluated near δθ = 0
    
    Args:
        theta_ideal: Nominal rotation angle
        delta_theta_range: Range for finite difference
        n_points: Number of points for numerical derivative
    
    Returns:
        Sensitivity coefficient dF/dθ at δθ = 0
    """
    delta_theta_vals = np.linspace(-delta_theta_range, delta_theta_range, n_points)
    fidelities = simulate_jitter_fidelity(theta_ideal, delta_theta_vals)
    
    h = delta_theta_vals[1] - delta_theta_vals[0]
    sensitivity = np.gradient(fidelities, h)
    
    center_idx = len(sensitivity) // 2
    return sensitivity[center_idx]


def compute_robustness_score(fidelity: np.ndarray) -> float:
    """
    Compute robustness score from fidelity variance.
    
    Robustness: R = 1 / Var(F)
    
    Args:
        fidelity: Array of fidelity values
    
    Returns:
        Robustness score (higher is better)
    """
    variance = np.var(fidelity)
    
    if variance < 1e-12:
        return np.inf
    
    return 1.0 / variance
