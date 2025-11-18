# Kế Hoạch Hành Động Nâng Cấp Hệ Thống (V7.3 → V8.0)

## 📋 Executive Summary

Dựa trên đánh giá toàn diện trong file `SYSTEM_EVALUATION.md`, đây là kế hoạch hành động cụ thể để nâng cấp hệ thống từ V7.3 lên V8.0.

**Thời gian dự kiến:** 2-3 tháng  
**Độ ưu tiên:** Cao → Trung bình → Thấp  
**Mục tiêu chính:** Tăng stability, performance, và chuẩn bị cho scale

---

## 🎯 Week 1-2: Quick Wins (Cải thiện nhanh)

### ✅ Task 1: Setup Testing Infrastructure
**Thời gian:** 5 ngày  
**Người thực hiện:** Dev Team  
**Độ ưu tiên:** 🔴 Cao

**Chi tiết:**
```bash
# 1. Setup pytest với coverage
pip install pytest pytest-cov pytest-mock

# 2. Tạo cấu trúc test
mkdir -p tests/{unit,integration}
touch tests/unit/test_ml_model.py
touch tests/unit/test_backtester.py
touch tests/unit/test_ai_feature_extractor.py
touch tests/integration/test_mvp_flow.py

# 3. Viết test cho 5 modules quan trọng nhất
# - logic/ml_model.py
# - logic/backtester.py
# - logic/ai_feature_extractor.py
# - logic/dashboard_analytics.py
# - logic/data_repository.py

# 4. Target: 50% coverage trong tuần đầu, 70% cuối tuần 2
pytest --cov=logic --cov-report=html
```

**Checklist:**
- [ ] Setup pytest và pytest-cov
- [ ] Tạo test fixtures cho data mẫu
- [ ] Viết 20+ unit tests cho ml_model.py
- [ ] Viết 15+ unit tests cho backtester.py
- [ ] Viết 10+ unit tests cho ai_feature_extractor.py
- [ ] Viết 5+ integration tests cho MVP flow
- [ ] Đạt 70% code coverage
- [ ] Setup GitHub Actions để run tests tự động

**Deliverables:**
- [ ] `tests/` folder với 50+ tests
- [ ] Coverage report > 70%
- [ ] CI pipeline running tests

---

### ✅ Task 2: Implement Caching
**Thời gian:** 3 ngày  
**Người thực hiện:** Backend Dev  
**Độ ưu tiên:** 🔴 Cao

**Chi tiết:**
```python
# 1. Thêm caching cho các hàm pure
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_loto_stats_last_n_days(data_tuple, days):
    # Convert list to tuple để có thể cache
    # Implement logic
    pass

# 2. Cache daily_bridge_predictions
import pickle
import os
from datetime import datetime

CACHE_DIR = "cache/"
CACHE_FILE = f"{CACHE_DIR}daily_predictions_{datetime.now().date()}.pkl"

def get_daily_predictions_with_cache(all_data_ai):
    # Check cache
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            return pickle.load(f)
    
    # Compute
    result = _get_daily_bridge_predictions(all_data_ai)
    
    # Save cache
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(result, f)
    
    return result

# 3. Cache AI predictions
@lru_cache(maxsize=100)
def get_ai_predictions_cached(data_hash, model_version):
    # Implement logic
    pass
```

**Checklist:**
- [ ] Add `@lru_cache` cho các hàm pure trong `dashboard_analytics.py`
- [ ] Implement disk cache cho `daily_bridge_predictions`
- [ ] Cache AI predictions với TTL = 1 ngày
- [ ] Thêm cache invalidation logic
- [ ] Benchmark performance (trước và sau)

**Deliverables:**
- [ ] Cache implementation trong `logic/cache_manager.py`
- [ ] Performance improvement > 30%
- [ ] Documentation về caching strategy

---

### ✅ Task 3: Code Quality Tools
**Thời gian:** 2 ngày  
**Người thực hiện:** All Devs  
**Độ ưu tiên:** 🟡 Trung bình

