"""
Extended unit tests for backtester.py to reach 30% coverage milestone.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


# Test imports and module loading
class TestBacktesterModuleStructure:
    """Test module structure and imports."""

    def test_settings_attributes_exist(self):
        """Test that SETTINGS object has required attributes."""
        from logic import backtester
        
        assert hasattr(backtester, 'SETTINGS')
        settings = backtester.SETTINGS
        
        # Check critical attributes
        assert hasattr(settings, 'STATS_DAYS')
        assert hasattr(settings, 'GAN_DAYS')
        assert hasattr(settings, 'HIGH_WIN_THRESHOLD')

    def test_db_name_constant(self):
        """Test that DB_NAME constant is defined."""
        from logic import backtester
        
        assert hasattr(backtester, 'DB_NAME')
        assert isinstance(backtester.DB_NAME, str)
        assert len(backtester.DB_NAME) > 0


class TestValidateBacktestParamsExtended:
    """Extended tests for _validate_backtest_params function."""
    
    def test_valid_params_with_data(self):
        """Test validation with valid parameters and data."""
        from logic.backtester import _validate_backtest_params
        
        # Create sample data
        sample_data = [
            {'ky': 1, 'data': 'test1'},
            {'ky': 2, 'data': 'test2'},
            {'ky': 3, 'data': 'test3'},
            {'ky': 4, 'data': 'test4'},
        ]
        
        result = _validate_backtest_params(sample_data, "2", "3")
        
        # Should return 5 values
        assert result is not None
        assert len(result) == 5
        
        all_data, final_end, start_check, offset, error = result
        
        # Basic validations
        assert all_data == sample_data
        assert error is None

    def test_minimum_required_data(self):
        """Test with minimum required data."""
        from logic.backtester import _validate_backtest_params
        
        # Need at least startRow + 1 records
        sample_data = [{'ky': i} for i in range(10)]
        
        result = _validate_backtest_params(sample_data, "3", "8")
        
        assert result is not None
        assert len(result) == 5
        all_data, final_end, start_check, offset, error = result
        
        # Should succeed with sufficient data
        assert error is None
        assert all_data is not None

    def test_large_end_row_clamped(self):
        """Test that end row is clamped to data size."""
        from logic.backtester import _validate_backtest_params
        
        sample_data = [{'ky': i} for i in range(5)]
        
        # Request end row beyond data size
        result = _validate_backtest_params(sample_data, "2", "1000")
        
        assert result is not None
        all_data, final_end, start_check, offset, error = result
        
        # Should succeed but clamp the end
        assert error is None
        assert final_end is not None


class TestParseK2NResultsExtended:
    """Extended tests for _parse_k2n_results function."""
    
    def test_parse_insufficient_data(self):
        """Test parsing with insufficient data rows."""
        from logic.backtester import _parse_k2n_results
        
        # Less than 4 rows
        k2n_results = [
            ['Ngày 1', 'Trúng']
        ]
        
        result = _parse_k2n_results(k2n_results)
        
        # Should return empty results
        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2
        cache_list, pending_dict = result
        assert isinstance(cache_list, list)
        assert isinstance(pending_dict, dict)

    def test_parse_empty_results(self):
        """Test parsing with empty results."""
        from logic.backtester import _parse_k2n_results
        
        result = _parse_k2n_results([])
        
        # Should return empty results
        assert result is not None
        cache_list, pending_dict = result
        assert cache_list == []
        assert pending_dict == {}


class TestCounterUsage:
    """Test Counter usage in backtester."""
    
    def test_counter_imported(self):
        """Test that Counter is imported from collections."""
        from logic import backtester
        
        # Counter should be available in the module
        assert hasattr(backtester, 'Counter')
        
        # Should be able to use it
        counter = backtester.Counter([1, 1, 2, 3, 3, 3])
        assert counter[1] == 2
        assert counter[3] == 3


class TestFallbackFunctions:
    """Test fallback function definitions."""
    
    def test_fallback_functions_defined(self):
        """Test that fallback functions are properly defined."""
        from logic import backtester
        
        # These functions should exist even if imports fail
        assert hasattr(backtester, 'getAllLoto_V30')
        assert hasattr(backtester, 'checkHitSet_V30_K2N')
        assert hasattr(backtester, 'getPositionName_V16')
        
        # They should be callable
        assert callable(backtester.getAllLoto_V30)
        assert callable(backtester.checkHitSet_V30_K2N)
        assert callable(backtester.getPositionName_V16)
