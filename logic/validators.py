# logic/validators.py
"""
Input validation utilities for security and data integrity.
"""
import os

from .constants import (
    ALLOWED_FILE_EXTENSIONS,
    DEFAULT_SETTINGS,
    MAX_FILE_SIZE_BYTES,
    MAX_LINES,
)


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_file_upload(file_path, content=None):
    """
    Validate file upload for security and size limits.
    
    Args:
        file_path: Path to the file
        content: Optional pre-loaded content string
    
    Raises:
        ValidationError: If validation fails
    
    Returns:
        True if validation passes
    """
    # Check file extension
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in ALLOWED_FILE_EXTENSIONS:
        raise ValidationError(
            f"Invalid file type: {ext}. "
            f"Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
        )
    
    # Check file size if file exists
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        if size > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                f"File too large: {size / 1024 / 1024:.1f}MB. "
                f"Max: {MAX_FILE_SIZE_BYTES / 1024 / 1024}MB"
            )
    
    # Check content size if provided
    if content:
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                f"Content too large: {len(content) / 1024 / 1024:.1f}MB"
            )
        
        # Check line count
        lines = content.split('\n')
        if len(lines) > MAX_LINES:
            raise ValidationError(
                f"Too many lines: {len(lines):,}. Max: {MAX_LINES:,}"
            )
    
    return True


def validate_config_value(key, value):
    """
    Validate configuration values for type and range.
    
    Args:
        key: Configuration key name
        value: Value to validate
    
    Raises:
        ValidationError: If validation fails
    
    Returns:
        Validated value (possibly converted to correct type)
    """
    if key not in DEFAULT_SETTINGS:
        raise ValidationError(f"Unknown configuration key: {key}")
    
    expected_type = type(DEFAULT_SETTINGS[key])
    
    # Type conversion and validation
    try:
        if expected_type == int:
            value = int(value)
        elif expected_type == float:
            value = float(value)
        elif expected_type == str:
            value = str(value)
    except (ValueError, TypeError):
        raise ValidationError(
            f"Invalid type for {key}: expected {expected_type.__name__}, got {type(value).__name__}"
        )
    
    # Range validations for specific keys
    if key == "STATS_DAYS":
        if not (1 <= value <= 30):
            raise ValidationError(f"STATS_DAYS must be between 1 and 30, got {value}")
    
    elif key == "GAN_DAYS":
        if not (1 <= value <= 100):
            raise ValidationError(f"GAN_DAYS must be between 1 and 100, got {value}")
    
    elif key == "HIGH_WIN_THRESHOLD":
        if not (0 <= value <= 100):
            raise ValidationError(f"HIGH_WIN_THRESHOLD must be between 0 and 100, got {value}")
    
    elif key == "AUTO_ADD_MIN_RATE":
        if not (0 <= value <= 100):
            raise ValidationError(f"AUTO_ADD_MIN_RATE must be between 0 and 100, got {value}")
    
    elif key == "AUTO_PRUNE_MIN_RATE":
        if not (0 <= value <= 100):
            raise ValidationError(f"AUTO_PRUNE_MIN_RATE must be between 0 and 100, got {value}")
    
    elif key == "K2N_RISK_START_THRESHOLD":
        if not (0 <= value <= 20):
            raise ValidationError(f"K2N_RISK_START_THRESHOLD must be between 0 and 20, got {value}")
    
    elif key == "K2N_RISK_PENALTY_PER_FRAME":
        if not (0 <= value <= 10):
            raise ValidationError(f"K2N_RISK_PENALTY_PER_FRAME must be between 0 and 10, got {value}")
    
    elif key == "AI_PROB_THRESHOLD":
        if not (0 <= value <= 100):
            raise ValidationError(f"AI_PROB_THRESHOLD must be between 0 and 100, got {value}")
    
    elif key == "AI_MAX_DEPTH":
        if not (1 <= value <= 20):
            raise ValidationError(f"AI_MAX_DEPTH must be between 1 and 20, got {value}")
    
    elif key == "AI_N_ESTIMATORS":
        if not (10 <= value <= 1000):
            raise ValidationError(f"AI_N_ESTIMATORS must be between 10 and 1000, got {value}")
    
    elif key == "AI_LEARNING_RATE":
        if not (0.001 <= value <= 1.0):
            raise ValidationError(f"AI_LEARNING_RATE must be between 0.001 and 1.0, got {value}")
    
    elif key == "AI_SCORE_WEIGHT":
        if not (0 <= value <= 1.0):
            raise ValidationError(f"AI_SCORE_WEIGHT must be between 0 and 1.0, got {value}")
    
    return value


def validate_config_dict(config_dict):
    """
    Validate an entire configuration dictionary.
    
    Args:
        config_dict: Dictionary of configuration values
    
    Raises:
        ValidationError: If any validation fails
    
    Returns:
        Validated configuration dictionary
    """
    validated = {}
    
    for key, value in config_dict.items():
        validated[key] = validate_config_value(key, value)
    
    return validated