**Chi tiết:**
```bash
# 1. Install tools
pip install black flake8 isort mypy

# 2. Create config files
# .flake8
cat > .flake8 << 'EOF'
[flake8]
max-line-length = 100
exclude = .git,__pycache__,build,dist
ignore = E203,W503
EOF

# pyproject.toml
cat > pyproject.toml << 'EOF'
[tool.black]
line-length = 100
target-version = ['py312']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
EOF

# 3. Run formatters
black .
isort .
flake8 .

# 4. Add pre-commit hooks
pip install pre-commit
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
EOF
pre-commit install
```

**Checklist:**
- [ ] Setup black, flake8, isort
- [ ] Format tất cả files
- [ ] Fix tất cả flake8 warnings
- [ ] Setup pre-commit hooks
- [ ] Update CI để check formatting

**Deliverables:**
- [ ] All code formatted với black
- [ ] Zero flake8 warnings
- [ ] Pre-commit hooks working

---

### ✅ Task 4: Add Type Hints & Docstrings
**Thời gian:** 3 ngày  
**Người thực hiện:** All Devs  
**Độ ưu tiên:** 🟡 Trung bình

**Chi tiết:**
```python
# Example: Thêm type hints và docstrings
from typing import List, Dict, Tuple, Optional
import numpy as np

def prepare_training_data(
    all_data_ai: List[List[Any]], 
    daily_bridge_predictions: Dict[str, Dict[str, Dict[str, float]]]
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Chuẩn bị dữ liệu huấn luyện cho mô hình AI XGBoost.
    
    Args:
        all_data_ai: Danh sách dữ liệu A:I từ database, mỗi phần tử là list 10 cột
                     [MaSoKy, Col_A_Ky, Col_B_GDB, ..., Col_I_G7]
        daily_bridge_predictions: Dictionary chứa dự đoán cầu cho mỗi ngày
                                  Format: {ky: {loto: {feature_name: value}}}
    
    Returns:
        Tuple[X, y] nếu thành công, (None, None) nếu thất bại
        - X: Features matrix (n_samples, n_features)
        - y: Labels array (n_samples,)
    
    Raises:
        ValueError: Nếu all_data_ai có ít hơn MIN_DATA_TO_TRAIN samples
    
    Example:
        >>> X, y = prepare_training_data(data, predictions)
        >>> if X is not None:
        ...     model.fit(X, y)
    """
    if not all_data_ai or len(all_data_ai) < MIN_DATA_TO_TRAIN:
        raise ValueError(f"Cần tối thiểu {MIN_DATA_TO_TRAIN} kỳ để huấn luyện AI.")
    # ... rest of implementation
```

**Checklist:**
- [ ] Add type hints cho tất cả public functions
- [ ] Add docstrings (Google Style) cho tất cả public functions
- [ ] Run mypy và fix errors
- [ ] Generate documentation với Sphinx

**Deliverables:**
- [ ] 100% functions có type hints
- [ ] 100% public functions có docstrings
- [ ] Sphinx documentation generated

---

## 🔧 Week 3-4: Architecture Refactoring

### ✅ Task 5: Loại Bỏ Phụ Thuộc Chéo
**Thời gian:** 1 tuần  
**Người thực hiện:** Senior Dev  
**Độ ưu tiên:** 🔴 Cao

**Chi tiết:**

**Vấn đề hiện tại:**
```python
# ml_model.py (HIỆN TẠI - SAI)
from .bridges.bridges_classic import getAllLoto_V30  # ❌ Import trực tiếp
from .dashboard_analytics import get_loto_stats_last_n_days  # ❌ Import trực tiếp

def prepare_training_data(all_data_ai, daily_bridge_predictions):
    # Sử dụng trực tiếp các hàm này
    current_loto_results = set(getAllLoto_V30(current_data))
    loto_stats = get_loto_stats_last_n_days(all_data_ai[:i], stats_days)
```

