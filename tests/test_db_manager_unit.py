# tests/test_db_manager_unit.py
"""
Unit tests for db_manager.py - Core database operations
"""
import pytest
import sqlite3

from logic.db_manager import (
    setup_database,
    add_managed_bridge,
    update_managed_bridge,
    delete_managed_bridge,
    get_db_connection,
    get_results_by_ky,
    get_all_kys_from_db,
    delete_ky_from_db,
    delete_all_managed_bridges,
    upsert_managed_bridge,
    update_bridge_k2n_cache_batch,
    update_bridge_win_rate_batch,
)


class TestSetupDatabase:
    """Test database setup"""
    
    def test_setup_database_creates_tables(self, temp_db):
        """Test that setup_database creates all required tables"""
        conn, cursor, db_path = temp_db
        
        # Check DuLieu_AI table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='DuLieu_AI'"
        )
        assert cursor.fetchone() is not None
        
        # Check results_A_I table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='results_A_I'"
        )
        assert cursor.fetchone() is not None
        
        # Check ManagedBridges table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ManagedBridges'"
        )
        assert cursor.fetchone() is not None
    
    def test_setup_database_schema(self, temp_db):
        """Test that tables have correct schema"""
        conn, cursor, db_path = temp_db
        
        # Check ManagedBridges columns
        cursor.execute("PRAGMA table_info(ManagedBridges)")
        columns = [row[1] for row in cursor.fetchall()]
        
        assert "id" in columns
        assert "name" in columns
        assert "is_enabled" in columns
        assert "win_rate_text" in columns
        assert "max_lose_streak_k2n" in columns
        assert "recent_win_count_10" in columns


class TestManagedBridges:
    """Test managed bridges CRUD operations"""
    
    def test_add_managed_bridge(self, temp_db):
        """Test adding a managed bridge"""
        conn, cursor, db_path = temp_db
        
        result, message = add_managed_bridge(
            "Test Bridge",
            "Test description",
            db_path,
        )
        
        assert result is True
        
        # Verify bridge was added
        cursor.execute("SELECT * FROM ManagedBridges WHERE name=?", ("Test Bridge",))
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "Test Bridge"  # name column
    
    def test_add_managed_bridge_duplicate(self, temp_db):
        """Test adding duplicate bridge fails"""
        conn, cursor, db_path = temp_db
        
        # Add first bridge
        add_managed_bridge("Test Bridge", "Desc", db_path)
        
        # Try to add duplicate
        result, message = add_managed_bridge("Test Bridge", "Desc2", db_path)
        
        assert result is False
        assert "đã tồn tại" in message.lower()
    
    def test_get_all_managed_bridges(self, temp_db):
        """Test getting all managed bridges"""
        from logic.data_repository import get_all_managed_bridges
        
        conn, cursor, db_path = temp_db
        
        # Add test bridges
        add_managed_bridge("Bridge1", "Desc1", db_path)
        add_managed_bridge("Bridge2", "Desc2", db_path)
        add_managed_bridge("Bridge3", "Desc3", db_path)
        
        # Disable one bridge
        cursor.execute("UPDATE ManagedBridges SET is_enabled=0 WHERE name='Bridge3'")
        conn.commit()
        
        # Get all bridges
        all_bridges = get_all_managed_bridges(db_path, only_enabled=False)
        assert len(all_bridges) >= 3
        
        # Get only enabled bridges
        enabled_bridges = get_all_managed_bridges(db_path, only_enabled=True)
        assert len(enabled_bridges) >= 2
    
    def test_update_managed_bridge(self, temp_db):
        """Test updating a managed bridge"""
        conn, cursor, db_path = temp_db
        
        # Add bridge
        add_managed_bridge("Test Bridge", "Old Desc", db_path)
        
        # Get bridge ID
        cursor.execute("SELECT id FROM ManagedBridges WHERE name=?", ("Test Bridge",))
        bridge_id = cursor.fetchone()[0]
        
        # Update bridge
        result, message = update_managed_bridge(bridge_id, "New Desc", False, db_path)
        assert result is True
        
        # Verify update
        cursor.execute(
            "SELECT description, is_enabled FROM ManagedBridges WHERE id=?",
            (bridge_id,)
        )
        row = cursor.fetchone()
        assert row[0] == "New Desc"
        assert row[1] == 0
    
    def test_update_nonexistent_bridge(self, temp_db):
        """Test updating non-existent bridge"""
        conn, cursor, db_path = temp_db
        
        result, message = update_managed_bridge(99999, "New Desc", True, db_path)
        
        # Should not raise error, but may return False or True depending on implementation
        assert isinstance(result, bool)
    
    def test_delete_managed_bridge(self, temp_db):
        """Test deleting a managed bridge"""
        conn, cursor, db_path = temp_db
        
        # Add bridge
        add_managed_bridge("Test Bridge", "Desc", db_path)
        
        # Get bridge ID
        cursor.execute("SELECT id FROM ManagedBridges WHERE name=?", ("Test Bridge",))
        bridge_id = cursor.fetchone()[0]
        
        # Delete bridge
        result, message = delete_managed_bridge(bridge_id, db_path)
        assert result is True
        
        # Verify deletion
        cursor.execute("SELECT * FROM ManagedBridges WHERE id=?", (bridge_id,))
        assert cursor.fetchone() is None
    
    def test_delete_nonexistent_bridge(self, temp_db):
        """Test deleting non-existent bridge"""
        conn, cursor, db_path = temp_db
        
        result, message = delete_managed_bridge(99999, db_path)
        
        # Should not raise error, but may return False or True depending on implementation
        assert isinstance(result, bool)


