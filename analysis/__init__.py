"""
QPOCS Analysis Module

Jitter analysis, crosstalk sweeps, and robustness analysis.
"""

from .jitter import *
from .crosstalk import *

__all__ = [
    # Jitter
    'generate_jitter_samples',
    'simulate_jitter_fidelity',
    'analytical_fidelity',
    'compute_infidelity',
    'compute_sensitivity',
    'compute_robustness_score',
    
    # Crosstalk
    'simulate_crosstalk',
    'sweep_coupling_strength',
    'sweep_pulse_duration',
    'sweep_2d_parameter_space',
]