**Giải pháp:**
```python
# lottery_service.py hoặc ai_feature_extractor.py (MỚI - ĐÚNG)
def prepare_features_for_ml(all_data_ai):
    """
    Thu thập tất cả features cần thiết cho ML model.
    """
    features_by_ky = {}
    
    for i in range(1, len(all_data_ai)):
        current_data = all_data_ai[i]
        current_ky = str(current_data[0])
        
        # Tính toán tất cả features tại đây
        current_loto_results = set(getAllLoto_V30(current_data))
        loto_stats = get_loto_stats_last_n_days(all_data_ai[:i], stats_days)
        loto_gan_stats = get_loto_gan_stats(all_data_ai[:i], gan_max_days)
        
        # Đóng gói thành dictionary
        features_by_ky[current_ky] = {
            'loto_results': current_loto_results,
            'loto_stats': loto_stats,
            'loto_gan_stats': loto_gan_stats,
            # ... more features
        }
    
    return features_by_ky

# ml_model.py (MỚI - ĐÚNG)
def prepare_training_data(
    all_data_ai: List[List[Any]], 
    daily_bridge_predictions: Dict,
    precomputed_features: Dict  # ✅ Nhận features từ bên ngoài
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Model chỉ nhận data đã được chuẩn bị sẵn, không tự tính toán.
    """
    X = []
    y = []
    
    for ky, features in precomputed_features.items():
        # Sử dụng features đã được tính sẵn
        loto_results = features['loto_results']
        loto_stats = features['loto_stats']
        
        # Build X, y
        # ...
    
    return np.array(X), np.array(y)
```

**Checklist:**
- [ ] Tạo function `prepare_features_for_ml()` trong `ai_feature_extractor.py`
- [ ] Refactor `ml_model.py` để nhận precomputed features
- [ ] Xóa import `bridges_classic` và `dashboard_analytics` khỏi `ml_model.py`
- [ ] Update `lottery_service.py` để gọi đúng flow
- [ ] Run tests để đảm bảo không break
- [ ] Benchmark performance

**Deliverables:**
- [ ] `ml_model.py` không còn import bridge hoặc analytics modules
- [ ] All tests pass
- [ ] Documentation updated

---

### ✅ Task 6: Implement Dependency Injection
**Thời gian:** 3 ngày  
**Người thực hiện:** Senior Dev  
**Độ ưu tiên:** 🟡 Trung bình

**Chi tiết:**
```python
# HIỆN TẠI (SAI)
DB_NAME = 'data/xo_so_prizes_all_logic.db'  # ❌ Hardcode

def load_data_ai_from_db():
    conn = sqlite3.connect(DB_NAME)  # ❌ Dependency cứng
    # ...

# MỚI (ĐÚNG) - Dependency Injection
class DatabaseConnection:
    """Interface cho database connection."""
    def execute(self, query: str) -> List[Any]:
        raise NotImplementedError

class SQLiteConnection(DatabaseConnection):
    """Concrete implementation cho SQLite."""
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def execute(self, query: str) -> List[Any]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return result

class DataRepository:
    """Repository nhận DB connection qua DI."""
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection  # ✅ Inject dependency
    
    def load_data_ai(self) -> List[List[Any]]:
        return self.db.execute('''
            SELECT MaSoKy, Col_A_Ky, ...
            FROM DuLieu_AI
            ORDER BY MaSoKy ASC
        ''')

# Usage
db_conn = SQLiteConnection('data/xo_so_prizes_all_logic.db')
repo = DataRepository(db_conn)
data = repo.load_data_ai()

# Testing
mock_db = MockDatabaseConnection()  # ✅ Dễ dàng mock
test_repo = DataRepository(mock_db)
```

**Checklist:**
- [ ] Tạo `DatabaseConnection` interface
- [ ] Implement `SQLiteConnection` class
- [ ] Refactor `DataRepository` để nhận connection qua constructor
- [ ] Update `MLModel` để nhận repository qua constructor
- [ ] Update all call sites
- [ ] Write tests với mock dependencies

**Deliverables:**
- [ ] All modules dùng DI
- [ ] Test coverage tăng lên (dễ mock hơn)
- [ ] Documentation updated

---

### ✅ Task 7: Optimize Database Queries
**Thời gian:** 2 ngày  
**Người thực hiện:** Backend Dev  
**Độ ưu tiên:** 🟡 Trung bình

**Chi tiết:**
```python
# HIỆN TẠI (SAI)
cursor.execute('SELECT * FROM ManagedBridges')  # ❌ SELECT *

# MỚI (ĐÚNG)
cursor.execute('''
    SELECT id, bridge_name, win_rate_text, max_lose_streak_k2n, is_enabled
    FROM ManagedBridges
    WHERE is_enabled = 1
    ORDER BY id DESC
    LIMIT 100
''')  # ✅ Chỉ lấy cột cần thiết, có WHERE, LIMIT

# Thêm indexes
cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_managed_bridges_enabled 
    ON ManagedBridges(is_enabled)
''')

cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_dulieu_ai_maso_ky 
    ON DuLieu_AI(MaSoKy)
''')
```

