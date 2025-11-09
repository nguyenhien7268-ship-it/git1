# TỔNG QUAN HỆ THỐNG PHÂN TÍCH XỔ SỐ (V4.2 - V17 & Bạc Nhớ)

Đây là tài liệu tóm tắt kiến trúc hệ thống, được xây dựng theo mô hình "Tách biệt Trách nhiệm" (Separation of Concerns) để tiện bảo trì và nâng cấp.

## 🚀 CÁCH CHẠY ỨNG DỤNG

Để khởi chạy, hãy chạy file: `main_app.py`

## 📂 CẤU TRÚC THƯ MỤC

/DuAnXoSo
├── main_app.py <- (File chạy chính)
├── lottery_service.py <- (File "Bộ Điều Phối")
├── xo_so_prizes_all_logic.db <- (Cơ sở dữ liệu)
├── README.md <- (File tóm tắt này)
|
├── /logic <- (Gói chứa TOÀN BỘ logic nghiệp vụ)
│   ├── __init__.py
│   ├── db_manager.py <- (Quản lý Database: setup, add, get, upsert...)
│   ├── data_parser.py <- (Các hàm Parse JSON/Text)
│   ├── bridges_classic.py <- (15 Cầu Cổ Điển & hàm hỗ trợ)
│   ├── bridges_v16.py <- (NÂNG CẤP: Logic 214 vị trí V17 Gốc + Bóng)
│   ├── bridges_memory.py <- (MỚI: Logic 756 Cầu Bạc Nhớ - Tổng/Hiệu 27 Lô)
│   └── backtester.py <- (NÂNG CẤP: Backtest, Dò cầu & Logic Bảng Tổng Hợp)
|
└── /ui <- (Gói chứa TOÀN BỘ giao diện người dùng)
    ├── __init__.py
    ├── ui_main_window.py <- (Cửa sổ chính của App)
    ├── ui_lookup.py <- (Cửa sổ "Tra Cứu")
    ├── ui_bridge_manager.py <- (Cửa sổ "Quản lý Cầu")
    ├── ui_results_viewer.py <- (Cửa sổ Bảng Kết Quả Treeview)
    └── ui_dashboard.py <- (MỚI: Cửa sổ "Bảng Tổng Hợp")


## 📜 MÔ TẢ LUỒNG HOẠT ĐỘNG

Hệ thống tuân thủ nghiêm ngặt luồng dữ liệu 1 chiều:

**Giao diện (`/ui`) -> Bộ Điều Phối (`lottery_service.py`) -> Logic (`/logic`)**

1.  **Giao diện (`/ui`):**
    * Chỉ chịu trách nhiệm **hiển thị** nút bấm, cửa sổ và **nhận** tương tác.
    * **Không** chứa logic nghiệp vụ.
    * Khi người dùng nhấn nút (ví dụ: "Bảng Tổng Hợp"), nó sẽ gọi 1 hàm duy nhất từ `ui_main_window.py` (ví dụ: `run_decision_dashboard()`).

2.  **Bộ Điều Phối (`lottery_service.py`):**
    * Là "cầu nối" **duy nhất** giữa Giao diện và Logic.
    * Nó `import` tất cả các hàm cần thiết từ các file trong gói `/logic`.
    * Nó "tái xuất" (re-export) các hàm này để các file `/ui` sử dụng.
    * Nếu một nút cần gọi 5 hàm logic, `lottery_service.py` sẽ làm việc đó, tổng hợp kết quả và trả về cho `/ui`.

3.  **Logic (`/logic`):**
    * Là "bộ não" của hệ thống, chứa toàn bộ các thuật toán tính toán.
    * `db_manager.py`: Chỉ nói chuyện với file `.db` (CRUD).
    * `data_parser.py`: Chỉ xử lý file JSON/Text.
    * `bridges_classic.py`: Định nghĩa 15 Cầu Cổ Điển.
    * `bridges_v16.py`: (NÂNG CẤP) Định nghĩa 214 vị trí V17 (Gốc + Bóng) và hàm hỗ trợ.
    * `bridges_memory.py`: (MỚI) Định nghĩa 27 vị trí Lô và 756 thuật toán Cầu Bạc Nhớ (Tổng/Hiệu).
    * `backtester.py`: (NÂNG CẤP) Chứa toàn bộ các hàm backtest nặng (15 Cầu, V17, Bạc Nhớ) VÀ các hàm logic thống kê cho Bảng Tổng Hợp (Lô Gan, Chấm Điểm, v.v.).

## 💡 CÁCH BẢO TRÌ VÀ NÂNG CẤP (HƯỚNG DẪN)

* **Để sửa logic Cầu 5 (Cổ điển):**
    * Mở: `logic/bridges_classic.py`
    * Tìm hàm: `getCau5_...`

* **Để sửa/thêm logic Bảng Tổng Hợp (ví dụ: thêm Lô Gan):**
    * Mở: `logic/backtester.py` (Tìm hàm `get_loto_gan_stats(...)`)
    * Mở: `lottery_service.py` (Để `import` và "tái xuất" hàm nếu là hàm mới)
    * Mở: `ui/ui_main_window.py` (Tìm hàm `_task_run_decision_dashboard` để gọi logic mới)
    * Mở: `ui/ui_dashboard.py` (Tìm hàm `populate_data` để hiển thị dữ liệu mới)

* **Để sửa logic Chấm Điểm của Bảng Tổng Hợp:**
    * Mở: `logic/backtester.py`
    * Tìm hàm: `get_top_scored_pairs`

* **Để sửa logic Dò Cầu V17 (23.005 cầu):**
    * Mở: `logic/bridges_v16.py` (Sửa logic lấy 214 vị trí tại `getAllPositions_V17_Shadow`)
    * Mở: `logic/backtester.py` (Sửa logic backtest tại `TIM_CAU_TOT_NHAT_V16`)

* **Để sửa logic Dò Cầu Bạc Nhớ (756 cầu):**
    * Mở: `logic/bridges_memory.py` (Sửa logic lấy 27 lô tại `get_27_loto_positions` hoặc sửa thuật toán `calculate_bridge_stl`)
    * Mở: `logic/backtester.py` (Sửa logic backtest tại `BACKTEST_MEMORY_BRIDGES`)

* **Để sửa logic Dò Cầu Tự Động (Auto Find/Prune):**
    * Mở: `logic/backtester.py`
    * Tìm hàm: `find_and_auto_manage_bridges` hoặc `prune_bad_bridges`