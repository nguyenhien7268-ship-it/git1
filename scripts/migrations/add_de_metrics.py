#!/usr/bin/env python3
"""
Safe migration script to add DE metrics columns and bridge_audit table.
Usage: python scripts/migrations/add_de_metrics.py [--db path/to/db.sqlite]
"""

import argparse
import os
import sqlite3
import sys
from pathlib import Path


def validate_db_path(db_path):
    """Validate that the database file exists."""
    if not os.path.exists(db_path):
        print(f"❌ ERROR: Database file not found: {db_path}")
        return False
    
    if not os.path.isfile(db_path):
        print(f"❌ ERROR: Path is not a file: {db_path}")
        return False
    
    print(f"✓ Database file found: {db_path}")
    return True


def check_table_exists(cursor, table_name):
    """Check if a table exists in the database."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    exists = cursor.fetchone() is not None
    if exists:
        print(f"✓ Table '{table_name}' exists")
    else:
        print(f"⚠ Table '{table_name}' not found")
    return exists


def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def add_column_if_missing(cursor, table_name, column_def):
    """Add a column to a table if it doesn't exist."""
    # Parse column definition to get column name
    column_name = column_def.split()[0]
    
    if check_column_exists(cursor, table_name, column_name):
        print(f"  ⊙ Column '{column_name}' already exists, skipping")
        return False
    
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
        print(f"  ✓ Added column '{column_name}'")
        return True
    except sqlite3.OperationalError as e:
        # Column might already exist (race condition or previous partial migration)
        if "duplicate column name" in str(e).lower():
            print(f"  ⊙ Column '{column_name}' already exists (caught exception)")
            return False
        raise


def create_bridge_audit_table(cursor):
    """Create the bridge_audit table if it doesn't exist."""
    if check_table_exists(cursor, 'bridge_audit'):
        print("  ⊙ Table 'bridge_audit' already exists, skipping")
        return False
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bridge_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bridge_id INTEGER,
            action TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            reason TEXT,
            actor TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    print("  ✓ Created table 'bridge_audit'")
    return True


def create_index_if_missing(cursor, index_name, table_name, column_name):
    """Create an index if it doesn't exist."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,)
    )
    
    if cursor.fetchone() is not None:
        print(f"  ⊙ Index '{index_name}' already exists, skipping")
        return False
    
    cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})")
    print(f"  ✓ Created index '{index_name}'")
    return True


def run_migration(db_path):
    """Run the migration on the specified database."""
    print("\n" + "="*60)
    print("DE METRICS MIGRATION - SAFE EXECUTION")
    print("="*60 + "\n")
    
    # Validate database
    if not validate_db_path(db_path):
        return False
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"✓ Connected to database\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to database: {e}")
        return False
    
    try:
        # Check if ManagedBridges table exists
        print("Step 1: Validate ManagedBridges table")
        if not check_table_exists(cursor, 'ManagedBridges'):
            print("❌ ERROR: 'ManagedBridges' table not found!")
            print("   This migration requires the ManagedBridges table to exist.")
            return False
        print()
        
        # Add DE metric columns
        print("Step 2: Add DE metric columns to ManagedBridges")
        columns_to_add = [
            "de_win_count_last30 INTEGER DEFAULT 0",
            "de_win_rate_last30 REAL DEFAULT 0.0",
            "de_current_streak INTEGER DEFAULT 0",
            "de_score REAL DEFAULT 0.0",
            "de_auto_enabled INTEGER DEFAULT 0",
            "de_manual_override INTEGER DEFAULT 0",
            "de_manual_override_value INTEGER DEFAULT NULL",
            "de_last_evaluated TEXT DEFAULT NULL"
        ]
        
        added_count = 0
        for column_def in columns_to_add:
            if add_column_if_missing(cursor, 'ManagedBridges', column_def):
                added_count += 1
        
        print(f"  → Added {added_count} new column(s)\n")
        
        # Create bridge_audit table
        print("Step 3: Create bridge_audit table")
        if create_bridge_audit_table(cursor):
            print("  → Created bridge_audit table\n")
        else:
            print("  → No action needed\n")
        
        # Create indexes
        print("Step 4: Create indexes")
        idx_added = 0
        if create_index_if_missing(cursor, 'idx_managed_bridges_type', 'ManagedBridges', 'type'):
            idx_added += 1
        if create_index_if_missing(cursor, 'idx_managed_bridges_de_auto', 'ManagedBridges', 'de_auto_enabled'):
            idx_added += 1
        print(f"  → Created {idx_added} new index(es)\n")
        
        # Commit changes
        conn.commit()
        print("✓ Migration completed successfully!")
        print("\n" + "="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: Migration failed: {e}")
        conn.rollback()
        print("   Changes have been rolled back.")
        return False
        
    finally:
        conn.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Add DE metrics columns and bridge_audit table to the database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/migrations/add_de_metrics.py
  python scripts/migrations/add_de_metrics.py --db data/xo_so_prizes_all_logic.db
  
IMPORTANT: Back up your database before running this migration!
        """
    )
    
    parser.add_argument(
        '--db',
        default='data/xo_so_prizes_all_logic.db',
        help='Path to SQLite database file (default: data/xo_so_prizes_all_logic.db)'
    )
    
    args = parser.parse_args()
    
    # Run migration
    success = run_migration(args.db)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
