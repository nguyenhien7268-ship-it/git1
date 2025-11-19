"""
Backtest module - Refactored backtesting functions

This package splits the original backtester_core.py (913 LOC) into smaller,
more maintainable modules (~260-390 LOC each).

Modules:
- backtest_k2n: K2N mode backtest functions (391 LOC)
- backtest_n1: N1 mode backtest functions (266 LOC)
- backtest_custom: Custom bridge and memory bridge backtest functions (341 LOC)
"""

# Re-export all backtest functions for backward compatibility
from .backtest_k2n import (
    BACKTEST_15_CAU_K2N_V30_AI_V8,
    BACKTEST_MANAGED_BRIDGES_K2N,
)

from .backtest_n1 import (
    BACKTEST_15_CAU_N1_V31_AI_V8,
    BACKTEST_MANAGED_BRIDGES_N1,
)

from .backtest_custom import (
    BACKTEST_CUSTOM_CAU_V16,
    BACKTEST_MEMORY_BRIDGES,
)

__all__ = [
    'BACKTEST_15_CAU_K2N_V30_AI_V8',
    'BACKTEST_MANAGED_BRIDGES_K2N',
    'BACKTEST_15_CAU_N1_V31_AI_V8',
    'BACKTEST_MANAGED_BRIDGES_N1',
    'BACKTEST_CUSTOM_CAU_V16',
    'BACKTEST_MEMORY_BRIDGES',
]
