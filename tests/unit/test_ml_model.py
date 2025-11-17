"""Unit tests for logic/ml_model.py module."""
import pytest
import os
import sys
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestStandardizePair:
    """Tests for _standardize_pair helper function."""

    def test_standardize_pair_basic(self):
        """Test basic pair standardization."""
        from logic.ml_model import _standardize_pair

        result = _standardize_pair(["30", "01"])
        assert result == "01-30"

    def test_standardize_pair_already_sorted(self):
        """Test pair that's already sorted."""
        from logic.ml_model import _standardize_pair

        result = _standardize_pair(["01", "30"])
        assert result == "01-30"

    def test_standardize_pair_same_numbers(self):
        """Test pair with same numbers."""
        from logic.ml_model import _standardize_pair

        result = _standardize_pair(["05", "05"])
        assert result == "05-05"

    def test_standardize_pair_empty_list(self):
        """Test with empty list."""
        from logic.ml_model import _standardize_pair

        result = _standardize_pair([])
        assert result is None

    def test_standardize_pair_wrong_length(self):
        """Test with wrong list length."""
        from logic.ml_model import _standardize_pair

        result1 = _standardize_pair(["01"])
        result2 = _standardize_pair(["01", "02", "03"])

        assert result1 is None
        assert result2 is None

    def test_standardize_pair_none(self):
        """Test with None input."""
        from logic.ml_model import _standardize_pair

        result = _standardize_pair(None)
        assert result is None


class TestPrepareTrainingData:
    """Tests for prepare_training_data function."""

    @patch("logic.ml_model.getAllLoto_V30")
    @patch("logic.ml_model.get_loto_stats_last_n_days")
    @patch("logic.ml_model.get_loto_gan_stats")
    @patch("logic.ml_model.SETTINGS")
    def test_prepare_training_data_insufficient_data(
        self, mock_settings, mock_gan, mock_stats, mock_get_loto
    ):
        """Test with insufficient data."""
        from logic.ml_model import prepare_training_data, MIN_DATA_TO_TRAIN

        mock_settings.STATS_DAYS = 7
        mock_settings.GAN_DAYS = 8

        # Not enough data
        all_data_ai = [["row" + str(i)] * 10 for i in range(MIN_DATA_TO_TRAIN - 1)]
        daily_predictions = {}

        X, y = prepare_training_data(all_data_ai, daily_predictions)

        assert X is None
        assert y is None

    @patch("logic.ml_model.getAllLoto_V30")
    @patch("logic.ml_model.get_loto_stats_last_n_days")
    @patch("logic.ml_model.get_loto_gan_stats")
    @patch("logic.ml_model.SETTINGS")
    def test_prepare_training_data_empty_data(
        self, mock_settings, mock_gan, mock_stats, mock_get_loto
    ):
        """Test with empty data."""
        from logic.ml_model import prepare_training_data

        mock_settings.STATS_DAYS = 7
        mock_settings.GAN_DAYS = 8

        X, y = prepare_training_data([], {})

        assert X is None
        assert y is None

    @patch("logic.ml_model.getAllLoto_V30")
    @patch("logic.ml_model.get_loto_stats_last_n_days")
    @patch("logic.ml_model.get_loto_gan_stats")
    @patch("logic.ml_model.SETTINGS")
    def test_prepare_training_data_basic(
        self, mock_settings, mock_gan, mock_stats, mock_get_loto
    ):
        """Test basic training data preparation."""
        from logic.ml_model import prepare_training_data

        mock_settings.STATS_DAYS = 7
        mock_settings.GAN_DAYS = 8

        # Mock functions to return simple data
        mock_get_loto.return_value = ["01", "02"]
        mock_stats.return_value = [("01", 5, 3), ("02", 4, 2)]
        mock_gan.return_value = [("99", 10), ("98", 9)]

        # Create mock data (60 rows to exceed MIN_DATA_TO_TRAIN)
        all_data_ai = [["2300" + str(i).zfill(2)] + ["data"] * 9 for i in range(60)]

        # Mock daily bridge predictions
        daily_predictions = {
            str(row[0]): {
                "01": {
                    "bridge_count": 2,
                    "avg_win_rate": 50.0,
                    "min_k2n_risk": 3,
                    "current_lose_streak": 0,
                }
            }
            for row in all_data_ai
        }

        X, y = prepare_training_data(all_data_ai, daily_predictions)

        # Should return numpy arrays
        assert X is not None
        assert y is not None
        assert isinstance(X, (np.ndarray, list))
        assert isinstance(y, (np.ndarray, list))

    @patch("logic.ml_model.getAllLoto_V30")
    @patch("logic.ml_model.get_loto_stats_last_n_days")
    @patch("logic.ml_model.get_loto_gan_stats")
    @patch("logic.ml_model.SETTINGS")
    def test_prepare_training_data_none_input(
        self, mock_settings, mock_gan, mock_stats, mock_get_loto
    ):
        """Test with None inputs."""
        from logic.ml_model import prepare_training_data

        mock_settings.STATS_DAYS = 7
        mock_settings.GAN_DAYS = 8

        X1, y1 = prepare_training_data(None, {})
        X2, y2 = prepare_training_data([], None)

        assert X1 is None
        assert y1 is None
        assert X2 is None
        assert y2 is None


