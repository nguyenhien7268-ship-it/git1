# 📘 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG (USER GUIDE)

> **Hệ thống:** XS-DAS V7.9 (Phiên bản Quản Lý Cầu Tự Động)
> **Đối tượng:** Người sử dụng (User/Analyst)
> **Mục đích:** Hướng dẫn vận hành các chức năng từ cơ bản đến nâng cao để chốt số hiệu quả.

---

## 📑 MỤC LỤC
1. [Tổng Quan Các Chức Năng](#1-tổng-quan-các-chức-năng)
2. [Quy Trình Soi Cầu Lô (Hàng Ngày)](#2-quy-trình-soi-cầu-lô-hàng-ngày)
3. [Quy Trình Soi Cầu Đề (V7.7 Mới)](#3-quy-trình-soi-cầu-đề-v77-mới)
4. [Quản Lý Dữ Liệu & Hệ Thống](#4-quản-lý-dữ-liệu--hệ-thống)
5. [Tính Năng Mới V7.9: Quản Lý Cầu Tự Động](#5-tính-năng-mới-v79-quản-lý-cầu-tự-động)

---

## 1. TỔNG QUAN CÁC CHỨC NĂNG

Hệ thống được chia làm 2 phân hệ chính hoạt động độc lập:

### 🅰️ PHÂN HỆ LÔ (Decision Dashboard)
Tập trung vào việc tìm ra cặp Song Thủ Lô (STL) hoặc Bạch Thủ Lô (BTL) có xác suất thắng cao nhất.

* **Bảng Quyết Định (Scoring):** Tự động chấm điểm các cặp số dựa trên AI, Vote và Cầu chạy.
* **Cảnh Báo Rủi Ro:** Phát hiện cầu hay gãy, cầu gan để trừ điểm.
* **AI Dự Đoán:** Sử dụng Machine Learning (XGBoost) để tham vấn độc lập.

### 🅱️ PHÂN HỆ ĐỀ (Special Prize Dashboard) - **NEW V7.7**
Tập trung vào việc lọc số (Filtering) để tạo ra dàn đề tối ưu.

* **Quét Cầu Đa Chiều:** Tự động tìm Cầu Chạm, Cầu Tổng, Cầu Bộ đang thông.
* **Thống Kê Thông Minh:** Sắp xếp Chạm/Tổng theo độ Gan (độ lì) tăng dần.
* **Phễu Lọc 3 Lớp:** Tự động tạo Dàn 65 số -> Lọc Top 10 -> Chốt Top 4.

---

## 2. QUY TRÌNH SOI CẦU LÔ (HÀNG NGÀY)

**Bước 1: Cập nhật dữ liệu**
* Vào Tab `Điều Khiển` -> Nhập kết quả mới nhất vào ô Text -> Bấm `⚡ Cập Nhật Ngay`.
* Bấm `Cập nhật Cache K2N` để hệ thống tính toán lại các cầu.

**Bước 2: Xem Bảng Quyết Định**
* Chuyển sang Tab `Bảng Quyết Định`.
* Bấm nút `Làm Mới Dữ Liệu`.
* **Cách đọc bảng:**
    * **Cột Điểm (Score):** Càng cao càng tốt (Thường > 7.0 là đẹp).
    * **Cột AI:** Nếu có biểu tượng 🤖 và % cao (>70%) là tín hiệu tốt.
    * **Cột Khuyến Nghị:**
        * <span style="color:green">**CHƠI**</span>: Điểm cao + Nhiều cầu báo + AI ủng hộ.
        * <span style="color:orange">**XEM XÉT**</span>: Điểm khá nhưng có chút rủi ro.
        * <span style="color:gray">**BỎ QUA**</span>: Điểm thấp hoặc đang dính Gan/Gãy.

**Bước 3: Kiểm tra chéo (Cross-Check)**
* Nhìn sang bảng `🔥 Thông 10 Kỳ`: Xem cầu nào đang chạy "bon" (thắng > 6/10 ngày).
* Nhìn sang bảng `⏳ Cầu K2N Chờ`: Xem có cầu nào đang nổ N1 xịt, chờ N2 không (thường N2 dễ nổ).

---

## 3. QUY TRÌNH SOI CẦU ĐỀ (V7.7 MỚI)

Đây là quy trình 3 bước chuẩn để bắt Đề:

### Bước 1: Phân Tích Thị Trường (Tab `Thống Kê`)
* Bấm nút `🔄 1. Phân Tích Thị Trường`.
* **Xem Tab "Chạm" & "Tổng":**
    * Hệ thống đã sắp xếp theo **Gan Tăng Dần**.
    * Chú ý các con ở đầu bảng (Màu xanh): Đây là các Chạm/Tổng hay về gần đây -> Dễ bệt lại.
    * Tránh các con ở cuối bảng (Màu đỏ): Đây là Chạm/Tổng đang gan lì -> Rủi ro cao.

### Bước 2: Quét Cầu & Chấm Điểm (Tab `Cầu Chạy`)
* Bấm nút `🔍 2. Quét Cầu & Chấm Điểm`.
* Hệ thống sẽ chạy ngầm (mất khoảng 3-5 giây) để quét hàng nghìn vị trí tạo cầu.
* Sau khi xong, bạn sẽ thấy:
    * **Cột Giữa:** Danh sách các cầu đang thông (Streak > 3 ngày).
    * **Gợi ý:** Nhìn xem có nhiều cầu báo về cùng 1 Chạm hoặc 1 Bộ nào không? (Hiệu ứng đám đông).

### Bước 3: Chốt Số (Tab `Dự Đoán`)
* Hệ thống tự động tính toán và đưa ra 3 phương án ở Cột Phải:
    * **Tab Dàn 65:** Dành cho người chơi nuôi, đánh web (tỷ lệ trúng ~90%).
    * **Tab Top 10:** Dành cho người đánh trà đá, văn nghệ. **Lưu ý:** Dàn này được lọc kỹ dựa trên các **Bộ Số** đang có cầu chạy.
    * **Tab Top 4 (Tứ Thủ):** 4 con số tinh túy nhất.
* **Thao tác:** Bấm `📋 Copy Dàn Đang Xem` để lấy số mang đi đánh.

### 💡 Mẹo Nâng Cao: Tạo Dàn Thủ Công
* Nếu bạn có "Tiếng Kết" riêng (Ví dụ: Mơ thấy Chạm 5), hãy dùng công cụ ở góc trên bên phải.
* Nhập `5` vào ô `Nhập Chạm` -> Bấm `⚡ Tạo Dàn`.
* Hệ thống sẽ sinh ra dàn 19 số chạm 5 cho bạn copy.

---

## 4. QUẢN LÝ DỮ LIỆU & HỆ THỐNG

### Nạp Dữ Liệu (Import)
* Hỗ trợ file `.txt` hoặc `.json`.
* Cấu trúc file text chuẩn: `Ngày (DD/MM/YYYY) - Mã Kỳ - Giải ĐB - Giải Nhất - ... - Giải 7`.
* **Lưu ý:** Nên dùng chức năng `Nạp Thêm (Append)` thay vì `Xóa Hết` để giữ lại các cầu đã lưu.

### Huấn Luyện AI
* Vào Tab `Điều Khiển` -> Bấm `🧠 Huấn luyện AI`.
* Thực hiện định kỳ **1 tuần/lần** hoặc khi thấy AI dự đoán kém đi.
* Quá trình này giúp AI học các quy luật mới nhất của nhà đài.

### Quản Lý Cầu (Bridge Manager)
* Vào Tab `Điều Khiển` -> Bấm `Quản lý Cầu (V17)`.
* Tại đây bạn có thể:
    * Xóa các cầu cũ không còn hiệu quả.
    * Thêm cầu mới bằng tay (nếu bạn biết vị trí).
    * Bật chức năng `Tự động Lọc/Tắt` để hệ thống tự dọn dẹp cầu rác.

---

## 5. TÍNH NĂNG MỚI V7.9: QUẢN LÝ CẦU TỰ ĐỘNG

Phiên bản V7.9 giới thiệu hệ thống quản lý cầu tự động với 3 tính năng chính:

### 🔍 Double-Click Backtest (Xem Lịch Sử 30 Ngày)

**Mục đích:** Kiểm tra hiệu quả của cầu trước khi quyết định chơi.

**Cách sử dụng:**
1. Vào Tab `Soi Cầu Đề` hoặc `Quản lý Cầu`.
2. Tìm cầu bạn muốn kiểm tra trong bảng danh sách.
3. **Double-click** (click đúp) vào tên cầu.
4. Một cửa sổ popup sẽ hiển thị:
   - **30 ngày lịch sử** backtest của cầu đó
   - **Tỷ lệ thắng** (Ví dụ: "Thắng 18/30 ngày (60%)")
   - **Chi tiết từng ngày:** Ngày, Dự Đoán, Kết Quả, Trạng Thái (Ăn/Gãy)
   - **Màu sắc:** Dòng thắng màu xanh, dòng thua màu đỏ

**Lưu ý:**
- Tính năng này hoạt động cho cả **Cầu Lô** và **Cầu Đề**.
- Backtest chạy trong luồng nền, không làm đơ giao diện.

### 📌 Ghim Cầu (Pin) - Bảo Vệ Cầu Quan Trọng

**Mục đích:** Bảo vệ các cầu quan trọng khỏi bị tự động loại bỏ bởi hệ thống Pruning.

**Cách sử dụng:**
1. Vào Tab `Quản lý Cầu (V17)`.
2. Tìm cầu bạn muốn ghim trong danh sách.
3. **Click đúp** vào tên cầu (hoặc sử dụng menu context nếu có).
4. Cầu sẽ được đánh dấu là **"Đã ghim"** (is_pinned = 1).
5. Cầu đã ghim sẽ:
   - ✅ **KHÔNG bị** tự động vô hiệu hóa bởi Pruning
   - ✅ **KHÔNG bị** tự động BẬT/TẮT bởi Auto Manage
   - ✅ **Được bảo vệ** hoàn toàn khỏi các tác vụ tự động hóa

**Bỏ ghim:**
- Click đúp lại vào cầu đã ghim để bỏ ghim.

**Lưu ý:**
- Tính năng này rất hữu ích khi bạn có cầu "tủ" mà không muốn hệ thống tự động xóa.
- Cầu đã ghim vẫn có thể được xóa thủ công nếu cần.

### ✂️ Loại Bỏ Tự Động (Pruning) - Tự Động Xóa Cầu Yếu

**Mục đích:** Tự động loại bỏ các cầu Đề có rủi ro lịch sử cao (chuỗi gãy quá dài).

**Cách kích hoạt:**
1. Vào Tab `Điều Khiển`.
2. Tìm nút **"Loại Bỏ Cầu Đề Yếu"** (hoặc tương tự).
3. Click để chạy tác vụ.

**Logic hoạt động:**
- Hệ thống sẽ:
  1. Lấy tất cả cầu Đề từ database.
  2. Tính toán **chuỗi Gãy Lâu Nhất (Max Lose Streak)** cho mỗi cầu.
  3. So sánh với **ngưỡng** (mặc định: 20 ngày, có thể cấu hình trong `config.json`).
  4. Nếu `Max Lose > Ngưỡng`: Tự động vô hiệu hóa cầu (is_enabled = 0).
  5. **Bỏ qua** các cầu đã ghim (is_pinned = 1).

**Cấu hình:**
- Ngưỡng mặc định: `DE_MAX_LOSE_THRESHOLD = 20` (trong `config.json`).
- Có thể điều chỉnh theo nhu cầu (ví dụ: 15 ngày cho chặt chẽ hơn, 30 ngày cho lỏng hơn).

**Lưu ý:**
- Tính năng này chỉ áp dụng cho **Cầu Đề** (DE_POS, DE_DYN).
- Cầu đã ghim sẽ **KHÔNG bị** ảnh hưởng.
- Tác vụ chạy trong luồng nền, không làm đơ giao diện.
- Kết quả sẽ được hiển thị trong log (ví dụ: "Đã vô hiệu hóa 3 cầu Đề (Max Lose > 20 ngày)").

---

*Tài liệu hướng dẫn nội bộ - Vui lòng không chia sẻ ra ngoài.*
