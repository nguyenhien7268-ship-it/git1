#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke check script for "chạm thông" enforcement (8 consecutive at end)
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
    print("Smoke Check: Chạm Thông Enforcement (8 Consecutive at End)")
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
    
    # Get configuration
    window_n = DEFAULT_SETTINGS.get('DE_WINDOW_KYS', 30)
    require_consec = DEFAULT_SETTINGS.get('CHAM_THONG_MIN_CONSEC', 8)
    print(f"✓ Using window N = {window_n}")
    print(f"✓ Minimum consecutive at end = {require_consec}")
    
    # Test 1: Calculate all combinations (no filter)
    print(f"\n{'='*80}")
    print("Test 1: All Touch Combinations (no filter)")
    print(f"{'='*80}\n")
    
    try:
        all_combos = calculate_top_touch_combinations(rows, num_touches=4, filter_cham_thong_only=False)
        
        if not all_combos:
            print("No touch combinations found")
        else:
            print(f"Found {len(all_combos)} combinations:\n")
            
            for idx, combo in enumerate(all_combos, 1):
                touches = combo['touches']
                touches_str = ','.join(map(str, sorted(touches)))
                total = combo.get('total_count', 0)
                max_consec = combo.get('max_consecutive', 0)
                consec_end = combo.get('consecutive_at_end', 0)
                covers_end = combo.get('covers_last_n_at_end', False)
                covers_full = combo.get('covers_last_n', False)
                rate = combo.get('rate_percent', 0.0)
                window = combo.get('window', window_n)
                
                print(f"{idx}. C{touches_str}")
                print(f"   Total count:           {total}/{window}")
                print(f"   Max consecutive:       {max_consec}")
                print(f"   Consecutive at end:    {consec_end} {'✓ THÔNG' if covers_end else ''}")
                print(f"   Covers last N (full):  {covers_full}")
                print(f"   Covers last N at end:  {covers_end} (requires >= {require_consec})")
                print(f"   Rate:                  {rate:.1f}%")
                print()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Filter only "chạm thông" (with consecutive at end requirement)
    print(f"{'='*80}")
    print(f"Test 2: Only 'Chạm Thông' (covers_last_n_at_end = True)")
    print(f"{'='*80}\n")
    
    try:
        thong_only = calculate_top_touch_combinations(rows, num_touches=4, filter_cham_thong_only=True)
        
        if not thong_only:
            print(f"No combinations meet the 'chạm thông' requirement (>= {require_consec} consecutive at end)")
            print("This is normal - the requirement is strict and may not always be met.")
        else:
            print(f"Found {len(thong_only)} 'chạm thông' combinations:\n")
            
            for idx, combo in enumerate(thong_only, 1):
                touches = combo['touches']
                touches_str = ','.join(map(str, sorted(touches)))
                consec_end = combo.get('consecutive_at_end', 0)
                total = combo.get('total_count', 0)
                rate = combo.get('rate_percent', 0.0)
                
                print(f"{idx}. C{touches_str}")
                print(f"   Consecutive at end:  {consec_end}/{consec_end} ✓ THÔNG")
                print(f"   Total count:         {total}/{window_n}")
                print(f"   Rate:                {rate:.1f}%")
                print()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Verification checks
    print(f"{'='*80}")
    print("Verification Checks:")
    print(f"{'='*80}\n")
    
    all_passed = True
    
    # Check 1: All combinations in Test 2 must have covers_last_n_at_end = True
    if thong_only:
        for combo in thong_only:
            if not combo.get('covers_last_n_at_end', False):
                print(f"❌ FAIL: C{','.join(map(str, combo['touches']))} in filtered list but covers_last_n_at_end=False")
                all_passed = False
        if all_passed:
            print(f"✓ PASS: All {len(thong_only)} filtered combinations have covers_last_n_at_end=True")
    
    # Check 2: All filtered combinations must have consecutive_at_end >= require_consec
    if thong_only:
        for combo in thong_only:
            consec = combo.get('consecutive_at_end', 0)
            if consec < require_consec:
                print(f"❌ FAIL: C{','.join(map(str, combo['touches']))} has consecutive_at_end={consec} < {require_consec}")
                all_passed = False
        if all_passed:
            print(f"✓ PASS: All filtered combinations have consecutive_at_end >= {require_consec}")
    
    # Check 3: Any combination with consecutive_at_end >= require_consec should have covers_last_n_at_end = True
    if all_combos:
        for combo in all_combos:
            consec = combo.get('consecutive_at_end', 0)
            covers_end = combo.get('covers_last_n_at_end', False)
            touches_str = ','.join(map(str, combo['touches']))
            
            if consec >= require_consec and not covers_end:
                print(f"❌ FAIL: C{touches_str} has consecutive_at_end={consec} >= {require_consec} but covers_last_n_at_end=False")
                all_passed = False
            elif consec < require_consec and covers_end:
                print(f"❌ FAIL: C{touches_str} has consecutive_at_end={consec} < {require_consec} but covers_last_n_at_end=True")
                all_passed = False
        
        if all_passed:
            print(f"✓ PASS: Logic consistency verified (consecutive_at_end <=> covers_last_n_at_end)")
    
    print()
    if all_passed:
        print(f"{'='*80}")
        print("✓ ALL CHECKS PASSED")
        print(f"{'='*80}")
    else:
        print(f"{'='*80}")
        print("❌ SOME CHECKS FAILED")
        print(f"{'='*80}")

if __name__ == '__main__':
    main()
