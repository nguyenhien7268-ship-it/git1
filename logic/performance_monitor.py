# logic/performance_monitor.py
"""
V7.7 Phase 3 Performance Monitoring System

This module tracks model performance over time and detects degradation.
It provides:
- Performance metrics tracking (F1-Score, Accuracy)
- Degradation detection
- Alerting mechanism
- Historical analysis
"""

from datetime import datetime
import numpy as np


class PerformanceMonitor:
    """
    Track model performance over time and detect degradation.
    """

    def __init__(self, degradation_threshold=0.02, lookback_periods=7):
        """
        Initialize Performance Monitor.

        Args:
            degradation_threshold: F1-Score drop threshold to trigger alert (default: 0.02)
            lookback_periods: Number of periods for moving average (default: 7)
        """
        self.performance_history = []  # List of performance records
        self.degradation_threshold = degradation_threshold
        self.lookback_periods = lookback_periods
        self.alerts = []

    def record_performance(self, date, predictions, actuals, model_version=None):
        """
        Calculate and record performance metrics.

        Args:
            date: Date of the predictions
            predictions: List of predicted labels (0/1)
            actuals: List of actual outcomes (0/1)
            model_version: Optional model version string

        Returns:
            dict: Calculated metrics
        """
        try:
            from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score

            # Calculate metrics
            f1 = f1_score(actuals, predictions, zero_division=0)
            acc = accuracy_score(actuals, predictions)
            precision = precision_score(actuals, predictions, zero_division=0)
            recall = recall_score(actuals, predictions, zero_division=0)

            record = {
                'date': date,
                'f1_score': f1,
                'accuracy': acc,
                'precision': precision,
                'recall': recall,
                'samples': len(predictions),
                'model_version': model_version,
                'timestamp': datetime.now()
            }

            self.performance_history.append(record)

            # Check for degradation
            if self._check_degradation():
                self._trigger_alert(record)

            return record

        except Exception as e:
            print(f"Error recording performance: {e}")
            return {}

    def _check_degradation(self, lookback=None):
        """
        Check if recent performance is degrading.

        Uses moving average comparison.

        Args:
            lookback: Number of periods to compare (default: self.lookback_periods)

        Returns:
            bool: True if degradation detected
        """
        if lookback is None:
            lookback = self.lookback_periods

        if len(self.performance_history) < lookback * 2:
            return False

        recent = self.performance_history[-lookback:]
        previous = self.performance_history[-lookback * 2:-lookback]

        recent_avg = np.mean([x['f1_score'] for x in recent])
        previous_avg = np.mean([x['f1_score'] for x in previous])

        degradation = previous_avg - recent_avg
        return degradation > self.degradation_threshold

    def _trigger_alert(self, record):
        """
        Trigger alert for performance degradation.

        Args:
            record: Performance record that triggered the alert
        """
        alert = {
            'timestamp': datetime.now(),
            'type': 'DEGRADATION',
            'f1_score': record['f1_score'],
            'message': f"Performance degradation detected! F1-Score: {record['f1_score']:.4f}",
            'severity': 'HIGH' if record['f1_score'] < 0.5 else 'MEDIUM'
        }

        self.alerts.append(alert)
        print(f"🚨 ALERT: {alert['message']}")

    def get_recent_performance(self, periods=7):
        """
        Get performance for recent periods.

        Args:
            periods: Number of recent periods to retrieve

        Returns:
            list: Recent performance records
        """
        if len(self.performance_history) == 0:
            return []

        return self.performance_history[-periods:]

    def get_performance_summary(self):
        """
        Get summary statistics of model performance.

        Returns:
            dict: Summary with mean, std, min, max for each metric
        """
        if len(self.performance_history) == 0:
            return {
                'count': 0,
                'message': 'No performance data available'
            }

        f1_scores = [x['f1_score'] for x in self.performance_history]
        accuracies = [x['accuracy'] for x in self.performance_history]

        return {
            'count': len(self.performance_history),
            'f1_score': {
                'mean': np.mean(f1_scores),
                'std': np.std(f1_scores),
                'min': np.min(f1_scores),
                'max': np.max(f1_scores),
                'current': f1_scores[-1] if f1_scores else None
            },
            'accuracy': {
                'mean': np.mean(accuracies),
                'std': np.std(accuracies),
                'min': np.min(accuracies),
                'max': np.max(accuracies),
                'current': accuracies[-1] if accuracies else None
            },
            'trend': self._calculate_trend(),
            'alerts_count': len(self.alerts)
        }

    def _calculate_trend(self):
        """
        Calculate performance trend (improving/degrading/stable).

        Returns:
            str: 'IMPROVING', 'DEGRADING', or 'STABLE'
        """
        if len(self.performance_history) < 5:
            return 'INSUFFICIENT_DATA'

        recent_5 = [x['f1_score'] for x in self.performance_history[-5:]]

        # Simple linear regression
        x = np.arange(len(recent_5))
        coeffs = np.polyfit(x, recent_5, 1)
        slope = coeffs[0]

        if slope > 0.01:
            return 'IMPROVING'
        elif slope < -0.01:
            return 'DEGRADING'
        else:
            return 'STABLE'

    def get_alerts(self, recent_only=True, count=10):
        """
        Get performance alerts.

        Args:
            recent_only: Only return recent alerts
            count: Maximum number of alerts to return

        Returns:
            list: Alert records
        """
        if recent_only:
            return self.alerts[-count:]
        return self.alerts

    def clear_alerts(self):
        """Clear all alerts."""
        self.alerts = []

    def save_to_database(self):
        """
        Save performance history to database.

        Returns:
            tuple: (success, message)
        """
        try:
            from logic.db_manager import get_db_connection

            conn = get_db_connection()
            cursor = conn.cursor()

            # Save recent performance records
            for record in self.performance_history[-10:]:  # Save last 10 records
                cursor.execute("""
                    INSERT INTO model_performance_log
                    (log_date, model_version, f1_score, accuracy, training_type, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    record['date'],
                    record.get('model_version', 'V7.7'),
                    record['f1_score'],
                    record['accuracy'],
                    'evaluation',
                    f"Precision: {record['precision']:.4f}, Recall: {record['recall']:.4f}"
                ))

            conn.commit()
            conn.close()

            return True, f"Saved {len(self.performance_history[-10:])} performance records"

        except Exception as e:
            return False, f"Error saving to database: {e}"

    def load_from_database(self, days=30):
        """
        Load performance history from database.

        Args:
            days: Number of days to load (default: 30)

        Returns:
            tuple: (success, message)
        """
        try:
            from logic.db_manager import get_db_connection

            conn = get_db_connection()
            cursor = conn.cursor()

            # Load recent records
            cursor.execute("""
                SELECT log_date, model_version, f1_score, accuracy, notes
                FROM model_performance_log
                WHERE training_type = 'evaluation'
                AND log_date >= date('now', ?)
                ORDER BY log_date
            """, (f'-{days} days',))

            rows = cursor.fetchall()
            conn.close()

            # Convert to performance history format
            for row in rows:
                # Parse precision and recall from notes if available
                precision, recall = 0.0, 0.0
                if row[4]:  # notes
                    try:
                        parts = row[4].split(',')
                        precision = float(parts[0].split(':')[1].strip())
                        recall = float(parts[1].split(':')[1].strip())
                    except Exception:
                        pass

                record = {
                    'date': row[0],
                    'model_version': row[1],
                    'f1_score': row[2],
                    'accuracy': row[3],
                    'precision': precision,
                    'recall': recall,
                    'samples': 0,  # Not stored
                    'timestamp': datetime.now()
                }
                self.performance_history.append(record)

            return True, f"Loaded {len(rows)} performance records"

        except Exception as e:
            return False, f"Error loading from database: {e}"


# Singleton instance
_monitor_instance = None


def get_performance_monitor():
    """Get singleton instance of PerformanceMonitor."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor()
    return _monitor_instance
