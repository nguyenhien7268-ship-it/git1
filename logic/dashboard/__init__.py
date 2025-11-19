"""
Dashboard module - Refactored dashboard analytics functions

This package splits the original dashboard_analytics.py (827 LOC) into smaller,
more maintainable modules.

Modules:
- dashboard_stats: Statistics calculation functions (127 LOC)
- dashboard_predictions: Prediction functions (331 LOC)
- dashboard_scoring: Scoring functions (232 LOC)
- dashboard_simulation: Simulation and historical data functions (220 LOC)
"""

# Re-export all dashboard functions for backward compatibility
from .dashboard_stats import (
    get_loto_stats_last_n_days,
    get_loto_gan_stats,
)

from .dashboard_predictions import (
    get_top_memory_bridge_predictions,
    get_prediction_consensus,
    get_high_win_rate_predictions,
    get_pending_k2n_bridges,
)

from .dashboard_scoring import (
    get_top_scored_pairs,
)

from .dashboard_simulation import (
    get_consensus_simulation,
    get_high_win_simulation,
    get_historical_dashboard_data,
)

__all__ = [
    # Stats functions
    'get_loto_stats_last_n_days',
    'get_loto_gan_stats',
    # Prediction functions
    'get_top_memory_bridge_predictions',
    'get_prediction_consensus',
    'get_high_win_rate_predictions',
    'get_pending_k2n_bridges',
    # Scoring functions
    'get_top_scored_pairs',
    # Simulation functions
    'get_consensus_simulation',
    'get_high_win_simulation',
    'get_historical_dashboard_data',
]
