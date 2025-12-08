# V11.0 - Tái Cấu Trúc Workflow Quản Lý Cầu Đề

**Ngày:** 2024-12-08  
**Phiên bản:** V11.0  
**Tác giả:** GitHub Copilot Agent

---

## 📋 Tổng Quan

Phiên bản V11.0 tái cấu trúc hoàn toàn workflow quản lý cầu Đề, tách biệt rõ ràng 4 giai đoạn:

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  QUÉT   │ -> │  DUYỆT  │ -> │ QUẢN LÝ │ -> │ PHÂN TÍCH│
│ (Scan)  │    │(Approve)│    │ (Manage)│    │(Analysis)│
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

---

## 🎯 Mục Tiêu

### Trước V11.0 (Vấn đề)
- Scanner tự động lưu cầu vào DB → Không cho phép user xem xét
- Dashboard tự động quét lại cầu mỗi lần phân tích → Tốn tài nguyên
- Không có bộ lọc chất lượng rõ ràng
- Cầu DE_KILLER được lưu vào DB dù không nên đề xuất
- Không phân biệt rõ "cầu đề xuất" vs "cầu đã quản lý"

### Sau V11.0 (Giải pháp)
✅ Scanner chỉ quét và trả về kết quả, KHÔNG tự động lưu  
✅ User xem xét và chọn cầu muốn thêm vào quản lý  
✅ Dashboard chỉ phân tích cầu đã lưu trong DB  
✅ Bộ lọc chất lượng tự động:
- Loại bỏ TOÀN BỘ DE_KILLER
- Lọc DE_DYN: Chỉ giữ cầu ≥ 28/30 (93.3%)  
✅ Workflow rõ ràng, dễ kiểm soát

---

## 🔧 Thay Đổi Kỹ Thuật

### 1. Backend (Logic Layer)

#### 1.1. `de_bridge_scanner.py`

**Thay đổi chính:**
```python
def scan_all(self, all_data_ai, auto_save=False):
    """
    Args:
        auto_save: Nếu False (default), chỉ trả về kết quả
                   Nếu True, tự động lưu vào DB (backward compatible)
    """
    # ... quét cầu ...
    
    # Áp dụng bộ lọc chất lượng
    filtered_bridges = self._apply_quality_filters(found_bridges)
    
    # Chỉ lưu khi auto_save=True
    if auto_save:
        self._save_to_db(filtered_bridges)
    
    return len(filtered_bridges), filtered_bridges
```

**Bộ lọc chất lượng:**
```python
def _apply_quality_filters(self, bridges):
    """
    1. Loại bỏ TOÀN BỘ DE_KILLER
    2. DE_DYN: Chỉ giữ streak ≥ 28/30 (93.3%)
    3. Các loại khác: Giữ nguyên
    """
    filtered = []
    for bridge in bridges:
        # Loại DE_KILLER
        if bridge['type'] == 'DE_KILLER':
            print(f"[FILTER] Loại bỏ DE_KILLER: {bridge['name']}")
            continue
        
        # Lọc DE_DYN theo tỷ lệ
        if bridge['type'] == 'DE_DYNAMIC_K':
            if bridge['streak'] < 28:  # < 93.3%
                print(f"[FILTER] Loại DE_DYN (thấp): {bridge['name']}")
                continue
        
        # Giữ lại
        filtered.append(bridge)
    
    return filtered
```

#### 1.2. `bridge_approval_service.py` (MỚI)

Service quản lý việc duyệt và lưu cầu:

```python
class BridgeApprovalService:
    def approve_single_bridge(self, bridge):
        """Duyệt và lưu 1 cầu vào DB"""
        # Kiểm tra trùng lặp
        # Lưu vào ManagedBridges
        return success, message
    
    def approve_multiple_bridges(self, bridges):
        """Duyệt và lưu nhiều cầu"""
        for bridge in bridges:
            self.approve_single_bridge(bridge)
        return success_count, failed_count, message
```

**Sử dụng:**
```python
from logic.bridges.bridge_approval_service import approve_bridges

success, failed, msg = approve_bridges(selected_bridges)
```

