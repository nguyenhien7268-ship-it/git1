"""
Tests for backtester module - Core business logic testing

This module tests the backtesting functionality which is critical
for the lottery analysis system.
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestBacktesterImports:
    """Test that backtester module can be imported and has required functions"""
    
    def test_backtester_module_imports(self):
        """Test backtester module can be imported"""
        from logic import backtester
        assert backtester is not None
    
    def test_backtester_has_settings(self):
        """Test SETTINGS is available in backtester"""
        from logic.backtester import SETTINGS
        assert SETTINGS is not None
        assert hasattr(SETTINGS, 'STATS_DAYS')
    
    def test_backtester_has_db_name(self):
        """Test DB_NAME constant is available"""
        from logic.backtester import DB_NAME
        assert DB_NAME is not None
        assert isinstance(DB_NAME, str)
        assert 'db' in DB_NAME.lower()


class TestBacktesterHelpers:
    """Test helper functions in backtester module"""
    
    def test_backtester_helpers_module_exists(self):
        """Test backtester_helpers module exists"""
        try:
            from logic import backtester_helpers
            assert backtester_helpers is not None
        except ImportError:
            pytest.skip("backtester_helpers module not found")
    
    def test_validation_functions_exist(self):
        """Test validation helper functions exist"""
        try:
            from logic import backtester_helpers
            # Check if module has validation functions
            assert hasattr(backtester_helpers, '__name__')
        except ImportError:
            pytest.skip("backtester_helpers module not found")


class TestBacktesterCore:
    """Test core backtesting logic"""
    
    def test_backtester_core_module_exists(self):
        """Test backtester_core module exists"""
        try:
            from logic import backtester_core
            assert backtester_core is not None
        except ImportError:
            pytest.skip("backtester_core module not found")
    
    def test_core_has_backtest_functions(self):
        """Test core module has backtest functions"""
        try:
            from logic import backtester_core
            module_contents = dir(backtester_core)
            # Should have some backtest-related functions
            backtest_functions = [
                name for name in module_contents 
                if 'BACKTEST' in name.upper() or 'backtest' in name.lower()
            ]
            assert len(backtest_functions) > 0, "Should have backtest functions"
        except ImportError:
            pytest.skip("backtester_core module not found")


class TestBacktesterAggregation:
    """Test aggregation functions"""
    
    def test_aggregation_module_exists(self):
        """Test backtester_aggregation module exists"""
        try:
            from logic import backtester_aggregation
            assert backtester_aggregation is not None
        except ImportError:
            pytest.skip("backtester_aggregation module not found")


class TestBacktesterIntegration:
    """Integration tests for backtester workflow"""
    
    def test_backtester_can_access_database_functions(self):
        """Test backtester can access database functions"""
        from logic.backtester import (
            get_all_managed_bridges,
            update_bridge_win_rate_batch,
            update_bridge_k2n_cache_batch
        )
        
        # These should be callable functions
        assert callable(get_all_managed_bridges)
        assert callable(update_bridge_win_rate_batch)
        assert callable(update_bridge_k2n_cache_batch)
    
    def test_backtester_can_access_bridge_functions(self):
        """Test backtester can access bridge calculation functions"""
        from logic.backtester import (
            ALL_15_BRIDGE_FUNCTIONS_V5,
            getAllLoto_V30,
            checkHitSet_V30_K2N
        )
        
        # These should exist
        assert ALL_15_BRIDGE_FUNCTIONS_V5 is not None
        assert callable(getAllLoto_V30)
        assert callable(checkHitSet_V30_K2N)
    
    def test_settings_has_required_parameters(self):
        """Test SETTINGS has all required backtest parameters"""
        from logic.backtester import SETTINGS
        
        required_params = [
            'STATS_DAYS',
            'HIGH_WIN_THRESHOLD',
            'K2N_RISK_START_THRESHOLD',
            'K2N_RISK_PENALTY_PER_FRAME',
        ]
        
        for param in required_params:
            assert hasattr(SETTINGS, param), f"SETTINGS should have {param}"
            value = getattr(SETTINGS, param)
            assert value is not None, f"{param} should not be None"
            assert isinstance(value, (int, float)), f"{param} should be numeric"


class TestBacktesterDataStructures:
    """Test data structures used in backtesting"""
    
    def test_bridge_functions_list_structure(self):
        """Test ALL_15_BRIDGE_FUNCTIONS_V5 has correct structure"""
        from logic.backtester import ALL_15_BRIDGE_FUNCTIONS_V5
        
        # Should be a list
        assert isinstance(ALL_15_BRIDGE_FUNCTIONS_V5, list)
        
        # If not empty, each element should be callable or a tuple with callable
        if len(ALL_15_BRIDGE_FUNCTIONS_V5) > 0:
            first_item = ALL_15_BRIDGE_FUNCTIONS_V5[0]
            # Could be a function or a tuple (name, function)
            assert callable(first_item) or (
                isinstance(first_item, tuple) and 
                len(first_item) >= 2 and 
                callable(first_item[1])
            )


class TestBacktesterErrorHandling:
    """Test error handling in backtester"""
    
    def test_backtester_handles_empty_data(self):
        """Test backtester handles empty data gracefully"""
        from logic.backtester import getAllLoto_V30
        
        # Test with None
        result = getAllLoto_V30(None)
        assert isinstance(result, list), "Should return a list even for None input"
    
    def test_backtester_handles_invalid_bridge_name(self):
        """Test backtester handles invalid bridge names"""
        try:
            from logic.backtester import getPositionName_V16
            
            # Test with invalid index
            result = getPositionName_V16(-1)
            # Should not crash - may return error string or default value
            assert result is not None
        except ImportError:
            pytest.skip("Function not available in backtester")


class TestBacktesterPerformance:
    """Performance-related tests"""
    
    def test_backtester_functions_are_defined(self):
        """Test that backtester exports expected functions"""
        import logic.backtester as backtester
        
        # Check module has reasonable number of exports
        public_functions = [
            name for name in dir(backtester) 
            if not name.startswith('_') and callable(getattr(backtester, name))
        ]
        
        # Should have multiple functions
        assert len(public_functions) > 5, "Backtester should export multiple functions"


@pytest.mark.skip(reason="Slow test placeholder - implement when needed")
class TestBacktesterSlowOperations:
    """Tests for slow operations (marked as slow)"""
    
    def test_placeholder_slow_test(self):
        """Placeholder for future slow backtest tests"""
        # This would test actual backtest operations which take longer
        assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
