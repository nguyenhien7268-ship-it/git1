# K1N-Primary Detection Flow Migration Guide

**Version**: V11.2  
**Date**: December 2024  
**Status**: Ready for Testing

## Overview

This migration introduces the K1N-primary detection flow for bridge scanning and import. The system now supports storing both K1N (real backtest) and K2N (simulated) rates, with configurable import policies.

## Key Changes

### Database Schema Changes

New columns added to `ManagedBridges` table:
- `k1n_rate_lo` (REAL): K1N rate for LO bridges
- `k1n_rate_de` (REAL): K1N rate for DE bridges  
- `k2n_rate_lo` (REAL): K2N rate for LO bridges
- `k2n_rate_de` (REAL): K2N rate for DE bridges
- `is_pending` (INTEGER): Approval status flag (0=approved, 1=pending)
- `imported_at` (TEXT): Import timestamp

### New Modules

1. **logic/models.py**: Dataclasses for candidates and configurations
   - `Candidate`: Bridge candidate with K1N/K2N rates
   - `ScanResult`: Scanner output structure
   - `ImportConfig`: Import policy configuration

2. **logic/bridge_importer.py**: Import orchestrator
   - Policy-based filtering (K1N-primary, K2N-primary, combined)
   - Preview mode for testing
   - Bulk atomic operations

3. **Enhanced logic/common_utils.py**: 
   - Vietnamese character normalization
   - Retry decorator for DB operations
   - Timestamp helpers

### Configuration

New settings in `logic/constants.py`:

```python
"THRESHOLD_K1N_LO": 85.0,          # K1N threshold for LO bridges (%)
"THRESHOLD_K1N_DE": 90.0,          # K1N threshold for DE bridges (%)
"THRESHOLD_K2N_LO": 80.0,          # K2N threshold for LO bridges (%)
"THRESHOLD_K2N_DE": 85.0,          # K2N threshold for DE bridges (%)
"POLICY_TYPE": "k1n_primary",      # Import policy
"FALLBACK_TO_K2N": True,           # Fallback when K1N missing
"AUTO_IMPORT_DEFAULT_ENABLE": False,   # Default enabled state
"AUTO_IMPORT_DEFAULT_PENDING": True,   # Default pending state
```

## Migration Steps

### 1. Backup Database

**CRITICAL**: Always backup before migration!

```bash
cd data
cp xo_so_prizes_all_logic.db xo_so_prizes_all_logic.db.backup_$(date +%Y%m%d)
```

### 2. Install Dependencies

```bash
cd /path/to/git1
python3 -m pip install -e .
```

This installs the package in editable mode for proper imports.

### 3. Run Database Migration

The migration is **idempotent** - safe to run multiple times.

```python
from logic.db_manager import setup_database

# Run migration (adds new columns if missing)
conn, cursor = setup_database()
conn.close()

print("Migration complete!")
```

### 4. Verify Migration

```python
from logic.db_manager import DB_NAME
import sqlite3

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Check new columns exist
cursor.execute("PRAGMA table_info(ManagedBridges)")
columns = [row[1] for row in cursor.fetchall()]

required_columns = [
    'k1n_rate_lo', 'k1n_rate_de', 
    'k2n_rate_lo', 'k2n_rate_de',
    'is_pending', 'imported_at'
]

for col in required_columns:
    if col in columns:
        print(f"✓ {col} exists")
    else:
        print(f"✗ {col} MISSING!")

conn.close()
```

### 5. Test New APIs

```python
from logic.db_manager import (
    get_all_managed_bridge_names,
    bulk_upsert_managed_bridges
)

# Test 1: Get existing names
names = get_all_managed_bridge_names()
print(f"Found {len(names)} existing bridges")

# Test 2: Bulk insert
test_bridges = [
    {
        'name': 'Test-Bridge-01',
        'description': 'Test bridge',
        'type': 'DE_DYN',
        'k1n_rate_de': 92.5,
        'k2n_rate_de': 88.0,
        'is_pending': 1
    }
]

result = bulk_upsert_managed_bridges(test_bridges)
print(f"Bulk upsert: {result}")
```

