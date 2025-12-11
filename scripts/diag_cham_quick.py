#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick diagnostic script for chạm-count reproduction
Purpose: Diagnose incorrect "chạm thống" counting in Tab Soi Cầu Đề
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from logic.data_repository import load_data_ai_from_db, DB_NAME, get_managed_bridges_with_prediction
    from logic.de_utils import get_touches_by_offset
    from logic.data_repository import _extract_digit_from_col
except ImportError as e:
    print(f"FATAL: Import error - {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def main():
    print("=" * 80)
    print("Diagnostic: Chạm Count Issue - DE_DYN Bridges")
    print("=" * 80)
    
    # 1. Load data
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
    
    # 2. Set window
    N = 30  # Default window for DE bridges
    print(f"✓ Using window N = {N} (last {N} rows)")
    
    # 3. Get DE_DYN bridges
    try:
        all_bridges = get_managed_bridges_with_prediction(DB_NAME, current_data=rows, only_enabled=False)
        de_dyn_bridges = [b for b in all_bridges if b['name'].startswith('DE_DYN_')]
        print(f"✓ Found {len(de_dyn_bridges)} DE_DYN bridges")
    except Exception as e:
        print(f"ERROR getting bridges: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Analyze first 50 (or all if < 50)
    sample_size = min(50, len(de_dyn_bridges))
    print(f"\n{'='*80}")
    print(f"Analyzing first {sample_size} DE_DYN bridges:")
    print(f"{'='*80}\n")
    
    for idx, bridge in enumerate(de_dyn_bridges[:sample_size], 1):
        try:
            bridge_name = bridge['name']
            
            # Parse bridge name: DE_DYN_G1_G2_K3
            parts = bridge_name.split('_')
            if len(parts) < 5:
                print(f"{idx}. {bridge_name}: SKIP (invalid format)")
                continue
            
            col1, col2, k_str = parts[2], parts[3], parts[4]
            k_val = int(k_str.replace('K', ''))
            
            # Get last N rows
            last_n_rows = rows[-N:] if len(rows) >= N else rows
            
            # Compute base value for last row (to get touches)
            last_row = rows[-1]
            d1 = _extract_digit_from_col(last_row, col1)
            d2 = _extract_digit_from_col(last_row, col2)
            
            if d1 is None or d2 is None:
                print(f"{idx}. {bridge_name}: SKIP (cannot extract digits)")
                continue
            
            base_sum = (d1 + d2) % 10
            
            # Get touches
            touches_raw = get_touches_by_offset(base_sum, k_val)
            # Normalize to ints
            touches = [int(t) if isinstance(t, str) else t for t in touches_raw]
            
            # Count occurrences in last N rows
            count = 0
            occur_kys = []
            
            for row in last_n_rows:
                # Compute the value for this row (same logic as UI)
                d1_row = _extract_digit_from_col(row, col1)
                d2_row = _extract_digit_from_col(row, col2)
                
                if d1_row is None or d2_row is None:
                    continue
                
                row_value = (d1_row + d2_row) % 10
                
                # Check if row_value is in touches
                if row_value in touches:
                    count += 1
                    ky = str(row[0]) if len(row) > 0 else "?"
                    occur_kys.append(ky)
            
            # Print summary
            touches_str = ','.join(map(str, sorted(set(touches))))
            sample_kys = occur_kys[:10]
            sample_kys_str = ','.join(sample_kys)
            
            print(f"{idx}. {bridge_name}")
            print(f"    Touches: {touches_str}")
            print(f"    Computed count: {count}/{N}")
            print(f"    Sample occur kys: {sample_kys_str}")
            
        except Exception as e:
            print(f"{idx}. {bridge_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("Diagnostic complete")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
