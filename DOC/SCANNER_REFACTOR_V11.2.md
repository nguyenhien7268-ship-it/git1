# Scanner Refactor V11.2 - K1N-Primary Detection Flow

## Overview

Version 11.2 introduces a major refactoring of the bridge scanner modules to support the K1N-Primary detection flow. The key change is that scanners no longer write directly to the database. Instead, they return `Candidate` objects that can be previewed and filtered before import.

## Key Changes

### 1. Read-Only Scanners

**Before (V10.x):**
```python
# Scanner wrote directly to DB
count, bridges = run_de_scanner(data)
# Bridges were already in DB
```

**After (V11.2):**
```python
# Scanner returns Candidates (no DB writes)
candidates, meta = run_de_scanner(data, db_name)
# Candidates are in-memory, not yet in DB
print(f"Found: {meta['found_total']}, Excluded: {meta['excluded_existing']}")
```

### 2. Candidate Objects with Rates

Each scanner now returns `Candidate` objects with:
- **normalized_name**: For duplicate checking
- **k1n_lo / k1n_de**: Real backtest rates (K1N)
- **k2n_lo / k2n_de**: Simulated rates (K2N) 
- **rate_missing**: Flag when rates not found in cache
- **pos1_idx / pos2_idx**: Position indices for V17 bridges
- **metadata**: Additional bridge-specific data

### 3. Automatic Exclusion of Existing Bridges

Scanners now:
1. Load existing bridge names once via `get_all_managed_bridge_names()`
2. Compare normalized names to exclude duplicates
3. Return only NEW candidates
4. Report counts in meta: `found_total`, `excluded_existing`, `returned_count`

### 4. Rate Cache Integration

Scanners attach K1N/K2N rates from DB cache:
1. Single call to `load_rates_cache()` 
2. Lookup rates by normalized name
3. Set `rate_missing=True` if not found
4. Enables policy-based filtering by BridgeImporter

## Refactored Modules

### DE Bridge Scanner (`logic/bridges/de_bridge_scanner.py`)

**Main Function:**
```python
def scan_all(
    self, 
    all_data_ai: List[List[str]], 
    db_name: str = DB_NAME
) -> Tuple[List[Candidate], Dict[str, Any]]:
    """
    Scan for DE bridges and return Candidate objects (READ-ONLY).
    
    Returns:
        Tuple of (candidates, meta):
            - candidates: List[Candidate] with rates attached
            - meta: {'found_total': X, 'excluded_existing': Y, 'returned_count': Z}
    """
```

**Changes:**
- ✅ Removed `_save_to_db()` method
- ✅ Added `_convert_to_candidates()` helper
- ✅ Loads existing names and rates cache once
- ✅ Returns Candidates instead of dicts
- ✅ No INSERT/UPDATE/DELETE operations

### LO Bridge Scanner (`logic/bridges/lo_bridge_scanner.py`)

**New Functions:**
```python
def scan_lo_bridges_v17(...) -> Tuple[List[Candidate], Dict[str, Any]]:
    """Scan LO V17 bridges and return Candidates (READ-ONLY)."""

def _convert_lo_bridges_to_candidates(...) -> List[Candidate]:
    """Convert bridge dicts to Candidate objects with rates."""
```

**Changes:**
- ✅ Added new wrapper functions for read-only scanning
- ✅ Removed `upsert_managed_bridge()` calls
- ✅ Returns Candidates with normalized names
- ✅ Old functions preserved for backward compatibility

## New Utilities

### load_rates_cache() (`logic/db_manager.py`)

```python
def load_rates_cache(db_name: str = DB_NAME) -> Dict[str, Dict[str, float]]:
    """
    Load K1N/K2N rates cache from ManagedBridges table.
    
    Returns:
        Dict[normalized_name, rates_dict] where rates_dict contains:
            - k1n_rate_lo: K1N rate for LO bridges
            - k1n_rate_de: K1N rate for DE bridges
            - k2n_rate_lo: K2N rate for LO bridges
            - k2n_rate_de: K2N rate for DE bridges
    """
```

## Import Workflow

### Step 1: Scan (Read-Only)

```python
from logic.bridges.de_bridge_scanner import run_de_scanner
from logic.bridges.lo_bridge_scanner import scan_lo_bridges_v17

# Scan DE bridges
de_candidates, de_meta = run_de_scanner(lottery_data, db_name)
print(f"DE: {de_meta['found_total']} found, {de_meta['returned_count']} new")

# Scan LO bridges  
lo_candidates, lo_meta = scan_lo_bridges_v17(
    lottery_data, start_period, end_period, db_name
)
print(f"LO: {lo_meta['found_total']} found, {lo_meta['returned_count']} new")
```

