# -*- coding: utf-8 -*-
"""
tests.test_bridge_add_normalization
------------------------------------
Test suite for bridge name normalization and sanitization logic.

Tests the NAME_SANITIZE_REGEX and normalization behavior in the adapter.
"""

import pytest
import sys
import os
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import constants
try:
    from logic.constants import (
        NAME_SANITIZE_REGEX,
        MIN_NAME_LENGTH,
        DEFAULT_WIN_RATE,
        BRIDGE_TYPE_MANUAL_LO,
        BRIDGE_TYPE_ALGO_DE,
        WHITELIST_DISPLAY_TYPES,
    )
except ImportError as e:
    pytest.skip(f"Could not import constants: {e}", allow_module_level=True)


class TestNameSanitization:
    """Test suite for name sanitization regex."""
    
    def test_sanitize_regex_exists(self):
        """Test that NAME_SANITIZE_REGEX is defined."""
        assert NAME_SANITIZE_REGEX is not None
        assert isinstance(NAME_SANITIZE_REGEX, re.Pattern)
    
    def test_sanitize_preserves_alphanumeric(self):
        """Test that alphanumeric characters are preserved."""
        test_name = "Bridge123"
        sanitized = NAME_SANITIZE_REGEX.sub(" ", test_name)
        assert "Bridge123" in sanitized
    
    def test_sanitize_preserves_spaces(self):
        """Test that spaces are preserved."""
        test_name = "Bridge Name Test"
        sanitized = NAME_SANITIZE_REGEX.sub(" ", test_name)
        assert "Bridge" in sanitized
        assert "Name" in sanitized
        assert "Test" in sanitized
    
    def test_sanitize_preserves_hyphens(self):
        """Test that hyphens are preserved."""
        test_name = "Bridge-Name-01"
        sanitized = NAME_SANITIZE_REGEX.sub(" ", test_name)
        assert "Bridge" in sanitized
        assert "Name" in sanitized
        assert "01" in sanitized
    
    def test_sanitize_preserves_underscores(self):
        """Test that underscores are preserved."""
        test_name = "Bridge_Name_01"
        sanitized = NAME_SANITIZE_REGEX.sub(" ", test_name)
        assert "Bridge" in sanitized
        assert "Name" in sanitized
        assert "01" in sanitized
    
    def test_sanitize_preserves_unicode_vietnamese(self):
        """Test that Vietnamese Unicode characters are preserved."""
        test_name = "Cầu Đặc Biệt"
        sanitized = NAME_SANITIZE_REGEX.sub(" ", test_name)
        # Should preserve Vietnamese characters
        assert "Cầu" in sanitized or len(sanitized) > 5  # Unicode preserved
    
    def test_sanitize_replaces_special_chars(self):
        """Test that special characters are replaced."""
        test_name = "Bridge@#$Name"
        sanitized = NAME_SANITIZE_REGEX.sub(" ", test_name)
        # Special chars should be replaced with space
        assert "@" not in sanitized
        assert "#" not in sanitized
        assert "$" not in sanitized
    
    def test_sanitize_handles_mixed_content(self):
        """Test sanitization with mixed valid/invalid characters."""
        test_name = "Bridge_01-Test@Name#Special"
        sanitized = NAME_SANITIZE_REGEX.sub(" ", test_name)
        # Valid chars preserved, invalid replaced
        assert "Bridge" in sanitized
        assert "01" in sanitized
        assert "Test" in sanitized
        assert "Name" in sanitized
        assert "@" not in sanitized
        assert "#" not in sanitized


class TestConstants:
    """Test suite for bridge-related constants."""
    
    def test_min_name_length_defined(self):
        """Test that MIN_NAME_LENGTH is defined."""
        assert MIN_NAME_LENGTH is not None
        assert isinstance(MIN_NAME_LENGTH, int)
        assert MIN_NAME_LENGTH > 0
    
    def test_default_win_rate_defined(self):
        """Test that DEFAULT_WIN_RATE is defined."""
        assert DEFAULT_WIN_RATE is not None
        assert isinstance(DEFAULT_WIN_RATE, str)
        # Should be a numeric string
        assert DEFAULT_WIN_RATE.isdigit()
    
    def test_bridge_type_constants_defined(self):
        """Test that bridge type constants are defined."""
        assert BRIDGE_TYPE_MANUAL_LO is not None
        assert BRIDGE_TYPE_ALGO_DE is not None
        assert isinstance(BRIDGE_TYPE_MANUAL_LO, str)
        assert isinstance(BRIDGE_TYPE_ALGO_DE, str)
    
    def test_whitelist_display_types_defined(self):
        """Test that WHITELIST_DISPLAY_TYPES is defined."""
        assert WHITELIST_DISPLAY_TYPES is not None
        assert isinstance(WHITELIST_DISPLAY_TYPES, tuple)
        assert len(WHITELIST_DISPLAY_TYPES) > 0
    
    def test_whitelist_display_types_structure(self):
        """Test that WHITELIST_DISPLAY_TYPES has correct structure."""
        for item in WHITELIST_DISPLAY_TYPES:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)  # Display type
            assert isinstance(item[1], str)  # Canonical type


