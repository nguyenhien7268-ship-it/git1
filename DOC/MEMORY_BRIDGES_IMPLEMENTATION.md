# "756 Cầu Bạc Nhớ" Implementation Documentation

## Overview

This document describes the complete implementation of the "756 Cầu Bạc Nhớ" (Memory Bridges) system, which adds support for 756 new bridge calculation algorithms based on memory (Bạc Nhớ) formulas.

## Project Structure

The implementation is organized in 3 main phases:

### Phase 1: Core Backtester Upgrade ⚙️
**File:** `logic/backtester_core.py`

Updated the core backtesting functions to support Memory Bridges alongside existing V17 bridges.

**Changes:**
1. Added `import re` at module level for bridge name parsing
2. Updated `BACKTEST_MANAGED_BRIDGES_N1()` function
3. Updated `BACKTEST_MANAGED_BRIDGES_K2N()` function

**Detection Logic:**
- Memory Bridges are identified by: `pos1_idx == -1 and pos2_idx == -1`
- V17 Bridges have: `pos1_idx >= 0 and pos2_idx >= 0`

**Bridge Name Parsing:**
Memory bridge names follow these formats:
- **Tổng (Sum):** `Tổng(00+01)`, `Tổng(05+10)`, `Tổng(26+26)`
- **Hiệu (Difference):** `Hiệu(00-01)`, `Hiệu(05-10)`, `Hiệu(26-26)`

Regex patterns:
```python
# For Tổng bridges
pattern = r'Tổng\((\d+)\+(\d+)\)'

# For Hiệu bridges
pattern = r'Hiệu\((\d+)-(\d+)\)'
```

**Algorithm Selection:**
```python
if pos1_idx == -1 and pos2_idx == -1:
    # Memory Bridge - parse name and use calculate_bridge_stl
    if "Tổng(" in bridge_name:
        pred = calculate_bridge_stl(loto1, loto2, "sum")
    elif "Hiệu(" in bridge_name:
        pred = calculate_bridge_stl(loto1, loto2, "diff")
else:
    # V17 Bridge - use existing logic
    pred = taoSTL_V30_Bong(a, b)
```

### Phase 2: Data Generator 🔧
**File:** `logic/bridges/bridge_manager_core.py`

Created function to generate all 756 Memory Bridges and insert them into the database.

**Function:** `init_all_756_memory_bridges_to_db(db_name, progress_callback)`

**Generation Logic:**
```python
for i in range(27):      # 27 positions (00-26)
    for j in range(i, 27):  # j >= i to avoid duplicates
        # Generate Tổng bridge
        bridge_name_sum = f"Tổng({i:02d}+{j:02d})"
        
        # Generate Hiệu bridge
        bridge_name_diff = f"Hiệu({i:02d}-{j:02d})"
```

**Total Bridges:** 27 × 28 / 2 = 378 combinations × 2 types = 756 bridges

**Database Fields:**
- `name`: e.g., "Tổng(00+01)" or "Hiệu(00-01)"
- `description`: Same as name
- `pos1_idx`: -1 (marks as Memory Bridge)
- `pos2_idx`: -1 (marks as Memory Bridge)
- `is_enabled`: 0 (disabled by default)
- `win_rate_text`: "N/A"

**Features:**
- Progress callback support for UI updates (every 50 bridges)
- Duplicate detection (skips existing bridges)
- Returns statistics: (success, message, added_count, skipped_count)

### Phase 3: UI Integration 🖥️
**File:** `ui/ui_settings.py`

Added UI button and handler to load 756 Memory Bridges into the database.

**Components:**
1. **Button:** "Nạp 756 Cầu Bạc Nhớ"
2. **Confirmation Dialog**
3. **Progress Window**
4. **Success/Error Notifications**

**Handler Function:** `load_756_memory_bridges()`

**User Flow:**
1. User clicks "Nạp 756 Cầu Bạc Nhớ" button
2. Confirmation dialog explains behavior and asks for confirmation
3. If confirmed, progress window appears with animated progress bar
4. Function runs in separate thread to keep UI responsive
5. Progress updates every 50 bridges (350/756, etc.)
6. Success/error notification shows final statistics

**Threading Implementation:**
```python
import_thread = threading.Thread(target=do_import)
import_thread.start()

# Keep UI responsive while thread runs
while import_thread.is_alive():
    progress_window.update()
    import_thread.join(timeout=0.1)
```

## Bridge Calculation Formulas

Memory Bridges use the `calculate_bridge_stl()` function from `logic/bridges/bridges_memory.py`:

### Tổng (Sum) Algorithm:
```python
btl = (loto1 + loto2) % 100
```

### Hiệu (Difference) Algorithm:
```python
btl = abs(loto1 - loto2)
```

### STL Generation:
- If result is a double (e.g., 11, 22): Use `taoSTL_V30_Bong()` to get shadow pair
- Otherwise: Return [number, reversed] (e.g., 12 → ["12", "21"])

## Database Schema

**Table:** `ManagedBridges`

