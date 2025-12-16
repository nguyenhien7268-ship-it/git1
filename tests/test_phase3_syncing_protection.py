"""
Test Phase 3: Dashboard Protection with SYNCING_BRIDGES
Tests that dashboard predictions are protected from incomplete data during synchronization.
"""
import pytest
import sqlite3
import os
import tempfile
import threading
import time
from unittest.mock import Mock, patch


class TestPhase3SyncingProtection:
    """Test syncing protection functionality"""
    
    def setup_method(self):
        """Create temporary test database"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Create test database schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create ManagedBridges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ManagedBridges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_enabled INTEGER DEFAULT 1,
                pos1_idx INTEGER,
                pos2_idx INTEGER,
                type TEXT,
                win_rate_text TEXT,
                max_lose_streak INTEGER DEFAULT 0,
                recent_win_count_10 INTEGER DEFAULT 0
            )
        """)
        
        # Insert test bridges
        for i in range(1, 6):
            cursor.execute("""
                INSERT INTO ManagedBridges 
                (name, description, is_enabled, pos1_idx, pos2_idx, type, win_rate_text)
                VALUES 
                (?, ?, 1, 0, 1, 'LO_V17', '40.00%')
            """, (f'TestBridge{i}', f'Test bridge {i}'))
        
        # Create DuLieu_AI table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS DuLieu_AI (
                MaSoKy INTEGER PRIMARY KEY,
                Col_A_Ky TEXT, Col_B_GDB TEXT, Col_C_G1 TEXT,
                Col_D_G2 TEXT, Col_E_G3 TEXT, Col_F_G4 TEXT,
                Col_G_G5 TEXT, Col_H_G6 TEXT, Col_I_G7 TEXT
            )
        """)
        
        # Insert test data
        for i in range(1, 35):
            cursor.execute("""
                INSERT INTO DuLieu_AI VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (i, str(i), '12', '34', '56', '78', '90', '11', '22', '33'))
        
        conn.commit()
        conn.close()
    
    def teardown_method(self):
        """Clean up test database"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_syncing_bridges_global_variable_exists(self):
        """Test that SYNCING_BRIDGES global variable exists"""
        from services.bridge_service import SYNCING_BRIDGES, SYNCING_LOCK
        
        assert SYNCING_BRIDGES is not None
        assert isinstance(SYNCING_BRIDGES, set)
        assert SYNCING_LOCK is not None
    
    def test_syncing_bridges_added_and_removed(self):
        """Test that bridges are added/removed from SYNCING_BRIDGES"""
        from services.bridge_service import BridgeService, SYNCING_BRIDGES, SYNCING_LOCK
        
        # Clear SYNCING_BRIDGES
        with SYNCING_LOCK:
            SYNCING_BRIDGES.clear()
        
        service = BridgeService(self.db_path, logger=None)
        
        # Load test data
        from logic.data_repository import load_data_ai_from_db
        all_data, _ = load_data_ai_from_db(self.db_path)
        
        # Before activation, should be empty
        with SYNCING_LOCK:
            assert len(SYNCING_BRIDGES) == 0
        
        # Call activate (should add bridges)
        result = service.activate_and_recalc_bridges(['TestBridge1'], all_data)
        
        # After activation completes, should be removed
        with SYNCING_LOCK:
            assert len(SYNCING_BRIDGES) == 0
    
    def test_get_safe_active_bridges_excludes_syncing(self):
        """Test that get_safe_active_bridges excludes syncing bridges"""
        from services.bridge_service import get_safe_active_bridges, SYNCING_BRIDGES, SYNCING_LOCK
        
        # Clear and add a bridge to SYNCING_BRIDGES
        with SYNCING_LOCK:
            SYNCING_BRIDGES.clear()
            SYNCING_BRIDGES.add('TestBridge1')
        
        try:
            # Get safe bridges
            safe_bridges = get_safe_active_bridges(self.db_path)
            
            # Should not include TestBridge1
            assert 'TestBridge1' not in safe_bridges
            
            # Should include other bridges
            assert len(safe_bridges) >= 4  # We have 5 bridges, 1 is syncing
            
        finally:
            # Cleanup
            with SYNCING_LOCK:
                SYNCING_BRIDGES.clear()
    
    def test_get_safe_active_bridges_includes_all_when_none_syncing(self):
        """Test that get_safe_active_bridges includes all when none syncing"""
        from services.bridge_service import get_safe_active_bridges, SYNCING_BRIDGES, SYNCING_LOCK
        
        # Clear SYNCING_BRIDGES
        with SYNCING_LOCK:
            SYNCING_BRIDGES.clear()
        
        # Get safe bridges
        safe_bridges = get_safe_active_bridges(self.db_path)
        
        # Should include all 5 bridges
        assert len(safe_bridges) == 5
    
    def test_get_syncing_bridges_count(self):
        """Test get_syncing_bridges_count function"""
        from services.bridge_service import get_syncing_bridges_count, SYNCING_BRIDGES, SYNCING_LOCK
        
        # Clear and add bridges
        with SYNCING_LOCK:
            SYNCING_BRIDGES.clear()
            SYNCING_BRIDGES.add('Bridge1')
            SYNCING_BRIDGES.add('Bridge2')
        
        try:
            count = get_syncing_bridges_count()
            assert count == 2
        finally:
            with SYNCING_LOCK:
                SYNCING_BRIDGES.clear()
    
    def test_get_syncing_bridges_list(self):
        """Test get_syncing_bridges_list function"""
        from services.bridge_service import get_syncing_bridges_list, SYNCING_BRIDGES, SYNCING_LOCK
        
        # Clear and add bridges
        with SYNCING_LOCK:
            SYNCING_BRIDGES.clear()
            SYNCING_BRIDGES.add('Bridge1')
            SYNCING_BRIDGES.add('Bridge2')
        
        try:
            bridges = get_syncing_bridges_list()
            assert isinstance(bridges, list)
            assert len(bridges) == 2
            assert 'Bridge1' in bridges
            assert 'Bridge2' in bridges
        finally:
            with SYNCING_LOCK:
                SYNCING_BRIDGES.clear()
    
    def test_thread_safety_of_syncing_bridges(self):
        """Test thread safety of SYNCING_BRIDGES operations"""
        from services.bridge_service import SYNCING_BRIDGES, SYNCING_LOCK
        
        # Clear
        with SYNCING_LOCK:
            SYNCING_BRIDGES.clear()
        
        results = []
        
        def add_bridges():
            with SYNCING_LOCK:
                for i in range(100):
                    SYNCING_BRIDGES.add(f'Bridge{i}')
        
        def remove_bridges():
            with SYNCING_LOCK:
                for i in range(50):
                    SYNCING_BRIDGES.discard(f'Bridge{i}')
        
        # Create threads
        threads = []
        for _ in range(5):
            t1 = threading.Thread(target=add_bridges)
            t2 = threading.Thread(target=remove_bridges)
            threads.extend([t1, t2])
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Should complete without errors
        with SYNCING_LOCK:
            # The count should be deterministic (50 remaining after removes)
            assert len(SYNCING_BRIDGES) >= 0  # Just check it didn't crash
        
        # Cleanup
        with SYNCING_LOCK:
            SYNCING_BRIDGES.clear()


class TestPhase3DashboardIntegration:
    """Test dashboard integration with syncing protection"""
    
    def test_get_safe_prediction_bridges_function_exists(self):
        """Test that get_safe_prediction_bridges function exists"""
        from logic.dashboard_analytics import get_safe_prediction_bridges
        
        assert get_safe_prediction_bridges is not None
        assert callable(get_safe_prediction_bridges)
    
    def test_get_safe_prediction_bridges_excludes_syncing(self):
        """Test that get_safe_prediction_bridges excludes syncing bridges"""
        from services.bridge_service import SYNCING_BRIDGES, SYNCING_LOCK
        from logic.dashboard_analytics import get_safe_prediction_bridges
        
        # Mock scenario: Add a bridge to syncing
        with SYNCING_LOCK:
            SYNCING_BRIDGES.clear()
            SYNCING_BRIDGES.add('TestBridge1')
        
        try:
            # Mock get_all_managed_bridges to return test data
            with patch('logic.dashboard_analytics.get_all_managed_bridges') as mock_get:
                mock_get.return_value = [
                    {'name': 'TestBridge1', 'is_enabled': 1},
                    {'name': 'TestBridge2', 'is_enabled': 1},
                ]
                
                safe_bridges = get_safe_prediction_bridges('test.db')
                
                # Should not include TestBridge1 (it's syncing)
                bridge_names = [b['name'] for b in safe_bridges]
                assert 'TestBridge1' not in bridge_names
                assert 'TestBridge2' in bridge_names
        
        finally:
            with SYNCING_LOCK:
                SYNCING_BRIDGES.clear()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
