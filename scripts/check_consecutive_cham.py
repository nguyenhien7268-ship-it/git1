#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke check script for consecutive coverage (covers_last_n) implementation
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from logic.data_repository import load_data_ai_from_db, DB_NAME
    from logic.de_analytics import calculate_top_touch_combinations, compute_touch_metrics
    from logic.constants import DEFAULT_SETTINGS
except ImportError as e:
    print(f"FATAL: Import error - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def main():
    print("=" * 80)
    print("Smoke Check: Consecutive Coverage (covers_last_n) Implementation")
    print("=" * 80)
    
    # Load data
    try:
        rows, msg = load_data_ai_from_db(DB_NAME)
        if not rows:
            print(f"ERROR: Failed to load data - {msg}")
            return
        print(f"✓ Loaded {len(rows)} rows from database")
    except Exception as e:
        print(f"ERROR loading data: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Get window size
    window_n = DEFAULT_SETTINGS.get('DE_WINDOW_KYS', 30)
    print(f"✓ Using window N = {window_n}")
    
    # Calculate top touch combinations
    print(f"\n{'='*80}")
    print("Top Touch Combinations with Consecutive Coverage Metrics:")
    print(f"{'='*80}\n")
    
    try:
        top_combos = calculate_top_touch_combinations(rows, num_touches=4, days=window_n)
        
        if not top_combos:
            print("No touch combinations found (may need more data or lower thresholds)")
            return
        
        print(f"Found {len(top_combos)} top combinations:\n")
        
        for idx, combo in enumerate(top_combos, 1):
            touches = combo['touches']
            touches_str = ','.join(map(str, sorted(touches)))
            total = combo.get('total_count', 0)
            max_consec = combo.get('max_consecutive', 0)
            covers = combo.get('covers_last_n', False)
            rate = combo.get('rate_percent', 0.0)
            window = combo.get('window', window_n)
            occur_kys = combo.get('occur_kys', [])
            
            print(f"{idx}. C{touches_str}")
            print(f"   Total count:      {total}/{window}")
            print(f"   Max consecutive:  {max_consec}")
            print(f"   Covers last N:    {covers} {'✓ THÔNG' if covers else ''}")
            print(f"   Rate:             {rate:.1f}%")
            print(f"   Sample kys:       {','.join(occur_kys[:10])}")
            print()
        
        # Verify assertions
        print(f"{'='*80}")
        print("Verification Checks:")
        print(f"{'='*80}\n")
        
        all_passed = True
        for combo in top_combos:
            total = combo.get('total_count', 0)
            covers = combo.get('covers_last_n', False)
            window = combo.get('window', window_n)
            touches_str = ','.join(map(str, sorted(combo['touches'])))
            
            # Check: if covers_last_n is True, total_count must equal window
            if covers and total != window:
                print(f"❌ FAIL: C{touches_str} - covers_last_n=True but total_count ({total}) != window ({window})")
                all_passed = False
            elif covers:
                print(f"✓ PASS: C{touches_str} - covers_last_n=True and total_count={total} equals window={window}")
            else:
                print(f"✓ PASS: C{touches_str} - covers_last_n=False (partial coverage: {total}/{window})")
        
        if all_passed:
            print(f"\n{'='*80}")
            print("✓ ALL CHECKS PASSED")
            print(f"{'='*80}")
        else:
            print(f"\n{'='*80}")
            print("❌ SOME CHECKS FAILED")
            print(f"{'='*80}")
            
    except Exception as e:
        print(f"ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
