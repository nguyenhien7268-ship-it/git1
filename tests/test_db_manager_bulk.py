# tests/test_db_manager_bulk.py
"""
Unit tests for bulk DB operations in db_manager.py (V11.2 K1N-primary flow).

Tests:
- get_all_managed_bridge_names()
- bulk_upsert_managed_bridges()
- update_managed_bridges_batch()
- delete_managed_bridges_batch()
- Atomic transactions and rollback behavior
"""

import pytest
import sqlite3
import tempfile
import os

from logic.db_manager import (
    setup_database,
    get_all_managed_bridge_names,
    bulk_upsert_managed_bridges,
    update_managed_bridges_batch,
    delete_managed_bridges_batch
)


@pytest.fixture
def temp_db_bulk():
    """Create temporary test database with schema"""
    fd, path = tempfile.mkstemp(suffix=".db")
    conn, cursor = setup_database(path)
    
    yield conn, cursor, path
    
    # Cleanup
    try:
        conn.close()
    except:
        pass
    os.close(fd)
    
    import time
    time.sleep(0.1)
    try:
        if os.path.exists(path):
            os.unlink(path)
    except Exception:
        pass


class TestGetAllManagedBridgeNames:
    """Test get_all_managed_bridge_names function."""
    
    def test_returns_empty_set_for_empty_db(self, temp_db_bulk):
        """Test returns empty set when no bridges exist."""
        conn, cursor, db_path = temp_db_bulk
        
        names = get_all_managed_bridge_names(db_path)
        
        assert isinstance(names, set)
        assert len(names) == 0
    
    def test_returns_normalized_names(self, temp_db_bulk):
        """Test returns normalized bridge names."""
        conn, cursor, db_path = temp_db_bulk
        
        # Insert test bridges
        cursor.execute(
            "INSERT INTO ManagedBridges (name, description) VALUES (?, ?)",
            ("Test Bridge 1", "Description 1")
        )
        cursor.execute(
            "INSERT INTO ManagedBridges (name, description) VALUES (?, ?)",
            ("Cầu Đẹp-01", "Description 2")
        )
        conn.commit()
        
        names = get_all_managed_bridge_names(db_path)
        
        assert len(names) == 2
        # Names should be normalized (lowercase, no special chars)
        assert "testbridge1" in names
        assert "caudep01" in names
    
    def test_handles_duplicate_names(self, temp_db_bulk):
        """Test handles duplicate names correctly."""
        conn, cursor, db_path = temp_db_bulk
        
        # Insert bridges with similar names
        cursor.execute(
            "INSERT INTO ManagedBridges (name, description) VALUES (?, ?)",
            ("Bridge-01", "Description 1")
        )
        cursor.execute(
            "INSERT INTO ManagedBridges (name, description) VALUES (?, ?)",
            ("Bridge 01", "Description 2")
        )
        conn.commit()
        
        names = get_all_managed_bridge_names(db_path)
        
        # Both should normalize to same value, so set contains 1 item
        assert "bridge01" in names


