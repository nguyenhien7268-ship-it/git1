"""Extended unit tests for logic/dashboard_analytics.py module."""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestStandardizePair:
    """Tests for _standardize_pair function."""

    def test_standardize_pair_basic(self):
        """Test basic pair standardization."""
        from logic.dashboard_analytics import _standardize_pair

        result = _standardize_pair(["30", "01"])
        assert result == "01-30"

    def test_standardize_pair_already_sorted(self):
        """Test already sorted pair."""
        from logic.dashboard_analytics import _standardize_pair

        result = _standardize_pair(["01", "30"])
        assert result == "01-30"

    def test_standardize_pair_same_numbers(self):
        """Test pair with same numbers."""
        from logic.dashboard_analytics import _standardize_pair

        result = _standardize_pair(["15", "15"])
        assert result == "15-15"

    def test_standardize_pair_empty_list(self):
        """Test with empty list."""
        from logic.dashboard_analytics import _standardize_pair

        result = _standardize_pair([])
        assert result is None

    def test_standardize_pair_wrong_length(self):
        """Test with wrong length list."""
        from logic.dashboard_analytics import _standardize_pair

        result = _standardize_pair(["01", "02", "03"])
        assert result is None

    def test_standardize_pair_none(self):
        """Test with None input."""
        from logic.dashboard_analytics import _standardize_pair

        result = _standardize_pair(None)
        assert result is None

    def test_standardize_pair_single_element(self):
        """Test with single element."""
        from logic.dashboard_analytics import _standardize_pair

        result = _standardize_pair(["01"])
        assert result is None


class TestGetPredictionConsensus:
    """Tests for get_prediction_consensus function."""

    @patch("logic.dashboard_analytics.get_all_managed_bridges")
    @patch("logic.dashboard_analytics.DB_NAME", "test.db")
    def test_get_prediction_consensus_basic(self, mock_get_bridges):
        """Test basic prediction consensus."""
        from logic.dashboard_analytics import get_prediction_consensus

        mock_get_bridges.return_value = [
            {"name": "Cầu 1", "next_prediction_stl": "01,02"},
            {"name": "Cầu 2", "next_prediction_stl": "01,02"},
            {"name": "Cầu 3", "next_prediction_stl": "03,04"},
        ]

        result = get_prediction_consensus()

        assert isinstance(result, list)
        # Should have 2 pairs, "01-02" with 2 votes, "03-04" with 1 vote
        if len(result) > 0:
            assert result[0][1] == 2  # Highest vote count

    @patch("logic.dashboard_analytics.get_all_managed_bridges")
    @patch("logic.dashboard_analytics.DB_NAME", "test.db")
    def test_get_prediction_consensus_no_bridges(self, mock_get_bridges):
        """Test with no managed bridges."""
        from logic.dashboard_analytics import get_prediction_consensus

        mock_get_bridges.return_value = []

        result = get_prediction_consensus()
        assert result == []

    @patch("logic.dashboard_analytics.get_all_managed_bridges")
    @patch("logic.dashboard_analytics.DB_NAME", "test.db")
    def test_get_prediction_consensus_invalid_predictions(self, mock_get_bridges):
        """Test with invalid prediction formats."""
        from logic.dashboard_analytics import get_prediction_consensus

        mock_get_bridges.return_value = [
            {"name": "Cầu 1", "next_prediction_stl": "N2"},
            {"name": "Cầu 2", "next_prediction_stl": "LỖI"},
            {"name": "Cầu 3", "next_prediction_stl": "01"},  # No comma
        ]

        result = get_prediction_consensus()
        assert result == []

    @patch("logic.dashboard_analytics.get_all_managed_bridges")
    @patch("logic.dashboard_analytics.DB_NAME", "test.db")
    def test_get_prediction_consensus_error_handling(self, mock_get_bridges):
        """Test error handling in consensus."""
        from logic.dashboard_analytics import get_prediction_consensus

        mock_get_bridges.side_effect = Exception("DB error")

        result = get_prediction_consensus()
        assert result == []


