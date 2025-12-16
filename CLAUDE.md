# Kế Hoạch Tái Cấu Trúc Code - Giai đoạn 1

📝 Kế Hoạch Chi Tiết: Phase 1 - Refactor Code Trùng Lặp

Mục tiêu: Loại bỏ ít nhất 50% code trùng lặp, tạo module utilities chung, và chuẩn hóa cấu trúc Backtester/Analytics trong vòng 2-3 ngày làm việc.

Bước 1: Chuẩn bị Môi trường và Kiểm tra Cơ sở (4 Giờ)

TaskHành động (Gemini Pro Planning)Lý do1.1Xác nhận trạng thái Test: Chạy toàn bộ bộ test hiện có (pytest -v) để đảm bảo không có lỗi nền trước khi refactor.Refactoring là một hoạt động rủi ro. Cần một lưới an toàn (passing tests).1.2Cài đặt Tools: Đảm bảo các công cụ định dạng code đã sẵn sàng: pip install black isort.Đảm bảo tính nhất quán của code sau refactor.Bước 2: Tạo Module Utilities Chung (logic/common_utils.py) (1 Ngày)

Mục tiêu: Hợp nhất các hàm tiện ích nhỏ, lặp lại để tạo Single Source of Truth.

TaskFile thay đổiChi tiết thực thi (cho AGENT)2.1logic/common_utils.py (NEW)Tạo file mới. Di chuyển và hợp nhất các hàm sau từ các module khác vào đây: 



 - Các hàm thao tác date/time. 



 - Các hàm validation đơn giản (ví dụ: is_valid_loto, is_valid_ky). 



 - Các đoạn code tạo DB queries lặp lại.

2.28-10 Files (bao gồm db_manager.py, data_parser.py, validators.py)Cập nhật Import: Thay thế các hàm đã di chuyển bằng from logic.common_utils import ....Bước 3: Tái cấu trúc Module Backtester (1 Ngày)

Mục tiêu: Giảm độ phức tạp, hợp nhất 4 file Backtester thành 2 hoặc 3 file có cấu trúc rõ ràng hơn.

TaskFile thay đổiChi tiết thực thi (cho AGENT)3.1logic/backtester_helpers.py (DELETE)Di chuyển tất cả các hàm helper trong file này vào logic/backtester_core.py hoặc logic/common_utils.py (tùy theo chức năng), sau đó xóa file backtester_helpers.py.3.2logic/backtester_core.py (REFACTOR)Refactor sang Class-based: Chuyển đổi logic chính trong file này thành một lớp BacktesterCore (hoặc tương tự) để sử dụng inheritance và quản lý trạng thái tốt hơn.3.3logic/backtester_aggregation.py, logic/backtester_scoring.pyCập nhật các file này để import và sử dụng cấu trúc Class mới từ backtester_core.py. Loại bỏ bất kỳ logic tính toán trùng lặp nào bằng cách gọi các phương thức trong BacktesterCore.Bước 4: Hợp nhất Logic Analytics (4 Giờ)

Mục tiêu: Giải quyết code trùng lặp và kích thước file lớn trong dashboard_analytics.py (1,069 dòng).

TaskFile thay đổiChi tiết thực thi (cho AGENT)4.1logic/dashboard_analytics.py (REFACTOR)Phân tích các hàm tính toán metrics/statistical trong file này và di chuyển các hàm có thể chia sẻ (ví dụ: tính tỷ lệ thắng, chuỗi liên tiếp) sang logic/analytics.py.4.2logic/analytics.py (UPDATE)Thiết lập lớp AnalyticsBase (nếu cần) hoặc thêm các hàm tính toán dùng chung để các module khác có thể import.Bước 5: Khử trùng lặp Code UI (4 Giờ)

Mục tiêu: Giảm code lặp lại trong các lớp UI (event handlers, table operations).

TaskFile thay đổiChi tiết thực thi (cho AGENT)5.1ui/ui_base.py (NEW)Tạo file mới. Định nghĩa lớp BaseToplevelWindow hoặc BaseFrame chứa: 



 - Các hàm xử lý sự kiện chung (ví dụ: _on_button_click, _handle_validation_error). 



 - Logic chung cho việc cập nhật Treeview/Table.

5.2ui/ui_main_window.py, ui/ui_dashboard.py, ui/ui_settings.pyCập nhật các lớp UI này để kế thừa từ BaseToplevelWindow hoặc BaseFrame mới, và loại bỏ các phương thức trùng lặp.Bước 6: Kiểm tra và Định dạng (2 Giờ)

TaskHành động (Gemini Pro Planning)Lý do6.1Chạy lại Test: Chạy lại toàn bộ bộ test (pytest -v) để đảm bảo không có lỗi logic do việc di chuyển file/hàm.Xác nhận rằng chức năng cốt lõi không bị hỏng.6.2Auto-Format: Chạy black . và isort . trên toàn bộ codebase.Đảm bảo phong cách code thống nhất sau khi tái cấu trúc.

Kỳ vọng Thành công (Success Criteria):

File logic/backtester_helpers.py được xóa.

Tất cả các module đã được cập nhật import.

Tất cả các bài kiểm tra đều vượt qua.

Tổng số dòng code Python giảm đáng kể (ước tính -1,000 LOC).