class TestBulkUpsertManagedBridges:
    """Test bulk_upsert_managed_bridges function."""
    
    def test_insert_new_bridges(self, temp_db_bulk):
        """Test inserting new bridges."""
        conn, cursor, db_path = temp_db_bulk
        
        bridges = [
            {
                'name': 'Bridge-01',
                'description': 'Test bridge 1',
                'type': 'DE_DYN',
                'k1n_rate_de': 95.5,
                'k2n_rate_de': 88.0,
            },
            {
                'name': 'Bridge-02',
                'description': 'Test bridge 2',
                'type': 'LO_V16',
                'k1n_rate_lo': 87.3,
                'k2n_rate_lo': 82.1,
            }
        ]
        
        result = bulk_upsert_managed_bridges(bridges, db_path)
        
        assert result['added'] == 2
        assert result['updated'] == 0
        assert result['skipped'] == 0
        assert result['errors'] == 0
        
        # Verify in DB
        cursor.execute("SELECT name, k1n_rate_de, k1n_rate_lo FROM ManagedBridges ORDER BY name")
        rows = cursor.fetchall()
        assert len(rows) == 2
        assert rows[0][0] == 'Bridge-01'
        assert rows[0][1] == 95.5  # k1n_rate_de
        assert rows[1][0] == 'Bridge-02'
        assert rows[1][2] == 87.3  # k1n_rate_lo
    
    def test_update_existing_bridges(self, temp_db_bulk):
        """Test updating existing bridges."""
        conn, cursor, db_path = temp_db_bulk
        
        # Insert initial bridge
        cursor.execute(
            "INSERT INTO ManagedBridges (name, description, type) VALUES (?, ?, ?)",
            ("Bridge-01", "Original description", "DE_DYN")
        )
        conn.commit()
        
        # Update with new data
        bridges = [
            {
                'name': 'Bridge-01',
                'description': 'Updated description',
                'k1n_rate_de': 92.0,
            }
        ]
        
        result = bulk_upsert_managed_bridges(bridges, db_path)
        
        assert result['added'] == 0
        assert result['updated'] == 1
        assert result['skipped'] == 0
        
        # Verify update
        cursor.execute("SELECT description, k1n_rate_de FROM ManagedBridges WHERE name=?", ("Bridge-01",))
        row = cursor.fetchone()
        assert row[0] == 'Updated description'
        assert row[1] == 92.0
    
    def test_mixed_insert_and_update(self, temp_db_bulk):
        """Test mix of inserts and updates."""
        conn, cursor, db_path = temp_db_bulk
        
        # Insert initial bridge
        cursor.execute(
            "INSERT INTO ManagedBridges (name, description) VALUES (?, ?)",
            ("Existing-Bridge", "Old data")
        )
        conn.commit()
        
        # Mix of new and existing
        bridges = [
            {'name': 'Existing-Bridge', 'k1n_rate_de': 90.0},  # Update
            {'name': 'New-Bridge', 'k1n_rate_lo': 85.0},        # Insert
        ]
        
        result = bulk_upsert_managed_bridges(bridges, db_path)
        
        assert result['added'] == 1
        assert result['updated'] == 1
        assert result['skipped'] == 0
    
    def test_skips_bridges_without_name(self, temp_db_bulk):
        """Test skips bridges with missing name."""
        conn, cursor, db_path = temp_db_bulk
        
        bridges = [
            {'name': 'Valid-Bridge', 'k1n_rate_de': 90.0},
            {'description': 'No name provided'},  # Missing name
            {'name': '', 'description': 'Empty name'},  # Empty name
        ]
        
        result = bulk_upsert_managed_bridges(bridges, db_path)
        
        assert result['added'] == 1
        assert result['skipped'] == 2
    
    def test_transactional_mode(self, temp_db_bulk):
        """Test transactional mode commits all or nothing."""
        conn, cursor, db_path = temp_db_bulk
        
        bridges = [
            {'name': 'Bridge-01', 'k1n_rate_de': 90.0},
            {'name': 'Bridge-02', 'k1n_rate_lo': 85.0},
        ]
        
        result = bulk_upsert_managed_bridges(bridges, db_path, transactional=True)
        
        assert result['added'] == 2
        
        # Verify both were committed
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges")
        count = cursor.fetchone()[0]
        assert count == 2
    
    def test_handles_empty_list(self, temp_db_bulk):
        """Test handles empty bridge list."""
        conn, cursor, db_path = temp_db_bulk
        
        result = bulk_upsert_managed_bridges([], db_path)
        
        assert result['added'] == 0
        assert result['updated'] == 0
        assert result['skipped'] == 0


class TestUpdateManagedBridgesBatch:
    """Test update_managed_bridges_batch function."""
    
    def test_update_multiple_bridges(self, temp_db_bulk):
        """Test updating multiple bridges."""
        conn, cursor, db_path = temp_db_bulk
        
        # Insert test bridges
        cursor.execute(
            "INSERT INTO ManagedBridges (name, is_enabled, is_pending) VALUES (?, ?, ?)",
            ("Bridge-01", 0, 1)
        )
        cursor.execute(
            "INSERT INTO ManagedBridges (name, is_enabled, is_pending) VALUES (?, ?, ?)",
            ("Bridge-02", 0, 1)
        )
        conn.commit()
        
        # Update both
        updates = [
            {'name': 'Bridge-01', 'is_enabled': 1, 'is_pending': 0},
            {'name': 'Bridge-02', 'is_enabled': 1, 'k1n_rate_lo': 88.0},
        ]
        
        result = update_managed_bridges_batch(updates, db_path)
        
        assert result['updated'] == 2
        assert result['skipped'] == 0
        
        # Verify updates
        cursor.execute("SELECT is_enabled, is_pending FROM ManagedBridges WHERE name=?", ("Bridge-01",))
        row = cursor.fetchone()
        assert row[0] == 1
        assert row[1] == 0
    
    def test_skips_nonexistent_bridges(self, temp_db_bulk):
        """Test skips bridges that don't exist."""
        conn, cursor, db_path = temp_db_bulk
        
        updates = [
            {'name': 'Nonexistent-Bridge', 'is_enabled': 1},
        ]
        
        result = update_managed_bridges_batch(updates, db_path)
        
        assert result['updated'] == 0
        assert result['skipped'] == 1
    
    def test_handles_empty_updates(self, temp_db_bulk):
        """Test handles empty update list."""
        conn, cursor, db_path = temp_db_bulk
        
        result = update_managed_bridges_batch([], db_path)
        
        assert result['updated'] == 0
        assert result['skipped'] == 0


