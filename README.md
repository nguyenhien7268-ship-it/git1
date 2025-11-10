TỔNG QUAN HỆ THỐNG PHÂN TÍCH XỔ SỐ (V6.8 - AI, Shadow & Caching)

Đây là tài liệu tổng quan kiến trúc hệ thống, được xây dựng theo mô hình "Tách biệt Trách nhiệm" (Separation of Concerns) để tiện bảo trì và nâng cấp.

🚀 CÁCH CHẠY ỨNG DỤNG

Để khởi chạy, hãy chạy file: main_app.py

Lưu ý: Hệ thống yêu cầu các thư viện bên ngoài. Hãy đảm bảo bạn đã cài đặt chúng:

Bash



pip install scikit-learn joblib pandas

✨ TÍNH NĂNG CHÍNH (SAU NÂNG CẤP V6.8)

Hệ thống đã được nâng cấp toàn diện, tập trung vào AI, mở rộng nguồn cầu và độ tin cậy của dữ liệu:

Tích hợp AI (Học máy - V2): Thêm mô hình RandomForest (loto_model.joblib) làm nguồn dự đoán mới. Mô hình được huấn luyện từ 7 nguồn dữ liệu phân tích và cung cấp Xác suất % cho 100 lô tô.

Mở rộng Nguồn Cầu (V17/Shadow): Nâng cấp logic cầu lên V17 với khả năng dò tìm trên 214 vị trí (107 vị trí gốc + 107 vị trí bóng dương), tổng cộng hơn 23,000 cặp cầu.

Tích hợp Cầu Bạc Nhớ: Thêm 756 công thức dựa trên Tổng/Hiệu của 27 vị trí lô tô, được tích hợp vào cả quá trình dò cầu tự động và chấm điểm.

Bảng Chấm Điểm Tổng Lực (V6.8): Bảng chấm điểm cốt lõi giờ đây tích hợp và cộng điểm thưởng động cho các cặp số có Xác suất AI vượt ngưỡng (AI_PROB_THRESHOLD).

Cấu hình Linh hoạt (ConfigManager): Toàn bộ các ngưỡng quan trọng (tỷ lệ thắng, số ngày Gan, ngưỡng tự động thêm/lọc cầu, ngưỡng AI) đều được điều chỉnh dễ dàng qua file config.json và giao diện Cài đặt.

Quản lý Rủi ro K2N: Tích hợp tính toán Chuỗi Thua Max K2N và trừ điểm phạt lũy tiến (K2N_RISK_PENALTY_PER_FRAME) cho các cầu đang trong khung rủi ro.

Tối ưu hóa Hiệu suất: Cập nhật cơ chế Caching K2N hàng loạt cho cả Cầu Cổ Điển và Cầu Đã Lưu, giúp giảm thời gian backtest và cải thiện tốc độ truy vấn.

📁 CẤU TRÚC THƯ MỤC CỐT LÕI

Thư mụcFileMô tả Chi tiếtrootmain_app.pyĐiểm khởi chạy ứng dụng (Tkinter).lottery_service.pyBộ điều phối (API) giữa UI và Logic.config.jsonChứa toàn bộ các tham số cấu hình vận hành của hệ thống.logic/config_manager.pyQuản lý tải/lưu config.json và cung cấp SETTINGS (Singleton).db_manager.pyQuản lý CSDL (SQLite), xử lý KyQuay, DuLieu_AI, và ManagedBridges (bao gồm cả cache K2N).data_parser.pyXử lý và chèn dữ liệu kết quả xổ số.bridges_v16.pyĐịnh nghĩa logic 214 vị trí và Bóng Dương (V17 Shadow).bridges_classic.pyĐịnh nghĩa 15 Cầu Cổ Điển và các hàm check hit cơ bản.bridges_memory.pyĐịnh nghĩa 756 Cầu Bạc Nhớ (Tổng/Hiệu).backtester.pyChứa các thuật toán Backtest, Tự động Dò Cầu/Lọc Cầu, và Logic Chấm Điểm Tổng Lực.ml_model.pyLogic huấn luyện và dự đoán của mô hình RandomForest.ui/ui_main_window.pyLớp cửa sổ chính (Root).ui_dashboard.pyHiển thị Bảng Chấm Điểm Tổng Lực.ui_settings.pyCửa sổ điều chỉnh tất cả tham số vận hành (config.json).ui_optimizer.pyGiao diện Tab Tối ưu Hóa (cho các chức năng Tinh chỉnh và Mô phỏng).(và các file UI khác)ui_bridge_manager.py, ui_tuner.py, ui_lookup.py, ui_results_viewer.py.📜 MÔ TẢ LUỒNG HOẠT ĐỘNG (V6.8)

Hệ thống tuân thủ nghiêm ngặt luồng dữ liệu 1 chiều:

$$\text{Giao diện (/ui)} \rightarrow \text{Bộ Điều Phối (lottery\_service.py)} \rightarrow \text{Logic (/logic)}$$

Luồng Dự đoán Chuyên sâu:

Khởi tạo: Giao diện gọi hàm run_decision_dashboard() trong lottery_service.py.

Tải Cấu hình: config_manager.py tải các ngưỡng (ví dụ: AI_PROB_THRESHOLD) từ config.json.

Tính toán Nguồn Dữ liệu (backtester.py):

Thực hiện 6 phân tích truyền thống (Lô Gan, Lô Hot, Vote Cầu từ Cache, K2N Pending, Bạc Nhớ Top N).

MỚI: Gọi get_ai_predictions (từ ml_model.py) để lấy Xác suất % cho 100 lô tô.

Chấm Điểm Tổng Lực (get_top_scored_pairs):

Hàm này tổng hợp tất cả 7 nguồn dữ liệu.

Cộng điểm cho các cặp có Vote cao, Tỷ lệ thắng cao, và Xác suất AI vượt ngưỡng.

Trừ điểm (Penalty) nếu cặp đó đang nằm trong khung K2N có rủi ro cao (Chuỗi Thua Max vượt ngưỡng).

Hiển thị: Giao diện hiển thị Bảng Chấm Điểm đã được tăng cường sức mạnh bởi AI và các công cụ quản lý rủi ro.

🛠️ CÁCH BẢO TRÌ VÀ NÂNG CẤP

Hướng dẫn dành cho Developer:

Tích hợp Tính năng mới: Luôn thêm logic vào lottery_service.py trước, sau đó triển khai logic trong /logic.

Thêm Tham số Cấu hình mới:

Cập nhật self.defaults, save_settings, _update_class_attributes, và get_all_settings trong logic/config_manager.py.

Thêm trường nhập liệu tương ứng vào ui/ui_settings.py.

Huấn luyện lại AI: Nếu mô hình cần cập nhật, chạy lại hàm train_ai_model() trong ml_model.py để tạo file loto_model.joblib mới.

Cập nhật Cầu Vị Trí: Thay đổi logic định nghĩa vị trí trong bridges_v16.py hoặc thêm công thức mới vào bridges_classic.py.