"""Unit tests for logic/backtester.py module."""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestValidateBacktestParams:
    """Tests for _validate_backtest_params function."""

    def test_validate_backtest_params_success(self):
        """Test successful validation."""
        from logic.backtester import _validate_backtest_params

        data = [["23001"] + ["data"] * 9 for i in range(100)]
        start_ky = "10"
        end_ky = "50"

        allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(
            data, start_ky, end_ky
        )

        assert allData is not None
        assert error is None
        assert finalEndRow > 0
        assert startCheckRow > 0
        assert offset == 10

    def test_validate_backtest_params_missing_params(self):
        """Test with missing parameters."""
        from logic.backtester import _validate_backtest_params

        allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(
            None, "10", "50"
        )

        assert allData is None
        assert error is not None
        assert "LỖI" in str(error[0])

    def test_validate_backtest_params_invalid_numbers(self):
        """Test with invalid number strings."""
        from logic.backtester import _validate_backtest_params

        data = [["row"]]
        allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(
            data, "abc", "def"
        )

        assert allData is None
        assert error is not None
        assert "số" in str(error[0])

    def test_validate_backtest_params_invalid_range(self):
        """Test with invalid start/end range."""
        from logic.backtester import _validate_backtest_params

        data = [["row"]]
        
        # Start is 0 or 1 (invalid)
        allData1, _, _, _, error1 = _validate_backtest_params(data, "1", "10")
        assert error1 is not None
        
        # End < Start
        allData2, _, _, _, error2 = _validate_backtest_params(data, "50", "10")
        assert error2 is not None

    def test_validate_backtest_params_insufficient_data(self):
        """Test with insufficient data."""
        from logic.backtester import _validate_backtest_params

        data = [["row"] * 10]  # Only 1 row
        
        # startRow=2, len(allData)=1, so finalEndRow = min(10, 1+2-1) = min(10, 2) = 2
        # startCheckRow = 2+1 = 3, which is > finalEndRow (2)
        # This should trigger insufficient data error
        allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(
            data, "2", "10"
        )

        # When startCheckRow (3) > finalEndRow (2), should get error
        assert error is not None
        assert "không đủ" in str(error[0]) or "LỖI" in str(error[0])


class TestParseK2NResults:
    """Tests for _parse_k2n_results function."""

    def test_parse_k2n_results_basic(self):
        """Test basic K2N results parsing."""
        from logic.backtester import _parse_k2n_results

        results_data = [
            ["Kỳ", "Cầu 1 (K2N)", "Cầu 2 (K2N)"],  # Headers
            ["Tỷ Lệ %", "50.0%", "60.0%"],  # Rates
            ["Streak", "3 thắng / 5 thua", "2 thắng / 4 thua"],  # Streaks
            ["Dự đoán", "01-23 (Đang chờ N2)", "45-67 (Khung mới N1)"],  # Predictions
        ]

        cache_list, pending_dict = _parse_k2n_results(results_data)

        assert len(cache_list) == 2
        assert len(pending_dict) == 1
        assert "Cầu 1" in pending_dict

    def test_parse_k2n_results_empty_data(self):
        """Test with empty data."""
        from logic.backtester import _parse_k2n_results

        cache_list, pending_dict = _parse_k2n_results([])

        assert cache_list == []
        assert pending_dict == {}

    def test_parse_k2n_results_insufficient_rows(self):
        """Test with insufficient rows."""
        from logic.backtester import _parse_k2n_results

        results_data = [
            ["Kỳ", "Cầu 1"],
            ["Tỷ Lệ %", "50.0%"],
        ]

        cache_list, pending_dict = _parse_k2n_results(results_data)

        assert cache_list == []
        assert pending_dict == {}

    def test_parse_k2n_results_none_input(self):
        """Test with None input."""
        from logic.backtester import _parse_k2n_results

        cache_list, pending_dict = _parse_k2n_results(None)

        assert cache_list == []
        assert pending_dict == {}

    def test_parse_k2n_results_malformed_streak(self):
        """Test with malformed streak data."""
        from logic.backtester import _parse_k2n_results

        results_data = [
            ["Kỳ", "Cầu 1"],
            ["Tỷ Lệ %", "50.0%"],
            ["Streak", "invalid"],
            ["Dự đoán", "01-23 (Đang chờ N2)"],
        ]

        cache_list, pending_dict = _parse_k2n_results(results_data)

        # Should handle malformed data gracefully
        assert isinstance(cache_list, list)
        assert isinstance(pending_dict, dict)


