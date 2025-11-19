"""
dashboard_analytics.py - Dashboard analytics functions (REFACTORED)

This module has been refactored to split 827 LOC into smaller modules:
- logic/dashboard/dashboard_stats.py (127 LOC)
- logic/dashboard/dashboard_predictions.py (331 LOC)
- logic/dashboard/dashboard_scoring.py (232 LOC)
- logic/dashboard/dashboard_simulation.py (220 LOC)

This file maintains backward compatibility by re-exporting all functions.
"""

# Import all dashboard functions from refactored modules
from .dashboard import (
    # Stats functions
    get_loto_stats_last_n_days,
    get_loto_gan_stats,
    # Prediction functions
    get_top_memory_bridge_predictions,
    get_prediction_consensus,
    get_high_win_rate_predictions,
    get_pending_k2n_bridges,
    # Scoring functions
    get_top_scored_pairs,
    # Simulation functions
    get_consensus_simulation,
    get_high_win_simulation,
    get_historical_dashboard_data,
)

# Re-export DB_NAME for backward compatibility
try:
    from .db_manager import DB_NAME
except ImportError:
    DB_NAME = "data/xo_so_prizes_all_logic.db"

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
    # Constants
    'DB_NAME',
]
