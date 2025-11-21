#!/usr/bin/env python3
"""
V7.7 Phase 3 Implementation Script

This script implements Phase 3 by training and activating:
1. Meta-Learner - Second-level AI combining predictions
2. Adaptive Trainer - Automatic retraining system
3. Performance Monitor - Performance tracking and alerts

Prerequisites:
- Phase 2 completed (14 features model trained)
- 100+ periods of prediction data collected

Usage:
    python scripts/v77_phase3_implement.py [--train-meta-learner] [--enable-adaptive]
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


def check_prerequisites():
    """Check if prerequisites are met."""
    print_header("CHECKING PREREQUISITES")

    try:
        from logic.phase3_data_collector import get_collector

        collector = get_collector()
        stats = collector.get_collection_stats()

        print("\n📊 Data Collection Status:")
        print("   Periods Collected: {}".format(stats['unique_periods']))
        print("   Ready for Phase 3: {}".format('✅ YES' if stats['ready_for_training'] else '❌ NO'))

        if not stats['ready_for_training']:
            print("\n⚠️  WARNING: Only {} periods collected".format(stats['unique_periods']))
            print("   Recommended: 100+ periods for reliable Meta-Learner training")
            print("   Continue anyway? (y/N): ", end='')
            response = input().strip().lower()
            if response != 'y':
                print("\n❌ Phase 3 implementation cancelled")
                return False

        collector.close()
        return True

    except Exception as e:
        print(f"\n❌ Error checking prerequisites: {e}")
        return False


def train_meta_learner():
    """Train the Meta-Learner on collected data."""
    print_header("TRAINING META-LEARNER")

    try:
        from logic.meta_learner import train_meta_learner_from_db

        print("\nTraining Meta-Learner from collected data...")
        print("This may take a few minutes...\n")

        success, message, meta_learner = train_meta_learner_from_db()

        if success:
            print(f"\n✅ {message}")

            # Show feature importance
            if meta_learner:
                print("\n📊 Feature Importance:")
                importance = meta_learner.get_feature_importance()
                sorted_features = sorted(importance.items(), key=lambda x: abs(x[1]), reverse=True)
                for i, (feature, coef) in enumerate(sorted_features[:5], 1):
                    print(f"   {i}. {feature}: {coef:+.4f}")

            return True
        else:
            print(f"\n❌ {message}")
            return False

    except Exception as e:
        print(f"\n❌ Error training Meta-Learner: {e}")
        import traceback
        traceback.print_exc()
        return False


def setup_adaptive_trainer(enable=False):
    """Setup Adaptive Trainer."""
    print_header("SETTING UP ADAPTIVE TRAINER")

    try:
        from logic.adaptive_trainer import get_adaptive_trainer

        config = {
            'ROLLING_WINDOW_SIZE': 400,
            'MIN_RETRAINING_GAP_DAYS': 7,
            'F1_DEGRADATION_THRESHOLD': 0.02,
            'FULL_RETRAIN_INTERVAL_DAYS': 30,
            'ENABLE_AUTO_RETRAIN': enable
        }

        trainer = get_adaptive_trainer(config)
        status = trainer.get_status()

        print("\n⚙️  Adaptive Trainer Configuration:")
        print("   Auto-Retrain: {}".format('✅ ENABLED' if status['enabled'] else '❌ DISABLED'))
        print("   Rolling Window: {} periods".format(status['rolling_window_size']))
        print("   Min Gap: {} days".format(status['min_gap_days']))
        print("   F1 Threshold: {:.2%}".format(status['f1_threshold']))
        print("   Full Retrain Interval: {} days".format(status['full_retrain_interval']))

        if enable:
            print("\n✅ Adaptive Trainer is ACTIVE")
            print("   The system will automatically retrain when needed")
        else:
            print("\n⚠️  Adaptive Trainer is INACTIVE")
            print("   Use --enable-adaptive flag to activate")

        return True

    except Exception as e:
        print(f"\n❌ Error setting up Adaptive Trainer: {e}")
        import traceback
        traceback.print_exc()
        return False


def setup_performance_monitor():
    """Setup Performance Monitor."""
    print_header("SETTING UP PERFORMANCE MONITOR")

    try:
        from logic.performance_monitor import get_performance_monitor

        monitor = get_performance_monitor()

        # Try to load historical data
        success, msg = monitor.load_from_database(days=30)
        if success:
            print(f"\n✅ {msg}")
        else:
            print(f"\n⚠️  {msg}")

        # Get summary
        summary = monitor.get_performance_summary()

        if summary['count'] > 0:
            print("\n📈 Performance Summary:")
            print("   Records: {}".format(summary['count']))
            print("   F1-Score Mean: {:.4f}".format(summary['f1_score']['mean']))
            print("   F1-Score Current: {:.4f}".format(summary['f1_score']['current']))
            print("   Trend: {}".format(summary['trend']))
            print("   Alerts: {}".format(summary['alerts_count']))
        else:
            print("\n📈 Performance Monitor ready (no historical data yet)")

        print("\n✅ Performance Monitor is ACTIVE")
        print("   System will track model performance and detect degradation")

        return True

    except Exception as e:
        print(f"\n❌ Error setting up Performance Monitor: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_usage_guide():
    """Show guide for using Phase 3 components."""
    print_header("PHASE 3 USAGE GUIDE")

    print("""
