# Hướng Dẫn Kiểm Tra Hệ Thống (Testing Guide)

## Tổng Quan

Tài liệu này hướng dẫn cách kiểm tra toàn bộ hệ thống sau khi nâng cấp Phase 1, 2 và 3.

---

## Phase 1: Kiểm Tra Kích Hoạt Cầu Real-time

### Test 1.1: Kích Hoạt Cầu Đơn Lẻ

**Mục tiêu:** Kiểm tra việc kích hoạt một cầu và tính toán metrics

**Các bước:**

1. Mở **Bridge Manager** (Quản lý Cầu)
2. Tìm một cầu đang TẮT (is_enabled=0)
3. Chọn cầu đó và nhấn nút **"Cập Nhật"**
4. Kiểm tra Log Window

**Kết quả mong đợi:**
```
>>> [ACTIVATE] Bắt đầu kích hoạt và tính toán 1 cầu...
>>> [ACTIVATE] Đã tải 150 kỳ dữ liệu.
  ✅ Cầu 'TênCầu': 45.23%, Streak: 3, Prediction: 12,34
>>> [ACTIVATE] Hoàn tất: Đã kích hoạt và cập nhật 1 cầu.
```

**Kiểm tra thêm:**
- Xem trong bảng Bridge Manager, cầu đã chuyển sang trạng thái BẬT
- Win Rate và Prediction đã được cập nhật
- UI không bị đóng băng trong quá trình tính toán

### Test 1.2: Kích Hoạt Nhiều Cầu (Batch)

**Các bước:**

1. Trong Bridge Manager, chọn **NHIỀU cầu** (giữ Ctrl + Click)
2. Nhấn **"Cập Nhật"**
3. Xem dialog xuất hiện

**Kết quả mong đợi:**
- Dialog: "Đang kích hoạt và tính toán lại [n] cầu trong nền. Vui lòng đợi kết quả trong log."
- Log hiển thị tiến trình cho từng cầu
- UI vẫn phản hồi (có thể thao tác khác)

### Test 1.3: Kiểm Tra Background Thread

**Các bước:**

1. Kích hoạt 5-10 cầu cùng lúc
2. Ngay lập tức chuyển sang tab khác (Dashboard, Settings)
3. Quan sát UI

**Kết quả mong đợi:**
- UI không bị lag hay freeze
- Có thể thao tác bình thường trong các tab khác
- Log cập nhật trong nền
- Sau vài giây, nhận được thông báo hoàn tất

---

## Phase 2: Kiểm Tra Smart Scanner (Hồi Sinh Cầu)

### Test 2.1: Chuẩn Bị Test Case

**Các bước chuẩn bị:**

1. Vào Bridge Manager
2. Chọn 2-3 cầu đang BẬT
3. Tắt các cầu này (set is_enabled=0)
4. Ghi nhớ tên các cầu đã tắt

### Test 2.2: Chạy Scanner (Dò Tìm Cầu)

**Các bước:**

1. Vào menu **"Dò Tìm Cầu"** hoặc **"Auto Scanner"**
2. Chọn loại cầu cần dò (Lô hoặc Đề)
3. Nhấn **"Start Scan"**
4. Quan sát Log

**Kết quả mong đợi:**
```
[Phase 2] Reviving disabled bridge: TênCầuĐãTắt
>>> [ACTIVATE] Bắt đầu kích hoạt và tính toán 1 cầu...
[Phase 2] ✅ Revived Bridge: TênCầuĐãTắt
```

**Kiểm tra thêm:**
- Vào Bridge Manager, cầu đã được BẬT lại tự động
- Win Rate, Streak, Prediction đã được cập nhật
- Không có cầu trùng lặp mới được tạo

### Test 2.3: Kiểm Tra Không Ảnh Hưởng Cầu Đang Bật

**Các bước:**

1. Đảm bảo có nhiều cầu đang BẬT
2. Chạy Scanner lại
3. Kiểm tra Log

**Kết quả mong đợi:**
- Không có log "[Phase 2] Reviving..." cho cầu đang BẬT
- Scanner bỏ qua các cầu đang hoạt động (theo thiết kế)
- Chỉ tìm và thêm cầu mới hoặc hồi sinh cầu TẮT

---

## Phase 3: Kiểm Tra Dashboard Protection (Bảo Vệ Dự Đoán)

### Test 3.1: Kiểm Tra Trạng Thái Bình Thường

**Các bước:**

1. Mở **Dashboard** tab
2. Quan sát header (dòng tiêu đề)

**Kết quả mong đợi:**
- KHÔNG có cảnh báo màu cam
- Dashboard hiển thị bình thường
- Tất cả dự đoán được hiển thị đầy đủ

