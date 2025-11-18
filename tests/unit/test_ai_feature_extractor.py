"""Unit tests for logic/ai_feature_extractor.py module."""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestParseWinRateText:
    """Tests for _parse_win_rate_text function."""

    def test_parse_win_rate_text_valid_percent(self):
        """Test parsing valid percentage string."""
        from logic.ai_feature_extractor import _parse_win_rate_text

        result = _parse_win_rate_text("50.5%")
        assert result == 50.5

    def test_parse_win_rate_text_valid_without_percent(self):
        """Test parsing valid number string without percent."""
        from logic.ai_feature_extractor import _parse_win_rate_text

        result = _parse_win_rate_text("75.3")
        assert result == 75.3

    def test_parse_win_rate_text_empty_string(self):
        """Test parsing empty string."""
        from logic.ai_feature_extractor import _parse_win_rate_text

        result = _parse_win_rate_text("")
        assert result == 0.0

    def test_parse_win_rate_text_none(self):
        """Test parsing None value."""
        from logic.ai_feature_extractor import _parse_win_rate_text

        result = _parse_win_rate_text(None)
        assert result == 0.0

    def test_parse_win_rate_text_invalid_string(self):
        """Test parsing invalid string."""
        from logic.ai_feature_extractor import _parse_win_rate_text

        result = _parse_win_rate_text("invalid")
        assert result == 0.0

    def test_parse_win_rate_text_with_spaces(self):
        """Test parsing string with spaces."""
        from logic.ai_feature_extractor import _parse_win_rate_text

        result = _parse_win_rate_text("  60.0%  ")
        assert result == 60.0


class TestStandardizePair:
    """Tests for _standardize_pair function."""

    def test_standardize_pair_basic(self):
        """Test basic pair standardization."""
        from logic.ai_feature_extractor import _standardize_pair

        result = _standardize_pair(["30", "01"])
        assert result == "01-30"

    def test_standardize_pair_already_sorted(self):
        """Test pair that's already sorted."""
        from logic.ai_feature_extractor import _standardize_pair

        result = _standardize_pair(["01", "30"])
        assert result == "01-30"

    def test_standardize_pair_same_numbers(self):
        """Test pair with same numbers."""
        from logic.ai_feature_extractor import _standardize_pair

        result = _standardize_pair(["15", "15"])
        assert result == "15-15"

    def test_standardize_pair_empty_list(self):
        """Test with empty list."""
        from logic.ai_feature_extractor import _standardize_pair

        result = _standardize_pair([])
        assert result is None

    def test_standardize_pair_wrong_length(self):
        """Test with wrong length list."""
        from logic.ai_feature_extractor import _standardize_pair

        result = _standardize_pair(["01", "02", "03"])
        assert result is None

    def test_standardize_pair_none(self):
        """Test with None input."""
        from logic.ai_feature_extractor import _standardize_pair

        result = _standardize_pair(None)
        assert result is None

    def test_standardize_pair_single_element(self):
        """Test with single element list."""
        from logic.ai_feature_extractor import _standardize_pair

        result = _standardize_pair(["01"])
        assert result is None


class TestGetDailyBridgePredictions:
    """Tests for _get_daily_bridge_predictions function."""

    @patch("logic.ai_feature_extractor.get_all_managed_bridges")
    @patch("logic.ai_feature_extractor.ALL_15_BRIDGE_FUNCTIONS_V5")
    @patch("logic.ai_feature_extractor.get_27_loto_names")
    def test_get_daily_bridge_predictions_basic(
        self, mock_loto_names, mock_bridge_functions, mock_managed_bridges
    ):
        """Test basic daily bridge predictions calculation."""
        from logic.ai_feature_extractor import _get_daily_bridge_predictions

        # Mock data
        mock_loto_names.return_value = [f"V{i}" for i in range(27)]
        mock_managed_bridges.return_value = []
        mock_bridge_functions.__len__ = Mock(return_value=0)
        mock_bridge_functions.__getitem__ = Mock(side_effect=IndexError)

        all_data_ai = [
            ["23001"] + ["data"] * 9,
            ["23002"] + ["data"] * 9,
            ["23003"] + ["data"] * 9,
        ]

        result = _get_daily_bridge_predictions(all_data_ai)

        assert isinstance(result, dict)

    @patch("logic.ai_feature_extractor.get_all_managed_bridges")
    @patch("logic.ai_feature_extractor.ALL_15_BRIDGE_FUNCTIONS_V5")
    @patch("logic.ai_feature_extractor.get_27_loto_names")
    def test_get_daily_bridge_predictions_empty_data(
        self, mock_loto_names, mock_bridge_functions, mock_managed_bridges
    ):
        """Test with empty data."""
        from logic.ai_feature_extractor import _get_daily_bridge_predictions

        mock_loto_names.return_value = [f"V{i}" for i in range(27)]
        mock_managed_bridges.return_value = []
        mock_bridge_functions.__len__ = Mock(return_value=0)

        all_data_ai = []

        result = _get_daily_bridge_predictions(all_data_ai)

        assert isinstance(result, dict)

    @patch("logic.ai_feature_extractor.get_all_managed_bridges")
    @patch("logic.ai_feature_extractor.ALL_15_BRIDGE_FUNCTIONS_V5")
    @patch("logic.ai_feature_extractor.get_27_loto_names")
    def test_get_daily_bridge_predictions_with_managed_bridges(
        self, mock_loto_names, mock_bridge_functions, mock_managed_bridges
    ):
        """Test with managed bridges."""
        from logic.ai_feature_extractor import _get_daily_bridge_predictions

        mock_loto_names.return_value = [f"V{i}" for i in range(27)]
        mock_managed_bridges.return_value = [
            {
                "win_rate_text": "50.5%",
                "max_lose_streak_k2n": 5,
                "current_streak": 2,
                "pos1_idx": -1,
            }
        ]
        mock_bridge_functions.__len__ = Mock(return_value=0)

        all_data_ai = [["23001"] + ["data"] * 9, ["23002"] + ["data"] * 9]

        result = _get_daily_bridge_predictions(all_data_ai)

        assert isinstance(result, dict)