**Checklist:**
- [ ] Review tất cả SQL queries
- [ ] Replace `SELECT *` với explicit columns
- [ ] Add WHERE clauses where possible
- [ ] Add LIMIT for large queries
- [ ] Create indexes cho các cột thường query
- [ ] Benchmark query performance

**Deliverables:**
- [ ] All queries optimized
- [ ] Indexes created
- [ ] Query time giảm 50%+

---

## ⚙️ Week 5-6: AI & Monitoring

### ✅ Task 8: Model Versioning & Metadata
**Thời gian:** 2 ngày  
**Người thực hiện:** ML Engineer  
**Độ ưu tiên:** 🔴 Cao

**Chi tiết:**
```python
# Cấu trúc file model mới
logic/ml_model_files/
├── models/
│   ├── loto_model_v7.3.0.joblib
│   ├── loto_model_v7.3.1.joblib
│   └── loto_model_v8.0.0.joblib
├── scalers/
│   ├── ai_scaler_v7.3.0.joblib
│   └── ai_scaler_v8.0.0.joblib
├── metadata/
│   ├── model_v7.3.0_metadata.json
│   └── model_v8.0.0_metadata.json
└── active_model.txt  # Chứa version đang active

# metadata.json structure
{
    "model_version": "8.0.0",
    "trained_date": "2026-01-15T10:30:00",
    "training_samples": 5000,
    "features": [
        "loto_hot_freq",
        "loto_gan_freq",
        "bridge_count",
        "avg_win_rate",
        "min_k2n_risk",
        "current_lose_streak"
    ],
    "hyperparameters": {
        "max_depth": 6,
        "n_estimators": 200,
        "learning_rate": 0.05,
        "objective": "binary:logistic"
    },
    "metrics": {
        "train_accuracy": 0.82,
        "val_accuracy": 0.78,
        "test_accuracy": 0.76,
        "precision": 0.74,
        "recall": 0.79,
        "f1_score": 0.76
    },
    "data_range": {
        "start_ky": "23001",
        "end_ky": "25364"
    }
}

# Code implementation
import json
from datetime import datetime
from pathlib import Path

class ModelVersionManager:
    def __init__(self, model_dir: Path = Path("logic/ml_model_files")):
        self.model_dir = model_dir
        self.models_dir = model_dir / "models"
        self.scalers_dir = model_dir / "scalers"
        self.metadata_dir = model_dir / "metadata"
        
        # Create dirs
        for d in [self.models_dir, self.scalers_dir, self.metadata_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def save_model(
        self, 
        model, 
        scaler, 
        version: str,
        metadata: dict
    ):
        """Save model với version và metadata."""
        # Save model
        model_path = self.models_dir / f"loto_model_v{version}.joblib"
        joblib.dump(model, model_path)
        
        # Save scaler
        scaler_path = self.scalers_dir / f"ai_scaler_v{version}.joblib"
        joblib.dump(scaler, scaler_path)
        
        # Save metadata
        metadata_path = self.metadata_dir / f"model_v{version}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update active model
        active_path = self.model_dir / "active_model.txt"
        active_path.write_text(version)
        
        print(f"✅ Đã lưu model version {version}")
    
    def load_model(self, version: str = None):
        """Load model theo version. Nếu không chỉ định, load active model."""
        if version is None:
            active_path = self.model_dir / "active_model.txt"
            if active_path.exists():
                version = active_path.read_text().strip()
            else:
                raise ValueError("Không tìm thấy active model")
        
        model_path = self.models_dir / f"loto_model_v{version}.joblib"
        scaler_path = self.scalers_dir / f"ai_scaler_v{version}.joblib"
        metadata_path = self.metadata_dir / f"model_v{version}_metadata.json"
        
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return model, scaler, metadata
    
    def list_models(self):
        """List tất cả models đã lưu."""
        models = list(self.models_dir.glob("loto_model_v*.joblib"))
        versions = [m.stem.replace("loto_model_v", "") for m in models]
        
        result = []
        for version in sorted(versions, reverse=True):
            metadata_path = self.metadata_dir / f"model_v{version}_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                result.append({
                    'version': version,
                    'trained_date': metadata['trained_date'],
                    'test_accuracy': metadata['metrics']['test_accuracy']
                })
        
        return result
```

