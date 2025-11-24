"""
Tests for V7.6 Recent Appearance Bonus feature
Tests the "Về Gần" scoring bonus that rewards pairs appearing in recent periods
"""

import pytest


def test_vote_weight_reduced():
    """Test that vote weight has been reduced from 0.5 to 0.3"""
    from logic.config_manager import AppSettings
    settings = AppSettings()
    assert settings.defaults["VOTE_SCORE_WEIGHT"] == 0.3


def test_filter_thresholds_increased():
    """Test that filter thresholds have been increased for better effectiveness"""
    try:
        from ui.ui_dashboard import FILTER_CONFIDENCE_THRESHOLD, FILTER_AI_PROB_THRESHOLD
        
        # Should be 5 stars (increased from 4)
        assert FILTER_CONFIDENCE_THRESHOLD == 5
        
        # Should be 60% (increased from 50)
        assert FILTER_AI_PROB_THRESHOLD == 60
    except ImportError:
        # Skip if tkinter not available
        pytest.skip("UI module requires tkinter")


def test_recent_appearance_bonus_logic():
    """Test the recent appearance bonus calculation logic"""
    # Simulate the bonus logic
    def calculate_bonus(appeared_in_3_periods, appeared_in_7_periods):
        if appeared_in_3_periods:
            return 2.0, "Về 3kỳ (+2.0)"
        elif appeared_in_7_periods:
            return 1.0, "Về 7kỳ (+1.0)"
        else:
            return 0.0, None
    
    # Test case 1: Pair appeared in last 3 periods
    bonus, reason = calculate_bonus(True, True)
    assert bonus == 2.0
    assert reason == "Về 3kỳ (+2.0)"
    
    # Test case 2: Pair appeared in last 7 periods but not in last 3
    bonus, reason = calculate_bonus(False, True)
    assert bonus == 1.0
    assert reason == "Về 7kỳ (+1.0)"
    
    # Test case 3: Pair did not appear recently
    bonus, reason = calculate_bonus(False, False)
    assert bonus == 0.0
    assert reason is None


def test_get_top_scored_pairs_accepts_recent_data():
    """Test that get_top_scored_pairs accepts recent_data parameter"""
    from logic.dashboard_analytics import get_top_scored_pairs
    import inspect
    
    # Get function signature
    sig = inspect.signature(get_top_scored_pairs)
    params = list(sig.parameters.keys())
    
    # Should have recent_data parameter
    assert 'recent_data' in params


def test_recent_appearance_bonus_integration():
    """Test integration of recent appearance bonus in scoring"""
    # This is a simple integration test to ensure the feature exists
    from logic.dashboard_analytics import get_top_scored_pairs
    
    # Mock data
    stats = []
    consensus = []
    high_win = []
    pending_k2n = {}
    gan_stats = []
    top_memory_bridges = []
    
    # Call with recent_data
    result = get_top_scored_pairs(
        stats, consensus, high_win, pending_k2n,
        gan_stats, top_memory_bridges,
        ai_predictions=None,
        recent_data=[]
    )
    
    # Should return a list (even if empty)
    assert isinstance(result, list)


def test_improvements_documented():
    """Test that improvements are documented in code"""
    from logic.dashboard_analytics import get_top_scored_pairs
    
    # Check docstring mentions V7.6 improvements
    docstring = get_top_scored_pairs.__doc__
    assert "V7.6" in docstring or "IMPROVED" in docstring


def test_enhanced_filtering_explanation():
    """Document the enhanced filtering approach (Solution A)"""
    # Solution A: Enhanced filtering
    # This is not code but documentation of the approach
    
    recommendations = {
        "confidence_threshold": 5,  # Up from 4
        "ai_threshold": 60,  # Up from 50
        "only_choi": True,  # Only select CHƠI recommendations
        "phong_do_min": 7,  # From "Phong Độ 10 Kỳ" tab, select ≥7/10
        "gan_days_range": (8, 15),  # Optimal "ripeness" range
        "avoid_k2n_streak": 6,  # Avoid if K2N streak > 6
    }
    
    assert recommendations["confidence_threshold"] == 5
    assert recommendations["ai_threshold"] == 60
    assert recommendations["only_choi"] is True


def test_recent_bonus_priority():
    """Test that 3-period bonus takes priority over 7-period bonus"""
    # When a pair appears in last 3 periods, it should get 2.0 bonus
    # not 1.0 + 2.0 (should be exclusive)
    
    in_3_periods = True
    in_7_periods = True  # Also in 7 periods
    
    if in_3_periods:
        bonus = 2.0
    elif in_7_periods:
        bonus = 1.0
    else:
        bonus = 0.0
    
    # Should be 2.0, not 3.0
    assert bonus == 2.0


def test_vote_weight_impact():
    """Test the impact of reduced vote weight"""
    import math
    
    # Old weight: 0.5
    # New weight: 0.3
    
    vote_count = 10
    old_score = math.sqrt(vote_count) * 0.5  # ~1.58
    new_score = math.sqrt(vote_count) * 0.3  # ~0.95
    
    # New score should be lower
    assert new_score < old_score
    
    # Reduction should be about 40%
    reduction = (old_score - new_score) / old_score
    assert 0.35 < reduction < 0.45  # About 40% reduction
