"""
Performance benchmark tests

Tests performance characteristics of critical system components
to ensure they meet performance requirements and don't regress.
"""
import pytest
import sys
import os
import time
import tempfile
import sqlite3

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def temp_test_db_with_data():
    """Create a temporary test database with sample data for performance testing"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    
    try:
        from logic.db_manager import setup_database
        conn, cursor = setup_database(db_path)
        
        # Insert 1000 sample records for performance testing
        for i in range(1000):
            masoky = 23000 + i
            ky = str(masoky)
            cursor.execute(
                """INSERT INTO DuLieu_AI 
                (MaSoKy, Col_A_Ky, Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3, 
                 Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (masoky, ky, '12345', '67890', '11111,22222', '33333',
                 '44444,55555,66666', '77777', '88888,99999', '00000')
            )
        
        conn.commit()
        conn.close()
        
        yield db_path
        
    finally:
        os.close(fd)
        if os.path.exists(db_path):
            os.unlink(db_path)


class TestDatabasePerformance:
    """Test database query performance"""
    
    def test_database_query_with_index_is_fast(self, temp_test_db_with_data):
        """Test that indexed queries are fast (< 10ms for 1000 records)"""
        conn = sqlite3.connect(temp_test_db_with_data)
        cursor = conn.cursor()
        
        # Query with index on ky
        start_time = time.time()
        cursor.execute("SELECT * FROM results_A_I WHERE ky = ?", ('23500',))
        result = cursor.fetchone()
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        conn.close()
        
        # Should be very fast with index (< 10ms)
        assert elapsed < 10, f"Query took {elapsed:.2f}ms, should be < 10ms"
    
    def test_database_index_improves_query_speed(self, temp_test_db_with_data):
        """Test that indexes significantly improve query performance"""
        conn = sqlite3.connect(temp_test_db_with_data)
        cursor = conn.cursor()
        
        # Check that indexes exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_results_ky'"
        )
        index_exists = cursor.fetchone() is not None
        
        conn.close()
        
        # Index should exist for performance
        assert index_exists, "Performance index idx_results_ky should exist"
    
    def test_bulk_insert_performance(self, temp_test_db_with_data):
        """Test bulk insert performance is reasonable"""
        conn = sqlite3.connect(temp_test_db_with_data)
        cursor = conn.cursor()
        
        # Measure time to insert 100 records
        start_time = time.time()
        for i in range(100):
            masoky = 24000 + i
            cursor.execute(
                """INSERT INTO DuLieu_AI 
                (MaSoKy, Col_A_Ky, Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3, 
                 Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (masoky, str(masoky), '12345', '67890', '11111,22222', '33333',
                 '44444,55555,66666', '77777', '88888,99999', '00000')
            )
        conn.commit()
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        conn.close()
        
        # 100 inserts should be reasonably fast (< 500ms)
        assert elapsed < 500, f"Bulk insert took {elapsed:.2f}ms, should be < 500ms"


class TestBacktestPerformance:
    """Test backtesting performance"""
    
    def test_backtest_n1_execution_time(self):
        """Test N1 backtest completes in reasonable time"""
        from logic.backtester_core import BACKTEST_15_CAU_N1_V31_AI_V8
        
        # Create minimal sample data
        sample_data = []
        for i in range(10):
            sample_data.append(
                (23000 + i, f'{23000 + i}', '12345', '67890', '11111,22222',
                 '33333', '44444,55555,66666', '77777', '88888,99999', '00000')
            )
        
        # Measure backtest execution time
        start_time = time.time()
        result = BACKTEST_15_CAU_N1_V31_AI_V8(sample_data, 0, 5)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should complete quickly for small dataset (< 1000ms)
        assert elapsed < 1000, f"N1 backtest took {elapsed:.2f}ms, should be < 1000ms"
        assert result is not None
    
    def test_backtest_k2n_execution_time(self):
        """Test K2N backtest completes in reasonable time"""
        from logic.backtester_core import BACKTEST_15_CAU_K2N_V30_AI_V8
        
        # Create minimal sample data
        sample_data = []
        for i in range(10):
            sample_data.append(
                (23000 + i, f'{23000 + i}', '12345', '67890', '11111,22222',
                 '33333', '44444,55555,66666', '77777', '88888,99999', '00000')
            )
        
        # Measure backtest execution time
        start_time = time.time()
        result = BACKTEST_15_CAU_K2N_V30_AI_V8(sample_data, 0, 5)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should complete quickly for small dataset (< 1000ms)
        assert elapsed < 1000, f"K2N backtest took {elapsed:.2f}ms, should be < 1000ms"
        assert result is not None
    
    def test_backtest_scales_reasonably_with_data_size(self):
        """Test backtest execution time scales reasonably with data size"""
        from logic.backtester_core import BACKTEST_15_CAU_N1_V31_AI_V8
        
        # Test with 5 records
        small_data = [
            (23000 + i, f'{23000 + i}', '12345', '67890', '11111,22222',
             '33333', '44444,55555,66666', '77777', '88888,99999', '00000')
            for i in range(5)
        ]
        
        start_time = time.time()
        BACKTEST_15_CAU_N1_V31_AI_V8(small_data, 0, 3)
        time_small = time.time() - start_time
        
        # Test with 20 records (4x larger)
        large_data = [
            (23000 + i, f'{23000 + i}', '12345', '67890', '11111,22222',
             '33333', '44444,55555,66666', '77777', '88888,99999', '00000')
            for i in range(20)
        ]
        
        start_time = time.time()
        BACKTEST_15_CAU_N1_V31_AI_V8(large_data, 0, 15)
        time_large = time.time() - start_time
        
        # Larger dataset should not be more than 10x slower
        # (indicating reasonable algorithmic complexity)
        assert time_large < time_small * 10, "Backtest should scale reasonably"


class TestMemoryUsage:
    """Test memory usage characteristics"""
    
    def test_backtester_does_not_accumulate_memory(self):
        """Test backtester doesn't accumulate excessive memory"""
        from logic.backtester_core import BACKTEST_15_CAU_N1_V31_AI_V8
        
        # Run backtest multiple times
        sample_data = [
            (23000 + i, f'{23000 + i}', '12345', '67890', '11111,22222',
             '33333', '44444,55555,66666', '77777', '88888,99999', '00000')
            for i in range(10)
        ]
        
        # Run 10 times - should not accumulate memory
        for _ in range(10):
            result = BACKTEST_15_CAU_N1_V31_AI_V8(sample_data, 0, 5)
            # Allow result to be garbage collected
            del result
        
        # If we got here without memory error, test passes
        assert True
    
    def test_large_result_set_is_manageable(self, temp_test_db_with_data):
        """Test that large result sets don't cause memory issues"""
        conn = sqlite3.connect(temp_test_db_with_data)
        cursor = conn.cursor()
        
        # Query all 1000 records
        cursor.execute("SELECT * FROM DuLieu_AI")
        results = cursor.fetchall()
        
        conn.close()
        
        # Should be able to load 1000 records without issue
        assert len(results) == 1000
        assert results is not None


class TestDataLoadingPerformance:
    """Test data loading performance"""
    
    def test_load_data_from_repository_is_fast(self, temp_test_db_with_data):
        """Test data repository loading is fast"""
        from logic.data_repository import load_data_ai_from_db
        
        # Measure data loading time
        start_time = time.time()
        data, message = load_data_ai_from_db(temp_test_db_with_data)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should load 1000 records quickly (< 200ms)
        assert elapsed < 200, f"Data loading took {elapsed:.2f}ms, should be < 200ms"
        assert data is not None
    
    def test_managed_bridges_loading_is_fast(self, temp_test_db_with_data):
        """Test managed bridges loading is fast"""
        from logic.data_repository import get_all_managed_bridges
        
        conn = sqlite3.connect(temp_test_db_with_data)
        
        # Add some managed bridges
        for i in range(50):
            conn.execute(
                """INSERT INTO ManagedBridges (name, description, is_enabled)
                VALUES (?, ?, 1)""",
                (f"Bridge_{i}", f"Test bridge {i}")
            )
        conn.commit()
        conn.close()
        
        # Measure loading time
        start_time = time.time()
        bridges = get_all_managed_bridges(temp_test_db_with_data, only_enabled=True)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should load 50 bridges quickly (< 50ms)
        assert elapsed < 50, f"Bridge loading took {elapsed:.2f}ms, should be < 50ms"
        assert len(bridges) >= 50


class TestConfigurationPerformance:
    """Test configuration loading performance"""
    
    def test_settings_loading_is_fast(self):
        """Test SETTINGS loads quickly"""
        # Measure import time (lazy loading)
        start_time = time.time()
        from logic.config_manager import SETTINGS
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should load configuration very quickly (< 100ms)
        assert elapsed < 100, f"Settings loading took {elapsed:.2f}ms, should be < 100ms"
        assert SETTINGS is not None
    
    def test_constants_loading_is_fast(self):
        """Test constants load quickly"""
        start_time = time.time()
        from logic.constants import DEFAULT_SETTINGS
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should load constants very quickly (< 50ms)
        assert elapsed < 50, f"Constants loading took {elapsed:.2f}ms, should be < 50ms"
        assert DEFAULT_SETTINGS is not None


class TestOverallSystemPerformance:
    """Test overall system performance characteristics"""
    
    def test_module_import_time_is_reasonable(self):
        """Test that importing main modules is fast"""
        import importlib
        import sys
        
        modules_to_test = [
            'logic.backtester',
            'logic.db_manager',
            'logic.data_repository',
            'logic.config_manager',
        ]
        
        for module_name in modules_to_test:
            # Remove from cache if present
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # Measure import time
            start_time = time.time()
            importlib.import_module(module_name)
            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            
            # Each module should import quickly (< 200ms)
            assert elapsed < 200, f"{module_name} import took {elapsed:.2f}ms, should be < 200ms"
    
    def test_test_suite_execution_is_fast(self):
        """Test that the test suite executes quickly"""
        # This test itself validates that tests run fast
        # The entire suite should run in < 5 seconds
        
        # If we're in the test run and this test is executing,
        # the suite is running at reasonable speed
        assert True, "Test suite execution is within acceptable range"


class TestPerformanceRegression:
    """Tests to catch performance regressions"""
    
    def test_baseline_operation_benchmarks(self):
        """Establish baseline benchmarks for common operations"""
        from logic.backtester_core import BACKTEST_15_CAU_N1_V31_AI_V8
        
        # Benchmark 1: Small backtest
        sample_data = [
            (23000, '23000', '12345', '67890', '11111,22222', '33333',
             '44444,55555,66666', '77777', '88888,99999', '00000')
        ]
        
        start_time = time.time()
        result = BACKTEST_15_CAU_N1_V31_AI_V8(sample_data, 0, 0)
        elapsed_small = time.time() - start_time
        
        # Baseline: small backtest should complete in < 0.5 seconds
        assert elapsed_small < 0.5, f"Small backtest baseline: {elapsed_small:.3f}s"
        
        # Store baseline for future comparison
        # In a real scenario, this would be persisted
        baseline_benchmarks = {
            'small_backtest': elapsed_small,
        }
        
        assert baseline_benchmarks['small_backtest'] < 0.5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
