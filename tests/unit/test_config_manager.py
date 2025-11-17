"""Unit tests for logic/config_manager.py module."""

import pytest
import os
import sys
import json
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from logic.config_manager import SETTINGS


class TestSettingsAccess:
    """Tests for SETTINGS object."""

    def test_settings_has_stats_days(self):
        """Test that SETTINGS has STATS_DAYS attribute."""
        assert hasattr(SETTINGS, "STATS_DAYS")
        assert isinstance(SETTINGS.STATS_DAYS, (int, float))

    def test_settings_has_gan_days(self):
        """Test that SETTINGS has GAN_DAYS attribute."""
        assert hasattr(SETTINGS, "GAN_DAYS")
        assert isinstance(SETTINGS.GAN_DAYS, (int, float))

    def test_settings_has_high_win_threshold(self):
        """Test that SETTINGS has HIGH_WIN_THRESHOLD attribute."""
        assert hasattr(SETTINGS, "HIGH_WIN_THRESHOLD")
        assert isinstance(SETTINGS.HIGH_WIN_THRESHOLD, (int, float))

    def test_settings_has_ai_params(self):
        """Test that SETTINGS has AI-related parameters."""
        assert hasattr(SETTINGS, "AI_PROB_THRESHOLD")
        assert hasattr(SETTINGS, "AI_MAX_DEPTH")
        assert hasattr(SETTINGS, "AI_N_ESTIMATORS")
        assert hasattr(SETTINGS, "AI_LEARNING_RATE")

    def test_settings_values_are_reasonable(self):
        """Test that SETTINGS values are within reasonable ranges."""
        assert 1 <= SETTINGS.STATS_DAYS <= 30
        assert 1 <= SETTINGS.GAN_DAYS <= 30
        assert 0 <= SETTINGS.HIGH_WIN_THRESHOLD <= 100
        assert 0 <= SETTINGS.AI_PROB_THRESHOLD <= 100


class TestConfigValues:
    """Tests for configuration values."""

    def test_ai_max_depth_range(self):
        """Test AI_MAX_DEPTH is in valid range."""
        assert 1 <= SETTINGS.AI_MAX_DEPTH <= 20

    def test_ai_n_estimators_range(self):
        """Test AI_N_ESTIMATORS is in valid range."""
        assert 10 <= SETTINGS.AI_N_ESTIMATORS <= 1000

    def test_ai_learning_rate_range(self):
        """Test AI_LEARNING_RATE is in valid range."""
        assert 0.001 <= SETTINGS.AI_LEARNING_RATE <= 1.0

    def test_ai_score_weight_range(self):
        """Test AI_SCORE_WEIGHT is in valid range."""
        assert 0 <= SETTINGS.AI_SCORE_WEIGHT <= 1.0


class TestConfigIntegration:
    """Integration tests for config functionality."""

    def test_config_file_exists(self):
        """Test that config.json file exists."""
        config_path = Path("config.json")
        assert config_path.exists(), "config.json should exist"

    def test_config_file_is_valid_json(self):
        """Test that config.json is valid JSON."""
        config_path = Path("config.json")
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail("config.json is not valid JSON")

    def test_config_has_required_keys(self):
        """Test that config.json has all required keys."""
        config_path = Path("config.json")
        with open(config_path, "r") as f:
            data = json.load(f)

        required_keys = [
            "STATS_DAYS",
            "GAN_DAYS",
            "HIGH_WIN_THRESHOLD",
            "AI_PROB_THRESHOLD",
            "AI_MAX_DEPTH",
            "AI_N_ESTIMATORS",
            "AI_LEARNING_RATE",
            "AI_SCORE_WEIGHT",
        ]

        for key in required_keys:
            assert key in data, f"config.json should have {key}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
