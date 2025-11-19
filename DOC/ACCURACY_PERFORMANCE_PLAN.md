# Kế Hoạch Nâng Cao Độ Chính Xác Dự Đoán & Hiệu Suất Hệ Thống

## Mục Tiêu Chính

**Focus:** Nâng cao độ chính xác dự đoán AI và tối ưu hiệu suất hệ thống cho dự án cá nhân.

## Phase 1: AI Accuracy Improvements (Ưu Tiên Cao)

### 1.1. Enhanced Q-Features (Quality Features)

**Hiện tại:** 3 Q-Features đã implement
- `q_avg_win_rate`: Tỷ lệ thắng trung bình
- `q_min_k2n_risk`: Risk score tối thiểu
- `q_max_curr_streak`: Streak hiện tại tối đa

**Mới:** 5+ Advanced Q-Features

#### 1.1.1. q_std_win_rate (Standard Deviation)
```python
# Đo độ biến động của win rate
q_std_win_rate = np.std(win_rates) if win_rates else 0.0
```
**Lợi ích:** Phát hiện bridges ổn định vs không ổn định

#### 1.1.2. q_bridge_diversity (Số lượng bridge types khác nhau)
```python
# Đếm số loại bridge khác nhau vote cho loto này
unique_bridge_types = len(set(bridge_types))
```
**Lợi ích:** Consensus cao từ nhiều nguồn khác nhau = tin cậy hơn

#### 1.1.3. q_consensus_strength (Mức độ đồng thuận)
```python
# % bridge vote cho cùng 1 prediction
most_common_count = Counter(predictions).most_common(1)[0][1]
consensus = most_common_count / total_bridges if total_bridges > 0 else 0
```
**Lợi ích:** Prediction được nhiều bridges đồng ý = chính xác hơn

#### 1.1.4. q_recent_performance (Performance gần đây)
```python
# Win rate trong 7 ngày gần nhất
recent_win_rate = calculate_win_rate_last_n_days(bridge, n=7)
```
**Lợi ích:** Bridges đang "hot" gần đây có thể chính xác hơn

#### 1.1.5. q_pattern_stability (Độ ổn định pattern)
```python
# Coefficient of variation của win rate over time
pattern_stability = mean_win_rate / std_win_rate if std > 0 else 0
```
**Lợi ích:** Patterns ổn định = dự đoán đáng tin cậy hơn

### 1.2. XGBoost Hyperparameter Optimization

**Current Parameters:**
```python
'max_depth': 6,
'n_estimators': 100,
'learning_rate': 0.1,
'objective': 'multi:softprob'
```

**Optimization Strategy: GridSearchCV**

```python
param_grid = {
    'max_depth': [4, 6, 8, 10],
    'n_estimators': [100, 200, 300],
    'learning_rate': [0.05, 0.1, 0.15],
    'subsample': [0.8, 0.9, 1.0],
    'colsample_bytree': [0.8, 0.9, 1.0],
    'min_child_weight': [1, 3, 5]
}

grid_search = GridSearchCV(
    xgb.XGBClassifier(),
    param_grid,
    cv=5,
    scoring='f1_weighted',
    n_jobs=-1
)
```

**Expected Impact:** +5-10% accuracy improvement

### 1.3. Feature Engineering Improvements

#### 1.3.1. Temporal Features
```python
# Ngày trong tuần, tuần trong tháng
day_of_week = datetime.weekday()
week_of_month = (datetime.day - 1) // 7 + 1
is_weekend = day_of_week in [5, 6]
```

#### 1.3.2. Rolling Statistics
```python
# Moving averages
win_rate_7d_ma = rolling_avg(win_rates, window=7)
win_rate_14d_ma = rolling_avg(win_rates, window=14)
# Momentum
win_rate_momentum = win_rate_7d_ma - win_rate_14d_ma
```

#### 1.3.3. Interaction Features
```python
# Tương tác giữa các bridge types
classic_x_v17 = f_classic_votes * f_v17_votes
classic_x_memory = f_classic_votes * f_memory_votes
```

#### 1.3.4. Lag Features
```python
# Kết quả 3 ngày trước
loto_appeared_1d_ago = check_loto_in_prev_day(loto, offset=1)
loto_appeared_2d_ago = check_loto_in_prev_day(loto, offset=2)
loto_appeared_3d_ago = check_loto_in_prev_day(loto, offset=3)
```

### 1.4. Ensemble Methods

#### 1.4.1. Stacking Multiple Models
```python
# XGBoost + LightGBM + CatBoost
base_models = [
    ('xgb', XGBClassifier(**params_xgb)),
    ('lgbm', LGBMClassifier(**params_lgbm)),
    ('cat', CatBoostClassifier(**params_cat))
]
meta_model = LogisticRegression()
stacking = StackingClassifier(estimators=base_models, final_estimator=meta_model)
```

**Expected Impact:** +3-5% accuracy improvement

#### 1.4.2. Weighted Voting
```python
voting = VotingClassifier(
    estimators=base_models,
    voting='soft',
    weights=[0.5, 0.3, 0.2]  # XGBoost highest weight
)
```

## Phase 2: Performance Optimization

### 2.1. Database Query Optimization

#### 2.1.1. Query Result Caching
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_managed_bridges_cached():
    return get_all_managed_bridges(DB_NAME, only_enabled=True)
