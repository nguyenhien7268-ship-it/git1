"""
backtester_scoring.py - Scoring functions for bridge evaluation

Extracted from backtester.py to improve maintainability.
Contains: Scoring algorithms for ranking bridges.
"""


def score_by_streak(rate, streak):
    """
    Score bridges prioritizing streak over rate.
    
    Args:
        rate: Win rate percentage
        streak: Win streak count
        
    Returns:
        float: Calculated score
    """
    return (streak * 1000) + (rate * 100)


def score_by_rate(rate, streak):
    """
    Score bridges prioritizing rate over streak.
    
    Args:
        rate: Win rate percentage
        streak: Win streak count
        
    Returns:
        float: Calculated score
    """
    return (rate * 1000) + (streak * 100)
