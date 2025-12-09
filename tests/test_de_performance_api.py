# tests/test_de_performance_api.py
# Unit tests for DE performance evaluator API

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from logic.bridges.de_performance import (
    evaluate_de_visibility,
    compute_de_score,
    format_de_status,
    get_visibility_summary
)


def test_manual_override_show():
    """Test manual override with value=1 (show)."""
    bridge = {
        "name": "DE_DYN_Test",
        "de_manual_override": 1,
        "de_manual_override_value": 1,
        "de_win_count_last30": 10,  # Low wins, but override
        "de_auto_enabled": 0
    }
    
    visible, reason, needs_eval = evaluate_de_visibility(bridge)
    
    assert visible == True, "Manual override with value=1 should show"
    assert "manual override" in reason
    assert needs_eval == False
    print("✓ test_manual_override_show passed")


def test_manual_override_hide():
    """Test manual override with value=0 (hide)."""
    bridge = {
        "name": "DE_DYN_Test",
        "de_manual_override": 1,
        "de_manual_override_value": 0,
        "de_win_count_last30": 30,  # High wins, but override
        "de_auto_enabled": 1
    }
    
    visible, reason, needs_eval = evaluate_de_visibility(bridge)
    
    assert visible == False, "Manual override with value=0 should hide"
    assert "manual override" in reason
    assert needs_eval == False
    print("✓ test_manual_override_hide passed")


def test_auto_enabled_flag():
    """Test auto enabled flag."""
    bridge = {
        "name": "DE_DYN_Test",
        "de_manual_override": 0,
        "de_auto_enabled": 1,
        "de_win_count_last30": 20  # Below threshold, but auto-enabled
    }
    
    visible, reason, needs_eval = evaluate_de_visibility(bridge)
    
    assert visible == True, "Auto enabled should show"
    assert "auto flag" in reason
    assert needs_eval == False
    print("✓ test_auto_enabled_flag passed")


def test_wins_above_enable_threshold():
    """Test wins >= enable threshold (28)."""
    bridge = {
        "name": "DE_DYN_Test",
        "de_manual_override": 0,
        "de_auto_enabled": 0,
        "de_win_count_last30": 28
    }
    
    visible, reason, needs_eval = evaluate_de_visibility(bridge)
    
    assert visible == True, "Wins >= 28 should show"
    assert "28" in reason and "enable_threshold" in reason
    assert needs_eval == False
    print("✓ test_wins_above_enable_threshold passed")


def test_wins_below_disable_threshold():
    """Test wins <= disable threshold (26)."""
    bridge = {
        "name": "DE_DYN_Test",
        "de_manual_override": 0,
        "de_auto_enabled": 0,
        "de_win_count_last30": 26
    }
    
    visible, reason, needs_eval = evaluate_de_visibility(bridge)
    
    assert visible == False, "Wins <= 26 should hide"
    assert "26" in reason and "disable_threshold" in reason
    assert needs_eval == False
    print("✓ test_wins_below_disable_threshold passed")


def test_hysteresis_zone_prev_enabled():
    """Test hysteresis zone (27) with prev enabled."""
    bridge = {
        "name": "DE_DYN_Test",
        "de_manual_override": 0,
        "de_auto_enabled": 1,  # Previous state
        "de_win_count_last30": 27
    }
    
    visible, reason, needs_eval = evaluate_de_visibility(bridge)
    
    # Note: auto_enabled=1 takes precedence, so it shows due to auto flag
    assert visible == True, "Hysteresis with prev=1 should show"
    assert needs_eval == False
    print("✓ test_hysteresis_zone_prev_enabled passed")


def test_hysteresis_zone_prev_disabled():
    """Test hysteresis zone (27) with prev disabled."""
    bridge = {
        "name": "DE_DYN_Test",
        "de_manual_override": 0,
        "de_auto_enabled": 0,  # Previous state
        "de_win_count_last30": 27
    }
    
    visible, reason, needs_eval = evaluate_de_visibility(bridge)
    
    assert visible == False, "Hysteresis with prev=0 should hide"
    assert "hysteresis" in reason
    assert needs_eval == False
    print("✓ test_hysteresis_zone_prev_disabled passed")


def test_no_metrics_needs_evaluation():
    """Test bridge with no metrics."""
    bridge = {
        "name": "DE_DYN_Test",
        "de_manual_override": 0,
        "de_auto_enabled": 0
        # No de_win_count_last30, no current_streak, no streak
    }
    
    visible, reason, needs_eval = evaluate_de_visibility(bridge)
    
    assert visible == False, "No metrics should hide"
    assert "no metrics" in reason
    assert needs_eval == True, "Should be marked needs_evaluation"
    print("✓ test_no_metrics_needs_evaluation passed")


