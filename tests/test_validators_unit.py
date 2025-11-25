# tests/test_validators_unit.py
"""
Unit tests for validators.py - Core validation functions
"""
import os
import tempfile
import pytest

from logic.validators import (
    ValidationError,
    validate_file_upload,
    validate_config_value,
    validate_config_dict,
)


class TestValidateFileUpload:
    """Test file upload validation"""
    
    def test_valid_txt_file(self, tmp_path):
        """Test valid .txt file"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        result = validate_file_upload(str(test_file))
        assert result is True
    
    def test_valid_json_file(self, tmp_path):
        """Test valid .json file"""
        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value"}')
        
        result = validate_file_upload(str(test_file))
        assert result is True
    
    def test_invalid_extension(self, tmp_path):
        """Test invalid file extension"""
        test_file = tmp_path / "test.exe"
        test_file.write_text("test")
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_upload(str(test_file))
        assert "Invalid file type" in str(exc_info.value)
    
    def test_file_too_large(self, tmp_path, monkeypatch):
        """Test file size validation"""
        from logic import validators
        
        # Mock MAX_FILE_SIZE_BYTES to 10 bytes for testing
        monkeypatch.setattr(validators, "MAX_FILE_SIZE_BYTES", 10)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("x" * 100)  # 100 bytes > 10 bytes
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_upload(str(test_file))
        assert "File too large" in str(exc_info.value)
    
    def test_content_too_large(self, tmp_path, monkeypatch):
        """Test content size validation"""
        from logic import validators
        
        monkeypatch.setattr(validators, "MAX_FILE_SIZE_BYTES", 10)
        
        large_content = "x" * 100
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_upload("test.txt", content=large_content)
        assert "Content too large" in str(exc_info.value)
    
    def test_too_many_lines(self, tmp_path, monkeypatch):
        """Test line count validation"""
        from logic import validators
        
        monkeypatch.setattr(validators, "MAX_LINES", 5)
        
        content = "\n".join([f"line {i}" for i in range(10)])
        
        with pytest.raises(ValidationError) as exc_info:
            validate_file_upload("test.txt", content=content)
        assert "Too many lines" in str(exc_info.value)


class TestValidateConfigValue:
    """Test configuration value validation"""
    
    def test_valid_stats_days(self):
        """Test valid STATS_DAYS"""
        result = validate_config_value("STATS_DAYS", 7)
        assert result == 7
    
    def test_stats_days_too_low(self):
        """Test STATS_DAYS below minimum"""
        with pytest.raises(ValidationError) as exc_info:
            validate_config_value("STATS_DAYS", 0)
        assert "must be between 1 and 30" in str(exc_info.value)
    
    def test_stats_days_too_high(self):
        """Test STATS_DAYS above maximum"""
        with pytest.raises(ValidationError) as exc_info:
            validate_config_value("STATS_DAYS", 31)
        assert "must be between 1 and 30" in str(exc_info.value)
    
    def test_valid_gan_days(self):
        """Test valid GAN_DAYS"""
        result = validate_config_value("GAN_DAYS", 15)
        assert result == 15
    
    def test_gan_days_out_of_range(self):
        """Test GAN_DAYS out of range"""
        with pytest.raises(ValidationError):
            validate_config_value("GAN_DAYS", 101)
    
    def test_valid_high_win_threshold(self):
        """Test valid HIGH_WIN_THRESHOLD"""
        result = validate_config_value("HIGH_WIN_THRESHOLD", 47.0)
        assert result == 47.0
    
    def test_high_win_threshold_out_of_range(self):
        """Test HIGH_WIN_THRESHOLD out of range"""
        with pytest.raises(ValidationError):
            validate_config_value("HIGH_WIN_THRESHOLD", 101)
    
    def test_type_conversion_int(self):
        """Test automatic type conversion for int"""
        result = validate_config_value("STATS_DAYS", "7")
        assert result == 7
        assert isinstance(result, int)
    
    def test_type_conversion_float(self):
        """Test automatic type conversion for float"""
        result = validate_config_value("HIGH_WIN_THRESHOLD", "47.5")
        assert result == 47.5
        assert isinstance(result, float)
    
    def test_invalid_type(self):
        """Test invalid type conversion"""
        with pytest.raises(ValidationError) as exc_info:
            validate_config_value("STATS_DAYS", "not_a_number")
        assert "Invalid type" in str(exc_info.value)
    
    def test_unknown_key(self):
        """Test unknown configuration key"""
        with pytest.raises(ValidationError) as exc_info:
            validate_config_value("UNKNOWN_KEY", 123)
        assert "Unknown configuration key" in str(exc_info.value)
    
    def test_ai_learning_rate_valid(self):
        """Test valid AI_LEARNING_RATE"""
        result = validate_config_value("AI_LEARNING_RATE", 0.1)
        assert result == 0.1
    
    def test_ai_learning_rate_too_low(self):
        """Test AI_LEARNING_RATE below minimum"""
        with pytest.raises(ValidationError):
            validate_config_value("AI_LEARNING_RATE", 0.0001)
    
    def test_ai_learning_rate_too_high(self):
        """Test AI_LEARNING_RATE above maximum"""
        with pytest.raises(ValidationError):
            validate_config_value("AI_LEARNING_RATE", 2.0)
    
    def test_k2n_risk_start_threshold_valid(self):
        """Test valid K2N_RISK_START_THRESHOLD"""
        result = validate_config_value("K2N_RISK_START_THRESHOLD", 4)
        assert result == 4
    
    def test_k2n_risk_start_threshold_out_of_range(self):
        """Test K2N_RISK_START_THRESHOLD out of range"""
        with pytest.raises(ValidationError):
            validate_config_value("K2N_RISK_START_THRESHOLD", 21)


class TestValidateConfigDict:
    """Test configuration dictionary validation"""
    
    def test_valid_config_dict(self):
        """Test valid configuration dictionary"""
        config = {
            "STATS_DAYS": 7,
            "GAN_DAYS": 15,
            "HIGH_WIN_THRESHOLD": 47.0,
        }
        
        result = validate_config_dict(config)
        assert result == config
        assert result["STATS_DAYS"] == 7
    
    def test_config_dict_with_invalid_value(self):
        """Test config dict with invalid value"""
        config = {
            "STATS_DAYS": 100,  # Invalid: > 30
            "GAN_DAYS": 15,
        }
        
        with pytest.raises(ValidationError):
            validate_config_dict(config)
    
    def test_config_dict_with_type_conversion(self):
        """Test config dict with string values that need conversion"""
        config = {
            "STATS_DAYS": "7",  # String that should convert to int
            "HIGH_WIN_THRESHOLD": "47.5",  # String that should convert to float
        }
        
        result = validate_config_dict(config)
        assert result["STATS_DAYS"] == 7
        assert isinstance(result["STATS_DAYS"], int)
        assert result["HIGH_WIN_THRESHOLD"] == 47.5
        assert isinstance(result["HIGH_WIN_THRESHOLD"], float)
    
    def test_empty_config_dict(self):
        """Test empty configuration dictionary"""
        result = validate_config_dict({})
        assert result == {}









