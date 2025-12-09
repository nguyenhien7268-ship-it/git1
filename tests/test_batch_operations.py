# tests/test_batch_operations.py
# Unit tests for batch add/delete operations (V11.1)

import unittest
import sqlite3
import os
import tempfile
import json
from datetime import datetime

# Import functions to test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.db_manager import (
    setup_database,
    upsert_managed_bridge,
    delete_managed_bridges,
    _upsert_managed_bridge_impl
)


class TestBatchOperations(unittest.TestCase):
    """Test batch add and delete operations"""
    
    def setUp(self):
        """Create a temporary database for each test"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Setup database schema
        setup_database(self.db_path)
    
    def tearDown(self):
        """Clean up temporary database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_upsert_with_dict(self):
        """Test upsert_managed_bridge with dict parameter"""
        bridge_dict = {
            'name': 'Test_Bridge_1',
            'description': 'Test description',
            'type': 'LO_POS',
            'win_rate_text': '85.5%',
            'is_enabled': 1
        }
        
        success, msg = upsert_managed_bridge(bridge_dict=bridge_dict, db_name=self.db_path)
        self.assertTrue(success)
        self.assertIn('thêm', msg.lower())
        
        # Verify in DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, type FROM ManagedBridges WHERE name = ?", ('Test_Bridge_1',))
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 'Test_Bridge_1')
        self.assertEqual(row[1], 'LO_POS')
    
    def test_upsert_with_kwargs(self):
        """Test upsert_managed_bridge with kwargs"""
        success, msg = upsert_managed_bridge(
            name='Test_Bridge_2',
            description='Test desc 2',
            type='DE_DYN',
            win_rate_text='90.0%',
            db_name=self.db_path
        )
        
        self.assertTrue(success)
        self.assertIn('thêm', msg.lower())
        
        # Verify in DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, type FROM ManagedBridges WHERE name = ?", ('Test_Bridge_2',))
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 'Test_Bridge_2')
        self.assertEqual(row[1], 'DE_DYN')
    
    def test_upsert_key_normalization(self):
        """Test that Vietnamese keys are normalized to English"""
        bridge_dict = {
            'ten': 'Test_Bridge_3',  # Vietnamese for 'name'
            'mo_ta': 'Mô tả',  # Vietnamese for 'description'
            'loai': 'LO_MEM',  # Vietnamese for 'type'
            'ty_le': '75.0%'  # Vietnamese for 'win_rate'
        }
        
        conn = sqlite3.connect(self.db_path)
        success, msg = _upsert_managed_bridge_impl(conn, bridge_dict, self.db_path)
        conn.commit()
        conn.close()
        
        self.assertTrue(success)
        
        # Verify in DB
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, type FROM ManagedBridges WHERE name = ?", ('Test_Bridge_3',))
        row = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 'Test_Bridge_3')
        self.assertEqual(row[1], 'Mô tả')
        self.assertEqual(row[2], 'LO_MEM')
    
    def test_delete_multiple_bridges(self):
        """Test bulk delete operation"""
        # Add multiple bridges
        for i in range(1, 6):
            upsert_managed_bridge(
                name=f'Bridge_{i}',
                description=f'Desc {i}',
                type='LO_POS',
                db_name=self.db_path
            )
        
        # Get IDs
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM ManagedBridges WHERE name LIKE 'Bridge_%' ORDER BY id")
        ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        self.assertEqual(len(ids), 5)
        
        # Delete first 3
        ids_to_delete = ids[:3]
        success, msg, count = delete_managed_bridges(ids_to_delete, self.db_path)
        
        self.assertTrue(success)
        self.assertEqual(count, 3)
        self.assertIn('3', msg)
        
        # Verify remaining bridges
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges WHERE name LIKE 'Bridge_%'")
        remaining = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(remaining, 2)
    
    def test_delete_empty_list(self):
        """Test delete with empty list"""
        success, msg, count = delete_managed_bridges([], self.db_path)
        
        self.assertTrue(success)
        self.assertEqual(count, 0)
        self.assertIn('Không có', msg)
    
    def test_batch_add_with_errors(self):
        """Test batch add handles individual errors gracefully"""
        # Add first bridge
        upsert_managed_bridge(
            name='Duplicate_Bridge',
            description='First',
            type='LO_POS',
            db_name=self.db_path
        )
        
        # Try to add multiple bridges including duplicate
        bridges = [
            {'name': 'New_Bridge_1', 'type': 'LO_POS'},
            {'name': 'Duplicate_Bridge', 'type': 'LO_POS'},  # Duplicate
            {'name': 'New_Bridge_2', 'type': 'DE_DYN'},
        ]
        
        results = []
        for bridge in bridges:
            success, msg = upsert_managed_bridge(bridge_dict=bridge, db_name=self.db_path)
            results.append({'name': bridge['name'], 'success': success, 'msg': msg})
        
        # First should succeed (new)
        self.assertTrue(results[0]['success'])
        
        # Second should succeed (update)
        self.assertTrue(results[1]['success'])
        self.assertIn('CẬP NHẬT', results[1]['msg'])
        
        # Third should succeed (new)
        self.assertTrue(results[2]['success'])
        
        # Verify all 3 exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 3)


if __name__ == '__main__':
    unittest.main()