---

### 2. UI Layer

#### 2.1. `ui_de_bridge_scanner.py` (MỚI)

Cửa sổ mới cho việc quét và duyệt cầu:

**Chức năng:**
- Button "🔍 Quét Cầu Mới" → Gọi scanner (auto_save=False)
- Hiển thị TẤT CẢ kết quả trong bảng
- Checkbox cho từng cầu để user chọn
- Filter theo loại cầu (DE_DYN, DE_SET, etc)
- Button "✅ Thêm Đã Chọn vào Quản Lý" → Lưu vào DB

**UI Layout:**
```
┌─────────────────────────────────────────────────┐
│ [🔍 Quét] [✅ Thêm Đã Chọn] [☑️ All] [⬜ None]  │
├─────────────────────────────────────────────────┤
│ Tổng: 150 cầu  |  Đã chọn: 25                   │
├─────────────────────────────────────────────────┤
│ Filter: ⚪ Tất cả ⚪ DE_DYN ⚪ DE_SET ...        │
├─────────────────────────────────────────────────┤
│ ☑️ │ Tên Cầu    │ Loại   │ Thông │ Tỷ Lệ │ Dự Đoán│
│ ☑️ │ DE_DYN_... │ DE_DYN │ 28/30 │ 93.3% │ 3,4,5  │
│ ⬜ │ DE_SET_... │ DE_SET │ 15/30 │ 50.0% │ Bộ 00  │
│ ...                                              │
└─────────────────────────────────────────────────┘
```

**Code mẫu:**
```python
def _start_scan(self):
    """Bắt đầu quét"""
    data = self.app.all_data_ai
    # Gọi scanner KHÔNG auto_save
    count, bridges = run_de_scanner(data, auto_save=False)
    self._display_results(bridges)

def _approve_selected(self):
    """Duyệt các cầu đã chọn"""
    selected = [b for b in self.scanned_bridges if b['selected']]
    success, failed, msg = approve_bridges(selected)
    messagebox.showinfo("Kết quả", msg)
```

#### 2.2. `ui_de_dashboard.py`

**Thay đổi:**
- Button: "🚀 QUÉT & PHÂN TÍCH" → "📊 PHÂN TÍCH CẦU ĐÃ QUẢN LÝ"
- Label: "🎯 Cầu Động" → "🎯 Cầu Đã Quản Lý"
- Logic: Không gọi `run_de_scanner()`, chỉ load từ DB

**Code cũ:**
```python
def _run_logic(self, data):
    # ❌ CŨ: Tự động quét
    bridges = run_de_scanner(data)
```

**Code mới:**
```python
def _run_logic(self, data):
    # ✅ MỚI: Chỉ load từ DB
    from logic.data_repository import get_all_managed_bridges
    all_bridges = get_all_managed_bridges(only_enabled=True)
    bridges = [b for b in all_bridges if b['type'].startswith('DE_')]
```

#### 2.3. `ui_bridge_manager.py`

**Thêm button:**
```python
ttk.Button(
    toolbar, 
    text="🔍 Quét Cầu Đề Mới",
    command=self.open_de_scanner
)
```

#### 2.4. `ui_main_window.py`

**Thay đổi button:**
```python
# CŨ: "🔍 Dò Tìm Cầu Mới" → run_auto_find_bridges()
# MỚI: "🔍 Quét Cầu Đề Mới" → show_de_scanner_window()
```

---

## 📖 Hướng Dẫn Sử Dụng

### Workflow Mới (User Perspective)

#### Bước 1: Quét Cầu Mới

1. Click button **"🛠️ QUẢN LÝ CẦU"** (hoặc từ menu chính)
2. Click button **"🔍 Quét Cầu Đề Mới"** (màu xanh)
3. Cửa sổ Scanner mở ra
4. Click **"🔍 Quét Cầu Mới"**
5. Hệ thống sẽ:
   - Quét dữ liệu lịch sử (30 kỳ)
   - Áp dụng bộ lọc chất lượng
   - Hiển thị TẤT CẢ kết quả đạt tiêu chuẩn

