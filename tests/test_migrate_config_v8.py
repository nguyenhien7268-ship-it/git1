"""
Unit tests for migrate_config_v8.py script.

Tests the migration from V7 single-threshold config to V8 dual-config architecture.
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import functions from the migration script
from scripts.migrate_config_v8 import (
    extract_old_values,
    create_dual_config,
    merge_configs,
    validate_config,
)


class TestExtractOldValues:
    """Test extraction of old configuration values."""

    def test_extract_existing_values(self):
        """Test extracting values when they exist in config."""
        config = {
            "AUTO_PRUNE_MIN_RATE": 43.0,
            "AUTO_ADD_MIN_RATE": 45.0,
            "OTHER_KEY": "value"
        }
        
        result = extract_old_values(config)
        
        assert result["AUTO_PRUNE_MIN_RATE"] == 43.0
        assert result["AUTO_ADD_MIN_RATE"] == 45.0

    def test_extract_with_defaults(self):
        """Test extracting values with defaults when keys missing."""
        config = {
            "OTHER_KEY": "value"
        }
        
        result = extract_old_values(config)
        
        assert result["AUTO_PRUNE_MIN_RATE"] == 40.0  # default
        assert result["AUTO_ADD_MIN_RATE"] == 50.0  # default

    def test_extract_partial_values(self):
        """Test extracting when only some values exist."""
        config = {
            "AUTO_PRUNE_MIN_RATE": 35.0
        }
        
        result = extract_old_values(config)
        
        assert result["AUTO_PRUNE_MIN_RATE"] == 35.0
        assert result["AUTO_ADD_MIN_RATE"] == 50.0  # default


class TestCreateDualConfig:
    """Test creation of dual-config structure."""

    def test_create_basic_structure(self):
        """Test creating dual-config from old values."""
        old_values = {
            "AUTO_PRUNE_MIN_RATE": 43.0,
            "AUTO_ADD_MIN_RATE": 45.0
        }
        
        result = create_dual_config(old_values)
        
        # Check structure exists
        assert "lo_config" in result
        assert "de_config" in result

    def test_lo_config_values(self):
        """Test lo_config has correct values."""
        old_values = {
            "AUTO_PRUNE_MIN_RATE": 43.0,
            "AUTO_ADD_MIN_RATE": 45.0
        }
        
        result = create_dual_config(old_values)
        lo_config = result["lo_config"]
        
        assert lo_config["remove_threshold"] == 43.0
        assert lo_config["add_threshold"] == 45.0
        assert lo_config["enable_threshold"] == 40.0  # 43 - 3
        assert "description" in lo_config

    def test_de_config_values(self):
        """Test de_config has correct values."""
        old_values = {
            "AUTO_PRUNE_MIN_RATE": 43.0,
            "AUTO_ADD_MIN_RATE": 45.0
        }
        
        result = create_dual_config(old_values)
        de_config = result["de_config"]
        
        assert de_config["remove_threshold"] == 43.0
        assert de_config["add_threshold"] == 45.0
        assert de_config["enable_threshold"] == 40.0  # 43 - 3
        assert "description" in de_config

    def test_enable_threshold_minimum(self):
        """Test enable_threshold has a minimum value of 35%."""
        old_values = {
            "AUTO_PRUNE_MIN_RATE": 36.0,  # Would result in 33.0 without minimum
            "AUTO_ADD_MIN_RATE": 40.0
        }
        
        result = create_dual_config(old_values)
        
        # Should be 35.0 (minimum) not 33.0 (36 - 3)
        assert result["lo_config"]["enable_threshold"] == 35.0
        assert result["de_config"]["enable_threshold"] == 35.0


class TestMergeConfigs:
    """Test merging old and new configurations."""

    def test_merge_preserves_old_keys(self):
        """Test that old configuration keys are preserved."""
        old_config = {
            "STATS_DAYS": 7,
            "GAN_DAYS": 8,
            "AUTO_PRUNE_MIN_RATE": 43.0,
            "AUTO_ADD_MIN_RATE": 45.0
        }
        new_config = {
            "lo_config": {"remove_threshold": 43.0},
            "de_config": {"remove_threshold": 43.0}
        }
        
        result = merge_configs(old_config, new_config)
        
        # Old keys should be preserved (except AUTO_PRUNE/AUTO_ADD)
        assert result["STATS_DAYS"] == 7
        assert result["GAN_DAYS"] == 8

    def test_merge_adds_new_structures(self):
        """Test that new dual-config structures are added."""
        old_config = {
            "AUTO_PRUNE_MIN_RATE": 43.0,
            "AUTO_ADD_MIN_RATE": 45.0
        }
        new_config = {
            "lo_config": {"remove_threshold": 43.0},
            "de_config": {"remove_threshold": 43.0}
        }
        
        result = merge_configs(old_config, new_config)
        
        assert "lo_config" in result
        assert "de_config" in result

    def test_merge_creates_deprecated_keys(self):
        """Test that deprecated keys are created."""
        old_config = {
            "AUTO_PRUNE_MIN_RATE": 43.0,
            "AUTO_ADD_MIN_RATE": 45.0
        }
        new_config = {
            "lo_config": {"remove_threshold": 43.0},
            "de_config": {"remove_threshold": 43.0}
        }
        
        result = merge_configs(old_config, new_config)
        
        assert "AUTO_PRUNE_MIN_RATE_DEPRECATED" in result
        assert "AUTO_ADD_MIN_RATE_DEPRECATED" in result
        assert result["AUTO_PRUNE_MIN_RATE_DEPRECATED"] == 43.0
        assert result["AUTO_ADD_MIN_RATE_DEPRECATED"] == 45.0

    def test_merge_removes_old_keys(self):
        """Test that old keys are removed."""
        old_config = {
            "AUTO_PRUNE_MIN_RATE": 43.0,
            "AUTO_ADD_MIN_RATE": 45.0,
            "OTHER_KEY": "value"
        }
        new_config = {
            "lo_config": {"remove_threshold": 43.0},
            "de_config": {"remove_threshold": 43.0}
        }
        
        result = merge_configs(old_config, new_config)
        
        # Old keys should be removed
        assert "AUTO_PRUNE_MIN_RATE" not in result
        assert "AUTO_ADD_MIN_RATE" not in result
        # Other keys should remain
        assert result["OTHER_KEY"] == "value"


class TestValidateConfig:
    """Test configuration validation."""

    def test_validate_complete_config(self):
        """Test validation of a complete, correct config."""
        config = {
            "lo_config": {
                "remove_threshold": 43.0,
                "add_threshold": 45.0,
                "enable_threshold": 40.0
            },
            "de_config": {
                "remove_threshold": 43.0,
                "add_threshold": 45.0,
                "enable_threshold": 40.0
            },
            "AUTO_PRUNE_MIN_RATE_DEPRECATED": 43.0,
            "AUTO_ADD_MIN_RATE_DEPRECATED": 45.0
        }
        
        result = validate_config(config)
        
        assert result is True

    def test_validate_missing_lo_config(self):
        """Test validation fails when lo_config is missing."""
        config = {
            "de_config": {
                "remove_threshold": 43.0,
                "add_threshold": 45.0,
                "enable_threshold": 40.0
            },
            "AUTO_PRUNE_MIN_RATE_DEPRECATED": 43.0,
            "AUTO_ADD_MIN_RATE_DEPRECATED": 45.0
        }
        
        result = validate_config(config)
        
        assert result is False

    def test_validate_missing_de_config(self):
        """Test validation fails when de_config is missing."""
        config = {
            "lo_config": {
                "remove_threshold": 43.0,
                "add_threshold": 45.0,
                "enable_threshold": 40.0
            },
            "AUTO_PRUNE_MIN_RATE_DEPRECATED": 43.0,
            "AUTO_ADD_MIN_RATE_DEPRECATED": 45.0
        }
        
        result = validate_config(config)
        
        assert result is False

    def test_validate_missing_thresholds(self):
        """Test validation fails when thresholds are missing."""
        config = {
            "lo_config": {
                "remove_threshold": 43.0
                # Missing add_threshold and enable_threshold
            },
            "de_config": {
                "remove_threshold": 43.0,
                "add_threshold": 45.0,
                "enable_threshold": 40.0
            },
            "AUTO_PRUNE_MIN_RATE_DEPRECATED": 43.0,
            "AUTO_ADD_MIN_RATE_DEPRECATED": 45.0
        }
        
        result = validate_config(config)
        
        assert result is False

    def test_validate_deprecated_keys_missing(self):
        """Test validation fails when deprecated keys are missing."""
        config = {
            "lo_config": {
                "remove_threshold": 43.0,
                "add_threshold": 45.0,
                "enable_threshold": 40.0
            },
            "de_config": {
                "remove_threshold": 43.0,
                "add_threshold": 45.0,
                "enable_threshold": 40.0
            }
            # Missing deprecated keys
        }
        
        result = validate_config(config)
        
        assert result is False

    def test_validate_old_keys_still_present(self):
        """Test validation fails when old keys are still present."""
        config = {
            "lo_config": {
                "remove_threshold": 43.0,
                "add_threshold": 45.0,
                "enable_threshold": 40.0
            },
            "de_config": {
                "remove_threshold": 43.0,
                "add_threshold": 45.0,
                "enable_threshold": 40.0
            },
            "AUTO_PRUNE_MIN_RATE_DEPRECATED": 43.0,
            "AUTO_ADD_MIN_RATE_DEPRECATED": 45.0,
            "AUTO_PRUNE_MIN_RATE": 43.0  # Should not be present
        }
        
        result = validate_config(config)
        
        assert result is False

    def test_validate_invalid_threshold_order_lo(self):
        """Test validation fails when lo_config thresholds are in wrong order."""
        config = {
            "lo_config": {
                "remove_threshold": 43.0,
                "add_threshold": 40.0,  # Should be >= remove_threshold
                "enable_threshold": 40.0
            },
            "de_config": {
                "remove_threshold": 43.0,
                "add_threshold": 45.0,
                "enable_threshold": 40.0
            },
            "AUTO_PRUNE_MIN_RATE_DEPRECATED": 43.0,
            "AUTO_ADD_MIN_RATE_DEPRECATED": 45.0
        }
        
        result = validate_config(config)
        
        assert result is False

    def test_validate_invalid_threshold_order_de(self):
        """Test validation fails when de_config thresholds are in wrong order."""
        config = {
            "lo_config": {
                "remove_threshold": 43.0,
                "add_threshold": 45.0,
                "enable_threshold": 40.0
            },
            "de_config": {
                "remove_threshold": 38.0,
                "add_threshold": 45.0,
                "enable_threshold": 40.0  # Should be <= remove_threshold
            },
            "AUTO_PRUNE_MIN_RATE_DEPRECATED": 43.0,
            "AUTO_ADD_MIN_RATE_DEPRECATED": 45.0
        }
        
        result = validate_config(config)
        
        assert result is False


class TestEndToEndMigration:
    """Test end-to-end migration process."""

    def test_complete_migration_flow(self):
        """Test complete migration from V7 to V8."""
        # Start with V7 config
        old_config = {
            "STATS_DAYS": 7,
            "GAN_DAYS": 8,
            "HIGH_WIN_THRESHOLD": 45.0,
            "AUTO_PRUNE_MIN_RATE": 43.0,
            "AUTO_ADD_MIN_RATE": 45.0,
            "K2N_RISK_START_THRESHOLD": 3
        }
        
        # Extract old values
        old_values = extract_old_values(old_config)
        
        # Create dual-config
        new_config = create_dual_config(old_values)
        
        # Merge
        merged_config = merge_configs(old_config, new_config)
        
        # Validate
        is_valid = validate_config(merged_config)
        
        # Assertions
        assert is_valid is True
        assert "lo_config" in merged_config
        assert "de_config" in merged_config
        assert "AUTO_PRUNE_MIN_RATE" not in merged_config
        assert "AUTO_ADD_MIN_RATE" not in merged_config
        assert "AUTO_PRUNE_MIN_RATE_DEPRECATED" in merged_config
        assert "AUTO_ADD_MIN_RATE_DEPRECATED" in merged_config
        assert merged_config["STATS_DAYS"] == 7
        assert merged_config["GAN_DAYS"] == 8

    def test_migration_preserves_all_settings(self):
        """Test that migration preserves all non-migrated settings."""
        old_config = {
            "STATS_DAYS": 7,
            "GAN_DAYS": 8,
            "HIGH_WIN_THRESHOLD": 45.0,
            "AUTO_PRUNE_MIN_RATE": 43.0,
            "AUTO_ADD_MIN_RATE": 45.0,
            "K2N_RISK_START_THRESHOLD": 3,
            "AI_PROB_THRESHOLD": 55.0,
            "AI_SCORE_WEIGHT": 0.4,
            "VOTE_SCORE_WEIGHT": 0.5
        }
        
        old_values = extract_old_values(old_config)
        new_config = create_dual_config(old_values)
        merged_config = merge_configs(old_config, new_config)
        
        # Check all non-migrated keys are preserved
        assert merged_config["STATS_DAYS"] == 7
        assert merged_config["GAN_DAYS"] == 8
        assert merged_config["HIGH_WIN_THRESHOLD"] == 45.0
        assert merged_config["K2N_RISK_START_THRESHOLD"] == 3
        assert merged_config["AI_PROB_THRESHOLD"] == 55.0
        assert merged_config["AI_SCORE_WEIGHT"] == 0.4
        assert merged_config["VOTE_SCORE_WEIGHT"] == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
