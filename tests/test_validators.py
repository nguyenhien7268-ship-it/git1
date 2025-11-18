# tests/test_validators.py
# Unit tests for validators module
import pytest


def test_validation_error_is_exception():
    """Test that ValidationError is an Exception"""
    from logic.validators import ValidationError
    
    assert issubclass(ValidationError, Exception)


def test_validate_file_upload_accepts_valid_txt():
    """Test validation passes for valid .txt file"""
    from logic.validators import validate_file_upload
    
    # Should not raise for valid extension
    result = validate_file_upload("test.txt")
    assert result is True


def test_validate_file_upload_accepts_valid_json():
    """Test validation passes for valid .json file"""
    from logic.validators import validate_file_upload
    
    result = validate_file_upload("test.json")
    assert result is True


def test_validate_file_upload_rejects_invalid_extension():
    """Test validation fails for invalid file extension"""
    from logic.validators import ValidationError, validate_file_upload
    
    with pytest.raises(ValidationError) as exc_info:
        validate_file_upload("test.exe")
    
    assert "Invalid file type" in str(exc_info.value)


def test_validate_file_upload_checks_content_size():
    """Test validation checks content size"""
    from logic.validators import ValidationError, validate_file_upload
    
    # Create content larger than limit
    large_content = "x" * (20 * 1024 * 1024)  # 20MB
    
    with pytest.raises(ValidationError) as exc_info:
        validate_file_upload("test.txt", content=large_content)
    
    assert "too large" in str(exc_info.value).lower()


def test_validate_file_upload_checks_line_count():
    """Test validation checks line count"""
    from logic.validators import ValidationError, validate_file_upload
    
    # Create content with too many lines
    many_lines = "\n".join(["line"] * 200_000)
    
    with pytest.raises(ValidationError) as exc_info:
        validate_file_upload("test.txt", content=many_lines)
    
    assert "Too many lines" in str(exc_info.value)


def test_validate_config_value_accepts_valid_stats_days():
    """Test config validation accepts valid STATS_DAYS"""
    from logic.validators import validate_config_value
    
    result = validate_config_value("STATS_DAYS", 7)
    assert result == 7


def test_validate_config_value_converts_string_to_int():
    """Test config validation converts types"""
    from logic.validators import validate_config_value
    
    result = validate_config_value("STATS_DAYS", "10")
    assert result == 10
    assert isinstance(result, int)


def test_validate_config_value_rejects_out_of_range():
    """Test config validation rejects out of range values"""
    from logic.validators import ValidationError, validate_config_value
    
    with pytest.raises(ValidationError) as exc_info:
        validate_config_value("STATS_DAYS", 100)  # Max is 30
    
    assert "between 1 and 30" in str(exc_info.value)


def test_validate_config_value_rejects_invalid_type():
    """Test config validation rejects invalid types"""
    from logic.validators import ValidationError, validate_config_value
    
    with pytest.raises(ValidationError):
        validate_config_value("STATS_DAYS", "not_a_number")


def test_validate_config_value_rejects_unknown_key():
    """Test config validation rejects unknown keys"""
    from logic.validators import ValidationError, validate_config_value
    
    with pytest.raises(ValidationError) as exc_info:
        validate_config_value("UNKNOWN_KEY", 123)
    
    assert "Unknown configuration key" in str(exc_info.value)


def test_validate_config_dict_validates_all_keys():
    """Test config dict validation"""
    from logic.validators import validate_config_dict
    
    config = {
        "STATS_DAYS": 10,
        "GAN_DAYS": 20,
        "HIGH_WIN_THRESHOLD": 50.0,
    }
    
    result = validate_config_dict(config)
    assert result["STATS_DAYS"] == 10
    assert result["GAN_DAYS"] == 20
    assert result["HIGH_WIN_THRESHOLD"] == 50.0


def test_validate_config_dict_rejects_invalid_values():
    """Test config dict validation rejects invalid values"""
    from logic.validators import ValidationError, validate_config_dict
    
    config = {
        "STATS_DAYS": 100,  # Out of range
        "GAN_DAYS": 20,
    }
    
    with pytest.raises(ValidationError):
        validate_config_dict(config)