#### Bước 2: Xem Xét & Chọn Cầu

6. Xem danh sách cầu được đề xuất
7. Có thể:
   - Filter theo loại cầu
   - Sắp xếp theo tỷ lệ/streak
   - Đọc mô tả chi tiết
8. Click vào checkbox để chọn cầu muốn thêm
   - Hoặc click **"☑️ Chọn Tất Cả"**

#### Bước 3: Duyệt & Lưu

9. Click **"✅ Thêm Đã Chọn vào Quản Lý"**
10. Xác nhận
11. Hệ thống lưu vào database
12. Cầu đã lưu sẽ xuất hiện trong "Quản Lý Cầu"

#### Bước 4: Phân Tích

13. Chuyển sang tab **"Soi Cầu Đề"**
14. Click **"📊 PHÂN TÍCH CẦU ĐÃ QUẢN LÝ"**
15. Hệ thống chỉ phân tích cầu đã lưu (bật)

---

## 🔍 Tiêu Chí Lọc

### 1. DE_KILLER - Loại Bỏ Hoàn Toàn

**Lý do:**
- Cầu KILLER dùng để loại bỏ số, KHÔNG phải đề xuất
- Không có giá trị dự đoán tích cực
- Chỉ gây nhiễu trong danh sách đề xuất

**Hành động:**
```
✗ KHÔNG bao giờ đề xuất DE_KILLER
✗ KHÔNG lưu vào DB
✓ Ghi log khi phát hiện và loại bỏ
```

### 2. DE_DYN (Dynamic) - Lọc Theo Tỷ Lệ

**Tiêu chuẩn:** Streak ≥ 28/30 (≥ 93.3%)

**Lý do:**
- Cầu Dynamic cần tỷ lệ cao mới đáng tin
- 28/30 = 93.3% là ngưỡng "xuất sắc"
- Dưới ngưỡng này: rủi ro cao

**Ví dụ:**
```
✓ DE_DYN_G1_G2_K3: 29/30 (96.7%) → GIỮ LẠI
✓ DE_DYN_GDB_G1_K1: 28/30 (93.3%) → GIỮ LẠI (boundary)
✗ DE_DYN_G3_G4_K2: 25/30 (83.3%) → LOẠI BỎ
```

### 3. Các Loại Khác - Giữ Nguyên

**DE_SET (Bộ):**
- Luôn giữ lại
- Tính chất đặc biệt, không dùng tỷ lệ đơn giản

**DE_MEMORY (Bạc Nhớ):**
- Luôn giữ lại
- Dựa trên pattern mining, có logic riêng

**DE_PASCAL:**
- Luôn giữ lại
- Thuật toán topology đặc biệt

**DE_POS_SUM:**
- Luôn giữ lại
- Cầu tổng vị trí, tỷ lệ không phải tiêu chí duy nhất

---

## 📊 Logging & Monitoring

### Log Khi Quét

```
>>> [DE SCANNER V11.0] Bắt đầu quét (Quality Filtering)...
>>> [DE SCANNER] Bạc Nhớ tìm thấy: 25
>>> [DE SCANNER] Cầu Loại phát hiện: 18 (sẽ KHÔNG đề xuất)

>>> [QUALITY FILTER] Kết quả lọc:
    - Tổng đầu vào: 287
    - Loại DE_KILLER: 18
    - Loại DE_DYN (< 93.3%): 45
    - Giữ lại: 224

>>> [DE SCANNER] Trả về 224 cầu (chưa lưu DB).
>>> [DE SCANNER] Hoàn tất quét.
```

### Log Khi Duyệt

```
>>> [APPROVAL] User chọn 35 cầu để thêm vào quản lý
>>> [APPROVAL] Đã thêm thành công: 33 cầu
>>> [APPROVAL] Lỗi: 2 cầu (trùng lặp)
```

---

## 🧪 Testing

### Test File: `test_v11_bridge_filtering.py`

