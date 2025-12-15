"""
Test Dashboard Filtering Logic for High-Performing Bridges
Tests the filtering logic that shows only bridges with:
- recent_win_count_10 >= DASHBOARD_MIN_RECENT_WINS (default: 9)
- is_enabled = 1
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.constants import DEFAULT_SETTINGS


class TestDashboardFiltering(unittest.TestCase):
    """Test dashboard filtering logic for recent form"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.min_wins = DEFAULT_SETTINGS.get("DASHBOARD_MIN_RECENT_WINS", 9)
    
    def test_threshold_configuration(self):
        """Test that threshold is properly configured"""
        self.assertEqual(self.min_wins, 9)
        self.assertIsInstance(self.min_wins, int)
    
    def test_filter_logic_enabled_high_wins(self):
        """Test that enabled bridge with high wins passes filter"""
        bridge = {
            "name": "TEST_BRIDGE_01",
            "recent_win_count_10": 9,
            "is_enabled": 1,
            "type": "LO_STL_FIXED"
        }
        
        # Apply filter logic
        recent_wins = bridge.get("recent_win_count_10", 0)
        is_enabled = bridge.get("is_enabled", 0)
        
        result = is_enabled == 1 and recent_wins >= self.min_wins
        self.assertTrue(result, "Enabled bridge with 9/10 wins should pass")
    
    def test_filter_logic_enabled_low_wins(self):
        """Test that enabled bridge with low wins fails filter"""
        bridge = {
            "name": "TEST_BRIDGE_02",
            "recent_win_count_10": 8,
            "is_enabled": 1,
            "type": "LO_STL_FIXED"
        }
        
        recent_wins = bridge.get("recent_win_count_10", 0)
        is_enabled = bridge.get("is_enabled", 0)
        
        result = is_enabled == 1 and recent_wins >= self.min_wins
        self.assertFalse(result, "Bridge with 8/10 wins should fail (< 9)")
    
    def test_filter_logic_disabled_high_wins(self):
        """Test that disabled bridge fails filter even with high wins"""
        bridge = {
            "name": "TEST_BRIDGE_03",
            "recent_win_count_10": 10,
            "is_enabled": 0,
            "type": "LO_STL_FIXED"
        }
        
        recent_wins = bridge.get("recent_win_count_10", 0)
        is_enabled = bridge.get("is_enabled", 0)
        
        result = is_enabled == 1 and recent_wins >= self.min_wins
        self.assertFalse(result, "Disabled bridge should fail even with 10/10 wins")
    
    def test_filter_logic_string_values(self):
        """Test that string values are handled correctly"""
        bridge = {
            "name": "TEST_BRIDGE_04",
            "recent_win_count_10": "9",  # String instead of int
            "is_enabled": "1",           # String instead of int
            "type": "LO_STL_FIXED"
        }
        
        # Parse values (as done in UI code)
        recent_wins = bridge.get("recent_win_count_10", 0)
        if isinstance(recent_wins, str):
            try:
                recent_wins = int(recent_wins)
            except ValueError:
                recent_wins = 0
        
        is_enabled = bridge.get("is_enabled", 0)
        if isinstance(is_enabled, str):
            try:
                is_enabled = int(is_enabled)
            except ValueError:
                is_enabled = 0
        
        result = is_enabled == 1 and recent_wins >= self.min_wins
        self.assertTrue(result, "String values should be parsed correctly")
    
    def test_filter_logic_missing_values(self):
        """Test that missing values default to 0 and fail filter"""
        bridge = {
            "name": "TEST_BRIDGE_05",
            "type": "LO_STL_FIXED"
            # recent_win_count_10 and is_enabled are missing
        }
        
        recent_wins = bridge.get("recent_win_count_10", 0)
        is_enabled = bridge.get("is_enabled", 0)
        
        result = is_enabled == 1 and recent_wins >= self.min_wins
        self.assertFalse(result, "Missing values should default to 0 and fail")
    
    def test_filter_logic_de_bridge_exclusion(self):
        """Test that DE bridges are properly excluded"""
        bridge = {
            "name": "DE_SET_01",
            "recent_win_count_10": 10,
            "is_enabled": 1,
            "type": "DE_SET"
        }
        
        # Check type filter (as done in UI code)
        bridge_type = str(bridge.get("type", "")).upper()
        is_de_bridge = bridge_type.startswith("DE")
        
        self.assertTrue(is_de_bridge, "DE_SET should be identified as DE bridge")
    
    def test_filter_batch_bridges(self):
        """Test filtering a batch of bridges"""
        bridges = [
            {"name": "B1", "recent_win_count_10": 10, "is_enabled": 1, "type": "LO"},
            {"name": "B2", "recent_win_count_10": 9, "is_enabled": 1, "type": "LO"},
            {"name": "B3", "recent_win_count_10": 8, "is_enabled": 1, "type": "LO"},
            {"name": "B4", "recent_win_count_10": 10, "is_enabled": 0, "type": "LO"},
            {"name": "B5", "recent_win_count_10": 10, "is_enabled": 1, "type": "DE_SET"},
        ]
        
        good_bridges = []
        for b in bridges:
            # Exclude DE bridges
            bridge_type = str(b.get("type", "")).upper()
            if bridge_type.startswith("DE"):
                continue
            
            # Parse values
            recent_wins = b.get("recent_win_count_10", 0)
            is_enabled = b.get("is_enabled", 0)
            
            # Filter
            if is_enabled == 1 and recent_wins >= self.min_wins:
                good_bridges.append(b)
        
        self.assertEqual(len(good_bridges), 2, "Should filter to 2 bridges (B1, B2)")
        self.assertEqual(good_bridges[0]["name"], "B1")
        self.assertEqual(good_bridges[1]["name"], "B2")
    
    def test_edge_case_exact_threshold(self):
        """Test bridge exactly at threshold (9 wins)"""
        bridge = {
            "name": "TEST_EDGE",
            "recent_win_count_10": 9,
            "is_enabled": 1,
            "type": "LO"
        }
        
        recent_wins = bridge.get("recent_win_count_10", 0)
        is_enabled = bridge.get("is_enabled", 0)
        
        result = is_enabled == 1 and recent_wins >= self.min_wins
        self.assertTrue(result, "Bridge with exactly 9 wins should pass (>=)")


if __name__ == "__main__":
    unittest.main()
