# tests/test_dashboard_cau_dong.py
# PR1: Unit tests for get_cau_dong_for_tab_soi_cau_de filtering logic

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import patch, MagicMock
from logic.dashboard_analytics import get_cau_dong_for_tab_soi_cau_de


def test_filter_de_killer():
    """
    Test that DE_KILLER bridges are completely filtered out.
    Mock get_all_managed_bridges to return a list containing DE_KILLER and DE_DYN.
    Ensure function removes DE_KILLER.
    """
    # Mock data with DE_KILLER and other types
    # Using current_streak field as it's in the DB schema
    mock_bridges = [
        {
            "id": 1,
            "name": "DE_KILLER_G1_G2_K5",
            "type": "DE_KILLER",
            "win_rate": 95.0,
            "current_streak": 28,
            "predicted_value": "CHẠM 5",
            "is_enabled": 1
        },
        {
            "id": 2,
            "name": "DE_DYN_GDB_G1_K3",
            "type": "DE_DYN",
            "win_rate": 93.3,
            "current_streak": 28,
            "predicted_value": "CHẠM 7",
            "is_enabled": 1
        },
        {
            "id": 3,
            "name": "DE_SET_Bo11",
            "type": "DE_SET",
            "win_rate": 85.0,
            "current_streak": 25,
            "predicted_value": "BỘ 11",
            "is_enabled": 1
        }
    ]
    
    # Patch get_all_managed_bridges to return our mock data
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de(threshold_thong=28)
        
        # Assert DE_KILLER is filtered out
        assert len(result) == 2, f"Expected 2 bridges after filtering, got {len(result)}"
        
        # Check that no DE_KILLER bridges remain
        for bridge in result:
            assert bridge["type"] != "DE_KILLER", "DE_KILLER bridge should be filtered out"
        
        # Verify the remaining bridges
        bridge_names = [b["name"] for b in result]
        assert "DE_DYN_GDB_G1_K3" in bridge_names
        assert "DE_SET_Bo11" in bridge_names
        assert "DE_KILLER_G1_G2_K5" not in bridge_names
        
        print("✓ test_filter_de_killer passed")


def test_filter_de_dyn_threshold():
    """
    Test that DE_DYN bridges are filtered by win_rate threshold.
    Mock return DE_DYN with win_rate 27 and 28.
    Ensure only 28 is included when threshold=28.
    """
    # Mock data with DE_DYN bridges at different win rates
    # Using current_streak field (raw count: 27, 28, 29 out of 30)
    mock_bridges = [
        {
            "id": 1,
            "name": "DE_DYN_Low_WinRate",
            "type": "DE_DYN",
            "win_rate": 90.0,  # 27/30 = 90% (below threshold)
            "current_streak": 27,
            "predicted_value": "CHẠM 3",
            "is_enabled": 1
        },
        {
            "id": 2,
            "name": "DE_DYN_High_WinRate",
            "type": "DE_DYN",
            "win_rate": 93.3,  # 28/30 = 93.3% (meets threshold)
            "current_streak": 28,
            "predicted_value": "CHẠM 7",
            "is_enabled": 1
        },
        {
            "id": 3,
            "name": "DE_DYN_Very_High_WinRate",
            "type": "DE_DYN",
            "win_rate": 96.7,  # 29/30 = 96.7% (above threshold)
            "current_streak": 29,
            "predicted_value": "CHẠM 9",
            "is_enabled": 1
        },
        {
            "id": 4,
            "name": "DE_SET_Always_Keep",
            "type": "DE_SET",
            "win_rate": 80.0,  # Should be kept regardless of threshold
            "current_streak": 24,
            "predicted_value": "BỘ 22",
            "is_enabled": 1
        }
    ]
    
    # Patch get_all_managed_bridges to return our mock data
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        # Test with threshold = 28 (93.3%)
        result = get_cau_dong_for_tab_soi_cau_de(threshold_thong=28)
        
        # Should keep: DE_DYN with streak>=28 (2 bridges) + DE_SET (1 bridge) = 3 total
        assert len(result) == 3, f"Expected 3 bridges after filtering, got {len(result)}"
        
        # Check that low win rate DE_DYN is filtered out
        bridge_names = [b["name"] for b in result]
        assert "DE_DYN_Low_WinRate" not in bridge_names, "Low win rate DE_DYN should be filtered"
        assert "DE_DYN_High_WinRate" in bridge_names, "High win rate DE_DYN should be kept"
        assert "DE_DYN_Very_High_WinRate" in bridge_names, "Very high win rate DE_DYN should be kept"
        assert "DE_SET_Always_Keep" in bridge_names, "DE_SET should be kept regardless"
        
        # Verify that all remaining DE_DYN bridges meet threshold
        # threshold_thong=28 means 28 out of 30 periods (raw count format)
        # The function normalizes both threshold and streak values to raw counts
        # So we expect all remaining DE_DYN bridges to have streak >= 28
        for bridge in result:
            if bridge["type"] == "DE_DYN":
                # Check the streak value (should be >= 28)
                # Note: Function maps current_streak -> streak, so check both
                streak_value = bridge.get("streak", 0) or bridge.get("current_streak", 0)
                # Mock data sets "current_streak" field, function maps it to "streak"
                assert streak_value >= 28, f"DE_DYN bridge {bridge['name']} has streak={streak_value} < 28"
        
        print("✓ test_filter_de_dyn_threshold passed")


