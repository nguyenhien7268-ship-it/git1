Markdown

# Xổ Số Data Analysis System (XS-DAS)

[![CI Pipeline](https://github.com/nguyenhien7268-ship-it/git1/actions/workflows/ci.yml/badge.svg)](https://github.com/nguyenhien7268-ship-it/git1/actions/workflows/ci.yml)
[![Code Quality](https://img.shields.io/badge/flake8-passing-brightgreen)](https://github.com/nguyenhien7268-ship-it/git1)
[![Tests](https://img.shields.io/badge/tests-12%20passing-brightgreen)](https://github.com/nguyenhien7268-ship-it/git1)

## 🎯 Giới Thiệu

Đây là Hệ thống Phân tích Dữ liệu Xổ Số (XS-DAS), được thiết kế để tự động backtest, phân tích chuyên sâu các chiến lược dò cầu, quản lý chiến lược và đưa ra dự đoán dựa trên AI. Hệ thống cung cấp các công cụ trực quan để tinh chỉnh và tối ưu hóa tham số.

---

## 🏗️ TÁI CẤU TRÚC KIẾN TRÚC (V7.3 - MVP)

Hệ thống đã được chuyển đổi sang kiến trúc **Model-View-Presenter (MVP)** để phân tách rõ ràng các luồng nghiệp vụ và nâng cao khả năng bảo trì:

* **Model (`logic/`)**: "Bộ não" của ứng dụng, chứa toàn bộ logic nghiệp vụ, tính toán, backtest, AI và truy vấn cơ sở dữ liệu.
* **View (`ui/`)**: "Bộ mặt" của ứng dụng, chỉ chịu trách nhiệm hiển thị giao diện (nút bấm, bảng biểu, biểu đồ) và báo cáo hành động của người dùng.
* **Presenter (`app_controller.py`):** "Bộ điều phối" trung gian, nhận lệnh từ View, yêu cầu Model xử lý, và cập nhật kết quả ngược lại cho View.
* **Services (`core_services.py`):** Cung cấp các dịch vụ lõi như quản lý đa luồng (`TaskManager`) và ghi log an toàn (`Logger`) để ngăn ứng dụng bị "đơ" (freeze) khi chạy tác vụ nặng.

---

## ✨ CÁC CHỨC NĂNG CỐT LÕI

### 1. Phân Tích & Backtest Chuyên Sâu
* **Backtest Đa Chế độ:** Thực hiện backtest trên 15 Cầu Cổ Điển, Cầu V17 (Shadow) và 756 Cầu Bạc Nhớ ở cả chế độ N1 (Ngày 1) và K2N (Khung 2 Ngày).
* **Quản Lý Cầu:** Cho phép người dùng thêm/xóa/vô hiệu hóa các cầu đã lưu.
* **Thống kê Lô Gan:** Tự động tính toán thống kê Lô Gan trên 8 kỳ.

### 2. Trí Tuệ Nhân Tạo (AI)
* **Huấn luyện Mô hình:** Chức năng Huấn luyện AI chuyên biệt (XGBoost).
* **Dự đoán:** Cung cấp dự đoán AI (V7.0) được tích hợp trực tiếp vào Bảng Quyết Định Tối Ưu.

### 3. Tối Ưu Hóa & Tinh Chỉnh Tham Số
* **Bảng Quyết Định Tối Ưu:** Tổng hợp kết quả từ 5 hệ thống phân tích cốt lõi (bao gồm AI và Cache K2N).
* **Tối Ưu Hóa Chiến Lược (Optimizer):** Cho phép chạy các kịch bản tối ưu hóa để tìm ra cấu hình lợi nhuận cao nhất.

---

## 📂 Cấu trúc Thư mục

du-an-backup/ ├── main_app.py # (RUN) File khởi chạy ứng dụng ├── app_controller.py # (Presenter) Bộ điều phối chính ├── core_services.py # (Services) Quản lý đa luồng, Logger │ ├── logic/ # (MODEL) Toàn bộ logic nghiệp vụ │ ├── lottery_service.py # (API Gateway) Cổng giao tiếp cho Model │ ├── db_manager.py # Logic CRUD cơ sở dữ liệu (SQLite) │ ├── data_repository.py # Logic tải/truy vấn dữ liệu lớn │ ├── data_parser.py # Logic phân tích (parse) file .txt, .json │ ├── backtester.py # Logic chạy backtest │ ├── dashboard_analytics.py # Logic chấm điểm cho Bảng Quyết Định │ ├── ai_feature_extractor.py # Logic trích xuất đặc trưng AI │ ├── ml_model.py # Logic mô hình AI (XGBoost) │ ├── config_manager.py # Quản lý file config.json │ └── bridges/ # Các thuật toán soi cầu │ ├── bridges_classic.py │ └── bridges_memory.py │ ├── ui/ # (VIEW) Toàn bộ giao diện │ ├── ui_main_window.py # Cửa sổ chính (quản lý các Tab) │ ├── ui_dashboard.py # Tab Bảng Quyết Định (có biểu đồ) │ ├── ui_lookup.py # Tab Tra Cứu │ ├── ui_optimizer.py # Tab Tối ưu hóa │ ├── ui_settings.py # Cửa sổ Cài đặt │ └── ... │ ├── data/ │ └── xo_so_prizes_all_logic.db # File cơ sở dữ liệu └── logic/ml_model_files/ ├── loto_model.joblib # File mô hình AI đã huấn luyện └── ai_scaler.joblib # File scaler


## ⚙️ Yêu cầu Thư viện

Ngoài các thư viện Python cơ bản, dự án này yêu cầu các thư viện bên ngoài:

```bash
pip install pandas
pip install matplotlib
pip install scikit-learn
pip install joblib
pip install xgboost
Hướng dẫn Khởi chạy
Cài đặt các thư viện yêu cầu: pip install -r requirements.txt (Nếu có file) hoặc cài đặt thủ công các thư viện ở trên.

Chạy file main_app.py:

Bash

python main_app.py