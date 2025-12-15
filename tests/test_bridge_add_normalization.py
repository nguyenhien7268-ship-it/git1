"""
Unit tests for bridge normalization and validation in ui_bridge_scanner.py

Tests the _normalize_bridge_info method with various input formats.
Pure Python tests - no database required.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest


class MockBridgeScannerTab:
    """
    Mock version of BridgeScannerTab for testing normalization logic.
    
    We only need the _normalize_bridge_info method for these tests.
    """
    
    def _normalize_bridge_info(self, bridge):
        """
        Normalize bridge information from various input formats.
        
        This is a copy of the method from ui.ui_bridge_scanner.BridgeScannerTab
        for pure Python testing without UI dependencies.
        """
        normalized = {
            "name": None,
            "type": None,
            "description": None,
            "rate": None,
            "streak": None
        }
        
        # Extract name - priority order: normalized_name, name, first element
        if isinstance(bridge, dict):
            # Dict format
            normalized["name"] = (
                bridge.get("normalized_name") or 
                bridge.get("name") or 
                bridge.get("bridge_name")
            )
            normalized["type"] = bridge.get("type") or bridge.get("bridge_type")
            normalized["description"] = bridge.get("description") or bridge.get("desc")
            normalized["rate"] = bridge.get("rate") or bridge.get("win_rate")
            normalized["streak"] = bridge.get("streak") or bridge.get("current_streak")
            
        elif hasattr(bridge, '__dict__'):
            # Object format - has attributes
            normalized["name"] = (
                getattr(bridge, "normalized_name", None) or
                getattr(bridge, "name", None) or
                getattr(bridge, "bridge_name", None) or
                str(bridge)
            )
            normalized["type"] = (
                getattr(bridge, "type", None) or
                getattr(bridge, "bridge_type", None)
            )
            normalized["description"] = (
                getattr(bridge, "description", None) or
                getattr(bridge, "desc", None)
            )
            normalized["rate"] = (
                getattr(bridge, "rate", None) or
                getattr(bridge, "win_rate", None)
            )
            normalized["streak"] = (
                getattr(bridge, "streak", None) or
                getattr(bridge, "current_streak", None)
            )
            
        elif isinstance(bridge, (list, tuple)) and len(bridge) > 0:
            # List/tuple format - extract by index
            normalized["name"] = str(bridge[0]) if len(bridge) > 0 else None
            normalized["type"] = str(bridge[1]) if len(bridge) > 1 else None
            normalized["description"] = str(bridge[2]) if len(bridge) > 2 else None
            normalized["rate"] = bridge[3] if len(bridge) > 3 else None
            normalized["streak"] = bridge[4] if len(bridge) > 4 else None
            
        else:
            # Fallback - convert to string
            normalized["name"] = str(bridge) if bridge else None
        
        # Validate name
        if not normalized["name"]:
            return None
            
        normalized["name"] = str(normalized["name"]).strip()
        
        # Check for invalid name values
        if (not normalized["name"] or 
            normalized["name"] in ["", "N/A", "None", "null"] or
            normalized["name"].isspace()):
            return None
        
        # Validate and normalize type
        if normalized["type"]:
            normalized["type"] = str(normalized["type"]).strip()
            # Check against whitelist
            valid_types = ["LÔ_V17", "LÔ_BN", "LÔ_STL_FIXED", "ĐỀ", "MEMORY", "CLASSIC"]
            if normalized["type"] not in valid_types:
                # Allow but mark as unknown
                normalized["type"] = f"UNKNOWN_{normalized['type']}"
        else:
            normalized["type"] = "UNKNOWN"
        
        # Normalize description
        if not normalized["description"]:
            normalized["description"] = normalized["name"]
        else:
            normalized["description"] = str(normalized["description"]).strip()
        
        # Normalize rate
        if normalized["rate"] is not None:
            try:
                if isinstance(normalized["rate"], str):
                    # Remove % sign if present
                    rate_str = normalized["rate"].replace("%", "").strip()
                    normalized["rate"] = float(rate_str)
                else:
                    normalized["rate"] = float(normalized["rate"])
            except (ValueError, TypeError):
                normalized["rate"] = 0.0
        else:
            normalized["rate"] = 0.0
        
        # Normalize streak
        if normalized["streak"] is not None:
            try:
                normalized["streak"] = int(normalized["streak"])
            except (ValueError, TypeError):
                normalized["streak"] = 0
        else:
            normalized["streak"] = 0
            
        return normalized


class TestBridgeNormalization:
    """Test bridge normalization with various input formats."""
    
    def setup_method(self):
        """Setup test fixture."""
        self.scanner = MockBridgeScannerTab()
    
    def test_valid_dict_with_all_fields(self):
        """Test normalization of valid dict with all fields."""
        bridge = {
            "name": "Test Bridge",
            "type": "LÔ_V17",
            "description": "Test Description",
            "rate": 45.5,
            "streak": 3
        }
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["name"] == "Test Bridge"
        assert result["type"] == "LÔ_V17"
        assert result["description"] == "Test Description"
        assert result["rate"] == 45.5
        assert result["streak"] == 3
    
    def test_dict_with_normalized_name_priority(self):
        """Test that normalized_name takes priority over name."""
        bridge = {
            "normalized_name": "Normalized Name",
            "name": "Regular Name",
            "type": "LÔ_BN"
        }
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["name"] == "Normalized Name"
    
    def test_dict_with_alternate_field_names(self):
        """Test dict with alternate field names (bridge_name, win_rate, etc)."""
        bridge = {
            "bridge_name": "Alt Name Bridge",
            "bridge_type": "ĐỀ",
            "desc": "Alt description",
            "win_rate": 50.0,
            "current_streak": 5
        }
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["name"] == "Alt Name Bridge"
        assert result["type"] == "ĐỀ"
        assert result["description"] == "Alt description"
        assert result["rate"] == 50.0
        assert result["streak"] == 5
    
    def test_empty_name_returns_none(self):
        """Test that empty name returns None."""
        bridge = {"name": "", "type": "LÔ_V17"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is None
    
    def test_none_name_returns_none(self):
        """Test that None name returns None."""
        bridge = {"name": None, "type": "LÔ_V17"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is None
    
    def test_na_name_returns_none(self):
        """Test that 'N/A' name returns None."""
        bridge = {"name": "N/A", "type": "LÔ_V17"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is None
    
    def test_whitespace_only_name_returns_none(self):
        """Test that whitespace-only name returns None."""
        bridge = {"name": "   ", "type": "LÔ_V17"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is None
    
    def test_none_string_name_returns_none(self):
        """Test that string 'None' returns None."""
        bridge = {"name": "None", "type": "LÔ_V17"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is None
    
    def test_tuple_format(self):
        """Test normalization of tuple format."""
        bridge = ("Bridge Name", "LÔ_V17", "Description", 45.0, 3)
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["name"] == "Bridge Name"
        assert result["type"] == "LÔ_V17"
        assert result["description"] == "Description"
        assert result["rate"] == 45.0
        assert result["streak"] == 3
    
    def test_list_format(self):
        """Test normalization of list format."""
        bridge = ["Bridge Name", "ĐỀ", "Description", 50.0, 2]
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["name"] == "Bridge Name"
        assert result["type"] == "ĐỀ"
        assert result["rate"] == 50.0
    
    def test_tuple_with_fewer_elements(self):
        """Test tuple with only name and type."""
        bridge = ("Bridge Name", "LÔ_BN")
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["name"] == "Bridge Name"
        assert result["type"] == "LÔ_BN"
        assert result["description"] == "Bridge Name"  # Defaults to name
        assert result["rate"] == 0.0
        assert result["streak"] == 0
    
    def test_object_with_attributes(self):
        """Test normalization of object with attributes."""
        class MockBridge:
            def __init__(self):
                self.name = "Object Bridge"
                self.type = "LÔ_V17"
                self.description = "Object Description"
                self.rate = 40.0
                self.streak = 1
        
        bridge = MockBridge()
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["name"] == "Object Bridge"
        assert result["type"] == "LÔ_V17"
        assert result["description"] == "Object Description"
        assert result["rate"] == 40.0
        assert result["streak"] == 1
    
    def test_object_with_normalized_name(self):
        """Test object with normalized_name attribute."""
        class MockBridge:
            def __init__(self):
                self.normalized_name = "Normalized"
                self.name = "Regular"
                self.type = "ĐỀ"
        
        bridge = MockBridge()
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["name"] == "Normalized"
    
    def test_unknown_type_marked_as_unknown(self):
        """Test that unknown type is marked with UNKNOWN_ prefix."""
        bridge = {"name": "Test Bridge", "type": "INVALID_TYPE"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["type"] == "UNKNOWN_INVALID_TYPE"
    
    def test_missing_type_marked_as_unknown(self):
        """Test that missing type defaults to UNKNOWN."""
        bridge = {"name": "Test Bridge"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["type"] == "UNKNOWN"
    
    def test_valid_types_whitelist(self):
        """Test that all valid types pass through correctly."""
        valid_types = ["LÔ_V17", "LÔ_BN", "LÔ_STL_FIXED", "ĐỀ", "MEMORY", "CLASSIC"]
        
        for vtype in valid_types:
            bridge = {"name": f"Test {vtype}", "type": vtype}
            result = self.scanner._normalize_bridge_info(bridge)
            
            assert result is not None
            assert result["type"] == vtype
    
    def test_rate_string_with_percent(self):
        """Test rate as string with % sign."""
        bridge = {"name": "Test Bridge", "type": "LÔ_V17", "rate": "45.5%"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["rate"] == 45.5
    
    def test_rate_string_without_percent(self):
        """Test rate as string without % sign."""
        bridge = {"name": "Test Bridge", "type": "LÔ_V17", "rate": "45.5"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["rate"] == 45.5
    
    def test_rate_as_integer(self):
        """Test rate as integer."""
        bridge = {"name": "Test Bridge", "type": "LÔ_V17", "rate": 45}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["rate"] == 45.0
    
    def test_invalid_rate_defaults_to_zero(self):
        """Test invalid rate defaults to 0.0."""
        bridge = {"name": "Test Bridge", "type": "LÔ_V17", "rate": "invalid"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["rate"] == 0.0
    
    def test_streak_as_string(self):
        """Test streak as string converts to int."""
        bridge = {"name": "Test Bridge", "type": "LÔ_V17", "streak": "5"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["streak"] == 5
    
    def test_invalid_streak_defaults_to_zero(self):
        """Test invalid streak defaults to 0."""
        bridge = {"name": "Test Bridge", "type": "LÔ_V17", "streak": "invalid"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["streak"] == 0
    
    def test_description_defaults_to_name(self):
        """Test description defaults to name when not provided."""
        bridge = {"name": "Test Bridge", "type": "LÔ_V17"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["description"] == "Test Bridge"
    
    def test_name_whitespace_trimmed(self):
        """Test name whitespace is trimmed."""
        bridge = {"name": "  Test Bridge  ", "type": "LÔ_V17"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["name"] == "Test Bridge"
    
    def test_none_bridge_returns_none(self):
        """Test None bridge returns None."""
        result = self.scanner._normalize_bridge_info(None)
        
        assert result is None
    
    def test_empty_dict_returns_none(self):
        """Test empty dict returns None."""
        result = self.scanner._normalize_bridge_info({})
        
        assert result is None
    
    def test_empty_list_returns_none(self):
        """Test empty list returns None."""
        result = self.scanner._normalize_bridge_info([])
        
        assert result is None


class TestBridgeNormalizationEdgeCases:
    """Test edge cases in bridge normalization."""
    
    def setup_method(self):
        """Setup test fixture."""
        self.scanner = MockBridgeScannerTab()
    
    def test_very_long_name(self):
        """Test handling of very long bridge name."""
        long_name = "A" * 500
        bridge = {"name": long_name, "type": "LÔ_V17"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["name"] == long_name
    
    def test_special_characters_in_name(self):
        """Test special characters in name are preserved."""
        bridge = {"name": "Cầu + Đặc Biệt #123", "type": "LÔ_V17"}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["name"] == "Cầu + Đặc Biệt #123"
    
    def test_negative_rate(self):
        """Test negative rate is handled."""
        bridge = {"name": "Test Bridge", "type": "LÔ_V17", "rate": -10.0}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["rate"] == -10.0  # Should preserve negative value
    
    def test_very_high_rate(self):
        """Test very high rate (>100%) is handled."""
        bridge = {"name": "Test Bridge", "type": "LÔ_V17", "rate": 150.0}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["rate"] == 150.0
    
    def test_negative_streak(self):
        """Test negative streak is handled."""
        bridge = {"name": "Test Bridge", "type": "LÔ_V17", "streak": -5}
        
        result = self.scanner._normalize_bridge_info(bridge)
        
        assert result is not None
        assert result["streak"] == -5  # Should preserve negative value


if __name__ == "__main__":
    """Run tests if executed directly."""
    pytest.main([__file__, "-v"])
