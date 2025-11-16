# Tên file: logic/analytics_utils.py
# (NỘI DUNG THAY THẾ TOÀN BỘ)
# File này tập hợp các hàm tiện ích phân tích (GĐ 1/2)
# để phá vỡ lỗi import vòng (circular import)

from typing import List, Tuple, Dict, Any, Optional

# ===================================================================================
# I. CÁC HÀM TIỆN ÍCH CƠ BẢN (CHUYỂN TỪ bridges_classic.py / V6)
# ===================================================================================

def checkHitSet_V30_K2N(pred_stl: List[str], actual_loto_set: set) -> str:
    """
    (Hàm Tiện ích GĐ 2) Kiểm tra kết quả K2N (đã được di dời).
    """
    if not pred_stl or len(pred_stl) < 2:
        return "LỖI"
        
    lo1, lo2 = pred_stl[0], pred_stl[1]
    
    hit_lo1 = lo1 in actual_loto_set
    hit_lo2 = lo2 in actual_loto_set

    if hit_lo1 and hit_lo2:
        return "✅✅"
    elif hit_lo1:
        return f"✅({lo1})"
    elif hit_lo2:
        return f"✅({lo2})"
    else:
        # (Sửa logic V6) Trả về K2N nếu N1 trượt
        return "K2N" 

# ===================================================================================
# II. CÁC HÀM TIỆN ÍCH V16/V17 (CHUYỂN TỪ bridges_v16.py)
# ===================================================================================

BONG_DUONG_V30 = {
    '0': '5', '1': '6', '2': '7', '3': '8', '4': '9',
    '5': '0', '6': '1', '7': '2', '8': '3', '9': '4'
}

def getBongDuong_V30(digit):
    return BONG_DUONG_V30.get(str(digit), str(digit))

def taoSTL_V30_Bong(a, b):
    try:
        strA, strB = str(int(a)), str(int(b))
    except Exception:
        return ['00', '55'] # Fallback nếu a, b không phải số
        
    if strA == strB:
        kep = f"{strA}{strB}".zfill(2)
        bongDigit = getBongDuong_V30(strA)
        bongKep = f"{bongDigit}{bongDigit}".zfill(2)
        return [kep, bongKep]
    else:
        lo1 = f"{strA}{strB}".zfill(2)
        lo2 = f"{strB}{strA}".zfill(2)
        return [lo1, lo2]

