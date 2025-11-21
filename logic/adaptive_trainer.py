# logic/adaptive_trainer.py
"""
V7.7 Phase 3 Adaptive Retraining System

This module manages automatic model retraining to adapt to changing lottery patterns.
It supports two modes:
1. Incremental: Fast daily retraining on rolling window of recent data
2. Full: Complete monthly retraining with hyperparameter tuning

The system monitors F1-Score performance and triggers retraining when degradation
is detected.
"""

from datetime import datetime
import traceback


class AdaptiveTrainer:
    """
    Manages automatic model retraining on rolling windows of data.
    """

    def __init__(self, config=None):
        """
        Initialize Adaptive Trainer with configuration.

        Args:
            config: Optional dict with settings:
                - ROLLING_WINDOW_SIZE: Periods for incremental training (default: 400)
                - MIN_RETRAINING_GAP_DAYS: Minimum days between retrains (default: 7)
                - F1_DEGRADATION_THRESHOLD: Trigger retrain if F1 drops (default: 0.02)
                - FULL_RETRAIN_INTERVAL_DAYS: Days between full retrains (default: 30)
                - ENABLE_AUTO_RETRAIN: Master switch (default: False for safety)
        """
        if config is None:
            config = self._load_default_config()

        self.rolling_window_size = config.get('ROLLING_WINDOW_SIZE', 400)
        self.min_retraining_gap = config.get('MIN_RETRAINING_GAP_DAYS', 7)
        self.f1_degradation_threshold = config.get('F1_DEGRADATION_THRESHOLD', 0.02)
        self.full_retrain_interval = config.get('FULL_RETRAIN_INTERVAL_DAYS', 30)
        self.enable_auto_retrain = config.get('ENABLE_AUTO_RETRAIN', False)

        self.last_retrain_date = None
        self.last_full_retrain = None
        self.baseline_f1_score = None

    def _load_default_config(self):
        """Load configuration from config_manager if available."""
        try:
            from logic.config_manager import SETTINGS
            return {
                'ROLLING_WINDOW_SIZE': getattr(SETTINGS, 'ROLLING_WINDOW_SIZE', 400),
                'MIN_RETRAINING_GAP_DAYS': getattr(SETTINGS, 'MIN_RETRAINING_GAP_DAYS', 7),
                'F1_DEGRADATION_THRESHOLD': getattr(SETTINGS, 'F1_DEGRADATION_THRESHOLD', 0.02),
                'FULL_RETRAIN_INTERVAL_DAYS': getattr(SETTINGS, 'FULL_RETRAIN_INTERVAL_DAYS', 30),
                'ENABLE_AUTO_RETRAIN': getattr(SETTINGS, 'ENABLE_AUTO_RETRAIN', False)
            }
        except ImportError:
            return {}

    def should_retrain_incremental(self, current_date=None, current_f1_score=None):
        """
        Decide if incremental retraining is needed.

        Args:
            current_date: Date to check (default: today)
            current_f1_score: Current model F1 score (optional)

        Returns:
            tuple: (should_retrain, reason)
        """
        if not self.enable_auto_retrain:
            return False, "Auto-retrain disabled"

        if current_date is None:
            current_date = datetime.now()

        # Check time gap
        if self.last_retrain_date:
            days_since_retrain = (current_date - self.last_retrain_date).days
            if days_since_retrain < self.min_retraining_gap:
                return False, f"Too soon (only {days_since_retrain} days)"

        # Check performance degradation
        if self.baseline_f1_score and current_f1_score:
            degradation = self.baseline_f1_score - current_f1_score
            if degradation > self.f1_degradation_threshold:
                return True, f"Performance degraded ({degradation:.3f} drop in F1)"

        # Check if enough time has passed
        if self.last_retrain_date:
            days_since_retrain = (current_date - self.last_retrain_date).days
            if days_since_retrain >= 7:
                return True, "Weekly retrain schedule"

        # Default: retrain if never trained before
        if self.last_retrain_date is None:
            return True, "Initial training"

        return False, "No retrain needed"

    def should_retrain_full(self, current_date=None):
        """
        Decide if full retraining is needed.

        Args:
            current_date: Date to check (default: today)

        Returns:
            tuple: (should_retrain, reason)
        """
        if not self.enable_auto_retrain:
            return False, "Auto-retrain disabled"

        if current_date is None:
            current_date = datetime.now()

        if self.last_full_retrain is None:
            return True, "Initial full training"

        days_since_full = (current_date - self.last_full_retrain).days
        if days_since_full >= self.full_retrain_interval:
            return True, f"Monthly schedule ({days_since_full} days)"

        return False, "No full retrain needed"

    def incremental_retrain(self, all_data_ai):
        """
        Perform incremental retraining on rolling window of recent data.

        Args:
            all_data_ai: Complete lottery data list

        Returns:
            tuple: (success, message)
        """
        try:
            # Take last N periods
            if len(all_data_ai) < self.rolling_window_size:
                recent_data = all_data_ai
            else:
                recent_data = all_data_ai[-self.rolling_window_size:]

            print(f"Incremental retrain using last {len(recent_data)} periods...")

            # Retrain model (same as full train but less data)
            from logic.ai_feature_extractor import _get_daily_bridge_predictions
            from logic.ml_model import train_ai_model

            bridge_predictions = _get_daily_bridge_predictions(recent_data)
            success, msg = train_ai_model(
                recent_data,
                bridge_predictions,
                use_hyperparameter_tuning=False  # Use existing hyperparameters
            )

            if success:
                self.last_retrain_date = datetime.now()
                print(f"✅ Incremental retrain successful at {self.last_retrain_date}")

            return success, msg

        except Exception as e:
            error_msg = f"Error during incremental retrain: {e}\n{traceback.format_exc()}"
            print(error_msg)
            return False, error_msg

    def full_retrain(self, all_data_ai, use_hyperparameter_tuning=True):
        """
        Perform full retraining on all available data.

        Args:
            all_data_ai: Complete lottery data list
            use_hyperparameter_tuning: Whether to tune hyperparameters

        Returns:
            tuple: (success, message)
        """
        try:
            print(f"Full retrain using all {len(all_data_ai)} periods...")

            from logic.ai_feature_extractor import _get_daily_bridge_predictions
            from logic.ml_model import train_ai_model

            bridge_predictions = _get_daily_bridge_predictions(all_data_ai)
            success, msg = train_ai_model(
                all_data_ai,
                bridge_predictions,
                use_hyperparameter_tuning=use_hyperparameter_tuning
            )

            if success:
                self.last_retrain_date = datetime.now()
                self.last_full_retrain = datetime.now()
                print(f"✅ Full retrain successful at {self.last_full_retrain}")

            return success, msg

        except Exception as e:
            error_msg = f"Error during full retrain: {e}\n{traceback.format_exc()}"
            print(error_msg)
            return False, error_msg

    def auto_retrain(self, all_data_ai, current_f1_score=None):
        """
        Automatically decide and execute appropriate retraining.

        Args:
            all_data_ai: Complete lottery data list
            current_f1_score: Optional current F1 score for degradation check

        Returns:
            tuple: (success, message, retrain_type)
                retrain_type: 'full', 'incremental', or None
        """
        if not self.enable_auto_retrain:
            return False, "Auto-retrain is disabled", None

        # Check if full retrain needed
        should_full, full_reason = self.should_retrain_full()
        if should_full:
            print(f"Triggering FULL retrain: {full_reason}")
            success, msg = self.full_retrain(all_data_ai, use_hyperparameter_tuning=True)
            return success, msg, 'full'

        # Check if incremental retrain needed
        should_incremental, incremental_reason = self.should_retrain_incremental(
            current_f1_score=current_f1_score
        )
        if should_incremental:
            print(f"Triggering INCREMENTAL retrain: {incremental_reason}")
            success, msg = self.incremental_retrain(all_data_ai)
            return success, msg, 'incremental'

        return True, "No retraining needed", None

    def set_baseline_f1(self, f1_score):
        """Set baseline F1 score for comparison."""
        self.baseline_f1_score = f1_score
        print(f"Baseline F1-Score set to: {f1_score:.4f}")

    def get_status(self):
        """
        Get current status of Adaptive Trainer.

        Returns:
            dict: Status information
        """
        return {
            'enabled': self.enable_auto_retrain,
            'last_retrain': self.last_retrain_date,
            'last_full_retrain': self.last_full_retrain,
            'baseline_f1': self.baseline_f1_score,
            'rolling_window_size': self.rolling_window_size,
            'min_gap_days': self.min_retraining_gap,
            'f1_threshold': self.f1_degradation_threshold,
            'full_retrain_interval': self.full_retrain_interval
        }


# Singleton instance for convenience
_trainer_instance = None


def get_adaptive_trainer(config=None):
    """Get singleton instance of AdaptiveTrainer."""
    global _trainer_instance
    if _trainer_instance is None:
        _trainer_instance = AdaptiveTrainer(config)
    return _trainer_instance
