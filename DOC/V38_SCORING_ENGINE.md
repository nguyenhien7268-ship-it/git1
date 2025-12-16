# HỆ THỐNG CHẤM ĐIỂM THÔNG MINH (SCORING ENGINE V3.8)

## 1. Tổng Quan
Phiên bản V3.8 đánh dấu bước chuyển mình quan trọng của hệ thống: từ "Dò Cầu" (Bridge Finding) đơn thuần sang "Chấm Điểm Đa Chiều" (Multi-dimensional Scoring). Hệ thống không chỉ tìm cầu mà còn đánh giá chất lượng cầu dựa trên bối cảnh thị trường (Gan, Tần suất, Bạc nhớ) để đưa ra quyết định "xuống tiền" chính xác hơn.

## 2. Công Thức Cốt Lõi (The Formula)
Điểm số (Score) của mỗi con số (Lô/Đề) được tính toán tự động theo công thức:

$$\text{Final Score} = \text{Attack} - \text{Defense} + \text{Bonus}$$

### A. Attack (Sức Mạnh Tấn Công - Cầu)
Đại diện cho lực đẩy từ các cầu đang chạy ổn định.
- **Nguồn dữ liệu:** Bảng `ManagedBridges` (Cầu K2N, Cầu Vị Trí, Pascal, Dynamic...).
- **Công thức tính:** > `Score += (Streak * 1.0) + (WinRate / 20.0)`
- **Ý nghĩa:** - Cầu càng thông (Streak cao) -> Điểm càng lớn.
  - Tỷ lệ thắng (WinRate) cao -> Điểm thưởng thêm.

### B. Defense (Hệ Thống Phòng Thủ - Killer)
Đại diện cho rủi ro cần tránh, đóng vai trò như "tấm khiên" bảo vệ người chơi khỏi các số xấu.
- **Nguồn dữ liệu:** Thống kê Lô Gan (`gan_stats`).
- **Cơ chế Phạt (Penalty):**
  - **Gan 10-15 ngày:** Phạt nhẹ (**-2 điểm**) -> Cảnh báo.
  - **Gan 15-25 ngày:** Phạt vừa (**-5 điểm**) -> Khuyên bỏ.
  - **Gan > 25 ngày:** Phạt nặng (**-15 điểm**) -> Loại bỏ hoàn toàn khỏi Top 10.

### C. Bonus (Điểm Thưởng Xu Hướng)
Đại diện cho sự ủng hộ của xác suất thống kê và dữ liệu lớn.
- **Tần Suất (Frequency):** Số về nhiều trong 30 ngày qua (Hot Trend) được cộng tối đa **+3.0 điểm**.
- **Bạc Nhớ (Memory):** Nếu số khớp với mẫu hình Bạc Nhớ (Confidence cao), được cộng thêm điểm theo công thức: `Confidence / 10` (Ví dụ: Tin cậy 80% -> +8 điểm).

## 3. Cải Tiến Kỹ Thuật (Architecture & Robustness)
Phiên bản V3.8 giải quyết triệt để các vấn đề ổn định của phiên bản trước:

1.  **Direct SQL Connection (Kết nối trực tiếp):** - Module `AnalysisService` giờ đây sử dụng kết nối SQLite trực tiếp để lấy dữ liệu cầu.
    - **Lợi ích:** Loại bỏ hoàn toàn lỗi "Circular Import" (Vòng lặp nhập khẩu) từng gây crash ứng dụng.

2.  **Smart Polling (Cơ chế Chờ Thông Minh):**
    - UI Dashboard không còn báo lỗi "Chưa có dữ liệu" khi Database tải chậm.
    - Hệ thống tự động kiểm tra dữ liệu mỗi 0.5s (Timeout lên tới 30s) trước khi chạy phân tích.

3.  **Real-time Scoring:**
    - Điểm số được tính toán lại ngay lập tức mỗi khi người dùng bấm "Làm Mới Dữ Liệu", đảm bảo kết quả luôn là mới nhất (Real-time).