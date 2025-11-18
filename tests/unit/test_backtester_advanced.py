"""
Advanced unit tests for logic/backtester.py module.

Tests main backtest functions.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import logic modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from logic import backtester


class TestTonghopTopCauFunctions(unittest.TestCase):
    """Tests for TONGHOP_TOP_CAU_N1_V5 and TONGHOP_TOP_CAU_RATE_V5 functions."""

    def test_tonghop_top_cau_n1_v5_exists(self):
        """Test TONGHOP_TOP_CAU_N1_V5 function exists and is callable."""
        self.assertTrue(hasattr(backtester, "TONGHOP_TOP_CAU_N1_V5"))
        self.assertTrue(callable(backtester.TONGHOP_TOP_CAU_N1_V5))

    def test_tonghop_top_cau_rate_v5_exists(self):
        """Test TONGHOP_TOP_CAU_RATE_V5 function exists and is callable."""
        self.assertTrue(hasattr(backtester, "TONGHOP_TOP_CAU_RATE_V5"))
        self.assertTrue(callable(backtester.TONGHOP_TOP_CAU_RATE_V5))

    @patch("logic.backtester.TONGHOP_TOP_CAU_CORE_V5")
    def test_tonghop_top_cau_n1_v5_calls_core(self, mock_core):
        """Test TONGHOP_TOP_CAU_N1_V5 calls CORE_V5 with correct params."""
        mock_core.return_value = []
        
        backtester.TONGHOP_TOP_CAU_N1_V5("range", "last_row", topN=5)
        
        mock_core.assert_called_once()
        call_args = mock_core.call_args
        self.assertEqual(call_args[0][0], "range")
        self.assertEqual(call_args[0][1], "last_row")
        self.assertEqual(call_args[0][2], 5)

    @patch("logic.backtester.TONGHOP_TOP_CAU_CORE_V5")
    def test_tonghop_top_cau_rate_v5_calls_core(self, mock_core):
        """Test TONGHOP_TOP_CAU_RATE_V5 calls CORE_V5 with correct params."""
        mock_core.return_value = []
        
        backtester.TONGHOP_TOP_CAU_RATE_V5("range", "last_row", topN=3)
        
        mock_core.assert_called_once()
        call_args = mock_core.call_args
        self.assertEqual(call_args[0][0], "range")
        self.assertEqual(call_args[0][1], "last_row")
        self.assertEqual(call_args[0][2], 3)


class TestBacktest15CauK2NFunctions(unittest.TestCase):
    """Tests for BACKTEST_15_CAU_K2N_V30_AI_V8 function."""

    def test_backtest_k2n_function_exists(self):
        """Test BACKTEST_15_CAU_K2N_V30_AI_V8 function exists."""
        self.assertTrue(hasattr(backtester, "BACKTEST_15_CAU_K2N_V30_AI_V8"))
        self.assertTrue(callable(backtester.BACKTEST_15_CAU_K2N_V30_AI_V8))

    @patch("logic.backtester._validate_backtest_params")
    def test_backtest_k2n_validates_params(self, mock_validate):
        """Test BACKTEST_15_CAU_K2N_V30_AI_V8 validates parameters."""
        mock_validate.side_effect = ValueError("Invalid params")
        
        with self.assertRaises(ValueError):
            backtester.BACKTEST_15_CAU_K2N_V30_AI_V8([], "1", "2")

    @patch("logic.backtester._validate_backtest_params")
    def test_backtest_k2n_empty_data(self, mock_validate):
        """Test BACKTEST_15_CAU_K2N_V30_AI_V8 with empty data."""
        mock_validate.return_value = None
        
        # Should handle empty data gracefully
        result = backtester.BACKTEST_15_CAU_K2N_V30_AI_V8([], "0", "0", history=False)
        
        # Should return empty or default structure
        self.assertIsNotNone(result)

    def test_backtest_k2n_history_parameter(self):
        """Test BACKTEST_15_CAU_K2N_V30_AI_V8 history parameter."""
        # Test that function accepts history parameter
        try:
            backtester.BACKTEST_15_CAU_K2N_V30_AI_V8([], "0", "0", history=True)
            backtester.BACKTEST_15_CAU_K2N_V30_AI_V8([], "0", "0", history=False)
        except TypeError as e:
            if "history" in str(e):
                self.fail(f"Function should accept history parameter: {e}")


class TestBacktest15CauN1Functions(unittest.TestCase):
    """Tests for BACKTEST_15_CAU_N1_V31_AI_V8 function."""

    def test_backtest_n1_function_exists(self):
        """Test BACKTEST_15_CAU_N1_V31_AI_V8 function exists."""
        self.assertTrue(hasattr(backtester, "BACKTEST_15_CAU_N1_V31_AI_V8"))
        self.assertTrue(callable(backtester.BACKTEST_15_CAU_N1_V31_AI_V8))

    @patch("logic.backtester._validate_backtest_params")
    def test_backtest_n1_validates_params(self, mock_validate):
        """Test BACKTEST_15_CAU_N1_V31_AI_V8 validates parameters."""
        mock_validate.side_effect = ValueError("Invalid params")
        
        with self.assertRaises(ValueError):
            backtester.BACKTEST_15_CAU_N1_V31_AI_V8([], "1", "2")

    @patch("logic.backtester._validate_backtest_params")
    def test_backtest_n1_empty_data(self, mock_validate):
        """Test BACKTEST_15_CAU_N1_V31_AI_V8 with empty data."""
        mock_validate.return_value = None
        
        # Should handle empty data gracefully
        result = backtester.BACKTEST_15_CAU_N1_V31_AI_V8([], "0", "0")
        
        # Should return empty or default structure
        self.assertIsNotNone(result)


class TestBacktestCustomCau(unittest.TestCase):
    """Tests for BACKTEST_CUSTOM_CAU_V16 function."""

    def test_backtest_custom_function_exists(self):
        """Test BACKTEST_CUSTOM_CAU_V16 function exists."""
        self.assertTrue(hasattr(backtester, "BACKTEST_CUSTOM_CAU_V16"))
        self.assertTrue(callable(backtester.BACKTEST_CUSTOM_CAU_V16))

    @patch("logic.backtester._validate_backtest_params")
    def test_backtest_custom_validates_params(self, mock_validate):
        """Test BACKTEST_CUSTOM_CAU_V16 validates parameters."""
        mock_validate.side_effect = ValueError("Invalid params")
        
        with self.assertRaises(ValueError):
            backtester.BACKTEST_CUSTOM_CAU_V16([], "1", "2", "bridge_name", "mode")

    def test_backtest_custom_mode_parameter(self):
        """Test BACKTEST_CUSTOM_CAU_V16 accepts mode parameter."""
        # Test that function accepts custom_bridge_name and mode parameters
        try:
            backtester.BACKTEST_CUSTOM_CAU_V16([], "0", "0", "test_bridge", "N1")
            backtester.BACKTEST_CUSTOM_CAU_V16([], "0", "0", "test_bridge", "K2N")
        except TypeError as e:
            if "mode" in str(e):
                self.fail(f"Function should accept mode parameter: {e}")


class TestBacktestManagedBridges(unittest.TestCase):
    """Tests for managed bridges backtest functions."""

    def test_backtest_managed_n1_exists(self):
        """Test BACKTEST_MANAGED_BRIDGES_N1 function exists."""
        self.assertTrue(hasattr(backtester, "BACKTEST_MANAGED_BRIDGES_N1"))
        self.assertTrue(callable(backtester.BACKTEST_MANAGED_BRIDGES_N1))

    def test_backtest_managed_k2n_exists(self):
        """Test BACKTEST_MANAGED_BRIDGES_K2N function exists."""
        self.assertTrue(hasattr(backtester, "BACKTEST_MANAGED_BRIDGES_K2N"))
        self.assertTrue(callable(backtester.BACKTEST_MANAGED_BRIDGES_K2N))

    @patch("logic.backtester._validate_backtest_params")
    @patch("logic.backtester.db_manager")
    def test_backtest_managed_n1_validates(self, mock_db, mock_validate):
        """Test BACKTEST_MANAGED_BRIDGES_N1 validates parameters."""
        mock_validate.side_effect = ValueError("Invalid params")
        
        with self.assertRaises(ValueError):
            backtester.BACKTEST_MANAGED_BRIDGES_N1([], "1", "2")

    @patch("logic.backtester._validate_backtest_params")
    @patch("logic.backtester.db_manager")
    def test_backtest_managed_k2n_validates(self, mock_db, mock_validate):
        """Test BACKTEST_MANAGED_BRIDGES_K2N validates parameters."""
        mock_validate.side_effect = ValueError("Invalid params")
        
        with self.assertRaises(ValueError):
            backtester.BACKTEST_MANAGED_BRIDGES_K2N([], "1", "2")

    def test_backtest_managed_n1_db_name_parameter(self):
        """Test BACKTEST_MANAGED_BRIDGES_N1 accepts db_name parameter."""
        try:
            backtester.BACKTEST_MANAGED_BRIDGES_N1([], "0", "0", db_name="test.db")
        except TypeError as e:
            if "db_name" in str(e):
                self.fail(f"Function should accept db_name parameter: {e}")

    def test_backtest_managed_k2n_history_parameter(self):
        """Test BACKTEST_MANAGED_BRIDGES_K2N accepts history parameter."""
        try:
            backtester.BACKTEST_MANAGED_BRIDGES_K2N([], "0", "0", history=True)
            backtester.BACKTEST_MANAGED_BRIDGES_K2N([], "0", "0", history=False)
        except TypeError as e:
            if "history" in str(e):
                self.fail(f"Function should accept history parameter: {e}")


class TestBacktestMemoryBridges(unittest.TestCase):
    """Tests for BACKTEST_MEMORY_BRIDGES function."""

    def test_backtest_memory_function_exists(self):
        """Test BACKTEST_MEMORY_BRIDGES function exists."""
        self.assertTrue(hasattr(backtester, "BACKTEST_MEMORY_BRIDGES"))
        self.assertTrue(callable(backtester.BACKTEST_MEMORY_BRIDGES))

    @patch("logic.backtester._validate_backtest_params")
    def test_backtest_memory_validates_params(self, mock_validate):
        """Test BACKTEST_MEMORY_BRIDGES validates parameters."""
        mock_validate.side_effect = ValueError("Invalid params")
        
        with self.assertRaises(ValueError):
            backtester.BACKTEST_MEMORY_BRIDGES([], "1", "2")

    @patch("logic.backtester._validate_backtest_params")
    def test_backtest_memory_empty_data(self, mock_validate):
        """Test BACKTEST_MEMORY_BRIDGES with empty data."""
        mock_validate.return_value = None
        
        # Should handle empty data gracefully
        result = backtester.BACKTEST_MEMORY_BRIDGES([], "0", "0")
        
        # Should return empty or default structure
        self.assertIsNotNone(result)


class TestBridgeUpdateFunctions(unittest.TestCase):
    """Tests for bridge rate update functions."""

    def test_run_and_update_all_bridge_rates_exists(self):
        """Test run_and_update_all_bridge_rates function exists."""
        self.assertTrue(hasattr(backtester, "run_and_update_all_bridge_rates"))
        self.assertTrue(callable(backtester.run_and_update_all_bridge_rates))

    def test_run_and_update_all_bridge_k2n_cache_exists(self):
        """Test run_and_update_all_bridge_K2N_cache function exists."""
        self.assertTrue(hasattr(backtester, "run_and_update_all_bridge_K2N_cache"))
        self.assertTrue(callable(backtester.run_and_update_all_bridge_K2N_cache))

    @patch("logic.backtester.db_manager")
    def test_run_and_update_bridge_rates_db_param(self, mock_db):
        """Test run_and_update_all_bridge_rates accepts db_name parameter."""
        try:
            backtester.run_and_update_all_bridge_rates([], db_name="test.db")
        except TypeError as e:
            if "db_name" in str(e):
                self.fail(f"Function should accept db_name parameter: {e}")

    @patch("logic.backtester.db_manager")
    def test_run_and_update_k2n_cache_params(self, mock_db):
        """Test run_and_update_all_bridge_K2N_cache accepts parameters."""
        try:
            backtester.run_and_update_all_bridge_K2N_cache(
                [], db_name="test.db", data_slice=None, write_to_db=True
            )
            backtester.run_and_update_all_bridge_K2N_cache(
                [], db_name="test.db", data_slice=10, write_to_db=False
            )
        except TypeError as e:
            if any(param in str(e) for param in ["db_name", "data_slice", "write_to_db"]):
                self.fail(f"Function should accept parameters: {e}")


if __name__ == "__main__":
    unittest.main()
