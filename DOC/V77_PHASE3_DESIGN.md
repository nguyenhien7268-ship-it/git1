# V7.7 Phase 3 Design: Adaptive Learning & Meta-Learning

## Overview
Phase 3 implements intelligent decision-making and continuous learning capabilities to maintain and improve model performance over time.

## Goals
1. **Meta-Learner**: Automatically combine AI predictions with manual bridge scores
2. **Adaptive Retraining**: Keep model current with evolving lottery patterns
3. **Performance Monitoring**: Detect and respond to model degradation
4. **Decision Optimization**: Replace manual heuristics with learned strategies

## Architecture

### Component 1: Meta-Learner System

#### Purpose
Learn the optimal way to combine:
- AI probability scores (from XGBoost model)
- Manual bridge scores (Win Rate, Streak, K2N Risk)
- Confidence indicators
- Recent form factors

#### Implementation Strategy

**Option A: Logistic Regression Meta-Learner** (Recommended - Simple & Interpretable)
```python
# logic/meta_learner.py (NEW FILE)

from sklearn.linear_model import LogisticRegression
import numpy as np

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
            random_state=42
        )
        self.scaler = StandardScaler()
        
    def prepare_meta_features(self, ai_prob, manual_score, confidence, 
                               vote_count, recent_form_score):
        """
        Create meta-features from base predictions and scores.
        
        Returns: Array of 10+ meta-features
        """
        features = [
            ai_prob,                          # F1: AI probability
            manual_score,                     # F2: Manual score
            confidence,                       # F3: Confidence (1-7)
            vote_count,                       # F4: Total votes
            recent_form_score,                # F5: Recent form bonus
            ai_prob * manual_score,           # F6: Interaction term
            ai_prob * confidence,             # F7: AI * confidence
            manual_score * confidence,        # F8: Manual * confidence
            abs(ai_prob - manual_score/10),   # F9: Agreement metric
            min(ai_prob, manual_score/10)     # F10: Conservative score
        ]
        return np.array(features).reshape(1, -1)
    
    def train(self, historical_data):
        """
        Train meta-learner on historical decisions and outcomes.
        
        Args:
            historical_data: List of tuples (meta_features, actual_outcome)
        """
        X = []
        y = []
        
        for features, outcome in historical_data:
            X.append(features)
            y.append(outcome)  # 1 if loto appeared, 0 if not
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train
        self.model.fit(X_scaled, y)
        
        return self.model.score(X_scaled, y)
    
    def predict_final_decision(self, ai_prob, manual_score, confidence,
                                vote_count, recent_form_score):
        """
        Make final decision by combining all inputs.
        
        Returns:
            final_prob: Calibrated probability (0-100)
            decision: 'CHƠI', 'XEM XÉT', or 'BỎ QUA'
        """
        meta_features = self.prepare_meta_features(
            ai_prob, manual_score, confidence, vote_count, recent_form_score
        )
        meta_features_scaled = self.scaler.transform(meta_features)
        
        # Get probability from meta-learner
        final_prob = self.model.predict_proba(meta_features_scaled)[0, 1] * 100
        
        # Decision thresholds (can be learned or configured)
        if final_prob >= 65:
            decision = 'CHƠI'
        elif final_prob >= 40:
            decision = 'XEM XÉT'
        else:
            decision = 'BỎ QUA'
        
        return final_prob, decision
```

**Option B: Small Neural Network** (More Powerful but Complex)
- 2-3 hidden layers with 16-32 neurons each
- ReLU activation, dropout for regularization
- Binary cross-entropy loss
- Can capture more complex interactions

**Recommendation**: Start with Logistic Regression for interpretability and simplicity.

#### Training Data Collection
```python
# In logic/data_repository.py (EXTEND)

def collect_meta_learning_data(start_ky, end_ky):
    """
    Collect historical predictions and actual outcomes for meta-learning.
    
    Returns: List of training samples with:
        - AI prediction at time of decision
        - Manual scores at time of decision
        - Confidence/voting data
        - Actual outcome (did loto appear?)
    """
    # Query database for historical predictions
    # Match with actual results
    # Return aligned dataset
    pass
```

### Component 2: Adaptive Retraining System

#### Purpose
Automatically retrain models to adapt to changing lottery patterns without manual intervention.

#### Strategy