**Kết quả:**
```
=== TEST QUALITY FILTERS ===
Input: 7 bridges
Output: 5 bridges
✓ DE_KILLER bridges removed
✓ DE_DYN bridges filtered correctly (2 kept)
✓ Other bridge types kept correctly
✓ Total filtered bridges: 5 (expected 5)

=== ALL TESTS PASSED ===

=== TEST AUTO_SAVE FLAG ===
✓ scan_all(auto_save=False) returned 0 bridges
✓ scan_all(auto_save=True) returned 0 bridges

==================================================
ALL V11.0 TESTS PASSED SUCCESSFULLY
==================================================
```

---

## 🔄 Backward Compatibility

### Giữ Nguyên API Cũ

```python
# API cũ vẫn hoạt động (auto_save=True)
def run_de_scanner(data):
    return DeBridgeScanner().scan_all(data, auto_save=True)

# API mới (khuyến khích)
def run_de_scanner(data, auto_save=False):
    return DeBridgeScanner().scan_all(data, auto_save)
```

### Migration Path

**Nếu code cũ:**
```python
# Code cũ tự động lưu
_, bridges = run_de_scanner(data)
# → Cầu đã được lưu vào DB
```

**Chuyển sang code mới:**
```python
# Bước 1: Quét (không lưu)
_, bridges = run_de_scanner(data, auto_save=False)

# Bước 2: Xem xét
selected = user_select(bridges)

# Bước 3: Duyệt
approve_bridges(selected)
```

---

## 📝 Best Practices

### Khi Quét Cầu

✅ **NÊN:**
- Quét định kỳ (1-2 lần/tuần) để cập nhật cầu mới
- Xem xét kỹ trước khi approve
- Ưu tiên cầu có tỷ lệ cao (> 95%)

❌ **KHÔNG NÊN:**
- Approve tất cả cầu mà không xem xét
- Quét quá thường xuyên (lãng phí tài nguyên)
- Giữ quá nhiều cầu yếu trong DB

### Khi Quản Lý

✅ **NÊN:**
- Tắt cầu kém hiệu quả thay vì xóa
- Sử dụng chức năng "Tối Ưu Thông Minh"
- Kiểm tra K1N/K2N định kỳ

### Khi Phân Tích

✅ **NÊN:**
- Chỉ bật cầu đang tin tưởng
- Kết hợp nhiều loại cầu (DYN + SET + MEMORY)
- Theo dõi xu hướng thay đổi

---

## 🚀 Future Enhancements

### V11.1 (Planned)

- [ ] Lưu lịch sử approval (audit log)
- [ ] Thêm filter nâng cao (theo streak, win_rate, date)
- [ ] Export/Import danh sách cầu
- [ ] Thống kê hiệu quả cầu theo thời gian

### V11.2 (Ideas)

- [ ] AI đề xuất cầu nên approve
- [ ] So sánh cầu trùng lặp
- [ ] Gợi ý khi có cầu mới tốt hơn cầu cũ

---

## 📞 Support

**Vấn đề:** Cầu không xuất hiện trong Dashboard?
**Giải pháp:** 
1. Kiểm tra cầu đã được lưu vào DB chưa (Quản Lý Cầu)
2. Kiểm tra cầu có đang bật (is_enabled=1)?
3. Kiểm tra loại cầu có phải DE_* không?

**Vấn đề:** Scanner không tìm thấy cầu nào?
**Giải pháp:**
1. Kiểm tra dữ liệu đủ 30 kỳ chưa?
2. Xem log filter - có thể tất cả đều bị loại
3. Thử giảm threshold tạm thời để kiểm tra

---

## 📄 Summary

**V11.0 là bước tiến lớn trong việc:**
- ✅ Tách biệt workflow rõ ràng
- ✅ Cho phép user kiểm soát tốt hơn
- ✅ Áp dụng bộ lọc chất lượng tự động
- ✅ Giảm thiểu rủi ro và nhiễu
- ✅ Tối ưu hiệu năng phân tích

**Breaking Changes:** KHÔNG (100% backward compatible)

**Recommended Action:** Chuyển sang workflow mới để tận dụng tối đa tính năng.

---

*Tài liệu này sẽ được cập nhật khi có thêm tính năng mới.*