**Checklist:**
- [ ] Implement `ModelVersionManager` class
- [ ] Update `train_ai_model()` để lưu metadata
- [ ] Update `get_ai_predictions()` để load từ ModelVersionManager
- [ ] Thêm UI để xem/switch giữa các model versions
- [ ] Write tests cho ModelVersionManager

**Deliverables:**
- [ ] ModelVersionManager working
- [ ] All models có metadata
- [ ] UI để manage models

---

### ✅ Task 9: Model Monitoring & Logging
**Thời gian:** 3 ngày  
**Người thực hiện:** ML Engineer  
**Độ ưu tiên:** 🔴 Cao

**Chi tiết:**
```python
# Tạo bảng database để log predictions
CREATE TABLE IF NOT EXISTS AI_Predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    model_version TEXT NOT NULL,
    ky TEXT NOT NULL,
    loto TEXT NOT NULL,
    predicted_probability REAL NOT NULL,
    predicted_label INTEGER NOT NULL,  -- 0 hoặc 1
    actual_result INTEGER,  -- NULL nếu chưa biết, 0/1 sau khi có kết quả
    is_correct BOOLEAN,  -- NULL nếu chưa biết
    features_json TEXT  -- Lưu features để debug
);

CREATE TABLE IF NOT EXISTS Model_Metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    calculation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    model_version TEXT NOT NULL,
    date_range_start TEXT,
    date_range_end TEXT,
    total_predictions INTEGER,
    accuracy REAL,
    precision_score REAL,
    recall REAL,
    f1_score REAL
);

# Implementation
import sqlite3
import json
from datetime import datetime, timedelta

class ModelMonitor:
    def __init__(self, db_path: str = "data/xo_so_prizes_all_logic.db"):
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self):
        """Tạo bảng nếu chưa tồn tại."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS AI_Predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                model_version TEXT NOT NULL,
                ky TEXT NOT NULL,
                loto TEXT NOT NULL,
                predicted_probability REAL NOT NULL,
                predicted_label INTEGER NOT NULL,
                actual_result INTEGER,
                is_correct BOOLEAN,
                features_json TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Model_Metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calculation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                model_version TEXT NOT NULL,
                date_range_start TEXT,
                date_range_end TEXT,
                total_predictions INTEGER,
                accuracy REAL,
                precision_score REAL,
                recall REAL,
                f1_score REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_prediction(
        self,
        model_version: str,
        ky: str,
        loto: str,
        probability: float,
        label: int,
        features: dict = None
    ):
        """Log một prediction."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        features_json = json.dumps(features) if features else None
        
        cursor.execute('''
            INSERT INTO AI_Predictions 
            (model_version, ky, loto, predicted_probability, predicted_label, features_json)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (model_version, ky, loto, probability, label, features_json))
        
        conn.commit()
        conn.close()
    
    def update_actual_result(self, ky: str, loto: str, actual_result: int):
        """Update kết quả thực tế sau khi có kết quả."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE AI_Predictions
            SET actual_result = ?,
                is_correct = (predicted_label = ?)
            WHERE ky = ? AND loto = ?
        ''', (actual_result, actual_result, ky, loto))
        
        conn.commit()
        conn.close()
    
    def calculate_metrics(self, days: int = 30) -> dict:
        """Tính metrics cho N ngày gần nhất."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current model version
        model_version = self._get_current_model_version()
        
        # Query predictions trong N ngày gần nhất
        cursor.execute('''
            SELECT predicted_label, actual_result, is_correct
            FROM AI_Predictions
            WHERE model_version = ?
                AND actual_result IS NOT NULL
                AND prediction_date >= datetime('now', '-{} days')
        '''.format(days), (model_version,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        # Calculate metrics
        total = len(rows)
        correct = sum(1 for _, _, is_correct in rows if is_correct)
        accuracy = correct / total if total > 0 else 0
        
        # Precision, Recall, F1
        tp = sum(1 for pred, actual, _ in rows if pred == 1 and actual == 1)
        fp = sum(1 for pred, actual, _ in rows if pred == 1 and actual == 0)
        fn = sum(1 for pred, actual, _ in rows if pred == 0 and actual == 1)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        metrics = {
            'model_version': model_version,
            'total_predictions': total,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
        
        # Save to database
        self._save_metrics(metrics, days)
        
        return metrics
    
    def _save_metrics(self, metrics: dict, days: int):
        """Lưu metrics vào database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        date_end = datetime.now().strftime('%Y-%m-%d')
        date_start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO Model_Metrics
            (model_version, date_range_start, date_range_end, 
             total_predictions, accuracy, precision_score, recall, f1_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics['model_version'],
            date_start,
            date_end,
            metrics['total_predictions'],
            metrics['accuracy'],
            metrics['precision'],
            metrics['recall'],
            metrics['f1_score']
        ))
        
        conn.commit()
        conn.close()
    
    def get_metrics_history(self, limit: int = 30) -> list:
        """Lấy lịch sử metrics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT calculation_date, model_version, 
                   total_predictions, accuracy, precision_score, recall, f1_score
            FROM Model_Metrics
            ORDER BY calculation_date DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'date': row[0],
                'model_version': row[1],
                'total_predictions': row[2],
                'accuracy': row[3],
                'precision': row[4],
                'recall': row[5],
                'f1_score': row[6]
            }
            for row in rows
        ]
    
    def _get_current_model_version(self) -> str:
        """Get current model version."""
        from pathlib import Path
        active_path = Path("logic/ml_model_files/active_model.txt")
        if active_path.exists():
            return active_path.read_text().strip()
        return "unknown"
```

