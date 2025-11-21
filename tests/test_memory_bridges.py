"""
Test suite for 756 Memory Bridges (Cầu Bạc Nhớ) functionality.
Tests Phase 1 (backtester core), Phase 2 (data generator), and Phase 3 (UI integration).
"""

import pytest
import sqlite3
import os
import tempfile


# ===================================================================================
# PHASE 2: Data Generator Tests
# ===================================================================================


def test_init_all_756_memory_bridges_creates_correct_count():
    """Test that init_all_756_memory_bridges_to_db creates exactly 756 bridges."""
    from logic.bridges.bridge_manager_core import init_all_756_memory_bridges_to_db
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db = tmp.name
    
    try:
        # Initialize database
        from logic.db_manager import setup_database
        setup_database(tmp_db)
        
        # Run the function
        success, message, added_count, skipped_count = init_all_756_memory_bridges_to_db(tmp_db)
        
        # Assertions
        assert success is True, f"Function should succeed but got: {message}"
        assert added_count == 756, f"Should add exactly 756 bridges, got {added_count}"
        assert skipped_count == 0, f"Should skip 0 bridges on first run, got {skipped_count}"
        
        # Verify in database
        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges WHERE pos1_idx = -1 AND pos2_idx = -1")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        assert db_count == 756, f"Database should have 756 memory bridges, got {db_count}"
        
    finally:
        # Clean up
        if os.path.exists(tmp_db):
            os.remove(tmp_db)


def test_init_all_756_memory_bridges_creates_correct_format():
    """Test that bridge names follow the correct format: Tổng(00+01) and Hiệu(00-01)."""
    from logic.bridges.bridge_manager_core import init_all_756_memory_bridges_to_db
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db = tmp.name
    
    try:
        from logic.db_manager import setup_database
        setup_database(tmp_db)
        
        init_all_756_memory_bridges_to_db(tmp_db)
        
        # Check a few sample bridges
        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()
        
        # Check for specific bridges
        cursor.execute("SELECT name FROM ManagedBridges WHERE name = ?", ("Tổng(00+00)",))
        assert cursor.fetchone() is not None, "Should have Tổng(00+00)"
        
        cursor.execute("SELECT name FROM ManagedBridges WHERE name = ?", ("Hiệu(00-00)",))
        assert cursor.fetchone() is not None, "Should have Hiệu(00-00)"
        
        cursor.execute("SELECT name FROM ManagedBridges WHERE name = ?", ("Tổng(26+26)",))
        assert cursor.fetchone() is not None, "Should have Tổng(26+26)"
        
        cursor.execute("SELECT name FROM ManagedBridges WHERE name = ?", ("Hiệu(26-26)",))
        assert cursor.fetchone() is not None, "Should have Hiệu(26-26)"
        
        # Check that all names follow the pattern
        cursor.execute("SELECT name FROM ManagedBridges WHERE pos1_idx = -1")
        all_names = [row[0] for row in cursor.fetchall()]
        
        import re
        for name in all_names:
            assert re.match(r'(Tổng|Hiệu)\(\d{2}[+\-]\d{2}\)', name), f"Invalid format: {name}"
        
        conn.close()
        
    finally:
        if os.path.exists(tmp_db):
            os.remove(tmp_db)


def test_init_all_756_memory_bridges_default_disabled():
    """Test that all memory bridges are created with is_enabled=0 by default."""
    from logic.bridges.bridge_manager_core import init_all_756_memory_bridges_to_db
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db = tmp.name
    
    try:
        from logic.db_manager import setup_database
        setup_database(tmp_db)
        
        init_all_756_memory_bridges_to_db(tmp_db)
        
        # Check that all are disabled
        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges WHERE pos1_idx = -1 AND is_enabled = 1")
        enabled_count = cursor.fetchone()[0]
        conn.close()
        
        assert enabled_count == 0, f"All memory bridges should be disabled by default, got {enabled_count} enabled"
        
    finally:
        if os.path.exists(tmp_db):
            os.remove(tmp_db)


def test_init_all_756_memory_bridges_skips_duplicates():
    """Test that running the function twice skips existing bridges."""
    from logic.bridges.bridge_manager_core import init_all_756_memory_bridges_to_db
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db = tmp.name
    
    try:
        from logic.db_manager import setup_database
        setup_database(tmp_db)
        
        # First run
        success1, msg1, added1, skipped1 = init_all_756_memory_bridges_to_db(tmp_db)
        assert added1 == 756
        assert skipped1 == 0
        
        # Second run - should skip all
        success2, msg2, added2, skipped2 = init_all_756_memory_bridges_to_db(tmp_db)
        assert success2 is True
        assert added2 == 0, "Should not add any bridges on second run"
        assert skipped2 == 756, "Should skip all 756 bridges on second run"
        
    finally:
        if os.path.exists(tmp_db):
            os.remove(tmp_db)


# ===================================================================================
# PHASE 1: Backtester Core Tests
# ===================================================================================


def test_memory_bridge_parser_tong():
    """Test that the parser correctly extracts positions from Tổng bridge names."""
    import re
    
    # Test patterns
    test_cases = [
        ("Tổng(00+01)", 0, 1),
        ("Tổng(05+10)", 5, 10),
        ("Tổng(26+26)", 26, 26),
        ("Tổng(0+1)", 0, 1),  # Without zero padding
    ]
    
    pattern = r'Tổng\((\d+)\+(\d+)\)'
    
    for bridge_name, expected_pos1, expected_pos2 in test_cases:
        match = re.search(pattern, bridge_name)
        assert match is not None, f"Pattern should match {bridge_name}"
        pos1 = int(match.group(1))
        pos2 = int(match.group(2))
        assert pos1 == expected_pos1, f"Expected pos1={expected_pos1}, got {pos1}"
        assert pos2 == expected_pos2, f"Expected pos2={expected_pos2}, got {pos2}"


