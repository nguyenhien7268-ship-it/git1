"""
Test suite for scripts/migrate_config_v8.py
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.migrate_config_v8 import (
    migrate_to_dual_config,
    validate_config,
    DEFAULT_DE_CONFIG,
    DEFAULT_LO_CONFIG
)


def test_migrate_to_dual_config_with_old_settings():
    """Test migration from old config to dual-config structure"""
    old_config = {
        "STATS_DAYS": 7,
        "AUTO_PRUNE_MIN_RATE": 45.5,
        "AUTO_ADD_MIN_RATE": 46.0,
        "HIGH_WIN_THRESHOLD": 47.0,
    }
    
    new_config = migrate_to_dual_config(old_config)
    
    # Check lo_config was created with old values
    assert 'lo_config' in new_config
    assert new_config['lo_config']['remove_threshold'] == 45.5
    assert new_config['lo_config']['add_threshold'] == 46.0
    
    # Check de_config was created with defaults
    assert 'de_config' in new_config
    assert new_config['de_config']['remove_threshold'] == DEFAULT_DE_CONFIG['remove_threshold']
    assert new_config['de_config']['add_threshold'] == DEFAULT_DE_CONFIG['add_threshold']
    
    # Check old keys were removed
    assert 'AUTO_PRUNE_MIN_RATE' not in new_config
    assert 'AUTO_ADD_MIN_RATE' not in new_config
    
    # Check other settings preserved
    assert new_config['STATS_DAYS'] == 7
    assert new_config['HIGH_WIN_THRESHOLD'] == 47.0


def test_migrate_to_dual_config_without_old_settings():
    """Test migration when old settings are missing (use defaults)"""
    old_config = {
        "STATS_DAYS": 7,
        "HIGH_WIN_THRESHOLD": 47.0,
    }
    
    new_config = migrate_to_dual_config(old_config)
    
    # Check lo_config was created with defaults
    assert 'lo_config' in new_config
    assert new_config['lo_config']['remove_threshold'] == DEFAULT_LO_CONFIG['remove_threshold']
    assert new_config['lo_config']['add_threshold'] == DEFAULT_LO_CONFIG['add_threshold']
    
    # Check de_config was created with defaults
    assert 'de_config' in new_config
    assert new_config['de_config']['remove_threshold'] == DEFAULT_DE_CONFIG['remove_threshold']
    assert new_config['de_config']['add_threshold'] == DEFAULT_DE_CONFIG['add_threshold']


def test_migrate_to_dual_config_already_migrated():
    """Test that already migrated config is not modified"""
    already_migrated = {
        "STATS_DAYS": 7,
        "lo_config": {
            "remove_threshold": 50.0,
            "add_threshold": 55.0,
        },
        "de_config": {
            "remove_threshold": 85.0,
            "add_threshold": 90.0,
        }
    }
    
    new_config = migrate_to_dual_config(already_migrated)
    
    # Should return unchanged
    assert new_config['lo_config']['remove_threshold'] == 50.0
    assert new_config['lo_config']['add_threshold'] == 55.0
    assert new_config['de_config']['remove_threshold'] == 85.0
    assert new_config['de_config']['add_threshold'] == 90.0


def test_validate_config_valid():
    """Test validation of valid config"""
    valid_config = {
        "lo_config": {
            "remove_threshold": 43.0,
            "add_threshold": 45.0,
        },
        "de_config": {
            "remove_threshold": 80.0,
            "add_threshold": 88.0,
        }
    }
    
    is_valid, errors = validate_config(valid_config)
    
    assert is_valid is True
    assert len(errors) == 0


def test_validate_config_missing_lo_config():
    """Test validation fails when lo_config is missing"""
    invalid_config = {
        "de_config": {
            "remove_threshold": 80.0,
            "add_threshold": 88.0,
        }
    }
    
    is_valid, errors = validate_config(invalid_config)
    
    assert is_valid is False
    assert any("Missing 'lo_config'" in error for error in errors)


def test_validate_config_missing_de_config():
    """Test validation fails when de_config is missing"""
    invalid_config = {
        "lo_config": {
            "remove_threshold": 43.0,
            "add_threshold": 45.0,
        }
    }
    
    is_valid, errors = validate_config(invalid_config)
    
    assert is_valid is False
    assert any("Missing 'de_config'" in error for error in errors)


def test_validate_config_missing_thresholds():
    """Test validation fails when thresholds are missing"""
    invalid_config = {
        "lo_config": {
            "remove_threshold": 43.0,
            # Missing add_threshold
        },
        "de_config": {
            # Missing remove_threshold
            "add_threshold": 88.0,
        }
    }
    
    is_valid, errors = validate_config(invalid_config)
    
    assert is_valid is False
    assert len(errors) >= 2


def test_validate_config_invalid_threshold_order():
    """Test validation fails when remove_threshold > add_threshold"""
    invalid_config = {
        "lo_config": {
            "remove_threshold": 50.0,  # Higher than add_threshold
            "add_threshold": 45.0,
        },
        "de_config": {
            "remove_threshold": 90.0,  # Higher than add_threshold
            "add_threshold": 88.0,
        }
    }
    
    is_valid, errors = validate_config(invalid_config)
    
    assert is_valid is False
    assert len(errors) == 2
    assert any("lo_config" in error and "should be <=" in error for error in errors)
    assert any("de_config" in error and "should be <=" in error for error in errors)


def test_threshold_order_edge_case():
    """Test that remove_threshold can equal add_threshold"""
    edge_case_config = {
        "lo_config": {
            "remove_threshold": 45.0,
            "add_threshold": 45.0,  # Equal to remove_threshold
        },
        "de_config": {
            "remove_threshold": 85.0,
            "add_threshold": 85.0,  # Equal to remove_threshold
        }
    }
    
    is_valid, errors = validate_config(edge_case_config)
    
    # Should be valid (remove <= add)
    assert is_valid is True
    assert len(errors) == 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