```

#### 2.1.2. Batch Queries
```python
# Thay vì N queries, dùng 1 query với IN clause
loto_ids = [1, 2, 3, ..., 100]
results = cursor.execute(
    "SELECT * FROM table WHERE loto_id IN ({})".format(','.join('?'*len(loto_ids))),
    loto_ids
)
```

**Expected Impact:** 50-70% query time reduction

### 2.2. Computation Caching

#### 2.2.1. Cache Bridge Predictions
```python
bridge_predictions_cache = {}

def get_bridge_predictions_cached(prev_row):
    key = hash(str(prev_row))
    if key not in bridge_predictions_cache:
        bridge_predictions_cache[key] = calculate_bridge_predictions(prev_row)
    return bridge_predictions_cache[key]
```

#### 2.2.2. Memoization
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def taoSTL_V30_Bong_cached(a, b):
    return taoSTL_V30_Bong(a, b)
```

**Expected Impact:** 30-50% computation time reduction

### 2.3. Vectorization

#### 2.3.1. NumPy Vectorization
```python
# Thay vì Python loop
for i in range(len(data)):
    result[i] = calculate(data[i])

# Dùng NumPy vectorization
result = np.vectorize(calculate)(data)
```

#### 2.3.2. Pandas Operations
```python
# Thay vì iterrows()
for idx, row in df.iterrows():
    df.at[idx, 'result'] = calculate(row['value'])

# Dùng apply()
df['result'] = df['value'].apply(calculate)
```

**Expected Impact:** 2-5x faster calculations

### 2.4. Memory Optimization

#### 2.4.1. Generator Expressions
```python
# Thay vì list (load tất cả vào memory)
large_list = [process(x) for x in huge_dataset]

# Dùng generator (lazy loading)
large_gen = (process(x) for x in huge_dataset)
```

#### 2.4.2. Data Chunking
```python
chunk_size = 1000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    process_chunk(chunk)
```

**Expected Impact:** -30-50% memory usage

## Phase 3: Model Validation & Monitoring

### 3.1. Cross-Validation

#### 3.1.1. K-Fold CV
```python
from sklearn.model_selection import cross_val_score

scores = cross_val_score(model, X, y, cv=5, scoring='f1_weighted')
print(f"CV F1 Score: {scores.mean():.3f} (+/- {scores.std():.3f})")
```

#### 3.1.2. Time-Series Split
```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    # Train and validate
```

### 3.2. Performance Metrics

#### 3.2.1. Core Metrics
```python
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred, average='weighted')
recall = recall_score(y_true, y_pred, average='weighted')
f1 = f1_score(y_true, y_pred, average='weighted')
```

#### 3.2.2. Top-K Accuracy
```python
def top_k_accuracy(y_true, y_pred_proba, k=10):
    """Tính Top-K accuracy (có bao nhiêu prediction đúng trong Top-K)"""
    top_k_preds = np.argsort(y_pred_proba, axis=1)[:, -k:]
    correct = sum(y_true[i] in top_k_preds[i] for i in range(len(y_true)))
    return correct / len(y_true)
```

#### 3.2.3. Hit Rate
```python
def hit_rate(predictions, actual_results, top_n=15):
    """Tỷ lệ trúng trong Top-N predictions"""
    top_n_preds = predictions[:top_n]
    hits = sum(1 for pred in top_n_preds if pred in actual_results)
    return hits / len(actual_results) if actual_results else 0
```

### 3.3. Monitoring Dashboard

#### 3.3.1. Real-time Tracking
- Track accuracy per day
- Monitor prediction confidence
- Log failed predictions

#### 3.3.2. Model Drift Detection
```python
# Compare recent performance vs training performance
recent_accuracy = calculate_accuracy_last_n_days(n=30)
if recent_accuracy < training_accuracy - 0.10:
    trigger_retrain_alert()
```

## Implementation Timeline

### Week 4: AI Accuracy Improvements
- **Day 1:** ✅ Create plan & setup
- **Day 2:** Implement 5 new Q-Features
- **Day 3:** XGBoost hyperparameter optimization
- **Day 4:** Feature engineering (temporal, rolling, interaction)
- **Day 5:** Validation & accuracy measurement

### Week 5: Performance Optimization
- **Day 1-2:** Database caching & batch queries
- **Day 3:** Vectorization of calculations
- **Day 4:** Memory optimization
- **Day 5:** Performance benchmarking

### Week 6: Ensemble & Validation
- **Day 1-2:** Ensemble methods implementation
- **Day 3-4:** Model validation & cross-validation
- **Day 5:** Final accuracy & performance report

## Success Criteria

### Accuracy Goals
- **Baseline:** TBD (measure first)
- **Target Top-10 accuracy:** > 60%
- **F1-score:** > 0.70
- **ROC-AUC:** > 0.80

### Performance Goals
- **Prediction time:** < 50ms
- **Training time:** < 5 minutes (with caching)
- **Memory usage:** < 500MB
- **Database queries:** < 5ms (currently < 10ms)

### Code Quality
- All tests passing ✅
- No performance regressions ✅
- Backward compatibility maintained ✅
- 0 security vulnerabilities ✅

## Monitoring & Reporting

### Daily Metrics
- Prediction accuracy
- False positive rate
- False negative rate
- Model confidence scores

### Weekly Reports
- Accuracy trends
- Performance benchmarks
- Model improvements
- Next actions

## Notes

- Dự án cá nhân nên focus vào practical improvements
- Không cần documentation quá chi tiết
- Priority: Accuracy > Performance > Documentation
- Measure baseline trước khi optimize