**Incremental Retraining** (Daily/Frequent)
```python
# logic/adaptive_trainer.py (NEW FILE)

class AdaptiveTrainer:
    """
    Manages automatic model retraining on rolling windows of data.
    """
    
    def __init__(self, config):
        self.rolling_window_size = config.get('ROLLING_WINDOW_SIZE', 400)
        self.min_retraining_gap = config.get('MIN_RETRAINING_GAP_DAYS', 7)
        self.f1_degradation_threshold = config.get('F1_DEGRADATION_THRESHOLD', 0.02)
        self.last_retrain_date = None
        self.baseline_f1_score = None
        
    def should_retrain_incremental(self, current_date, current_f1_score):
        """
        Decide if incremental retraining is needed.
        
        Triggers when:
        1. Enough days passed since last retrain
        2. F1 score degraded below threshold
        """
        # Check time gap
        if self.last_retrain_date:
            days_since_retrain = (current_date - self.last_retrain_date).days
            if days_since_retrain < self.min_retraining_gap:
                return False
        
        # Check performance degradation
        if self.baseline_f1_score and current_f1_score:
            degradation = self.baseline_f1_score - current_f1_score
            if degradation > self.f1_degradation_threshold:
                return True
        
        # Default: retrain weekly
        return self.last_retrain_date is None or days_since_retrain >= 7
    
    def incremental_retrain(self, all_data_ai):
        """
        Retrain on rolling window of recent data.
        
        Benefits:
        - Faster than full retrain
        - Focuses on recent patterns
        - Can run daily without heavy load
        """
        # Take last N periods
        recent_data = all_data_ai[-self.rolling_window_size:]
        
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
            
        return success, msg
    
    def should_retrain_full(self, current_date):
        """
        Decide if full retraining is needed.
        
        Triggers when:
        1. Monthly schedule
        2. Major performance drop
        3. Significant data accumulation
        """
        if self.last_full_retrain is None:
            return True
            
        days_since_full = (current_date - self.last_full_retrain).days
        return days_since_full >= 30  # Monthly full retrain
```

**Configuration Parameters**
```python
# In logic/config_manager.py (EXTEND)

class AppSettings:
    # ... existing settings ...
    
    # V7.7 Phase 3: Adaptive Learning
    ROLLING_WINDOW_SIZE = 400           # Periods for incremental training
    MIN_RETRAINING_GAP_DAYS = 7         # Minimum days between retrains
    F1_DEGRADATION_THRESHOLD = 0.02     # Trigger retrain if F1 drops 2%
    FULL_RETRAIN_INTERVAL_DAYS = 30     # Monthly full retrain
    ENABLE_AUTO_RETRAIN = True          # Master switch
```

#### Monitoring System
```python
# logic/performance_monitor.py (NEW FILE)

class PerformanceMonitor:
    """
    Track model performance over time and detect degradation.
    """
    
    def __init__(self):
        self.performance_history = []  # List of (date, f1_score, accuracy)
        
    def record_performance(self, date, predictions, actuals):
        """
        Calculate and record performance metrics.
        """
        from sklearn.metrics import f1_score, accuracy_score
        
        f1 = f1_score(actuals, predictions)
        acc = accuracy_score(actuals, predictions)
        
        self.performance_history.append({
            'date': date,
            'f1_score': f1,
            'accuracy': acc
        })
        
        # Alert if degradation detected
        if self._check_degradation():
            self._trigger_alert()
            
    def _check_degradation(self, lookback=7):
        """
        Check if recent performance is degrading.
        
        Uses moving average comparison.
        """
        if len(self.performance_history) < lookback * 2:
            return False
            
        recent = self.performance_history[-lookback:]
        previous = self.performance_history[-lookback*2:-lookback]
        
        recent_avg = np.mean([x['f1_score'] for x in recent])
        previous_avg = np.mean([x['f1_score'] for x in previous])
        
        return recent_avg < previous_avg - 0.02  # 2% drop
```

### Component 3: Integration with Existing System

