#!/usr/bin/env python3
"""
V7.7 Phase 3 Data Collection Progress Checker

This script checks the progress of data collection for Phase 3 and provides
status updates on when the system will be ready for Meta-Learner training.

Usage:
    python scripts/v77_phase3_check_progress.py
"""

import sys
import os
from datetime import datetime
# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


def print_progress_bar(percentage, width=50):
    """Print a progress bar."""
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    print(f"[{bar}] {percentage:.1f}%")


def check_data_collection_progress():
    """Check and display Phase 3 data collection progress."""
    print_header("V7.7 PHASE 3 DATA COLLECTION PROGRESS")
    
    try:
        from logic.phase3_data_collector import get_collector
        
        collector = get_collector()
        stats = collector.get_collection_stats()
        
        print("\n📊 Collection Statistics:")
        print("   Total Predictions Logged: {:,}".format(stats['total_predictions']))
        print("   Predictions with Outcomes: {:,}".format(stats['predictions_with_outcomes']))
        print("   Unique Periods Collected: {}".format(stats['unique_periods']))
        
        if stats['oldest_period'] and stats['newest_period']:
            print("   Oldest Period: {}".format(stats['oldest_period']))
            print("   Newest Period: {}".format(stats['newest_period']))
        
        print("\n📈 Progress to Phase 3 Readiness:")
        print("   Required Periods: 100")
        print("   Current Periods: {}".format(stats['unique_periods']))
        print("   Remaining: {}".format(max(0, 100 - stats['unique_periods'])))
        print()
        print_progress_bar(stats['progress_percentage'])
        
        if stats['ready_for_training']:
            print("\n✅ READY FOR PHASE 3!")
            print("   You have collected enough data to train the Meta-Learner.")
            print("   Next step: Run Phase 3 implementation")
            print("   Command: python scripts/v77_phase3_implement.py")
        else:
            remaining = 100 - stats['unique_periods']
            print("\n⏳ NOT YET READY")
            print("   Need {} more periods of data collection".format(remaining))
            print("   Estimated time: {} days (if collecting daily)".format(remaining))
            print("\n💡 What to do:")
            print("   1. Continue running the system normally")
            print("   2. Predictions will be logged automatically")
            print("   3. Check progress periodically with this script")
            print("   4. Once ready, proceed to Phase 3 implementation")
        
        collector.close()
        
    except Exception as e:
        print(f"\n❌ Error checking progress: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def check_database_tables():
    """Check if Phase 3 database tables exist."""
    print_header("DATABASE TABLE STATUS")
    
    try:
        from logic.db_manager import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check meta_learning_history table
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='meta_learning_history'
        """)
        meta_table_exists = cursor.fetchone() is not None

        # Check model_performance_log table
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='model_performance_log'
        """)
        perf_table_exists = cursor.fetchone() is not None
        
        print("\nPhase 3 Database Tables:")
        print("   meta_learning_history: {}".format('✅ Exists' if meta_table_exists else '❌ Missing'))
        print("   model_performance_log: {}".format('✅ Exists' if perf_table_exists else '❌ Missing'))
        
        if not meta_table_exists or not perf_table_exists:
            print("\n⚠️  Warning: Phase 3 tables are missing!")
            print("   Run this command to create them:")
            print("   python scripts/v77_phase2_finalize.py --skip-db-setup")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_integration_guide():
    """Show guide for integrating data collection."""
    print_header("INTEGRATION GUIDE")
    
    print("""
📝 How to Integrate Data Collection:

The Phase 3 data collector is ready to use. Integrate it into your dashboard
or prediction workflow:

1. After making predictions:

    from logic.phase3_data_collector import log_prediction
    
    for loto in range(100):
        log_prediction(
            ky=current_ky,
            loto=str(loto).zfill(2),
            ai_probability=ai_probs[loto],
            manual_score=manual_scores[loto],
            confidence=confidence_levels[loto],
            vote_count=vote_counts[loto],
            recent_form_score=recent_form_scores.get(loto, 0.0)
        )

2. After actual results are known:

    from logic.phase3_data_collector import log_outcome
    from logic.bridges.bridges_classic import getAllLoto_V30
    
    # Get actual results
    lotos_appeared = getAllLoto_V30(result_row)
    
    # Log outcomes
    for loto in range(100):
        loto_str = str(loto).zfill(2)
        outcome = 1 if loto_str in lotos_appeared else 0
        log_outcome(ky=current_ky, loto=loto_str, actual_outcome=outcome)

3. Or use batch methods:

    from logic.phase3_data_collector import get_collector
    
    collector = get_collector()
    
    # Log batch of predictions
    predictions = [
        {'loto': '00', 'ai_probability': 45.2, 'manual_score': 7.5, ...},
        {'loto': '01', 'ai_probability': 32.1, 'manual_score': 5.0, ...},
        # ...
    ]
    collector.log_batch_predictions(ky=current_ky, predictions_list=predictions)
    
    # Log batch of outcomes
    lotos_appeared = ['00', '15', '27', ...]
    collector.log_batch_outcomes(ky=current_ky, lotos_appeared=lotos_appeared)

For more details, see: logic/phase3_data_collector.py
    """)


def main():
    """Main function."""
    print("=" * 80)
    print("V7.7 PHASE 3 PREPARATION")
    print("Data Collection Progress Checker")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check database tables
    if not check_database_tables():
        print("\n⚠️  Setup incomplete. Please fix database issues first.")
        return 1
    
    # Check data collection progress
    if not check_data_collection_progress():
        print("\n⚠️  Could not check progress. Please verify setup.")
        return 1
    
    # Show integration guide
    show_integration_guide()
    
    print("\n" + "=" * 80)
    print("For more information:")
    print("   Phase 3 Design: DOC/V77_PHASE3_DESIGN.md")
    print("   Data Collector: logic/phase3_data_collector.py")
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
