# tests/test_config_manager.py
# Unit tests for configuration manager
import os
import sys
import json
import tempfile
from unittest.mock import patch, mock_open

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


class TestConfigManagerMethods:
    """Test AppSettings class methods"""
    
    def test_load_settings_with_existing_file(self):
        """Test load_settings when config.json exists"""
        from logic.config_manager import AppSettings
        
        test_config = {
            "STATS_DAYS": 10,
            "GAN_DAYS": 20,
            "HIGH_WIN_THRESHOLD": 50.0,
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            with patch('logic.config_manager.CONFIG_FILE', temp_path):
                settings = AppSettings()
                assert settings.STATS_DAYS == 10
                assert settings.GAN_DAYS == 20
                assert settings.HIGH_WIN_THRESHOLD == 50.0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_load_settings_with_missing_file(self):
        """Test load_settings when config.json doesn't exist"""
        from logic.config_manager import AppSettings
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        os.unlink(temp_path)  # Ensure file doesn't exist
        
        try:
            with patch('logic.config_manager.CONFIG_FILE', temp_path):
                settings = AppSettings()
                # Should use defaults
                assert settings.STATS_DAYS == 7  # Default value
                assert settings.GAN_DAYS == 15  # Default value
                # File should be created
                assert os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_load_settings_with_invalid_json(self):
        """Test load_settings handles invalid JSON gracefully"""
        from logic.config_manager import AppSettings
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            temp_path = f.name
        
        try:
            with patch('logic.config_manager.CONFIG_FILE', temp_path):
                settings = AppSettings()
                # Should fallback to defaults
                assert settings.STATS_DAYS == 7  # Default value
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_save_settings_success(self):
        """Test save_settings saves correctly"""
        from logic.config_manager import AppSettings
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"STATS_DAYS": 7}, f)
            temp_path = f.name
        
        try:
            with patch('logic.config_manager.CONFIG_FILE', temp_path):
                settings = AppSettings()
                settings.STATS_DAYS = 15
                result, message = settings.save_settings(log=False)
                
                assert result is True
                assert "thành công" in message.lower() or "success" in message.lower()
                
                # Verify file was saved
                with open(temp_path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    assert saved_config["STATS_DAYS"] == 15
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_save_settings_error_handling(self):
        """Test save_settings handles errors gracefully"""
        from logic.config_manager import AppSettings
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"STATS_DAYS": 7}, f)
            temp_path = f.name
        
        try:
            with patch('logic.config_manager.CONFIG_FILE', temp_path):
                settings = AppSettings()
                
                # Mock open to raise an error
                with patch('builtins.open', side_effect=PermissionError("Access denied")):
                    result, message = settings.save_settings(log=False)
                    assert result is False
                    assert "lỗi" in message.lower() or "error" in message.lower()
        finally:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def test_update_setting_success(self):
        """Test update_setting updates and saves correctly"""
        from logic.config_manager import AppSettings
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"STATS_DAYS": 7}, f)
            temp_path = f.name
        
        try:
            with patch('logic.config_manager.CONFIG_FILE', temp_path):
                settings = AppSettings()
                result, message = settings.update_setting("STATS_DAYS", "14")
                
                assert result is True
                assert settings.STATS_DAYS == 14
                
                # Verify saved
                with open(temp_path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    assert saved_config["STATS_DAYS"] == 14
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_update_setting_invalid_key(self):
        """Test update_setting with invalid key"""
        from logic.config_manager import AppSettings
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"STATS_DAYS": 7}, f)
            temp_path = f.name
        
        try:
            with patch('logic.config_manager.CONFIG_FILE', temp_path):
                settings = AppSettings()
                result, message = settings.update_setting("INVALID_KEY", "10")
                
                assert result is False
                assert "không tồn tại" in message.lower() or "not exist" in message.lower()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_update_setting_invalid_value(self):
        """Test update_setting with invalid value type"""
        from logic.config_manager import AppSettings
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"STATS_DAYS": 7}, f)
            temp_path = f.name
        
        try:
            with patch('logic.config_manager.CONFIG_FILE', temp_path):
                settings = AppSettings()
                result, message = settings.update_setting("STATS_DAYS", "not_a_number")
                
                assert result is False
                assert "lỗi" in message.lower() or "error" in message.lower()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_all_settings(self):
        """Test get_all_settings returns all settings"""
        from logic.config_manager import AppSettings
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"STATS_DAYS": 10}, f)
            temp_path = f.name
        
        try:
            with patch('logic.config_manager.CONFIG_FILE', temp_path):
                settings = AppSettings()
                all_settings = settings.get_all_settings()
                
                assert isinstance(all_settings, dict)
                assert "STATS_DAYS" in all_settings
                assert "GAN_DAYS" in all_settings
                assert "HIGH_WIN_THRESHOLD" in all_settings
                assert all_settings["STATS_DAYS"] == 10
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_update_setting_type_conversion_int(self):
        """Test update_setting converts string to int"""
        from logic.config_manager import AppSettings
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"STATS_DAYS": 7}, f)
            temp_path = f.name
        
        try:
            with patch('logic.config_manager.CONFIG_FILE', temp_path):
                settings = AppSettings()
                result, _ = settings.update_setting("STATS_DAYS", "20")
                
                assert result is True
                assert isinstance(settings.STATS_DAYS, int)
                assert settings.STATS_DAYS == 20
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_update_setting_type_conversion_float(self):
        """Test update_setting converts string to float"""
        from logic.config_manager import AppSettings
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"HIGH_WIN_THRESHOLD": 47.0}, f)
            temp_path = f.name
        
        try:
            with patch('logic.config_manager.CONFIG_FILE', temp_path):
                settings = AppSettings()
                result, _ = settings.update_setting("HIGH_WIN_THRESHOLD", "55.5")
                
                assert result is True
                assert isinstance(settings.HIGH_WIN_THRESHOLD, float)
                assert settings.HIGH_WIN_THRESHOLD == 55.5
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_update_setting_type_conversion_string(self):
        """Test update_setting handles string values"""
        from logic.config_manager import AppSettings
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"AI_OBJECTIVE": "binary:logistic"}, f)
            temp_path = f.name
        
        try:
            with patch('logic.config_manager.CONFIG_FILE', temp_path):
                settings = AppSettings()
                result, _ = settings.update_setting("AI_OBJECTIVE", "binary:hinge")
                
                assert result is True
                assert isinstance(settings.AI_OBJECTIVE, str)
                assert settings.AI_OBJECTIVE == "binary:hinge"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