#### Dashboard Integration
```python
# In logic/dashboard_analytics.py (EXTEND)

def get_final_recommendations_with_meta_learner(bridge_data, ai_predictions):
    """
    Enhanced version that uses meta-learner for final decisions.
    """
    from logic.meta_learner import MetaLearner
    
    meta_learner = MetaLearner()
    # Load trained meta-learner model
    meta_learner.load_model('logic/ml_model_files/meta_learner.joblib')
    
    final_recommendations = []
    
    for pair_data in bridge_data:
        ai_prob = get_ai_prob_for_pair(pair_data, ai_predictions)
        manual_score = pair_data['score']
        confidence = pair_data['confidence']
        vote_count = pair_data['total_votes']
        recent_form = pair_data['recent_form_bonus']
        
        # Use meta-learner for final decision
        final_prob, decision = meta_learner.predict_final_decision(
            ai_prob, manual_score, confidence, vote_count, recent_form
        )
        
        pair_data['meta_probability'] = final_prob
        pair_data['meta_decision'] = decision
        final_recommendations.append(pair_data)
    
    return final_recommendations
```

#### UI Settings for Phase 3
```python
# In ui/ui_settings.py (EXTEND)

def add_phase3_settings_tab(notebook):
    """
    Add new tab for Phase 3 adaptive learning settings.
    """
    phase3_frame = ttk.Frame(notebook)
    notebook.add(phase3_frame, text="🤖 Học Thích Ứng")
    
    # Meta-Learner settings
    ttk.Label(phase3_frame, text="Meta-Learner Settings").grid(row=0, column=0)
    # ... controls for meta-learner parameters
    
    # Adaptive Retraining settings
    ttk.Label(phase3_frame, text="Adaptive Retraining").grid(row=5, column=0)
    # ... controls for retraining schedule
    
    # Performance Monitoring
    ttk.Label(phase3_frame, text="Performance Monitoring").grid(row=10, column=0)
    # ... display current F1 score, trend, last retrain date
```

## Implementation Plan

### Step 1: Data Collection (Week 1)
- [ ] Implement meta-learning data collection
- [ ] Store historical predictions with outcomes
- [ ] Build training dataset (need 100+ periods minimum)

### Step 2: Meta-Learner Development (Week 1-2)
- [ ] Create `logic/meta_learner.py`
- [ ] Implement Logistic Regression version
- [ ] Train on historical data
- [ ] Validate performance vs current heuristics

### Step 3: Adaptive Trainer (Week 2)
- [ ] Create `logic/adaptive_trainer.py`
- [ ] Implement incremental retraining
- [ ] Add scheduling logic
- [ ] Test on historical data

### Step 4: Performance Monitoring (Week 2)
- [ ] Create `logic/performance_monitor.py`
- [ ] Track F1 scores over time
- [ ] Implement degradation detection
- [ ] Add alerting mechanism

### Step 5: Integration (Week 3)
- [ ] Integrate meta-learner with dashboard
- [ ] Add UI controls for Phase 3 settings
- [ ] Update documentation
- [ ] Create migration guide

### Step 6: Testing & Validation (Week 3-4)
- [ ] Unit tests for all new components
- [ ] Integration tests
- [ ] Backtest on historical data
- [ ] A/B comparison with Phase 2 system

## Success Metrics

### Meta-Learner Performance
- **Target**: 3-5% improvement in F1 score over manual heuristics
- **Metric**: Cross-validated F1 on held-out test set

### Adaptive Retraining Effectiveness
- **Target**: Maintain F1 score within 2% of peak performance
- **Metric**: Rolling 30-day F1 score stability

### System Efficiency
- **Target**: Incremental retrain completes in <5 minutes
- **Target**: Full retrain completes in <30 minutes

## Risks and Mitigations

### Risk 1: Meta-Learner Overfitting
**Mitigation**: 
- Use regularization (L2 penalty)
- Cross-validation during training
- Monitor test set performance

### Risk 2: Adaptive Retraining Instability
**Mitigation**:
- Gradual rollout with manual override
- Keep backup of previous model version
- Require minimum performance threshold

### Risk 3: Increased Complexity
**Mitigation**:
- Comprehensive documentation
- Clear UI for enabling/disabling features
- Fallback to Phase 2 behavior if issues

## Future Enhancements (Post-Phase 3)

1. **Ensemble Methods**: Combine multiple models
2. **Reinforcement Learning**: Optimize decision strategy
3. **Online Learning**: Update model continuously without full retrain
4. **Feature Selection**: Automatically select most important features
5. **Hyperparameter Auto-Tuning**: Continuous optimization

## References

- Phase 2 Implementation: `V77_PHASE2_IMPLEMENTATION.md`
- Existing ML Model: `logic/ml_model.py`
- Dashboard Analytics: `logic/dashboard_analytics.py`
- Configuration: `logic/config_manager.py`
