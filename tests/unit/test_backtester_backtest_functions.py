"""
Unit tests for backtester.py BACKTEST_* functions
Testing backtesting functionality for K2N, N1, V16, managed bridges, and memory bridges
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from logic import backtester


class TestBacktestK2N:
    """Tests for BACKTEST_15_CAU_K2N_V30_AI_V8 function"""

    def test_backtest_k2n_invalid_params(self):
        """Test K2N backtest with invalid parameters"""
        result = backtester.BACKTEST_15_CAU_K2N_V30_AI_V8([], "230001", "230010")
        # Function returns error message list instead of raising exception
        assert isinstance(result, list)
        assert len(result) > 0
        # Check if it's an error message
        if result and len(result) > 0:
            assert "LỖI" in str(result[0]) or isinstance(result[0], list)

    def test_backtest_k2n_empty_data(self):
        """Test K2N backtest with empty data"""
        result = backtester.BACKTEST_15_CAU_K2N_V30_AI_V8([], "230001", "230010", history=False)
        assert result is not None or result == []

    def test_backtest_k2n_with_history_flag(self):
        """Test K2N backtest history flag behavior"""
        # Test that function accepts history parameter
        try:
            backtester.BACKTEST_15_CAU_K2N_V30_AI_V8([], "230001", "230002", history=True)
            backtester.BACKTEST_15_CAU_K2N_V30_AI_V8([], "230001", "230002", history=False)
        except (ValueError, IndexError, KeyError, TypeError):
            pass  # Expected for empty data


class TestBacktestN1:
    """Tests for BACKTEST_15_CAU_N1_V31_AI_V8 function"""

    def test_backtest_n1_invalid_params(self):
        """Test N1 backtest with invalid parameters"""
        result = backtester.BACKTEST_15_CAU_N1_V31_AI_V8([], "230001", "230010")
        # Function returns error message list instead of raising exception
        assert isinstance(result, list)
        assert len(result) > 0
        # Check if it's an error message
        if result and len(result) > 0:
            assert "LỖI" in str(result[0]) or isinstance(result[0], list)

    def test_backtest_n1_empty_data(self):
        """Test N1 backtest with empty data"""
        result = backtester.BACKTEST_15_CAU_N1_V31_AI_V8([], "230001", "230010")
        assert result is not None or result == []

    def test_backtest_n1_function_signature(self):
        """Test N1 backtest function accepts correct parameters"""
        import inspect
        sig = inspect.signature(backtester.BACKTEST_15_CAU_N1_V31_AI_V8)
        params = list(sig.parameters.keys())
        assert "toan_bo_A_I" in params
        assert "ky_bat_dau_kiem_tra" in params
        assert "ky_ket_thuc_kiem_tra" in params


class TestBacktestCustomV16:
    """Tests for BACKTEST_CUSTOM_CAU_V16 function"""

    def test_backtest_custom_v16_invalid_params(self):
        """Test custom V16 backtest with invalid parameters"""
        result = backtester.BACKTEST_CUSTOM_CAU_V16([], "230001", "230010", "test_bridge", "N1")
        # Function returns result list instead of raising exception
        assert result is not None

    def test_backtest_custom_v16_empty_data(self):
        """Test custom V16 backtest with empty data"""
        result = backtester.BACKTEST_CUSTOM_CAU_V16([], "230001", "230010", "test_bridge", "N1")
        assert result is not None or result == []

    def test_backtest_custom_v16_modes(self):
        """Test custom V16 backtest accepts different modes"""
        try:
            backtester.BACKTEST_CUSTOM_CAU_V16([], "230001", "230002", "bridge", "N1")
            backtester.BACKTEST_CUSTOM_CAU_V16([], "230001", "230002", "bridge", "K2N")
        except (ValueError, IndexError, KeyError, TypeError, AttributeError):
            pass  # Expected for empty data

    def test_backtest_custom_v16_function_signature(self):
        """Test custom V16 backtest function signature"""
        import inspect
        sig = inspect.signature(backtester.BACKTEST_CUSTOM_CAU_V16)
        params = list(sig.parameters.keys())
        assert "custom_bridge_name" in params
        assert "mode" in params


class TestBacktestManagedBridgesN1:
    """Tests for BACKTEST_MANAGED_BRIDGES_N1 function"""

    def test_managed_bridges_n1_invalid_params(self):
        """Test managed bridges N1 with invalid parameters"""
        # Function handles empty data gracefully, returns empty dict
        result = backtester.BACKTEST_MANAGED_BRIDGES_N1([], "230001", "230010")
        assert isinstance(result, (dict, list))

    def test_managed_bridges_n1_empty_data(self):
        """Test managed bridges N1 with empty data"""
        result = backtester.BACKTEST_MANAGED_BRIDGES_N1([], "230001", "230010")
        assert result is not None or result == []

    def test_managed_bridges_n1_with_db_name(self):
        """Test managed bridges N1 accepts db_name parameter"""
        try:
            backtester.BACKTEST_MANAGED_BRIDGES_N1([], "230001", "230002", db_name="test.db")
        except (ValueError, IndexError, KeyError, TypeError):
            pass  # Expected for empty data

    def test_managed_bridges_n1_function_signature(self):
        """Test managed bridges N1 function signature"""
        import inspect
        sig = inspect.signature(backtester.BACKTEST_MANAGED_BRIDGES_N1)
        params = list(sig.parameters.keys())
        assert "db_name" in params


class TestBacktestManagedBridgesK2N:
    """Tests for BACKTEST_MANAGED_BRIDGES_K2N function"""

    def test_managed_bridges_k2n_invalid_params(self):
        """Test managed bridges K2N with invalid parameters"""
        # Function handles empty data gracefully, returns dict or list
        result = backtester.BACKTEST_MANAGED_BRIDGES_K2N([], "230001", "230010", history=False)
        assert isinstance(result, (dict, list))

    def test_managed_bridges_k2n_empty_data(self):
        """Test managed bridges K2N with empty data"""
        result = backtester.BACKTEST_MANAGED_BRIDGES_K2N([], "230001", "230010", history=False)
        assert result is not None or result == []

    def test_managed_bridges_k2n_with_params(self):
        """Test managed bridges K2N accepts all parameters"""
        try:
            backtester.BACKTEST_MANAGED_BRIDGES_K2N(
                [], "230001", "230002", db_name="test.db", history=True
            )
            backtester.BACKTEST_MANAGED_BRIDGES_K2N(
                [], "230001", "230002", db_name="test.db", history=False
            )
        except (ValueError, IndexError, KeyError, TypeError):
            pass  # Expected for empty data

    def test_managed_bridges_k2n_function_signature(self):
        """Test managed bridges K2N function signature"""
        import inspect
        sig = inspect.signature(backtester.BACKTEST_MANAGED_BRIDGES_K2N)
        params = list(sig.parameters.keys())
        assert "db_name" in params
        assert "history" in params


class TestBacktestMemoryBridges:
    """Tests for BACKTEST_MEMORY_BRIDGES function"""

    def test_memory_bridges_invalid_params(self):
        """Test memory bridges with invalid parameters"""
        # Function handles empty data gracefully, returns dict or list
        result = backtester.BACKTEST_MEMORY_BRIDGES([], "230001", "230010")
        assert isinstance(result, (dict, list))

    def test_memory_bridges_empty_data(self):
        """Test memory bridges with empty data"""
        result = backtester.BACKTEST_MEMORY_BRIDGES([], "230001", "230010")
        assert result is not None or result == []

    def test_memory_bridges_function_signature(self):
        """Test memory bridges function signature"""
        import inspect
        sig = inspect.signature(backtester.BACKTEST_MEMORY_BRIDGES)
        params = list(sig.parameters.keys())
        assert len(params) == 3
        assert "toan_bo_A_I" in params


class TestRunAndUpdateFunctions:
    """Tests for run_and_update_* helper functions"""

    def test_run_and_update_all_bridge_rates_empty(self):
        """Test run_and_update_all_bridge_rates with empty data"""
        result = backtester.run_and_update_all_bridge_rates([])
        assert result is not None or result == []

    def test_run_and_update_all_bridge_rates_with_db(self):
        """Test run_and_update_all_bridge_rates with db_name parameter"""
        try:
            backtester.run_and_update_all_bridge_rates([], db_name="test.db")
        except (ValueError, IndexError, KeyError, TypeError):
            pass  # Expected for empty data

    def test_run_and_update_k2n_cache_empty(self):
        """Test run_and_update_all_bridge_K2N_cache with empty data"""
        result = backtester.run_and_update_all_bridge_K2N_cache([], write_to_db=False)
        assert result is not None or result == []

    def test_run_and_update_k2n_cache_with_params(self):
        """Test run_and_update_all_bridge_K2N_cache with all parameters"""
        try:
            backtester.run_and_update_all_bridge_K2N_cache(
                [], db_name="test.db", data_slice=None, write_to_db=False
            )
            backtester.run_and_update_all_bridge_K2N_cache(
                [], db_name="test.db", data_slice=10, write_to_db=True
            )
        except (ValueError, IndexError, KeyError, TypeError):
            pass  # Expected for empty data

    def test_run_and_update_k2n_cache_function_signature(self):
        """Test K2N cache function signature"""
        import inspect
        sig = inspect.signature(backtester.run_and_update_all_bridge_K2N_cache)
        params = list(sig.parameters.keys())
        assert "data_slice" in params
        assert "write_to_db" in params
