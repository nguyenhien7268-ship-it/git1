# logic/phase3_data_collector.py
"""
V7.7 Phase 3 Data Collection Module

This module collects prediction data alongside actual outcomes to train
the Meta-Learner in Phase 3. It automatically logs:
- AI probability predictions
- Manual scores (from bridge analysis)
- Confidence levels
- Vote counts
- Actual outcomes

After collecting 100+ periods, this data will be used to train the Meta-Learner.
"""

from datetime import datetime
import traceback


class Phase3DataCollector:
    """
    Collects prediction data for Phase 3 Meta-Learner training.
    
    Usage:
        collector = Phase3DataCollector()
        collector.log_prediction(ky, loto, ai_prob, manual_score, confidence, votes)
        collector.log_outcome(ky, loto, actual_outcome)
    """
    
    def __init__(self):
        self.db_conn = None
    
    def _get_connection(self):
        """Get database connection."""
        if self.db_conn is None:
            from logic.db_manager import get_db_connection
            self.db_conn = get_db_connection()
        return self.db_conn
    
    def log_prediction(self, ky, loto, ai_probability, manual_score,
                       confidence, vote_count, recent_form_score=0.0):
        """
        Log a prediction for a specific ky and loto.
        
        Args:
            ky: Period identifier (e.g., '20001')
            loto: Loto number (e.g., '00', '01', ...)
            ai_probability: AI model probability (0-100)
            manual_score: Manual bridge score (0-10)
            confidence: Confidence level (1-7)
            vote_count: Total number of votes
            recent_form_score: Recent form bonus score
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Insert or update prediction data
            cursor.execute("""
                INSERT OR REPLACE INTO meta_learning_history
                (ky, loto, ai_probability, manual_score, confidence,
                 vote_count, recent_form_score, actual_outcome, decision_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?)
            """, (
                str(ky),
                str(loto),
                float(ai_probability),
                float(manual_score),
                int(confidence),
                int(vote_count),
                float(recent_form_score),
                datetime.now()
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error logging prediction for {ky}/{loto}: {e}")
            traceback.print_exc()
            return False
    
    def log_outcome(self, ky, loto, actual_outcome):
        """
        Log the actual outcome for a specific ky and loto.
        
        Args:
            ky: Period identifier
            loto: Loto number
            actual_outcome: 1 if loto appeared, 0 if not
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Update the actual outcome
            cursor.execute("""
                UPDATE meta_learning_history
                SET actual_outcome = ?
                WHERE ky = ? AND loto = ?
            """, (int(actual_outcome), str(ky), str(loto)))
            
            conn.commit()
            
            if cursor.rowcount == 0:
                print(f"Warning: No prediction found for {ky}/{loto} to update outcome")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error logging outcome for {ky}/{loto}: {e}")
            traceback.print_exc()
            return False
    
    def log_batch_predictions(self, ky, predictions_list):
        """
        Log a batch of predictions for a specific ky.
        
        Args:
            ky: Period identifier
            predictions_list: List of dicts with keys:
                - loto
                - ai_probability
                - manual_score
                - confidence
                - vote_count
                - recent_form_score (optional)
        
        Returns:
            tuple: (success_count, total_count)
        """
        success_count = 0
        total_count = len(predictions_list)
        
        for pred in predictions_list:
            result = self.log_prediction(
                ky=ky,
                loto=pred['loto'],
                ai_probability=pred.get('ai_probability', 0.0),
                manual_score=pred.get('manual_score', 0.0),
                confidence=pred.get('confidence', 0),
                vote_count=pred.get('vote_count', 0),
                recent_form_score=pred.get('recent_form_score', 0.0)
            )
            if result:
                success_count += 1
        
        return success_count, total_count
    
    def log_batch_outcomes(self, ky, lotos_appeared):
        """
        Log actual outcomes for a specific ky.
        
        Args:
            ky: Period identifier
            lotos_appeared: List or set of lotos that appeared (e.g., ['00', '15', '27'])
        
        Returns:
            int: Number of outcomes logged
        """
        lotos_appeared_set = set(lotos_appeared)
        count = 0
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all predictions for this ky
            cursor.execute("""
                SELECT loto FROM meta_learning_history
                WHERE ky = ? AND actual_outcome IS NULL
            """, (str(ky),))
            
            predicted_lotos = [row[0] for row in cursor.fetchall()]
            
            # Update all outcomes
            for loto in predicted_lotos:
                outcome = 1 if loto in lotos_appeared_set else 0
                if self.log_outcome(ky, loto, outcome):
                    count += 1
            
            return count
            
        except Exception as e:
            print(f"Error logging batch outcomes for {ky}: {e}")
            traceback.print_exc()
            return count
    
    def get_collection_stats(self):
        """
        Get statistics about collected data.
        
        Returns:
            dict: Statistics including:
                - total_predictions: Total predictions logged
                - predictions_with_outcomes: Predictions with known outcomes
                - unique_periods: Number of unique periods
                - oldest_period: Oldest period with data
                - newest_period: Newest period with data
                - ready_for_training: Whether we have enough data (100+ periods)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total predictions
            cursor.execute("SELECT COUNT(*) FROM meta_learning_history")
            total_predictions = cursor.fetchone()[0]
            
            # Predictions with outcomes
            cursor.execute("""
                SELECT COUNT(*) FROM meta_learning_history
                WHERE actual_outcome IS NOT NULL
            """)
            predictions_with_outcomes = cursor.fetchone()[0]
            
            # Unique periods
            cursor.execute("""
                SELECT COUNT(DISTINCT ky) FROM meta_learning_history
                WHERE actual_outcome IS NOT NULL
            """)
            unique_periods = cursor.fetchone()[0]
            
            # Oldest and newest periods
            cursor.execute("""
                SELECT MIN(ky), MAX(ky) FROM meta_learning_history
                WHERE actual_outcome IS NOT NULL
            """)
            oldest, newest = cursor.fetchone()
            
            return {
                'total_predictions': total_predictions,
                'predictions_with_outcomes': predictions_with_outcomes,
                'unique_periods': unique_periods,
                'oldest_period': oldest,
                'newest_period': newest,
                'ready_for_training': unique_periods >= 100,
                'progress_percentage': min(100, (unique_periods / 100) * 100) if unique_periods else 0
            }
            
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            traceback.print_exc()
            return {
                'total_predictions': 0,
                'predictions_with_outcomes': 0,
                'unique_periods': 0,
                'oldest_period': None,
                'newest_period': None,
                'ready_for_training': False,
                'progress_percentage': 0
            }
    
    def close(self):
        """Close database connection."""
        if self.db_conn:
            self.db_conn.close()
            self.db_conn = None


# Convenience functions for easy integration

_collector_instance = None


def get_collector():
    """Get singleton instance of Phase3DataCollector."""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = Phase3DataCollector()
    return _collector_instance


def log_prediction(ky, loto, ai_probability, manual_score, confidence, vote_count, recent_form_score=0.0):
    """
    Convenience function to log a prediction.
    See Phase3DataCollector.log_prediction() for details.
    """
    collector = get_collector()
    return collector.log_prediction(ky, loto, ai_probability, manual_score,
                                    confidence, vote_count, recent_form_score)


def log_outcome(ky, loto, actual_outcome):
    """
    Convenience function to log an outcome.
    See Phase3DataCollector.log_outcome() for details.
    """
    collector = get_collector()
    return collector.log_outcome(ky, loto, actual_outcome)


def get_stats():
    """
    Convenience function to get collection statistics.
    See Phase3DataCollector.get_collection_stats() for details.
    """
    collector = get_collector()
    return collector.get_stats()