Relevant columns:
- `id` (INTEGER PRIMARY KEY)
- `name` (TEXT UNIQUE) - Bridge name
- `pos1_idx` (INTEGER) - Position 1 index (-1 for Memory Bridges)
- `pos2_idx` (INTEGER) - Position 2 index (-1 for Memory Bridges)
- `is_enabled` (INTEGER) - 0=disabled, 1=enabled
- `win_rate_text` (TEXT) - Cached win rate
- `description` (TEXT) - Bridge description

## Testing

### Test Coverage
**Total Tests:** 78 (68 existing + 10 new)

**New Tests:** `tests/test_memory_bridges.py`
1. `test_init_all_756_memory_bridges_creates_correct_count` - Verifies 756 bridges
2. `test_init_all_756_memory_bridges_creates_correct_format` - Validates format
3. `test_init_all_756_memory_bridges_default_disabled` - Checks is_enabled=0
4. `test_init_all_756_memory_bridges_skips_duplicates` - Tests idempotency
5. `test_memory_bridge_parser_tong` - Tests Tổng regex parser
6. `test_memory_bridge_parser_hieu` - Tests Hiệu regex parser
7. `test_calculate_bridge_stl_imported` - Validates import
8. `test_memory_bridge_detection_logic` - Tests detection logic
9. `test_full_integration_memory_bridge_in_database` - End-to-end test
10. `test_progress_callback_is_called` - Validates callback

### Test Results
```
======================== 78 passed, 3 skipped in 5.91s =========================
```

All tests pass, including:
- All 68 existing tests (no regressions)
- All 10 new Memory Bridge tests

### Code Quality
- **Linting:** All files pass flake8 with `--max-line-length=100`
- **Security:** CodeQL scan found 0 alerts
- **Code Review:** All comments addressed

## Usage Instructions

### For Users

1. **Loading Memory Bridges:**
   - Open Settings window
   - Click "Nạp 756 Cầu Bạc Nhớ" button
   - Confirm the operation
   - Wait for progress bar to complete

2. **Enabling Memory Bridges:**
   - Go to "Quản Lý Cầu" (Bridge Management)
   - Find bridges with names like "Tổng(00+01)" or "Hiệu(00-01)"
   - Enable desired bridges manually

3. **Running Backtest:**
   - Select "Cầu Đã Lưu N1" or "Cầu Đã Lưu K2N" mode
   - Enabled Memory Bridges will be included automatically
   - Results will show predictions using Memory Bridge formulas

### For Developers

**Detecting Memory Bridges:**
```python
if bridge["pos1_idx"] == -1 and bridge["pos2_idx"] == -1:
    # This is a Memory Bridge
    # Parse name and use calculate_bridge_stl()
```

**Parsing Bridge Names:**
```python
import re

# For Tổng bridges
match = re.search(r'Tổng\((\d+)\+(\d+)\)', bridge_name)
if match:
    pos1 = int(match.group(1))
    pos2 = int(match.group(2))

# For Hiệu bridges
match = re.search(r'Hiệu\((\d+)-(\d+)\)', bridge_name)
if match:
    pos1 = int(match.group(1))
    pos2 = int(match.group(2))
```

**Using Memory Bridge Calculation:**
```python
from logic.bridges.bridges_memory import (
    calculate_bridge_stl,
    get_27_loto_positions
)

# Get 27 loto positions from row
lotos = get_27_loto_positions(row)

# Calculate prediction
pred_stl = calculate_bridge_stl(lotos[pos1], lotos[pos2], "sum")  # or "diff"
```

## Performance Considerations

1. **Bridge Count:** 756 new bridges significantly increase backtest time
2. **Database Size:** Each bridge adds 1 row to ManagedBridges table
3. **UI Responsiveness:** Threading prevents freeze during bulk insert
4. **Memory Usage:** Minimal impact as bridges are processed one at a time

## Future Enhancements

Possible improvements:
1. Batch enable/disable of Memory Bridges by range
2. Filter by win rate threshold in Bridge Management
3. Auto-enable high-performing Memory Bridges after initial backtest
4. Export/import Memory Bridge configurations
5. Visual analytics for Memory Bridge performance

## Files Modified

1. `logic/backtester_core.py` - Core backtest logic
2. `logic/bridges/bridge_manager_core.py` - Data generator
3. `ui/ui_settings.py` - UI integration
4. `tests/test_memory_bridges.py` - Test suite

## Dependencies

No new dependencies added. Uses existing modules:
- `re` (standard library)
- `sqlite3` (standard library)
- `threading` (standard library)

## Backward Compatibility

✅ **Fully backward compatible**
- V17 bridges continue to work exactly as before
- No database schema changes required
- Existing functionality preserved
- No breaking changes

## Support

For questions or issues:
1. Check this documentation
2. Review test cases in `tests/test_memory_bridges.py`
3. See UI screenshots in `DOC/UI_CHANGES_SCREENSHOT.md`
4. Review code comments in modified files

---

**Version:** 1.0  
**Date:** 2025-11-20  
**Status:** ✅ Complete and Tested
