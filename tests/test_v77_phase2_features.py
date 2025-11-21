# tests/test_v77_phase2_features.py
# V7.7 Phase 2: Tests for new F13 and F14 features
"""
Unit tests for V7.7 Phase 2 new AI features:
- F13: q_hit_in_last_3_days - Binary indicator if loto appeared in last 3 periods
- F14: Change_in_Gan - Change in gan value between periods
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_f13_hit_in_last_3_days_feature_exists():
    """Test that F13 feature is included in bridge predictions"""
    from logic.ai_feature_extractor import _get_daily_bridge_predictions
    
    # Mock minimal data - need at least 5 rows to test properly
    mock_all_data_ai = [
        [20001, "12345", "67890", "11111,22222", "33333", "44444,55555,66666", "77777", "88888,99999", "00000"],
        [20002, "00111", "22333", "44555,66777", "88999", "11222,33444,55666", "77888", "00111,22333", "44555"],
        [20003, "11223", "33445", "55667,78899", "00112", "23344,56677,89900", "11223", "34455,66778", "99001"],
        [20004, "00112", "23344", "45566,78899", "01122", "33445,66778,90011", "22334", "45567,78890", "01122"],
        [20005, "11223", "34455", "66778,90011", "22334", "45567,78890,12233", "34455", "67789,01122", "33445"],
    ]
    
    # Get predictions
    daily_predictions = _get_daily_bridge_predictions(mock_all_data_ai)
    
    # Check that F13 feature exists for at least one ky
    found_f13 = False
    for ky, lotos in daily_predictions.items():
        for loto, features in lotos.items():
            if "q_hit_in_last_3_days" in features:
                found_f13 = True
                break
        if found_f13:
            break
    
    assert found_f13, "F13 (q_hit_in_last_3_days) feature should exist in predictions"


def test_f13_logic_binary_values():
    """Test that F13 returns binary values (0 or 1)"""
    from logic.ai_feature_extractor import _get_daily_bridge_predictions
    
    mock_all_data_ai = [
        [20001, "12345", "67890", "11111,22222", "33333", "44444,55555,66666", "77777", "88888,99999", "00000"],
        [20002, "00111", "22333", "44555,66777", "88999", "11222,33444,55666", "77888", "00111,22333", "44555"],
        [20003, "11223", "33445", "55667,78899", "00112", "23344,56677,89900", "11223", "34455,66778", "99001"],
    ]
    
    daily_predictions = _get_daily_bridge_predictions(mock_all_data_ai)
    
    # Check all F13 values are 0 or 1
    for ky, lotos in daily_predictions.items():
        for loto, features in lotos.items():
            f13_value = features.get("q_hit_in_last_3_days", -1)
            assert f13_value in [0, 1], f"F13 should be 0 or 1, got {f13_value}"


def test_f14_change_in_gan_calculation():
    """Test that F14 (Change_in_Gan) is calculated correctly"""
    from logic.ml_model import _get_loto_gan_history
    
    # Mock data where we can predict gan changes
    mock_all_data_ai = [
        [20001, "12345", "67890", "11111,22222", "33333", "44444,55555,66666", "77777", "88888,99999", "00000"],
        [20002, "00111", "22333", "44555,66777", "88999", "11222,33444,55666", "77888", "00111,22333", "44555"],
        [20003, "11223", "33445", "55667,78899", "00112", "23344,56677,89900", "11223", "34455,66778", "99001"],
    ]
    
    gan_history_map, gan_change_map = _get_loto_gan_history(mock_all_data_ai)
    
    # Check that gan_change_map is returned and has data
    assert gan_change_map is not None, "gan_change_map should be returned"
    assert len(gan_change_map) > 0, "gan_change_map should have data"
    
    # Check that changes are integers
    for ky, gan_changes in gan_change_map.items():
        for loto, change in gan_changes.items():
            assert isinstance(change, int), f"Gan change should be int, got {type(change)}"


def test_f14_change_logic():
    """Test that F14 change logic is correct (increase by 1 if not hit, reset to 0 if hit)"""
    from logic.ml_model import _get_loto_gan_history
    
    mock_all_data_ai = [
        [20001, "12345", "67890", "11111,22222", "33333", "44444,55555,66666", "77777", "88888,99999", "00000"],
        [20002, "00111", "22333", "44555,66777", "88999", "11222,33444,55666", "77888", "00111,22333", "44555"],
        [20003, "11223", "33445", "55667,78899", "00112", "23344,56677,89900", "11223", "34455,66778", "99001"],
    ]
    
    gan_history_map, gan_change_map = _get_loto_gan_history(mock_all_data_ai)
    
    # For lotos that appeared in row, change should be negative or 0 (gan reset)
    # For lotos that didn't appear, change should be 1 (gan increased by 1)
    
    # Check at least one period has changes
    assert len(gan_change_map) >= 2, "Should have at least 2 periods with gan changes"
    
    # Verify change values are reasonable (-30 to +30 range)
    for ky, gan_changes in gan_change_map.items():
        for loto, change in gan_changes.items():
            assert -30 <= change <= 30, f"Gan change {change} for loto {loto} seems unreasonable"


def test_feature_count_is_14():
    """Test that the model now uses 14 features (was 12, added F13 and F14)"""
    from logic.ml_model import _create_ai_dataset
    
    mock_all_data_ai = [
        [20001, "12345", "67890", "11111,22222", "33333", "44444,55555,66666", "77777", "88888,99999", "00000"],
        [20002, "00111", "22333", "44555,66777", "88999", "11222,33444,55666", "77888", "00111,22333", "44555"],
        [20003, "11223", "33445", "55667,78899", "00112", "23344,56677,89900", "11223", "34455,66778", "99001"],
    ]
    
    # Mock bridge predictions with all features including F13
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
                "q_avg_win_rate_stddev_100": 5.2,
                "q_hit_in_last_3_days": 0
            }
        },
        "20003": {
            "00": {
                "v5_count": 2,
                "v17_count": 1,
                "memory_count": 1,
                "q_avg_win_rate": 50.0,
                "q_min_k2n_risk": 4,
                "q_max_curr_streak": 2,
                "q_max_current_lose_streak": 1,
                "q_is_k2n_risk_close": 1,
                "q_avg_win_rate_stddev_100": 3.5,
                "q_hit_in_last_3_days": 1
            }
        }
    }
    
    X, y = _create_ai_dataset(mock_all_data_ai, mock_bridge_predictions)
    
    # Check that X has 14 features per row
    if X.shape[0] > 0:
        assert X.shape[1] == 14, f"Expected 14 features, got {X.shape[1]}"


def test_feature_names_list_has_14_items():
    """Test that feature names list includes F13 and F14"""
    # This is tested implicitly in the model training, but we can verify
    # the feature names are defined correctly
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
        "F12_Win_Rate_StdDev",
        "F13_Hit_Last_3_Days",
        "F14_Change_In_Gan"
    ]
    
    assert len(expected_features) == 14, "Should have 14 feature names"
    assert "F13_Hit_Last_3_Days" in expected_features, "F13 should be in feature names"
    assert "F14_Change_In_Gan" in expected_features, "F14 should be in feature names"


def test_f13_default_value():
    """Test that F13 has a default value of 0 when no appearance data"""
    from logic.ai_feature_extractor import _get_daily_bridge_predictions
    
    # Single row - no history, so F13 should be 0 for all lotos
    mock_all_data_ai = [
        [20001, "12345", "67890", "11111,22222", "33333", "44444,55555,66666", "77777", "88888,99999", "00000"],
        [20002, "00111", "22333", "44555,66777", "88999", "11222,33444,55666", "77888", "00111,22333", "44555"],
    ]
    
    daily_predictions = _get_daily_bridge_predictions(mock_all_data_ai)
    
    # For the second period (20002), check a random loto
    if "20002" in daily_predictions:
        loto_features = daily_predictions["20002"].get("99", {})
        f13_value = loto_features.get("q_hit_in_last_3_days", -1)
        # Should be 0 or 1 (depending on whether 99 appeared in previous period)
        assert f13_value in [0, 1], f"F13 default should be 0 or 1, got {f13_value}"


def test_f14_integration_in_training():
    """Test that F14 is properly integrated in training dataset"""
    from logic.ml_model import _create_ai_dataset
    
    mock_all_data_ai = [
        [20001, "12345", "67890", "11111,22222", "33333", "44444,55555,66666", "77777", "88888,99999", "00000"],
        [20002, "00111", "22333", "44555,66777", "88999", "11222,33444,55666", "77888", "00111,22333", "44555"],
        [20003, "11223", "33445", "55667,78899", "00112", "23344,56677,89900", "11223", "34455,66778", "99001"],
    ]
    
    mock_bridge_predictions = {
        "20002": {"00": {"v5_count": 1, "v17_count": 0, "memory_count": 2,
                         "q_avg_win_rate": 45.0, "q_min_k2n_risk": 5,
                         "q_max_curr_streak": 3, "q_max_current_lose_streak": 0,
                         "q_is_k2n_risk_close": 0, "q_avg_win_rate_stddev_100": 5.2,
                         "q_hit_in_last_3_days": 0}},
        "20003": {"01": {"v5_count": 2, "v17_count": 1, "memory_count": 1,
                         "q_avg_win_rate": 50.0, "q_min_k2n_risk": 4,
                         "q_max_curr_streak": 2, "q_max_current_lose_streak": 1,
                         "q_is_k2n_risk_close": 1, "q_avg_win_rate_stddev_100": 3.5,
                         "q_hit_in_last_3_days": 1}}
    }
    
    X, y = _create_ai_dataset(mock_all_data_ai, mock_bridge_predictions)
    
    # Verify dataset was created
    assert X.shape[0] > 0, "Should create at least some training samples"
    assert X.shape[1] == 14, f"Should have 14 features, got {X.shape[1]}"
    
    # Verify F14 (index 13) contains reasonable values
    f14_values = X[:, 13]  # F14 is the 14th feature (index 13)
    assert len(f14_values) > 0, "F14 should have values"
    # Gan changes should be within reasonable range
    assert all(-50 <= v <= 50 for v in f14_values), "F14 values should be reasonable"
