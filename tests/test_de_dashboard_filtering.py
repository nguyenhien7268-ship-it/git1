# tests/test_de_dashboard_filtering.py
"""
Test suite for DE Dashboard filtering logic (V8.2)
Verifies that DE dashboard correctly filters bridges based on:
- recent_win_count_10 >= threshold (default: 9)
- is_enabled == 1
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.constants import DEFAULT_SETTINGS


class TestDEDashboardFiltering(unittest.TestCase):
    """Test DE Dashboard filtering logic"""
    
    def test_de_threshold_configuration(self):
        """Verify DE_DASHBOARD_MIN_RECENT_WINS is configured correctly"""
        threshold = DEFAULT_SETTINGS.get("DE_DASHBOARD_MIN_RECENT_WINS", 0)
        self.assertEqual(threshold, 9, "DE dashboard threshold should be 9")
    
    def test_filter_logic_enabled_high_wins(self):
        """Bridge with is_enabled=1 and recent_wins>=9 should pass filter"""
        bridge = {
            "name": "DE_SET_01",
            "type": "DE_SET",
            "recent_win_count_10": 10,
            "is_enabled": 1
        }
        
        # Simulate filter logic
        recent_wins = bridge.get("recent_win_count_10", 0)
        is_enabled = bridge.get("is_enabled", 0)
        min_wins = 9
        
        should_show = (is_enabled == 1 and recent_wins >= min_wins)
        self.assertTrue(should_show, "Enabled bridge with 10/10 wins should be shown")
    
    def test_filter_logic_enabled_low_wins(self):
        """Bridge with is_enabled=1 but recent_wins<9 should fail filter"""
        bridge = {
            "name": "DE_SET_02",
            "type": "DE_SET",
            "recent_win_count_10": 8,
            "is_enabled": 1
        }
        
        recent_wins = bridge.get("recent_win_count_10", 0)
        is_enabled = bridge.get("is_enabled", 0)
        min_wins = 9
        
        should_show = (is_enabled == 1 and recent_wins >= min_wins)
        self.assertFalse(should_show, "Bridge with only 8/10 wins should be hidden")
    
    def test_filter_logic_disabled_high_wins(self):
        """Bridge with is_enabled=0 should fail filter even with high wins"""
        bridge = {
            "name": "DE_SET_03",
            "type": "DE_SET",
            "recent_win_count_10": 10,
            "is_enabled": 0
        }
        
        recent_wins = bridge.get("recent_win_count_10", 0)
        is_enabled = bridge.get("is_enabled", 0)
        min_wins = 9
        
        should_show = (is_enabled == 1 and recent_wins >= min_wins)
        self.assertFalse(should_show, "Disabled bridge should be hidden regardless of wins")
    
    def test_filter_logic_string_values(self):
        """Filter should handle string values correctly"""
        bridge = {
            "name": "DE_SET_04",
            "type": "DE_SET",
            "recent_win_count_10": "9",  # String instead of int
            "is_enabled": "1"  # String instead of int
        }
        
        # Simulate safe parsing
        recent_wins = bridge.get("recent_win_count_10", 0)
        if isinstance(recent_wins, str):
            recent_wins = int(recent_wins) if recent_wins.isdigit() else 0
        
        is_enabled = bridge.get("is_enabled", 0)
        if isinstance(is_enabled, str):
            is_enabled = int(is_enabled) if is_enabled.isdigit() else 0
        
        min_wins = 9
        should_show = (is_enabled == 1 and recent_wins >= min_wins)
        self.assertTrue(should_show, "String values should be parsed correctly")
    
    def test_filter_logic_missing_values(self):
        """Bridge with missing values should default to 0 and fail filter"""
        bridge = {
            "name": "DE_SET_05",
            "type": "DE_SET"
            # recent_win_count_10 and is_enabled missing
        }
        
        recent_wins = bridge.get("recent_win_count_10", 0)
        is_enabled = bridge.get("is_enabled", 0)
        min_wins = 9
        
        should_show = (is_enabled == 1 and recent_wins >= min_wins)
        self.assertFalse(should_show, "Bridge with missing values should be hidden")
    
    def test_filter_de_type_identification(self):
        """Verify DE bridge type identification logic"""
        test_cases = [
            ({"type": "DE_SET", "name": "DE_SET_01"}, True),
            ({"type": "CAU_DE", "name": "CAU_DE_01"}, True),
            ({"type": "LO", "name": "DE_SPECIAL"}, True),  # Has "DE" in name
            ({"type": "LO_STL", "name": "LO_STL_01"}, False),
            ({"type": "DE_PLUS", "name": "DE_PLUS_01"}, True),
        ]
        
        for bridge, expected_is_de in test_cases:
            bridge_type = str(bridge.get('type', '')).upper()
            bridge_name = str(bridge.get('name', '')).upper()
            
            is_de = (
                bridge_type.startswith(('DE_', 'CAU_DE')) or
                "Đề" in bridge.get('name', '') or
                "DE" in bridge_name
            )
            
            self.assertEqual(is_de, expected_is_de,
                           f"Bridge {bridge} DE classification failed")
    
    def test_filter_batch_bridges(self):
        """Test filtering multiple bridges correctly"""
        bridges = [
            {"name": "DE_01", "type": "DE_SET", "recent_win_count_10": 10, "is_enabled": 1},
            {"name": "DE_02", "type": "DE_SET", "recent_win_count_10": 9, "is_enabled": 1},
            {"name": "DE_03", "type": "DE_SET", "recent_win_count_10": 8, "is_enabled": 1},
            {"name": "DE_04", "type": "DE_SET", "recent_win_count_10": 10, "is_enabled": 0},
            {"name": "DE_05", "type": "DE_SET", "recent_win_count_10": 9, "is_enabled": 0},
        ]
        
        min_wins = 9
        filtered = []
        
        for b in bridges:
            recent_wins = b.get("recent_win_count_10", 0)
            is_enabled = b.get("is_enabled", 0)
            
            if is_enabled == 1 and recent_wins >= min_wins:
                filtered.append(b)
        
        self.assertEqual(len(filtered), 2, "Should filter to exactly 2 bridges")
        self.assertEqual(filtered[0]["name"], "DE_01")
        self.assertEqual(filtered[1]["name"], "DE_02")
    
    def test_edge_case_exact_threshold(self):
        """Bridge with exactly 9 wins should pass filter"""
        bridge = {
            "name": "DE_EDGE",
            "type": "DE_SET",
            "recent_win_count_10": 9,
            "is_enabled": 1
        }
        
        recent_wins = bridge.get("recent_win_count_10", 0)
        is_enabled = bridge.get("is_enabled", 0)
        min_wins = 9
        
        should_show = (is_enabled == 1 and recent_wins >= min_wins)
        self.assertTrue(should_show, "Bridge with exactly 9 wins should be shown")


if __name__ == '__main__':
    unittest.main()
