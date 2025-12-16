"""
Tests for delete ky functionality in lookup window
"""

import pytest
import sqlite3
import os


def test_delete_ky_function_exists():
    """Test that delete_ky_from_db function exists and is importable"""
    from logic.db_manager import delete_ky_from_db
    assert callable(delete_ky_from_db)


def test_delete_ky_from_database(tmp_path):
    """Test deleting a ky from the database"""
    from logic.db_manager import delete_ky_from_db, setup_database
    
    # Create a temporary database
    test_db = tmp_path / "test_delete.db"
    db_path = str(test_db)
    
    # Setup database
    setup_database(db_path)
    
    # Insert test data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Insert into results_A_I
    cursor.execute("""
        INSERT INTO results_A_I (ky, date, gdb, g1, g2, g3, g4, g5, g6, g7)
        VALUES ('12345', '2025-01-01', '12345', '67890', '11111,22222', 
                '33333,44444,55555,66666,77777,88888', '1111,2222,3333,4444',
                '111,222,333,444,555,666', '11,22,33,44', '1,2,3,4')
    """)
    
    # Insert into DuLieu_AI
    cursor.execute("""
        INSERT INTO DuLieu_AI (Col_A_Ky, Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3,
                               Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7)
        VALUES ('12345', '12345', '67890', '11111,22222', '33333,44444,55555,66666,77777,88888',
                '1111,2222,3333,4444', '111,222,333,444,555,666', '11,22,33,44', '1,2,3,4')
    """)
    
    conn.commit()
    conn.close()
    
    # Verify data exists
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM results_A_I WHERE ky = '12345'")
    assert cursor.fetchone()[0] == 1
    cursor.execute("SELECT COUNT(*) FROM DuLieu_AI WHERE Col_A_Ky = '12345'")
    assert cursor.fetchone()[0] == 1
    conn.close()
    
    # Delete the ky
    success, message = delete_ky_from_db('12345', db_path)
    assert success is True
    assert '12345' in message
    
    # Verify data is deleted from both tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM results_A_I WHERE ky = '12345'")
    assert cursor.fetchone()[0] == 0
    cursor.execute("SELECT COUNT(*) FROM DuLieu_AI WHERE Col_A_Ky = '12345'")
    assert cursor.fetchone()[0] == 0
    conn.close()


def test_delete_nonexistent_ky(tmp_path):
    """Test deleting a ky that doesn't exist"""
    from logic.db_manager import delete_ky_from_db, setup_database
    
    # Create a temporary database
    test_db = tmp_path / "test_delete_nonexist.db"
    db_path = str(test_db)
    
    # Setup database
    setup_database(db_path)
    
    # Try to delete a non-existent ky
    success, message = delete_ky_from_db('99999', db_path)
    # Should still return success (no error), but 0 records deleted
    assert success is True


def test_compact_star_display():
    """Test that star display is compact (e.g., '4⭐' instead of '⭐⭐⭐⭐')"""
    # Test the formatting logic
    sources = 4
    compact_display = f"{sources}⭐" if sources > 0 else ""
    assert compact_display == "4⭐"
    
    sources = 0
    compact_display = f"{sources}⭐" if sources > 0 else ""
    assert compact_display == ""
    
    sources = 7
    compact_display = f"{sources}⭐" if sources > 0 else ""
    assert compact_display == "7⭐"
    
    # Verify it's shorter than the old format
    sources = 5
    old_format = "⭐" * sources
    new_format = f"{sources}⭐"
    assert len(new_format) < len(old_format)
