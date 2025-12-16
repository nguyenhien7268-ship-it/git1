# tests/test_de_visibility_policy.py
# V11.0: Unit tests for DE visibility policy (auto/manual/hysteresis)

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch
from logic.dashboard_analytics import get_cau_dong_for_tab_soi_cau_de


def test_manual_override_show():
    """
    Test manual override: de_manual_override=1, de_manual_override_value=1
    Bridge should be visible even if metrics are low.
    """
    mock_bridges = [
        {
            "id": 1,
            "name": "DE_DYN_Manual_Show",
            "type": "DE_DYN",
            "de_manual_override": 1,
            "de_manual_override_value": 1,
            "de_win_count_last30": 20,  # Below threshold
            "de_auto_enabled": 0,
            "is_enabled": 1
        }
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de()
        
        assert len(result) == 1, f"Expected 1 bridge (manual override), got {len(result)}"
        assert result[0]["name"] == "DE_DYN_Manual_Show"
        print("✓ test_manual_override_show passed")


def test_manual_override_hide():
    """
    Test manual override: de_manual_override=1, de_manual_override_value=0
    Bridge should be hidden even if metrics are high.
    """
    mock_bridges = [
        {
            "id": 1,
            "name": "DE_DYN_Manual_Hide",
            "type": "DE_DYN",
            "de_manual_override": 1,
            "de_manual_override_value": 0,
            "de_win_count_last30": 29,  # Above threshold
            "de_auto_enabled": 1,  # Would normally show
            "is_enabled": 1
        }
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de()
        
        assert len(result) == 0, f"Expected 0 bridges (manual hide), got {len(result)}"
        print("✓ test_manual_override_hide passed")


def test_auto_enabled_flag():
    """
    Test auto enabled: de_auto_enabled=1
    Bridge should be visible even if metrics are below threshold.
    """
    mock_bridges = [
        {
            "id": 1,
            "name": "DE_DYN_Auto_Enabled",
            "type": "DE_DYN",
            "de_manual_override": 0,
            "de_auto_enabled": 1,
            "de_win_count_last30": 25,  # Below enable threshold
            "is_enabled": 1
        }
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de()
        
        assert len(result) == 1, f"Expected 1 bridge (auto enabled), got {len(result)}"
        assert result[0]["name"] == "DE_DYN_Auto_Enabled"
        print("✓ test_auto_enabled_flag passed")


def test_wins_above_enable_threshold():
    """
    Test computed metrics: wins_last30 = 28 (>= enable threshold)
    Bridge should be visible.
    """
    mock_bridges = [
        {
            "id": 1,
            "name": "DE_DYN_High_Wins",
            "type": "DE_DYN",
            "de_manual_override": 0,
            "de_auto_enabled": 0,
            "de_win_count_last30": 28,
            "is_enabled": 1
        }
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de()
        
        assert len(result) == 1, f"Expected 1 bridge (wins >= 28), got {len(result)}"
        assert result[0]["name"] == "DE_DYN_High_Wins"
        print("✓ test_wins_above_enable_threshold passed")


def test_wins_below_disable_threshold():
    """
    Test computed metrics: wins_last30 = 26 (<= disable threshold)
    Bridge should be hidden.
    """
    mock_bridges = [
        {
            "id": 1,
            "name": "DE_DYN_Low_Wins",
            "type": "DE_DYN",
            "de_manual_override": 0,
            "de_auto_enabled": 0,
            "de_win_count_last30": 26,
            "is_enabled": 1
        }
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de()
        
        assert len(result) == 0, f"Expected 0 bridges (wins <= 26), got {len(result)}"
        print("✓ test_wins_below_disable_threshold passed")


def test_hysteresis_zone_with_prev_enabled():
    """
    Test hysteresis: wins_last30 = 27 (in zone), prev de_auto_enabled = 1
    Bridge should remain visible.
    """
    mock_bridges = [
        {
            "id": 1,
            "name": "DE_DYN_Hysteresis_Enabled",
            "type": "DE_DYN",
            "de_manual_override": 0,
            "de_auto_enabled": 1,  # Previous state
            "de_win_count_last30": 27,  # In hysteresis zone (26 < 27 < 28)
            "is_enabled": 1
        }
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de()
        
        # Should be visible due to auto_enabled flag taking precedence
        assert len(result) == 1, f"Expected 1 bridge (hysteresis + prev enabled), got {len(result)}"
        print("✓ test_hysteresis_zone_with_prev_enabled passed")


def test_hysteresis_zone_with_prev_disabled():
    """
    Test hysteresis: wins_last30 = 27 (in zone), prev de_auto_enabled = 0
    Bridge should remain hidden.
    """
    mock_bridges = [
        {
            "id": 1,
            "name": "DE_DYN_Hysteresis_Disabled",
            "type": "DE_DYN",
            "de_manual_override": 0,
            "de_auto_enabled": 0,  # Previous state
            "de_win_count_last30": 27,  # In hysteresis zone
            "is_enabled": 1
        }
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de()
        
        assert len(result) == 0, f"Expected 0 bridges (hysteresis + prev disabled), got {len(result)}"
        print("✓ test_hysteresis_zone_with_prev_disabled passed")


def test_no_metrics_needs_evaluation():
    """
    Test missing metrics: no de_win_count_last30, no current_streak
    Bridge should be hidden and marked needs_evaluation.
    """
    mock_bridges = [
        {
            "id": 1,
            "name": "DE_DYN_No_Metrics",
            "type": "DE_DYN",
            "de_manual_override": 0,
            "de_auto_enabled": 0,
            "is_enabled": 1
            # No de_win_count_last30, no current_streak
        }
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de()
        
        assert len(result) == 0, f"Expected 0 bridges (no metrics), got {len(result)}"
        # Note: The bridge is filtered out, so we can't check needs_evaluation flag in result
        # But the function should log "needs evaluation"
        print("✓ test_no_metrics_needs_evaluation passed")


def test_filter_lo_bridges():
    """
    Test that LO_* bridges are completely filtered out.
    """
    mock_bridges = [
        {
            "id": 1,
            "name": "LO_V17_Shadow",
            "type": "LO_V17",
            "de_win_count_last30": 30,
            "de_auto_enabled": 1,
            "is_enabled": 1
        },
        {
            "id": 2,
            "name": "DE_DYN_Valid",
            "type": "DE_DYN",
            "de_win_count_last30": 28,
            "de_auto_enabled": 0,
            "is_enabled": 1
        }
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de()
        
        assert len(result) == 1, f"Expected 1 DE bridge (LO filtered), got {len(result)}"
        assert result[0]["name"] == "DE_DYN_Valid"
        assert result[0]["type"].upper() == "DE_DYN"
        print("✓ test_filter_lo_bridges passed")


def test_de_killer_always_filtered():
    """
    Test that DE_KILLER bridges are always filtered out.
    """
    mock_bridges = [
        {
            "id": 1,
            "name": "DE_KILLER_Test",
            "type": "DE_KILLER",
            "de_win_count_last30": 30,
            "de_auto_enabled": 1,
            "de_manual_override": 1,
            "de_manual_override_value": 1,
            "is_enabled": 1
        }
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de()
        
        assert len(result) == 0, f"Expected 0 bridges (DE_KILLER filtered), got {len(result)}"
        print("✓ test_de_killer_always_filtered passed")


def test_de_set_always_visible():
    """
    Test that DE_SET bridges are always visible (no special filtering).
    """
    mock_bridges = [
        {
            "id": 1,
            "name": "DE_SET_Bo11",
            "type": "DE_SET",
            "current_streak": 25,
            "is_enabled": 1
        }
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de()
        
        assert len(result) == 1, f"Expected 1 bridge (DE_SET visible), got {len(result)}"
        assert result[0]["name"] == "DE_SET_Bo11"
        print("✓ test_de_set_always_visible passed")


def test_mixed_scenario_comprehensive():
    """
    Test comprehensive scenario with multiple bridge types and states.
    """
    mock_bridges = [
        # Should be filtered
        {"id": 1, "name": "LO_Bridge", "type": "LO_V17", "is_enabled": 1},
        {"id": 2, "name": "DE_KILLER", "type": "DE_KILLER", "is_enabled": 1},
        {"id": 3, "name": "DE_DYN_Low", "type": "DE_DYN", "de_win_count_last30": 25, "de_auto_enabled": 0, "is_enabled": 1},
        {"id": 4, "name": "DE_DYN_Manual_Hide", "type": "DE_DYN", "de_manual_override": 1, "de_manual_override_value": 0, "is_enabled": 1},
        
        # Should be visible
        {"id": 5, "name": "DE_DYN_High", "type": "DE_DYN", "de_win_count_last30": 29, "de_auto_enabled": 0, "is_enabled": 1},
        {"id": 6, "name": "DE_DYN_Auto", "type": "DE_DYN", "de_win_count_last30": 20, "de_auto_enabled": 1, "is_enabled": 1},
        {"id": 7, "name": "DE_DYN_Manual_Show", "type": "DE_DYN", "de_manual_override": 1, "de_manual_override_value": 1, "de_win_count_last30": 10, "is_enabled": 1},
        {"id": 8, "name": "DE_SET", "type": "DE_SET", "current_streak": 20, "is_enabled": 1},
        {"id": 9, "name": "DE_MEMORY", "type": "DE_MEMORY", "current_streak": 15, "is_enabled": 1},
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de()
        
        # Should have 5 visible bridges
        assert len(result) == 5, f"Expected 5 visible bridges, got {len(result)}"
        
        visible_names = [b["name"] for b in result]
        assert "DE_DYN_High" in visible_names
        assert "DE_DYN_Auto" in visible_names
        assert "DE_DYN_Manual_Show" in visible_names
        assert "DE_SET" in visible_names
        assert "DE_MEMORY" in visible_names
        
        # Verify filtered out
        assert "LO_Bridge" not in visible_names
        assert "DE_KILLER" not in visible_names
        assert "DE_DYN_Low" not in visible_names
        assert "DE_DYN_Manual_Hide" not in visible_names
        
        print("✓ test_mixed_scenario_comprehensive passed")


if __name__ == "__main__":
    # Run tests manually
    test_manual_override_show()
    test_manual_override_hide()
    test_auto_enabled_flag()
    test_wins_above_enable_threshold()
    test_wins_below_disable_threshold()
    test_hysteresis_zone_with_prev_enabled()
    test_hysteresis_zone_with_prev_disabled()
    test_no_metrics_needs_evaluation()
    test_filter_lo_bridges()
    test_de_killer_always_filtered()
    test_de_set_always_visible()
    test_mixed_scenario_comprehensive()
    print("\n✅ All DE visibility policy tests passed!")
