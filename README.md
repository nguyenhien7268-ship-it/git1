# TỔNG QUAN HỆ THỐNG PHÂN TÍCH XỔ SỐ (V7.1 - XGBoost, Q-Features, Threading & Score Weight)

Đây là tài liệu tổng quan kiến trúc hệ thống, được xây dựng theo mô hình **"Tách biệt Trách nhiệm" (Separation of Concerns)** để tiện bảo trì và nâng cấp.

---
## 🚀 CÁCH CHẠY ỨNG DỤNG

Để khởi chạy, hãy chạy file: `main_app.py`

Lưu ý: Hệ thống yêu cầu các thư viện bên ngoài. Hãy đảm bảo bạn đã cài đặt chúng:
```bash
pip install scikit-learn joblib pandas xgboost

✨ TÍNH NĂNG CHÍNH (SAU NÂNG CẤP V7.0/V7.1)Hệ thống đã được nâng cấp toàn diện, tập trung vào AI, mở rộng nguồn cầu và độ tin cậy của dữ liệu:Tách biệt Nền tảng (V7.0 Foundation):Tạo lớp Data Repository để tách biệt hoàn toàn logic tải dữ liệu lớn ra khỏi db_manager.py, giúp dễ dàng thay đổi hệ quản trị CSDL (ví dụ: từ SQLite sang PostgreSQL) mà không ảnh hưởng đến logic AI.Áp dụng Multi-Threading trong lottery_service.py cho các tác vụ nặng như Huấn luyện AI, giúp ngăn chặn giao diện (UI) bị đóng băng (freeze).Nâng cấp Mô hình AI (V7.1 XGBoost):Chuyển từ RandomForest sang XGBoost/LightGBM (V7.1) để tăng cường độ chính xác dự đoán.Mô hình AI đã được huấn luyện lại với bộ đặc trưng làm giàu (Q-Features): bổ sung 3 chỉ số Chất lượng của Cầu (Tỷ lệ thắng trung bình, Rủi ro K2N tối thiểu, Chuỗi thắng/thua tối đa).Công cụ Quản lý Rủi ro & Chấm Điểm:Hệ thống Chấm Điểm Tổng Lực (Total Score) mới tích hợp chức năng trừ điểm (Penalty) đối với các cặp lô tô đang nằm trong khung K2N có rủi ro cao (Chuỗi Thua Max vượt ngưỡng trong lịch sử).Áp dụng công thức cộng điểm theo Trọng số AI $$\text{Score\_Tổng} = \text{Score\_Truyền\_Thống} + (\text{AI\_Probability} \times \text{AI\_WEIGHT})$$ thay vì kiểm tra ngưỡng cứng.📁 CẤU TRÚC THƯ MỤC CỐT LÕI (CẬP NHẬT SAU REFACTORING)Thư mụcFileMô tả Chi tiếtrootmain_app.pyĐiểm khởi chạy ứng dụng (Tkinter).lottery_service.pyBộ điều phối (API) giữa UI và Logic.config.jsonChứa toàn bộ các tham số cấu hình vận hành (Bổ sung AI_LEARNING_RATE, AI_OBJECTIVE, AI_SCORE_WEIGHT).data/xo_so_prizes_all_logic.db(MỚI VỊ TRÍ) File Cơ sở Dữ liệu chính (SQLite).logic/config_manager.pyQuản lý tải/lưu config.json và cung cấp SETTINGS.db_manager.pyQuản lý CSDL (SQLite), xử lý KyQuay, DuLieu_AI, và ManagedBridges.data_repository.py(MỚI) Chứa các hàm tải dữ liệu lớn từ DB.backtester.pyChứa các thuật toán Backtest, Tự động Dò Cầu/Lọc Cầu.ml_model.pyLogic huấn luyện và dự đoán của mô hình AI (XGBoost V7.1).logic/bridges/bridges_classic.py(MỚI VỊ TRÍ) Logic cầu truyền thống (V5).bridges_memory.py(MỚI VỊ TRÍ) Logic cầu Bạc Nhớ/27 vị trí lô.bridges_v16.py(MỚI VỊ TRÍ) Logic cầu V17 (Shadow) và các hàm hỗ trợ vị trí.bridge_manager_core.py(MỚI VỊ TRÍ) Logic quản lý cầu tự động (Tìm, Lọc).logic/ml_model_files/loto_model.joblib(MỚI VỊ TRÍ) Mô hình AI đã huấn luyện (XGBoost V7.1).ai_scaler.joblib(MỚI VỊ TRÍ) Bộ chuẩn hóa dữ liệu (Scaler) cho mô hình AI.ui/ui_dashboard.pyHiển thị Bảng Chấm Điểm Tổng Lực.ui_settings.pyCửa sổ điều chỉnh tất cả tham số vận hành.🔍 LUỒNG RA QUYẾT ĐỊNH SÂU (Đã cập nhật V7.1):Khởi tạo: Giao diện gọi hàm run_decision_dashboard() trong lottery_service.py.Tải Cấu hình: config_manager.py tải các ngưỡng (bao gồm AI_SCORE_WEIGHT, AI_LEARNING_RATE mới) từ config.json.Tính toán Nguồn Dữ liệu (dashboard_analytics.py/backtester.py):Thực hiện 6 phân tích truyền thống (Lô Gan, Lô Hot, Vote Cầu từ Cache, K2N Pending, Bạc Nhớ Top N).Gọi get_ai_predictions (từ ml_model.py) để lấy Xác suất % cho 100 lô tô (Sử dụng mô hình XGBoost V7.1).Chấm Điểm Tổng Lực (get_top_scored_pairs - V7.0):Hàm này tổng hợp tất cả 7 nguồn dữ liệu.Áp dụng công thức trọng số AI mới: Cộng điểm theo công thức $$\text{Score\_Tổng} = \text{Score\_Truyền\_Thống} + (\text{AI\_Probability} \times \text{AI\_WEIGHT})$$.Trừ điểm (Penalty) nếu cặp đó đang nằm trong khung K2N có rủi ro cao (Chuỗi Thua Max vượt ngưỡng).Hiển thị: Giao diện hiển thị Bảng Chấm Điểm đã được tăng cường sức mạnh bởi AI và các công cụ quản lý rủi ro.🛠️ CÁCH BẢO TRÌ VÀ NÂNG CẤPHướng dẫn dành cho Developer:Tích hợp Tính năng mới: Luôn thêm logic vào lottery_service.py trước, sau đó triển khai logic trong /logic22.Thêm Tham số Cấu hình mới: Cập nhật self.defaults, save_settings, _update_class_attributes, và get_all_settings trong logic/config_manager.py23.Huấn luyện lại AI: Nếu mô hình cần cập nhật, chạy lại hàm train_ai_model() trong ml_model.py để tạo file loto_model.joblib mới (XGBoost V7.1) (sẽ bao gồm Q-Features mới)25.
---

## 2. Các bước nâng cấp tiếp theo

Sau khi xác nhận hệ thống chạy ổn định với XGBoost V7.1 và cập nhật tài liệu, bạn cần tập trung vào Tối ưu hóa hiệu suất và hoàn tất việc tích hợp logic tính điểm.

### Bước 1: Hoàn tất Logic Chấm Điểm Tổng Lực (Phase 3) 📝

Bạn cần đảm bảo logic tính điểm cuối cùng trong hệ thống đã được cập nhật chính xác theo công thức trọng số và trừ điểm rủi ro.

**Hành động:**
1.  Mở file **`git1/logic/dashboard_analytics.py`** hoặc **`git1/logic/backtester.py`** (nơi chứa hàm `get_top_scored_pairs`).
2.  **Xác nhận/Sửa đổi** logic bên trong hàm này để:
    * Sử dụng giá trị **`AI_SCORE_WEIGHT`** mới từ `logic/config_manager.py`.
    * Áp dụng công thức cộng điểm trọng số.
    * Đảm bảo logic **Penalty K2N** (trừ điểm) vẫn hoạt động chính xác dựa trên dữ liệu rủi ro K2N.

### Bước 2: Tối ưu hóa Tham số (Hyperparameter Tuning) ⚙️

XGBoost nhạy cảm với các tham số mới. Việc tinh chỉnh sẽ trực tiếp quyết định độ chính xác cuối cùng của hệ thống.

**Hành động:**
1.  **Mở giao diện cài đặt** (`ui/ui_settings.py` hoặc `ui/ui_optimizer.py`).
2.  Tiến hành **thử nghiệm** các tổ hợp tham số mới đã được thêm vào `config.json`:
    * **`AI_MAX_DEPTH`** (Thử các giá trị thấp hơn như 3, 4, 5, 6).
    * **`AI_N_ESTIMATORS`** (Tăng số cây lên 200, 300, 400).
    * **`AI_LEARNING_RATE`** (Tinh chỉnh ở mức thấp như 0.01, 0.05, 0.1).
3.  **Lặp lại Huấn luyện:** Sau mỗi lần thay đổi các tham số trên, bạn **phải** chạy lại **Huấn luyện AI** để mô hình `.joblib` mới có hiệu lực.