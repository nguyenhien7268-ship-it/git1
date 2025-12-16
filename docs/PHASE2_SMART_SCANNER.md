# Phase 2: Smart Scanner with Bridge Revival

## Overview

Phase 2 upgrades the scanner logic to intelligently revive disabled bridges instead of blindly skipping them. This maximizes bridge reuse and reduces manual maintenance.

## The Problem (Before Phase 2)

**Old Logic:**
```
Scanner finds bridge → Already exists in DB → Skip (continue)
```

**Issues:**
- Disabled bridges remain disabled forever
- Scanner doesn't know if bridge is enabled or disabled
- Users must manually enable old bridges
- Duplicate effort creating same bridge multiple times

## The Solution (Phase 2)

**New Logic:**
```
Scanner finds bridge → Already exists in DB → Check is_enabled status
  ├─ If ENABLED (is_enabled=1) → Skip (no action needed)
  └─ If DISABLED (is_enabled=0) → Revive!
       ├─ Load lottery data
       ├─ Call activate_and_recalc_bridges()
       ├─ Recalculate WinRate, Streak, Prediction
       ├─ Set is_enabled=1
       └─ Log result
```

## Implementation Details

### Files Modified

#### 1. `logic/bridges/lo_bridge_scanner.py`
**Function:** `_convert_lo_bridges_to_candidates()`

**Changes:**
- Import BridgeService on first use (efficient)
- Check `is_enabled` status before skipping
- Call `activate_and_recalc_bridges([name])` for disabled bridges
- Log all revival attempts with `[Phase 2]` prefix

**Code snippet:**
```python
if norm_name in existing_names:
    # Bridge exists - check if disabled
    bridge_info = get_bridge_by_name(name, db_name)
    
    if bridge_info and bridge_info.get('is_enabled', 1) == 0:
        # DISABLED - revive it!
        print(f"[Phase 2] Reviving disabled bridge: {name}")
        result = bridge_service.activate_and_recalc_bridges([name], all_data)
        
        if result.get('success'):
            print(f"[Phase 2] ✅ Revived Bridge: {name}")
    
    continue  # Skip adding to candidates
```

#### 2. `logic/bridges/de_bridge_scanner.py`
**Method:** `DeBridgeScanner._convert_to_candidates()`

**Changes:**
- Same logic as LO scanner
- Uses proper logging module (logger.info/warning)
- Added `db_name` parameter to method signature

**Code snippet:**
```python
if bridge_info and bridge_info.get('is_enabled', 1) == 0:
    logger.info(f"[Phase 2] Reviving disabled DE bridge: {name}")
    result = bridge_service.activate_and_recalc_bridges([name], all_data)
    
    if result.get('success'):
        logger.info(f"[Phase 2] ✅ Revived DE Bridge: {name}")
```

### Key Features

1. **Automatic Revival** - No manual intervention needed
2. **Fresh Metrics** - Revived bridges get updated performance data
3. **Smart Detection** - Only revives if `is_enabled=0`
4. **Proper Logging** - All attempts logged with `[Phase 2]` prefix
5. **Error Handling** - Graceful fallback if BridgeService unavailable

## Usage

### For Users

**No action needed!** The scanner now automatically:
- Detects disabled bridges
- Reactivates them with fresh metrics
- Logs the revival

### For Developers

**To test manually:**
1. Disable a bridge: `UPDATE ManagedBridges SET is_enabled=0 WHERE name='BridgeName'`
2. Run scanner
3. Check logs for `[Phase 2] Revived Bridge: BridgeName`
4. Verify bridge is enabled: `SELECT is_enabled FROM ManagedBridges WHERE name='BridgeName'`

## Logging Output

**Successful revival:**
```
[Phase 2] Reviving disabled bridge: LO_POS_Test1_Test2
[Phase 2] ✅ Revived Bridge: LO_POS_Test1_Test2
```

**Failed revival:**
```
[Phase 2] Reviving disabled bridge: LO_POS_Test1_Test2
[Phase 2] ⚠️ Failed to revive LO_POS_Test1_Test2: Insufficient data
```

**Error during check:**
```
[Phase 2] Error checking bridge status for LO_POS_Test1_Test2: <error details>
```

## Performance

**Impact:** Minimal
- BridgeService initialized once per scan (not per bridge)
- Revival only happens for disabled bridges (rare)
- Normal scanning unaffected

**Typical scenarios:**
- 100 bridges scanned, 0 disabled → No revival overhead
- 100 bridges scanned, 1 disabled → 1 revival call (~100ms)
- Most scans have 0 disabled bridges

## Testing

### Integration Test
```bash
python3 docs/integration_test_phase2.py
```

**Results:**
- ✅ Database setup verified
- ✅ Phase 2 modifications confirmed
- ✅ Disabled bridge status verified
- ✅ Revival logic in place

### Unit Tests
```bash
python3 -m pytest tests/test_phase2_bridge_revival.py -v
```

**Coverage:**
- LO scanner revival
- DE scanner revival
- Enabled bridges not revived

## Integration with Phase 1

Phase 2 leverages Phase 1 infrastructure:
- Uses `BridgeService.activate_and_recalc_bridges()` from Phase 1
- Reuses bridge activation logic
- Maintains consistent logging format
- Thread-safe operations

## Error Handling

**If BridgeService unavailable:**
- Prints warning: `[Phase 2] Warning: Could not import BridgeService - revival disabled`
- Falls back to old behavior (skip existing bridges)
- Scanner continues normally

**If data insufficient:**
- Logs: `[Phase 2] ⚠️ Insufficient data to revive {name}`
- Bridge remains disabled
- No exception thrown

**If activation fails:**
- Logs failure reason
- Bridge remains disabled
- Scanner continues with other bridges

## Benefits

1. **Reduced Maintenance** - No manual bridge enabling needed
2. **Better Resource Use** - Reuses existing bridges instead of duplicating
3. **Automatic Updates** - Disabled bridges get fresh metrics when revived
4. **Transparency** - All revivals logged clearly
5. **Backward Compatible** - Works with existing bridge infrastructure

## Future Enhancements

- [ ] Configurable revival threshold (e.g., only revive if K2N > X%)
- [ ] Batch revival for multiple disabled bridges
- [ ] Revival history tracking
- [ ] UI notification for revived bridges

## Troubleshooting

**Bridge not reviving?**
1. Check logs for `[Phase 2]` messages
2. Verify bridge is actually disabled: `SELECT is_enabled FROM ManagedBridges WHERE name='BridgeName'`
3. Ensure sufficient lottery data (>= 2 periods)
4. Check BridgeService is available

**Revival failing?**
1. Review error message in log
2. Check lottery data availability
3. Verify bridge configuration (pos1_idx, pos2_idx, etc.)
4. Ensure database permissions

## Summary

Phase 2 makes the scanner intelligent by:
- ✅ Checking bridge status before skipping
- ✅ Reviving disabled bridges automatically
- ✅ Updating metrics in real-time
- ✅ Logging all actions clearly
- ✅ No performance penalty

**Result:** Smarter, more efficient bridge management with zero manual intervention!
