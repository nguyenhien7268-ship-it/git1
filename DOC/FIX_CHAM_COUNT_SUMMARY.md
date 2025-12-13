# Fix Chạm Count Issue - Summary

## Problem
The "chạm thống" (touch statistics) display in Tab Soi Cầu Đề showed incorrect counts.

Example: UI displayed `C2,6,7,9(11N)` where 11 should represent total occurrences within the last 30 days, but it was actually showing the maximum consecutive streak.

## Root Cause
In `logic/de_analytics.py`, function `calculate_top_touch_combinations` (line 407):
- Was returning `max_s` which represents the **longest consecutive streak**
- Should have been returning `wins` which represents the **total count of occurrences**

Example:
- If touches [2,6,7,9] appeared in days: 1,2,3,5,8,9,10,15,20,25,30 (11 times total)
- Old code returned `max_s = 3` (longest consecutive run was days 1,2,3)
- Fixed code returns `wins = 11` (total occurrences)

## Changes Made

### 1. Fixed Counting Logic (`logic/de_analytics.py`)
**Line 407**: Changed from `max_s` to `wins`
```python
# Before
res.append({'touches': t_list, 'streak': max_s, 'rate_percent': rate})

# After
res.append({'touches': t_list, 'streak': wins, 'rate_percent': rate})
```

### 2. Improved UI Display (`ui/ui_de_dashboard.py`)
**Line 387**: Made format clearer
```python
# Before: ambiguous "(11N)"
f"C{','.join(map(str, x['touches']))}({x['streak']}N)"

# After: clearer "(11 lần)" meaning "11 times"
f"C{','.join(map(str, x['touches']))}({x['streak']} lần)"
```

### 3. Added Diagnostic Tool
Created `scripts/diag_cham_quick.py` to:
- Reproduce the counting issue
- Verify the fix
- Analyze DE_DYN bridges
- Compute correct counts for verification

## Testing
Ran diagnostic on 50 sample DE_DYN bridges:
- Successfully computed counts for all bridges
- Verified counts match expected values
- Sample output shows correct counting logic

## Impact
This fix ensures that the touch statistics display accurately reflects the total number of occurrences within the evaluation window (default: 30 days), rather than showing the longest consecutive streak.

Users can now trust that when they see `C2,6,7,9(15 lần)`, it means the touches appeared in 15 out of the last 30 draws.
