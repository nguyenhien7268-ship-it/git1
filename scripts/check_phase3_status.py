#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check Phase 3 Data Collection Status
This script checks the current status of Phase 3 meta-learning data collection.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from logic.phase3_data_collector import get_collector
    
    print("=" * 60)
    print("PHASE 3 DATA COLLECTION STATUS")
    print("=" * 60)
    
    collector = get_collector()
    stats = collector.get_collection_stats()
    
    print(f"\nTotal Predictions Logged: {stats['total_predictions']}")
    print(f"Predictions with Outcomes: {stats['predictions_with_outcomes']}")
    print(f"Unique Periods: {stats['unique_periods']}")
    print(f"Oldest Period: {stats['oldest_period']}")
    print(f"Newest Period: {stats['newest_period']}")
    print(f"\nProgress: {stats['progress_percentage']:.1f}%")
    print(f"Ready for Training: {'YES' if stats['ready_for_training'] else 'NO (need 100+ periods)'}")
    
    if stats['unique_periods'] > 0:
        avg_predictions_per_period = stats['predictions_with_outcomes'] / stats['unique_periods']
        print(f"\nAverage Predictions per Period: {avg_predictions_per_period:.1f}")
    
    print("\n" + "=" * 60)
    
    if not stats['ready_for_training']:
        remaining = 100 - stats['unique_periods']
        print(f"\nNeed {remaining} more periods to activate Meta-Learner.")
        print("Tip: Run the dashboard analysis regularly to collect data.")
    else:
        print("\nSUCCESS! Meta-Learner can now be trained.")
        print("Next step: Run the Meta-Learner training script.")
    
    collector.close()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
