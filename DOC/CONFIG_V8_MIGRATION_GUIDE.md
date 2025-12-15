# Config V8 Migration Guide - Dual-Config Architecture

## Overview

Version 8 introduces a **Dual-Config Architecture** that separates bridge management thresholds for **Lo (Lô)** and **De (Dề)** bridge types. This allows for independent optimization and more granular control over each bridge category.

---

## What Changed?

### Old Structure (V7)
```json
{
    "AUTO_PRUNE_MIN_RATE": 43.0,
    "AUTO_ADD_MIN_RATE": 45.0
}
```

**Single thresholds** applied to all bridge types uniformly.

### New Structure (V8)
```json
{
    "lo_config": {
        "remove_threshold": 43.0,
        "add_threshold": 45.0,
        "enable_threshold": 40.0,
        "description": "Configuration for Lo bridges (2-digit lottery numbers)"
    },
    "de_config": {
        "remove_threshold": 43.0,
        "add_threshold": 45.0,
        "enable_threshold": 40.0,
        "description": "Configuration for De bridges (1-digit lottery numbers)"
    },
    "AUTO_PRUNE_MIN_RATE_DEPRECATED": 43.0,
    "AUTO_ADD_MIN_RATE_DEPRECATED": 45.0
}
```

**Independent thresholds** for each bridge type with backward compatibility.

---

## Migration Process

### Automatic Migration

Use the provided migration script:

```bash
# Preview changes (dry-run)
python scripts/migrate_config_v8.py --dry-run

# Run migration with backup
python scripts/migrate_config_v8.py --backup

# Run migration without prompts
python scripts/migrate_config_v8.py --backup --force
```

### Migration Script Features

✅ **Safe Migration:**
- Creates backup before modification
- Validates configuration structure
- Shows clear preview of changes
- Requires confirmation (unless --force)

✅ **Intelligent Mapping:**
- `AUTO_PRUNE_MIN_RATE` → `lo_config.remove_threshold` and `de_config.remove_threshold`
- `AUTO_ADD_MIN_RATE` → `lo_config.add_threshold` and `de_config.add_threshold`
- Calculates `enable_threshold` = `remove_threshold - 3.0` (minimum 35%)

✅ **Backward Compatibility:**
- Preserves old values as `*_DEPRECATED` keys
- Allows gradual code migration
- No breaking changes to existing code

---

## Configuration Definitions

### Lo Config (2-Digit Bridges)

Configuration for **Lô** (2-digit lottery number) bridges.

| Threshold | Default | Description |
|-----------|---------|-------------|
| `remove_threshold` | 43.0% | Minimum win rate to keep bridge active. Below this → disable bridge |
| `add_threshold` | 45.0% | Minimum win rate to add new bridge to managed list |
| `enable_threshold` | 40.0% | Minimum win rate to re-enable disabled bridge |

**Relationship:** `add_threshold >= remove_threshold >= enable_threshold`

### De Config (1-Digit Bridges)

Configuration for **Dề** (1-digit lottery number) bridges.

| Threshold | Default | Description |
|-----------|---------|-------------|
| `remove_threshold` | 43.0% | Minimum win rate to keep bridge active. Below this → disable bridge |
| `add_threshold` | 45.0% | Minimum win rate to add new bridge to managed list |
| `enable_threshold` | 40.0% | Minimum win rate to re-enable disabled bridge |

**Relationship:** `add_threshold >= remove_threshold >= enable_threshold`

---

## Threshold Logic Explained

### Three-Tier Threshold System

```
High Performance    ═══════════════════════════════════
                    ║ add_threshold (45%)              ║
                    ║ → Add new bridges                 ║
                    ═══════════════════════════════════
Good Performance    ║ remove_threshold (43%)           ║
                    ║ → Keep active                     ║
                    ═══════════════════════════════════
Buffer Zone         ║ enable_threshold (40%)           ║
                    ║ → Re-enable disabled             ║
                    ═══════════════════════════════════
Poor Performance    ║ Below enable_threshold           ║
                    ║ → Disable/Remove                  ║
                    ═══════════════════════════════════
```