class TestDeleteManagedBridgesBatch:
    """Test delete_managed_bridges_batch function."""
    
    def test_delete_multiple_bridges(self, temp_db_bulk):
        """Test deleting multiple bridges."""
        conn, cursor, db_path = temp_db_bulk
        
        # Insert test bridges
        cursor.execute("INSERT INTO ManagedBridges (name) VALUES (?)", ("Bridge-01",))
        cursor.execute("INSERT INTO ManagedBridges (name) VALUES (?)", ("Bridge-02",))
        cursor.execute("INSERT INTO ManagedBridges (name) VALUES (?)", ("Bridge-03",))
        conn.commit()
        
        # Delete two
        names = ['Bridge-01', 'Bridge-02']
        result = delete_managed_bridges_batch(names, db_path)
        
        assert result['deleted'] == 2
        assert result['errors'] == 0
        
        # Verify only one remains
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges")
        count = cursor.fetchone()[0]
        assert count == 1
        
        cursor.execute("SELECT name FROM ManagedBridges")
        remaining = cursor.fetchone()[0]
        assert remaining == 'Bridge-03'
    
    def test_handles_empty_list(self, temp_db_bulk):
        """Test handles empty name list."""
        conn, cursor, db_path = temp_db_bulk
        
        result = delete_managed_bridges_batch([], db_path)
        
        assert result['deleted'] == 0
    
    def test_handles_nonexistent_names(self, temp_db_bulk):
        """Test handles names that don't exist."""
        conn, cursor, db_path = temp_db_bulk
        
        names = ['Nonexistent-01', 'Nonexistent-02']
        result = delete_managed_bridges_batch(names, db_path)
        
        # Should not error, just report 0 deleted
        assert result['deleted'] == 0
        assert result['errors'] == 0


class TestAtomicTransactions:
    """Test atomic transaction behavior."""
    
    def test_migration_is_idempotent(self, temp_db_bulk):
        """Test that running setup_database multiple times is safe."""
        conn, cursor, db_path = temp_db_bulk
        
        # Run setup again (should not error)
        conn2, cursor2 = setup_database(db_path)
        
        # Verify columns exist
        cursor2.execute("PRAGMA table_info(ManagedBridges)")
        columns = [row[1] for row in cursor2.fetchall()]
        
        assert 'k1n_rate_lo' in columns
        assert 'k1n_rate_de' in columns
        assert 'k2n_rate_lo' in columns
        assert 'k2n_rate_de' in columns
        assert 'is_pending' in columns
        assert 'imported_at' in columns
        
        conn2.close()
    
    def test_bulk_upsert_maintains_consistency(self, temp_db_bulk):
        """Test bulk upsert maintains data consistency."""
        conn, cursor, db_path = temp_db_bulk
        
        # Insert initial data
        bridges = [
            {'name': 'Bridge-01', 'k1n_rate_de': 90.0},
            {'name': 'Bridge-02', 'k1n_rate_lo': 85.0},
        ]
        
        result1 = bulk_upsert_managed_bridges(bridges, db_path, transactional=True)
        assert result1['added'] == 2
        
        # Update same data
        bridges[0]['k1n_rate_de'] = 95.0  # Update Bridge-01
        
        result2 = bulk_upsert_managed_bridges(bridges, db_path, transactional=True)
        assert result2['updated'] == 2  # Both should be updates now
        
        # Verify final state
        cursor.execute("SELECT k1n_rate_de FROM ManagedBridges WHERE name='Bridge-01'")
        rate = cursor.fetchone()[0]
        assert rate == 95.0
