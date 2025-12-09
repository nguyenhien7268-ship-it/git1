# tests/test_update_de_bridge_performance.py
# Unit tests for update_de_bridge_performance job

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sqlite3
import tempfile
import pytest
from unittest.mock import patch, MagicMock


def create_test_db():
    """Create a minimal test database with ManagedBridges and bridge_audit tables."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create ManagedBridges table
    cursor.execute("""
        CREATE TABLE ManagedBridges (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            current_streak INTEGER DEFAULT 0,
            de_win_count_last30 INTEGER DEFAULT 0,
            de_win_rate_last30 REAL DEFAULT 0.0,
            de_current_streak INTEGER DEFAULT 0,
            de_score REAL DEFAULT 0.0,
            de_auto_enabled INTEGER DEFAULT 0,
            de_manual_override INTEGER DEFAULT 0,
            de_manual_override_value INTEGER DEFAULT NULL,
            de_last_evaluated TEXT DEFAULT NULL,
            is_enabled INTEGER DEFAULT 1
        )
    """)
    
    # Create bridge_audit table
    cursor.execute("""
        CREATE TABLE bridge_audit (
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
    
    # Insert test bridges
    test_bridges = [
        (1, "DE_DYN_Test1", "DE_DYN", 28, 0, 0.0, 0, 0.0, 0, 0, None, None, 1),
        (2, "DE_DYN_Test2", "DE_DYN", 25, 0, 0.0, 0, 0.0, 0, 0, None, None, 1),
        (3, "DE_SET_Test1", "DE_SET", 20, 0, 0.0, 0, 0.0, 0, 0, None, None, 1),
    ]
    
    cursor.executemany("""
        INSERT INTO ManagedBridges (
            id, name, type, current_streak,
            de_win_count_last30, de_win_rate_last30, de_current_streak, de_score,
            de_auto_enabled, de_manual_override, de_manual_override_value,
            de_last_evaluated, is_enabled
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, test_bridges)
    
    conn.commit()
    conn.close()
    
    return db_path


def test_dry_run_mode():
    """Test that dry-run mode does not write to database."""
    db_path = create_test_db()
    
    try:
        # Import job module
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "jobs"))
        from update_de_bridge_performance import get_db_connection, get_de_bridges, process_bridge, load_config
        
        # Connect and get initial state
        conn = get_db_connection(db_path)
        bridges_before = get_de_bridges(conn, limit=1)
        initial_metrics = bridges_before[0]["de_win_count_last30"]
        conn.close()
        
        # Run in dry-run mode
        conn = get_db_connection(db_path)
        config = load_config()
        bridges = get_de_bridges(conn, limit=1)
        
        for bridge in bridges:
            process_bridge(conn, bridge, config, dry_run=True)
        
        conn.close()
        
        # Check that nothing was written
        conn = get_db_connection(db_path)
        bridges_after = get_de_bridges(conn, limit=1)
        final_metrics = bridges_after[0]["de_win_count_last30"]
        conn.close()
        
        assert final_metrics == initial_metrics, "Dry-run should not modify database"
        print("✓ test_dry_run_mode passed")
        
    finally:
        os.unlink(db_path)


def test_actual_update():
    """Test that actual mode updates database."""
    db_path = create_test_db()
    
    try:
        # Import job module
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "jobs"))
        from update_de_bridge_performance import get_db_connection, get_de_bridges, process_bridge, load_config
        
        # Run actual update
        conn = get_db_connection(db_path)
        config = load_config()
        bridges = get_de_bridges(conn, limit=1)
        
        # Process first bridge (DE_DYN with current_streak=28)
        bridge = bridges[0]
        initial_auto = bridge["de_auto_enabled"]
        
        process_bridge(conn, bridge, config, dry_run=False)
        conn.commit()
        
        # Check that it was updated
        cursor = conn.cursor()
        cursor.execute("SELECT de_last_evaluated, de_auto_enabled FROM ManagedBridges WHERE id = ?", (bridge["id"],))
        row = cursor.fetchone()
        
        assert row[0] is not None, "de_last_evaluated should be set"
        # Since we used legacy current_streak=28, de_auto_enabled should be 1
        assert row[1] == 1, f"Expected de_auto_enabled=1 for wins=28, got {row[1]}"
        
        conn.close()
        
        print("✓ test_actual_update passed")
        
    finally:
        os.unlink(db_path)


def test_audit_entry_created():
    """Test that audit entries are created when de_auto_enabled changes."""
    db_path = create_test_db()
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "jobs"))
        from update_de_bridge_performance import get_db_connection, get_de_bridges, process_bridge, load_config
        
        conn = get_db_connection(db_path)
        config = load_config()
        
        # Get bridge with auto_enabled=0 initially
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ManagedBridges WHERE id = 1")
        bridge = dict(zip([d[0] for d in cursor.description], cursor.fetchone()))
        
        # Process it (should enable due to streak=28)
        process_bridge(conn, bridge, config, dry_run=False)
        conn.commit()
        
        # Check audit entry was created
        cursor.execute("SELECT COUNT(*) FROM bridge_audit WHERE bridge_id = ?", (bridge["id"],))
        count = cursor.fetchone()[0]
        
        assert count > 0, "Audit entry should be created when de_auto_enabled changes"
        
        conn.close()
        
        print("✓ test_audit_entry_created passed")
        
    finally:
        os.unlink(db_path)


def test_load_config():
    """Test configuration loading."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "jobs"))
    from update_de_bridge_performance import load_config
    
    config = load_config()
    
    assert "window_kys" in config
    assert "enable_threshold" in config
    assert "disable_threshold" in config
    assert config["enable_threshold"] >= config["disable_threshold"]
    
    print("✓ test_load_config passed")


def test_get_de_bridges():
    """Test getting DE bridges from database."""
    db_path = create_test_db()
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "jobs"))
        from update_de_bridge_performance import get_db_connection, get_de_bridges
        
        conn = get_db_connection(db_path)
        bridges = get_de_bridges(conn)
        
        # Should have 2 DE_DYN bridges (DE_SET is excluded from processing in job)
        de_bridges = [b for b in bridges if b["type"].startswith("DE_")]
        assert len(de_bridges) == 3, f"Expected 3 DE bridges, got {len(de_bridges)}"
        
        # Test limit
        limited = get_de_bridges(conn, limit=1)
        assert len(limited) == 1, "Limit should work"
        
        conn.close()
        
        print("✓ test_get_de_bridges passed")
        
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    # Run tests manually
    test_load_config()
    test_get_de_bridges()
    test_dry_run_mode()
    test_actual_update()
    test_audit_entry_created()
    print("\n✅ All update_de_bridge_performance tests passed!")
