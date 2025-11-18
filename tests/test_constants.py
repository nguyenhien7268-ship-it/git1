# tests/test_constants.py
# Unit tests for constants module


def test_default_settings_exist():
    """Test that DEFAULT_SETTINGS is defined"""
    from logic.constants import DEFAULT_SETTINGS
    
    assert DEFAULT_SETTINGS is not None
    assert isinstance(DEFAULT_SETTINGS, dict)
    assert len(DEFAULT_SETTINGS) > 0


def test_default_settings_has_required_keys():
    """Test that all required configuration keys exist"""
    from logic.constants import DEFAULT_SETTINGS
    
    required_keys = [
        "STATS_DAYS",
        "GAN_DAYS",
        "HIGH_WIN_THRESHOLD",
        "AUTO_ADD_MIN_RATE",
        "AUTO_PRUNE_MIN_RATE",
        "K2N_RISK_START_THRESHOLD",
        "K2N_RISK_PENALTY_PER_FRAME",
        "AI_PROB_THRESHOLD",
        "AI_MAX_DEPTH",
        "AI_N_ESTIMATORS",
        "AI_LEARNING_RATE",
        "AI_OBJECTIVE",
        "AI_SCORE_WEIGHT",
    ]
    
    for key in required_keys:
        assert key in DEFAULT_SETTINGS, f"Missing key: {key}"


def test_default_settings_values_are_reasonable():
    """Test that default values are within reasonable ranges"""
    from logic.constants import DEFAULT_SETTINGS
    
    assert DEFAULT_SETTINGS["STATS_DAYS"] > 0
    assert DEFAULT_SETTINGS["GAN_DAYS"] > 0
    assert 0 <= DEFAULT_SETTINGS["HIGH_WIN_THRESHOLD"] <= 100
    assert 0 <= DEFAULT_SETTINGS["AUTO_ADD_MIN_RATE"] <= 100
    assert 0 <= DEFAULT_SETTINGS["AUTO_PRUNE_MIN_RATE"] <= 100
    assert DEFAULT_SETTINGS["K2N_RISK_START_THRESHOLD"] >= 0
    assert DEFAULT_SETTINGS["K2N_RISK_PENALTY_PER_FRAME"] >= 0
    assert 0 <= DEFAULT_SETTINGS["AI_PROB_THRESHOLD"] <= 100


def test_file_upload_constants_defined():
    """Test that file upload limits are defined"""
    from logic.constants import (
        ALLOWED_FILE_EXTENSIONS,
        MAX_FILE_SIZE_BYTES,
        MAX_FILE_SIZE_MB,
        MAX_LINES,
    )
    
    assert MAX_FILE_SIZE_MB > 0
    assert MAX_FILE_SIZE_BYTES == MAX_FILE_SIZE_MB * 1024 * 1024
    assert MAX_LINES > 0
    assert len(ALLOWED_FILE_EXTENSIONS) > 0
    assert all(ext.startswith('.') for ext in ALLOWED_FILE_EXTENSIONS)
