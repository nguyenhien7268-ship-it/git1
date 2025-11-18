# tests/test_db_manager.py
# Unit tests for database manager module
import pytest


def test_setup_database_creates_all_tables(temp_db):
    """Verify all required tables are created"""
    conn, cursor, path = temp_db

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    assert "DuLieu_AI" in tables, "DuLieu_AI table not created"
    assert "results_A_I" in tables, "results_A_I table not created"
    assert "ManagedBridges" in tables, "ManagedBridges table not created"


def test_setup_database_creates_indexes(temp_db):
    """Verify performance indexes are created"""
    conn, cursor, path = temp_db

    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    indexes = [row[0] for row in cursor.fetchall()]

    # Check all 4 indexes exist
    assert "idx_results_ky" in indexes, "idx_results_ky not created"
    assert "idx_dulieu_masoky" in indexes, "idx_dulieu_masoky not created"
    assert "idx_bridges_enabled" in indexes, "idx_bridges_enabled not created"
    assert "idx_bridges_enabled_rate" in indexes, "idx_bridges_enabled_rate not created"
    assert len(indexes) == 4, f"Expected 4 indexes, found {len(indexes)}"


def test_get_results_by_ky_returns_none_for_missing_ky(temp_db):
    """Test behavior when ky doesn't exist"""
    conn, cursor, path = temp_db

    from logic.db_manager import get_results_by_ky

    result = get_results_by_ky("99999", conn)
    assert result is None, "Should return None for non-existent ky"


def test_add_managed_bridge_creates_new_record(temp_db, sample_bridge_data):
    """Test adding a new bridge"""
    conn, cursor, path = temp_db

    from logic.db_manager import add_managed_bridge

    bridge = sample_bridge_data[0]
    success, message = add_managed_bridge(
        bridge_name=bridge["name"],
        description=bridge["description"],
        db_name=path,
    )

    assert success is True, f"Bridge creation should succeed: {message}"
    assert "Đã thêm cầu" in message, "Success message should confirm bridge added"

    # Verify it was inserted
    cursor.execute("SELECT * FROM ManagedBridges WHERE name = ?", (bridge["name"],))
    row = cursor.fetchone()
    assert row is not None, "Bridge should exist in database"
    assert row[1] == bridge["name"], "Bridge name should match"


def test_add_duplicate_bridge_fails(temp_db, sample_bridge_data):
    """Test that duplicate bridge names are rejected"""
    conn, cursor, path = temp_db

    from logic.db_manager import add_managed_bridge

    bridge = sample_bridge_data[0]

    # Add first bridge
    success_1, message_1 = add_managed_bridge(
        bridge_name=bridge["name"],
        description=bridge["description"],
        db_name=path,
    )
    assert success_1 is True, "First bridge should be added successfully"

    # Try to add duplicate - should return False
    success_2, message_2 = add_managed_bridge(
        bridge_name=bridge["name"],  # Same name!
        description="Different description",
        db_name=path,
    )
    assert success_2 is False, "Duplicate bridge should fail"
    assert "đã tồn tại" in message_2 or "IntegrityError" in message_2, "Error message should mention duplicate"


def test_managed_bridges_table_has_max_lose_streak_column(temp_db):
    """Verify ManagedBridges has max_lose_streak_k2n column"""
    conn, cursor, path = temp_db

    cursor.execute("PRAGMA table_info(ManagedBridges)")
    columns = [row[1] for row in cursor.fetchall()]

    assert "max_lose_streak_k2n" in columns, "max_lose_streak_k2n column missing"


def test_database_indexes_improve_query_performance(temp_db):
    """Verify indexes exist and can be used"""
    conn, cursor, path = temp_db

    # Insert test data
    cursor.execute(
        "INSERT INTO results_A_I (ky, date, gdb) VALUES (?, ?, ?)",
        ("23001", "2023-01-01", "12345"),
    )
    conn.commit()

    # Query should use index (we can check EXPLAIN QUERY PLAN)
    cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM results_A_I WHERE ky = '23001'")
    plan = cursor.fetchall()

    # The plan should mention using an index
    plan_str = str(plan).lower()
    assert "index" in plan_str or "idx" in plan_str, "Query should use index"