### Test 3.2: Kích Hoạt Cầu và Xem Cảnh Báo

**Các bước:**

1. Mở Bridge Manager trong tab
2. Kích hoạt 3-5 cầu cùng lúc
3. **NGAY LẬP TỨC** chuyển sang Dashboard tab
4. Nhấn nút **"Làm Mới Dữ Liệu"** trong Dashboard

**Kết quả mong đợi:**
```
⚠️ Hệ thống đang cập nhật dữ liệu cho 3 cầu. Kết quả dự đoán có thể thay đổi.
```
- Cảnh báo màu **CAM/VÀNG** xuất hiện
- Số lượng cầu [n] chính xác
- Dashboard vẫn hoạt động nhưng hiển thị cảnh báo

### Test 3.3: Kiểm Tra Cảnh Báo Tự Động Biến Mất

**Các bước:**

1. Đợi vài giây (cho việc tính toán hoàn tất)
2. Nhấn **"Làm Mới Dữ Liệu"** lại
3. Quan sát header

**Kết quả mong đợi:**
- Cảnh báo **BIẾN MẤT** (text trống)
- Dashboard về trạng thái bình thường
- Dự đoán hiển thị đầy đủ với dữ liệu mới

### Test 3.4: Kiểm Tra Dữ Liệu An Toàn

**Mục tiêu:** Xác minh Dashboard chỉ dùng dữ liệu hoàn chỉnh

**Phương pháp kiểm tra (Advanced):**

Nếu có kiến thức code, có thể test thêm:

```python
# Trong Python console hoặc test script
from services.bridge_service import get_syncing_bridges_count, SYNCING_BRIDGES
from logic.dashboard_analytics import get_safe_prediction_bridges

# Khi KHÔNG có cầu đang sync
print(get_syncing_bridges_count())  # Kỳ vọng: 0

# Khi CÓ cầu đang sync (trong lúc activate)
# (Cần chạy activate trong thread khác)
# Kỳ vọng: > 0
```

---

## Kiểm Tra Toàn Diện (End-to-End Testing)

### Scenario 1: Quy Trình Hoàn Chỉnh

**Kịch bản:** Từ tắt cầu → Scanner phát hiện → Kích hoạt → Dashboard an toàn

**Các bước:**

1. **Setup:**
   - Tắt 3 cầu Lô và 2 cầu Đề
   - Ghi nhớ tên

2. **Chạy Scanner:**
   - Menu → Dò Tìm Cầu Lô
   - Quan sát Log: Phải thấy "[Phase 2] ✅ Revived Bridge" cho 3 cầu

3. **Kiểm tra Bridge Manager:**
   - Các cầu đã được BẬT lại
   - Win Rate đã cập nhật

4. **Kiểm tra Dashboard:**
   - Chuyển sang Dashboard
   - Nếu còn đang tính → Cảnh báo xuất hiện
   - Đợi hoàn tất → Cảnh báo biến mất

5. **Verify:**
   - Tất cả cầu đã được kích hoạt
   - Dashboard hiển thị dự đoán từ dữ liệu hoàn chỉnh
   - Không có lỗi trong Log

### Scenario 2: Stress Test (Tải Nặng)

**Mục tiêu:** Kiểm tra hệ thống dưới tải cao

**Các bước:**

1. Kích hoạt **10-20 cầu cùng lúc**
2. Đồng thời mở nhiều tab (Bridge Manager, Dashboard, Settings)
3. Thao tác qua lại giữa các tab
4. Chạy Scanner trong khi đang kích hoạt

**Kết quả mong đợi:**
- UI không crash hay freeze
- Log hiển thị đúng thứ tự
- Cảnh báo Dashboard cập nhật chính xác
- Thread safety đảm bảo (không có lỗi "race condition")

---

## Kiểm Tra Lỗi và Edge Cases

### Test E1: Cầu Không Tồn Tại

**Các bước:**

1. Thử kích hoạt cầu không có trong DB
2. Quan sát Log

**Kết quả mong đợi:**
```
⚠️ Không tìm thấy cầu trong DB
```
- Không crash
- Thông báo lỗi rõ ràng

### Test E2: Dữ Liệu Không Đủ

**Các bước:**

1. Xóa hầu hết dữ liệu lịch sử (giữ lại < 2 kỳ)
2. Thử kích hoạt cầu

**Kết quả mong đợi:**
```
Cần ít nhất 2 kỳ dữ liệu để tính toán.
```

### Test E3: Kích Hoạt Nhiều Lần Liên Tiếp

**Các bước:**

