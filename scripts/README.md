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

## After Running Scripts

### Phase 2 Completion Checklist
- [ ] Run `v77_phase2_finalize.py` successfully
- [ ] Verify model files exist in `logic/ml_model_files/`
- [ ] Test predictions to ensure 14 features work correctly
- [ ] Begin collecting prediction data for Phase 3

### Next Steps: Phase 3 Preparation
1. **Data Collection** (3 months minimum)
   - System will automatically collect predictions to `meta_learning_history` table
   - Need minimum 100 periods before Phase 3 implementation
   
2. **Phase 3 Implementation** (after data collection)
   - Implement Meta-Learner (`logic/meta_learner.py`)
   - Implement Adaptive Trainer (`logic/adaptive_trainer.py`)
   - Setup Performance Monitoring (`logic/performance_monitor.py`)
   - See `DOC/V77_PHASE3_DESIGN.md` for detailed architecture

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
