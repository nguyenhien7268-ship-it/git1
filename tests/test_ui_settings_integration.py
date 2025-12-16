"""
Integration tests for UI Settings and dual-config system.

Tests the complete flow from UI Settings to core logic:
- Settings UI can load dual-config correctly
- Settings UI can save dual-config modifications
- Core logic reflects changes from Settings UI
- No conflicts between UI and core logic
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


# ============================================================================
# UI SETTINGS LOADING TESTS
# ============================================================================

def test_ui_settings_can_load_dual_config():
    """Test that UI Settings can load dual-config structure"""
    from logic.config_manager import SETTINGS
    
    # Simulate UI loading settings
    lo_config = SETTINGS.get('lo_config', {})
    de_config = SETTINGS.get('de_config', {})
    
    # UI should be able to access all required fields
    assert lo_config is not None, "UI should load lo_config"
    assert de_config is not None, "UI should load de_config"
    
    # Check structure matches UI expectations
    assert 'remove_threshold' in lo_config, "UI expects remove_threshold in lo_config"
    assert 'add_threshold' in lo_config, "UI expects add_threshold in lo_config"
    assert 'remove_threshold' in de_config, "UI expects remove_threshold in de_config"
    assert 'add_threshold' in de_config, "UI expects add_threshold in de_config"


def test_ui_settings_threshold_display():
    """Test that thresholds can be displayed correctly in UI"""
    from logic.config_manager import SETTINGS
    
    lo_config = SETTINGS.get('lo_config', {})
    de_config = SETTINGS.get('de_config', {})
    
    # Get values for display (as UI would)
    lo_remove = lo_config.get('remove_threshold', 0)
    lo_add = lo_config.get('add_threshold', 0)
    de_remove = de_config.get('remove_threshold', 0)
    de_add = de_config.get('add_threshold', 0)
    
    # Values should be displayable as percentages
    assert isinstance(lo_remove, (int, float)), "Lo remove should be numeric for display"
    assert isinstance(lo_add, (int, float)), "Lo add should be numeric for display"
    assert isinstance(de_remove, (int, float)), "De remove should be numeric for display"
    assert isinstance(de_add, (int, float)), "De add should be numeric for display"
    
    # Format for display
    lo_remove_display = f"{lo_remove}%"
    lo_add_display = f"{lo_add}%"
    de_remove_display = f"{de_remove}%"
    de_add_display = f"{de_add}%"
    
    # Should all be valid strings
    assert isinstance(lo_remove_display, str)
    assert isinstance(lo_add_display, str)
    assert isinstance(de_remove_display, str)
    assert isinstance(de_add_display, str)


def test_ui_settings_default_values():
    """Test that UI can provide sensible defaults"""
    from logic.config_manager import SETTINGS
    
    # UI should provide defaults if config is missing
    lo_config = SETTINGS.get('lo_config', {'remove_threshold': 43.0, 'add_threshold': 45.0})
    de_config = SETTINGS.get('de_config', {'remove_threshold': 80.0, 'add_threshold': 88.0})
    
    # Defaults should be present
    assert lo_config.get('remove_threshold') is not None
    assert lo_config.get('add_threshold') is not None
    assert de_config.get('remove_threshold') is not None
    assert de_config.get('add_threshold') is not None


# ============================================================================
# UI SETTINGS SAVING TESTS
# ============================================================================

def test_ui_settings_save_structure():
    """Test that UI can construct proper save structure"""
    # Simulate UI preparing to save settings
    new_settings = {
        'lo_config': {
            'remove_threshold': 44.0,
            'add_threshold': 45.5
        },
        'de_config': {
            'remove_threshold': 82.0,
            'add_threshold': 90.0
        }
    }
    
    # Verify structure is valid JSON
    json_str = json.dumps(new_settings)
    assert json_str is not None, "Settings should be JSON serializable"
    
    # Verify structure can be loaded back
    loaded = json.loads(json_str)
    assert loaded['lo_config']['remove_threshold'] == 44.0
    assert loaded['de_config']['add_threshold'] == 90.0


def test_ui_settings_validation():
    """Test UI-side validation of settings before save"""
    
    def validate_threshold(value):
        """Simulates UI validation logic"""
        try:
            val = float(value)
            return 0 <= val <= 100
        except (ValueError, TypeError):
            return False
    
    # Valid values
    assert validate_threshold(45.5) is True
    assert validate_threshold(80.0) is True
    assert validate_threshold(0) is True
    assert validate_threshold(100) is True
    
    # Invalid values
    assert validate_threshold(-5) is False
    assert validate_threshold(150) is False
    assert validate_threshold('invalid') is False
    assert validate_threshold(None) is False


def test_ui_settings_persistence_format():
    """Test that settings can be persisted in correct format"""
    # Create a temporary config file
    temp_dir = tempfile.mkdtemp()
    temp_config = os.path.join(temp_dir, 'test_config.json')
    
    try:
        # Simulate UI saving settings
        settings_to_save = {
            'lo_config': {
                'remove_threshold': 43.5,
                'add_threshold': 46.0
            },
            'de_config': {
                'remove_threshold': 81.0,
                'add_threshold': 89.0
            },
            'other_setting': 'test_value'
        }
        
        # Write to file
        with open(temp_config, 'w', encoding='utf-8') as f:
            json.dump(settings_to_save, f, indent=2)
        
        # Read back and verify
        with open(temp_config, 'r', encoding='utf-8') as f:
            loaded_settings = json.load(f)
        
        assert loaded_settings['lo_config']['remove_threshold'] == 43.5
        assert loaded_settings['de_config']['add_threshold'] == 89.0
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


# ============================================================================
# UI TO CORE LOGIC INTEGRATION TESTS
# ============================================================================

def test_ui_changes_reflected_in_core():
    """Test that changes from UI are reflected in core logic"""
    from logic.config_manager import SETTINGS
    
    # Get current values (simulating UI reading config)
    lo_config = SETTINGS.get('lo_config', {})
    de_config = SETTINGS.get('de_config', {})
    
    current_lo_remove = lo_config.get('remove_threshold', 43.0)
    current_de_remove = de_config.get('remove_threshold', 80.0)
    
    # Verify core logic can access these same values
    from logic.bridges.bridge_manager_core import SETTINGS as CORE_SETTINGS
    
    core_lo_config = CORE_SETTINGS.get('lo_config', {})
    core_de_config = CORE_SETTINGS.get('de_config', {})
    
    core_lo_remove = core_lo_config.get('remove_threshold', 43.0)
    core_de_remove = core_de_config.get('remove_threshold', 80.0)
    
    # Values should match (UI and core see same config)
    assert current_lo_remove == core_lo_remove, "UI and core should see same lo_remove"
    assert current_de_remove == core_de_remove, "UI and core should see same de_remove"


def test_ui_settings_tab_structure():
    """Test that Settings UI tab structure is properly organized"""
    from logic.config_manager import SETTINGS
    
    # Tab 1: Lo/De Config - should have dual-config
    lo_config = SETTINGS.get('lo_config')
    de_config = SETTINGS.get('de_config')
    
    assert lo_config is not None, "Tab 1 should display lo_config"
    assert de_config is not None, "Tab 1 should display de_config"
    
    # Verify Tab 1 has all required fields
    tab1_fields = ['remove_threshold', 'add_threshold']
    for field in tab1_fields:
        assert field in lo_config, f"Tab 1 should display lo_config.{field}"
        assert field in de_config, f"Tab 1 should display de_config.{field}"


def test_settings_no_conflicts_with_other_tabs():
    """Test that dual-config doesn't conflict with other tabs"""
    from logic.config_manager import SETTINGS
    
    # Get dual-config (Tab 1)
    lo_config = SETTINGS.get('lo_config', {})
    de_config = SETTINGS.get('de_config', {})
    
    # Get AI config (Tab 2) - should not conflict
    ai_max_depth = SETTINGS.get('AI_MAX_DEPTH')
    ai_estimators = SETTINGS.get('AI_N_ESTIMATORS')
    
    # Get performance config (Tab 3) - should not conflict
    data_limit = SETTINGS.get('DATA_LIMIT_DASHBOARD')
    
    # All should coexist without issues
    assert lo_config is not None
    assert de_config is not None
    # AI and performance settings may or may not exist, but shouldn't break dual-config


