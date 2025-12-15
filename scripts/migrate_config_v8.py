#!/usr/bin/env python3
"""
Config Migration Script V8 - Dual-Config Architecture (Lo/De)

This script migrates the old single-threshold configuration to a new
dual-config architecture with independent optimization thresholds for
Lo (2-digit) and De (1-digit) bridge management systems.

Old Structure:
    AUTO_PRUNE_MIN_RATE: 43.0    # Single threshold for all bridges
    AUTO_ADD_MIN_RATE: 45.0      # Single threshold for all bridges

New Structure:
    lo_config:
        remove_threshold: 43.0   # For Lo bridges (2-digit)
        add_threshold: 45.0      # For Lo bridges (2-digit)
        enable_threshold: 40.0   # For Lo bridges (2-digit)
    de_config:
        remove_threshold: 43.0   # For De bridges (1-digit)
        add_threshold: 45.0      # For De bridges (1-digit)
        enable_threshold: 40.0   # For De bridges (1-digit)

Usage:
    python scripts/migrate_config_v8.py [--backup] [--dry-run]

Options:
    --backup    Create a backup of config.json before migration
    --dry-run   Show what would be changed without modifying files
    --force     Skip confirmation prompts
"""

import json
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CONFIG_FILE = "config.json"
BACKUP_DIR = "config_backups"


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


def print_info(text):
    """Print info message."""
    print(f"ℹ️  {text}")


def print_success(text):
    """Print success message."""
    print(f"✅ {text}")


def print_warning(text):
    """Print warning message."""
    print(f"⚠️  {text}")


def print_error(text):
    """Print error message."""
    print(f"❌ {text}")


def create_backup(config_path):
    """
    Create a backup of the current config file.
    
    Args:
        config_path: Path to the config file
        
    Returns:
        str: Path to the backup file
    """
    # Create backup directory if it doesn't exist
    backup_dir = Path(BACKUP_DIR)
    backup_dir.mkdir(exist_ok=True)
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"config_v7_backup_{timestamp}.json"
    backup_path = backup_dir / backup_filename
    
    # Copy file
    shutil.copy2(config_path, backup_path)
    print_success(f"Backup created: {backup_path}")
    
    return str(backup_path)


def read_config(config_path):
    """
    Read the current config file.
    
    Args:
        config_path: Path to the config file
        
    Returns:
        dict: Current configuration
    """
    if not os.path.exists(config_path):
        print_error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        print_success(f"Config file loaded: {config_path}")
        return config
    except Exception as e:
        print_error(f"Failed to read config file: {e}")
        sys.exit(1)


def extract_old_values(config):
    """
    Extract old threshold values from config.
    
    Args:
        config: Current configuration dict
        
    Returns:
        dict: Extracted values
    """
    old_values = {
        "AUTO_PRUNE_MIN_RATE": config.get("AUTO_PRUNE_MIN_RATE", 40.0),
        "AUTO_ADD_MIN_RATE": config.get("AUTO_ADD_MIN_RATE", 50.0),
    }
    
    print_info("Extracted old values:")
    print(f"  AUTO_PRUNE_MIN_RATE: {old_values['AUTO_PRUNE_MIN_RATE']}")
    print(f"  AUTO_ADD_MIN_RATE: {old_values['AUTO_ADD_MIN_RATE']}")
    
    return old_values


def create_dual_config(old_values):
    """
    Create new dual-config structure from old values.
    
    Args:
        old_values: Dict with old configuration values
        
    Returns:
        dict: New configuration structure
    """
    # Calculate enable_threshold as slightly lower than remove_threshold
    # This creates a buffer zone for bridge management
    auto_prune = old_values["AUTO_PRUNE_MIN_RATE"]
    auto_add = old_values["AUTO_ADD_MIN_RATE"]
    enable_threshold = max(auto_prune - 3.0, 35.0)  # At least 35%
    
    new_config = {
        "lo_config": {
            "remove_threshold": auto_prune,
            "add_threshold": auto_add,
            "enable_threshold": enable_threshold,
            "description": "Configuration for Lo bridges (2-digit lottery numbers)"
        },
        "de_config": {
            "remove_threshold": auto_prune,
            "add_threshold": auto_add,
            "enable_threshold": enable_threshold,
            "description": "Configuration for De bridges (1-digit lottery numbers)"
        }
    }
    
    print_info("Created new dual-config structure:")
    print(f"  lo_config:")
    print(f"    - remove_threshold: {new_config['lo_config']['remove_threshold']}%")
    print(f"    - add_threshold: {new_config['lo_config']['add_threshold']}%")
    print(f"    - enable_threshold: {new_config['lo_config']['enable_threshold']}%")
    print(f"  de_config:")
    print(f"    - remove_threshold: {new_config['de_config']['remove_threshold']}%")
    print(f"    - add_threshold: {new_config['de_config']['add_threshold']}%")
    print(f"    - enable_threshold: {new_config['de_config']['enable_threshold']}%")
    
    return new_config