# (Di dời từ bridges_v16.py)
POSITION_MAP_V17 = {
    "GDB_0": (2, 0), "GDB_1": (2, 1), "GDB_2": (2, 2), "GDB_3": (2, 3), "GDB_4": (2, 4),
    "G1_0": (3, 0), "G1_1": (3, 1), "G1_2": (3, 2), "G1_3": (3, 3), "G1_4": (3, 4),
    "G2_0_0": (4, 0, 0), "G2_0_1": (4, 0, 1), "G2_0_2": (4, 0, 2), "G2_0_3": (4, 0, 3), "G2_0_4": (4, 0, 4),
    "G2_1_0": (4, 1, 0), "G2_1_1": (4, 1, 1), "G2_1_2": (4, 1, 2), "G2_1_3": (4, 1, 3), "G2_1_4": (4, 1, 4),
    "G3_0_0": (5, 0, 0), "G3_0_1": (5, 0, 1), "G3_0_2": (5, 0, 2), "G3_0_3": (5, 0, 3), "G3_0_4": (5, 0, 4),
    "G3_1_0": (5, 1, 0), "G3_1_1": (5, 1, 1), "G3_1_2": (5, 1, 2), "G3_1_3": (5, 1, 3), "G3_1_4": (5, 1, 4),
    "G3_2_0": (5, 2, 0), "G3_2_1": (5, 2, 1), "G3_2_2": (5, 2, 2), "G3_2_3": (5, 2, 3), "G3_2_4": (5, 2, 4),
    "G3_3_0": (5, 3, 0), "G3_3_1": (5, 3, 1), "G3_3_2": (5, 3, 2), "G3_3_3": (5, 3, 3), "G3_3_4": (5, 3, 4),
    "G3_4_0": (5, 4, 0), "G3_4_1": (5, 4, 1), "G3_4_2": (5, 4, 2), "G3_4_3": (5, 4, 3), "G3_4_4": (5, 4, 4),
    "G3_5_0": (5, 5, 0), "G3_5_1": (5, 5, 1), "G3_5_2": (5, 5, 2), "G3_5_3": (5, 5, 3), "G3_5_4": (5, 5, 4),
    "G4_0_0": (6, 0, 0), "G4_0_1": (6, 0, 1), "G4_0_2": (6, 0, 2), "G4_0_3": (6, 0, 3),
    "G4_1_0": (6, 1, 0), "G4_1_1": (6, 1, 1), "G4_1_2": (6, 1, 2), "G4_1_3": (6, 1, 3),
    "G4_2_0": (6, 2, 0), "G4_2_1": (6, 2, 1), "G4_2_2": (6, 2, 2), "G4_2_3": (6, 2, 3),
    "G4_3_0": (6, 3, 0), "G4_3_1": (6, 3, 1), "G4_3_2": (6, 3, 2), "G4_3_3": (6, 3, 3),
    "G5_0_0": (7, 0, 0), "G5_0_1": (7, 0, 1), "G5_0_2": (7, 0, 2), "G5_0_3": (7, 0, 3),
    "G5_1_0": (7, 1, 0), "G5_1_1": (7, 1, 1), "G5_1_2": (7, 1, 2), "G5_1_3": (7, 1, 3),
    "G5_2_0": (7, 2, 0), "G5_2_1": (7, 2, 1), "G5_2_2": (7, 2, 2), "G5_2_3": (7, 2, 3),
    "G5_3_0": (7, 3, 0), "G5_3_1": (7, 3, 1), "G5_3_2": (7, 3, 2), "G5_3_3": (7, 3, 3),
    "G5_4_0": (7, 4, 0), "G5_4_1": (7, 4, 1), "G5_4_2": (7, 4, 2), "G5_4_3": (7, 4, 3),
    "G5_5_0": (7, 5, 0), "G5_5_1": (7, 5, 1), "G5_5_2": (7, 5, 2), "G5_5_3": (7, 5, 3),
    "G6_0_0": (8, 0, 0), "G6_0_1": (8, 0, 1), "G6_0_2": (8, 0, 2),
    "G6_1_0": (8, 1, 0), "G6_1_1": (8, 1, 1), "G6_1_2": (8, 1, 2),
    "G6_2_0": (8, 2, 0), "G6_2_1": (8, 2, 1), "G6_2_2": (8, 2, 2),
    "G7_0_0": (9, 0, 0), "G7_0_1": (9, 0, 1),
    "G7_1_0": (9, 1, 0), "G7_1_1": (9, 1, 1),
    "G7_2_0": (9, 2, 0), "G7_2_1": (9, 2, 1),
    "G7_3_0": (9, 3, 0), "G7_3_1": (9, 3, 1),
}

# (Di dời từ bridges_v16.py)
# Tạo map ngược để lấy tên từ (Giải, Index)
_POSITION_NAME_MAP_V17 = {v: k for k, v in POSITION_MAP_V17.items()}

# (Di dời từ bridges_v16.py)
def get_position_name_V16(prize_index: int, digit_index: int, sub_prize_index: Optional[int] = None) -> Optional[str]:
    """
    (Hàm tiện ích GĐ 2) Lấy tên vị trí V17 từ (Giải, Index).
    """
    if sub_prize_index is not None:
        key = (prize_index, sub_prize_index, digit_index)
    else:
        key = (prize_index, digit_index)
    
    return _POSITION_NAME_MAP_V17.get(key)

# (Di dời từ bridges_v16.py)
def get_index_from_name_V16(name: str) -> Optional[Tuple]:
    """
    (Hàm tiện ích GĐ 2) Lấy (Giải, Index) từ tên vị trí V17.
    Hàm này được db_manager sử dụng.
    """
    return POSITION_MAP_V17.get(name)