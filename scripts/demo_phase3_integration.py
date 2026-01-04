#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 3 Integration Proof of Concept
Demonstrates how to integrate phase3_data_collector into the dashboard workflow.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def demo_prediction_logging():
    """
    Demonstrate prediction logging workflow.
    This mimics what should happen in the real dashboard.
    """
    print("=" * 60)
    print("PHASE 3 INTEGRATION DEMO")
    print("=" * 60)
    
    from logic.phase3_data_collector import get_collector, log_prediction
    
    # Simulate dashboard analysis for period "20001"
    next_ky = "20001"
    
    print(f"\n[STEP 1] Simulating Dashboard Analysis for period {next_ky}...")
    
    # Example predictions (this would come from real dashboard logic)
    predictions = [
        {
            'loto': '00',
            'ai_probability': 65.5,
            'manual_score': 8.2,
            'confidence': 6,
            'vote_count': 12,
            'recent_form_score': 2.5
        },
        {
            'loto': '15',
            'ai_probability': 72.3,
            'manual_score': 9.1,
            'confidence': 7,
            'vote_count': 15,
            'recent_form_score': 3.0
        },
        {
            'loto': '27',
            'ai_probability': 58.0,
            'manual_score': 7.0,
            'confidence': 5,
            'vote_count': 8,
            'recent_form_score': 1.5
        },
    ]
    
    # Log all predictions
    print(f"\n[STEP 2] Logging {len(predictions)} predictions...")
    collector = get_collector()
    success_count, total = collector.log_batch_predictions(next_ky, predictions)
    
    print(f"   Logged: {success_count}/{total} predictions")
    
    # Simulate actual results coming in later
    print(f"\n[STEP 3] Simulating actual results for period {next_ky}...")
    actual_results = ['00', '15', '42', '73']  # Lotos that actually appeared
    print(f"   Actual lotos: {actual_results}")
    
    # Log outcomes
    print(f"\n[STEP 4] Logging outcomes...")
    outcomes_logged = collector.log_batch_outcomes(next_ky, actual_results)
    print(f"   Updated: {outcomes_logged} predictions with outcomes")
    
    # Check stats
    print(f"\n[STEP 5] Checking collection stats...")
    stats = collector.get_collection_stats()
    
    print(f"\n   Total Predictions: {stats['total_predictions']}")
    print(f"   With Outcomes: {stats['predictions_with_outcomes']}")
    print(f"   Unique Periods: {stats['unique_periods']}")
    print(f"   Progress: {stats['progress_percentage']:.1f}%")
    
    collector.close()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    
    print("\n[INTEGRATION GUIDE]")
    print("To integrate into real code, add this to:")
    print("  1. services/AnalysisService.prepare_dashboard_data()")
    print("     OR")
    print("  2. app_controller.py task_run_decision_dashboard()")
    print("\nExample:")
    print("""
    # After generating predictions:
    from logic.phase3_data_collector import log_prediction
    
    for loto, pred_data in predictions.items():
        log_prediction(
            ky=next_ky,
            loto=loto,
            ai_probability=pred_data['ai_prob'],
            manual_score=pred_data['manual_score'],
            confidence=pred_data['confidence'],
            vote_count=pred_data['vote_count'],
            recent_form_score=pred_data.get('form_score', 0.0)
        )
    
    # When importing new data with actual results:
    from logic.phase3_data_collector import log_batch_outcomes
    
    actual_lotos = extract_lotos_from_new_data(ky)
    log_batch_outcomes(ky, actual_lotos)
    """)


if __name__ == '__main__':
    try:
        demo_prediction_logging()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
