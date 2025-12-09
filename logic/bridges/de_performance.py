# logic/bridges/de_performance.py
"""
DE Performance Evaluator

Pure functions for evaluating DE bridge visibility and performance.
No database writes - evaluation only.

Usage:
    from logic.bridges.de_performance import evaluate_de_visibility
    
    visible, reason = evaluate_de_visibility(bridge, thresholds)
"""


def evaluate_de_visibility(bridge, thresholds=None):
    """
    Evaluate if a DE_DYN bridge should be visible based on performance metrics.
    
    Implements the visibility policy with precedence:
    1. Manual override (de_manual_override == 1): use de_manual_override_value
    2. Auto enabled (de_auto_enabled == 1): show
    3. Computed metrics with hysteresis: check de_win_count_last30
    
    Args:
        bridge: Bridge dict with metrics from DB
        thresholds: Optional dict with 'enable', 'disable', 'window' keys
                   If None, uses defaults: enable=28, disable=26, window=30
    
    Returns:
        tuple: (visible: bool, reason: str, needs_evaluation: bool)
        
    Examples:
        >>> bridge = {"de_manual_override": 1, "de_manual_override_value": 1}
        >>> visible, reason, needs_eval = evaluate_de_visibility(bridge)
        >>> print(visible, reason)
        True "manual override (value=1)"
        
        >>> bridge = {"de_auto_enabled": 1, "de_win_count_last30": 20}
        >>> visible, reason, needs_eval = evaluate_de_visibility(bridge)
        >>> print(visible)
        True
        
        >>> bridge = {"de_win_count_last30": 28, "de_auto_enabled": 0}
        >>> visible, reason, needs_eval = evaluate_de_visibility(bridge)
        >>> print(visible)
        True
    """
    # Load thresholds
    if thresholds is None:
        thresholds = {
            "enable": 28,
            "disable": 26,
            "window": 30
        }
    
    enable_threshold = thresholds.get("enable", 28)
    disable_threshold = thresholds.get("disable", 26)
    window = thresholds.get("window", 30)
    
    bridge_name = bridge.get("name", "N/A")
    
    # Priority 1: Manual override
    de_manual_override = bridge.get("de_manual_override", 0)
    if de_manual_override == 1:
        de_manual_override_value = bridge.get("de_manual_override_value", 0)
        visible = bool(de_manual_override_value)
        reason = f"manual override (value={de_manual_override_value})"
        return visible, reason, False
    
    # Priority 2: Auto enabled flag
    de_auto_enabled = bridge.get("de_auto_enabled", 0)
    if de_auto_enabled == 1:
        return True, "auto flag true", False
    
    # Priority 3: Computed metrics with hysteresis
    de_win_count_last30 = bridge.get("de_win_count_last30")
    
    if de_win_count_last30 is None:
        # Try legacy fields as fallback
        current_streak = bridge.get("current_streak")
        streak = bridge.get("streak")
        
        if current_streak is not None:
            wins_last30 = int(current_streak) if current_streak <= window else int((current_streak / 100.0) * window)
        elif streak is not None:
            wins_last30 = int(streak) if streak <= window else int((streak / 100.0) * window)
        else:
            # No metrics available - mark for evaluation and hide
            return False, "no metrics available", True
    else:
        wins_last30 = int(de_win_count_last30)
    
    # Apply hysteresis thresholds
    if wins_last30 >= enable_threshold:
        return True, f"wins30={wins_last30} >= enable_threshold={enable_threshold}", False
    elif wins_last30 <= disable_threshold:
        return False, f"wins30={wins_last30} <= disable_threshold={disable_threshold}", False
    else:
        # In hysteresis zone: check previous auto_enabled state
        prev_auto_enabled = bridge.get("de_auto_enabled", 0)
        if prev_auto_enabled == 1:
            return True, f"wins30={wins_last30} in hysteresis zone, prev_auto=1", False
        else:
            return False, f"wins30={wins_last30} in hysteresis zone, prev_auto=0", False


def compute_de_score(wins_count, total_periods=30):
    """
    Compute a simple DE performance score.
    
    Args:
        wins_count: Number of wins in the period
        total_periods: Total number of periods evaluated (default 30)
    
    Returns:
        float: Score from 0.0 to 10.0
    """
    if total_periods <= 0:
        return 0.0
    
    win_rate = wins_count / total_periods
    score = win_rate * 10.0
    return round(score, 2)


def format_de_status(bridge, thresholds=None):
    """
    Format a human-readable status string for a DE bridge.
    
    Args:
        bridge: Bridge dict with metrics
        thresholds: Optional thresholds dict
    
    Returns:
        str: Formatted status string
    """
    visible, reason, needs_eval = evaluate_de_visibility(bridge, thresholds)
    
    status_icon = "✓" if visible else "✗"
    eval_flag = " [NEEDS EVAL]" if needs_eval else ""
    
    wins = bridge.get("de_win_count_last30", "?")
    rate = bridge.get("de_win_rate_last30", "?")
    score = bridge.get("de_score", "?")
    
    return f"{status_icon} Visible={visible} | Wins={wins}/30 ({rate}%) | Score={score} | {reason}{eval_flag}"


def get_visibility_summary(bridges, thresholds=None):
    """
    Get a summary of visibility status for multiple bridges.
    
    Args:
        bridges: List of bridge dicts
        thresholds: Optional thresholds dict
    
    Returns:
        dict: Summary with counts and lists
    """
    summary = {
        "total": len(bridges),
        "visible": 0,
        "hidden": 0,
        "needs_evaluation": 0,
        "manual_override": 0,
        "auto_enabled": 0,
        "metric_based": 0
    }
    
    visible_bridges = []
    hidden_bridges = []
    needs_eval_bridges = []
    
    for bridge in bridges:
        visible, reason, needs_eval = evaluate_de_visibility(bridge, thresholds)
        
        if visible:
            summary["visible"] += 1
            visible_bridges.append(bridge)
        else:
            summary["hidden"] += 1
            hidden_bridges.append(bridge)
        
        if needs_eval:
            summary["needs_evaluation"] += 1
            needs_eval_bridges.append(bridge)
        
        # Categorize by decision type
        if "manual override" in reason:
            summary["manual_override"] += 1
        elif "auto flag" in reason:
            summary["auto_enabled"] += 1
        else:
            summary["metric_based"] += 1
    
    summary["visible_bridges"] = visible_bridges
    summary["hidden_bridges"] = hidden_bridges
    summary["needs_eval_bridges"] = needs_eval_bridges
    
    return summary


__all__ = [
    "evaluate_de_visibility",
    "compute_de_score",
    "format_de_status",
    "get_visibility_summary"
]