def merge_configs(old_config, new_config):
    """
    Merge old and new configurations.
    
    Args:
        old_config: Original configuration
        new_config: New dual-config structure
        
    Returns:
        dict: Merged configuration
    """
    # Start with old config
    merged = old_config.copy()
    
    # Add new dual-config structures
    merged.update(new_config)
    
    # Keep old keys for backward compatibility (marked as deprecated)
    merged["AUTO_PRUNE_MIN_RATE_DEPRECATED"] = old_config.get("AUTO_PRUNE_MIN_RATE", 40.0)
    merged["AUTO_ADD_MIN_RATE_DEPRECATED"] = old_config.get("AUTO_ADD_MIN_RATE", 50.0)
    
    # Remove old keys (they're now in deprecated versions)
    if "AUTO_PRUNE_MIN_RATE" in merged:
        del merged["AUTO_PRUNE_MIN_RATE"]
    if "AUTO_ADD_MIN_RATE" in merged:
        del merged["AUTO_ADD_MIN_RATE"]
    
    print_success("Configurations merged successfully")
    
    return merged


def validate_config(config):
    """
    Validate the new configuration structure.
    
    Args:
        config: Configuration to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    print_info("Validating new configuration...")
    
    errors = []
    
    # Check required structures exist
    if "lo_config" not in config:
        errors.append("Missing 'lo_config' structure")
    else:
        lo_config = config["lo_config"]
        if "remove_threshold" not in lo_config:
            errors.append("Missing 'lo_config.remove_threshold'")
        if "add_threshold" not in lo_config:
            errors.append("Missing 'lo_config.add_threshold'")
        if "enable_threshold" not in lo_config:
            errors.append("Missing 'lo_config.enable_threshold'")
    
    if "de_config" not in config:
        errors.append("Missing 'de_config' structure")
    else:
        de_config = config["de_config"]
        if "remove_threshold" not in de_config:
            errors.append("Missing 'de_config.remove_threshold'")
        if "add_threshold" not in de_config:
            errors.append("Missing 'de_config.add_threshold'")
        if "enable_threshold" not in de_config:
            errors.append("Missing 'de_config.enable_threshold'")
    
    # Check deprecated keys exist
    if "AUTO_PRUNE_MIN_RATE_DEPRECATED" not in config:
        errors.append("Missing 'AUTO_PRUNE_MIN_RATE_DEPRECATED' (backward compatibility)")
    if "AUTO_ADD_MIN_RATE_DEPRECATED" not in config:
        errors.append("Missing 'AUTO_ADD_MIN_RATE_DEPRECATED' (backward compatibility)")
    
    # Check old keys are removed
    if "AUTO_PRUNE_MIN_RATE" in config:
        errors.append("Old key 'AUTO_PRUNE_MIN_RATE' should be removed")
    if "AUTO_ADD_MIN_RATE" in config:
        errors.append("Old key 'AUTO_ADD_MIN_RATE' should be removed")
    
    # Validate threshold values
    if "lo_config" in config:
        lo_config = config["lo_config"]
        if lo_config.get("add_threshold", 0) < lo_config.get("remove_threshold", 0):
            errors.append("lo_config: add_threshold should be >= remove_threshold")
        if lo_config.get("remove_threshold", 0) < lo_config.get("enable_threshold", 0):
            errors.append("lo_config: remove_threshold should be >= enable_threshold")
    
    if "de_config" in config:
        de_config = config["de_config"]
        if de_config.get("add_threshold", 0) < de_config.get("remove_threshold", 0):
            errors.append("de_config: add_threshold should be >= remove_threshold")
        if de_config.get("remove_threshold", 0) < de_config.get("enable_threshold", 0):
            errors.append("de_config: remove_threshold should be >= enable_threshold")
    
    if errors:
        print_error("Validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print_success("Validation passed")
    return True


def write_config(config_path, config):
    """
    Write the new configuration to file.
    
    Args:
        config_path: Path to the config file
        config: Configuration to write
    """
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print_success(f"Configuration written to: {config_path}")
    except Exception as e:
        print_error(f"Failed to write config file: {e}")
        sys.exit(1)


def print_migration_summary(old_values, new_config):
    """Print a summary of the migration."""
    print_header("MIGRATION SUMMARY")
    
    print("\n📊 Old Configuration (V7):")
    print(f"  AUTO_PRUNE_MIN_RATE: {old_values['AUTO_PRUNE_MIN_RATE']}%")
    print(f"  AUTO_ADD_MIN_RATE: {old_values['AUTO_ADD_MIN_RATE']}%")
    
    print("\n📊 New Configuration (V8 - Dual-Config):")
    print(f"  Lo Config (2-digit bridges):")
    print(f"    - Remove Threshold: {new_config['lo_config']['remove_threshold']}%")
    print(f"    - Add Threshold: {new_config['lo_config']['add_threshold']}%")
    print(f"    - Enable Threshold: {new_config['lo_config']['enable_threshold']}%")
    print(f"  De Config (1-digit bridges):")
    print(f"    - Remove Threshold: {new_config['de_config']['remove_threshold']}%")
    print(f"    - Add Threshold: {new_config['de_config']['add_threshold']}%")
    print(f"    - Enable Threshold: {new_config['de_config']['enable_threshold']}%")
    
    print("\n✨ Benefits:")
    print("  ✓ Independent optimization thresholds for Lo and De bridges")
    print("  ✓ More granular control over bridge management")
    print("  ✓ Backward compatibility with deprecated keys")
    print("  ✓ Self-healing configuration structure")


def main():
    """Main migration function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate config.json to V8 Dual-Config architecture"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a backup of config.json before migration"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompts"
    )
    
    args = parser.parse_args()
    
    print_header("CONFIG MIGRATION V8 - DUAL-CONFIG ARCHITECTURE (LO/DE)")
    
    # 1. Read current config
    config_path = CONFIG_FILE
    if not os.path.exists(config_path):
        print_error(f"Config file not found: {config_path}")
        print_info("Please ensure config.json exists in the project root")
        sys.exit(1)
    
    current_config = read_config(config_path)
    
    # 2. Check if already migrated
    if "lo_config" in current_config and "de_config" in current_config:
        print_warning("Configuration already appears to be migrated to V8")
        print_info("Existing lo_config and de_config found")
        if not args.force:
            response = input("\nDo you want to re-migrate? (y/N): ").strip().lower()
            if response != 'y':
                print_info("Migration cancelled")
                sys.exit(0)
    
    # 3. Extract old values
    old_values = extract_old_values(current_config)
    
    # 4. Create dual-config structure
    new_config = create_dual_config(old_values)
    
    # 5. Merge configurations
    merged_config = merge_configs(current_config, new_config)
    
    # 6. Validate new config
    if not validate_config(merged_config):
        print_error("Configuration validation failed")
        sys.exit(1)
    
    # 7. Print summary
    print_migration_summary(old_values, new_config)
    
    # 8. Dry run check
    if args.dry_run:
        print_header("DRY RUN - NO CHANGES MADE")
        print("\nNew configuration preview:")
        print(json.dumps(merged_config, indent=4, ensure_ascii=False))
        print_info("Run without --dry-run to apply changes")
        sys.exit(0)
    
    # 9. Confirmation
    if not args.force:
        print("\n" + "=" * 80)
        response = input("Proceed with migration? (y/N): ").strip().lower()
        if response != 'y':
            print_info("Migration cancelled")
            sys.exit(0)
    
    # 10. Create backup if requested
    if args.backup:
        create_backup(config_path)
    
    # 11. Write new config
    write_config(config_path, merged_config)
    
    # 12. Final success message
    print_header("MIGRATION COMPLETE ✅")
    print("\n✅ Config file successfully migrated to V8 Dual-Config architecture")
    print(f"✅ File updated: {config_path}")
    if args.backup:
        print(f"✅ Backup saved in: {BACKUP_DIR}/")
    
    print("\n📝 Next Steps:")
    print("  1. Review the updated config.json")
    print("  2. Update code to use lo_config/de_config structures")
    print("  3. Test bridge management with new thresholds")
    print("  4. Remove deprecated keys after code migration is complete")
    
    print("\n⚠️  Notes:")
    print("  - Old keys preserved as *_DEPRECATED for backward compatibility")
    print("  - You can now set different thresholds for Lo and De bridges")
    print("  - Update your code to read from lo_config and de_config")


if __name__ == "__main__":
    main()