def test_filter_mixed_scenarios():
    """
    Test with mixed scenarios: DE_KILLER + low DE_DYN + high DE_DYN + other types
    """
    mock_bridges = [
        {"id": 1, "name": "DE_KILLER_1", "type": "DE_KILLER", "win_rate": 100, "current_streak": 30, "is_enabled": 1},
        {"id": 2, "name": "DE_DYN_Low", "type": "DE_DYN", "win_rate": 86.7, "current_streak": 26, "is_enabled": 1},
        {"id": 3, "name": "DE_DYN_High", "type": "DE_DYN", "win_rate": 93.3, "current_streak": 28, "is_enabled": 1},
        {"id": 4, "name": "DE_SET_1", "type": "DE_SET", "win_rate": 75, "current_streak": 22, "is_enabled": 1},
        {"id": 5, "name": "DE_MEMORY_1", "type": "DE_MEMORY", "win_rate": 65, "current_streak": 19, "is_enabled": 1},
        {"id": 6, "name": "DE_PASCAL_1", "type": "DE_PASCAL", "win_rate": 70, "current_streak": 21, "is_enabled": 1},
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de(threshold_thong=28)
        
        # Should filter out: DE_KILLER_1, DE_DYN_Low
        # Should keep: DE_DYN_High, DE_SET_1, DE_MEMORY_1, DE_PASCAL_1 = 4 bridges
        assert len(result) == 4, f"Expected 4 bridges, got {len(result)}"
        
        bridge_names = [b["name"] for b in result]
        assert "DE_KILLER_1" not in bridge_names
        assert "DE_DYN_Low" not in bridge_names
        assert "DE_DYN_High" in bridge_names
        assert "DE_SET_1" in bridge_names
        assert "DE_MEMORY_1" in bridge_names
        assert "DE_PASCAL_1" in bridge_names
        
        print("✓ test_filter_mixed_scenarios passed")


def test_filter_non_de_bridges():
    """
    Test that non-DE bridges (LO_*, etc.) are filtered out.
    Only DE_* bridges should be included in the Soi Cầu Đề tab.
    """
    mock_bridges = [
        {"id": 1, "name": "LO_V17_Shadow_1", "type": "LO_V17", "win_rate": 95, "current_streak": 30, "is_enabled": 1},
        {"id": 2, "name": "LO_BAC_NHO_1", "type": "LO_BAC_NHO", "win_rate": 90, "current_streak": 28, "is_enabled": 1},
        {"id": 3, "name": "DE_DYN_1", "type": "DE_DYN", "win_rate": 93.3, "current_streak": 28, "is_enabled": 1},
        {"id": 4, "name": "DE_SET_1", "type": "DE_SET", "win_rate": 85, "current_streak": 25, "is_enabled": 1},
        {"id": 5, "name": "UNKNOWN_TYPE", "type": "UNKNOWN", "win_rate": 80, "current_streak": 20, "is_enabled": 1},
    ]
    
    with patch('logic.dashboard_analytics.get_all_managed_bridges', return_value=mock_bridges):
        result = get_cau_dong_for_tab_soi_cau_de(threshold_thong=28)
        
        # Should filter out: LO_V17, LO_BAC_NHO, UNKNOWN
        # Should keep: DE_DYN_1, DE_SET_1 = 2 bridges
        assert len(result) == 2, f"Expected 2 DE bridges, got {len(result)}"
        
        # Check that all remaining bridges are DE_* type
        for bridge in result:
            bridge_type = (bridge.get("type", "") or "").upper()
            assert bridge_type.startswith("DE_"), f"Non-DE bridge found: {bridge['name']} ({bridge_type})"
        
        # Verify specific bridges
        bridge_names = [b["name"] for b in result]
        assert "DE_DYN_1" in bridge_names
        assert "DE_SET_1" in bridge_names
        assert "LO_V17_Shadow_1" not in bridge_names
        assert "LO_BAC_NHO_1" not in bridge_names
        assert "UNKNOWN_TYPE" not in bridge_names
        
        print("✓ test_filter_non_de_bridges passed")


if __name__ == "__main__":
    # Run tests manually
    test_filter_de_killer()
    test_filter_de_dyn_threshold()
    test_filter_mixed_scenarios()
    test_filter_non_de_bridges()
    print("\n✅ All tests passed!")