### 6. Test Importer

```python
from logic.bridge_importer import BridgeImporter
from logic.models import Candidate, ImportConfig

# Create test candidate
candidate = Candidate(
    name="Test-High-K1N",
    normalized_name="testhighk1n",
    type="de",
    kind="single",
    k1n_de=95.0,
    k2n_de=88.0,
    description="High K1N test bridge"
)

# Test preview mode
config = ImportConfig(policy_type="k1n_primary")
importer = BridgeImporter(config)

result = importer.preview_import([candidate])
print(importer.get_import_summary(result))
```

## Rollback Procedure

If issues occur, rollback steps:

### 1. Restore Database Backup

```bash
cd data
cp xo_so_prizes_all_logic.db.backup_YYYYMMDD xo_so_prizes_all_logic.db
```

### 2. Revert Code Changes

```bash
git checkout sua-loi-tu-44d144b  # Or previous stable branch
python3 -m pip uninstall xoso-das
```

### 3. Remove New Columns (Optional)

If you want to remove the new columns (not recommended - they don't harm):

```sql
-- SQLite doesn't support DROP COLUMN easily
-- Instead, create new table without columns and copy data
-- This is complex - prefer keeping columns with default values
```

## Testing

### Run Unit Tests

```bash
cd /path/to/git1

# Run all K1N-primary tests
python3 -m pytest tests/test_db_manager_bulk.py \
                  tests/test_common_utils_k1n.py \
                  tests/test_bridge_importer.py -v

# Expected: 57 tests pass
```

### Integration Testing

1. Run scanner (Phase 3 - not yet implemented)
2. Import candidates with different policies
3. Verify DB state
4. Test approval workflow

## Performance Considerations

- **Bulk Operations**: Use bulk APIs for >10 bridges
- **DB Locking**: Retry logic handles concurrent access
- **Memory**: Candidate lists held in memory during import
- **Normalization**: Vietnamese text requires extra processing

## Common Issues

### Issue 1: Import Module Errors

**Symptom**: `ModuleNotFoundError: No module named 'logic.xyz'`

**Solution**:
```bash
python3 -m pip install -e .
```

### Issue 2: Database Locked

**Symptom**: `sqlite3.OperationalError: database is locked`

**Solution**: Retry logic built-in. If persistent:
- Check for long-running queries
- Increase timeout in db connection
- Close unused connections

### Issue 3: Vietnamese Characters Not Normalizing

**Symptom**: Bridges with Vietnamese names not matching

**Solution**: Already fixed in normalize_bridge_name(). Handles:
- đ, ê, â, ô, ơ, ư, etc.
- All tone marks (à, á, ả, ã, ạ)

## FAQ

**Q: Will existing bridges be affected?**  
A: No. New columns have default values. Existing functionality unchanged.

**Q: Can I run old and new scanner together?**  
A: Yes, during transition. Old scanner uses `win_rate_text`, new uses `k1n_rate_*`.

**Q: What happens if scanner doesn't provide K1N?**  
A: If `FALLBACK_TO_K2N=True`, importer uses K2N. Otherwise, candidate rejected.

**Q: How do I change import thresholds?**  
A: Update constants in `logic/constants.py` or pass custom `ImportConfig`.

**Q: Is the migration reversible?**  
A: Yes, via database backup restore. New columns don't break old code.

## Next Steps

After successful migration:

1. **Phase 3**: Refactor scanner to use new flow
2. **UI Integration**: Add approval interface
3. **Monitoring**: Track K1N vs K2N accuracy
4. **Optimization**: Tune thresholds based on performance

## Support

For issues or questions:
- Check test files for usage examples
- Review docstrings in new modules
- Consult code review feedback

## Changelog

**V11.2.0 (Dec 2024)**
- Initial K1N-primary detection flow
- Database schema migration
- Bulk import APIs
- Comprehensive unit tests (57 tests)
- Vietnamese normalization fix
