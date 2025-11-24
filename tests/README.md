# Testing Infrastructure - XS-DAS

## Tổng Quan

Hệ thống testing đã được thiết lập với pytest và coverage để đảm bảo chất lượng code và tăng confidence khi refactor.

## Cấu Trúc Tests

```
tests/
├── conftest.py                    # Pytest fixtures và shared utilities
├── test_basic.py                  # Basic smoke tests
├── test_validators_unit.py        # Unit tests cho validators.py
├── test_backtester_helpers_unit.py # Unit tests cho backtester_helpers.py
├── test_db_manager_unit.py        # Unit tests cho db_manager.py
└── ... (các integration tests khác)
```

## Chạy Tests

### Chạy tất cả tests
```bash
pytest tests/ -v
```

### Chạy tests với coverage
```bash
pytest tests/ -v --cov=logic --cov=app_controller --cov-report=html --cov-report=term-missing
```

### Chạy chỉ unit tests
```bash
pytest tests/ -v -k "unit"
```

### Chạy tests cụ thể
```bash
pytest tests/test_validators_unit.py -v
```

## Coverage

Coverage configuration được định nghĩa trong `.coveragerc`.

### Xem coverage report
```bash
# Generate HTML report
pytest --cov=logic --cov-report=html
# Mở file htmlcov/index.html trong browser
```

### Target Coverage
- **Hiện tại:** ~0% (chỉ có smoke tests)
- **Mục tiêu Phase 1:** ≥ 60% cho critical paths
- **Mục tiêu cuối cùng:** ≥ 80%

## Test Categories

Tests được đánh dấu bằng markers:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, with dependencies)
- `@pytest.mark.slow` - Slow tests (skip with `-m "not slow"`)

## Fixtures

### temp_db
Tạo temporary database cho testing:
```python
def test_something(temp_db):
    conn, cursor, db_path = temp_db
    # Use database...
```

### sample_lottery_data
Sample lottery data format:
```python
def test_backtest(sample_lottery_data):
    # Use sample data...
```

### mock_settings
Mock SETTINGS object:
```python
def test_config(mock_settings):
    # Use mock settings...
```

## Best Practices

1. **Isolation**: Mỗi test phải độc lập, không phụ thuộc vào test khác
2. **Fixtures**: Sử dụng fixtures thay vì setup/teardown thủ công
3. **Naming**: Test functions phải bắt đầu với `test_`
4. **Assertions**: Sử dụng descriptive assertions
5. **Coverage**: Tập trung vào critical paths trước

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) tự động:
- Chạy tests trên Python 3.9, 3.10, 3.11
- Generate coverage reports
- Upload coverage to Codecov
- Run linting checks

## Next Steps

1. ✅ Setup pytest infrastructure
2. ✅ Create unit tests cho core functions
3. ✅ Setup coverage configuration
4. ✅ Create CI/CD workflow
5. ⏳ Thêm unit tests cho bridge functions
6. ⏳ Thêm integration tests
7. ⏳ Đạt 60% coverage cho critical paths