class TestTonghopTopCauCoreV5:
    """Tests for TONGHOP_TOP_CAU_CORE_V5 function."""

    @patch("logic.backtester.ALL_15_BRIDGE_FUNCTIONS_V5")
    def test_tonghop_invalid_backtest_range(self, mock_bridges):
        """Test with invalid backtest range."""
        from logic.backtester import TONGHOP_TOP_CAU_CORE_V5

        result = TONGHOP_TOP_CAU_CORE_V5([], ["23001"] * 10, 5, lambda r, s: r)

        assert "LỖI" in str(result[0])

    @patch("logic.backtester.ALL_15_BRIDGE_FUNCTIONS_V5")
    def test_tonghop_invalid_last_row(self, mock_bridges):
        """Test with invalid last row."""
        from logic.backtester import TONGHOP_TOP_CAU_CORE_V5

        fullBacktest = [["Kỳ", "Cầu 1"], ["23001", "✅"]]

        result = TONGHOP_TOP_CAU_CORE_V5(fullBacktest, [], 5, lambda r, s: r)

        assert "LỖI" in str(result[0])

    @patch("logic.backtester.ALL_15_BRIDGE_FUNCTIONS_V5")
    def test_tonghop_no_bridge_columns(self, mock_bridges):
        """Test when no bridge columns found."""
        from logic.backtester import TONGHOP_TOP_CAU_CORE_V5

        fullBacktest = [["Kỳ", "Column1"], ["23001", "data"]]
        lastRow = ["23001"] + ["data"] * 9

        result = TONGHOP_TOP_CAU_CORE_V5(
            fullBacktest, lastRow, 5, lambda r, s: r + s
        )

        assert "LỖI" in str(result[0])

    @patch("logic.backtester.ALL_15_BRIDGE_FUNCTIONS_V5")
    def test_tonghop_basic_scoring(self, mock_bridges):
        """Test basic scoring and top bridge selection."""
        from logic.backtester import TONGHOP_TOP_CAU_CORE_V5

        # Mock bridge functions
        mock_bridge1 = Mock(return_value=["01", "23"])
        mock_bridge2 = Mock(return_value=["45", "67"])
        mock_bridges.__getitem__ = Mock(side_effect=[mock_bridge1, mock_bridge2])
        mock_bridges.__len__ = Mock(return_value=2)

        fullBacktest = [
            ["Kỳ", "Cầu 1 (Test)", "Cầu 2 (Test)"],
            ["23001", "✅", "❌"],
            ["23002", "✅", "✅"],
            ["23003", "✅", "❌"],
        ]
        lastRow = ["23003"] + ["data"] * 9

        result = TONGHOP_TOP_CAU_CORE_V5(
            fullBacktest, lastRow, 2, lambda r, s: r * 10 + s
        )

        # Should return some result
        assert isinstance(result, list)
        assert len(result) > 0


class TestSettingsIntegration:
    """Tests for SETTINGS integration in backtester."""

    @patch("logic.backtester.SETTINGS")
    def test_settings_attributes_available(self, mock_settings):
        """Test that SETTINGS attributes are available."""
        mock_settings.STATS_DAYS = 7
        mock_settings.GAN_DAYS = 15
        mock_settings.HIGH_WIN_THRESHOLD = 47.0

        from logic import backtester

        # Should not raise AttributeError
        assert hasattr(backtester.SETTINGS, "STATS_DAYS")


class TestBacktesterImports:
    """Tests for import handling in backtester."""

    def test_module_imports_successfully(self):
        """Test that backtester module can be imported."""
        try:
            from logic import backtester

            assert hasattr(backtester, "_validate_backtest_params")
            assert hasattr(backtester, "_parse_k2n_results")
        except ImportError:
            pytest.fail("backtester module should import successfully")

    def test_fallback_functions_defined(self):
        """Test that fallback functions are defined."""
        from logic import backtester

        # These should exist even if imports fail
        assert hasattr(backtester, "_validate_backtest_params")
        assert hasattr(backtester, "_parse_k2n_results")


class TestBacktesterHelpers:
    """Tests for helper functions in backtester."""

    def test_validate_params_handles_edge_cases(self):
        """Test validation handles various edge cases."""
        from logic.backtester import _validate_backtest_params

        # Empty list
        result = _validate_backtest_params([], "10", "20")
        assert result[4] is not None  # Should have error

        # None values
        result = _validate_backtest_params(None, None, None)
        assert result[4] is not None

    def test_parse_k2n_handles_exceptions(self):
        """Test K2N parsing handles exceptions gracefully."""
        from logic.backtester import _parse_k2n_results

        # Malformed data should not crash
        malformed_data = [
            ["Kỳ"],
            [None],
            [123],
            [{"key": "value"}],
        ]

        try:
            cache_list, pending_dict = _parse_k2n_results(malformed_data)
            # Should return empty results but not crash
            assert isinstance(cache_list, list)
            assert isinstance(pending_dict, dict)
        except Exception as e:
            pytest.fail(f"Should handle malformed data gracefully: {e}")


class TestBacktesterDataValidation:
    """Tests for data validation in backtester functions."""

    def test_validate_backtest_params_boundary_values(self):
        """Test boundary values for validation."""
        from logic.backtester import _validate_backtest_params

        data = [["row"] * 10 for i in range(100)]

        # Minimum valid start (2)
        result = _validate_backtest_params(data, "2", "10")
        assert result[4] is None  # No error

        # Maximum values
        result = _validate_backtest_params(data, "2", "200")
        assert result[4] is None  # Should handle large end values

    def test_parse_k2n_results_various_formats(self):
        """Test K2N parsing with various data formats."""
        from logic.backtester import _parse_k2n_results

        # Standard format
        results1 = [
            ["Kỳ", "Cầu A"],
            ["50.0%", "60.0%"],
            ["1 thắng / 2 thua", "3 thắng / 1 thua"],
            ["01-02 (Đang chờ N2)", "03-04 (Khung mới N1)"],
        ]
        cache1, pending1 = _parse_k2n_results(results1)
        assert len(cache1) == 1

        # With extra columns
        results2 = [
            ["Kỳ", "Cầu A", "Cầu B", "Cầu C"],
            ["50%", "60%", "70%", "80%"],
            ["1 thắng / 2 thua"] * 4,
            ["01-02 (Đang chờ N2)"] * 4,
        ]
        cache2, pending2 = _parse_k2n_results(results2)
        assert len(cache2) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
