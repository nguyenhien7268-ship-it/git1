# "756 Cầu Bạc Nhớ" Implementation Documentation (V2.1 Standard)

## Overview

This document describes the complete implementation of the "756 Cầu Bạc Nhớ" (Memory Bridges) system, updated to strictly follow the **Naming Convention V2.1**. This system adds support for 756 new bridge calculation algorithms based on memory (Bạc Nhớ) formulas, using standardized IDs for better management.

## Project Structure

The implementation is organized in 3 main phases:

### Phase 1: Core Logic Upgrade
**File:** logic/bridges/bridge_manager_core.py

Updated the core scanning and generation functions to support V2.1 standardized IDs.

**Identification Strategy:**
* **Prefix:** LO_MEM_
* **Type:** LO_MEM
* **Indices:** pos1_idx is -1 and pos2_idx is -1

**Bridge Name Format (V2.1):**
Memory bridge names now follow these standardized formats:
* **Sum (Tổng):** LO_MEM_SUM_[LOTO1]_[LOTO2] (Example: LO_MEM_SUM_00_01)
* **Difference (Hiệu):** LO_MEM_DIFF_[LOTO1]_[LOTO2] (Example: LO_MEM_DIFF_00_01)

**Parsing Logic:**
Instead of using Regex on display names (e.g., "Tổng(00+01)"), the system now parses the ID directly for better performance and reliability.
* Step 1: Check if name contains "LO_MEM_SUM" or "LO_MEM_DIFF".
* Step 2: Split the string by underscore `_`.
* Step 3: Extract parameters (Loto 1 is at index 3, Loto 2 is at index 4).

### Phase 2: Data Generator
**File:** logic/bridges/bridge_manager_core.py

Updated function `init_all_756_memory_bridges_to_db` to generate IDs according to V2.1 standards.

**Generation Logic:**
It loops through all 27 loto positions (from 00 to 26).
* **Loop:** i from 0 to 26; j from i to 26.
* **Sum Bridge ID:** f"LO_MEM_SUM_{loto_i}_{loto_j}"
* **Diff Bridge ID:** f"LO_MEM_DIFF_{loto_i}_{loto_j}"

**Total Bridges:** 756 bridges (378 Sum types + 378 Diff types).

**Database Fields Configuration:**
* **name:** LO_MEM_SUM_00_01 (This is the Standard ID used for logic).
* **description:** Bạc Nhớ: Tổng(00 + 01) (This is the human-readable text for UI).
* **type:** LO_MEM (New field introduced in V2.1 for classification).
* **pos1_idx:** -1 (Indicates this is a Memory Bridge).
* **pos2_idx:** -1 (Indicates this is a Memory Bridge).
* **is_enabled:** 0 (Disabled by default).

### Phase 3: UI Integration
**File:** ui/ui_settings.py

Maintained the UI button "Nạp 756 Cầu Bạc Nhớ" which now triggers the updated generator function.

**Components:**
* Button: "Nạp 756 Cầu Bạc Nhớ".
* Progress Window: Visual feedback while generating 756 V2.1 bridges.

**User Flow:**
1.  User clicks "Nạp 756 Cầu Bạc Nhớ".
2.  System generates/updates bridges with LO_MEM_... IDs.
3.  Success notification confirms the number of bridges added/skipped.

## Bridge Calculation Formulas

Memory Bridges use the `calculate_bridge_stl()` function from `logic/bridges/bridges_memory.py`.

### 1. Sum Algorithm (Tổng)
* Formula: btl = (loto1 + loto2) % 100

### 2. Difference Algorithm (Hiệu)
* Formula: btl = abs(loto1 - loto2)

### 3. STL Generation
* If the result is a double number (e.g., 11, 22): Use `taoSTL_V30_Bong()` to get the shadow pair.
* Otherwise: Return the number and its reverse (e.g., 12 returns ["12", "21"]).

## Database Schema Updates

The `ManagedBridges` table schema has been updated to support V2.1. Below are the key columns:

* **id**: Integer (Primary Key).
* **name**: Text. Stores the V2.1 Standard ID (e.g., LO_MEM_SUM_00_01).
* **type**: Text. Stores the Bridge Type (Value: LO_MEM).
* **description**: Text. Stores the display name (e.g., Bạc Nhớ: Tổng(00 + 01)).
* **pos1_idx**: Integer. Value: -1.
* **pos2_idx**: Integer. Value: -1.
* **is_enabled**: Integer. Value: 1 for Enabled, 0 for Disabled.

## Testing

### Test Coverage
**Files:** tests/test_memory_bridges.py

Tests have been updated to validate the V2.1 format:
1.  **Initialization Test:** Verifies 756 bridges are created with the correct `LO_MEM_` prefix.
2.  **Naming Format Test:** Validates that names match `LO_MEM_SUM` and `LO_MEM_DIFF` patterns.
3.  **Calculation Test:** Verifies calculation logic based on new ID parsing mechanisms.

## Usage Instructions

### For Users

1.  **Loading Memory Bridges:**
    * Go to Settings -> Click "Nạp 756 Cầu Bạc Nhớ".

2.  **Enabling Memory Bridges:**
    * Go to "Quản Lý Cầu".
    * Search for "Bạc Nhớ" or type "LO_MEM" in the filter box.
    * Select and Enable the desired bridges.

3.  **Running Backtest:**
    * Select "Cầu Đã Lưu N1/K2N".
    * The system automatically recognizes the `LO_MEM` type and executes the correct logic.

### For Developers

**Detecting Memory Bridges:**
Check if `bridge_type` equals 'LO_MEM' or if `name` starts with 'LO_MEM_'.

**Parsing Bridge Names (V2.1):**
Split the `name` string by the underscore character `_`.
* Index 2: Operation type ('SUM' or 'DIFF').
* Index 3: Loto 1.
* Index 4: Loto 2.

## Performance Considerations

* **Bridge Count:** 756 bridges.
* **Scan Speed:** Scanning V2.1 bridges is significantly faster as it uses direct string splitting instead of Regex on description fields.
* **Database:** Standardized IDs improve query performance and consistency.

## Future Enhancements

* **Batch Management:** Enable all 'SUM' or 'DIFF' bridges via SQL commands.
* **Auto-Optimization:** Prune `LO_MEM` bridges with low win rates (using the generic `prune_bad_bridges` function).

## Files Modified

* `logic/bridges/bridge_manager_core.py`: Generator & Scanner (V2.1 Logic).
* `logic/bridges/bridges_memory.py`: Calculation Logic.
* `logic/db_manager.py`: Schema Updates (Self-healing columns).

## Backward Compatibility

**Warning: Breaking Changes for V1.0**
* Old bridges named `Tổng(...)` are considered "Legacy/Unknown" and should be cleaned up.
* The code now expects the `LO_MEM_...` format for logic execution.
* **Migration:** The script `scripts/run_scan_migration.py` handles the conversion and cleanup process.

## Support

For issues, run `python scripts/check_bridge_types_distribution.py` to verify if your database contains valid `LO_MEM` bridges.

---

**Version:** 2.1 (Standardized)
**Date:** 2025-12-02
**Status:** Complete and Deployed