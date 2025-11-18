# tests/conftest.py
# Pytest fixtures for test suite
import os
import sqlite3
import sys
import tempfile

import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def temp_db():
    """Create temporary test database"""
    fd, path = tempfile.mkstemp(suffix=".db")

    # Setup database
    from logic.db_manager import setup_database

    conn, cursor = setup_database(path)

    yield conn, cursor, path

    # Cleanup
    conn.close()
    os.close(fd)
    os.unlink(path)


@pytest.fixture
def sample_lottery_data():
    """Provide sample test data for lottery results"""
    return [
        (
            23001,
            "23001",
            "12345",
            "67890",
            "11111,22222",
            "33333",
            "44444,55555,66666",
            "77777",
            "88888,99999",
            "00000",
        ),
        (
            23002,
            "23002",
            "54321",
            "09876",
            "22222,11111",
            "44444",
            "55555,66666,44444",
            "88888",
            "99999,88888",
            "11111",
        ),
        (
            23003,
            "23003",
            "11223",
            "33445",
            "55667,78899",
            "00112",
            "23344,56677,89900",
            "11223",
            "34455,66778",
            "99001",
        ),
    ]


@pytest.fixture
def sample_bridge_data():
    """Sample bridge data for testing"""
    return [
        {
            "name": "Test Bridge 1",
            "description": "Test bridge for unit tests",
            "pos1_idx": 0,
            "pos2_idx": 1,
            "is_enabled": 1,
        },
        {
            "name": "Test Bridge 2",
            "description": "Another test bridge",
            "pos1_idx": 2,
            "pos2_idx": 3,
            "is_enabled": 1,
        },
    ]
