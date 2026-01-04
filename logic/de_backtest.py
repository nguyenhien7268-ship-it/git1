#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
De Bridge Backtest Module
Provides backtest functionality for De (Special Prize) bridges
"""

def get_bridge_backtest(bridge_name, all_data, days=30):
    """
    Perform REAL backtest for a bridge over the last N days.
    Calculates prediction for EACH historical period using BacktestRunner.
    """
    try:
        from logic.backtest_runner import BacktestRunner
        
        # Initialize runner
        runner = BacktestRunner()
        
        # Run backtest
        # Note: This runs synchronously and might block UI slightly.
        # For 30 days it should be acceptable (< 1-2 sec).
        result = runner.run_backtest(bridge_name, all_data, days=days)
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'history': [],
            'win_rate': 0,
            'total_wins': 0,
            'total_tests': 0,
            'avg_streak': 0,
            'error': str(e)
        }