**Checklist:**
- [ ] Implement `ModelMonitor` class
- [ ] Update `get_ai_predictions()` để log predictions
- [ ] Tạo background task để update actual results
- [ ] Tạo background task để calculate metrics hàng ngày
- [ ] Thêm UI dashboard để hiển thị metrics
- [ ] Setup alert khi accuracy < threshold

**Deliverables:**
- [ ] ModelMonitor working
- [ ] Predictions được log
- [ ] Daily metrics calculation
- [ ] Metrics dashboard trong UI

---

### ✅ Task 10: Hyperparameter Tuning với Optuna
**Thời gian:** 4 ngày  
**Người thực hiện:** ML Engineer  
**Độ ưu tiên:** 🟡 Trung bình

**Chi tiết:**
```bash
# Install Optuna
pip install optuna

# Implement
```

```python
import optuna
from sklearn.model_selection import cross_val_score
import xgboost as xgb

class HyperparameterTuner:
    def __init__(self, X, y):
        self.X = X
        self.y = y
        self.best_params = None
        self.best_score = None
    
    def objective(self, trial):
        """Objective function cho Optuna."""
        # Define hyperparameters to tune
        params = {
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'n_estimators': trial.suggest_int('n_estimators', 100, 500),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'gamma': trial.suggest_float('gamma', 0, 5),
            'reg_alpha': trial.suggest_float('reg_alpha', 0, 5),
            'reg_lambda': trial.suggest_float('reg_lambda', 0, 5),
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'random_state': 42
        }
        
        # Create model
        model = xgb.XGBClassifier(**params)
        
        # Cross-validation
        scores = cross_val_score(
            model, self.X, self.y, 
            cv=5, 
            scoring='accuracy',
            n_jobs=-1
        )
        
        return scores.mean()
    
    def tune(self, n_trials: int = 100):
        """Chạy hyperparameter tuning."""
        study = optuna.create_study(direction='maximize')
        study.optimize(self.objective, n_trials=n_trials, show_progress_bar=True)
        
        self.best_params = study.best_params
        self.best_score = study.best_value
        
        print(f"\n✅ Best accuracy: {self.best_score:.4f}")
        print(f"✅ Best params: {self.best_params}")
        
        return self.best_params, self.best_score
    
    def save_best_params(self, filepath: str = "logic/ml_model_files/best_params.json"):
        """Lưu best params vào file."""
        import json
        from pathlib import Path
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'tuning_date': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Đã lưu best params vào {filepath}")

# Usage
def run_hyperparameter_tuning(X, y, n_trials=100):
    """Chạy hyperparameter tuning."""
    print(f"🔍 Bắt đầu tuning với {n_trials} trials...")
    
    tuner = HyperparameterTuner(X, y)
    best_params, best_score = tuner.tune(n_trials=n_trials)
    tuner.save_best_params()
    
    return best_params, best_score

# Thêm vào UI
def on_tune_hyperparameters_click():
    """Handler cho nút Tune Hyperparameters trong UI."""
    # Load data
    all_data_ai, _ = load_data_ai_from_db()
    daily_predictions = get_daily_bridge_predictions(all_data_ai)
    precomputed_features = prepare_features_for_ml(all_data_ai)
    
    # Prepare training data
    X, y = prepare_training_data(all_data_ai, daily_predictions, precomputed_features)
    
    # Run tuning
    best_params, best_score = run_hyperparameter_tuning(X, y, n_trials=50)
    
    # Show results
    messagebox.showinfo(
        "Tuning Complete",
        f"Best Accuracy: {best_score:.4f}\n\n"
        f"Best Params:\n{json.dumps(best_params, indent=2)}\n\n"
        f"Bạn có muốn train lại model với params này không?"
    )
```

