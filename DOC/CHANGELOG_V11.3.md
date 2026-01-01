
# CHANGELOG V11.3 - SCORING ENGINE REFACTOR & CLEANUP

## 📅 Release Date: 2026-01-01

## 🎯 Summary
Phiên bản V11.3 tập trung vào việc **hiện đại hóa hệ thống tính điểm (Scoring Engine)** và **dọn dẹp toàn diện** codebase để loại bỏ nợ kỹ thuật (Technical Debt). Không có tính năng người dùng mới, nhưng độ ổn định và khả năng bảo trì được cải thiện đáng kể.

## ✨ New Features (Internal)

### 1. Object-Oriented Scoring Engine
- **Refactor `logic/backtester_scoring.py`**:
    - Chuyển đổi từ các hàm rời rạc sang kiến trúc Class `BaseScorer`.
    - **`LoScorer`**: Class chuyên biệt cho tính điểm Lô (STL/BTL), tích hợp logic Vote, Phong độ (Recent Form), Lô Gan, AI Probability.
    - **`DeScorer`**: Class chuyên biệt cho tính điểm Đề, sẵn sàng mở rộng cho các thuật toán phức tạp hơn.
    - **Backward Compatibility**: Giữ các alias `score_by_streak`, `score_by_rate` để không phá vỡ code cũ.

### 2. Dashboard Integration
- **Refactor `logic/analytics/dashboard_scorer.py`**:
    - Loại bỏ hàm `get_top_scored_pairs` cũ (dài dòng, khó đọc).
    - Thay thế bằng lời gọi `LoScorer().score_all_pairs(...)`.
    - Giữ nguyên luồng dữ liệu (Data Pipeline) nhưng ủy quyền tính toán cho Scorer Class.

## 🛠 Improvements & Cleanup

### 1. Codebase Cleanup
- **Archive**: Di chuyển 15+ file `.bak` và script cũ (V7, V8 migration scripts) vào thư mục `archive/`.
- **Organization**: Dọn dẹp thư mục `scripts/` và root directory.

### 2. Testing
- Thêm `tests/test_scoring_functions.py` mới sử dụng `unittest` chuẩn.
- Coverage cho logic tính điểm đạt 100% các nhánh quan trọng (Risk Penalty, Bonus).

## 🐛 Bug Fixes
- Sửa lỗi tiềm ẩn khi `dashboard_scorer` import logic vòng tròn bằng cách sử dụng lazy import hoặc cấu trúc class tách biệt.
- Khắc phục vấn đề UnicodeEncodeError trong script kiểm tra bằng cách mock config.

---

## ⚠️ Breaking Changes
- Các script bên thứ 3 (nếu có) gọi trực tiếp `get_top_scored_pairs` từ `dashboard_scorer.py` vẫn hoạt động nhưng logic bên trong đã thay đổi.
- Cần đảm bảo `logic.config_manager` được khởi tạo đúng trước khi gọi Scorer.
