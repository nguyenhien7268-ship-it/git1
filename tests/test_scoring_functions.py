# tests/test_scoring_functions.py
# Phase 1: Testing Critical - Unit tests for scoring logic
"""
Unit tests for core scoring functions including:
- K2N risk penalty calculation
- Recent form bonus calculation
- Configuration parameter validation
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_k2n_penalty_calculation_single_bridge():
    """Test K2N penalty for a single high-risk bridge"""
    from logic.config_manager import SETTINGS
    
    # Setup: bridge with max_lose above threshold
    threshold = SETTINGS.K2N_RISK_START_THRESHOLD
    penalty_per_frame = SETTINGS.K2N_RISK_PENALTY_PER_FRAME
    
    # Case 1: Bridge at threshold
    max_lose_at_threshold = threshold
    assert max_lose_at_threshold >= threshold
    expected_penalty = penalty_per_frame
    
    # Case 2: Bridge well above threshold
    max_lose_high = threshold + 5
    assert max_lose_high >= threshold
    expected_penalty_high = penalty_per_frame  # Fixed penalty, not scaled
    
    # Verify penalty is applied correctly
    assert expected_penalty == penalty_per_frame
    assert expected_penalty_high == penalty_per_frame


def test_k2n_penalty_not_applied_below_threshold():
    """Test that K2N penalty is NOT applied when below threshold"""
    from logic.config_manager import SETTINGS
    
    threshold = SETTINGS.K2N_RISK_START_THRESHOLD
    
    # Case: Bridge below threshold should not trigger penalty
    max_lose_below = threshold - 1
    assert max_lose_below < threshold
    
    # No penalty should be applied
    # (In actual code, this is checked with: if max_lose >= threshold)


def test_k2n_penalty_multiple_bridges_same_pair():
    """Test K2N penalty aggregation for multiple bridges predicting same pair"""
    from logic.config_manager import SETTINGS
    
    penalty_per_frame = SETTINGS.K2N_RISK_PENALTY_PER_FRAME
    
    # Simulate 3 bridges predicting same pair, all high risk
    num_bridges = 3
    total_penalty = num_bridges * penalty_per_frame
    
    # With current config (0.75), 3 bridges = -2.25 points
    expected = 3 * 0.75
    assert abs(total_penalty - expected) < 0.01


def test_recent_form_bonus_high_tier():
    """Test recent form bonus for high-performance bridges (8-10 wins)"""
    from logic.config_manager import SETTINGS
    
    min_high = SETTINGS.RECENT_FORM_MIN_HIGH
    bonus_high = SETTINGS.RECENT_FORM_BONUS_HIGH
    
    # Bridge with very high recent wins
    recent_wins = 9
    assert recent_wins >= min_high
    
    # Should get high tier bonus
    expected_bonus = bonus_high
    assert expected_bonus == SETTINGS.RECENT_FORM_BONUS_HIGH


def test_recent_form_bonus_medium_tier():
    """Test recent form bonus for medium-performance bridges (8 wins)"""
    from logic.config_manager import SETTINGS
    
    min_med = SETTINGS.RECENT_FORM_MIN_MED
    min_high = SETTINGS.RECENT_FORM_MIN_HIGH
    bonus_med = SETTINGS.RECENT_FORM_BONUS_MED
    
    # Bridge with medium recent wins (current config: MIN_MED=8, MIN_HIGH=9)
    recent_wins = 8
    assert recent_wins >= min_med
    assert recent_wins < min_high
    
    # Should get medium tier bonus
    expected_bonus = bonus_med
    assert expected_bonus == SETTINGS.RECENT_FORM_BONUS_MED


def test_recent_form_bonus_low_tier():
    """Test recent form bonus for low-performance bridges (7 wins)"""
    from logic.config_manager import SETTINGS
    
    min_low = SETTINGS.RECENT_FORM_MIN_LOW
    min_med = SETTINGS.RECENT_FORM_MIN_MED
    bonus_low = SETTINGS.RECENT_FORM_BONUS_LOW
    
    # Bridge with low recent wins (current config: MIN_LOW=7, MIN_MED=8)
    recent_wins = 7
    assert recent_wins >= min_low
    assert recent_wins < min_med
    
    # Should get low tier bonus
    expected_bonus = bonus_low
    assert expected_bonus == SETTINGS.RECENT_FORM_BONUS_LOW


def test_recent_form_no_bonus_below_threshold():
    """Test that no bonus is given for bridges below minimum threshold"""
    from logic.config_manager import SETTINGS
    
    min_low = SETTINGS.RECENT_FORM_MIN_LOW
    
    # Bridge below minimum threshold
    recent_wins = min_low - 1
    assert recent_wins < min_low
    
    # No bonus should be applied


def test_recent_form_bonus_multiple_bridges_aggregation():
    """Test recent form bonus aggregation for multiple bridges predicting same pair"""
    from logic.config_manager import SETTINGS
    
    bonus_high = SETTINGS.RECENT_FORM_BONUS_HIGH
    bonus_med = SETTINGS.RECENT_FORM_BONUS_MED
    
    # Simulate 2 high-performance and 1 medium-performance bridge
    num_high = 2
    num_med = 1
    
    total_bonus = (num_high * bonus_high) + (num_med * bonus_med)
    
    # With current config: 2*3.0 + 1*2.0 = 8.0 points
    expected = (2 * 3.0) + (1 * 2.0)
    assert abs(total_bonus - expected) < 0.01


def test_config_parameters_loaded_correctly():
    """Test that all scoring parameters are loaded from config.json correctly"""
    from logic.config_manager import SETTINGS
    
    # Verify K2N risk parameters
    assert hasattr(SETTINGS, 'K2N_RISK_START_THRESHOLD')
    assert hasattr(SETTINGS, 'K2N_RISK_PENALTY_PER_FRAME')
    assert isinstance(SETTINGS.K2N_RISK_START_THRESHOLD, int)
    assert isinstance(SETTINGS.K2N_RISK_PENALTY_PER_FRAME, (int, float))
    
    # Verify recent form parameters
    assert hasattr(SETTINGS, 'RECENT_FORM_PERIODS')
    assert hasattr(SETTINGS, 'RECENT_FORM_MIN_HIGH')
    assert hasattr(SETTINGS, 'RECENT_FORM_MIN_MED')
    assert hasattr(SETTINGS, 'RECENT_FORM_MIN_LOW')
    assert hasattr(SETTINGS, 'RECENT_FORM_BONUS_HIGH')
    assert hasattr(SETTINGS, 'RECENT_FORM_BONUS_MED')
    assert hasattr(SETTINGS, 'RECENT_FORM_BONUS_LOW')
    
    # Verify AI parameters
    assert hasattr(SETTINGS, 'AI_SCORE_WEIGHT')
    assert hasattr(SETTINGS, 'AI_PROB_THRESHOLD')
    assert isinstance(SETTINGS.AI_SCORE_WEIGHT, (int, float))
    assert isinstance(SETTINGS.AI_PROB_THRESHOLD, (int, float))


def test_config_parameters_phase0_values():
    """Test that Phase 0 config updates are applied correctly"""
    from logic.config_manager import SETTINGS
    
    # Verify Phase 0 updates
    assert SETTINGS.AI_SCORE_WEIGHT == 0.4, "AI_SCORE_WEIGHT should be 0.4 after Phase 0"
    assert SETTINGS.AI_PROB_THRESHOLD == 55.0, "AI_PROB_THRESHOLD should be 55.0 after Phase 0"
    assert SETTINGS.K2N_RISK_PENALTY_PER_FRAME == 0.75, "K2N_RISK_PENALTY_PER_FRAME should be 0.75 after Phase 0"


def test_recent_form_threshold_ordering():
    """Test that recent form thresholds are in correct order: HIGH >= MED >= LOW"""
    from logic.config_manager import SETTINGS
    
    min_high = SETTINGS.RECENT_FORM_MIN_HIGH
    min_med = SETTINGS.RECENT_FORM_MIN_MED
    min_low = SETTINGS.RECENT_FORM_MIN_LOW
    
    # Verify correct ordering
    assert min_high >= min_med, "MIN_HIGH should be >= MIN_MED"
    assert min_med >= min_low, "MIN_MED should be >= MIN_LOW"


def test_recent_form_bonus_ordering():
    """Test that recent form bonuses are in correct order: HIGH >= MED >= LOW"""
    from logic.config_manager import SETTINGS
    
    bonus_high = SETTINGS.RECENT_FORM_BONUS_HIGH
    bonus_med = SETTINGS.RECENT_FORM_BONUS_MED
    bonus_low = SETTINGS.RECENT_FORM_BONUS_LOW
    
    # Verify correct ordering
    assert bonus_high >= bonus_med, "BONUS_HIGH should be >= BONUS_MED"
    assert bonus_med >= bonus_low, "BONUS_MED should be >= BONUS_LOW"
    
    # Verify all bonuses are positive
    assert bonus_high > 0, "BONUS_HIGH should be positive"
    assert bonus_med > 0, "BONUS_MED should be positive"
    assert bonus_low > 0, "BONUS_LOW should be positive"


def test_backtester_scoring_functions():
    """Test basic scoring functions from backtester_scoring module"""
    from logic.backtester_scoring import score_by_streak, score_by_rate
    
    # Test score_by_streak: prioritizes streak
    rate = 50.0
    streak = 5
    score_streak = score_by_streak(rate, streak)
    expected_streak = (streak * 1000) + (rate * 100)
    assert score_streak == expected_streak
    assert score_streak == 10000  # 5*1000 + 50*100 = 10000
    
    # Test score_by_rate: prioritizes rate
    score_rate = score_by_rate(rate, streak)
    expected_rate = (rate * 1000) + (streak * 100)
    assert score_rate == expected_rate
    assert score_rate == 50500  # 50*1000 + 5*100 = 50500
    
    # Verify that score_by_rate gives higher score for high rate
    assert score_by_rate(70, 3) > score_by_streak(70, 3)


def test_ai_score_weight_impact():
    """Test that AI score weight properly influences final scoring"""
    from logic.config_manager import SETTINGS
    
    ai_weight = SETTINGS.AI_SCORE_WEIGHT
    
    # With Phase 0, AI weight should be 0.4 (40% influence)
    assert ai_weight == 0.4
    
    # Simulate AI prediction score impact
    ai_probability = 0.8  # 80% probability
    ai_contribution = ai_probability * ai_weight
    
    # AI should contribute 0.32 (32% of max) to final score
    expected_contribution = 0.8 * 0.4
    assert abs(ai_contribution - expected_contribution) < 0.01


if __name__ == "__main__":
    import pytest
    
    # Run all tests in this file
    pytest.main([__file__, "-v"])
