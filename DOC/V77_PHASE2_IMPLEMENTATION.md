# V7.7 Phase 2 Implementation Guide

## Overview
This document describes the implementation of V7.7 Phase 2 features, which expanded the AI model from 12 to 14 features by adding F13 and F14.

## New Features

### F13: q_hit_in_last_3_days
**Purpose**: Binary indicator (0/1) to capture short-term momentum by checking if a loto appeared in the last 3 periods.

**Implementation**: `logic/ai_feature_extractor.py`
- Tracks loto appearances in `loto_appearance_history` dictionary
- Maintains sliding window of last 3 appearances per loto
- Returns 1 if loto has any recent appearance, 0 otherwise

**Benefits**:
- Captures short-term trends and momentum
- Helps identify "hot" lotos that are appearing frequently
- Complements F1 (Gan) which measures absence

**Code Location**: Lines 115-118, 190-200, 304-307

### F14: Change_in_Gan
**Purpose**: Tracks the change in gan value between consecutive periods to capture acceleration/deceleration of gan.

**Implementation**: `logic/ml_model.py`
- Modified `_get_loto_gan_history()` to return two maps:
  - `gan_history_map`: Absolute gan values (existing)
  - `gan_change_map`: Change in gan values (new)
- Change calculated as: `current_gan[loto] - prev_gan[loto]`
- Positive values: Gan is increasing (loto not appearing)
- Negative values: Gan decreased or reset (loto appeared)

**Benefits**:
- Detects when a loto is "heating up" (gan increasing steadily)
- Identifies potential "explosion points" (long absence followed by appearance)
- Provides rate-of-change information, not just absolute values

**Code Location**: Lines 41-83, 100-101, 192-193

## Feature Engineering Details

### Complete Feature List (14 Features)
1. **F1**: Gan - Days since last appearance
2. **F2**: V5_Count - Votes from 15 classic bridges
3. **F3**: V17_Count - Votes from saved bridges
4. **F4**: Memory_Count - Votes from 756 memory bridges
5. **F5**: Total_Votes - Sum of F2-F4
6. **F6**: Source_Diversity - Count of non-zero sources (max 3)
7. **F7**: Avg_Win_Rate - Average win rate from managed bridges
8. **F8**: Min_K2N_Risk - Minimum K2N risk score
9. **F9**: Max_Curr_Streak - Maximum current streak
10. **F10**: Max_Lose_Streak - Maximum current lose streak (Phase 2)
11. **F11**: Is_K2N_Risk_Close - Binary indicator for K2N proximity (Phase 2)
12. **F12**: Win_Rate_StdDev - Win rate standard deviation over 100 periods (Phase 2)
13. **F13**: Hit_Last_3_Days - NEW in V7.7 Phase 2
14. **F14**: Change_In_Gan - NEW in V7.7 Phase 2

## Training and Prediction Pipeline

### Training
```python
# In ml_model.py -> _create_ai_dataset()
gan_history_map, gan_change_map = _get_loto_gan_history(all_data_ai)

# For each loto in each period:
features.append(loto_features.get("q_hit_in_last_3_days", 0))  # F13
features.append(gan_change_for_actual_ky.get(loto, 0))         # F14
```

### Prediction
```python
# In ml_model.py -> get_ai_predictions()
gan_history_map, gan_change_map = _get_loto_gan_history(all_data_ai)
gan_change_today = gan_change_map.get(last_ky_str, {})

# For each loto:
features.append(loto_features.get("q_hit_in_last_3_days", 0))  # F13
features.append(gan_change_today.get(loto, 0))                 # F14
```

## Testing

### Test Coverage
Created `tests/test_v77_phase2_features.py` with 8 comprehensive tests:
1. `test_f13_hit_in_last_3_days_feature_exists` - Verifies F13 is present
2. `test_f13_logic_binary_values` - Validates F13 returns 0/1
3. `test_f14_change_in_gan_calculation` - Verifies F14 calculation
4. `test_f14_change_logic` - Validates F14 change logic
5. `test_feature_count_is_14` - Ensures 14 features in dataset
6. `test_feature_names_list_has_14_items` - Validates feature names
7. `test_f13_default_value` - Tests F13 default behavior
8. `test_f14_integration_in_training` - Integration test for F14

### Running Tests
```bash
# Run V7.7 Phase 2 specific tests
python -m pytest tests/test_v77_phase2_features.py -v

# Run all AI/ML tests
python -m pytest tests/test_phase2_features.py tests/test_phase3_model_optimization.py tests/test_v77_phase2_features.py -v
```

## Model Retraining

After implementing F13 and F14, the model MUST be retrained:

```python
# In UI or via command
from logic.ai_feature_extractor import run_ai_training_threaded

# Option 1: Standard training
run_ai_training_threaded(callback=your_callback)

# Option 2: With hyperparameter tuning (recommended for Phase 2 completion)
# Set use_hyperparameter_tuning=True in train_ai_model() call
```

**Important**: 
- Old models (with 12 features) are incompatible with new feature extraction
- After retraining, model will expect 14 features for all predictions
- Feature importance may shift with new features

## Expected Impact

### F13 (Hit_Last_3_Days) Impact
- Should help identify "hot streaks" and momentum
- May increase precision for frequently appearing lotos
- Complements recency bias in existing features

### F14 (Change_In_Gan) Impact
- Provides derivative information (rate of change)
- Should help predict "explosion points" after long gan periods
- May improve timing predictions for gan-based strategies

## Backward Compatibility

### Breaking Changes
- Old model files (*.joblib) with 12 features are incompatible
- Must retrain model after upgrading to V7.7 Phase 2
- Any external code calling `_get_loto_gan_history()` must handle 2 return values

### Migration Path
1. Update code to V7.7 Phase 2
2. Run full model retraining with `use_hyperparameter_tuning=True`
3. Verify predictions work correctly
4. Delete old model files if any issues

## Next Steps: Phase 3

Phase 3 will focus on:
1. **Meta-Learner**: Second-level AI to combine predictions with manual scores
2. **Adaptive Retraining**: Automated incremental and full retraining
3. **Rolling Window**: Configure optimal training window size
4. **Performance Monitoring**: Track F1-Score degradation over time

See `V77_PHASE3_DESIGN.md` for detailed Phase 3 architecture (to be created).

## References

- Problem Statement: Root README or issue tracker
- Implementation: `logic/ai_feature_extractor.py`, `logic/ml_model.py`
- Tests: `tests/test_v77_phase2_features.py`
- Related: V7.5 Phase 2 features (F10-F12), V7.7 Phase 1 (scoring improvements)
