# Xổ Số Data Analysis System (XS-DAS) - V7.5

[![CI Pipeline](https://github.com/nguyenhien7268-ship-it/git1/actions/workflows/ci.yml/badge.svg)](https://github.com/nguyenhien7268-ship-it/git1/actions/workflows/ci.yml)
[![Code Quality](https://img.shields.io/badge/flake8-passing-brightgreen)](https://github.com/nguyenhien7268-ship-it/git1)
[![Tests](https://img.shields.io/badge/tests-12%20passing-brightgreen)](https://github.com/nguyenhien7268-ship-it/git1)

## 🎯 Giới Thiệu

Đây là Hệ thống Phân tích Dữ liệu Xổ Số (XS-DAS), được thiết kế để tự động backtest, phân tích chuyên sâu các chiến lược dò cầu, quản lý chiến lược và đưa ra dự đoán dựa trên AI. Hệ thống cung cấp các công cụ trực quan để tinh chỉnh và tối ưu hóa tham số đầu tư.

---

## 🚀 CẬP NHẬT MỚI (V7.5 - DASHBOARD REVOLUTION)

Phiên bản V7.5 tập trung nâng cấp toàn diện trải nghiệm **Bảng Quyết Định (Dashboard)** và tối ưu hóa logic chấm điểm:

* **📊 Giao diện Dashboard 24 Cột:** Layout mới tối ưu hóa không gian, chia tỷ lệ 2/3 cho Bảng Chấm Điểm và 1/3 cho Cầu K2N Chờ.
* **🧠 Logic Chấm Điểm Thông Minh:**
    * **Phạt Rủi Ro Cố Định:** Chuyển từ phạt theo số khung sang phạt điểm cố định (mặc định -1.0) khi cầu vượt ngưỡng gãy.
    * **Gom Nhóm Lý Do (Aggregation):** Tự động gộp các lý do trùng lặp (VD: "Rủi ro K2N (x3) -3.0") giúp bảng điểm gọn gàng, dễ đọc.
* **🔥 Bảng Phong Độ 10 Kỳ:** Thay thế biểu đồ tĩnh bằng bảng dữ liệu động, lọc ra các cầu đang "thông" (>= 5/10 kỳ thắng).
* **⚡ Tối Ưu Backtest Core:** Sửa lỗi tính toán phong độ trong chế độ chạy ngầm (background backtest).

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