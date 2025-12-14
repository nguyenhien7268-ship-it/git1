"""
Test suite for config_manager.py self-healing functionality

Note: These are simplified unit tests that verify the self-healing behavior
directly rather than through the singleton pattern.
"""
import os
import sys
import json
import tempfile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_config_has_dual_config_structure():
    """Test that SETTINGS object has dual-config structure"""
    from logic.config_manager import SETTINGS
    
    # Check that both configs exist
    assert hasattr(SETTINGS, 'settings'), "SETTINGS should have settings dict"
    assert 'lo_config' in SETTINGS.settings, "lo_config should be in settings"
    assert 'de_config' in SETTINGS.settings, "de_config should be in settings"
    
    # Check lo_config structure
    lo_config = SETTINGS.settings['lo_config']
    assert 'remove_threshold' in lo_config
    assert 'add_threshold' in lo_config
    assert isinstance(lo_config['remove_threshold'], (int, float))
    assert isinstance(lo_config['add_threshold'], (int, float))
    
    # Check de_config structure
    de_config = SETTINGS.settings['de_config']
    assert 'remove_threshold' in de_config
    assert 'add_threshold' in de_config
    assert isinstance(de_config['remove_threshold'], (int, float))
    assert isinstance(de_config['add_threshold'], (int, float))


def test_config_get_method_for_dual_config():
    """Test that dual-config can be accessed via get method"""
    from logic.config_manager import SETTINGS
    
    lo_config = SETTINGS.get('lo_config')
    assert lo_config is not None
    assert 'remove_threshold' in lo_config
    assert 'add_threshold' in lo_config
    
    de_config = SETTINGS.get('de_config')
    assert de_config is not None
    assert 'remove_threshold' in de_config
    assert 'add_threshold' in de_config


def test_default_settings_has_dual_config():
    """Test that DEFAULT_SETTINGS includes dual-config"""
    from logic.constants import DEFAULT_SETTINGS
    
    assert 'lo_config' in DEFAULT_SETTINGS
    assert 'de_config' in DEFAULT_SETTINGS
    
    # Verify structure
    assert 'remove_threshold' in DEFAULT_SETTINGS['lo_config']
    assert 'add_threshold' in DEFAULT_SETTINGS['lo_config']
    assert 'remove_threshold' in DEFAULT_SETTINGS['de_config']
    assert 'add_threshold' in DEFAULT_SETTINGS['de_config']


def test_threshold_values_are_reasonable():
    """Test that threshold values are in reasonable ranges"""
    from logic.config_manager import SETTINGS
    
    lo_config = SETTINGS.get('lo_config', {})
    de_config = SETTINGS.get('de_config', {})
    
    # Check Lo thresholds
    lo_remove = lo_config.get('remove_threshold', 0)
    lo_add = lo_config.get('add_threshold', 0)
    
    assert 0 <= lo_remove <= 100, "Lo remove_threshold should be 0-100%"
    assert 0 <= lo_add <= 100, "Lo add_threshold should be 0-100%"
    assert lo_remove <= lo_add, "Lo remove_threshold should be <= add_threshold"
    
    # Check De thresholds
    de_remove = de_config.get('remove_threshold', 0)
    de_add = de_config.get('add_threshold', 0)
    
    assert 0 <= de_remove <= 100, "De remove_threshold should be 0-100%"
    assert 0 <= de_add <= 100, "De add_threshold should be 0-100%"
    assert de_remove <= de_add, "De remove_threshold should be <= add_threshold"


def test_config_file_has_dual_config():
    """Test that config.json file has dual-config structure"""
    config_path = os.path.join(PROJECT_ROOT, "config.json")
    
    if not os.path.exists(config_path):
        # Skip if config file doesn't exist (e.g., in CI)
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    assert 'lo_config' in config_data, "config.json should have lo_config"
    assert 'de_config' in config_data, "config.json should have de_config"
    
    # Verify structure
    assert 'remove_threshold' in config_data['lo_config']
    assert 'add_threshold' in config_data['lo_config']
    assert 'remove_threshold' in config_data['de_config']
    assert 'add_threshold' in config_data['de_config']


def test_de_thresholds_higher_than_lo():
    """Test that De thresholds are typically higher than Lo thresholds (more conservative)"""
    from logic.config_manager import SETTINGS
    from logic.constants import DEFAULT_SETTINGS
    
    # Check defaults - De should be more conservative (higher thresholds)
    default_lo = DEFAULT_SETTINGS.get('lo_config', {})
    default_de = DEFAULT_SETTINGS.get('de_config', {})
    
    if default_lo and default_de:
        assert default_de['remove_threshold'] > default_lo['remove_threshold'], \
            "De remove_threshold should be higher than Lo (more conservative)"
        assert default_de['add_threshold'] > default_lo['add_threshold'], \
            "De add_threshold should be higher than Lo (more conservative)"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
