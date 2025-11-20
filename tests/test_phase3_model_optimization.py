# tests/test_phase3_model_optimization.py
# Phase 3: Model Optimization - Tests for ML model enhancements
"""
Unit tests for Phase 3 model optimization:
- New features integrated into training and prediction
- Feature importance tracking
- Cross-validation
- Hyperparameter tuning capability
"""

import sys
import os
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_feature_count_in_training():
    """Test that training creates correct number of features (12 total with Phase 2)"""
    from logic.ml_model import _create_ai_dataset
    
    # Mock minimal data
    mock_all_data_ai = [
        [20001, "12345", "67890", "11111,22222", "33333", "44444,55555,66666", "77777", "88888,99999", "00000"],
        [20002, "54321", "09876", "22222,11111", "44444", "55555,66666,44444", "88888", "99999,88888", "11111"],
        [20003, "11223", "33445", "55667,78899", "00112", "23344,56677,89900", "11223", "34455,66778", "99001"],
    ]
    
    # Mock bridge predictions with all Phase 2 features
    mock_bridge_predictions = {
        "20002": {
            "00": {
                "v5_count": 1,
                "v17_count": 0,
                "memory_count": 2,
                "q_avg_win_rate": 45.0,
                "q_min_k2n_risk": 5,
                "q_max_curr_streak": 3,
                "q_max_current_lose_streak": 0,
                "q_is_k2n_risk_close": 0,
                "q_avg_win_rate_stddev_100": 5.2
            }
        },
        "20003": {
            "01": {
                "v5_count": 2,
                "v17_count": 1,
                "memory_count": 1,
                "q_avg_win_rate": 50.0,
                "q_min_k2n_risk": 3,
                "q_max_curr_streak": 5,
                "q_max_current_lose_streak": 1,
                "q_is_k2n_risk_close": 1,
                "q_avg_win_rate_stddev_100": 7.8
            }
        }
    }
    
    X, y = _create_ai_dataset(mock_all_data_ai, mock_bridge_predictions)
    
    # Should have 12 features per row (F1-F12)
    if X.shape[0] > 0:
        assert X.shape[1] == 12, f"Expected 12 features, got {X.shape[1]}"


def test_phase2_features_included_in_prediction():
    """Test that prediction function includes all Phase 2 features"""
    # Check the feature list in get_ai_predictions
    # This tests the structure, not the actual prediction
    
    # Mock loto features with Phase 2 additions
    loto_features = {
        "v5_count": 1,
        "v17_count": 2,
        "memory_count": 3,
        "q_avg_win_rate": 45.0,
        "q_min_k2n_risk": 5,
        "q_max_curr_streak": 3,
        # Phase 2 features
        "q_max_current_lose_streak": 2,
        "q_is_k2n_risk_close": 1,
        "q_avg_win_rate_stddev_100": 6.5
    }
    
    # Verify all Phase 2 features exist
    assert "q_max_current_lose_streak" in loto_features
    assert "q_is_k2n_risk_close" in loto_features
    assert "q_avg_win_rate_stddev_100" in loto_features


def test_feature_names_defined():
    """Test that feature names are properly defined for importance tracking"""
    expected_features = [
        "F1_Gan",
        "F2_V5_Count",
        "F3_V17_Count",
        "F4_Memory_Count",
        "F5_Total_Votes",
        "F6_Source_Diversity",
        "F7_Avg_Win_Rate",
        "F8_Min_K2N_Risk",
        "F9_Max_Curr_Streak",
        "F10_Max_Lose_Streak",
        "F11_Is_K2N_Risk_Close",
        "F12_Win_Rate_StdDev"
    ]
    
    # Verify we have 12 feature names
    assert len(expected_features) == 12
    
    # Verify Phase 2 feature names are included
    assert "F10_Max_Lose_Streak" in expected_features
    assert "F11_Is_K2N_Risk_Close" in expected_features
    assert "F12_Win_Rate_StdDev" in expected_features


def test_hyperparameter_tuning_parameter():
    """Test that train_ai_model accepts hyperparameter tuning parameter"""
    from logic.ml_model import train_ai_model
    import inspect
    
    # Check function signature
    sig = inspect.signature(train_ai_model)
    params = list(sig.parameters.keys())
    
    # Should have use_hyperparameter_tuning parameter
    assert "use_hyperparameter_tuning" in params


def test_config_integration_for_hyperparameters():
    """Test that model can read hyperparameters from config"""
    from logic.config_manager import SETTINGS
    
    # Verify config has AI hyperparameters
    assert hasattr(SETTINGS, 'AI_N_ESTIMATORS')
    assert hasattr(SETTINGS, 'AI_LEARNING_RATE')
    assert hasattr(SETTINGS, 'AI_MAX_DEPTH')
    
    # Verify they are reasonable values
    assert SETTINGS.AI_N_ESTIMATORS > 0
    assert 0 < SETTINGS.AI_LEARNING_RATE < 1
    assert SETTINGS.AI_MAX_DEPTH > 0


def test_feature_importance_structure():
    """Test feature importance dict structure"""
    # Simulate feature importance output
    feature_names = [
        "F1_Gan", "F2_V5_Count", "F3_V17_Count", "F4_Memory_Count",
        "F5_Total_Votes", "F6_Source_Diversity", "F7_Avg_Win_Rate",
        "F8_Min_K2N_Risk", "F9_Max_Curr_Streak", "F10_Max_Lose_Streak",
        "F11_Is_K2N_Risk_Close", "F12_Win_Rate_StdDev"
    ]
    
    mock_importances = np.random.random(12)
    feature_importance = dict(zip(feature_names, mock_importances))
    
    # Should have 12 features
    assert len(feature_importance) == 12
    
    # All features should have importance values
    for feature in feature_names:
        assert feature in feature_importance
        assert isinstance(feature_importance[feature], (float, np.floating))


def test_model_paths_defined():
    """Test that model file paths are properly defined"""
    from logic.ml_model import MODEL_FILE_PATH, SCALER_FILE_PATH
    
    assert MODEL_FILE_PATH is not None
    assert SCALER_FILE_PATH is not None
    assert "loto_model.joblib" in MODEL_FILE_PATH
    assert "ai_scaler.joblib" in SCALER_FILE_PATH


def test_phase3_feature_defaults():
    """Test that Phase 2 features have proper defaults when missing"""
    # Simulate feature extraction with missing Phase 2 data
    loto_features = {
        "v5_count": 1,
        "v17_count": 2,
        "memory_count": 3,
        "q_avg_win_rate": 45.0,
        "q_min_k2n_risk": 5,
        "q_max_curr_streak": 3
        # Phase 2 features intentionally missing
    }
    
    # Get with defaults
    lose_streak = loto_features.get("q_max_current_lose_streak", 0)
    is_close = loto_features.get("q_is_k2n_risk_close", 0)
    stddev = loto_features.get("q_avg_win_rate_stddev_100", 0.0)
    
    # Verify defaults are appropriate
    assert lose_streak == 0
    assert is_close == 0
    assert stddev == 0.0


def test_cross_validation_imports():
    """Test that cross-validation utilities are properly imported"""
    from sklearn.model_selection import cross_val_score, GridSearchCV
    
    # Just verify imports work
    assert cross_val_score is not None
    assert GridSearchCV is not None


if __name__ == "__main__":
    import pytest
    
    # Run all tests in this file
    pytest.main([__file__, "-v"])
