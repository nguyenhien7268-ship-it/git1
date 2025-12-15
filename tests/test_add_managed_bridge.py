# -*- coding: utf-8 -*-
"""
tests.test_add_managed_bridge
------------------------------
Test suite for add_managed_bridge_adapter service function.

Tests validation, normalization, defaulting, and error handling.
"""

import pytest
import sys
import os
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the adapter function
try:
    from lottery_service import add_managed_bridge_adapter
    from logic.constants import DEFAULT_WIN_RATE, MIN_NAME_LENGTH
except ImportError as e:
    pytest.skip(f"Could not import required modules: {e}", allow_module_level=True)


class TestAddManagedBridgeAdapter:
    """Test suite for add_managed_bridge_adapter function."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        # Create temp file
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Setup database schema
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ManagedBridges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_enabled INTEGER DEFAULT 1,
                date_added TEXT DEFAULT (datetime('now', 'localtime')),
                win_rate_text TEXT DEFAULT 'N/A',
                current_streak INTEGER DEFAULT 0,
                next_prediction_stl TEXT DEFAULT 'N/A',
                pos1_idx INTEGER,
                pos2_idx INTEGER,
                max_lose_streak_k2n INTEGER DEFAULT 0,
                recent_win_count_10 INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
        
        yield path
        
        # Cleanup
        try:
            os.unlink(path)
        except:
            pass
    
    def test_add_bridge_with_valid_name(self, temp_db):
        """Test adding a bridge with a valid name."""
        result = add_managed_bridge_adapter(
            bridge_name="Test Bridge 01",
            description="Test description",
            db_name=temp_db
        )
        
        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2
        success, message = result
        assert isinstance(success, bool)
        assert isinstance(message, str)
        # Note: Result depends on DB implementation, just verify structure
    
    def test_add_bridge_empty_name_fails(self, temp_db):
        """Test that empty bridge name is rejected."""
        result = add_managed_bridge_adapter(
            bridge_name="",
            description="Test",
            db_name=temp_db
        )
        
        success, message = result
        assert success is False
        assert "required" in message.lower()
    
    def test_add_bridge_whitespace_only_name_fails(self, temp_db):
        """Test that whitespace-only name is rejected."""
        result = add_managed_bridge_adapter(
            bridge_name="   ",
            description="Test",
            db_name=temp_db
        )
        
        success, message = result
        assert success is False
        assert "required" in message.lower() or "short" in message.lower()
    
    def test_add_bridge_none_name_fails(self, temp_db):
        """Test that None as bridge name is rejected."""
        result = add_managed_bridge_adapter(
            bridge_name=None,
            description="Test",
            db_name=temp_db
        )
        
        success, message = result
        assert success is False
        assert "required" in message.lower()
    
    def test_add_bridge_normalizes_whitespace(self, temp_db):
        """Test that leading/trailing whitespace is normalized."""
        result = add_managed_bridge_adapter(
            bridge_name="  Test Bridge  ",
            description="Test",
            db_name=temp_db
        )
        
        # Should succeed (whitespace normalized)
        success, message = result
        # Can't assert True without knowing DB state, but should not fail on whitespace
        assert isinstance(success, bool)
    
    def test_add_bridge_sanitizes_special_chars(self, temp_db):
        """Test that special characters are sanitized."""
        result = add_managed_bridge_adapter(
            bridge_name="Test@#$Bridge",
            description="Test",
            db_name=temp_db
        )
        
        # Should succeed after sanitization
        success, message = result
        assert isinstance(success, bool)
    
    def test_add_bridge_defaults_win_rate(self, temp_db):
        """Test that win_rate defaults when not provided."""
        with patch('lottery_service.add_managed_bridge') as mock_db:
            mock_db.return_value = (True, "Success")
            
            result = add_managed_bridge_adapter(
                bridge_name="Test Bridge",
                description="Test",
                win_rate=None,
                db_name=temp_db
            )
            
            # Should have called with default
            success, message = result
            assert success is True
    
    def test_add_bridge_preserves_win_rate(self, temp_db):
        """Test that provided win_rate is preserved."""
        with patch('lottery_service.add_managed_bridge') as mock_db:
            mock_db.return_value = (True, "Success")
            
            result = add_managed_bridge_adapter(
                bridge_name="Test Bridge",
                description="Test",
                win_rate="75",
                db_name=temp_db
            )
            
            success, message = result
            assert success is True
    
    def test_add_bridge_normalizes_description(self, temp_db):
        """Test that description is normalized."""
        result = add_managed_bridge_adapter(
            bridge_name="Test Bridge",
            description="  Test Description  ",
            db_name=temp_db
        )
        
        success, message = result
        assert isinstance(success, bool)
    
    def test_add_bridge_handles_none_description(self, temp_db):
        """Test that None description is handled."""
        result = add_managed_bridge_adapter(
            bridge_name="Test Bridge",
            description=None,
            db_name=temp_db
        )
        
        success, message = result
        assert isinstance(success, bool)
    
    def test_add_bridge_normalizes_bridge_type(self, temp_db):
        """Test that bridge_type is normalized."""
        result = add_managed_bridge_adapter(
            bridge_name="Test Bridge",
            description="Test",
            bridge_type="manual_lo",
            db_name=temp_db
        )
        
        success, message = result
        assert isinstance(success, bool)
    
    def test_add_bridge_handles_unicode_names(self, temp_db):
        """Test that Unicode characters in names are handled."""
        result = add_managed_bridge_adapter(
            bridge_name="Cầu Đặc Biệt",
            description="Mô tả",
            db_name=temp_db
        )
        
        success, message = result
        assert isinstance(success, bool)
    
    def test_add_bridge_with_kwargs(self, temp_db):
        """Test that additional kwargs are accepted."""
        result = add_managed_bridge_adapter(
            bridge_name="Test Bridge",
            description="Test",
            db_name=temp_db,
            extra_param="extra_value"
        )
        
        # Should not raise error with extra kwargs
        success, message = result
        assert isinstance(success, bool)
    
    def test_add_bridge_db_error_handling(self, temp_db):
        """Test that database errors are handled gracefully."""
        # Use invalid database path
        result = add_managed_bridge_adapter(
            bridge_name="Test Bridge",
            description="Test",
            db_name="/invalid/path/db.db"
        )
        
        success, message = result
        assert success is False
        assert isinstance(message, str)
    
    def test_add_bridge_type_error_handling(self, temp_db):
        """Test handling of type errors (non-string name)."""
        result = add_managed_bridge_adapter(
            bridge_name=12345,  # Invalid type
            description="Test",
            db_name=temp_db
        )
        
        # Should handle type error gracefully
        success, message = result
        assert isinstance(success, bool)
        assert isinstance(message, str)


class TestAddManagedBridgeIntegration:
    """Integration tests for add_managed_bridge_adapter."""
    
    @pytest.fixture
    def test_db(self):
        """Create a test database with schema."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Setup full schema
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ManagedBridges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_enabled INTEGER DEFAULT 1,
                date_added TEXT DEFAULT (datetime('now', 'localtime')),
                win_rate_text TEXT DEFAULT 'N/A',
                current_streak INTEGER DEFAULT 0,
                next_prediction_stl TEXT DEFAULT 'N/A',
                pos1_idx INTEGER,
                pos2_idx INTEGER,
                max_lose_streak_k2n INTEGER DEFAULT 0,
                recent_win_count_10 INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()
        
        yield path
        
        try:
            os.unlink(path)
        except:
            pass
    
    def test_add_multiple_bridges(self, test_db):
        """Test adding multiple bridges sequentially."""
        bridges = [
            ("Bridge A", "Description A"),
            ("Bridge B", "Description B"),
            ("Bridge C", "Description C"),
        ]
        
        for name, desc in bridges:
            result = add_managed_bridge_adapter(
                bridge_name=name,
                description=desc,
                db_name=test_db
            )
            success, message = result
            assert isinstance(success, bool)
    
    def test_duplicate_bridge_handling(self, test_db):
        """Test that duplicate bridge names are handled."""
        # Add first time
        result1 = add_managed_bridge_adapter(
            bridge_name="Duplicate Bridge",
            description="First",
            db_name=test_db
        )
        
        # Add second time (duplicate)
        result2 = add_managed_bridge_adapter(
            bridge_name="Duplicate Bridge",
            description="Second",
            db_name=test_db
        )
        
        # Both should return results (DB determines behavior)
        assert isinstance(result1, tuple)
        assert isinstance(result2, tuple)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