def test_legacy_current_streak_fallback():
    """Test fallback to legacy current_streak field."""
    bridge = {
        "name": "DE_DYN_Test",
        "de_manual_override": 0,
        "de_auto_enabled": 0,
        "current_streak": 28  # Legacy field
        # No de_win_count_last30
    }
    
    visible, reason, needs_eval = evaluate_de_visibility(bridge)
    
    assert visible == True, "Legacy current_streak=28 should show"
    assert needs_eval == False
    print("✓ test_legacy_current_streak_fallback passed")


def test_compute_de_score():
    """Test DE score computation."""
    # Perfect score (30/30)
    score = compute_de_score(30, 30)
    assert score == 10.0, f"Expected 10.0, got {score}"
    
    # 28/30 = 93.3% = 9.33
    score = compute_de_score(28, 30)
    assert 9.3 <= score <= 9.4, f"Expected ~9.33, got {score}"
    
    # 15/30 = 50% = 5.0
    score = compute_de_score(15, 30)
    assert score == 5.0, f"Expected 5.0, got {score}"
    
    # 0/30 = 0% = 0.0
    score = compute_de_score(0, 30)
    assert score == 0.0, f"Expected 0.0, got {score}"
    
    print("✓ test_compute_de_score passed")


def test_format_de_status():
    """Test status formatting."""
    bridge = {
        "name": "DE_DYN_Test",
        "de_win_count_last30": 28,
        "de_win_rate_last30": 93.3,
        "de_score": 9.33,
        "de_auto_enabled": 0,
        "de_manual_override": 0
    }
    
    status = format_de_status(bridge)
    
    assert "✓" in status, "Should show checkmark for visible"
    assert "Visible=True" in status
    assert "Wins=28" in status
    assert "93.3" in status
    print(f"  Status: {status}")
    print("✓ test_format_de_status passed")


def test_get_visibility_summary():
    """Test visibility summary for multiple bridges."""
    bridges = [
        {"name": "B1", "de_manual_override": 1, "de_manual_override_value": 1},
        {"name": "B2", "de_auto_enabled": 1, "de_win_count_last30": 20},
        {"name": "B3", "de_win_count_last30": 28, "de_auto_enabled": 0, "de_manual_override": 0},
        {"name": "B4", "de_win_count_last30": 25, "de_auto_enabled": 0, "de_manual_override": 0},
        {"name": "B5", "de_auto_enabled": 0, "de_manual_override": 0},  # No metrics
    ]
    
    summary = get_visibility_summary(bridges)
    
    assert summary["total"] == 5
    assert summary["visible"] == 3, f"Expected 3 visible, got {summary['visible']}"
    assert summary["hidden"] == 2, f"Expected 2 hidden, got {summary['hidden']}"
    assert summary["needs_evaluation"] == 1, f"Expected 1 needs eval, got {summary['needs_evaluation']}"
    assert summary["manual_override"] >= 1
    assert summary["auto_enabled"] >= 1
    
    print(f"  Summary: {summary['visible']}/{summary['total']} visible, {summary['needs_evaluation']} need eval")
    print("✓ test_get_visibility_summary passed")


def test_custom_thresholds():
    """Test with custom thresholds."""
    bridge = {
        "name": "DE_DYN_Test",
        "de_win_count_last30": 25,
        "de_auto_enabled": 0,
        "de_manual_override": 0
    }
    
    # Default thresholds (enable=28, disable=26)
    visible_default, _, _ = evaluate_de_visibility(bridge)
    assert visible_default == False, "25 < 26, should hide with default"
    
    # Custom lower thresholds (enable=24, disable=22)
    custom_thresholds = {"enable": 24, "disable": 22, "window": 30}
    visible_custom, _, _ = evaluate_de_visibility(bridge, custom_thresholds)
    assert visible_custom == True, "25 >= 24, should show with custom"
    
    print("✓ test_custom_thresholds passed")


if __name__ == "__main__":
    # Run tests manually
    test_manual_override_show()
    test_manual_override_hide()
    test_auto_enabled_flag()
    test_wins_above_enable_threshold()
    test_wins_below_disable_threshold()
    test_hysteresis_zone_prev_enabled()
    test_hysteresis_zone_prev_disabled()
    test_no_metrics_needs_evaluation()
    test_legacy_current_streak_fallback()
    test_compute_de_score()
    test_format_de_status()
    test_get_visibility_summary()
    test_custom_thresholds()
    print("\n✅ All DE performance API tests passed!")
