"""
Unit tests for db_manager.py

Tests database operations, bridge management, and data insertion.
"""

import pytest
import sqlite3
import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the module to test
from logic import db_manager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


class TestSetupDatabase:
    """Tests for setup_database function"""

    def test_setup_database_creates_tables(self, temp_db):
        """Test that setup_database creates all required tables"""
        conn, cursor = db_manager.setup_database(temp_db)

        # Check KyQuay table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='KyQuay'"
        )
        assert cursor.fetchone() is not None

        # Check DuLieu_AI table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='DuLieu_AI'"
        )
        assert cursor.fetchone() is not None

        # Check ManagedBridges table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ManagedBridges'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    def test_setup_database_returns_connection_and_cursor(self, temp_db):
        """Test that setup_database returns valid connection and cursor"""
        conn, cursor = db_manager.setup_database(temp_db)

        assert isinstance(conn, sqlite3.Connection)
        assert isinstance(cursor, sqlite3.Cursor)

        conn.close()

    def test_setup_database_managed_bridges_columns(self, temp_db):
        """Test that ManagedBridges has all required columns"""
        conn, cursor = db_manager.setup_database(temp_db)

        cursor.execute("PRAGMA table_info(ManagedBridges)")
        columns = [row[1] for row in cursor.fetchall()]

        required_columns = [
            "id",
            "name",
            "description",
            "is_enabled",
            "win_rate_text",
            "current_streak",
            "next_prediction_stl",
            "max_lose_streak_k2n",
        ]

        for col in required_columns:
            assert col in columns, f"Column {col} not found in ManagedBridges"

        conn.close()


class TestProcessKyEntry:
    """Tests for _process_ky_entry function"""

    def test_process_ky_entry_basic(self, temp_db):
        """Test basic prize data insertion"""
        conn, cursor = db_manager.setup_database(temp_db)

        prize_data = [
            ("Đặc Biệt", "12345"),
            ("Nhất", "67890"),
            ("Nhì", "11111 22222"),
        ]

        result = db_manager._process_ky_entry("240101", prize_data, cursor)

        assert result == 1

        # Verify data was inserted
        cursor.execute("SELECT * FROM DuLieu_AI WHERE MaSoKy = ?", ("240101",))
        row = cursor.fetchone()
        assert row is not None

        conn.close()

    def test_process_ky_entry_empty_data(self, temp_db):
        """Test with empty prize data"""
        conn, cursor = db_manager.setup_database(temp_db)

        result = db_manager._process_ky_entry("240102", [], cursor)

        assert result == 0

        conn.close()

    def test_process_ky_entry_invalid_format(self, temp_db):
        """Test with invalid data format"""
        conn, cursor = db_manager.setup_database(temp_db)

        # Invalid format - not tuple/list of 2
        prize_data = [("Đặc Biệt",)]

        result = db_manager._process_ky_entry("240103", prize_data, cursor)

        assert result == 0

        conn.close()


class TestGetAllKysFromDb:
    """Tests for get_all_kys_from_db function"""

    def test_get_all_kys_empty_db(self, temp_db):
        """Test retrieving from empty database"""
        conn, cursor = db_manager.setup_database(temp_db)
        conn.close()

        result = db_manager.get_all_kys_from_db(temp_db)

        assert result == []

    def test_get_all_kys_with_data(self, temp_db):
        """Test retrieving data from populated database"""
        conn, cursor = db_manager.setup_database(temp_db)

        # Insert test data
        cursor.execute(
            "INSERT INTO KyQuay (MaSoKy, NgayThang, ThoiGian) VALUES (?, ?, ?)",
            ("240101", "01/01/2024", "18:00"),
        )
        cursor.execute(
            "INSERT INTO KyQuay (MaSoKy, NgayThang, ThoiGian) VALUES (?, ?, ?)",
            ("240102", "02/01/2024", "18:00"),
        )
        conn.commit()
        conn.close()

        result = db_manager.get_all_kys_from_db(temp_db)

        assert len(result) == 2
        assert result[0][0] == "240102"  # DESC order
        assert result[1][0] == "240101"

    def test_get_all_kys_nonexistent_db(self):
        """Test with nonexistent database"""
        result = db_manager.get_all_kys_from_db("/nonexistent/path/db.db")

        assert result == []