🎯 How to Use Phase 3 Components:

1. META-LEARNER - Enhanced Decision Making
   
   from logic.meta_learner import load_meta_learner
   
   meta_learner = load_meta_learner()
   if meta_learner:
       final_prob, decision = meta_learner.predict_final_decision(
           ai_prob=45.2,
           manual_score=7.5,
           confidence=5,
           vote_count=8,
           recent_form_score=2.0
       )
       print(f"Decision: {decision} (Probability: {final_prob:.1f}%)")

2. ADAPTIVE TRAINER - Automatic Retraining
   
   from logic.adaptive_trainer import get_adaptive_trainer
   from logic.data_repository import load_data_ai_from_db
   
   trainer = get_adaptive_trainer()
   all_data_ai, _ = load_data_ai_from_db()
   
   # Check if retrain needed and execute
   should_retrain, reason = trainer.should_retrain_incremental()
   if should_retrain:
       success, msg = trainer.incremental_retrain(all_data_ai)

3. PERFORMANCE MONITOR - Track Model Health
   
   from logic.performance_monitor import get_performance_monitor
   
   monitor = get_performance_monitor()
   
   # Record performance after predictions
   metrics = monitor.record_performance(
       date='2025-01-15',
       predictions=[1, 0, 1, ...],
       actuals=[1, 1, 0, ...]
   )
   
   # Get summary
   summary = monitor.get_performance_summary()
   print(f"F1-Score Trend: {summary['trend']}")

4. INTEGRATION - Combine All Components
   
   # In your dashboard/prediction code:
   
   # Step 1: Make predictions with Meta-Learner
   meta_learner = load_meta_learner()
   final_prob, decision = meta_learner.predict_final_decision(...)
   
   # Step 2: Check if adaptive retrain needed
   trainer = get_adaptive_trainer()
   success, msg, retrain_type = trainer.auto_retrain(all_data_ai)
   
   # Step 3: Monitor performance
   monitor = get_performance_monitor()
   monitor.record_performance(date, predictions, actuals)

For detailed documentation, see:
- DOC/V77_PHASE3_DESIGN.md - Complete architecture
- logic/meta_learner.py - Meta-Learner implementation
- logic/adaptive_trainer.py - Adaptive Trainer implementation
- logic/performance_monitor.py - Performance Monitor implementation
    """)


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description='V7.7 Phase 3 Implementation - Meta-Learner and Adaptive Training',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--train-meta-learner',
        action='store_true',
        help='Train the Meta-Learner on collected data'
    )
    parser.add_argument(
        '--enable-adaptive',
        action='store_true',
        help='Enable Adaptive Trainer for automatic retraining'
    )
    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help='Skip prerequisite checks'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("V7.7 PHASE 3 IMPLEMENTATION")
    print("Meta-Learner & Adaptive Training System")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Check prerequisites
    if not args.skip_checks:
        if not check_prerequisites():
            return 1

    success_count = 0
    total_steps = 3

    # Step 1: Train Meta-Learner (if requested)
    if args.train_meta_learner:
        if train_meta_learner():
            success_count += 1
    else:
        print_header("META-LEARNER TRAINING")
        print("\n⏭️  Skipped (use --train-meta-learner to train)")
        print("   If already trained, Meta-Learner is ready to use")

    # Step 2: Setup Adaptive Trainer
    if setup_adaptive_trainer(enable=args.enable_adaptive):
        success_count += 1

    # Step 3: Setup Performance Monitor
    if setup_performance_monitor():
        success_count += 1

    # Show usage guide
    show_usage_guide()

    # Summary
    print("\n" + "=" * 80)
    if success_count == total_steps:
        print("✅ PHASE 3 IMPLEMENTATION COMPLETE!")
    else:
        print(f"⚠️  PHASE 3 PARTIALLY COMPLETE ({success_count}/{total_steps} steps)")
    print("=" * 80)

    print("\nNext Steps:")
    print("1. Integrate Meta-Learner into your dashboard for better decisions")
    print("2. Monitor system performance regularly")
    print("3. Let Adaptive Trainer handle retraining automatically")
    print("\nFor help, see: DOC/V77_PHASE3_DESIGN.md")
    print("=" * 80)

    return 0 if success_count == total_steps else 1


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