### Step 2: Preview with Policy

```python
from logic.bridge_importer import BridgeImporter, ImportConfig

# Configure import policy
config = ImportConfig(
    policy_type='k1n_primary',      # Primary decision based on K1N
    threshold_k1n_de=90.0,          # DE bridges need ≥90% K1N
    threshold_k1n_lo=85.0,          # LO bridges need ≥85% K1N
    fallback_to_k2n=True,           # Use K2N if K1N missing
    threshold_k2n_de=85.0,          # Fallback threshold
    preview_only=True               # Don't write to DB yet
)

# Preview which candidates will be imported
importer = BridgeImporter(config)
preview = importer.filter_candidates(de_candidates + lo_candidates)

print(f"Accepted: {len(preview['accepted'])}")
print(f"Rejected: {len(preview['rejected'])} (below threshold)")
print(f"Duplicates: {len(preview['duplicates'])} (already in DB)")
```

### Step 3: Import to Database

```python
# Actually import accepted candidates
config.preview_only = False
result = importer.import_candidates(de_candidates + lo_candidates)

print(f"Imported: {result['imported']}")
print(f"Failed: {result['failed']}")
print(f"Skipped: {result['skipped']}")
```

## Benefits

1. **Separation of Concerns**: Scanning logic separate from DB writes
2. **Preview Before Import**: Inspect candidates before committing
3. **Policy-Based Filtering**: Apply thresholds to K1N/K2N rates
4. **No Duplicate Imports**: Automatic exclusion of existing bridges
5. **Atomic Operations**: Bulk imports with transaction support
6. **Testability**: Easy to test scanners without DB side effects

## Testing

Integration tests in `tests/test_scanner_refactor.py`:

```python
def test_no_db_writes_during_scan(temp_db, sample_lottery_data):
    """Verify scanner does not write to DB."""
    count_before = count_bridges_in_db(temp_db)
    
    scanner = DeBridgeScanner()
    candidates, meta = scanner.scan_all(sample_lottery_data, temp_db)
    
    count_after = count_bridges_in_db(temp_db)
    assert count_before == count_after  # No DB writes!

def test_attaches_rates_from_cache(temp_db):
    """Verify K1N/K2N rates are attached."""
    # Pre-populate cache
    setup_rates_in_db(temp_db)
    
    candidates, meta = run_scanner(temp_db)
    
    for candidate in candidates:
        assert hasattr(candidate, 'k1n_de')
        assert hasattr(candidate, 'k2n_de')
        assert hasattr(candidate, 'rate_missing')
```

## Migration Notes

### For Existing Code

If you have code that calls the old scanner functions:

**Option 1: Continue using old functions (backward compatible)**
```python
# Old functions still work (but write to DB)
TIM_CAU_TOT_NHAT_V16(data, start, end, db_name)
TIM_CAU_BAC_NHO_TOT_NHAT(data, start, end, db_name)
```

**Option 2: Migrate to new scanner + importer**
```python
# New pattern: scan → preview → import
candidates, meta = scan_lo_bridges_v17(data, start, end, db_name)
importer = BridgeImporter(config)
result = importer.import_candidates(candidates)
```

### For UI Code

Update UI to show preview before import:

```python
# 1. Scan and show results
candidates, meta = run_de_scanner(data, db_name)
show_candidates_in_table(candidates)

# 2. Let user review and select
selected_candidates = get_user_selection()

# 3. Import selected
importer = BridgeImporter(config)
result = importer.import_candidates(selected_candidates)
show_import_results(result)
```

## Performance

- **Single DB read for existing names**: O(N) where N = existing bridges
- **Single DB read for rates cache**: O(N) where N = existing bridges  
- **In-memory filtering**: O(M) where M = scanned candidates
- **Bulk import**: O(K) where K = candidates to import

Total: **2 reads + 1 write** (vs old: N writes where N = candidates)

## Future Enhancements

- [ ] Add progress callbacks for long-running scans
- [ ] Support incremental scanning (only new data)
- [ ] Add scan result caching
- [ ] UI for interactive candidate review
- [ ] Export/import candidate sets

## References

- `logic/models.py`: Candidate dataclass definition
- `logic/bridge_importer.py`: Import policy and execution
- `logic/db_manager.py`: load_rates_cache(), get_all_managed_bridge_names()
- `logic/common_utils.py`: normalize_bridge_name()
- `tests/test_scanner_refactor.py`: Integration tests

---

**Version**: V11.2  
**Date**: December 2025  
**Status**: ✅ Implemented and Tested
