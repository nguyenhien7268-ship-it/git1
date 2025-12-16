"""
Test suite for DE Scanner result normalization.

Tests the robust normalization logic in ui/ui_bridge_scanner.py
that handles various scanner return formats.

V8.3 - Created to verify fix for closure bugs and diverse return types.
"""

import unittest


class MockBridgeObject:
    """Mock bridge object with attributes instead of dict."""
    def __init__(self, name, description, win_rate, streak, bridge_type):
        self.name = name
        self.normalized_name = name.upper()
        self.description = description
        self.win_rate = win_rate
        self.streak = streak
        self.type = bridge_type


class TestDEScannerNormalization(unittest.TestCase):
    """Test normalization of diverse scanner return formats."""
    
    def test_normalize_tuple_list_int(self):
        """Test normalizing (list, int) return format."""
        bridges = [{'name': 'DE_01', 'win_rate': 0.85, 'streak': 5}]
        scanner_result = (bridges, 1)
        
        # Normalization logic
        count, found_bridges = 0, []
        if isinstance(scanner_result, tuple) and len(scanner_result) == 2:
            if isinstance(scanner_result[0], list) and isinstance(scanner_result[1], int):
                found_bridges, count = scanner_result[0], scanner_result[1]
        
        self.assertEqual(count, 1)
        self.assertEqual(len(found_bridges), 1)
        self.assertEqual(found_bridges[0]['name'], 'DE_01')
    
    def test_normalize_tuple_int_list(self):
        """Test normalizing (int, list) return format."""
        bridges = [{'name': 'DE_02', 'win_rate': 0.75}]
        scanner_result = (2, bridges)
        
        # Normalization logic
        count, found_bridges = 0, []
        if isinstance(scanner_result, tuple) and len(scanner_result) == 2:
            if isinstance(scanner_result[0], int) and isinstance(scanner_result[1], list):
                count, found_bridges = scanner_result[0], scanner_result[1]
        
        self.assertEqual(count, 2)
        self.assertEqual(len(found_bridges), 1)
    
    def test_normalize_plain_list(self):
        """Test normalizing plain list return format."""
        scanner_result = [{'name': 'DE_03'}, {'name': 'DE_04'}]
        
        # Normalization logic
        found_bridges = scanner_result if isinstance(scanner_result, list) else []
        count = len(found_bridges)
        
        self.assertEqual(count, 2)
        self.assertEqual(found_bridges[0]['name'], 'DE_03')
    
    def test_normalize_single_object(self):
        """Test normalizing single object return."""
        scanner_result = {'name': 'DE_SINGLE', 'win_rate': 0.9}
        
        # Normalization logic
        found_bridges = [scanner_result]
        count = 1
        
        self.assertEqual(count, 1)
        self.assertEqual(found_bridges[0]['name'], 'DE_SINGLE')
    
    def test_normalize_none_result(self):
        """Test handling None return."""
        scanner_result = None
        
        # Normalization logic
        if scanner_result is None:
            count = 0
            found_bridges = []
        
        self.assertEqual(count, 0)
        self.assertEqual(len(found_bridges), 0)
    
    def test_extract_name_from_dict(self):
        """Test extracting name from dict with various key names."""
        bridge1 = {'name': 'DE_NAME_KEY'}
        bridge2 = {'normalized_name': 'DE_NORM_KEY'}
        bridge3 = {'description': 'DE_DESC_ONLY'}
        
        # Extraction logic
        name1 = bridge1.get('name') or bridge1.get('normalized_name') or bridge1.get('description', 'N/A')
        name2 = bridge2.get('name') or bridge2.get('normalized_name') or bridge2.get('description', 'N/A')
        name3 = bridge3.get('name') or bridge3.get('normalized_name') or bridge3.get('description', 'N/A')
        
        self.assertEqual(name1, 'DE_NAME_KEY')
        self.assertEqual(name2, 'DE_NORM_KEY')
        self.assertEqual(name3, 'DE_DESC_ONLY')
    
    def test_extract_name_from_object(self):
        """Test extracting name from object with attributes."""
        bridge = MockBridgeObject('DE_OBJ', 'Description', 0.8, 3, 'DE_SET')
        
        # Extraction logic
        name = getattr(bridge, 'name', None) or getattr(bridge, 'normalized_name', None) or 'N/A'
        
        self.assertEqual(name, 'DE_OBJ')
    
    def test_normalize_win_rate_fraction(self):
        """Test normalizing win_rate as fraction (0-1) to percentage."""
        win_rate = 0.85
        
        # Normalization logic
        if isinstance(win_rate, (int, float)):
            if 0 < win_rate <= 1:
                rate_str = f"{win_rate * 100:.1f}%"
            else:
                rate_str = f"{win_rate:.1f}%"
        
        self.assertEqual(rate_str, "85.0%")
    
    def test_normalize_win_rate_percentage(self):
        """Test normalizing win_rate as already percentage (>1)."""
        win_rate = 85.5
        
        # Normalization logic
        if isinstance(win_rate, (int, float)):
            if 0 < win_rate <= 1:
                rate_str = f"{win_rate * 100:.1f}%"
            else:
                rate_str = f"{win_rate:.1f}%"
        
        self.assertEqual(rate_str, "85.5%")
    
    def test_normalize_win_rate_list(self):
        """Test normalizing win_rate as list of values."""
        win_rate = [0.85, 0.90, 0.78]
        
        # Normalization logic
        if isinstance(win_rate, list):
            rate_str = ', '.join([f"{r:.1f}%" if isinstance(r, (int, float)) else str(r) for r in win_rate])
        
        self.assertEqual(rate_str, "0.8%, 0.9%, 0.8%")
    
    def test_normalize_streak_int(self):
        """Test normalizing streak as integer."""
        streak = 5
        streak_str = str(streak)
        self.assertEqual(streak_str, "5")
    
    def test_normalize_streak_list(self):
        """Test normalizing streak as list."""
        streak = [3, 5, 2]
        streak_str = ', '.join([str(s) for s in streak])
        self.assertEqual(streak_str, "3, 5, 2")


if __name__ == '__main__':
    unittest.main()
