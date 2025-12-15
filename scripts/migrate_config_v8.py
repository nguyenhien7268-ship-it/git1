#!/usr/bin/env python3
# scripts/migrate_config_v8.py
"""
Migration script for Config V8 - Dual-Config Architecture (Lô/Đề)

This script migrates the old config.json structure to the new dual-config format:
- Maps AUTO_PRUNE_MIN_RATE -> lo_config['remove_threshold']
- Maps AUTO_ADD_MIN_RATE -> lo_config['add_threshold']
- Creates safe defaults for de_config
"""

import json
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CONFIG_FILE = "config.json"
BACKUP_DIR = "backups"

# Safe defaults for Đề config (more conservative thresholds)
DEFAULT_DE_CONFIG = {
    "remove_threshold": 80.0,  # Tắt cầu Đề khi tỷ lệ < 80%
    "add_threshold": 88.0,      # Bật lại cầu Đề khi tỷ lệ >= 88%
}

# Default Lô config (will be populated from old settings)
DEFAULT_LO_CONFIG = {
    "remove_threshold": 43.0,  # Tắt cầu Lô khi tỷ lệ < 43%
    "add_threshold": 45.0,      # Bật lại cầu Lô khi tỷ lệ >= 45%
}


def create_backup(config_path):
    """
    Create a timestamped backup of the config file.
    
    Args:
        config_path: Path to config.json
        
    Returns:
        str: Path to backup file
    """
    if not os.path.exists(config_path):
        return None
    
    # Create backup directory if not exists
    backup_dir = os.path.join(os.path.dirname(config_path), BACKUP_DIR)
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"config_backup_{timestamp}.json"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    shutil.copy2(config_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    
    return backup_path


def load_config(config_path):
    """
    Load existing config.json.
    
    Args:
        config_path: Path to config.json
        
    Returns:
        dict: Config data or empty dict if file doesn't exist
    """
    if not os.path.exists(config_path):
        print(f"⚠️  Config file not found: {config_path}")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✅ Loaded existing config from: {config_path}")
        return config
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return {}


def migrate_to_dual_config(old_config):
    """
    Migrate old config structure to new dual-config format.
    
    Args:
        old_config: Old config dict
        
    Returns:
        dict: New config with lo_config and de_config
    """
    print("\n🔄 Starting migration to Dual-Config V8...")
    
    # Start with a copy of old config
    new_config = old_config.copy()
    
    # Check if already migrated
    if 'lo_config' in new_config and 'de_config' in new_config:
        print("ℹ️  Config already has dual-config structure. Skipping migration.")
        return new_config
    
    # Extract old threshold values
    old_prune = old_config.get('AUTO_PRUNE_MIN_RATE', DEFAULT_LO_CONFIG['remove_threshold'])
    old_add = old_config.get('AUTO_ADD_MIN_RATE', DEFAULT_LO_CONFIG['add_threshold'])
    
    print(f"  📊 Old AUTO_PRUNE_MIN_RATE: {old_prune}%")
    print(f"  📊 Old AUTO_ADD_MIN_RATE: {old_add}%")
    
    # Create lo_config from old values
    lo_config = {
        "remove_threshold": float(old_prune),
        "add_threshold": float(old_add),
    }
    
    # Create de_config with safe defaults
    de_config = DEFAULT_DE_CONFIG.copy()
    
    # Add dual-config structure to new config
    new_config['lo_config'] = lo_config
    new_config['de_config'] = de_config
    
    # Remove old deprecated keys
    deprecated_keys = ['AUTO_PRUNE_MIN_RATE', 'AUTO_ADD_MIN_RATE']
    for key in deprecated_keys:
        if key in new_config:
            del new_config[key]
            print(f"  🗑️  Removed deprecated key: {key}")
    
    print(f"\n✅ Migration complete:")
    print(f"  📦 lo_config: remove={lo_config['remove_threshold']}%, add={lo_config['add_threshold']}%")
    print(f"  📦 de_config: remove={de_config['remove_threshold']}%, add={de_config['add_threshold']}%")
    
    return new_config


def save_config(config_path, config_data):
    """
    Save config to file with proper formatting.
    
    Args:
        config_path: Path to config.json
        config_data: Config dict to save
        
    Returns:
        bool: Success status
    """
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        print(f"\n✅ Saved new config to: {config_path}")
        return True
    except Exception as e:
        print(f"\n❌ Error saving config: {e}")
        return False


def validate_config(config_data):
    """
    Validate the migrated config structure.
    
    Args:
        config_data: Config dict to validate
        
    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    errors = []
    
    # Check for required keys
    if 'lo_config' not in config_data:
        errors.append("Missing 'lo_config' key")
    else:
        lo_config = config_data['lo_config']
        if 'remove_threshold' not in lo_config:
            errors.append("Missing 'lo_config.remove_threshold'")
        if 'add_threshold' not in lo_config:
            errors.append("Missing 'lo_config.add_threshold'")
        
        # Validate threshold relationship
        if 'remove_threshold' in lo_config and 'add_threshold' in lo_config:
            if lo_config['remove_threshold'] > lo_config['add_threshold']:
                errors.append(f"lo_config: remove_threshold ({lo_config['remove_threshold']}) should be <= add_threshold ({lo_config['add_threshold']})")
    
    if 'de_config' not in config_data:
        errors.append("Missing 'de_config' key")
    else:
        de_config = config_data['de_config']
        if 'remove_threshold' not in de_config:
            errors.append("Missing 'de_config.remove_threshold'")
        if 'add_threshold' not in de_config:
            errors.append("Missing 'de_config.add_threshold'")
        
        # Validate threshold relationship
        if 'remove_threshold' in de_config and 'add_threshold' in de_config:
            if de_config['remove_threshold'] > de_config['add_threshold']:
                errors.append(f"de_config: remove_threshold ({de_config['remove_threshold']}) should be <= add_threshold ({de_config['add_threshold']})")
    
    is_valid = len(errors) == 0
    
    if is_valid:
        print("\n✅ Config validation passed")
    else:
        print("\n❌ Config validation failed:")
        for error in errors:
            print(f"  - {error}")
    
    return is_valid, errors


def main():
    """Main migration function."""
    print("=" * 60)
    print("CONFIG V8 MIGRATION - Dual-Config Architecture (Lô/Đề)")
    print("=" * 60)
    
    # Determine config path
    config_path = os.path.join(PROJECT_ROOT, CONFIG_FILE)
    
    # Load existing config
    old_config = load_config(config_path)
    
    if not old_config:
        print("\n⚠️  No existing config found. Creating new config with defaults...")
        old_config = {}
    else:
        # Create backup
        backup_path = create_backup(config_path)
        if backup_path:
            print(f"  💾 Original config backed up")
    
    # Perform migration
    new_config = migrate_to_dual_config(old_config)
    
    # Validate new config
    is_valid, errors = validate_config(new_config)
    
    if not is_valid:
        print("\n❌ Migration failed validation. Please check errors above.")
        print("  💡 Original config preserved (if backup was created)")
        return False
    
    # Save new config
    success = save_config(config_path, new_config)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ MIGRATION SUCCESSFUL!")
        print("=" * 60)
        print("\n📋 Next steps:")
        print("  1. Review the new config.json structure")
        print("  2. Test the application with the new config")
        print("  3. Adjust thresholds in lo_config/de_config as needed")
        print(f"\n💡 Backup location: {os.path.join(os.path.dirname(config_path), BACKUP_DIR)}")
        return True
    else:
        print("\n❌ Migration failed. Please check errors above.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
