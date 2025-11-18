"""Unit tests for logic/dashboard_analytics.py module."""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestGetLotoStatsLastNDays:
    """Tests for get_loto_stats_last_n_days function."""

    @patch("logic.dashboard_analytics.getAllLoto_V30")
    @patch("logic.dashboard_analytics.SETTINGS")
    def test_get_loto_stats_basic(self, mock_settings, mock_get_loto):
        """Test basic loto stats calculation."""
        from logic.dashboard_analytics import get_loto_stats_last_n_days

        mock_settings.STATS_DAYS = 3

        # Mock data: 3 rows with loto numbers
        mock_get_loto.side_effect = [["01", "02", "03"], ["01", "04"], ["01", "02"]]

        all_data_ai = [
            ["23001", "A1", "B1", "C1", "D1", "E1", "F1", "G1", "H1", "I1"],
            ["23002", "A2", "B2", "C2", "D2", "E2", "F2", "G2", "H2", "I2"],
            ["23003", "A3", "B3", "C3", "D3", "E3", "F3", "G3", "H3", "I3"],
        ]

        result = get_loto_stats_last_n_days(all_data_ai, n=3)

        assert isinstance(result, list)
        # '01' appears 3 times, should be first
        if len(result) > 0:
            assert result[0][0] == "01"
            assert result[0][1] == 3  # hit count

    @patch("logic.dashboard_analytics.SETTINGS")
    def test_get_loto_stats_empty_data(self, mock_settings):
        """Test with empty data."""
        from logic.dashboard_analytics import get_loto_stats_last_n_days

        mock_settings.STATS_DAYS = 7

        result = get_loto_stats_last_n_days([], n=7)
        assert result == []

    @patch("logic.dashboard_analytics.SETTINGS")
    def test_get_loto_stats_none_data(self, mock_settings):
        """Test with None data."""
        from logic.dashboard_analytics import get_loto_stats_last_n_days

        mock_settings.STATS_DAYS = 7

        result = get_loto_stats_last_n_days(None, n=7)
        assert result == []

    @patch("logic.dashboard_analytics.getAllLoto_V30")
    @patch("logic.dashboard_analytics.SETTINGS")
    def test_get_loto_stats_uses_default_n(self, mock_settings, mock_get_loto):
        """Test that function uses SETTINGS.STATS_DAYS when n is None."""
        from logic.dashboard_analytics import get_loto_stats_last_n_days

        mock_settings.STATS_DAYS = 5
        mock_get_loto.return_value = ["01", "02"]

        all_data_ai = [["row" + str(i)] * 10 for i in range(10)]

        result = get_loto_stats_last_n_days(all_data_ai, n=None)

        # Should process last 5 rows
        assert mock_get_loto.call_count == 5


class TestGetLotoGanStats:
    """Tests for get_loto_gan_stats function."""

    @patch("logic.dashboard_analytics.getAllLoto_V30")
    @patch("logic.dashboard_analytics.SETTINGS")
    def test_get_loto_gan_stats_basic(self, mock_settings, mock_get_loto):
        """Test basic gan stats calculation."""
        from logic.dashboard_analytics import get_loto_gan_stats

        mock_settings.GAN_DAYS = 3

        # Mock: recent days have lotos 01-05, so 06-99 are gan
        mock_get_loto.side_effect = [["01", "02"], ["03", "04"], ["05"]] + [
            ["01"]
        ] * 100  # Past history

        all_data_ai = [["row" + str(i)] * 10 for i in range(10)]

        result = get_loto_gan_stats(all_data_ai, n_days=3)

        assert isinstance(result, list)
        # Should find gan lotos (06-99)
        if len(result) > 0:
            # Verify it's a list of tuples (loto, days_gan)
            assert isinstance(result[0], tuple)
            assert len(result[0]) == 2

    @patch("logic.dashboard_analytics.SETTINGS")
    def test_get_loto_gan_stats_empty_data(self, mock_settings):
        """Test with empty data."""
        from logic.dashboard_analytics import get_loto_gan_stats

        mock_settings.GAN_DAYS = 8

        result = get_loto_gan_stats([], n_days=8)
        assert result == []

    @patch("logic.dashboard_analytics.SETTINGS")
    def test_get_loto_gan_stats_insufficient_data(self, mock_settings):
        """Test with insufficient data (less than n_days)."""
        from logic.dashboard_analytics import get_loto_gan_stats

        mock_settings.GAN_DAYS = 10

        all_data_ai = [["row" + str(i)] * 10 for i in range(5)]

        result = get_loto_gan_stats(all_data_ai, n_days=10)
        assert result == []

    @patch("logic.dashboard_analytics.getAllLoto_V30")
    @patch("logic.dashboard_analytics.SETTINGS")
    def test_get_loto_gan_stats_no_gan_lotos(self, mock_settings, mock_get_loto):
        """Test when all lotos appeared recently (no gan)."""
        from logic.dashboard_analytics import get_loto_gan_stats

        mock_settings.GAN_DAYS = 3

        # All 100 lotos appear in recent days
        all_lotos = [str(i).zfill(2) for i in range(100)]
        mock_get_loto.side_effect = [all_lotos[:33], all_lotos[33:66], all_lotos[66:]]

        all_data_ai = [["row" + str(i)] * 10 for i in range(10)]

        result = get_loto_gan_stats(all_data_ai, n_days=3)
        assert result == []


class TestAnalyticsFunctions:
    """Integration tests for analytics functions."""

    def test_functions_handle_errors_gracefully(self):
        """Test that functions handle errors without crashing."""
        from logic.dashboard_analytics import get_loto_stats_last_n_days, get_loto_gan_stats

        # Test with invalid data types
        result1 = get_loto_stats_last_n_days(None)
        assert isinstance(result1, list)

        result2 = get_loto_gan_stats(None)
        assert isinstance(result2, list)

    @patch("logic.dashboard_analytics.getAllLoto_V30")
    def test_functions_return_expected_types(self, mock_get_loto):
        """Test that functions return expected data types."""
        from logic.dashboard_analytics import get_loto_stats_last_n_days, get_loto_gan_stats

        mock_get_loto.return_value = ["01", "02"]

        all_data_ai = [["row" + str(i)] * 10 for i in range(10)]

        result1 = get_loto_stats_last_n_days(all_data_ai)
        assert isinstance(result1, list)

        result2 = get_loto_gan_stats(all_data_ai)
        assert isinstance(result2, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