class TestGetResultsByKy:
    """Tests for get_results_by_ky function"""

    def test_get_results_by_ky_found(self, temp_db):
        """Test retrieving existing results"""
        conn, cursor = db_manager.setup_database(temp_db)

        # Insert test data
        cursor.execute(
            """INSERT INTO DuLieu_AI 
               (MaSoKy, Col_A_Ky, Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3, Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "240101",
                "240101",
                "12345",
                "67890",
                "11111,22222",
                None,
                None,
                None,
                None,
                None,
            ),
        )
        conn.commit()
        conn.close()

        result = db_manager.get_results_by_ky("240101", temp_db)

        assert result is not None
        assert result[0] == "240101"
        assert result[2] == "12345"

    def test_get_results_by_ky_not_found(self, temp_db):
        """Test retrieving non-existent results"""
        conn, cursor = db_manager.setup_database(temp_db)
        conn.close()

        result = db_manager.get_results_by_ky("999999", temp_db)

        assert result is None

    def test_get_results_by_ky_invalid_db(self):
        """Test with invalid database path"""
        result = db_manager.get_results_by_ky("240101", "/nonexistent/db.db")

        assert result is None


class TestDeleteAllManagedBridges:
    """Tests for delete_all_managed_bridges function"""

    def test_delete_all_managed_bridges_success(self, temp_db):
        """Test successful deletion of all bridges"""
        conn, cursor = db_manager.setup_database(temp_db)

        # Insert test bridges
        cursor.execute(
            "INSERT INTO ManagedBridges (name, description) VALUES (?, ?)",
            ("Test Bridge 1", "Description 1"),
        )
        cursor.execute(
            "INSERT INTO ManagedBridges (name, description) VALUES (?, ?)",
            ("Test Bridge 2", "Description 2"),
        )
        conn.commit()

        result = db_manager.delete_all_managed_bridges(cursor)

        assert result is True

        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges")
        count = cursor.fetchone()[0]
        assert count == 0

        conn.close()

    def test_delete_all_managed_bridges_empty_table(self, temp_db):
        """Test deletion on empty table"""
        conn, cursor = db_manager.setup_database(temp_db)

        result = db_manager.delete_all_managed_bridges(cursor)

        assert result is True

        conn.close()


class TestAddManagedBridge:
    """Tests for add_managed_bridge function"""

    @patch("logic.db_manager.get_index_from_name_V16")
    def test_add_managed_bridge_success(self, mock_get_index, temp_db):
        """Test successful bridge addition"""
        mock_get_index.side_effect = [1, 2]  # Return indices for pos1 and pos2

        conn, cursor = db_manager.setup_database(temp_db)
        conn.close()

        success, message = db_manager.add_managed_bridge(
            "Đầu + Đuôi", "Test bridge", "50.5%", temp_db
        )

        assert success is True

        # Verify insertion
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM ManagedBridges WHERE name = ?", ("Đầu + Đuôi",))
        result = cursor.fetchone()
        assert result is not None
        conn.close()

    def test_add_managed_bridge_invalid_name(self, temp_db):
        """Test with invalid bridge name format"""
        conn, cursor = db_manager.setup_database(temp_db)
        conn.close()

        success, message = db_manager.add_managed_bridge(
            "Invalid Bridge", "Test", "50%", temp_db
        )

        assert success is False
        assert "không hợp lệ" in message

    @patch("logic.db_manager.get_index_from_name_V16")
    def test_add_managed_bridge_invalid_position_names(self, mock_get_index, temp_db):
        """Test with invalid position names"""
        mock_get_index.return_value = None  # Invalid positions

        conn, cursor = db_manager.setup_database(temp_db)
        conn.close()

        success, message = db_manager.add_managed_bridge(
            "Invalid + Position", "Test", "50%", temp_db
        )

        assert success is False
        assert "dịch tên vị trí" in message


class TestPrizeToColMap:
    """Tests for PRIZE_TO_COL_MAP constant"""

    def test_prize_to_col_map_exists(self):
        """Test that prize map is defined"""
        assert hasattr(db_manager, "PRIZE_TO_COL_MAP")
        assert isinstance(db_manager.PRIZE_TO_COL_MAP, dict)

    def test_prize_to_col_map_has_all_prizes(self):
        """Test that all prize types are mapped"""
        required_prizes = [
            "Đặc Biệt",
            "Nhất",
            "Nhì",
            "Ba",
            "Bốn",
            "Năm",
            "Sáu",
            "Bảy",
        ]

        for prize in required_prizes:
            assert prize in db_manager.PRIZE_TO_COL_MAP


class TestModuleConstants:
    """Tests for module-level constants"""

    def test_db_name_defined(self):
        """Test that DB_NAME is defined"""
        assert hasattr(db_manager, "DB_NAME")
        assert isinstance(db_manager.DB_NAME, str)
        assert len(db_manager.DB_NAME) > 0

    def test_db_name_format(self):
        """Test that DB_NAME has expected format"""
        assert db_manager.DB_NAME.endswith(".db")


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_process_ky_entry_with_list_values(self, temp_db):
        """Test prize data with list values instead of strings"""
        conn, cursor = db_manager.setup_database(temp_db)

        prize_data = [
            ("Đặc Biệt", ["12345"]),
            ("Nhất", ["67890", "11111"]),
        ]

        result = db_manager._process_ky_entry("240104", prize_data, cursor)

        assert result == 1

        conn.close()

    def test_process_ky_entry_with_dash_separated_numbers(self, temp_db):
        """Test prize data with dash-separated numbers"""
        conn, cursor = db_manager.setup_database(temp_db)

        prize_data = [
            ("Đặc Biệt", "12345"),
            ("Nhì", "11111-22222-33333"),
        ]

        result = db_manager._process_ky_entry("240105", prize_data, cursor)

        assert result == 1

        # Verify dashes are converted to commas
        cursor.execute("SELECT Col_D_G2 FROM DuLieu_AI WHERE MaSoKy = ?", ("240105",))
        row = cursor.fetchone()
        assert "," in row[0]
        assert "-" not in row[0]

        conn.close()