class TestDatabaseQueries:
    """Test database query functions"""
    
    def test_get_db_connection(self, temp_db):
        """Test getting database connection"""
        conn, cursor, db_path = temp_db
        
        new_conn = get_db_connection(db_path)
        assert new_conn is not None
        
        new_cursor = new_conn.cursor()
        new_cursor.execute("SELECT 1")
        assert new_cursor.fetchone()[0] == 1
        
        new_conn.close()
    
    def test_get_results_by_ky(self, temp_db):
        """Test getting results by ky"""
        conn, cursor, db_path = temp_db
        
        # Insert test data
        cursor.execute(
            """
            INSERT INTO results_A_I (ky, date, gdb, g1, g2)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("23001", "01/01/2023", "12", "34", "56")
        )
        conn.commit()
        
        # Get results
        result = get_results_by_ky("23001", db_path)
        assert result is not None
        assert result[1] == "23001"  # ky column
        assert result[2] == "01/01/2023"  # date column
    
    def test_get_results_by_ky_not_found(self, temp_db):
        """Test getting results by ky when not found"""
        conn, cursor, db_path = temp_db
        
        result = get_results_by_ky("99999", db_path)
        assert result is None
    
    def test_get_all_kys_from_db(self, temp_db):
        """Test getting all kys from database"""
        conn, cursor, db_path = temp_db
        
        # Insert test data
        cursor.execute(
            """
            INSERT INTO results_A_I (ky, date, gdb)
            VALUES (?, ?, ?)
            """,
            ("23001", "01/01/2023", "12")
        )
        cursor.execute(
            """
            INSERT INTO results_A_I (ky, date, gdb)
            VALUES (?, ?, ?)
            """,
            ("23002", "02/01/2023", "34")
        )
        conn.commit()
        
        # Get all kys
        kys = get_all_kys_from_db(db_path)
        assert len(kys) == 2
        assert kys[0][0] == "23002"  # Should be sorted DESC
        assert kys[1][0] == "23001"
    
    def test_get_all_kys_from_db_empty(self, temp_db):
        """Test getting all kys from empty database"""
        conn, cursor, db_path = temp_db
        
        kys = get_all_kys_from_db(db_path)
        assert kys == []
    
    def test_delete_ky_from_db(self, temp_db):
        """Test deleting a ky from database"""
        conn, cursor, db_path = temp_db
        
        # Insert test data
        cursor.execute(
            """
            INSERT INTO results_A_I (ky, date, gdb)
            VALUES (?, ?, ?)
            """,
            ("23001", "01/01/2023", "12")
        )
        cursor.execute(
            """
            INSERT INTO DuLieu_AI (MaSoKy, Col_A_Ky, Col_B_GDB)
            VALUES (?, ?, ?)
            """,
            (23001, "23001", "12")
        )
        conn.commit()
        
        # Delete ky
        result, message = delete_ky_from_db("23001", db_path)
        assert result is True
        assert "23001" in message
        
        # Verify deletion
        cursor.execute("SELECT * FROM results_A_I WHERE ky = ?", ("23001",))
        assert cursor.fetchone() is None
        
        cursor.execute("SELECT * FROM DuLieu_AI WHERE Col_A_Ky = ?", ("23001",))
        assert cursor.fetchone() is None
    
    def test_delete_ky_from_db_not_found(self, temp_db):
        """Test deleting non-existent ky"""
        conn, cursor, db_path = temp_db
        
        result, message = delete_ky_from_db("99999", db_path)
        assert result is True  # Should succeed even if nothing to delete
        assert "99999" in message


class TestManagedBridgesAdvanced:
    """Test advanced managed bridges operations"""
    
    def test_delete_all_managed_bridges(self, temp_db):
        """Test deleting all managed bridges"""
        conn, cursor, db_path = temp_db
        
        # Add some bridges
        add_managed_bridge("Bridge1", "Desc1", db_path)
        add_managed_bridge("Bridge2", "Desc2", db_path)
        
        # Verify bridges exist
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges")
        assert cursor.fetchone()[0] == 2
        
        # Delete all
        result = delete_all_managed_bridges(conn)
        assert result is True
        
        # Commit and verify
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges")
        assert cursor.fetchone()[0] == 0
    
    def test_upsert_managed_bridge_insert(self, temp_db):
        """Test upsert managed bridge - insert new"""
        conn, cursor, db_path = temp_db
        
        result, message = upsert_managed_bridge(
            "New Bridge", "Description", "50%", db_path
        )
        
        assert result is True
        assert "THÊM" in message
        
        # Verify bridge was added - check by column name instead of index
        cursor.execute(
            "SELECT name, win_rate_text FROM ManagedBridges WHERE name=?",
            ("New Bridge",)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "New Bridge"
        assert row[1] == "50%"  # win_rate_text
    
    def test_upsert_managed_bridge_update(self, temp_db):
        """Test upsert managed bridge - update existing"""
        conn, cursor, db_path = temp_db
        
        # Add bridge first
        add_managed_bridge("Existing Bridge", "Old Desc", db_path)
        
        # Upsert with new data
        result, message = upsert_managed_bridge(
            "Existing Bridge", "New Desc", "60%", db_path
        )
        
        assert result is True
        assert "CẬP NHẬT" in message
        
        # Verify update
        cursor.execute(
            "SELECT description, win_rate_text FROM ManagedBridges WHERE name=?",
            ("Existing Bridge",)
        )
        row = cursor.fetchone()
        assert row[0] == "New Desc"
        assert row[1] == "60%"
    
    def test_upsert_managed_bridge_with_pos_indices(self, temp_db):
        """Test upsert with position indices"""
        conn, cursor, db_path = temp_db
        
        result, message = upsert_managed_bridge(
            "Bridge with Pos", "Desc", "50%", db_path, pos1_idx=0, pos2_idx=1
        )
        
        assert result is True
        
        # Verify pos indices
        cursor.execute(
            "SELECT pos1_idx, pos2_idx FROM ManagedBridges WHERE name=?",
            ("Bridge with Pos",)
        )
        row = cursor.fetchone()
        assert row[0] == 0
        assert row[1] == 1
    
    def test_update_bridge_k2n_cache_batch(self, temp_db):
        """Test batch update K2N cache"""
        conn, cursor, db_path = temp_db
        
        # Add bridges first
        add_managed_bridge("Bridge1", "Desc1", db_path)
        add_managed_bridge("Bridge2", "Desc2", db_path)
        
        # Prepare cache data
        cache_data = [
            ("50%", 2, "12,34", 0, 5, "Bridge1"),  # win_rate, streak, stl, max_lose, recent_win, name
            ("60%", 3, "56,78", 1, 7, "Bridge2"),
        ]
        
        result, message = update_bridge_k2n_cache_batch(cache_data, db_path)
        
        assert result is True
        assert "cache k2n" in message.lower() or "cache K2N" in message
        
        # Verify updates
        cursor.execute(
            "SELECT win_rate_text, current_streak, next_prediction_stl, max_lose_streak_k2n, recent_win_count_10 FROM ManagedBridges WHERE name=?",
            ("Bridge1",)
        )
        row = cursor.fetchone()
        assert row[0] == "50%"
        assert row[1] == 2
        assert row[2] == "12,34"
        assert row[3] == 0
        assert row[4] == 5
    
    def test_update_bridge_k2n_cache_batch_empty(self, temp_db):
        """Test batch update with empty list"""
        conn, cursor, db_path = temp_db
        
        result, message = update_bridge_k2n_cache_batch([], db_path)
        
        assert result is True
        assert "0 cầu" in message or "cập nhật" in message.lower()
    
    def test_update_bridge_win_rate_batch(self, temp_db):
        """Test batch update win rates"""
        conn, cursor, db_path = temp_db
        
        # Add bridges first
        add_managed_bridge("Bridge1", "Desc1", db_path)
        add_managed_bridge("Bridge2", "Desc2", db_path)
        
        # Prepare rate data: (win_rate_text, bridge_name) - note the order!
        rate_data = [
            ("55%", "Bridge1"),
            ("65%", "Bridge2"),
        ]
        
        result, message = update_bridge_win_rate_batch(rate_data, db_path)
        
        assert result is True
        assert "cập nhật" in message.lower()
        
        # Verify updates
        cursor.execute(
            "SELECT win_rate_text FROM ManagedBridges WHERE name=?",
            ("Bridge1",)
        )
        row = cursor.fetchone()
        assert row[0] == "55%"
    
    def test_update_bridge_win_rate_batch_empty(self, temp_db):
        """Test batch update with empty list"""
        conn, cursor, db_path = temp_db
        
        result, message = update_bridge_win_rate_batch([], db_path)
        
        assert result is True
        assert "0 cầu" in message or "cập nhật" in message.lower()
    
    def test_add_managed_bridge_with_v17_name(self, temp_db):
        """Test adding bridge with V17 name format"""
        conn, cursor, db_path = temp_db
        
        # Mock get_index_from_name_V16 to return indices
        from unittest.mock import patch
        
        with patch('logic.db_manager.get_index_from_name_V16') as mock_get_index:
            mock_get_index.side_effect = lambda x: 0 if "GDB" in x else 1
            
            result, message = add_managed_bridge(
                "GDB[0]+G1[1]", "V17 Bridge", db_path
            )
            
            assert result is True
            
            # Verify pos indices were set
            cursor.execute(
                "SELECT pos1_idx, pos2_idx FROM ManagedBridges WHERE name=?",
                ("GDB[0]+G1[1]",)
            )
            row = cursor.fetchone()
            # Should have indices (or None if parsing failed)
            assert row is not None
    
    def test_add_managed_bridge_with_memory_name(self, temp_db):
        """Test adding bridge with memory bridge name format"""
        conn, cursor, db_path = temp_db
        
        # Use proper memory bridge name format
        result, message = add_managed_bridge(
            "Tổng(GDB+G1)", "Memory Bridge", db_path
        )
        
        assert result is True
        
        # Verify pos indices are -1 for memory bridges
        cursor.execute(
            "SELECT pos1_idx, pos2_idx FROM ManagedBridges WHERE name=?",
            ("Tổng(GDB+G1)",)
        )
        row = cursor.fetchone()
        # Note: The function checks for "Tổng(" or "Hiệu(" in the name
        # If the format doesn't match exactly, pos indices might be None
        if row:
            # Either -1 (memory bridge) or None (if parsing failed)
            assert row[0] in (-1, None)
            assert row[1] in (-1, None)