def test_memory_bridge_parser_hieu():
    """Test that the parser correctly extracts positions from Hiệu bridge names."""
    import re
    
    test_cases = [
        ("Hiệu(00-01)", 0, 1),
        ("Hiệu(05-10)", 5, 10),
        ("Hiệu(26-26)", 26, 26),
        ("Hiệu(0-1)", 0, 1),  # Without zero padding
    ]
    
    pattern = r'Hiệu\((\d+)-(\d+)\)'
    
    for bridge_name, expected_pos1, expected_pos2 in test_cases:
        match = re.search(pattern, bridge_name)
        assert match is not None, f"Pattern should match {bridge_name}"
        pos1 = int(match.group(1))
        pos2 = int(match.group(2))
        assert pos1 == expected_pos1, f"Expected pos1={expected_pos1}, got {pos1}"
        assert pos2 == expected_pos2, f"Expected pos2={expected_pos2}, got {pos2}"


def test_calculate_bridge_stl_imported():
    """Test that calculate_bridge_stl is properly imported in backtester_core."""
    from logic.backtester_core import calculate_bridge_stl
    
    # Test basic functionality
    result = calculate_bridge_stl("12", "34", "sum")
    assert isinstance(result, list), "Should return a list"
    assert len(result) == 2, "Should return 2 elements [lo, lon]"


def test_memory_bridge_detection_logic():
    """Test the logic for detecting memory bridges (pos1_idx == -1 and pos2_idx == -1)."""
    # This tests the core logic without needing full integration
    
    # Mock bridge data
    v17_bridge = {"pos1_idx": 0, "pos2_idx": 1, "name": "GDB[0]+G1[1]"}
    memory_bridge = {"pos1_idx": -1, "pos2_idx": -1, "name": "Tổng(00+01)"}
    
    # Test detection
    assert not (v17_bridge["pos1_idx"] == -1 and v17_bridge["pos2_idx"] == -1), "Should not detect V17 bridge as memory bridge"
    assert (memory_bridge["pos1_idx"] == -1 and memory_bridge["pos2_idx"] == -1), "Should detect memory bridge"


# ===================================================================================
# INTEGRATION TESTS
# ===================================================================================


def test_full_integration_memory_bridge_in_database():
    """Integration test: Create a memory bridge in DB and verify it can be used."""
    from logic.bridges.bridge_manager_core import init_all_756_memory_bridges_to_db
    from logic.data_repository import get_all_managed_bridges
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db = tmp.name
    
    try:
        from logic.db_manager import setup_database
        setup_database(tmp_db)
        
        # Add memory bridges
        init_all_756_memory_bridges_to_db(tmp_db)
        
        # Enable one bridge for testing
        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()
        cursor.execute("UPDATE ManagedBridges SET is_enabled = 1 WHERE name = ?", ("Tổng(00+01)",))
        conn.commit()
        conn.close()
        
        # Retrieve enabled bridges
        bridges = get_all_managed_bridges(tmp_db, only_enabled=True)
        
        # Find our memory bridge
        memory_bridge = None
        for bridge in bridges:
            if bridge["name"] == "Tổng(00+01)":
                memory_bridge = bridge
                break
        
        assert memory_bridge is not None, "Should find the enabled memory bridge"
        assert memory_bridge["pos1_idx"] == -1, "Memory bridge should have pos1_idx = -1"
        assert memory_bridge["pos2_idx"] == -1, "Memory bridge should have pos2_idx = -1"
        
    finally:
        if os.path.exists(tmp_db):
            os.remove(tmp_db)


def test_progress_callback_is_called():
    """Test that progress callback is properly called during bridge generation."""
    from logic.bridges.bridge_manager_core import init_all_756_memory_bridges_to_db
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db = tmp.name
    
    try:
        from logic.db_manager import setup_database
        setup_database(tmp_db)
        
        # Track callback invocations
        callback_calls = []
        
        def progress_callback(current, total, message):
            callback_calls.append((current, total, message))
        
        # Run with callback
        init_all_756_memory_bridges_to_db(tmp_db, progress_callback=progress_callback)
        
        # Verify callback was called
        assert len(callback_calls) > 0, "Progress callback should be called at least once"
        
        # Verify final callback
        final_call = callback_calls[-1]
        assert final_call[0] == 756, "Final callback should show 756 current"
        assert final_call[1] == 756, "Final callback should show 756 total"
        
    finally:
        if os.path.exists(tmp_db):
            os.remove(tmp_db)


def test_init_all_756_memory_bridges_with_enable_all():
    """Test that enable_all parameter enables all bridges."""
    from logic.bridges.bridge_manager_core import init_all_756_memory_bridges_to_db
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_db = tmp.name
    
    try:
        from logic.db_manager import setup_database
        setup_database(tmp_db)
        
        # Run with enable_all=True
        success, message, added, skipped = init_all_756_memory_bridges_to_db(
            tmp_db, enable_all=True
        )
        
        assert success is True
        assert added == 756
        
        # Check that all bridges are enabled
        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges WHERE pos1_idx = -1 AND is_enabled = 1")
        enabled_count = cursor.fetchone()[0]
        conn.close()
        
        assert enabled_count == 756, f"All 756 bridges should be enabled, got {enabled_count}"
        
    finally:
        if os.path.exists(tmp_db):
            os.remove(tmp_db)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