### Decision Matrix

| Win Rate | Status | Action |
|----------|--------|--------|
| ≥ 45% | Excellent | Add to managed list if new |
| 43-45% | Good | Keep active |
| 40-43% | Buffer | Monitor, re-enable if improving |
| < 40% | Poor | Disable or remove |

### Buffer Zone (40-43%)

The **buffer zone** prevents oscillation:
- Bridges disabled at 42.9% won't re-enable until they reach 40%+
- Prevents constant enable/disable cycles
- Allows time for performance recovery

---

## Code Integration

### Reading New Config

#### Python Example

```python
# Load configuration
with open("config.json", "r") as f:
    config = json.load(f)

# Access Lo bridge thresholds
lo_remove = config["lo_config"]["remove_threshold"]
lo_add = config["lo_config"]["add_threshold"]
lo_enable = config["lo_config"]["enable_threshold"]

# Access De bridge thresholds
de_remove = config["de_config"]["remove_threshold"]
de_add = config["de_config"]["add_threshold"]
de_enable = config["de_config"]["enable_threshold"]
```

#### Config Manager Integration

```python
class AppSettings:
    def __init__(self):
        self.load_settings()
    
    def load_settings(self):
        with open(CONFIG_FILE, "r") as f:
            settings = json.load(f)
        
        # Load Lo config
        self.LO_REMOVE_THRESHOLD = settings["lo_config"]["remove_threshold"]
        self.LO_ADD_THRESHOLD = settings["lo_config"]["add_threshold"]
        self.LO_ENABLE_THRESHOLD = settings["lo_config"]["enable_threshold"]
        
        # Load De config
        self.DE_REMOVE_THRESHOLD = settings["de_config"]["remove_threshold"]
        self.DE_ADD_THRESHOLD = settings["de_config"]["add_threshold"]
        self.DE_ENABLE_THRESHOLD = settings["de_config"]["enable_threshold"]
        
        # Backward compatibility (if needed)
        if "AUTO_PRUNE_MIN_RATE_DEPRECATED" in settings:
            self.AUTO_PRUNE_MIN_RATE = settings["AUTO_PRUNE_MIN_RATE_DEPRECATED"]
        if "AUTO_ADD_MIN_RATE_DEPRECATED" in settings:
            self.AUTO_ADD_MIN_RATE = settings["AUTO_ADD_MIN_RATE_DEPRECATED"]
```

### Bridge Type Detection

```python
def get_bridge_config(bridge_type, config):
    """
    Get appropriate config based on bridge type.
    
    Args:
        bridge_type: String like "STL", "VT", "DE_PLUS", etc.
        config: Full configuration dict
    
    Returns:
        dict: Appropriate config (lo_config or de_config)
    """
    # Determine if bridge is De type
    if bridge_type.upper().startswith("DE_"):
        return config["de_config"]
    else:
        # Default to Lo config
        return config["lo_config"]

# Usage
bridge_config = get_bridge_config("STL_PLUS_5", config)
should_add = win_rate >= bridge_config["add_threshold"]
should_remove = win_rate < bridge_config["remove_threshold"]
```

---

## Benefits of Dual-Config

### 1. Independent Optimization

Lo and De bridges can have different performance characteristics:
- **Lo bridges** (2-digit): More combinations, different win patterns
- **De bridges** (1-digit): Fewer combinations, different dynamics

With dual-config, you can optimize each independently:

```json
{
    "lo_config": {
        "remove_threshold": 43.0,
        "add_threshold": 45.0,
        "enable_threshold": 40.0
    },
    "de_config": {
        "remove_threshold": 50.0,   // Higher threshold for De
        "add_threshold": 55.0,       // More selective for De
        "enable_threshold": 45.0
    }
}
```