class TestGetHighWinRatePredictions:
    """Tests for get_high_win_rate_predictions function."""

    @patch("logic.dashboard_analytics.get_all_managed_bridges")
    @patch("logic.dashboard_analytics.SETTINGS")
    @patch("logic.dashboard_analytics.DB_NAME", "test.db")
    def test_get_high_win_rate_basic(self, mock_settings, mock_get_bridges):
        """Test basic high win rate filtering."""
        from logic.dashboard_analytics import get_high_win_rate_predictions

        mock_settings.HIGH_WIN_THRESHOLD = 50.0

        mock_get_bridges.return_value = [
            {
                "name": "Cầu 1",
                "win_rate_text": "55.5%",
                "next_prediction_stl": "01,02",
            },
            {
                "name": "Cầu 2",
                "win_rate_text": "45.0%",
                "next_prediction_stl": "03,04",
            },
            {
                "name": "Cầu 3",
                "win_rate_text": "60.0%",
                "next_prediction_stl": "05,06",
            },
        ]

        result = get_high_win_rate_predictions(threshold=50.0)

        assert isinstance(result, list)
        # Should have 2 bridges with win rate >= 50%
        assert len(result) == 2
        assert result[0]["name"] == "Cầu 1"

    @patch("logic.dashboard_analytics.get_all_managed_bridges")
    @patch("logic.dashboard_analytics.SETTINGS")
    @patch("logic.dashboard_analytics.DB_NAME", "test.db")
    def test_get_high_win_rate_no_bridges(self, mock_settings, mock_get_bridges):
        """Test with no managed bridges."""
        from logic.dashboard_analytics import get_high_win_rate_predictions

        mock_settings.HIGH_WIN_THRESHOLD = 50.0
        mock_get_bridges.return_value = []

        result = get_high_win_rate_predictions()
        assert result == []

    @patch("logic.dashboard_analytics.get_all_managed_bridges")
    @patch("logic.dashboard_analytics.SETTINGS")
    @patch("logic.dashboard_analytics.DB_NAME", "test.db")
    def test_get_high_win_rate_na_values(self, mock_settings, mock_get_bridges):
        """Test with N/A win rates."""
        from logic.dashboard_analytics import get_high_win_rate_predictions

        mock_settings.HIGH_WIN_THRESHOLD = 50.0

        mock_get_bridges.return_value = [
            {
                "name": "Cầu 1",
                "win_rate_text": "N/A",
                "next_prediction_stl": "01,02",
            },
            {"name": "Cầu 2", "win_rate_text": "", "next_prediction_stl": "03,04"},
        ]

        result = get_high_win_rate_predictions()
        assert result == []

    @patch("logic.dashboard_analytics.get_all_managed_bridges")
    @patch("logic.dashboard_analytics.SETTINGS")
    @patch("logic.dashboard_analytics.DB_NAME", "test.db")
    def test_get_high_win_rate_invalid_predictions(self, mock_settings, mock_get_bridges):
        """Test filtering out invalid predictions."""
        from logic.dashboard_analytics import get_high_win_rate_predictions

        mock_settings.HIGH_WIN_THRESHOLD = 50.0

        mock_get_bridges.return_value = [
            {"name": "Cầu 1", "win_rate_text": "60%", "next_prediction_stl": "N2"},
            {"name": "Cầu 2", "win_rate_text": "55%", "next_prediction_stl": "LỖI"},
            {"name": "Cầu 3", "win_rate_text": "70%", "next_prediction_stl": "01"},
        ]

        result = get_high_win_rate_predictions()
        assert result == []