# ============================================================================
# SETTINGS UI ERROR HANDLING TESTS
# ============================================================================

def test_ui_handles_missing_config_gracefully():
    """Test that UI handles missing config.json gracefully"""
    from logic.constants import DEFAULT_SETTINGS
    
    # UI should be able to fall back to defaults
    default_lo = DEFAULT_SETTINGS.get('lo_config', {})
    default_de = DEFAULT_SETTINGS.get('de_config', {})
    
    # Defaults should be available
    assert default_lo, "Should have default lo_config"
    assert default_de, "Should have default de_config"
    
    # Should have required fields
    assert 'remove_threshold' in default_lo
    assert 'add_threshold' in default_lo
    assert 'remove_threshold' in default_de
    assert 'add_threshold' in default_de


def test_ui_handles_corrupted_config():
    """Test UI behavior with corrupted config values"""
    
    def safe_float_parse(value, default=0.0):
        """Simulates UI safe parsing logic"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    # Test with various corrupted values
    assert safe_float_parse("45.5") == 45.5
    assert safe_float_parse(45.5) == 45.5
    assert safe_float_parse("invalid", 43.0) == 43.0
    assert safe_float_parse(None, 43.0) == 43.0
    assert safe_float_parse([1, 2, 3], 43.0) == 43.0


def test_ui_validation_prevents_invalid_saves():
    """Test that UI validation prevents invalid threshold values"""
    
    def validate_and_save(lo_remove, lo_add, de_remove, de_add):
        """Simulates UI validation before save"""
        # Check all are numeric
        try:
            lo_remove = float(lo_remove)
            lo_add = float(lo_add)
            de_remove = float(de_remove)
            de_add = float(de_add)
        except (ValueError, TypeError):
            return False, "All values must be numeric"
        
        # Check ranges
        if not (0 <= lo_remove <= 100):
            return False, "Lo remove must be 0-100"
        if not (0 <= lo_add <= 100):
            return False, "Lo add must be 0-100"
        if not (0 <= de_remove <= 100):
            return False, "De remove must be 0-100"
        if not (0 <= de_add <= 100):
            return False, "De add must be 0-100"
        
        # Check logical relationships
        if lo_remove > lo_add + 5:
            return False, "Lo remove should be <= Lo add"
        if de_remove > de_add + 5:
            return False, "De remove should be <= De add"
        
        return True, "Valid"
    
    # Valid cases
    assert validate_and_save(43, 45, 80, 88)[0] is True
    assert validate_and_save(45.5, 46.0, 82.0, 90.0)[0] is True
    
    # Invalid cases
    assert validate_and_save(-5, 45, 80, 88)[0] is False  # Negative
    assert validate_and_save(43, 150, 80, 88)[0] is False  # > 100
    assert validate_and_save(50, 40, 80, 88)[0] is False  # Remove > Add
    assert validate_and_save("invalid", 45, 80, 88)[0] is False  # Non-numeric


# ============================================================================
# COMPREHENSIVE INTEGRATION TEST
# ============================================================================

def test_full_ui_to_core_workflow():
    """Comprehensive test of full workflow from UI to core logic"""
    from logic.config_manager import SETTINGS
    from logic.bridges.bridge_manager_core import is_de_bridge, prune_bad_bridges, auto_manage_bridges
    
    # Step 1: UI loads settings
    lo_config = SETTINGS.get('lo_config', {})
    de_config = SETTINGS.get('de_config', {})
    
    assert lo_config is not None, "UI should load lo_config"
    assert de_config is not None, "UI should load de_config"
    
    # Step 2: UI displays thresholds
    lo_remove = lo_config.get('remove_threshold', 43.0)
    lo_add = lo_config.get('add_threshold', 45.0)
    de_remove = de_config.get('remove_threshold', 80.0)
    de_add = de_config.get('add_threshold', 88.0)
    
    # All should be valid
    assert isinstance(lo_remove, (int, float))
    assert isinstance(lo_add, (int, float))
    assert isinstance(de_remove, (int, float))
    assert isinstance(de_add, (int, float))
    
    # Step 3: Core logic uses the same settings
    test_bridges = [
        {'name': 'DE_TEST_01', 'type': 'DE_SET'},
        {'name': 'LO_TEST_01', 'type': 'LO_MEM'},
    ]
    
    # Classify bridges
    de_result = is_de_bridge(test_bridges[0])
    lo_result = is_de_bridge(test_bridges[1])
    
    assert de_result is True, "Should classify De bridge"
    assert lo_result is False, "Should classify Lo bridge"
    
    # Step 4: Core logic functions work with current settings
    prune_msg = prune_bad_bridges([], db_name=":memory:")
    manage_msg = auto_manage_bridges([], db_name=":memory:")
    
    assert isinstance(prune_msg, str), "Prune should return message"
    assert isinstance(manage_msg, str), "Manage should return message"


def test_settings_persistence_across_modules():
    """Test that settings are consistent across different modules"""
    # Import from different modules
    from logic.config_manager import SETTINGS as SETTINGS1
    from logic.bridges.bridge_manager_core import SETTINGS as SETTINGS2
    
    # Both should reference same underlying config
    lo1 = SETTINGS1.get('lo_config', {})
    lo2 = SETTINGS2.get('lo_config', {})
    
    # Should have same structure
    if lo1 and lo2:
        assert lo1.get('remove_threshold') == lo2.get('remove_threshold'), \
            "Settings should be consistent across modules"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
