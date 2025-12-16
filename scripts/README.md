# V7.7 Upgrade Scripts

This directory contains scripts to help execute the V7.7 upgrade plan.

## Available Scripts

### 1. v77_phase2_finalize.py

**Purpose**: Complete Phase 2 by retraining the AI model with 14 features and preparing for Phase 3.

**What it does:**
1. Creates Phase 3 database tables (`meta_learning_history`, `model_performance_log`)
2. Retrains the AI model with all 14 features (F1-F14)
3. Verifies the model is correctly saved
4. Logs training results to database

**Usage:**

```bash
# Basic retraining (faster, uses default parameters)
python scripts/v77_phase2_finalize.py

# With hyperparameter tuning (recommended for best results, but slower)
python scripts/v77_phase2_finalize.py --hyperparameter-tuning

# Skip database setup if already done
python scripts/v77_phase2_finalize.py --skip-db-setup
```

**Requirements:**
- Database must be accessible with lottery data
- Minimum 50 periods of data required for training
- For hyperparameter tuning: Recommended 100+ periods for better results

**Expected Duration:**
- Without tuning: 2-10 minutes (depending on data size)
- With tuning: 10-30 minutes (performs grid search)

**Output:**
- Updates model files: `logic/ml_model_files/loto_model.joblib` and `ai_scaler.joblib`
- Creates/updates Phase 3 database tables
- Logs training results to `model_performance_log` table

---

### 2. v77_phase3_check_progress.py

**Purpose**: Check Phase 3 data collection progress and readiness for Meta-Learner training.

**What it does:**
1. Checks database tables for Phase 3 exist
2. Reports data collection statistics
3. Shows progress toward 100-period minimum
4. Provides integration guide for data collection
5. Indicates when ready for Phase 3 implementation

**Usage:**

```bash
# Check current progress
python scripts/v77_phase3_check_progress.py
```

**Output Example:**
```
📊 Collection Statistics:
   Total Predictions Logged: 5,000
   Predictions with Outcomes: 4,500
   Unique Periods Collected: 45

📈 Progress to Phase 3 Readiness:
   Required Periods: 100
   Current Periods: 45
   Remaining: 55
[████████████████████░░░░░░░░░░░░░░] 45.0%

⏳ NOT YET READY
   Need 55 more periods of data collection
   Estimated time: 55 days (if collecting daily)
```

**When to run:**
- After Phase 2 completion
- Periodically during data collection (weekly/monthly)
- Before attempting Phase 3 implementation

---

### 3. v77_phase3_implement.py

**Purpose**: Implement Phase 3 components - Meta-Learner, Adaptive Trainer, and Performance Monitor.

**What it does:**
1. Checks if 100+ periods of data collected (prerequisite)
2. Trains Meta-Learner on historical predictions and outcomes
3. Sets up Adaptive Trainer for automatic retraining
4. Configures Performance Monitor for model health tracking
5. Provides usage guide for all Phase 3 components

**Usage:**

```bash
# Check prerequisites only (doesn't train/enable anything)
python scripts/v77_phase3_implement.py

# Train Meta-Learner and enable Adaptive Trainer
python scripts/v77_phase3_implement.py --train-meta-learner --enable-adaptive

# Train Meta-Learner only
python scripts/v77_phase3_implement.py --train-meta-learner

# Skip prerequisite checks
python scripts/v77_phase3_implement.py --skip-checks
```

**Prerequisites:**
- Phase 2 completed (14-feature model trained)
- 100+ periods of prediction data collected in `meta_learning_history` table
- Database accessible with collected data

**Expected Duration:**
- Prerequisite check: <1 minute
- Meta-Learner training: 1-5 minutes (depends on data size)
- Full setup: 2-10 minutes

**Output:**
- Creates `logic/ml_model_files/meta_learner.joblib` and `meta_scaler.joblib`
- Configures Adaptive Trainer (can enable/disable auto-retrain)
- Initializes Performance Monitor
- Provides detailed usage guide

**When to run:**
- After collecting 100+ periods of data
- When ready to activate Phase 3 features
- To retrain Meta-Learner with new data

---

## After Running Scripts

### Phase 2 Completion Checklist
- [ ] Run `v77_phase2_finalize.py` successfully
- [ ] Verify model files exist in `logic/ml_model_files/`
- [ ] Test predictions to ensure 14 features work correctly
- [ ] Begin collecting prediction data for Phase 3

### Phase 3 Completion Checklist
- [ ] Collect 100+ periods of data (check with `v77_phase3_check_progress.py`)
- [ ] Run `v77_phase3_implement.py --train-meta-learner`
- [ ] Verify Meta-Learner files exist in `logic/ml_model_files/`
- [ ] Optionally enable Adaptive Trainer with `--enable-adaptive`
- [ ] Integrate Meta-Learner into dashboard for enhanced decisions

### Next Steps: Phase 3 Usage
1. **Use Meta-Learner** for better decisions
   ```python
   from logic.meta_learner import load_meta_learner
   meta_learner = load_meta_learner()
   final_prob, decision = meta_learner.predict_final_decision(...)
   ```

2. **Monitor Performance** continuously
   ```python
   from logic.performance_monitor import get_performance_monitor
   monitor = get_performance_monitor()
   monitor.record_performance(date, predictions, actuals)
   ```

3. **Let Adaptive Trainer** handle retraining automatically
   ```python
   from logic.adaptive_trainer import get_adaptive_trainer
   trainer = get_adaptive_trainer()
   success, msg, type = trainer.auto_retrain(all_data_ai)
   ```

## Troubleshooting

### Database Connection Errors
```
Error: Could not connect to database
```
**Solution**: Ensure `config.json` has correct database path and the database file exists.

### Import Errors
```
Error: No module named 'logic'
```
**Solution**: Run script from repository root: `python scripts/v77_phase2_finalize.py`

### Insufficient Data Error
```
Error: Need at least 50 periods of data
```
**Solution**: Add more lottery result data to the database before training.

### Out of Memory Errors
```
Error: MemoryError during training
```
**Solution**: 
- Close other applications to free memory
- Try without hyperparameter tuning first
- Consider using a subset of data for testing

## Documentation References

- **Phase 2 Implementation**: `DOC/V77_PHASE2_IMPLEMENTATION.md`
- **Phase 3 Design**: `DOC/V77_PHASE3_DESIGN.md`
- **Feasibility Assessment** (Vietnamese): `DOC/V77_FEASIBILITY_ASSESSMENT_VI.md`
- **Quick Reference**: `V77_UPGRADE_SUMMARY.md`

## Support

For issues or questions:
1. Check the documentation in `DOC/` directory
2. Review error messages and traceback carefully
3. Ensure all prerequisites are met (data, dependencies, etc.)
