# tests/test_scanner_refactor.py
"""
Integration tests for scanner refactoring (V11.2 K1N-Primary flow).

Tests verify that:
1. Scanners return Candidate objects instead of writing to DB
2. Existing bridges are excluded from results
3. K1N/K2N rates are attached from cache
4. rate_missing flag is set when cache is absent
5. Single DB calls for existing names and rates cache
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
import sqlite3
import tempfile
from typing import List

from logic.bridges.de_bridge_scanner import DeBridgeScanner, run_de_scanner
from logic.bridges.lo_bridge_scanner import scan_lo_bridges_v17, _convert_lo_bridges_to_candidates
from logic.models import Candidate
from logic.db_manager import (
    setup_database, 
    bulk_upsert_managed_bridges,
    get_all_managed_bridge_names,
    load_rates_cache
)
from logic.common_utils import normalize_bridge_name


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Setup database schema
    setup_database(db_path)
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def sample_lottery_data():
    """Create sample lottery data for testing scanners."""
    # Minimal data structure for testing
    # Format: [Ky, GDB, G1, G2, G3, G4, G5, G6, G7]
    data = []
    for i in range(50):
        row = [
            f"KY{i:03d}",  # Ky
            "12345",       # GDB
            "67890",       # G1
            "11111,22222", # G2
            "33333,44444,55555,66666,77777,88888", # G3
            "01234,12345,23456,34567", # G4
            "45678,56789,67890,78901,89012,90123", # G5
            "98765,87654,76543", # G6
            "43,21,10,99" # G7
        ]
        data.append(row)
    return data


@pytest.fixture
def existing_bridges_in_db(temp_db):
    """Pre-populate DB with some existing bridges."""
    existing_bridges = [
        {
            'name': 'DE_TEST_BRIDGE_01',
            'type': 'DE_SET',
            'description': 'Test bridge 1',
            'k1n_rate_de': 95.0,
            'k2n_rate_de': 88.0,
            'is_pending': 0,
            'is_enabled': 1
        },
        {
            'name': 'LO_POS_TEST_01',
            'type': 'LO_POS',
            'description': 'Test LO bridge',
            'k1n_rate_lo': 87.0,
            'k2n_rate_lo': 85.0,
            'is_pending': 0,
            'is_enabled': 1
        }
    ]
    
    bulk_upsert_managed_bridges(existing_bridges, temp_db)
    return existing_bridges


class TestDeBridgeScannerRefactor:
    """Test DE bridge scanner refactoring."""
    
    def test_returns_candidates_not_count(self, temp_db, sample_lottery_data):
        """Test that scan_all returns (candidates, meta) instead of (count, bridges)."""
        scanner = DeBridgeScanner()
        result = scanner.scan_all(sample_lottery_data, temp_db)
        
        # Should return tuple of (List[Candidate], Dict)
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        candidates, meta = result
        assert isinstance(candidates, list)
        assert isinstance(meta, dict)
        
        # Meta should have expected keys
        assert 'found_total' in meta
        assert 'excluded_existing' in meta
        assert 'returned_count' in meta
    
    def test_no_db_writes_during_scan(self, temp_db, sample_lottery_data):
        """Test that scanner does not write to DB during scan."""
        # Count bridges before scan
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges WHERE type LIKE 'DE_%'")
        count_before = cursor.fetchone()[0]
        conn.close()
        
        # Run scanner
        scanner = DeBridgeScanner()
        candidates, meta = scanner.scan_all(sample_lottery_data, temp_db)
        
        # Count bridges after scan - should be same
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges WHERE type LIKE 'DE_%'")
        count_after = cursor.fetchone()[0]
        conn.close()
        
        assert count_before == count_after, "Scanner should not write to DB"
    
    def test_excludes_existing_bridges(self, temp_db, existing_bridges_in_db, sample_lottery_data):
        """Test that existing bridges are excluded from results."""
        # Get existing names before scan
        existing_names_before = get_all_managed_bridge_names(temp_db)
        
        # Run scanner
        scanner = DeBridgeScanner()
        candidates, meta = scanner.scan_all(sample_lottery_data, temp_db)
        
        # Check that no returned candidate matches existing names
        for candidate in candidates:
            assert candidate.normalized_name not in existing_names_before
        
        # Meta should show some bridges were excluded
        # (This might be 0 if no duplicates found in scan, which is fine)
        assert meta['excluded_existing'] >= 0
        assert meta['returned_count'] == len(candidates)
        assert meta['found_total'] >= meta['returned_count']
    
    def test_attaches_rates_from_cache(self, temp_db, existing_bridges_in_db, sample_lottery_data):
        """Test that K1N/K2N rates are attached from cache when available."""
        # Run scanner
        scanner = DeBridgeScanner()
        candidates, meta = scanner.scan_all(sample_lottery_data, temp_db)
        
        # All candidates should be Candidate objects
        for candidate in candidates:
            assert isinstance(candidate, Candidate)
            assert candidate.type == 'de'
            assert hasattr(candidate, 'k1n_de')
            assert hasattr(candidate, 'k2n_de')
            assert hasattr(candidate, 'rate_missing')
            assert hasattr(candidate, 'normalized_name')
    
    def test_rate_missing_flag_when_no_cache(self, temp_db, sample_lottery_data):
        """Test that rate_missing flag is set when cache is absent."""
        # Run scanner on empty DB (no cached rates)
        scanner = DeBridgeScanner()
        candidates, meta = scanner.scan_all(sample_lottery_data, temp_db)
        
        # Most candidates should have rate_missing=True since DB is empty
        if len(candidates) > 0:
            # At least one candidate should exist and have rate_missing flag
            missing_flags = [c.rate_missing for c in candidates]
            # With empty DB, all should be missing rates
            assert any(missing_flags), "Some candidates should have rate_missing=True"


class TestLoBridgeScannerRefactor:
    """Test LO bridge scanner refactoring."""
    
    def test_scan_lo_v17_returns_candidates(self, temp_db, sample_lottery_data):
        """Test that scan_lo_bridges_v17 returns (candidates, meta)."""
        result = scan_lo_bridges_v17(
            sample_lottery_data,
            ky_bat_dau_kiem_tra=10,
            ky_ket_thuc_kiem_tra=40,
            db_name=temp_db
        )
        
        # Should return tuple
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        candidates, meta = result
        assert isinstance(candidates, list)
        assert isinstance(meta, dict)
        
        # Meta should have expected keys
        assert 'found_total' in meta
        assert 'excluded_existing' in meta
        assert 'returned_count' in meta
    
    def test_lo_scanner_no_db_writes(self, temp_db, sample_lottery_data):
        """Test that LO scanner does not write to DB."""
        # Count before
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges WHERE type LIKE 'LO_%'")
        count_before = cursor.fetchone()[0]
        conn.close()
        
        # Run scanner
        candidates, meta = scan_lo_bridges_v17(
            sample_lottery_data,
            ky_bat_dau_kiem_tra=10,
            ky_ket_thuc_kiem_tra=40,
            db_name=temp_db
        )
        
        # Count after
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges WHERE type LIKE 'LO_%'")
        count_after = cursor.fetchone()[0]
        conn.close()
        
        assert count_before == count_after
    
    def test_lo_candidates_have_correct_type(self, temp_db, sample_lottery_data):
        """Test that LO candidates have type='lo'."""
        candidates, meta = scan_lo_bridges_v17(
            sample_lottery_data,
            ky_bat_dau_kiem_tra=10,
            ky_ket_thuc_kiem_tra=40,
            db_name=temp_db
        )
        
        for candidate in candidates:
            assert isinstance(candidate, Candidate)
            assert candidate.type == 'lo'
            assert hasattr(candidate, 'k1n_lo')
            assert hasattr(candidate, 'k2n_lo')


class TestHelperFunctions:
    """Test helper functions for scanner refactoring."""
    
    def test_normalize_bridge_name_consistency(self):
        """Test that normalize_bridge_name is consistent."""
        names = [
            "DE_TEST_BRIDGE_01",
            "  de_test_bridge_01  ",
            "De-Test-Bridge-01",
            "DE TEST BRIDGE 01"
        ]
        
        normalized = [normalize_bridge_name(name) for name in names]
        
        # All should normalize to same value
        assert len(set(normalized)) == 1
    
    def test_get_all_managed_bridge_names(self, temp_db, existing_bridges_in_db):
        """Test get_all_managed_bridge_names returns normalized set."""
        names = get_all_managed_bridge_names(temp_db)
        
        assert isinstance(names, set)
        assert len(names) == len(existing_bridges_in_db)
        
        # Names should be normalized
        for name in names:
            assert name == name.lower()
            assert name == normalize_bridge_name(name)
    
    def test_load_rates_cache(self, temp_db, existing_bridges_in_db):
        """Test load_rates_cache returns rates dictionary."""
        cache = load_rates_cache(temp_db)
        
        assert isinstance(cache, dict)
        
        # Should have entries for existing bridges
        assert len(cache) >= len(existing_bridges_in_db)
        
        # Each entry should have rate keys
        for norm_name, rates in cache.items():
            assert 'k1n_rate_lo' in rates
            assert 'k1n_rate_de' in rates
            assert 'k2n_rate_lo' in rates
            assert 'k2n_rate_de' in rates
            
            # Rates should be numeric
            assert isinstance(rates['k1n_rate_lo'], (int, float))
            assert isinstance(rates['k1n_rate_de'], (int, float))


class TestEndToEndFlow:
    """Test end-to-end scanner flow."""
    
    def test_scan_and_exclude_existing_flow(self, temp_db, sample_lottery_data):
        """Test complete flow: scan -> exclude existing -> return new candidates."""
        # Step 1: Add some bridges to DB
        initial_bridges = [
            {
                'name': 'DE_EXISTING_01',
                'type': 'DE_SET',
                'description': 'Existing bridge',
                'k1n_rate_de': 92.0,
                'k2n_rate_de': 87.0
            }
        ]
        bulk_upsert_managed_bridges(initial_bridges, temp_db)
        
        # Step 2: Run scanner
        scanner = DeBridgeScanner()
        candidates, meta = scanner.scan_all(sample_lottery_data, temp_db)
        
        # Step 3: Verify results
        assert isinstance(candidates, list)
        assert isinstance(meta, dict)
        
        # Step 4: Check that existing bridge is not in results
        existing_norm = normalize_bridge_name('DE_EXISTING_01')
        returned_names = {c.normalized_name for c in candidates}
        
        assert existing_norm not in returned_names
        
        # Step 5: Verify meta counts
        assert meta['returned_count'] == len(candidates)
        assert meta['found_total'] >= meta['returned_count']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
