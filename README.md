TỔNG QUAN HỆ THỐNG PHÂN TÍCH XỔ SỐ (V7.0 - Q-Features, Threading & Score Weight)

Đây là tài liệu tổng quan kiến trúc hệ thống, được xây dựng theo mô hình "Tách biệt Trách nhiệm" (Separation of Concerns) để tiện bảo trì và nâng cấp.

🚀 CÁCH CHẠY ỨNG DỤNG

Để khởi chạy, hãy chạy file: main_app.py

Lưu ý: Hệ thống yêu cầu các thư viện bên ngoài. Hãy đảm bảo bạn đã cài đặt chúng:

Bash



pip install scikit-learn joblib pandas

✨ TÍNH NĂNG CHÍNH (SAU NÂNG CẤP V7.0)

Hệ thống đã được nâng cấp toàn diện, tập trung vào AI, mở rộng nguồn cầu và độ tin cậy của dữ liệu:

Tách biệt Nền tảng (V7.0 Foundation):

Tạo lớp Data Repository để tách biệt hoàn toàn logic tải dữ liệu lớn ra khỏi db_manager.py, giúp dễ dàng thay đổi hệ quản trị CSDL (ví dụ: từ SQLite sang PostgreSQL) mà không ảnh hưởng đến logic AI.

Áp dụng Multi-Threading trong lottery_service.py cho các tác vụ nặng như Huấn luyện AI, giúp ngăn chặn giao diện (UI) bị đóng băng (freeze).

Tăng Cường Đặc trưng AI (V7.0 Q-Features):

Mô hình AI đã được huấn luyện lại với bộ đặc trưng làm giàu, bổ sung 3 chỉ số Chất lượng Cầu (Q-Features) mới: Average_Win_Rate (Tỷ lệ thắng trung bình), Min_K2N_Risk (Chuỗi thua Max K2N nhỏ nhất), và Current_Lose_Streak (Chuỗi thua hiện tại).

Việc bổ sung này giúp mô hình AI học được Chất lượng thay vì chỉ Số lượng cầu, tăng đáng kể độ chính xác dự đoán.

Tối Ưu Hóa Trọng số (V7.0 Scoring):

Bảng Chấm Điểm Tổng Lực được thay đổi để tích hợp kết quả AI một cách liên tục và linh hoạt hơn.

Loại bỏ logic kiểm tra ngưỡng AI cứng (AI_PROB_THRESHOLD). Thay vào đó, áp dụng công thức cộng điểm theo trọng số: 

$$\text{Total\_Score} = \text{Score\_Truyền\_Thống} + (\text{AI\_Probability} \times \text{AI\_WEIGHT})$$

Thêm tham số cấu hình AI_SCORE_WEIGHT để kiểm soát mức độ ảnh hưởng của AI lên điểm số cuối cùng.

Tính năng hiện có (V6.8):

Tích hợp AI (Học máy - V2): Mô hình RandomForest (loto_model.joblib) làm nguồn dự đoán mới1.

Mở rộng Nguồn Cầu (V17/Shadow): Khả năng dò tìm trên 214 vị trí (107 vị trí gốc + 107 vị trí bóng dương), tổng cộng hơn 23,000 cặp cầu2.

Quản lý Rủi ro K2N: Tích hợp tính toán Chuỗi Thua Max K2N và trừ điểm phạt lũy tiến (K2N_RISK_PENALTY_PER_FRAME)3.

Tối ưu hóa Hiệu suất: Cập nhật cơ chế Caching K2N hàng loạt4.

📁 CẤU TRÚC THƯ MỤC CỐT LÕI

Thư mụcFileMô tả Chi tiếtrootmain_app.pyĐiểm khởi chạy ứng dụng (Tkinter)5.

lottery_service.pyBộ điều phối (API) giữa UI và Logic6.

config.jsonChứa toàn bộ các tham số cấu hình vận hành của hệ thống7.

logic/config_manager.pyQuản lý tải/lưu config.json và cung cấp SETTINGS (Singleton)8.

db_manager.pyQuản lý CSDL (SQLite), xử lý KyQuay, DuLieu_AI, và ManagedBridges (bao gồm cả cache K2N)9.

data_repository.py(MỚI V7.0) Chứa toàn bộ các hàm tải dữ liệu lớn từ DB (ví dụ: load_data_ai_from_db), tách biệt khỏi db_manager.py.backtester.pyChứa các thuật toán Backtest, Tự động Dò Cầu/Lọc Cầu, và Logic Chấm Điểm Tổng Lực10.

ml_model.pyLogic huấn luyện và dự đoán của mô hình RandomForest11.

ui/ui_dashboard.pyHiển thị Bảng Chấm Điểm Tổng Lực12.

ui_settings.pyCửa sổ điều chỉnh tất cả tham số vận hành (config.json)13.

(và các file UI khác)

ui_bridge_manager.py, ui_tuner.py, ui_lookup.py, ui_results_viewer.py14.

📜 MÔ TẢ LUỒNG HOẠT ĐỘNG (V7.0)

Hệ thống tuân thủ nghiêm ngặt luồng dữ liệu 1 chiều:

$$\text{Giao diện (/ui)} \rightarrow \text{Bộ Điều Phối (lottery\_service.py)} \rightarrow \text{Logic (/logic)}$$

Luồng Dự đoán Chuyên sâu (Đã cập nhật V7.0):



Khởi tạo: Giao diện gọi hàm run_decision_dashboard() trong lottery_service.py15.



Tải Cấu hình: config_manager.py tải các ngưỡng (bao gồm AI_SCORE_WEIGHT mới) từ config.json16.

Tính toán Nguồn Dữ liệu (dashboard_analytics.py/backtester.py):

Thực hiện 6 phân tích truyền thống (Lô Gan, Lô Hot, Vote Cầu từ Cache, K2N Pending, Bạc Nhớ Top N)17.

Gọi get_ai_predictions (từ ml_model.py) để lấy Xác suất % cho 100 lô tô18.

Chấm Điểm Tổng Lực (get_top_scored_pairs - V7.0):

Hàm này tổng hợp tất cả 7 nguồn dữ liệu19.

Áp dụng công thức trọng số AI mới: Cộng điểm theo công thức 

$$\text{Score\_Truyền\_Thống} + (\text{AI\_Probability} \times \text{AI\_WEIGHT})$$

.

Trừ điểm (Penalty) nếu cặp đó đang nằm trong khung K2N có rủi ro cao (Chuỗi Thua Max vượt ngưỡng)20.



Hiển thị: Giao diện hiển thị Bảng Chấm Điểm đã được tăng cường sức mạnh bởi AI và các công cụ quản lý rủi ro21.

🛠️ CÁCH BẢO TRÌ VÀ NÂNG CẤP

Hướng dẫn dành cho Developer:



Tích hợp Tính năng mới: Luôn thêm logic vào lottery_service.py trước, sau đó triển khai logic trong /logic22.

Thêm Tham số Cấu hình mới:

Cập nhật self.defaults, save_settings, _update_class_attributes, và get_all_settings trong logic/config_manager.py23.

Thêm trường nhập liệu tương ứng vào ui/ui_settings.py24.



Huấn luyện lại AI: Nếu mô hình cần cập nhật, chạy lại hàm train_ai_model() trong ml_model.py để tạo file loto_model.joblib mới (sẽ bao gồm Q-Features mới)25.