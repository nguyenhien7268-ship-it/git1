# tests/test_common_utils_k1n.py
"""
Unit tests for common_utils.py K1N-primary enhancements (V11.2).

Tests:
- normalize_bridge_name()
- retry_on_db_lock() decorator
- timestamp helpers
"""

import pytest
import sqlite3
import time
from unittest.mock import Mock, patch

from logic.common_utils import (
    normalize_bridge_name,
    retry_on_db_lock,
    get_current_timestamp,
    get_current_date
)


class TestNormalizeBridgeName:
    """Test normalize_bridge_name function."""
    
    def test_removes_whitespace(self):
        """Test removes leading/trailing whitespace."""
        assert normalize_bridge_name("  Bridge  ") == "bridge"
        assert normalize_bridge_name("\tBridge\n") == "bridge"
    
    def test_converts_to_lowercase(self):
        """Test converts to lowercase."""
        assert normalize_bridge_name("BRIDGE") == "bridge"
        assert normalize_bridge_name("BrIdGe") == "bridge"
    
    def test_removes_special_characters(self):
        """Test removes special characters."""
        assert normalize_bridge_name("Bridge-01") == "bridge01"
        assert normalize_bridge_name("Cầu Đẹp") == "caudep"
        assert normalize_bridge_name("Bridge_#1") == "bridge1"
    
    def test_removes_spaces_between_words(self):
        """Test removes internal whitespace."""
        assert normalize_bridge_name("My Bridge Name") == "mybridgename"
        assert normalize_bridge_name("Bridge   01") == "bridge01"
    
    def test_handles_empty_string(self):
        """Test handles empty string."""
        assert normalize_bridge_name("") == ""
        assert normalize_bridge_name("   ") == ""
    
    def test_handles_none(self):
        """Test handles None input."""
        assert normalize_bridge_name(None) == ""
    
    def test_handles_numbers(self):
        """Test preserves numbers."""
        assert normalize_bridge_name("Bridge123") == "bridge123"
        assert normalize_bridge_name("01-02-03") == "010203"
    
    def test_idempotent(self):
        """Test function is idempotent."""
        name = "Bridge-01"
        normalized = normalize_bridge_name(name)
        assert normalize_bridge_name(normalized) == normalized


class TestRetryOnDbLock:
    """Test retry_on_db_lock decorator."""
    
    def test_succeeds_on_first_try(self):
        """Test function succeeds without retry."""
        call_count = {'count': 0}
        
        @retry_on_db_lock(max_retries=3)
        def successful_function():
            call_count['count'] += 1
            return "success"
        
        result = successful_function()
        
        assert result == "success"
        assert call_count['count'] == 1
    
    def test_retries_on_operational_error(self):
        """Test retries on sqlite3.OperationalError."""
        call_count = {'count': 0}
        
        @retry_on_db_lock(max_retries=3, initial_delay=0.01)
        def failing_then_succeeding():
            call_count['count'] += 1
            if call_count['count'] < 2:
                raise sqlite3.OperationalError("database is locked")
            return "success"
        
        result = failing_then_succeeding()
        
        assert result == "success"
        assert call_count['count'] == 2
    
    def test_gives_up_after_max_retries(self):
        """Test gives up after max retries."""
        call_count = {'count': 0}
        
        @retry_on_db_lock(max_retries=3, initial_delay=0.01)
        def always_failing():
            call_count['count'] += 1
            raise sqlite3.OperationalError("database is locked")
        
        with pytest.raises(sqlite3.OperationalError):
            always_failing()
        
        assert call_count['count'] == 3
    
    def test_exponential_backoff(self):
        """Test uses exponential backoff."""
        delays = []
        
        @retry_on_db_lock(max_retries=3, initial_delay=0.1)
        def track_delays():
            if len(delays) < 2:
                delays.append(time.time())
                raise sqlite3.OperationalError("database is locked")
            return "success"
        
        result = track_delays()
        
        assert result == "success"
        # Verify delays increased (roughly doubled)
        if len(delays) >= 2:
            time_diff = delays[1] - delays[0]
            assert time_diff >= 0.1  # At least initial delay
    
    def test_propagates_other_exceptions(self):
        """Test propagates non-OperationalError exceptions."""
        @retry_on_db_lock(max_retries=3)
        def raises_value_error():
            raise ValueError("Not a DB error")
        
        with pytest.raises(ValueError):
            raises_value_error()
    
    def test_preserves_function_metadata(self):
        """Test decorator preserves function metadata."""
        @retry_on_db_lock(max_retries=3)
        def my_function():
            """My docstring."""
            pass
        
        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."
    
    def test_works_with_arguments(self):
        """Test decorator works with function arguments."""
        @retry_on_db_lock(max_retries=2, initial_delay=0.01)
        def add_numbers(a, b):
            return a + b
        
        result = add_numbers(5, 3)
        assert result == 8


class TestTimestampHelpers:
    """Test timestamp helper functions."""
    
    def test_get_current_timestamp_format(self):
        """Test get_current_timestamp returns correct format."""
        timestamp = get_current_timestamp()
        
        # Should match YYYY-MM-DD HH:MM:SS format
        assert len(timestamp) == 19
        assert timestamp[4] == '-'
        assert timestamp[7] == '-'
        assert timestamp[10] == ' '
        assert timestamp[13] == ':'
        assert timestamp[16] == ':'
    
    def test_get_current_timestamp_is_recent(self):
        """Test get_current_timestamp returns recent time."""
        from datetime import datetime
        
        timestamp_str = get_current_timestamp()
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        
        # Should be within 1 second of current time
        diff = (now - timestamp).total_seconds()
        assert abs(diff) < 1.0
    
    def test_get_current_date_format(self):
        """Test get_current_date returns correct format."""
        date = get_current_date()
        
        # Should match YYYY-MM-DD format
        assert len(date) == 10
        assert date[4] == '-'
        assert date[7] == '-'
    
    def test_get_current_date_is_today(self):
        """Test get_current_date returns today's date."""
        from datetime import datetime
        
        date_str = get_current_date()
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        
        assert date == today
    
    def test_timestamp_and_date_consistency(self):
        """Test timestamp and date helpers are consistent."""
        timestamp = get_current_timestamp()
        date = get_current_date()
        
        # Date portion of timestamp should match date
        timestamp_date = timestamp.split(' ')[0]
        assert timestamp_date == date


class TestIntegration:
    """Integration tests for common utils."""
    
    def test_normalize_used_with_set(self):
        """Test normalize_bridge_name works well with set operations."""
        names = ["Bridge-01", "bridge01", "Bridge 01", "BRIDGE-01"]
        normalized = {normalize_bridge_name(name) for name in names}
        
        # All should normalize to same value
        assert len(normalized) == 1
        assert "bridge01" in normalized
    
    def test_retry_with_real_db_operation(self, temp_db):
        """Test retry decorator with actual DB operation."""
        conn, cursor, db_path = temp_db
        
        @retry_on_db_lock(max_retries=3, initial_delay=0.01)
        def insert_bridge(name):
            cursor.execute(
                "INSERT INTO ManagedBridges (name, description) VALUES (?, ?)",
                (name, "Test")
            )
            conn.commit()
        
        # Should work without errors
        insert_bridge("Test-Bridge")
        
        # Verify insertion
        cursor.execute("SELECT name FROM ManagedBridges WHERE name=?", ("Test-Bridge",))
        result = cursor.fetchone()
        assert result[0] == "Test-Bridge"
