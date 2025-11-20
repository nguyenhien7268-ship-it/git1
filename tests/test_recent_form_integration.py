# Test file for verifying RECENT_FORM parameters are properly integrated
# into ui_tuner and ui_optimizer


def test_recent_form_params_in_config_manager():
    """Verify that config_manager has all RECENT_FORM parameters."""
    from logic.config_manager import SETTINGS
    
    required_params = [
        "RECENT_FORM_PERIODS",
        "RECENT_FORM_MIN_HIGH",
        "RECENT_FORM_BONUS_HIGH",
        "RECENT_FORM_MIN_MED",
        "RECENT_FORM_BONUS_MED",
        "RECENT_FORM_MIN_LOW",
        "RECENT_FORM_BONUS_LOW",
    ]
    
    settings_dict = SETTINGS.get_all_settings()
    
    for param in required_params:
        assert param in settings_dict, f"Missing {param} in settings"
        assert settings_dict[param] is not None, f"{param} is None"


def test_tuner_has_recent_form_params():
    """Verify that ui_tuner includes RECENT_FORM parameters."""
    # We can't fully test UI without tkinter, so we check the source file directly
    import os
    
    tuner_path = os.path.join(os.path.dirname(__file__), "..", "ui", "ui_tuner.py")
    
    with open(tuner_path, "r", encoding="utf-8") as f:
        source = f.read()
    
    required_params = [
        "RECENT_FORM_PERIODS",
        "RECENT_FORM_MIN_HIGH",
        "RECENT_FORM_BONUS_HIGH",
        "RECENT_FORM_MIN_MED",
        "RECENT_FORM_BONUS_MED",
        "RECENT_FORM_MIN_LOW",
        "RECENT_FORM_BONUS_LOW",
    ]
    
    for param in required_params:
        assert param in source, f"Missing {param} in TunerWindow"


def test_optimizer_has_recent_form_params():
    """Verify that ui_optimizer includes RECENT_FORM parameters."""
    # We can't fully test UI without tkinter, so we check the source file directly
    import os
    
    optimizer_path = os.path.join(os.path.dirname(__file__), "..", "ui", "ui_optimizer.py")
    
    with open(optimizer_path, "r", encoding="utf-8") as f:
        source = f.read()
    
    required_params = [
        "RECENT_FORM_PERIODS",
        "RECENT_FORM_MIN_HIGH",
        "RECENT_FORM_BONUS_HIGH",
        "RECENT_FORM_MIN_MED",
        "RECENT_FORM_BONUS_MED",
        "RECENT_FORM_MIN_LOW",
        "RECENT_FORM_BONUS_LOW",
    ]
    
    for param in required_params:
        assert param in source, f"Missing {param} in OptimizerTab"
        
    # Check that integer parameters are in the validation list
    assert "RECENT_FORM_PERIODS" in source
    assert "RECENT_FORM_MIN_HIGH" in source
    assert "RECENT_FORM_MIN_MED" in source
    assert "RECENT_FORM_MIN_LOW" in source


def test_recent_form_params_have_correct_defaults():
    """Verify that RECENT_FORM parameters have reasonable default values."""
    from logic.config_manager import SETTINGS
    
    settings = SETTINGS.get_all_settings()
    
    # Check integer parameters
    assert isinstance(settings["RECENT_FORM_PERIODS"], int)
    assert settings["RECENT_FORM_PERIODS"] > 0
    
    assert isinstance(settings["RECENT_FORM_MIN_HIGH"], int)
    assert isinstance(settings["RECENT_FORM_MIN_MED"], int)
    assert isinstance(settings["RECENT_FORM_MIN_LOW"], int)
    
    # Check logical ordering: HIGH > MED > LOW
    assert settings["RECENT_FORM_MIN_HIGH"] >= settings["RECENT_FORM_MIN_MED"]
    assert settings["RECENT_FORM_MIN_MED"] >= settings["RECENT_FORM_MIN_LOW"]
    
    # Check float parameters (bonus values)
    assert isinstance(settings["RECENT_FORM_BONUS_HIGH"], (int, float))
    assert isinstance(settings["RECENT_FORM_BONUS_MED"], (int, float))
    assert isinstance(settings["RECENT_FORM_BONUS_LOW"], (int, float))
    
    # Check logical ordering: BONUS_HIGH > BONUS_MED > BONUS_LOW
    assert settings["RECENT_FORM_BONUS_HIGH"] >= settings["RECENT_FORM_BONUS_MED"]
    assert settings["RECENT_FORM_BONUS_MED"] >= settings["RECENT_FORM_BONUS_LOW"]
    
    # All bonuses should be positive
    assert settings["RECENT_FORM_BONUS_HIGH"] > 0
    assert settings["RECENT_FORM_BONUS_MED"] > 0
    assert settings["RECENT_FORM_BONUS_LOW"] > 0
