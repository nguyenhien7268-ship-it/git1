#!/usr/bin/env python3
"""
V7.7 Phase 2 Finalization Script

This script completes Phase 2 by:
1. Retraining the AI model with 14 features (F1-F14)
2. Creating the database table for Phase 3 data collection
3. Validating the model training

Usage:
    python scripts/v77_phase2_finalize.py [--hyperparameter-tuning]

Options:
    --hyperparameter-tuning    Enable hyperparameter tuning during retraining (recommended)
                               This will take longer but optimize the model parameters.
"""

import sys
import os
import argparse
from datetime import datetime
# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def create_phase3_database_table():
    """
    Create the meta_learning_history table for Phase 3 data collection.
    This table will store predictions alongside actual outcomes for training the meta-learner.
    """
    print("\n" + "=" * 80)
    print("Step 1: Creating Phase 3 Database Table")
    print("=" * 80)
    
    try:
        import sqlite3
        from logic.db_manager import DB_NAME
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Create meta_learning_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meta_learning_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ky TEXT NOT NULL,
                loto TEXT NOT NULL,
                ai_probability REAL,
                manual_score REAL,
                confidence INTEGER,
                vote_count INTEGER,
                recent_form_score REAL,
                actual_outcome INTEGER,
                decision_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ky, loto)
            )
        """)
        
        # Create model_performance_log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_performance_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_date DATE NOT NULL,
                model_version TEXT,
                f1_score REAL,
                accuracy REAL,
                training_type TEXT,
                training_duration_seconds INTEGER,
                notes TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Phase 3 database tables created successfully!")
        print("   - meta_learning_history: For storing predictions and outcomes")
        print("   - model_performance_log: For tracking model performance over time")
        return True
        
    except Exception as e:
        print(f"❌ Error creating Phase 3 tables: {e}")
        import traceback
        traceback.print_exc()
        return False


def retrain_model_with_14_features(use_hyperparameter_tuning=False):
    """
    Retrain the AI model with all 14 features (including new F13 and F14).
    
    Args:
        use_hyperparameter_tuning: If True, performs grid search for optimal hyperparameters
    """
    print("\n" + "=" * 80)
    print("Step 2: Retraining AI Model with 14 Features")
    print("=" * 80)
    print(f"Hyperparameter Tuning: {'ENABLED' if use_hyperparameter_tuning else 'DISABLED'}")
    print()
    
    try:
        from logic.data_repository import load_data_ai_from_db
        from logic.ai_feature_extractor import _get_daily_bridge_predictions
        from logic.ml_model import train_ai_model
        
        # Load data
        print("Loading lottery data from database...")
        all_data_ai, msg = load_data_ai_from_db()
        if all_data_ai is None:
            print(f"❌ Error loading data: {msg}")
            return False
        print(f"✅ Loaded {len(all_data_ai)} periods of data")
        
        # Extract features
        print("\nExtracting features for all periods (including F13 and F14)...")
        print("This may take several minutes for large datasets...")
        daily_bridge_predictions = _get_daily_bridge_predictions(all_data_ai)
        print(f"✅ Feature extraction complete for {len(daily_bridge_predictions)} periods")
        
        # Train model
        print("\nTraining AI model with 14 features...")
        if use_hyperparameter_tuning:
            print("⚠️  Hyperparameter tuning is enabled - this will take longer but find optimal parameters")
        
        start_time = datetime.now()
        success, result_msg = train_ai_model(
            all_data_ai,
            daily_bridge_predictions,
            use_hyperparameter_tuning=use_hyperparameter_tuning
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if success:
            print(f"\n✅ {result_msg}")
            print(f"⏱️  Training completed in {duration:.1f} seconds ({duration / 60:.1f} minutes)")
            
            # Log to database
            try:
                from logic.db_manager import get_db_connection
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO model_performance_log
                    (log_date, model_version, training_type, training_duration_seconds, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    datetime.now().date(),
                    'V7.7-Phase2-14Features',
                    'full_with_tuning' if use_hyperparameter_tuning else 'full',
                    int(duration),
                    result_msg
                ))
                conn.commit()
                conn.close()
                print("✅ Training log saved to database")
            except Exception as log_error:
                print(f"⚠️  Could not log training to database: {log_error}")
            
            return True
        else:
            print(f"\n❌ Training failed: {result_msg}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error during model training: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_model():
    """
    Verify that the model is correctly saved and can be loaded.
    """
    print("\n" + "=" * 80)
    print("Step 3: Verifying Model")
    print("=" * 80)
    
    try:
        import os
        from logic.ml_model import MODEL_FILE_PATH, SCALER_FILE_PATH
        
        # Check if model files exist
        if not os.path.exists(MODEL_FILE_PATH):
            print(f"❌ Model file not found: {MODEL_FILE_PATH}")
            return False
        
        if not os.path.exists(SCALER_FILE_PATH):
            print(f"❌ Scaler file not found: {SCALER_FILE_PATH}")
            return False
        
        print(f"✅ Model file exists: {MODEL_FILE_PATH}")
        print(f"✅ Scaler file exists: {SCALER_FILE_PATH}")
        
        # Try to load the model
        import joblib
        joblib.load(MODEL_FILE_PATH)  # Verify model can be loaded
        scaler = joblib.load(SCALER_FILE_PATH)
        
        # Check feature count
        if hasattr(scaler, 'n_features_in_'):
            n_features = scaler.n_features_in_
            print(f"✅ Model expects {n_features} features")
            if n_features == 14:
                print("✅ Correct! Model is configured for 14 features (F1-F14)")
            else:
                print(f"⚠️  Warning: Expected 14 features but model has {n_features}")
        
        print("\n✅ Model verification successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error verifying model: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='V7.7 Phase 2 Finalization - Retrain model with 14 features',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic retraining (faster, uses default parameters)
  python scripts/v77_phase2_finalize.py
  
  # With hyperparameter tuning (recommended, but slower)
  python scripts/v77_phase2_finalize.py --hyperparameter-tuning
        """
    )
    parser.add_argument(
        '--hyperparameter-tuning',
        action='store_true',
        help='Enable hyperparameter tuning (recommended for best results)'
    )
    parser.add_argument(
        '--skip-db-setup',
        action='store_true',
        help='Skip database table creation (if already done)'
    )
    
    args = parser.parse_args()

    print("=" * 80)
    print("V7.7 PHASE 2 FINALIZATION")
    print("=" * 80)
    print("This script will:")
    print("1. Create Phase 3 database tables (if not skipped)")
    print("2. Retrain AI model with 14 features (F1-F14)")
    print("3. Verify the model is correctly saved")
    print("=" * 80)
    
    # Step 1: Create Phase 3 database tables
    if not args.skip_db_setup:
        if not create_phase3_database_table():
            print("\n⚠️  Database setup failed, but continuing with training...")
    else:
        print("\n⏭️  Skipping database setup (--skip-db-setup)")
    
    # Step 2: Retrain model
    if not retrain_model_with_14_features(use_hyperparameter_tuning=args.hyperparameter_tuning):
        print("\n❌ Phase 2 finalization FAILED")
        print("Please check the error messages above and try again.")
        return 1
    
    # Step 3: Verify model
    if not verify_model():
        print("\n⚠️  Model verification failed, but training completed")
        print("Please manually verify the model files exist and are correct.")
    
    print("\n" + "=" * 80)
    print("✅ PHASE 2 FINALIZATION COMPLETE!")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. Test the model with predictions to ensure 14 features work correctly")
    print("2. Begin collecting prediction data for Phase 3 Meta-Learner")
    print("3. After collecting 100+ periods, proceed with Phase 3 implementation")
    print("\nFor Phase 3 details, see: DOC/V77_PHASE3_DESIGN.md")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
