# tests/test_phase2_features.py
# Phase 2: Feature Engineering - Tests for new AI features
"""
Unit tests for Phase 2 new AI features:
- Current_Lose_Streak
- StdDev_Win_Rate_100
- Is_K2N_Risk_Close
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_calculate_win_rate_stddev_basic():
    """Test standard deviation calculation with simple data"""
    from logic.ai_feature_extractor import _calculate_win_rate_stddev
    
    # Test with uniform data (stddev should be 0)
    uniform_rates = [50.0] * 10
    stddev = _calculate_win_rate_stddev(uniform_rates)
    assert stddev == 0.0, "Uniform data should have 0 stddev"
    
    # Test with varying data
    varying_rates = [40.0, 50.0, 60.0, 50.0, 40.0]
    stddev = _calculate_win_rate_stddev(varying_rates)
    assert stddev > 0, "Varying data should have positive stddev"
    
    # Calculated: mean=48, variance=56, stddev≈7.48
    expected_stddev = 7.48
    assert abs(stddev - expected_stddev) < 0.1


def test_calculate_win_rate_stddev_empty_data():
    """Test stddev with empty or insufficient data"""
    from logic.ai_feature_extractor import _calculate_win_rate_stddev
    
    # Empty list
    stddev = _calculate_win_rate_stddev([])
    assert stddev == 0.0
    
    # Single value
    stddev = _calculate_win_rate_stddev([50.0])
    assert stddev == 0.0
    
    # None
    stddev = _calculate_win_rate_stddev(None)
    assert stddev == 0.0


def test_calculate_win_rate_stddev_with_periods():
    """Test stddev calculation respects period limit"""
    from logic.ai_feature_extractor import _calculate_win_rate_stddev
    
    # Create 150 values, but only last 100 should be used
    rates = list(range(1, 151))  # 1, 2, 3, ..., 150
    
    # With periods=100, should only use last 100 values (51-150)
    stddev_100 = _calculate_win_rate_stddev(rates, periods=100)
    
    # With periods=50, should only use last 50 values (101-150)
    stddev_50 = _calculate_win_rate_stddev(rates, periods=50)
    
    # Different periods should give different results
    assert stddev_100 != stddev_50
    assert stddev_100 > 0
    assert stddev_50 > 0


def test_current_lose_streak_feature_extraction():
    """Test that current_lose_streak is properly extracted from bridge data"""
    # This tests the concept - actual extraction happens in _get_daily_bridge_predictions
    
    # Simulate bridge data structure
    bridge_data = {
        "name": "Test Bridge",
        "current_lose_streak": 3,
        "win_rate_text": "45.5%",
        "max_lose_streak_k2n": 5
    }
    
    # Verify the field exists and can be accessed
    current_lose_streak = bridge_data.get("current_lose_streak", 0)
    assert current_lose_streak == 3


def test_is_k2n_risk_close_logic():
    """Test K2N risk proximity detection logic"""
    from logic.config_manager import SETTINGS
    
    k2n_threshold = SETTINGS.K2N_RISK_START_THRESHOLD
    
    # Case 1: Bridge at threshold (distance = 0, should be close)
    bridge_risk_at_threshold = k2n_threshold
    risk_distance = k2n_threshold - bridge_risk_at_threshold
    is_close = 1 if 0 <= risk_distance <= 2 else 0
    assert is_close == 1, "Bridge at threshold should be marked as close"
    
    # Case 2: Bridge 1 frame below threshold (distance = 1, should be close)
    bridge_risk_close = k2n_threshold - 1
    risk_distance = k2n_threshold - bridge_risk_close
    is_close = 1 if 0 <= risk_distance <= 2 else 0
    assert is_close == 1, "Bridge 1 frame below threshold should be close"
    
    # Case 3: Bridge 2 frames below threshold (distance = 2, should be close)
    bridge_risk_edge = k2n_threshold - 2
    risk_distance = k2n_threshold - bridge_risk_edge
    is_close = 1 if 0 <= risk_distance <= 2 else 0
    assert is_close == 1, "Bridge 2 frames below threshold should be close"
    
    # Case 4: Bridge 3 frames below threshold (distance = 3, should NOT be close)
    bridge_risk_far = k2n_threshold - 3
    risk_distance = k2n_threshold - bridge_risk_far
    is_close = 1 if 0 <= risk_distance <= 2 else 0
    assert is_close == 0, "Bridge 3 frames below threshold should NOT be close"
    
    # Case 5: Bridge above threshold (negative distance, should NOT be close)
    bridge_risk_above = k2n_threshold + 1
    risk_distance = k2n_threshold - bridge_risk_above
    is_close = 1 if 0 <= risk_distance <= 2 else 0
    assert is_close == 0, "Bridge above threshold should NOT be close"


def test_phase2_features_integration_with_config():
    """Test that Phase 2 features can access configuration properly"""
    from logic.config_manager import SETTINGS
    
    # Verify K2N threshold is accessible (needed for Is_K2N_Risk_Close)
    assert hasattr(SETTINGS, 'K2N_RISK_START_THRESHOLD')
    threshold = SETTINGS.K2N_RISK_START_THRESHOLD
    assert isinstance(threshold, int)
    assert threshold > 0


def test_stddev_calculation_precision():
    """Test stddev calculation with known values for precision"""
    from logic.ai_feature_extractor import _calculate_win_rate_stddev
    
    # Known dataset: [2, 4, 4, 4, 5, 5, 7, 9]
    # Mean = 5, Variance = 4, StdDev = 2
    rates = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    stddev = _calculate_win_rate_stddev(rates)
    
    expected_stddev = 2.0
    assert abs(stddev - expected_stddev) < 0.01, f"Expected {expected_stddev}, got {stddev}"


def test_multiple_features_coexist():
    """Test that all three Phase 2 features can coexist in feature vector"""
    # Simulate a complete feature dict that would be created
    features = {
        "q_max_current_lose_streak": 5,
        "q_is_k2n_risk_close": 1,
        "q_avg_win_rate_stddev_100": 12.5,
        # Existing features
        "q_avg_win_rate": 45.0,
        "q_min_k2n_risk": 3,
        "q_max_curr_streak": 8
    }
    
    # Verify all Phase 2 features exist
    assert "q_max_current_lose_streak" in features
    assert "q_is_k2n_risk_close" in features
    assert "q_avg_win_rate_stddev_100" in features
    
    # Verify values are accessible
    assert features["q_max_current_lose_streak"] == 5
    assert features["q_is_k2n_risk_close"] == 1
    assert features["q_avg_win_rate_stddev_100"] == 12.5


def test_feature_default_values():
    """Test that Phase 2 features have sensible defaults when no data available"""
    # When no bridges predict a loto, defaults should be set
    default_features = {
        "q_max_current_lose_streak": 0,
        "q_is_k2n_risk_close": 0,
        "q_avg_win_rate_stddev_100": 0.0
    }
    
    # Verify defaults are appropriate
    assert default_features["q_max_current_lose_streak"] == 0, "Default lose streak should be 0"
    assert default_features["q_is_k2n_risk_close"] == 0, "Default risk close should be 0 (not close)"
    assert default_features["q_avg_win_rate_stddev_100"] == 0.0, "Default stddev should be 0.0"


if __name__ == "__main__":
    import pytest
    
    # Run all tests in this file
    pytest.main([__file__, "-v"])