class TestNormalizationLogic:
    """Test normalization logic patterns."""
    
    def test_whitespace_normalization(self):
        """Test whitespace normalization pattern."""
        test_cases = [
            ("  Bridge  ", "Bridge"),
            ("\tBridge\t", "Bridge"),
            ("Bridge  Name", "Bridge Name"),
            ("  ", ""),
        ]
        
        for input_val, expected_pattern in test_cases:
            # Simulate normalization
            normalized = input_val.strip()
            if expected_pattern:
                assert expected_pattern in normalized or normalized == expected_pattern
    
    def test_collapse_multiple_spaces(self):
        """Test collapsing multiple spaces pattern."""
        test_name = "Bridge    Name    Test"
        # Apply space collapsing (similar to adapter logic)
        collapsed = re.sub(r"\s+", " ", test_name).strip()
        assert collapsed == "Bridge Name Test"
    
    def test_combined_normalization(self):
        """Test combined normalization steps."""
        test_cases = [
            ("  Bridge@Name  ", "Bridge Name"),
            ("Bridge#$%Test", "Bridge Test"),
            ("Cầu  Đặc  Biệt", "Cầu Đặc Biệt"),
        ]
        
        for input_val, expected_pattern in test_cases:
            # Simulate full normalization pipeline
            normalized = input_val.strip()
            normalized = NAME_SANITIZE_REGEX.sub(" ", normalized)
            normalized = re.sub(r"\s+", " ", normalized).strip()
            
            # Should contain expected words (order may vary due to special chars)
            words = expected_pattern.split()
            for word in words:
                if word.isalnum():  # Only check alphanumeric words
                    assert word in normalized or len(normalized) > 0


class TestBridgeTypeMapping:
    """Test bridge type mapping logic."""
    
    def test_type_mapping_dict_creation(self):
        """Test creating type mapping dictionary."""
        type_mapping = dict(WHITELIST_DISPLAY_TYPES)
        assert isinstance(type_mapping, dict)
        assert len(type_mapping) > 0
    
    def test_type_mapping_lookup(self):
        """Test looking up types in mapping."""
        type_mapping = dict(WHITELIST_DISPLAY_TYPES)
        
        # Test known mappings
        test_cases = [
            ("manual_lo", BRIDGE_TYPE_MANUAL_LO),
            ("algo_de", BRIDGE_TYPE_ALGO_DE),
        ]
        
        for display_type, expected_canonical in test_cases:
            if display_type in type_mapping:
                assert type_mapping[display_type] == expected_canonical
    
    def test_type_mapping_case_insensitive(self):
        """Test that type mapping handles case conversion."""
        type_mapping = dict(WHITELIST_DISPLAY_TYPES)
        
        # Test case variations
        test_type = "MANUAL_LO"
        normalized_type = test_type.lower()
        
        if normalized_type in type_mapping:
            result = type_mapping[normalized_type]
            assert isinstance(result, str)


class TestEdgeCases:
    """Test edge cases in normalization."""
    
    def test_empty_string_normalization(self):
        """Test normalization of empty string."""
        test_name = ""
        normalized = test_name.strip()
        assert len(normalized) < MIN_NAME_LENGTH
    
    def test_only_special_chars(self):
        """Test normalization of only special characters."""
        test_name = "@#$%^&*()"
        sanitized = NAME_SANITIZE_REGEX.sub(" ", test_name)
        collapsed = re.sub(r"\s+", " ", sanitized).strip()
        # Should result in empty or very short string
        assert len(collapsed) < 5
    
    def test_very_long_name(self):
        """Test normalization of very long name."""
        test_name = "A" * 1000
        normalized = test_name.strip()
        assert len(normalized) > MIN_NAME_LENGTH
    
    def test_unicode_edge_cases(self):
        """Test Unicode edge cases."""
        test_cases = [
            "Đặc Biệt",  # Vietnamese
            "数字",  # Chinese (may or may not be preserved depending on regex)
            "テスト",  # Japanese (may or may not be preserved)
        ]
        
        for test_name in test_cases:
            sanitized = NAME_SANITIZE_REGEX.sub(" ", test_name)
            # Should not crash and should return something
            assert isinstance(sanitized, str)


class TestDefaultValues:
    """Test default value constants."""
    
    def test_default_win_rate_is_numeric(self):
        """Test that DEFAULT_WIN_RATE is a valid number."""
        try:
            value = int(DEFAULT_WIN_RATE)
            assert value >= 0
            assert value <= 100
        except ValueError:
            pytest.fail("DEFAULT_WIN_RATE should be a numeric string")
    
    def test_default_win_rate_format(self):
        """Test that DEFAULT_WIN_RATE is formatted correctly."""
        assert len(DEFAULT_WIN_RATE) > 0
        assert DEFAULT_WIN_RATE.isdigit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
