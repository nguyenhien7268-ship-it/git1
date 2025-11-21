# logic/meta_learner.py
"""
V7.7 Phase 3 Meta-Learner Implementation

This module implements a second-level AI (Meta-Learner) that learns to optimally
combine XGBoost predictions with manual bridge scores to make final decisions.

The Meta-Learner uses Logistic Regression to balance:
- AI probability scores
- Manual bridge scores
- Confidence indicators
- Vote counts
- Recent form factors

After training on 100+ periods of historical data, it can make better decisions
than either AI or manual scoring alone.
"""

import os
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

# Model file paths
META_MODEL_PATH = "logic/ml_model_files/meta_learner.joblib"
META_SCALER_PATH = "logic/ml_model_files/meta_scaler.joblib"


class MetaLearner:
    """
    Second-level AI that learns to combine XGBoost predictions
    with manual scoring to make final decisions.
    """

    def __init__(self):
        self.model = LogisticRegression(
            penalty='l2',
            C=1.0,
            class_weight='balanced',
            random_state=42,
            max_iter=1000
        )
        self.scaler = StandardScaler()
        self.is_trained = False

    def prepare_meta_features(self, ai_prob, manual_score, confidence,
                              vote_count, recent_form_score):
        """
        Create meta-features from base predictions and scores.

        Args:
            ai_prob: AI probability (0-100)
            manual_score: Manual bridge score (0-10)
            confidence: Confidence level (1-7)
            vote_count: Total number of votes
            recent_form_score: Recent form bonus score

        Returns:
            Array of 10 meta-features
        """
        features = [
            ai_prob / 100.0,                           # F1: AI probability (normalized)
            manual_score / 10.0,                       # F2: Manual score (normalized)
            confidence / 7.0,                          # F3: Confidence (normalized)
            min(vote_count / 10.0, 1.0),              # F4: Vote count (capped)
            recent_form_score / 5.0,                   # F5: Recent form (normalized)
            (ai_prob / 100.0) * (manual_score / 10.0), # F6: AI × Manual interaction
            (ai_prob / 100.0) * (confidence / 7.0),    # F7: AI × Confidence
            (manual_score / 10.0) * (confidence / 7.0),# F8: Manual × Confidence
            abs((ai_prob / 100.0) - (manual_score / 10.0)),  # F9: Agreement metric
            min(ai_prob / 100.0, manual_score / 10.0)  # F10: Conservative score
        ]
        return np.array(features).reshape(1, -1)

    def train(self, historical_data):
        """
        Train meta-learner on historical decisions and outcomes.

        Args:
            historical_data: List of dicts with keys:
                - ai_probability: AI prediction (0-100)
                - manual_score: Manual score (0-10)
                - confidence: Confidence level (1-7)
                - vote_count: Number of votes
                - recent_form_score: Recent form bonus
                - actual_outcome: 1 if loto appeared, 0 if not

        Returns:
            tuple: (success, message, metrics_dict)
        """
        if len(historical_data) < 100:
            return False, f"Insufficient data: {len(historical_data)} samples (need 100+)", {}

        try:
            X = []
            y = []

            for record in historical_data:
                features = self.prepare_meta_features(
                    ai_prob=record.get('ai_probability', 0.0),
                    manual_score=record.get('manual_score', 0.0),
                    confidence=record.get('confidence', 0),
                    vote_count=record.get('vote_count', 0),
                    recent_form_score=record.get('recent_form_score', 0.0)
                )
                X.append(features[0])
                y.append(record['actual_outcome'])

            X = np.array(X)
            y = np.array(y)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.model.fit(X_scaled, y)
            self.is_trained = True

            # Calculate cross-validation scores
            cv_scores = cross_val_score(self.model, X_scaled, y, cv=5, scoring='f1')
            training_score = self.model.score(X_scaled, y)

            metrics = {
                'training_accuracy': training_score,
                'cv_f1_mean': cv_scores.mean(),
                'cv_f1_std': cv_scores.std(),
                'samples_used': len(historical_data)
            }

            message = (f"Meta-Learner trained successfully!\n"
                       f"Training Accuracy: {training_score * 100:.2f}%\n"
                       f"CV F1-Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})\n"
                       f"Samples: {len(historical_data)}")

            return True, message, metrics

        except Exception as e:
            return False, f"Error training Meta-Learner: {e}", {}

    def predict_final_decision(self, ai_prob, manual_score, confidence,
                               vote_count, recent_form_score,
                               thresholds=None):
        """
        Make final decision by combining all inputs through the Meta-Learner.

        Args:
            ai_prob: AI probability (0-100)
            manual_score: Manual score (0-10)
            confidence: Confidence level (1-7)
            vote_count: Number of votes
            recent_form_score: Recent form bonus
            thresholds: Optional dict with 'CHOI' and 'XEM_XET' thresholds

        Returns:
            tuple: (final_probability, decision_label)
                - final_probability: Calibrated probability (0-100)
                - decision_label: 'CHƠI', 'XEM XÉT', or 'BỎ QUA'
        """
        if not self.is_trained:
            # Fallback to simple heuristic if not trained
            combined = (ai_prob + manual_score * 10) / 2
            if combined >= 70:
                return combined, 'CHƠI'
            elif combined >= 50:
                return combined, 'XEM XÉT'
            else:
                return combined, 'BỎ QUA'

        try:
            # Prepare meta-features
            meta_features = self.prepare_meta_features(
                ai_prob, manual_score, confidence, vote_count, recent_form_score
            )

            # Scale features
            meta_features_scaled = self.scaler.transform(meta_features)

            # Get probability from meta-learner
            final_prob = self.model.predict_proba(meta_features_scaled)[0, 1] * 100

            # Apply thresholds
            if thresholds is None:
                thresholds = {'CHOI': 65, 'XEM_XET': 40}

            if final_prob >= thresholds.get('CHOI', 65):
                decision = 'CHƠI'
            elif final_prob >= thresholds.get('XEM_XET', 40):
                decision = 'XEM XÉT'
            else:
                decision = 'BỎ QUA'

            return final_prob, decision

        except Exception as e:
            print(f"Error in Meta-Learner prediction: {e}")
            # Fallback
            combined = (ai_prob + manual_score * 10) / 2
            if combined >= 70:
                return combined, 'CHƠI'
            elif combined >= 50:
                return combined, 'XEM XÉT'
            else:
                return combined, 'BỎ QUA'

    def save(self, model_path=None, scaler_path=None):
        """Save trained Meta-Learner and scaler to disk."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained Meta-Learner")

        model_path = model_path or META_MODEL_PATH
        scaler_path = scaler_path or META_SCALER_PATH

        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)

        return model_path, scaler_path

    def load(self, model_path=None, scaler_path=None):
        """Load trained Meta-Learner and scaler from disk."""
        model_path = model_path or META_MODEL_PATH
        scaler_path = scaler_path or META_SCALER_PATH

        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            raise FileNotFoundError("Meta-Learner model files not found")

        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.is_trained = True

        return True

    def get_feature_importance(self):
        """
        Get feature importance/coefficients from the trained model.

        Returns:
            dict: Feature names mapped to their coefficients
        """
        if not self.is_trained:
            return {}

        feature_names = [
            'AI_Probability',
            'Manual_Score',
            'Confidence',
            'Vote_Count',
            'Recent_Form',
            'AI_x_Manual',
            'AI_x_Confidence',
            'Manual_x_Confidence',
            'Agreement_Metric',
            'Conservative_Score'
        ]

        coefficients = self.model.coef_[0]
        return dict(zip(feature_names, coefficients))


def train_meta_learner_from_db():
    """
    Convenience function to train Meta-Learner from collected database data.

    Returns:
        tuple: (success, message, meta_learner_instance)
    """
    try:
        from logic.db_manager import get_db_connection

        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch all complete records
        cursor.execute("""
            SELECT ai_probability, manual_score, confidence,
                   vote_count, recent_form_score, actual_outcome
            FROM meta_learning_history
            WHERE actual_outcome IS NOT NULL
        """)

        rows = cursor.fetchall()
        conn.close()

        if len(rows) < 100:
            return False, f"Insufficient data: {len(rows)} records (need 100+)", None

        # Convert to list of dicts
        historical_data = []
        for row in rows:
            historical_data.append({
                'ai_probability': row[0] or 0.0,
                'manual_score': row[1] or 0.0,
                'confidence': row[2] or 0,
                'vote_count': row[3] or 0,
                'recent_form_score': row[4] or 0.0,
                'actual_outcome': row[5]
            })

        # Train Meta-Learner
        meta_learner = MetaLearner()
        success, message, metrics = meta_learner.train(historical_data)

        if success:
            # Save the trained model
            meta_learner.save()
            message += f"\n\nModel saved to:\n  - {META_MODEL_PATH}\n  - {META_SCALER_PATH}"

        return success, message, meta_learner

    except Exception as e:
        return False, f"Error training Meta-Learner from database: {e}", None


def load_meta_learner():
    """
    Convenience function to load a trained Meta-Learner.

    Returns:
        MetaLearner instance or None if not found
    """
    try:
        meta_learner = MetaLearner()
        meta_learner.load()
        return meta_learner
    except Exception as e:
        print(f"Could not load Meta-Learner: {e}")
        return None
