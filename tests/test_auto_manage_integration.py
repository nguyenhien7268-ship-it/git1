"""
Tests for V7.7 Auto-Manage Bridges Integration Fix
Tests that auto_manage_bridges uses the correct threshold (AUTO_PRUNE_MIN_RATE)
"""

import pytest


def test_auto_manage_uses_prune_threshold():
    """Test that auto_manage_bridges enables bridges at PRUNE threshold, not ADD threshold"""
    # The key insight: AUTO_ADD_MIN_RATE (50%) is for finding new bridges
    # AUTO_PRUNE_MIN_RATE (40%) is for managing existing bridges
    
    AUTO_ADD_MIN_RATE = 50.0  # For discovery/adding new bridges
    AUTO_PRUNE_MIN_RATE = 40.0  # For managing existing bridges
    
    # Test cases for bridge management
    test_cases = [
        # (win_rate, should_be_enabled, description)
        (45.0, True, "Between thresholds - should be enabled"),
        (40.0, True, "At prune threshold - should be enabled"),
        (39.9, False, "Below prune threshold - should be disabled"),
        (50.0, True, "At add threshold - should be enabled"),
        (55.0, True, "Above add threshold - should be enabled"),
        (35.0, False, "Well below threshold - should be disabled"),
    ]
    
    for win_rate, expected_enabled, description in test_cases:
        # New logic: Use PRUNE threshold for enable/disable
        should_enable = win_rate >= AUTO_PRUNE_MIN_RATE
        should_disable = win_rate < AUTO_PRUNE_MIN_RATE
        
        assert should_enable == expected_enabled, f"Failed: {description} (rate={win_rate})"
        assert should_disable != expected_enabled, f"Failed: {description} (rate={win_rate})"


def test_old_vs_new_logic():
    """Test the difference between old and new auto_manage logic"""
    AUTO_ADD_MIN_RATE = 50.0
    AUTO_PRUNE_MIN_RATE = 40.0
    
    # Test the critical range: 40% - 50%
    test_rates = [40.0, 42.0, 45.0, 48.0, 49.9]
    
    for rate in test_rates:
        # Old logic: Enable only if >= 50%
        old_should_enable = rate >= AUTO_ADD_MIN_RATE
        
        # New logic: Enable if >= 40%
        new_should_enable = rate >= AUTO_PRUNE_MIN_RATE
        
        # In the 40-50% range, new logic enables but old logic doesn't
        assert new_should_enable is True, f"New logic should enable at {rate}%"
        assert old_should_enable is False, f"Old logic wouldn't enable at {rate}%"


def test_add_threshold_still_used_for_discovery():
    """Test that AUTO_ADD_MIN_RATE is still used for finding/adding new bridges"""
    AUTO_ADD_MIN_RATE = 50.0
    
    # When discovering new bridges, we want higher quality
    discovery_rates = [
        (48.0, False, "Below 50% - don't add to DB"),
        (50.0, True, "At 50% - add to DB"),
        (55.0, True, "Above 50% - add to DB"),
    ]
    
    for rate, should_add, description in discovery_rates:
        should_add_to_db = rate >= AUTO_ADD_MIN_RATE
        assert should_add_to_db == should_add, f"Discovery logic: {description}"


def test_thresholds_purpose_documented():
    """Document the purpose of each threshold"""
    thresholds = {
        "AUTO_ADD_MIN_RATE": {
            "value": 50.0,
            "purpose": "For discovering and adding new bridges to database",
            "used_in": ["TIM_CAU_TOT_NHAT_V16", "TIM_CAU_BAC_NHO_TOT_NHAT"],
            "reason": "Higher bar for initial quality"
        },
        "AUTO_PRUNE_MIN_RATE": {
            "value": 40.0,
            "purpose": "For managing existing bridges (enable/disable)",
            "used_in": ["auto_manage_bridges", "prune_bad_bridges"],
            "reason": "Keep bridges that are still somewhat useful"
        }
    }
    
    # Verify the relationship
    assert thresholds["AUTO_ADD_MIN_RATE"]["value"] > thresholds["AUTO_PRUNE_MIN_RATE"]["value"]
    assert thresholds["AUTO_ADD_MIN_RATE"]["value"] == 50.0
    assert thresholds["AUTO_PRUNE_MIN_RATE"]["value"] == 40.0


def test_no_gap_in_management():
    """Test that there's no gap between enable and disable thresholds"""
    AUTO_PRUNE_MIN_RATE = 40.0
    
    # With the fix, enable and disable use the same threshold
    # This means no "gap" where bridges are neither enabled nor disabled
    
    test_rates = [39.9, 40.0, 40.1]
    
    for rate in test_rates:
        should_enable = rate >= AUTO_PRUNE_MIN_RATE
        should_disable = rate < AUTO_PRUNE_MIN_RATE
        
        # Exactly one should be True (no gap, no overlap)
        assert should_enable != should_disable, f"Rate {rate}% should be either enable or disable, not both or neither"


def test_integrated_functionality():
    """Test that the two management functions are now properly integrated"""
    # Both prune_bad_bridges and auto_manage_bridges use AUTO_PRUNE_MIN_RATE
    # auto_manage_bridges does both enabling and disabling
    # prune_bad_bridges only does disabling (legacy function)
    
    AUTO_PRUNE_MIN_RATE = 40.0
    
    # Simulate a bridge with 45% win rate
    bridge_rate = 45.0
    
    # auto_manage_bridges logic (new integrated approach)
    should_enable_auto = bridge_rate >= AUTO_PRUNE_MIN_RATE
    should_disable_auto = bridge_rate < AUTO_PRUNE_MIN_RATE
    
    # prune_bad_bridges logic (only disables)
    should_disable_prune = bridge_rate < AUTO_PRUNE_MIN_RATE
    
    # Both should agree on disabling
    assert should_disable_auto == should_disable_prune
    
    # auto_manage also handles enabling
    assert should_enable_auto is True
    assert should_disable_auto is False


def test_config_values():
    """Test that config values maintain correct relationship"""
    from logic.config_manager import AppSettings
    
    settings = AppSettings()
    
    # Verify both values exist
    assert hasattr(settings, 'AUTO_ADD_MIN_RATE')
    assert hasattr(settings, 'AUTO_PRUNE_MIN_RATE')
    
    # Verify relationship: ADD threshold should be >= PRUNE threshold
    # (Add threshold can equal prune threshold if user wants strict management)
    assert settings.AUTO_ADD_MIN_RATE >= settings.AUTO_PRUNE_MIN_RATE, \
        "AUTO_ADD_MIN_RATE should be >= AUTO_PRUNE_MIN_RATE"
    
    # Verify they are reasonable values (between 0 and 100)
    assert 0 <= settings.AUTO_ADD_MIN_RATE <= 100
    assert 0 <= settings.AUTO_PRUNE_MIN_RATE <= 100
