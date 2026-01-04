#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Initialize Phase 3 Meta-Learning Table
Creates the meta_learning_history table for Phase 3 data collection.
"""

import sys
import os
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from logic.db_manager import DB_NAME
    
    print("=" * 60)
    print("INITIALIZING PHASE 3 META-LEARNING TABLE")
    print("=" * 60)
    print(f"\nDatabase: {DB_NAME}")
    
    # Connect to database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create meta_learning_history table
    print("\nCreating meta_learning_history table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meta_learning_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ky TEXT NOT NULL,
            loto TEXT NOT NULL,
            ai_probability REAL,
            manual_score REAL,
            confidence INTEGER,
            vote_count INTEGER,
            recent_form_score REAL DEFAULT 0.0,
            actual_outcome INTEGER,
            decision_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ky, loto)
        )
    """)
    
    # Create index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_meta_learning_ky 
        ON meta_learning_history(ky)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_meta_learning_outcome 
        ON meta_learning_history(actual_outcome)
    """)
    
    conn.commit()
    
    # Verify table was created
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='meta_learning_history'
    """)
    
    if cursor.fetchone():
        print("[OK] Table 'meta_learning_history' created successfully!")
        
        # Check row count
        cursor.execute("SELECT COUNT(*) FROM meta_learning_history")
        count = cursor.fetchone()[0]
        print(f"   Current row count: {count}")
    else:
        print("[ERROR] Failed to create table!")
        sys.exit(1)
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("INITIALIZATION COMPLETE")
    print("=" * 60)
    print("\nPhase 3 is now ready to collect data.")
    print("The data collector will automatically log predictions")
    print("when you run the dashboard analysis.")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