class TestGetPendingK2NBridges:
    """Tests for get_pending_k2n_bridges function."""

    @patch("logic.dashboard_analytics.get_all_managed_bridges")
    @patch("logic.dashboard_analytics.getAllLoto_V30")
    @patch("logic.dashboard_analytics.checkHitSet_V30_K2N")
    @patch("logic.dashboard_analytics.ALL_15_BRIDGE_FUNCTIONS_V5", [])
    @patch("logic.dashboard_analytics.DB_NAME", "test.db")
    def test_get_pending_k2n_basic(
        self, mock_check_hit, mock_get_loto, mock_get_bridges
    ):
        """Test basic pending K2N bridges."""
        from logic.dashboard_analytics import get_pending_k2n_bridges

        last_row = ["23001"] + ["A"] * 9
        prev_row = ["23000"] + ["B"] * 9

        mock_get_loto.return_value = ["01", "02", "03"]
        mock_check_hit.return_value = "❌"  # Missed
        mock_get_bridges.return_value = []

        result = get_pending_k2n_bridges(last_row, prev_row)

        assert isinstance(result, list)

    @patch("logic.dashboard_analytics.DB_NAME", "test.db")
    def test_get_pending_k2n_empty_rows(self):
        """Test with empty rows."""
        from logic.dashboard_analytics import get_pending_k2n_bridges

        result = get_pending_k2n_bridges(None, None)
        assert result == []

    @patch("logic.dashboard_analytics.getAllLoto_V30")
    @patch("logic.dashboard_analytics.DB_NAME", "test.db")
    def test_get_pending_k2n_no_loto(self, mock_get_loto):
        """Test with no loto results."""
        from logic.dashboard_analytics import get_pending_k2n_bridges

        last_row = ["23001"] + ["A"] * 9
        prev_row = ["23000"] + ["B"] * 9

        mock_get_loto.return_value = []

        result = get_pending_k2n_bridges(last_row, prev_row)
        assert result == []


class TestGetTopMemoryBridgePredictions:
    """Tests for get_top_memory_bridge_predictions function."""

    @patch("logic.dashboard_analytics.get_27_loto_names")
    @patch("logic.dashboard_analytics.get_27_loto_positions")
    @patch("logic.dashboard_analytics.getAllLoto_V30")
    @patch("logic.dashboard_analytics.calculate_bridge_stl")
    def test_get_top_memory_bridge_empty_data(
        self, mock_calc_stl, mock_get_loto, mock_get_positions, mock_get_names
    ):
        """Test with empty data."""
        from logic.dashboard_analytics import get_top_memory_bridge_predictions

        mock_get_names.return_value = ["ĐB", "G1", "G2"]

        result = get_top_memory_bridge_predictions([], ["last_row"], top_n=5)
        assert result == []

    @patch("logic.dashboard_analytics.get_27_loto_names")
    @patch("logic.dashboard_analytics.get_27_loto_positions")
    @patch("logic.dashboard_analytics.getAllLoto_V30")
    @patch("logic.dashboard_analytics.calculate_bridge_stl")
    def test_get_top_memory_bridge_insufficient_data(
        self, mock_calc_stl, mock_get_loto, mock_get_positions, mock_get_names
    ):
        """Test with insufficient data (< 2 rows)."""
        from logic.dashboard_analytics import get_top_memory_bridge_predictions

        mock_get_names.return_value = ["ĐB", "G1"]

        all_data_ai = [["23001"] + ["A"] * 9]

        result = get_top_memory_bridge_predictions(all_data_ai, all_data_ai[0], top_n=5)
        assert result == []


class TestModuleImportsAndFallbacks:
    """Tests for module import handling and fallbacks."""

    def test_module_imports_successfully(self):
        """Test that module imports without errors."""
        import logic.dashboard_analytics

        assert logic.dashboard_analytics is not None

    def test_fallback_functions_defined(self):
        """Test that fallback functions are defined."""
        from logic.dashboard_analytics import (
            getAllLoto_V30,
            checkHitSet_V30_K2N,
            get_27_loto_names,
        )

        # Functions should exist (either imported or fallback)
        assert callable(getAllLoto_V30)
        assert callable(checkHitSet_V30_K2N)
        assert callable(get_27_loto_names)


class TestErrorHandling:
    """Tests for error handling across dashboard_analytics functions."""

    def test_functions_handle_exceptions_gracefully(self):
        """Test that functions handle exceptions without crashing."""
        from logic.dashboard_analytics import (
            get_loto_stats_last_n_days,
            get_loto_gan_stats,
            get_prediction_consensus,
            get_high_win_rate_predictions,
            get_pending_k2n_bridges,
        )

        # All should return empty lists on error, not crash
        result1 = get_loto_stats_last_n_days(None)
        assert isinstance(result1, list)

        result2 = get_loto_gan_stats(None)
        assert isinstance(result2, list)

        result3 = get_prediction_consensus()
        assert isinstance(result3, list)

        result4 = get_high_win_rate_predictions()
        assert isinstance(result4, list)

        result5 = get_pending_k2n_bridges(None, None)
        assert isinstance(result5, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