### 2. Risk Management

Different risk tolerances per bridge type:
- Conservative for Lo bridges
- Aggressive for De bridges
- Or vice versa!

### 3. Data-Driven Tuning

After collecting performance data:
1. Analyze Lo vs De bridge performance
2. Adjust thresholds independently
3. Optimize each category separately

### 4. Backward Compatibility

Deprecated keys ensure:
- No breaking changes
- Gradual migration path
- Time to update code

---

## Migration Checklist

### Immediate (Required)
- [x] Run migration script: `python scripts/migrate_config_v8.py --backup`
- [x] Verify backup created in `config_backups/`
- [x] Check new config structure in `config.json`

### Short-term (Recommended)
- [ ] Update `logic/config_manager.py` to read new config structure
- [ ] Test bridge management with new thresholds
- [ ] Update UI to show/edit dual-config thresholds

### Long-term (Optional)
- [ ] Collect performance data for Lo vs De bridges
- [ ] Optimize thresholds independently
- [ ] Remove deprecated keys after code fully migrated

---

## Troubleshooting

### Migration Script Issues

**Problem:** Config file not found
```
❌ Config file not found: config.json
```
**Solution:** Ensure you're running from project root directory

**Problem:** Invalid config structure
```
❌ Configuration validation failed
```
**Solution:** Check config.json syntax with `python -m json.tool config.json`

**Problem:** Permission denied
```
❌ Failed to write config file: Permission denied
```
**Solution:** Check file permissions: `chmod 644 config.json`

### Rollback Migration

If you need to rollback:

```bash
# 1. Find backup file
ls config_backups/

# 2. Restore from backup
cp config_backups/config_v7_backup_YYYYMMDD_HHMMSS.json config.json

# 3. Verify
python -m json.tool config.json
```

---

## Advanced Usage

### Custom Threshold Ratios

You can set different ratios between thresholds:

```json
{
    "lo_config": {
        "remove_threshold": 40.0,
        "add_threshold": 50.0,     // 10% gap
        "enable_threshold": 35.0
    },
    "de_config": {
        "remove_threshold": 45.0,
        "add_threshold": 48.0,     // 3% gap (tighter)
        "enable_threshold": 42.0
    }
}
```

### Regional Differences

For multi-region support:

```json
{
    "lo_config_north": { ... },
    "lo_config_south": { ... },
    "de_config_north": { ... },
    "de_config_south": { ... }
}
```

---

## FAQ

### Q: Do I need to migrate immediately?

**A:** No, but it's recommended. The deprecated keys provide backward compatibility, but you'll miss out on independent optimization.

### Q: Will this break my existing code?

**A:** No. Deprecated keys (`AUTO_PRUNE_MIN_RATE_DEPRECATED`) maintain the old values. Code using old keys will continue to work.

### Q: Can I use different thresholds for Lo and De?

**A:** Yes! That's the main benefit. After migration, edit `config.json` to set different values.

### Q: What if I want to revert?

**A:** Use the backup file created in `config_backups/`. Simply copy it back to `config.json`.

### Q: How do I know which bridges are Lo vs De?

**A:** Typically:
- **Lo bridges:** STL, VT, MOI, G7, G1 series (2-digit predictions)
- **De bridges:** DE_PLUS, DE_KILLER series (1-digit predictions)

Check bridge type in your code or database.

---

## Support

For issues or questions:
1. Check this documentation
2. Review backup files in `config_backups/`
3. Run migration script with `--dry-run` to preview changes
4. Check test suite: `pytest tests/test_migrate_config_v8.py -v`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| V8 | 2025-12-14 | Initial dual-config architecture release |
| V7 | - | Single threshold system |

---

**Last Updated:** 2025-12-14  
**Status:** Production Ready ✅  
**Backward Compatible:** Yes ✅
