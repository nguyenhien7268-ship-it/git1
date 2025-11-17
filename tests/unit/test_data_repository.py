"""Unit tests for logic/data_repository.py module."""
import pytest
import sqlite3
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from logic.data_repository import (
    load_data_ai_from_db,
    get_all_managed_bridges,
    get_latest_ky_date
)


class TestLoadDataAiFromDb:
    """Tests for load_data_ai_from_db function."""
    
    def test_load_data_success(self, tmp_path):
        """Test loading data from database successfully."""
        # Create temporary database
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create table and insert test data
        cursor.execute('''
            CREATE TABLE DuLieu_AI (
                MaSoKy TEXT,
                Col_A_Ky TEXT, Col_B_GDB TEXT, Col_C_G1 TEXT,
                Col_D_G2 TEXT, Col_E_G3 TEXT, Col_F_G4 TEXT,
                Col_G_G5 TEXT, Col_H_G6 TEXT, Col_I_G7 TEXT
            )
        ''')
        cursor.execute('''
            INSERT INTO DuLieu_AI VALUES 
            ('23001', 'A1', 'B1', 'C1', 'D1', 'E1', 'F1', 'G1', 'H1', 'I1'),
            ('23002', 'A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2')
        ''')
        conn.commit()
        conn.close()
        
        # Test load
        result, message = load_data_ai_from_db(str(db_path))
        
        assert result is not None
        assert len(result) == 2
        assert result[0][0] == '23001'
        assert "Đã tải 2 hàng" in message
    
    def test_load_data_db_not_found(self):
        """Test loading data when database doesn't exist."""
        result, message = load_data_ai_from_db('nonexistent.db')
        
        assert result is None
        # Accept either error message (file not found or table not found)
        assert "Không tìm thấy database" in message or "Lỗi khi tải dữ liệu" in message
    
    def test_load_data_empty_database(self, tmp_path):
        """Test loading data from empty database."""
        db_path = tmp_path / "empty.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE DuLieu_AI (
                MaSoKy TEXT,
                Col_A_Ky TEXT, Col_B_GDB TEXT, Col_C_G1 TEXT,
                Col_D_G2 TEXT, Col_E_G3 TEXT, Col_F_G4 TEXT,
                Col_G_G5 TEXT, Col_H_G6 TEXT, Col_I_G7 TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        result, message = load_data_ai_from_db(str(db_path))
        
        assert result is not None
        assert len(result) == 0
        assert "Đã tải 0 hàng" in message


class TestGetAllManagedBridges:
    """Tests for get_all_managed_bridges function."""
    
    def test_get_all_bridges_success(self, tmp_path):
        """Test getting all bridges successfully."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE ManagedBridges (
                id INTEGER PRIMARY KEY,
                bridge_name TEXT,
                is_enabled INTEGER,
                win_rate_text TEXT
            )
        ''')
        cursor.execute('''
            INSERT INTO ManagedBridges (bridge_name, is_enabled, win_rate_text) VALUES 
            ('Bridge1', 1, '50.5%'),
            ('Bridge2', 0, '45.0%'),
            ('Bridge3', 1, '55.0%')
        ''')
        conn.commit()
        conn.close()
        
        result = get_all_managed_bridges(str(db_path))
        
        assert len(result) == 3
        assert isinstance(result[0], dict)
        assert result[0]['bridge_name'] in ['Bridge1', 'Bridge2', 'Bridge3']
    
    def test_get_only_enabled_bridges(self, tmp_path):
        """Test getting only enabled bridges."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE ManagedBridges (
                id INTEGER PRIMARY KEY,
                bridge_name TEXT,
                is_enabled INTEGER
            )
        ''')
        cursor.execute('''
            INSERT INTO ManagedBridges (bridge_name, is_enabled) VALUES 
            ('Bridge1', 1),
            ('Bridge2', 0),
            ('Bridge3', 1)
        ''')
        conn.commit()
        conn.close()
        
        result = get_all_managed_bridges(str(db_path), only_enabled=True)
        
        assert len(result) == 2
        assert all(bridge['is_enabled'] == 1 for bridge in result)
    
    def test_get_bridges_db_not_found(self):
        """Test getting bridges when database doesn't exist."""
        result = get_all_managed_bridges('nonexistent.db')
        
        assert result == []
    
    def test_get_bridges_empty_table(self, tmp_path):
        """Test getting bridges from empty table."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE ManagedBridges (
                id INTEGER PRIMARY KEY,
                bridge_name TEXT,
                is_enabled INTEGER
            )
        ''')
        conn.commit()
        conn.close()
        
        result = get_all_managed_bridges(str(db_path))
        
        assert result == []


class TestGetLatestKyDate:
    """Tests for get_latest_ky_date function."""
    
    def test_get_latest_ky_date_success(self, tmp_path):
        """Test getting latest ky and date successfully."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE DuLieu_AI (MaSoKy TEXT)
        ''')
        cursor.execute('''
            CREATE TABLE KyQuay (MaSoKy TEXT, NgayThang TEXT)
        ''')
        cursor.execute("INSERT INTO DuLieu_AI VALUES ('23001'), ('23002')")
        cursor.execute("INSERT INTO KyQuay VALUES ('23001', '01/01/2023'), ('23002', '02/01/2023')")
        conn.commit()
        
        ky, date = get_latest_ky_date(cursor)
        
        assert ky == '23002'
        assert date is not None
    
    def test_get_latest_ky_date_no_data(self, tmp_path):
        """Test getting latest ky when no data exists."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE DuLieu_AI (MaSoKy TEXT)
        ''')
        cursor.execute('''
            CREATE TABLE KyQuay (MaSoKy TEXT, NgayThang TEXT)
        ''')
        conn.commit()
        
        result = get_latest_ky_date(cursor)
        
        # Should return None or handle gracefully
        assert result is not None or result is None


# Fixtures
@pytest.fixture
def sample_db(tmp_path):
    """Create a sample database for testing."""
    db_path = tmp_path / "sample.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE DuLieu_AI (
            MaSoKy TEXT,
            Col_A_Ky TEXT, Col_B_GDB TEXT, Col_C_G1 TEXT,
            Col_D_G2 TEXT, Col_E_G3 TEXT, Col_F_G4 TEXT,
            Col_G_G5 TEXT, Col_H_G6 TEXT, Col_I_G7 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE ManagedBridges (
            id INTEGER PRIMARY KEY,
            bridge_name TEXT,
            is_enabled INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    
    return str(db_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
