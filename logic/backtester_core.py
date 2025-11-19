"""
backtester_core.py - Core backtesting functions (REFACTORED)

This module has been refactored to split 913 LOC into smaller modules:
- logic/backtest/backtest_k2n.py (395 LOC)
- logic/backtest/backtest_n1.py (270 LOC)
- logic/backtest/backtest_custom.py (345 LOC)

This file maintains backward compatibility by re-exporting all functions.
"""

# Import all backtest functions from refactored modules
from .backtest import (
    BACKTEST_15_CAU_K2N_V30_AI_V8,
    BACKTEST_MANAGED_BRIDGES_K2N,
    BACKTEST_15_CAU_N1_V31_AI_V8,
    BACKTEST_MANAGED_BRIDGES_N1,
    BACKTEST_CUSTOM_CAU_V16,
    BACKTEST_MEMORY_BRIDGES,
)

# Re-export commonly used dependencies for backward compatibility
try:
    from .config_manager import SETTINGS
except ImportError:
    try:
        from .constants import DEFAULT_SETTINGS
    except ImportError:
        from constants import DEFAULT_SETTINGS
    SETTINGS = type("obj", (object,), DEFAULT_SETTINGS)

try:
    from .bridges.bridges_classic import ALL_15_BRIDGE_FUNCTIONS_V5
except ImportError:
    ALL_15_BRIDGE_FUNCTIONS_V5 = []

try:
    from .db_manager import DB_NAME
except ImportError:
    DB_NAME = "data/xo_so_prizes_all_logic.db"

__all__ = [
    'BACKTEST_15_CAU_K2N_V30_AI_V8',
    'BACKTEST_MANAGED_BRIDGES_K2N',
    'BACKTEST_15_CAU_N1_V31_AI_V8',
    'BACKTEST_MANAGED_BRIDGES_N1',
    'BACKTEST_CUSTOM_CAU_V16',
    'BACKTEST_MEMORY_BRIDGES',
    'SETTINGS',
    'ALL_15_BRIDGE_FUNCTIONS_V5',
    'DB_NAME',
]
