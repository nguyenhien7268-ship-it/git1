Markdown

# Hệ Thống Phân Tích Xổ Số (V7.3 - Tái Cấu Trúc MVP)

Đây là dự án phân tích dữ liệu xổ số bằng Python, sử dụng Tkinter (ttk) cho giao diện và XGBoost cho mô hình dự đoán.

Phiên bản này đã được tái cấu trúc lớn (Refactoring) để cải thiện độ ổn định, khả năng bảo trì và thêm các tính năng nâng cao.

## Các Nâng Cấp Chính (Từ V6.0 -> V7.3)

### 1. Tái cấu trúc Kiến trúc (MVP)
Hệ thống đã được chuyển đổi từ mô hình nguyên khối (monolithic) sang kiến trúc **Model-View-Presenter (MVP)** để phân tách rõ ràng các luồng nghiệp vụ:

* **Model (`logic/`)**: "Bộ não" của ứng dụng, chứa toàn bộ logic nghiệp vụ, tính toán, backtest, AI và truy vấn cơ sở dữ liệu.
* **View (`ui/`)**: "Bộ mặt" của ứng dụng, chỉ chịu trách nhiệm hiển thị giao diện (nút bấm, bảng biểu, biểu đồ) và báo cáo hành động của người dùng.
* **Presenter (`app_controller.py`):** "Bộ điều phối" trung gian, nhận lệnh từ View, yêu cầu Model xử lý, và cập nhật kết quả ngược lại cho View.
* **Services (`core_services.py`):** Cung cấp các dịch vụ lõi như quản lý đa luồng (`TaskManager`) và ghi log an toàn (`Logger`) để ngăn ứng dụng bị "đơ" (freeze) khi chạy tác vụ nặng.

### 2. Nâng cấp Giao diện Người dùng (UI/UX)
* **Giao diện Đa Tab:** Hợp nhất các cửa sổ `Dashboard` (Bảng Quyết Định) và `Tra Cứu` thành các Tab chính trong ứng dụng, loại bỏ việc mở quá nhiều cửa sổ con.
* **Sắp xếp Tab "Điều Khiển":** Gom nhóm các chức năng (Nạp, Quản lý, Backtest) vào một `Notebook` con, giúp giao diện gọn gàng, giải quyết tình trạng "Button Hell" (quá nhiều nút).
* **Trực quan hóa Dữ liệu:** Tích hợp `matplotlib` và `pandas` để thêm biểu đồ cột (Bar Chart) vào Tab "Bảng Quyết Định", trực quan hóa Top 5 cặp số có điểm cao nhất.

### 3. Tái cấu trúc Logic (Model)
* File `lottery_service.py` đã được dọn dẹp, chỉ còn vai trò là một API điều phối (imports và exports) cho Model.
* Logic xử lý dữ liệu (parsing, thêm text) đã được chuyển vào file chuyên biệt `logic/data_parser.py`.
* Toàn bộ logic "bộ não" của AI (tính toán đặc trưng - features) và các hàm đa luồng AI đã được chuyển vào file chuyên biệt `logic/ai_feature_extractor.py`.

## Cấu trúc Thư mục

du-an-backup/ │ ├── main_app.py # (RUN) File khởi chạy ứng dụng ├── app_controller.py # (Presenter) Bộ điều phối chính ├── core_services.py # (Services) Quản lý đa luồng, Logger │ ├── logic/ # (MODEL) Toàn bộ logic nghiệp vụ │ ├── lottery_service.py # (API Gateway) Cổng giao tiếp cho Model │ ├── db_manager.py # Logic CRUD cơ sở dữ liệu (SQLite) │ ├── data_repository.py # Logic tải/truy vấn dữ liệu lớn │ ├── data_parser.py # Logic phân tích (parse) file .txt, .json │ ├── backtester.py # Logic chạy backtest │ ├── dashboard_analytics.py# Logic chấm điểm cho Bảng Quyết Định │ ├── ai_feature_extractor.py # Logic trích xuất đặc trưng AI │ ├── ml_model.py # Logic mô hình AI (XGBoost) │ ├── config_manager.py # Quản lý file config.json │ │ │ └── bridges/ # Các thuật toán soi cầu │ ├── bridges_classic.py │ ├── bridges_memory.py │ └── ... │ ├── ui/ # (VIEW) Toàn bộ giao diện │ ├── ui_main_window.py # Cửa sổ chính (quản lý các Tab) │ ├── ui_dashboard.py # Tab Bảng Quyết Định (có biểu đồ) │ ├── ui_lookup.py # Tab Tra Cứu │ ├── ui_optimizer.py # Tab Tối ưu hóa │ ├── ui_settings.py # Cửa sổ Cài đặt │ └── ... │ ├── data/ │ └── xo_so_prizes_all_logic.db # File cơ sở dữ liệu │ ├── logic/ml_model_files/ │ ├── loto_model.joblib # File mô hình AI đã huấn luyện │ └── ai_scaler.joblib # File scaler │ └── README.md # Tài liệu dự án


## Yêu cầu Thư viện
Ngoài các thư viện Python cơ bản, dự án này yêu cầu các thư viện bên ngoài (cần cài đặt qua pip):

```bash
pip install pandas
pip install matplotlib
pip install scikit-learn
pip install joblib
pip install xgboost
Hướng dẫn Khởi chạy
Cài đặt các thư viện yêu cầu: pip install -r requirements.txt (Nếu có file) hoặc cài đặt thủ công các thư vện ở trên.

Chạy file main_app.py:

Bash

python main_app.py