**Checklist:**
- [ ] Install Optuna
- [ ] Implement `HyperparameterTuner` class
- [ ] Thêm nút "Tune Hyperparameters" trong UI (`ui_tuner.py`)
- [ ] Test tuning với small dataset
- [ ] Run full tuning (có thể mất vài giờ)
- [ ] Update config.json với best params

**Deliverables:**
- [ ] HyperparameterTuner working
- [ ] UI để trigger tuning
- [ ] Best params saved
- [ ] Model accuracy tăng 5-10%

---

## 🚀 Week 7-8: DevOps & Production Ready

### ✅ Task 11: Logging System
**Thời gian:** 2 ngày  
**Người thực hiện:** Backend Dev  
**Độ ưu tiên:** 🟡 Trung bình

**Chi tiết:**
```python
# Setup logging
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    """Setup logging system."""
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Console handler (INFO level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler (DEBUG level) với rotation
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Error file handler (ERROR level)
    error_handler = RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    return logger

# Usage trong code
# Replace print() với logger
# HIỆN TẠI (SAI)
print("Đang tải dữ liệu...")  # ❌

# MỚI (ĐÚNG)
logger = logging.getLogger(__name__)
logger.info("Đang tải dữ liệu...")  # ✅
logger.debug(f"Chi tiết: {data}")
logger.warning("Cảnh báo: dữ liệu có thể không đầy đủ")
logger.error("Lỗi khi tải dữ liệu", exc_info=True)
```

**Checklist:**
- [ ] Implement `setup_logging()` function
- [ ] Replace tất cả `print()` với `logger.info()`, `logger.debug()`, etc.
- [ ] Add try-except với logging.error() cho các functions quan trọng
- [ ] Test log rotation
- [ ] Add logs/ vào .gitignore

**Deliverables:**
- [ ] Logging system working
- [ ] No more print() statements
- [ ] Logs rotating properly

---

### ✅ Task 12: CI/CD với GitHub Actions
**Thời gian:** 2 ngày  
**Người thực hiện:** DevOps  
**Độ ưu tiên:** 🟡 Trung bình

**Chi tiết:**
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
    
    - name: Check code formatting
      run: |
        black --check .
        isort --check-only .
    
    - name: Run type checking
      run: |
        mypy logic/ --ignore-missing-imports
    
    - name: Run tests
      run: |
        pytest --cov=logic --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build executable
      run: |
        pyinstaller main_app.spec
    
    - name: Create Release
      uses: softprops/action-gh-release@v1
      with:
        files: dist/main_app.exe
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Checklist:**
- [ ] Create `.github/workflows/ci.yml`
- [ ] Create `.github/workflows/release.yml`
- [ ] Setup Codecov account
- [ ] Test CI pipeline
- [ ] Add CI badge to README

**Deliverables:**
- [ ] CI pipeline running on every push
- [ ] Automated releases on tags
- [ ] Code coverage badge in README

