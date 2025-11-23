# tests/conftest.py
# Pytest fixtures for test suite
import os
import sys
import tempfile
from unittest.mock import MagicMock, Mock, patch

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

    # Cleanup - ensure connection is closed
    try:
        conn.close()
    except Exception:
        pass
    os.close(fd)
    # Wait a bit and retry if file is locked (Windows issue)
    import time
    time.sleep(0.1)
    try:
        if os.path.exists(path):
            os.unlink(path)
    except PermissionError:
        # On Windows, sometimes file is still locked
        # Try again after a short delay
        time.sleep(0.2)
        try:
            if os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass  # Ignore if still can't delete


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


@pytest.fixture
def mock_settings():
    """Mock SETTINGS object for testing"""
    from logic.constants import DEFAULT_SETTINGS
    
    mock = MagicMock()
    for key, value in DEFAULT_SETTINGS.items():
        setattr(mock, key, value)
    
    def get_all_settings():
        return DEFAULT_SETTINGS.copy()
    
    def get(key, default=None):
        return getattr(mock, key, default)
    
    mock.get_all_settings = get_all_settings
    mock.get = get
    mock.load_settings = Mock()
    mock.save_settings = Mock()
    
    return mock


@pytest.fixture
def sample_ai_data():
    """Sample A:I data format for backtesting"""
    return [
        # Format: (MaSoKy, Col_A_Ky, Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3, Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7)
        (23001, "23001", "12", "34", "56", "78", "90", "11", "22", "33"),
        (23002, "23002", "23", "45", "67", "89", "01", "12", "23", "34"),
        (23003, "23003", "34", "56", "78", "90", "12", "23", "34", "45"),
        (23004, "23004", "45", "67", "89", "01", "23", "34", "45", "56"),
        (23005, "23005", "56", "78", "90", "12", "34", "45", "56", "67"),
    ]


@pytest.fixture
def sample_results_ai_data():
    """Sample results_A_I data format"""
    return [
        {
            "ky": "23001",
            "date": "2023-01-01",
            "gdb": "12", "g1": "34", "g2": "56", "g3": "78", "g4": "90",
            "g5": "11", "g6": "22", "g7": "33",
            "l0": "00", "l1": "01", "l2": "02", "l3": "03", "l4": "04",
            "l5": "05", "l6": "06", "l7": "07", "l8": "08", "l9": "09",
            "l10": "10", "l11": "11", "l12": "12", "l13": "13", "l14": "14",
            "l15": "15", "l16": "16", "l17": "17", "l18": "18", "l19": "19",
            "l20": "20", "l21": "21", "l22": "22", "l23": "23", "l24": "24",
            "l25": "25", "l26": "26",
        },
    ]


@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing"""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


@pytest.fixture(autouse=True)
def reset_config():
    """Reset config to defaults before each test"""
    yield
    # Cleanup if needed
    pass
