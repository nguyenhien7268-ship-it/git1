# Xổ Số Data Analysis System (XS-DAS) - V11.2

[![CI Pipeline](https://github.com/nguyenhien7268-ship-it/git1/actions/workflows/ci.yml/badge.svg)](https://github.com/nguyenhien7268-ship-it/git1/actions/workflows/ci.yml)
[![Code Quality](https://img.shields.io/badge/flake8-passing-brightgreen)](https://github.com/nguyenhien7268-ship-it/git1)
[![Tests](https://img.shields.io/badge/tests-12%20passing-brightgreen)](https://github.com/nguyenhien7268-ship-it/git1)

## 🎯 Giới Thiệu

Đây là Hệ thống Phân tích Dữ liệu Xổ Số (XS-DAS), được thiết kế để tự động backtest, phân tích chuyên sâu các chiến lược dò cầu, quản lý chiến lược và đưa ra dự đoán dựa trên AI. Hệ thống cung cấp các công cụ trực quan để tinh chỉnh và tối ưu hóa tham số đầu tư.

---

---

## 🚀 CẬP NHẬT MỚI (V11.3 - SCORING REFACTOR & CLEANUP)

Refactor toàn diện hệ thống tính điểm và dọn dẹp codebase:

* **🎯 Scoring Engine 2.0:**
    * Chuyển đổi từ functional sang OOP: `LoScorer` (Lô) và `DeScorer` (Đề).
    * Tích hợp logic Vote, Phong độ, Lô Gan, AI vào một class duy nhất `LoScorer`.
    * Loại bỏ code legacy trong `dashboard_scorer.py`, giúp dễ bảo trì và mở rộng.
* **🧹 Project Cleanup:**
    * Di chuyển các file `.bak` và script cũ vào `archive/`.
    * Chuẩn hóa cấu trúc thư mục.

---

## 🔙 CẬP NHẬT TRƯỚC (V11.2 - K1N-PRIMARY SCANNER REFACTOR)

Phiên bản V11.2 tập trung vào tái cấu trúc **Scanner Module** để hỗ trợ quy trình K1N-Primary Detection Flow:

* **🔍 Scanner Read-Only:** Các module scanner (de_bridge_scanner.py, lo_bridge_scanner.py) không còn ghi trực tiếp vào DB.
    * Scanners trả về `Candidate` objects với K1N/K2N rates đính kèm
    * Tự động loại trừ bridges đã tồn tại trước khi trả kết quả
    * Single DB call cho hiệu suất tối ưu
* **📊 K1N/K2N Rate Integration:** 
    * Tự động đính kèm K1N (real backtest) và K2N (simulated) rates từ cache
    * Đánh dấu `rate_missing` flag khi không tìm thấy rates trong cache
    * Hỗ trợ policy-based filtering (K1N-primary, K2N-primary, combined)
* **🔄 Import Workflow:** 
    * Scan → Preview → Import với `BridgeImporter.preview_import()`
    * Cho phép kiểm tra trước khi thêm bridges vào DB
    * Atomic bulk operations để đảm bảo tính toàn vẹn dữ liệu
* **✅ Testing Infrastructure:** Integration tests mới để verify scanner behavior

### Cách sử dụng Scanner mới:

```python
from logic.bridges.de_bridge_scanner import run_de_scanner
from logic.bridge_importer import BridgeImporter, ImportConfig

# 1. Scan bridges (READ-ONLY, no DB writes)
candidates, meta = run_de_scanner(lottery_data, db_name)
print(f"Found: {meta['found_total']}, Excluded: {meta['excluded_existing']}")

# 2. Preview and filter candidates
config = ImportConfig(policy_type='k1n_primary', threshold_k1n_de=90.0)
importer = BridgeImporter(config)
preview = importer.preview_import(candidates)
print(f"Will import: {preview['accepted']}, Reject: {preview['rejected']}")

# 3. Import accepted candidates
result = importer.import_candidates(candidates)
print(f"Imported: {result['imported']}")
```

---

## 🔙 CẬP NHẬT TRƯỚC ĐÓ (V7.5 - DASHBOARD REVOLUTION)

* **📊 Giao diện Dashboard 24 Cột:** Layout mới tối ưu hóa không gian, chia tỷ lệ 2/3 cho Bảng Chấm Điểm và 1/3 cho Cầu K2N Chờ.
* **🧠 Logic Chấm Điểm Thông Minh:** Phạt rủi ro cố định, gom nhóm lý do, bảng phong độ 10 kỳ.
* **⚡ Tối Ưu Backtest Core:** Sửa lỗi tính toán phong độ trong chế độ chạy ngầm.

---

## 🏗️ KIẾN TRÚC HỆ THỐNG (MVP)

Hệ thống vận hành theo mô hình **Model-View-Presenter (MVP)** cải tiến:

### 1. Model (`logic/`)
"Bộ não" của ứng dụng, chứa toàn bộ logic nghiệp vụ:
* **`backtester_core.py`**: Lõi tính toán Backtest, hỗ trợ đa thuật toán (V17 & Bạc Nhớ).
* **`dashboard_analytics.py`**: Engine chấm điểm tổng lực, phân tích rủi ro và cơ hội.
* **`bridges/`**: Chứa các thuật toán soi cầu:
    * `bridges_v16.py`: Cầu V17 (Bóng Âm Dương).
    * `bridges_memory.py`: Cầu Bạc Nhớ (Tổng/Hiệu).
* **`ml_model.py`**: Mô hình AI (XGBoost) dự đoán xác suất.
* **`db_manager.py`**: Quản lý cơ sở dữ liệu SQLite (`ManagedBridges`, `results_A_I`).

### 2. View (`ui/`)
Giao diện người dùng (Tkinter):
* **`ui_dashboard.py`**: Bảng điều khiển trung tâm (Decision Dashboard).
* **`ui_bridge_manager.py`**: Quản lý danh sách cầu đã lưu.
* **`ui_settings.py`**: Cài đặt tham số hệ thống (Ngưỡng phạt, Trọng số AI...).
* **`ui_main_window.py`**: Khung chương trình chính.

### 3. Controller
* **`app_controller.py`**: Điều phối luồng dữ liệu giữa UI và Logic.

---

## ⚙️ Yêu cầu Thư viện

Cài đặt các thư viện cần thiết qua `pip`:

```bash
pip install -r requirements.txt