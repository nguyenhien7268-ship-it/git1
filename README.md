# TỔNG QUAN HỆ THỐNG PHÂN TÍCH XỔ SỐ (V3.3)

Đây là tài liệu tóm tắt kiến trúc hệ thống, được xây dựng theo mô hình "Tách biệt Trách nhiệm" (Separation of Concerns) để tiện bảo trì và nâng cấp.

## 🚀 CÁCH CHẠY ỨNG DỤNG

Để khởi chạy, hãy chạy file: `main_app.py`

## 📂 CẤU TRÚC THƯ MỤC

/DuAnXoSo ├── main_app.py <- (File chạy chính) ├── lottery_service.py <- (File "Bộ Điều Phối") ├── xo_so_prizes_all_logic.db <- (Cơ sở dữ liệu) ├── README.md <- (File tóm tắt này) | ├── /logic <- (Gói chứa TOÀN BỘ logic nghiệp vụ) │ ├── init.py │ ├── db_manager.py <- (Quản lý Database: setup, add, get...) │ ├── data_parser.py <- (Các hàm Parse JSON/Text) │ ├── bridges_classic.py <- (15 Cầu Cổ Điển & hàm hỗ trợ) │ ├── bridges_v16.py <- (Logic 107 vị trí V16) │ ├── backtester.py <- (Các hàm BACKTEST_... & TIM_CAU_...) │ └── analytics.py <- (Logic Bảng Tổng Hợp) | └── /ui <- (Gói chứa TOÀN BỘ giao diện người dùng) ├── init.py ├── ui_main_window.py <- (Cửa sổ chính của App) ├── ui_lookup.py <- (Cửa sổ "Tra Cứu") ├── ui_bridge_manager.py <- (Cửa sổ "Quản lý Cầu") ├── ui_results_viewer.py <- (Cửa sổ Bảng Kết Quả Treeview) └── ui_dashboard.py <- (MỚI: Cửa sổ "Bảng Tổng Hợp")


## 📜 MÔ TẢ LUỒNG HOẠT ĐỘNG

Hệ thống tuân thủ nghiêm ngặt luồng dữ liệu 1 chiều:

**Giao diện (`/ui`) -> Bộ Điều Phối (`lottery_service.py`) -> Logic (`/logic`)**

1.  **Giao diện (`/ui`):**
    * Chỉ chịu trách nhiệm **hiển thị** nút bấm, cửa sổ và **nhận** tương tác.
    * **Không** chứa logic nghiệp vụ.
    * Khi người dùng nhấn nút (ví dụ: "Bảng Tổng Hợp"), nó sẽ gọi 1 hàm duy nhất từ `ui_main_window.py` (ví dụ: `run_decision_dashboard()`).

2.  **Bộ Điều Phối (`lottery_service.py`):**
    * Là "cầu nối" **duy nhất** giữa Giao diện và Logic.
    * Nó `import` tất cả các hàm cần thiết từ 6 file trong gói `/logic`.
    * Nó "tái xuất" (re-export) các hàm này để các file `/ui` sử dụng.
    * Nếu một nút cần gọi 5 hàm logic, `lottery_service.py` sẽ làm việc đó, tổng hợp kết quả và trả về cho `/ui`.

3.  **Logic (`/logic`):**
    * Là "bộ não" của hệ thống, chứa toàn bộ các thuật toán tính toán.
    * `db_manager.py`: Chỉ nói chuyện với file `.db`.
    * `data_parser.py`: Chỉ xử lý file JSON/Text.
    * `bridges_classic.py` & `bridges_v16.py`: Chỉ định nghĩa các thuật toán soi cầu.
    * `backtester.py`: Chỉ chạy các vòng lặp backtest nặng.
    * `analytics.py`: Chỉ chứa các hàm thống kê (Loto về nhiều, Đếm Vote, Cầu K2N...).

## 💡 CÁCH BẢO TRÌ VÀ NÂNG CẤP (HƯỚNG DẪN)

* **Để sửa logic Cầu 5 (V5):**
    * Mở: `logic/bridges_classic.py`
    * Tìm hàm: `getCau5_...`

* **Để sửa/thêm logic Bảng Tổng Hợp (ví dụ: thêm Lô Gan):**
    * Mở: `logic/analytics.py` (Để thêm hàm `get_loto_gan(...)`)
    * Mở: `lottery_service.py` (Để `import` và "tái xuất" hàm `get_loto_gan`)
    * Mở: `ui/ui_main_window.py` (Tìm hàm `_task_run_decision_dashboard` để gọi hàm mới)
    * Mở: `ui/ui_dashboard.py` (Tìm hàm `populate_data` để hiển thị dữ liệu mới)

* **Để sửa giao diện Cửa sổ Tra Cứu:**
    * Mở: `ui/ui_lookup.py`

* **Để sửa logic Backtest K2N (ví dụ: sửa cách đếm chuỗi):**
    * Mở: `logic/backtester.py`
    * Tìm hàm: `BACKTEST_15_CAU_K2N_V30_AI_V8`

* **Để thêm Cầu Cổ Điển mới (ví dụ: Cầu 16):**
    * Mở: `logic/bridges_classic.py` (Thêm hàm `getCau16_...`)
    * Mở: `logic/backtester.py` (Thêm Cầu 16 vào hàm `BACKTEST_15_CAU...`)