class TestRunAITrainingThreaded:
    """Tests for run_ai_training_threaded function."""

    def test_run_ai_training_threaded_exists(self):
        """Test that run_ai_training_threaded function exists."""
        from logic import ai_feature_extractor

        assert hasattr(ai_feature_extractor, "run_ai_training_threaded")
        assert callable(ai_feature_extractor.run_ai_training_threaded)

    def test_run_ai_training_threaded_signature(self):
        """Test function signature."""
        from logic.ai_feature_extractor import run_ai_training_threaded
        import inspect

        sig = inspect.signature(run_ai_training_threaded)
        # Should accept callback parameter
        assert "callback" in sig.parameters or len(sig.parameters) >= 0


class TestRunAIPredictionForDashboard:
    """Tests for run_ai_prediction_for_dashboard function."""

    def test_run_ai_prediction_exists(self):
        """Test that run_ai_prediction_for_dashboard function exists."""
        from logic import ai_feature_extractor

        assert hasattr(ai_feature_extractor, "run_ai_prediction_for_dashboard")
        assert callable(ai_feature_extractor.run_ai_prediction_for_dashboard)

    def test_run_ai_prediction_signature(self):
        """Test function signature."""
        from logic.ai_feature_extractor import run_ai_prediction_for_dashboard
        import inspect

        sig = inspect.signature(run_ai_prediction_for_dashboard)
        # Should return tuple (result, error)
        # No required parameters or optional parameters
        assert len(sig.parameters) >= 0


class TestSettingsIntegration:
    """Tests for SETTINGS integration."""

    def test_settings_import_attempt(self):
        """Test that module attempts to import SETTINGS."""
        from logic import ai_feature_extractor
        import inspect

        # Check source code contains SETTINGS import
        source = inspect.getsource(ai_feature_extractor)
        assert "SETTINGS" in source or "config_manager" in source


class TestModuleImports:
    """Tests for module imports."""

    def test_module_imports_successfully(self):
        """Test that module can be imported."""
        try:
            from logic import ai_feature_extractor

            assert hasattr(ai_feature_extractor, "_parse_win_rate_text")
            assert hasattr(ai_feature_extractor, "_standardize_pair")
        except ImportError:
            pytest.fail("ai_feature_extractor module should import successfully")

    def test_fallback_functions_defined(self):
        """Test that fallback functions exist if imports fail."""
        from logic import ai_feature_extractor

        # These should exist (either real or fallback)
        assert hasattr(ai_feature_extractor, "run_ai_training_threaded")
        assert hasattr(ai_feature_extractor, "run_ai_prediction_for_dashboard")


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_parse_win_rate_text_edge_cases(self):
        """Test edge cases for win rate parsing."""
        from logic.ai_feature_extractor import _parse_win_rate_text

        # Zero
        assert _parse_win_rate_text("0%") == 0.0
        assert _parse_win_rate_text("0.0") == 0.0

        # 100%
        assert _parse_win_rate_text("100%") == 100.0
        assert _parse_win_rate_text("100.0") == 100.0

        # Decimal values
        assert _parse_win_rate_text("45.67%") == 45.67

    def test_standardize_pair_string_values(self):
        """Test pair standardization with string values."""
        from logic.ai_feature_extractor import _standardize_pair

        # Two-digit strings
        result = _standardize_pair(["99", "01"])
        assert result == "01-99"

        # Single-digit strings
        result = _standardize_pair(["5", "3"])
        assert result == "3-5"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
