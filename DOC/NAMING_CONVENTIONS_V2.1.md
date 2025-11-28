# QUY CHUẨN ĐẶT TÊN CẦU (NAMING CONVENTION V2.1)

**Phiên bản:** 2.1 (Áp dụng từ V7.9)

**Ngày cập nhật:** 28/11/2025



Tài liệu này quy định cách đặt tên định danh (ID) cho các cầu Lô và Đề trong hệ thống, đảm bảo tính nhất quán giữa Scanner (Quét cầu), Manager (Quản lý) và Database.



---



## I. CẤU TRÚC CHUNG

Mọi ID cầu đều tuân theo format:

`[HỆ]_[THUẬT_TOÁN]_[LOGIC]_[THAM_SỐ]`



* **[HỆ]:** `DE` (Đề - Giải Đặc Biệt), `LO` (Lô Tô).

* **[THUẬT_TOÁN]:** `STL` (Song Thủ), `DYN` (Động), `POS` (Vị trí).

* **[LOGIC]:** `FIXED` (Cố định), `VAR` (Biến thiên).



---



## II. CẦU ĐỀ (DE BRIDGES)



### 1. Cầu Động (Dynamic Offset)

Đây là loại cầu phổ biến nhất, tự động tìm quy luật cộng thêm số K.



* **Format:** `DE_DYN_[VỊ_TRÍ_1]_[VỊ_TRÍ_2]_K[SỐ]`

* **Ví dụ:** `DE_DYN_GDB_G2_K1`

* **Giải nghĩa:**

    * `DE`: Cầu Đề.

    * `DYN`: Thuật toán động (Dynamic).

    * `GDB`, `G2`: Tên giải lấy số tham chiếu (Lấy con số **CUỐI CÙNG** của giải).

    * `K1`: Hệ số biến thiên (Offset) = 1.

* **Công thức tính:**

    $$( \text{Đuôi } VỊ\_TRÍ\_1 + \text{Đuôi } VỊ\_TRÍ\_2 + K ) \pmod{10} = \text{Chạm}$$



### 2. Cầu Vị Trí (Position Sum)

Cộng giá trị của 2 vị trí cố định bất kỳ trong bảng kết quả (hỗ trợ cả cầu Bóng V17).



* **Format:** `DE_POS_[POS_CODE_1]_[POS_CODE_2]`

* **Ví dụ:** `DE_POS_GDB0_G11`

* **Giải nghĩa:**

    * `GDB0`: Số thứ 1 (Index 0) của giải Đặc Biệt.

    * `G11`: Số thứ 2 (Index 1) của giải Nhất.



---



## III. CẦU LÔ (LO BRIDGES)



### 1. Cầu Lô Cố Định (Fixed Classic)

Bộ 15 cầu lô kinh điển được hardcode trong hệ thống.



* **Format:** `LO_STL_FIXED_[INDEX]`

* **Danh sách chi tiết:**



| ID | Mô tả Logic (Nguồn: `bridges_classic.py`) |

| :--- | :--- |

| `LO_STL_FIXED_01` | Đuôi GĐB + 5 |

| `LO_STL_FIXED_02` | G6.2 (Đuôi) + G7.3 (Đuôi) |

| `LO_STL_FIXED_03` | Đuôi GĐB + Đuôi G1 |

| `LO_STL_FIXED_04` | GĐB (Sát đuôi) + G1 (Đuôi) |

| `LO_STL_FIXED_05` | Đầu G7.0 + Đuôi G7.3 |

| `LO_STL_FIXED_06` | Đuôi G7.1 + Đầu G7.2 |

| `LO_STL_FIXED_07` | Đầu G5.0 + Đầu G7.0 |

| `LO_STL_FIXED_08` | Đầu G3.0 + Đầu G4.0 |

| `LO_STL_FIXED_09` | Đầu GĐB + Đầu G1 |

| `LO_STL_FIXED_10` | G2.1 (Giữa) + G3.2 (Đuôi) |

| `LO_STL_FIXED_11` | GĐB (Giữa) + G3.1 (Đuôi) |

| `LO_STL_FIXED_12` | Đuôi GĐB + G3.2 (Giữa) |

| `LO_STL_FIXED_13` | Đuôi G7.2 + 8 |

| `LO_STL_FIXED_14` | Đuôi G1 + 2 |

| `LO_STL_FIXED_15` | Đuôi GĐB + 7 |



---



## IV. QUY TẮC MAP TÊN GIẢI (MAPPING)



Hệ thống sử dụng quy tắc ánh xạ tên giải sang vị trí số cuối cùng (Last Digit Index) trong chuỗi dữ liệu thô (gồm 107 số).



| Tên Giải | Ký hiệu | Index Số Cuối (Trong mảng 107 số) |

| :--- | :--- | :--- |

| Đặc Biệt | `GDB` | 4 |

| Giải Nhất | `G1` | 9 |

| Giải Nhì | `G2` | 19 (Lấy đuôi giải 2.2) |

| Giải Ba | `G3` | 49 (Lấy đuôi giải 3.6) |

| Giải Tư | `G4` | 65 (Lấy đuôi giải 4.4) |

| Giải Năm | `G5` | 89 (Lấy đuôi giải 5.6) |

| Giải Sáu | `G6` | 98 (Lấy đuôi giải 6.3) |

| Giải Bảy | `G7` | 106 (Lấy đuôi giải 7.4) |



> **Lưu ý:** Khi tính toán Cầu Động (`DE_DYN`), hệ thống luôn sử dụng con số tại các Index này.