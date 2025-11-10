TỔNG QUAN HỆ THỐNG PHÂN TÍCH XỔ SỐ (V6.6 - Tối ưu hóa & AI)
Đây là tài liệu tổng quan kiến trúc hệ thống, được xây dựng theo mô hình "Tách biệt Trách nhiệm" (Separation of Concerns) để tiện bảo trì và nâng cấp.

🚀 CÁCH CHẠY ỨNG DỤNG
Để khởi chạy, hãy chạy file: main_app.py

Lưu ý: Hệ thống yêu cầu các thư viện bên ngoài. Hãy đảm bảo bạn đã cài đặt chúng:

Bash

pip install scikit-learn joblib pandas
✨ TÍNH NĂNG CHÍNH (SAU NÂNG CẤP V6.6)
Hệ thống đã được nâng cấp toàn diện, tập trung vào AI và độ tin cậy của dữ liệu:

Tích hợp AI (Học máy): Thêm mô hình RandomForest (loto_model.joblib) làm nguồn dự đoán mới, được huấn luyện từ 7 nguồn dữ liệu phân tích khác nhau.

Bảng Chấm Điểm V6.6: Bảng Chấm Điểm Tổng Lực giờ đây tích hợp và cộng điểm thưởng cho các cặp số được AI dự đoán có xác suất cao.

Sửa Lỗi Dữ liệu Cốt Lõi: Khắc phục lỗi khiến 15 Cầu Cổ Điển không được cập nhật cache. 15 Cầu Cổ Điển giờ đây được tự động thêm vào CSDL và cập nhật cache K2N cùng các cầu khác.

Tối ưu hóa Giao diện: Giao diện Bảng Tổng Hợp được chia thành 2 Tab (Tổng Quan và Chi Tiết) để ưu tiên hiển thị các bảng quan trọng nhất.

Quản lý Tham số: Tất cả tham số vận hành được quản lý qua config.json và giao diện Cài đặt.

📂 CẤU TRÚC THƯ MỤC
/DuAnXoSo ├── main_app.py <- (File chạy chính) ├── lottery_service.py <- (File "Bộ Điều Phối" - API trung gian) ├── config.json <- (File Cài đặt Tham số Hệ thống) ├── loto_model.joblib <- (File "bộ não" AI đã huấn luyện) ├── xo_so_prizes_all_logic.db <- (Cơ sở dữ liệu) ├── README.md <- (File tóm tắt này) | ├── /logic <- (Gói chứa TOÀN BỘ logic nghiệp vụ) │ ├── init.py │ ├── config_manager.py <- (Quản lý đọc/ghi file config.json) │ ├── ml_model.py <- (Logic Huấn luyện & Dự đoán AI - V2 Tối ưu hóa) │ ├── db_manager.py <- (Quản lý Database: Đã sửa lỗi Cầu Cổ Điển) │ ├── data_parser.py <- (Các hàm Parse JSON/Text) │ ├── bridges_classic.py <- (15 Cầu Cổ Điển & hàm hỗ trợ) │ ├── bridges_v16.py <- (Logic 214 vị trí V17 Gốc + Bóng) │ ├── bridges_memory.py <- (Logic 756 Cầu Bạc Nhớ - Tổng/Hiệu) │ └── backtester.py <- (NÂNG CẤP: Chứa all backtest, analytics, Chấm Điểm V6.6) │ └── /ui <- (Gói chứa TOÀN BỘ file giao diện) ├── init.py ├── ui_main_window.py <- (Cửa sổ chính, quản lý các Tab) ├── ui_dashboard.py <- (Cửa sổ Bảng Tổng Hợp - Đã sửa lỗi 2 Tab/8 Bảng) ├── ui_lookup.py <- (Cửa sổ Tra Cứu Kỳ Quay) ├── ui_bridge_manager.py<- (Cửa sổ Quản lý Cầu) ├── ui_results_viewer.py<- (Cửa sổ Hiển thị Kết quả Backtest) ├── ui_settings.py <- (Cửa sổ Cài đặt Tham số) ├── ui_tuner.py <- (Cửa sổ Trợ lý Tinh chỉnh) └── ui_optimizer.py <- (Giao diện Tab Tối ưu Hóa)

📜 MÔ TẢ LUỒNG HOẠT ĐỘNG (V6.6)
Hệ thống tuân thủ nghiêm ngặt luồng dữ liệu 1 chiều, với các bước bổ sung:

Giao diện (/ui) -> Bộ Điều Phối (lottery_service.py) -> Logic (/logic)

Dự đoán Chuyên sâu: Giao diện gọi run_decision_dashboard().

Logic Chấm Điểm (backtester.py):

Thực hiện 6 phân tích truyền thống (Lô Gan, Vote, K2N, Bạc Nhớ...).

MỚI: Gọi get_ai_predictions (từ ml_model.py) để lấy Xác suất % cho 100 loto.

Hàm get_top_scored_pairs sử dụng 6 nguồn truyền thống VÀ Xác suất AI để tính điểm cuối cùng (Chấm Điểm Tổng Lực).

Hiển thị: Giao diện hiển thị Bảng Chấm Điểm đã được tăng cường sức mạnh bởi AI.

🛠️ CÁCH BẢO TRÌ VÀ NÂNG CẤP (HƯỚNG DẪN)
Để sửa logic Chấm Điểm (Bao gồm AI):

Mở: logic/backtester.py

Tìm hàm: get_top_scored_pairs (Logic cộng điểm AI được thêm vào hàm này).

Để Huấn luyện lại Mô hình AI:

Mở: logic/ml_model.py

Tìm hàm: train_ai_model (Sử dụng code V2 - Tối ưu hóa để đảm bảo tốc độ).

Để sửa logic Dò Cầu Bạc Nhớ/V17:

Mở: logic/backtester.py

Tìm hàm: TIM_CAU_TOT_NHAT_V16 (V17) hoặc TIM_CAU_BAC_NHO_TOT_NHAT (Bạc Nhớ).

Để sửa lỗi dữ liệu Cầu Cổ Điển:

Mở: logic/db_manager.py

Xem hàm: setup_database (Nơi 15 cầu được tự động thêm vào).