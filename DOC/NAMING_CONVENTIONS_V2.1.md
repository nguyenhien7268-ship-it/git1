# QUY CHUẨN ĐẶT TÊN CẦU (NAMING CONVENTION V2.1)

**Phiên bản:** 2.1 (Final Standard)
**Ngày cập nhật:** 02/12/2025

Tài liệu này quy định cách đặt tên định danh (ID) cho các cầu Lô và Đề trong hệ thống, đảm bảo tính nhất quán giữa Scanner (Quét cầu), Manager (Quản lý) và Database.

---

## I. CẤU TRÚC CHUNG

Mọi ID cầu đều tuân theo format:
`[HỆ]_[THUẬT_TOÁN]_[LOGIC]_[THAM_SỐ]`

* **[HỆ]:** `DE` (Đề - Giải Đặc Biệt), `LO` (Lô Tô).
* **[THUẬT_TOÁN]:** `STL` (Song Thủ), `DYN` (Động), `POS` (Vị trí), `SET` (Bộ), `MEM` (Bạc Nhớ).
* **[LOGIC]:** `FIXED` (Cố định), `SUM` (Tổng), `DIFF` (Hiệu).

---

## II. CẦU ĐỀ (DE BRIDGES)

### 1. Cầu Động (Dynamic Offset)
Tự động tìm quy luật cộng thêm số K vào đuôi giải.

* **Format:** `DE_DYN_[VỊ_TRÍ_1]_[VỊ_TRÍ_2]_K[SỐ]`
* **Ví dụ:** `DE_DYN_GDB_G2_K1`
* **Logic:** `(Đuôi VT1 + Đuôi VT2 + K) % 10 = Chạm`

### 2. Cầu Vị Trí (Position Sum)
Cộng giá trị của 2 vị trí cố định (hỗ trợ cầu Bóng).

* **Format:** `DE_POS_[POS_CODE_1]_[POS_CODE_2]`
* **Ví dụ:** `DE_POS_GDB0_G11`
* **Logic:** `(Val1 + Val2) % 10 = Chạm`

### 3. Cầu Bộ (Set Bridges) - [MỚI]
Ghép 2 vị trí thành số để tìm Bộ số tương ứng.

* **Format:** `DE_SET_[POS_CODE_1]_[POS_CODE_2]`
* **Ví dụ:** `DE_SET_GDB2_G12`
    * `GDB2`: Vị trí index 2 giải ĐB (ví dụ số 5).
    * `G12`: Vị trí index 2 giải Nhất (ví dụ số 3).
    * Ghép lại: `53` -> Thuộc **Bộ 03**.
    * Dự đoán: Dàn số thuộc Bộ 03 (03, 30, 08, 80, 53, 35, 58, 85).

---

## III. CẦU LÔ (LO BRIDGES)

### 1. Cầu Lô Cố Định (Fixed Classic)
Bộ 15 cầu lô kinh điển (Bridge 01 - 15).

* **Format:** `LO_STL_FIXED_[INDEX]`
* **Ví dụ:** `LO_STL_FIXED_01` (Cầu GĐB + 5)

### 2. Cầu Lô Vị Trí (Position V17) - [CHUẨN HÓA]
Cầu lô ghép từ 2 vị trí bất kỳ trong bảng kết quả (V17 Shadow).

* **Format:** `LO_POS_[POS_CODE_1]_[POS_CODE_2]`
* **Quy tắc làm sạch tên (Sanitize):**
    * Các ký tự `[`, `]`, `(`, `)`, `.`, ` ` sẽ được thay thế bằng `_` hoặc loại bỏ.
* **Ví dụ:**
    * Cũ: `G1[0]+GDB[2]`
    * Mới: `LO_POS_G1_0_GDB_2`

### 3. Cầu Bạc Nhớ (Memory Bridges) - [CHUẨN HÓA]
756 cầu dựa trên quy luật Bạc Nhớ (Tổng/Hiệu của các cặp số loto ra kỳ trước).

* **Format Tổng:** `LO_MEM_SUM_[LOTO_1]_[LOTO_2]`
    * Ví dụ: `LO_MEM_SUM_00_01` (Bạc nhớ Tổng cặp 00 và 01).
* **Format Hiệu:** `LO_MEM_DIFF_[LOTO_1]_[LOTO_2]`
    * Ví dụ: `LO_MEM_DIFF_00_01` (Bạc nhớ Hiệu cặp 00 và 01).

---

## IV. QUY TẮC MAP TÊN GIẢI (MAPPING)

Hệ thống sử dụng quy tắc ánh xạ tên giải sang vị trí số cuối cùng (Last Digit Index) cho Cầu Động (`DE_DYN`):

| Tên Giải | Ký hiệu | Index Số Cuối |
| :--- | :--- | :--- |
| Đặc Biệt | `GDB` | 4 |
| Giải Nhất | `G1` | 9 |
| Giải Nhì | `G2` | 19 |
| Giải Ba | `G3` | 49 |
| Giải Tư | `G4` | 65 |
| Giải Năm | `G5` | 89 |
| Giải Sáu | `G6` | 98 |
| Giải Bảy | `G7` | 106 |