---

### ✅ Task 13: Documentation với Sphinx
**Thời gian:** 2 ngày  
**Người thực hiện:** Tech Writer / Dev  
**Độ ưu tiên:** 🟢 Thấp

**Chi tiết:**
```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Setup Sphinx
mkdir docs
cd docs
sphinx-quickstart

# Configure
# Edit docs/conf.py
```

```python
# docs/conf.py
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Hệ Thống Phân Tích Xổ Số'
copyright = '2026'
author = 'Your Team'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # Support Google/NumPy docstrings
    'sphinx.ext.viewcode',
]

html_theme = 'sphinx_rtd_theme'
```

```bash
# Generate documentation
cd docs
sphinx-apidoc -o . ../logic
make html

# Documentation sẽ ở docs/_build/html/index.html
```

**Checklist:**
- [ ] Install Sphinx
- [ ] Setup Sphinx project
- [ ] Generate API documentation
- [ ] Write user guide
- [ ] Deploy docs to GitHub Pages

**Deliverables:**
- [ ] API documentation generated
- [ ] User guide written
- [ ] Docs hosted on GitHub Pages

---

## 📊 Success Metrics & KPIs

### Metrics sau Week 2 (Quick Wins)
- [ ] ✅ Test coverage: 0% → 70%+
- [ ] ✅ Build time: giảm 30%+
- [ ] ✅ Query time: giảm 50%+
- [ ] ✅ Zero flake8 warnings
- [ ] ✅ All functions có type hints và docstrings

### Metrics sau Week 4 (Architecture Refactoring)
- [ ] ✅ ml_model.py không import bridges/analytics
- [ ] ✅ All modules dùng Dependency Injection
- [ ] ✅ Test coverage: 70% → 80%+

### Metrics sau Week 6 (AI & Monitoring)
- [ ] ✅ Model accuracy tăng 5-10%
- [ ] ✅ Model versioning working
- [ ] ✅ Daily metrics calculation
- [ ] ✅ Metrics dashboard trong UI

### Metrics sau Week 8 (DevOps)
- [ ] ✅ CI pipeline running
- [ ] ✅ Automated deployment
- [ ] ✅ Logging system working
- [ ] ✅ API documentation complete

---

## 🎯 Deliverables Summary

### Week 1-2
- [ ] 50+ unit tests (coverage 70%+)
- [ ] Caching implementation
- [ ] Code formatted với black
- [ ] Type hints & docstrings added

### Week 3-4
- [ ] Phụ thuộc chéo được giải quyết
- [ ] Dependency Injection implemented
- [ ] Database queries optimized

### Week 5-6
- [ ] Model versioning system
- [ ] Model monitoring dashboard
- [ ] Hyperparameter tuning với Optuna
- [ ] Model accuracy tăng 5-10%

### Week 7-8
- [ ] Logging system
- [ ] CI/CD pipeline
- [ ] API documentation
- [ ] Production-ready system

---

## 🚨 Risks & Mitigation

### Risk 1: Breaking Changes
**Risk:** Refactoring có thể break existing functionality  
**Mitigation:**
- Viết tests trước khi refactor
- Incremental changes, test sau mỗi change
- Keep backup của code cũ

### Risk 2: Performance Regression
**Risk:** Thêm logging/monitoring có thể làm chậm hệ thống  
**Mitigation:**
- Benchmark trước và sau mỗi change
- Optimize logging (async logging)
- Profile code để tìm bottlenecks

### Risk 3: Data Loss
**Risk:** Migration database có thể mất dữ liệu  
**Mitigation:**
- Backup database trước khi migrate
- Test migration trên copy của database
- Có rollback plan

---

## ✅ Sign-off

**Project Manager:** __________________  
**Tech Lead:** __________________  
**QA Lead:** __________________  

**Ngày phê duyệt:** __________________

---

**Tài liệu liên quan:**
- `SYSTEM_EVALUATION.md` - Đánh giá chi tiết hệ thống
- `README.md` - Hướng dẫn sử dụng
- `Kế Hoạch Nâng Cấp Hệ Thống Phân Tích Xổ Số (V7.0)K.txt` - Kế hoạch nâng cấp gốc