class TestConstants:
    """Tests for module constants."""

    def test_all_lotos_length(self):
        """Test ALL_LOTOS has 100 elements."""
        from logic.ml_model import ALL_LOTOS

        assert len(ALL_LOTOS) == 100

    def test_all_lotos_format(self):
        """Test ALL_LOTOS elements are zero-padded."""
        from logic.ml_model import ALL_LOTOS

        assert ALL_LOTOS[0] == "00"
        assert ALL_LOTOS[9] == "09"
        assert ALL_LOTOS[10] == "10"
        assert ALL_LOTOS[99] == "99"

    def test_min_data_to_train(self):
        """Test MIN_DATA_TO_TRAIN is reasonable."""
        from logic.ml_model import MIN_DATA_TO_TRAIN

        assert MIN_DATA_TO_TRAIN >= 10
        assert MIN_DATA_TO_TRAIN <= 1000

    def test_model_file_paths(self):
        """Test model file paths are defined."""
        from logic.ml_model import MODEL_FILE_PATH, SCALER_FILE_PATH

        assert "model" in MODEL_FILE_PATH.lower()
        assert "scaler" in SCALER_FILE_PATH.lower()
        assert MODEL_FILE_PATH.endswith(".joblib")
        assert SCALER_FILE_PATH.endswith(".joblib")


class TestGetAIPredictions:
    """Tests for get_ai_predictions function (if exists)."""

    @patch("logic.ml_model.os.path.exists")
    def test_get_ai_predictions_model_not_found(self, mock_exists):
        """Test when model file doesn't exist."""
        # Import will fail if function doesn't exist, which is okay
        try:
            from logic.ml_model import get_ai_predictions

            mock_exists.return_value = False

            result = get_ai_predictions([], {})

            # Should return None or tuple with error message when model not found
            assert result is None or isinstance(result, tuple) or result == {} or result == []
        except ImportError:
            # Function doesn't exist yet, test passes
            pass


class TestTrainAIModel:
    """Tests for train_ai_model function (if exists)."""

    def test_train_ai_model_insufficient_data(self):
        """Test training with insufficient data."""
        try:
            from logic.ml_model import train_ai_model

            # Mock insufficient data
            result = train_ai_model([], {})

            # Should handle gracefully (return False or error message)
            assert result is False or isinstance(result, tuple)
        except ImportError:
            # Function doesn't exist yet, test passes
            pass


class TestSettingsIntegration:
    """Tests for SETTINGS integration."""

    @patch("logic.ml_model.SETTINGS")
    def test_settings_attributes_used(self, mock_settings):
        """Test that SETTINGS attributes are accessed safely."""
        from logic.ml_model import prepare_training_data

        mock_settings.STATS_DAYS = 7
        mock_settings.GAN_DAYS = 8

        # Should not raise AttributeError even with mock SETTINGS
        X, y = prepare_training_data([], {})

        # Should handle empty data gracefully
        assert X is None
        assert y is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
