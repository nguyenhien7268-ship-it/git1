# tests/test_config_manager.py
# Unit tests for configuration manager
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_settings_loads_from_config_json():
    """Test that SETTINGS loads config correctly"""
    from logic.config_manager import SETTINGS

    # Check key attributes exist
    assert hasattr(SETTINGS, "STATS_DAYS"), "STATS_DAYS attribute missing"
    assert hasattr(SETTINGS, "HIGH_WIN_THRESHOLD"), "HIGH_WIN_THRESHOLD missing"
    assert hasattr(SETTINGS, "GAN_DAYS"), "GAN_DAYS missing"

    # Check values are reasonable
    assert SETTINGS.STATS_DAYS > 0, "STATS_DAYS should be positive"
    assert SETTINGS.HIGH_WIN_THRESHOLD > 0, "HIGH_WIN_THRESHOLD should be positive"
    assert SETTINGS.GAN_DAYS > 0, "GAN_DAYS should be positive"


def test_settings_has_ai_parameters():
    """Test that AI configuration parameters exist"""
    from logic.config_manager import SETTINGS

    # Check AI-related settings
    assert hasattr(SETTINGS, "AI_PROB_THRESHOLD"), "AI_PROB_THRESHOLD missing"
    assert hasattr(SETTINGS, "AI_MAX_DEPTH"), "AI_MAX_DEPTH missing"
    assert hasattr(SETTINGS, "AI_N_ESTIMATORS"), "AI_N_ESTIMATORS missing"
    assert hasattr(SETTINGS, "AI_LEARNING_RATE"), "AI_LEARNING_RATE missing"


def test_settings_get_method_with_default():
    """Test SETTINGS attributes can be accessed"""
    from logic.config_manager import SETTINGS

    # Test existing attribute
    stats_days = getattr(SETTINGS, "STATS_DAYS", 999)
    assert stats_days != 999, "Should return actual value, not default"
    assert isinstance(stats_days, int), "STATS_DAYS should be an integer"

    # Test non-existing attribute returns default
    fake_attr = getattr(SETTINGS, "NON_EXISTENT_KEY", 123)
    assert fake_attr == 123, "Should return default for non-existent attribute"


def test_config_has_k2n_risk_parameters():
    """Test K2N risk management parameters"""
    from logic.config_manager import SETTINGS

    assert hasattr(SETTINGS, "K2N_RISK_START_THRESHOLD"), "K2N_RISK_START_THRESHOLD missing"
    assert hasattr(SETTINGS, "K2N_RISK_PENALTY_PER_FRAME"), "K2N_RISK_PENALTY_PER_FRAME missing"

    # Check reasonable values
    assert SETTINGS.K2N_RISK_START_THRESHOLD >= 0, "K2N threshold should be non-negative"
    assert SETTINGS.K2N_RISK_PENALTY_PER_FRAME >= 0, "K2N penalty should be non-negative"
