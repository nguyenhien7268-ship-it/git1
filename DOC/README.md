# Xổ Số Data Analysis System (XS-DAS) - V7.8

[![CI Pipeline](https://github.com/nguyenhien7268-ship-it/git1/actions/workflows/ci.yml/badge.svg)](https://github.com/nguyenhien7268-ship-it/git1/actions/workflows/ci.yml)
[![Code Quality](https://img.shields.io/badge/flake8-passing-brightgreen)](https://github.com/nguyenhien7268-ship-it/git1)
[![Tests](https://img.shields.io/badge/tests-15%20passing-brightgreen)](https://github.com/nguyenhien7268-ship-it/git1)

CẤU TRÚC THƯ MỤC
root/
├── data/
│   └── xo_so_prizes_all_logic.db    # Cơ sở dữ liệu chính
├── DOC/                             # Tài liệu dự án
├── logic/                           # BACKEND LOGIC
│   ├── bridges/                     # Các thuật toán soi cầu
│   │   ├── bridge_manager_de.py     # Quản lý cầu Đề (Cũ/Sẽ sửa sau)
│   │   ├── de_bridge_scanner.py     # Quét cầu Đề (Sẽ nâng cấp ở GĐ 2)
│   │   └── ... (các file cầu Lô)
│   ├── ml_model_files/              # File mô hình AI
│   ├── backtester_core.py           # Lõi kiểm thử (Dùng chung)
│   ├── db_manager.py                # Quản lý kết nối DB
│   ├── de_analytics.py              # (MỚI) 🟢 Phân tích thị trường Đề
│   ├── de_utils.py                  # (MỚI) 🟢 Tiện ích & Adapter Đề
│   └── ... (các file logic Lô)
├── ui/                              # GIAO DIỆN NGƯỜI DÙNG
│   ├── ui_de_dashboard.py           # (SẼ SỬA) Màn hình Soi Cầu Đề
│   ├── ui_dashboard.py              # Màn hình Soi Cầu Lô
│   └── ...
├── app_controller.py                # Bộ điều phối chính
├── main_app.py                      # File chạy chương trình
└── ...

## 🎯 Giới Thiệu

Đây là Hệ thống Phân tích Dữ liệu Xổ Số (XS-DAS), được thiết kế để tự động backtest, phân tích chuyên sâu các chiến lược dò cầu, quản lý chiến lược và đưa ra dự đoán dựa trên AI. Hệ thống cung cấp các công cụ trực quan để tinh chỉnh và tối ưu hóa tham số đầu tư.

---

## 🚀 CẬP NHẬT MỚI (V7.8 - SEPARATION OF CONCERNS)

Phiên bản V7.8 đánh dấu bước ngoặt về kiến trúc hệ thống, tách biệt hoàn toàn logic xử lý **Lô** và **Đề** để tối ưu hóa hiệu năng và khả năng bảo trì:

* **🔮 Hệ Thống Soi Cầu Đề Chuyên Biệt:**
    * **Module Mới:** `bridge_manager_de.py` hoạt động độc lập.
    * **Thuật Toán:** Sử dụng vị trí V17 (Shadow) để tìm cặp số cốt lõi, từ đó suy ra **4 Chạm Đề** (Gốc + Bóng Dương).
    * **Backtest Kép:** Đánh giá đồng thời tỷ lệ ăn ngày 1 (N1) và khung nuôi 2 ngày (K2N).
* **🛠️ Tái Cấu Trúc Core:**
    * `bridge_manager_core.py`: Được tinh gọn để chỉ tập trung xử lý **Cầu Lô** (V17 + Bạc Nhớ).
    * Giảm thiểu xung đột logic, giúp việc nâng cấp thuật toán cho từng loại hình trở nên dễ dàng hơn.
* **📊 Dashboard Nâng Cấp:**
    * Tích hợp hiển thị dữ liệu Soi Cầu Đề ngay trên giao diện chính (Tab riêng biệt).
    * Quy trình "Tự động Dò & Thêm Cầu" giờ đây chạy song song cả 2 hệ thống Lô và Đề.

---

## 🏗️ KIẾN TRÚC HỆ THỐNG (MVP)

Hệ thống vận hành theo mô hình **Model-View-Presenter (MVP)** cải tiến:

### 1. Model (`logic/`)
"Bộ não" của ứng dụng, chứa toàn bộ logic nghiệp vụ được phân chia rõ ràng:

* **Bridge Managers (Quản lý Cầu):**
    * **`bridge_manager_core.py`**: Quản lý và dò tìm **Cầu Lô** (V17, Bạc Nhớ).
    * **`bridge_manager_de.py`**: Quản lý và dò tìm **Cầu Đề** (4 Chạm, K1N/K2N).
* **Backtest Engine:**
    * `backtester_core.py`: Lõi tính toán Backtest hiệu năng cao.
    * `backtester_scoring.py`: Hệ thống chấm điểm thông minh.
* **Analytics & AI:**
    * `dashboard_analytics.py`: Engine chấm điểm tổng lực.
    * `ml_model.py`: Mô hình AI (XGBoost) dự đoán xác suất.
    * `ai_feature_extractor.py`: Trích xuất đặc trưng cho AI.
* **Database:**
    * `db_manager.py`: Quản lý cơ sở dữ liệu SQLite (`ManagedBridges`, `results_A_I`).

### 2. View (`ui/`)
Giao diện người dùng (Tkinter):
* **`ui_main_window.py`**: Khung chương trình chính.
* **`ui_dashboard.py`**: Bảng Quyết Định Lô (Decision Dashboard).
* **`ui_de_dashboard.py`**: Bảng Soi Cầu Đề chuyên sâu.
* **`ui_bridge_manager.py`**: Quản lý danh sách cầu đã lưu (chung cho cả Lô & Đề).
* **`ui_settings.py`**: Cài đặt tham số hệ thống.

### 3. Controller
* **`app_controller.py`**: Điều phối luồng dữ liệu, gọi đúng Manager (Lô hoặc Đề) dựa trên yêu cầu người dùng.
* **`lottery_service.py`**: Facade API giúp UI giao tiếp với tầng Logic.

---

## ⚙️ Yêu cầu Thư viện

Cài đặt các thư viện cần thiết qua `pip`:

```bash
pip install -r requirements.txt
📝 Hướng Dẫn Sử Dụng Nhanh
Nạp Dữ Liệu: * Mở tab "Nạp/Cập Nhật Dữ Liệu".

Nhập file dữ liệu hoặc paste text dữ liệu mới nhất.

Nhấn "Cập Nhật Ngay".

Dò Cầu Tự Động (Lô & Đề): * Vào tab "Quản lý & Dò Cầu".

Nhấn nút "Tự động Dò & Thêm Cầu (V17+BN)".

Hệ thống sẽ chạy lần lượt: Dò Lô V17 -> Dò Bạc Nhớ -> Dò Đề V17.

Xem Kết Quả:

Lô: Xem tại tab "Bảng Quyết Định" (Kết hợp chấm điểm AI, Phong độ, Bạc nhớ...).

Đề: Xem tại tab "Soi Cầu Đề" (Thống kê Chạm, Bộ số, Dàn đề dự đoán).

Quản Lý Cầu: * Vào nút "Quản lý Cầu (V17)".

Tại đây bạn có thể xem, xóa hoặc tắt/bật các cầu đã lưu. Cầu Đề sẽ có tên bắt đầu bằng "Đề...".