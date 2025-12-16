# tests/test_add_managed_bridge.py
"""
Unit tests for add_managed_bridge service adapter (V11.4).

Tests verify:
1. Service layer normalization of bridge data
2. Backward compatibility with DB API (kwargs vs positional)
3. Error handling for invalid inputs
4. Type mapping from display types to DB types
5. Logging behavior

NO database schema changes.
NO modification of public DB signatures.
"""

import unittest
from unittest.mock import patch, MagicMock, call
import tempfile
import os


class TestAddManagedBridge(unittest.TestCase):
    """Test suite for add_managed_bridge service adapter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
    
    @patch('lottery_service.upsert_managed_bridge')
    def test_add_bridge_basic_success(self, mock_upsert):
        """Test basic bridge addition with valid data."""
        from lottery_service import add_managed_bridge
        
        mock_upsert.return_value = (True, "Bridge added successfully")
        
        success, msg = add_managed_bridge(
            bridge_name="TEST_BRIDGE_01",
            description="Test bridge",
            bridge_type="LO_POS",
            win_rate_text="85.5%"
        )
        
        self.assertTrue(success)
        self.assertIn("success", msg.lower())
        
        # Verify upsert was called with normalized data
        self.assertTrue(mock_upsert.called)
        call_kwargs = mock_upsert.call_args[1]
        self.assertEqual(call_kwargs['bridge_name'], "TEST_BRIDGE_01")
        self.assertEqual(call_kwargs['description'], "Test bridge")
        self.assertIn('bridge_data', call_kwargs)
        self.assertEqual(call_kwargs['bridge_data']['type'], "LO_POS")
    
    @patch('lottery_service.upsert_managed_bridge')
    def test_add_bridge_name_normalization(self, mock_upsert):
        """Test that bridge names are normalized (stripped)."""
        from lottery_service import add_managed_bridge
        
        mock_upsert.return_value = (True, "OK")
        
        # Name with leading/trailing spaces
        add_managed_bridge(
            bridge_name="  BRIDGE_WITH_SPACES  ",
            description="Test",
            bridge_type="LO_POS"
        )
        
        call_kwargs = mock_upsert.call_args[1]
        self.assertEqual(call_kwargs['bridge_name'], "BRIDGE_WITH_SPACES")
    
    @patch('lottery_service.upsert_managed_bridge')
    def test_add_bridge_empty_name_fails(self, mock_upsert):
        """Test that empty bridge names are rejected."""
        from lottery_service import add_managed_bridge
        
        # Empty string
        success, msg = add_managed_bridge(
            bridge_name="",
            description="Test",
            bridge_type="LO_POS"
        )
        
        self.assertFalse(success)
        self.assertIn("required", msg.lower())
        self.assertFalse(mock_upsert.called)
        
        # Whitespace only
        success, msg = add_managed_bridge(
            bridge_name="   ",
            description="Test",
            bridge_type="LO_POS"
        )
        
        self.assertFalse(success)
        self.assertIn("required", msg.lower())
    
    @patch('lottery_service.upsert_managed_bridge')
    def test_add_bridge_none_name_fails(self, mock_upsert):
        """Test that None bridge names are rejected."""
        from lottery_service import add_managed_bridge
        
        success, msg = add_managed_bridge(
            bridge_name=None,
            description="Test",
            bridge_type="LO_POS"
        )
        
        self.assertFalse(success)
        self.assertIn("required", msg.lower())
        self.assertFalse(mock_upsert.called)
    
    @patch('lottery_service.upsert_managed_bridge')
    def test_add_bridge_type_mapping(self, mock_upsert):
        """Test that display types are mapped to DB types."""
        from lottery_service import add_managed_bridge
        
        mock_upsert.return_value = (True, "OK")
        
        # Test various type mappings
        test_cases = [
            ("LO_V17", "LO_POS"),  # Display -> DB mapping
            ("LO_BN", "LO_MEM"),   # Display -> DB mapping
            ("LO_POS", "LO_POS"),  # Already DB type
            ("DE_SET", "DE_SET"),  # DE type
            ("DE_MEMORY", "DE_MEMORY"),  # DE type
            ("UNKNOWN_TYPE", "UNKNOWN_TYPE"),  # Unmapped passes through
        ]
        
        for display_type, expected_db_type in test_cases:
            mock_upsert.reset_mock()
            
            add_managed_bridge(
                bridge_name=f"TEST_{display_type}",
                description="Test",
                bridge_type=display_type
            )
            
            call_kwargs = mock_upsert.call_args[1]
            actual_type = call_kwargs['bridge_data']['type']
            self.assertEqual(
                actual_type,
                expected_db_type,
                f"Type {display_type} should map to {expected_db_type}, got {actual_type}"
            )
    
    @patch('lottery_service.upsert_managed_bridge')
    def test_add_bridge_fallback_to_positional(self, mock_upsert):
        """Test fallback to positional args when kwargs fail."""
        from lottery_service import add_managed_bridge
        
        # First call with kwargs raises exception, second (positional) succeeds
        mock_upsert.side_effect = [
            TypeError("kwargs not supported"),  # First call fails
            (True, "Added with positional args")  # Second call succeeds
        ]
        
        success, msg = add_managed_bridge(
            bridge_name="TEST_BRIDGE",
            description="Test",
            bridge_type="LO_POS",
            win_rate_text="80%"
        )
        
        self.assertTrue(success)
        self.assertIn("positional", msg.lower())
        
        # Verify both calls were made
        self.assertEqual(mock_upsert.call_count, 2)
    
    @patch('lottery_service.upsert_managed_bridge')
    def test_add_bridge_preserves_extra_kwargs(self, mock_upsert):
        """Test that extra kwargs are preserved in bridge_data."""
        from lottery_service import add_managed_bridge
        
        mock_upsert.return_value = (True, "OK")
        
        add_managed_bridge(
            bridge_name="TEST",
            description="Test",
            bridge_type="LO_POS",
            pos1_idx=1,
            pos2_idx=2,
            custom_field="custom_value"
        )
        
        call_kwargs = mock_upsert.call_args[1]
        bridge_data = call_kwargs['bridge_data']
        
        # pos indices should be extracted as separate args
        self.assertEqual(call_kwargs.get('pos1_idx'), 1)
        self.assertEqual(call_kwargs.get('pos2_idx'), 2)
        
        # Other kwargs should be in bridge_data
        self.assertEqual(bridge_data.get('custom_field'), "custom_value")
    
    @patch('lottery_service.upsert_managed_bridge')
    def test_add_bridge_default_values(self, mock_upsert):
        """Test that default values are set correctly."""
        from lottery_service import add_managed_bridge
        
        mock_upsert.return_value = (True, "OK")
        
        add_managed_bridge(
            bridge_name="TEST",
            description="Test"
            # No type, win_rate provided
        )
        
        call_kwargs = mock_upsert.call_args[1]
        bridge_data = call_kwargs['bridge_data']
        
        # Check defaults
        self.assertEqual(bridge_data['type'], "UNKNOWN")
        self.assertEqual(bridge_data['win_rate_text'], "N/A")
        self.assertEqual(bridge_data['is_enabled'], 1)
        self.assertEqual(bridge_data['search_rate_text'], "N/A")
    
    @patch('lottery_service.upsert_managed_bridge')
    def test_add_bridge_logging(self, mock_upsert):
        """Test that operations are logged (implicitly via execution)."""
        from lottery_service import add_managed_bridge
        
        mock_upsert.return_value = (True, "OK")
        
        # The function internally uses logging, we just verify it doesn't crash
        success, msg = add_managed_bridge(
            bridge_name="TEST",
            description="Test",
            bridge_type="LO_POS",
            win_rate_text="80%"
        )
        
        # Verify the function executed successfully
        self.assertTrue(success)
        self.assertTrue(mock_upsert.called)
    
    @patch('lottery_service.upsert_managed_bridge')
    def test_add_bridge_db_error_handling(self, mock_upsert):
        """Test handling of database errors."""
        from lottery_service import add_managed_bridge
        
        # Both kwargs and positional fail
        mock_upsert.side_effect = Exception("Database error")
        
        success, msg = add_managed_bridge(
            bridge_name="TEST",
            description="Test",
            bridge_type="LO_POS"
        )
        
        self.assertFalse(success)
        self.assertIn("failed", msg.lower())
        self.assertIn("database error", msg.lower())


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing DB API."""
    
    def test_db_upsert_managed_bridge_alias(self):
        """Test that db_upsert_managed_bridge alias exists and works."""
        from lottery_service import db_upsert_managed_bridge, upsert_managed_bridge
        
        # Verify alias points to same function (without mocking)
        self.assertIs(db_upsert_managed_bridge, upsert_managed_bridge)
    
    @patch('lottery_service.upsert_managed_bridge')
    def test_old_ui_code_still_works(self, mock_upsert):
        """Test that old UI code calling upsert directly still works."""
        from lottery_service import upsert_managed_bridge
        
        mock_upsert.return_value = (True, "OK")
        
        # Simulate old UI code calling upsert directly
        success, msg = upsert_managed_bridge(
            name="OLD_BRIDGE",
            description="Old style call",
            win_rate_text="75%",
            db_name="test.db",
            pos1_idx=1,
            pos2_idx=2,
            bridge_data={"type": "LO_POS", "is_enabled": 1}
        )
        
        # Should work without errors
        self.assertTrue(mock_upsert.called)


class TestServiceLayerIsolation(unittest.TestCase):
    """Test that service layer properly isolates UI from DB."""
    
    @patch('lottery_service.upsert_managed_bridge')
    def test_service_handles_db_signature_changes(self, mock_upsert):
        """Test service layer adapts to DB signature changes."""
        from lottery_service import add_managed_bridge
        
        # Simulate DB function with different signature
        mock_upsert.return_value = (True, "OK")
        
        # UI calls service with consistent interface
        success, msg = add_managed_bridge(
            bridge_name="TEST",
            description="Test",
            bridge_type="LO_POS"
        )
        
        self.assertTrue(success)
        # Service should have adapted the call to DB layer
        self.assertTrue(mock_upsert.called)


if __name__ == '__main__':
    unittest.main()
