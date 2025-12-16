"""
Test Phase 2: Bridge Revival in Scanner
Tests that scanners revive disabled bridges instead of skipping them.
"""
import pytest
import sqlite3
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock


class TestPhase2BridgeRevival:
    """Test bridge revival functionality in scanners"""
    
    def setup_method(self):
        """Create temporary test database with a disabled bridge"""
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
                recent_win_count_10 INTEGER DEFAULT 0,
                search_rate_text TEXT,
                search_period INTEGER DEFAULT 0,
                is_pinned INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)
        
        # Insert a DISABLED test bridge
        cursor.execute("""
            INSERT INTO ManagedBridges 
            (name, description, is_enabled, pos1_idx, pos2_idx, type, win_rate_text)
            VALUES 
            ('LO_POS_Test1_Test2', 'Test bridge - disabled', 0, 0, 1, 'LO_POS', '30.00%')
        """)
        
        # Create DuLieu_AI table with test data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS DuLieu_AI (
                MaSoKy INTEGER PRIMARY KEY,
                Col_A_Ky TEXT,
                Col_B_GDB TEXT,
                Col_C_G1 TEXT,
                Col_D_G2 TEXT,
                Col_E_G3 TEXT,
                Col_F_G4 TEXT,
                Col_G_G5 TEXT,
                Col_H_G6 TEXT,
                Col_I_G7 TEXT
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
    
    def test_lo_scanner_revives_disabled_bridge(self):
        """Test that LO scanner revives disabled bridges instead of skipping"""
        from logic.bridges.lo_bridge_scanner import _convert_lo_bridges_to_candidates
        from logic.common_utils import normalize_bridge_name
        
        # Setup test data
        bridge_dicts = [{
            'name': 'LO_POS_Test1_Test2',
            'type': 'LO_POS',
            'db_name': self.db_path,
            'win_rate': 30.0,
            'predicted_value': '12,34',
            'streak': 2,
            'win_count_10': 3,
            'pos1_idx': 0,
            'pos2_idx': 1,
            'description': 'Test bridge'
        }]
        
        existing_names = {normalize_bridge_name('LO_POS_Test1_Test2')}
        rates_cache = {}
        
        # Mock bridge service to avoid actual activation
        with patch('logic.bridges.lo_bridge_scanner.BridgeService') as MockService:
            mock_service_instance = Mock()
            MockService.return_value = mock_service_instance
            mock_service_instance.activate_and_recalc_bridges.return_value = {
                'success': True,
                'message': 'Test success',
                'updated_bridges': []
            }
            
            # Call the function
            candidates = _convert_lo_bridges_to_candidates(
                bridge_dicts, 
                existing_names, 
                rates_cache
            )
            
            # Should attempt to revive the bridge
            assert mock_service_instance.activate_and_recalc_bridges.called
            
            # Should not create candidate since bridge exists
            assert len(candidates) == 0
    
    def test_de_scanner_revives_disabled_bridge(self):
        """Test that DE scanner revives disabled bridges instead of skipping"""
        # Create a disabled DE bridge
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ManagedBridges 
            (name, description, is_enabled, type, win_rate_text)
            VALUES 
            ('DE_SET_Test', 'Test DE bridge - disabled', 0, 'DE_SET', '25.00%')
        """)
        conn.commit()
        conn.close()
        
        from logic.bridges.de_bridge_scanner import DeBridgeScanner
        from logic.common_utils import normalize_bridge_name
        
        scanner = DeBridgeScanner()
        
        bridge_dicts = [{
            'name': 'DE_SET_Test',
            'type': 'DE_SET',
            'win_rate': 25.0,
            'full_dan': '01-02-03',
            'streak': 3,
            'display_desc': 'Test DE bridge',
            'ranking_score': 10.0
        }]
        
        existing_names = {normalize_bridge_name('DE_SET_Test')}
        rates_cache = {}
        
        # Mock bridge service
        with patch('logic.bridges.de_bridge_scanner.BridgeService') as MockService:
            mock_service_instance = Mock()
            MockService.return_value = mock_service_instance
            mock_service_instance.activate_and_recalc_bridges.return_value = {
                'success': True,
                'message': 'Test success',
                'updated_bridges': []
            }
            
            # Call the function
            candidates = scanner._convert_to_candidates(
                bridge_dicts, 
                existing_names, 
                rates_cache,
                self.db_path
            )
            
            # Should attempt to revive the bridge
            assert mock_service_instance.activate_and_recalc_bridges.called
            
            # Should not create candidate since bridge exists
            assert len(candidates) == 0
    
    def test_scanner_skips_enabled_bridges(self):
        """Test that scanner skips bridges that are already enabled"""
        # Create an ENABLED bridge
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ManagedBridges 
            (name, description, is_enabled, type, win_rate_text)
            VALUES 
            ('LO_POS_Enabled', 'Test enabled bridge', 1, 'LO_POS', '40.00%')
        """)
        conn.commit()
        conn.close()
        
        from logic.bridges.lo_bridge_scanner import _convert_lo_bridges_to_candidates
        from logic.common_utils import normalize_bridge_name
        
        bridge_dicts = [{
            'name': 'LO_POS_Enabled',
            'type': 'LO_POS',
            'db_name': self.db_path,
            'win_rate': 40.0,
            'predicted_value': '12,34'
        }]
        
        existing_names = {normalize_bridge_name('LO_POS_Enabled')}
        rates_cache = {}
        
        # Mock bridge service
        with patch('logic.bridges.lo_bridge_scanner.BridgeService') as MockService:
            mock_service_instance = Mock()
            MockService.return_value = mock_service_instance
            
            # Call the function
            candidates = _convert_lo_bridges_to_candidates(
                bridge_dicts, 
                existing_names, 
                rates_cache
            )
            
            # Should NOT attempt to revive an enabled bridge
            assert not mock_service_instance.activate_and_recalc_bridges.called
            
            # Should not create candidate since bridge exists
            assert len(candidates) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