1. Kích hoạt cùng một cầu 3 lần liên tiếp
2. Quan sát Log và SYNCING_BRIDGES

**Kết quả mong đợi:**
- Lần 1: Thành công
- Lần 2, 3: Vẫn chạy nhưng cảnh báo có thể xuất hiện
- Không có deadlock hay lỗi thread

---

## Checklist Tổng Hợp

### Phase 1 ✅
- [ ] Kích hoạt cầu đơn lẻ thành công
- [ ] Kích hoạt nhiều cầu (batch) thành công
- [ ] Background thread không làm UI đóng băng
- [ ] Win Rate, Streak, Prediction được cập nhật
- [ ] Log hiển thị đầy đủ với prefix [ACTIVATE]

### Phase 2 ✅
- [ ] Scanner phát hiện cầu TẮT
- [ ] Cầu TẮT được hồi sinh tự động
- [ ] Log hiển thị "[Phase 2] ✅ Revived Bridge"
- [ ] Không tạo cầu trùng lặp
- [ ] Cầu đang BẬT không bị ảnh hưởng

### Phase 3 ✅
- [ ] Cảnh báo xuất hiện khi có cầu đang sync
- [ ] Cảnh báo biến mất khi hoàn tất
- [ ] Dashboard không dùng dữ liệu chưa hoàn chỉnh
- [ ] Thread safety đảm bảo (không crash)
- [ ] get_syncing_bridges_count() trả về đúng

### Tổng Thể ✅
- [ ] Không có lỗi trong Log
- [ ] UI phản hồi mượt mà
- [ ] Dữ liệu đồng bộ chính xác
- [ ] Không có memory leak (test dài hạn)

---

## Công Cụ Hỗ Trợ Testing

### 1. Log Window

**Vị trí:** Cửa sổ chính → Log tab

**Cách sử dụng:**
- Quan sát các message với prefix:
  - `[ACTIVATE]` - Phase 1
  - `[Phase 2]` - Phase 2
  - `[Phase 3]` - Phase 3

### 2. Python Console (Nâng Cao)

**Kiểm tra SYNCING_BRIDGES:**

```python
from services.bridge_service import get_syncing_bridges_count, get_syncing_bridges_list

# Số cầu đang sync
print(get_syncing_bridges_count())

# Danh sách cầu đang sync
print(get_syncing_bridges_list())
```

### 3. Database Inspector (Nâng Cao)

**Kiểm tra trạng thái cầu:**

```sql
-- Xem cầu đang BẬT
SELECT name, is_enabled, win_rate_text FROM ManagedBridges WHERE is_enabled=1;

-- Xem cầu đang TẮT
SELECT name, is_enabled FROM ManagedBridges WHERE is_enabled=0;
```

---

## Khắc Phục Sự Cố

### Vấn đề: Cảnh báo không xuất hiện

**Nguyên nhân:** 
- Dashboard chưa refresh
- Sync quá nhanh (< 1 giây)

**Giải pháp:**
- Nhấn "Làm Mới Dữ Liệu"
- Test với nhiều cầu hơn (5-10 cầu)

### Vấn đề: Cầu không được hồi sinh

**Nguyên nhân:**
- Scanner không tìm thấy cầu
- Cầu bị lỗi dữ liệu

**Giải pháp:**
- Kiểm tra Log có message "[Phase 2]" không
- Xem lỗi cụ thể trong Log
- Verify cầu tồn tại trong DB

### Vấn đề: UI bị lag

**Nguyên nhân:**
- Quá nhiều cầu được kích hoạt cùng lúc
- Database chậm

**Giải pháp:**
- Giảm số cầu activate mỗi lần
- Kiểm tra kích thước database
- Đảm bảo SSD đủ nhanh

---

## Kết Luận

Sau khi hoàn thành tất cả các test trên, hệ thống đã được nâng cấp thành công với:

- ✅ **Phase 1:** Kích hoạt cầu real-time, không block UI
- ✅ **Phase 2:** Tự động hồi sinh cầu cũ, không tạo trùng
- ✅ **Phase 3:** Bảo vệ Dashboard, dữ liệu an toàn

**Lưu ý:** 
- Nếu phát hiện lỗi, ghi lại **message log chính xác** và báo cáo
- Kiểm tra phiên bản code: Phải có các commit Phase 1, 2, 3
- Backup database trước khi test

**Hỗ trợ:**
- Xem `docs/PHASE1_BRIDGE_ACTIVATION.md` cho chi tiết Phase 1
- Xem `docs/PHASE2_SMART_SCANNER.md` cho chi tiết Phase 2  
- Xem `docs/PHASE3_DASHBOARD_PROTECTION.md` cho chi tiết Phase 3
