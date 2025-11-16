# TÊN FILE: logic/bridges/bridges_classic.py
# NỘI DUNG THAY THẾ TOÀN BỘ
# (SỬA LỖI LOGIC: Cập nhật logic V6 để xử lý Cặp Trùng (Kép) theo yêu cầu)

import sqlite3
from typing import List, Dict, Any, Optional, Callable, Tuple
import pandas as pd
from collections import defaultdict
from .base_bridge import BaseBridge, BridgeContext, BridgeResult

# ===================================================================================
# I. CÁC HÀM TIỆN ÍCH CƠ SỞ (ĐÃ SỬA LỖI)
# ===================================================================================

def get_giai_value(row_data: List[Any], giai_index: int) -> str:
    """Hàm helper an toàn để lấy dữ liệu giải (đã là list)."""
    try:
        # row_data[0] = MaSoKy, row_data[1] = Col_A_Ky
        # row_data[2] = GDB, row_data[3] = G1, ...
        return str(row_data[giai_index] or "")
    except (IndexError, TypeError):
        return ""

def get_loto_from_giai(giai_data_str: str, index: int) -> Optional[str]:
    """Lấy loto (2 số cuối) từ một chuỗi giải tại một vị trí index."""
    try:
        numbers = [n.strip() for n in giai_data_str.split(',') if n.strip()]
        if 0 <= index < len(numbers):
            number_str = numbers[index]
            if len(number_str) >= 2:
                return number_str[-2:]
    except Exception:
        pass
    return None

def calculate_loto_stats(loto_list: List[str]) -> Tuple[Dict[int, List[str]], Dict[int, List[str]]]:
    """Tách danh sách loto (['01', '23']) thành thống kê Đầu/Đuôi."""
    dau_stats = defaultdict(list)
    duoi_stats = defaultdict(list)
    for loto in loto_list:
        if len(loto) == 2:
            try:
                dau = int(loto[0])
                duoi = int(loto[1])
                dau_stats[dau].append(loto)
                duoi_stats[duoi].append(loto)
            except ValueError:
                continue
    return dau_stats, duoi_stats

def getAllLoto_V30(row: List[Any]) -> List[str]:
    """Lấy TẤT CẢ 27 loto từ 1 hàng dữ liệu (đã là list)."""
    loto_list = []
    # Lặp từ GDB (index 2) đến G7 (index 9)
    for i in range(2, 10): 
        giai_data_str = get_giai_value(row, i)
        numbers = [n.strip() for n in giai_data_str.split(',') if n.strip()]
        for num_str in numbers:
            if len(num_str) >= 2:
                loto_list.append(num_str[-2:])
            # Xử lý GDB có thể là 1 số duy nhất (ví dụ: 0)
            elif i == 2 and len(num_str) == 1:
                loto_list.append(num_str.zfill(2))
                
    return loto_list

# ===================================================================================
# II. ĐỊNH NGHĨA 15 CẦU CỔ ĐIỂN V5 (SỬA LỖI)
# ===================================================================================

def bridge_GDB_0(row): return get_loto_from_giai(get_giai_value(row, 2), 0)
def bridge_GDB_1(row): return get_loto_from_giai(get_giai_value(row, 2), 1)
def bridge_G1_0(row): return get_loto_from_giai(get_giai_value(row, 3), 0)
def bridge_G2_0(row): return get_loto_from_giai(get_giai_value(row, 4), 0)
def bridge_G2_1(row): return get_loto_from_giai(get_giai_value(row, 4), 1)
def bridge_G3_0(row): return get_loto_from_giai(get_giai_value(row, 5), 0)
def bridge_G3_1(row): return get_loto_from_giai(get_giai_value(row, 5), 1)
def bridge_G3_2(row): return get_loto_from_giai(get_giai_value(row, 5), 2)
def bridge_G3_3(row): return get_loto_from_giai(get_giai_value(row, 5), 3)
def bridge_G3_4(row): return get_loto_from_giai(get_giai_value(row, 5), 4)
def bridge_G3_5(row): return get_loto_from_giai(get_giai_value(row, 5), 5)
def bridge_G4_0(row): return get_loto_from_giai(get_giai_value(row, 6), 0)
def bridge_G4_1(row): return get_loto_from_giai(get_giai_value(row, 6), 1)
def bridge_G4_2(row): return get_loto_from_giai(get_giai_value(row, 6), 2)
def bridge_G4_3(row): return get_loto_from_giai(get_giai_value(row, 6), 3)

# Danh sách 15 cầu
ALL_15_BRIDGE_FUNCTIONS_V5: List[Callable] = [
    bridge_GDB_0, bridge_GDB_1, bridge_G1_0, bridge_G2_0, bridge_G2_1,
    bridge_G3_0, bridge_G3_1, bridge_G3_2, bridge_G3_3, bridge_G3_4, bridge_G3_5,
    bridge_G4_0, bridge_G4_1, bridge_G4_2, bridge_G4_3
]

# ===================================================================================
# III. LOGIC GHÉP LÔ (STL) (ĐÃ CẬP NHẬT TỪ V6 + LOGIC KÉP MỚI)
# ===================================================================================

BONG_DUONG_V30 = {
    '0': '5', '1': '6', '2': '7', '3': '8', '4': '9',
    '5': '0', '6': '1', '7': '2', '8': '3', '9': '4'
}

def getBongDuong_V30(digit):
    """(LOGIC V6) Lấy bóng dương của 1 ký tự số."""
    return BONG_DUONG_V30.get(str(digit), str(digit))

def taoSTL_V30_Bong(loto1_str: str, loto2_str: str) -> List[str]:
    """
    (LOGIC V6 + SỬA LỖI TRÙNG) 
    - Nếu a == b: Trả về [Kép, Bóng Kép] (ví dụ: [77, 22])
    - Nếu a != b: Trả về [Bóng(Tổng), Bóng(Hiệu)] (ví dụ: [56, 68])
    """
    try:
        # Đảm bảo đầu vào là chuỗi
        loto1_str = str(loto1_str)
        loto2_str = str(loto2_str)
        
        # (LOGIC KÉP MỚI) Xử lý cặp trùng (Kép)
        if loto1_str == loto2_str:
            # Lấy 1 chữ số (vì a và b giống nhau)
            digit_str = loto1_str[0] 
            
            kep = f"{digit_str}{digit_str}"
            
            # Lấy bóng của số đó
            bong_digit = getBongDuong_V30(digit_str)
            bong_kep = f"{bong_digit}{bong_digit}"
                
            return sorted([kep, bong_kep])
        
        # (LOGIC V6) Cho các cặp khác (Tổng/Hiệu + Bóng)
        loto1 = int(loto1_str)
        loto2 = int(loto2_str)
        
        # TÍNH TỔNG VÀ HIỆU
        tong = (loto1 + loto2) % 100
        hieu = abs(loto1 - loto2) # Hiệu (không mod 100)
        
        # TÍNH BÓNG CỦA TỔNG VÀ HIỆU
        tong_str = str(tong).zfill(2)
        hieu_str = str(hieu).zfill(2)
        
        # Áp dụng bóng cho từng chữ số
        bong_tong_1 = getBongDuong_V30(tong_str[0])
        bong_tong_2 = getBongDuong_V30(tong_str[1])
        
        bong_hieu_1 = getBongDuong_V30(hieu_str[0])
        bong_hieu_2 = getBongDuong_V30(hieu_str[1])
        
        # Ghép lại
        loto_bong_tong = f"{bong_tong_1}{bong_tong_2}"
        loto_bong_hieu = f"{bong_hieu_1}{bong_hieu_2}"

        # SẮP XẾP VÀ TRẢ VỀ
        return sorted([loto_bong_tong, loto_bong_hieu])
        
    except (ValueError, TypeError):
        return ["00", "00"]
    except Exception as e:
        print(f"Lỗi taoSTL_V30_Bong: {e}")
        return ["00", "00"]

# ===================================================================================
# IV. LỚP PLUG-IN CẦU CỔ ĐIỂN (GĐ 2)
# ===================================================================================

class ClassicBridge(BaseBridge):
    """
    (GĐ 2) Plug-in triển khai 15 Cầu Cổ Điển V5.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.bridge_functions = ALL_15_BRIDGE_FUNCTIONS_V5

    def get_bridge_name(self) -> str:
        return "Classic_15_Bridges"

    def get_bridge_version(self) -> str:
        return "v5.0"

    def calculate_predictions(self, context: BridgeContext) -> List[BridgeResult]:
        """
        Tính toán dự đoán cho 15 cầu cổ điển.
        """
        results: List[BridgeResult] = []
        
        if len(context.historical_data) == 0:
            return []
            
        # (SỬA LỖI GĐ 4) Chỉ lấy hàng CUỐI CÙNG (N-1)
        # (SỬA LỖI .to_dict() -> .to_list())
        # Chuyển đổi hàng cuối cùng thành LIST (thay vì dict)
        last_row = context.historical_data.iloc[-1].to_list()
        # ===================================================================

        for i, bridge_func in enumerate(self.bridge_functions):
            bridge_id = f"Classic_C{i+1}"
            try:
                loto1 = bridge_func(last_row)
                
                # (SỬA LỖI) Lấy loto2 từ hàm GDB_1 nếu là Cầu 1, ngược lại lấy GDB_0
                loto2_func = bridge_GDB_1 if i == 0 else bridge_GDB_0
                loto2 = loto2_func(last_row)

                if loto1 is None or loto2 is None:
                    continue

                # SỬ DỤNG LOGIC MỚI MÀ CHÚNG TA VỪA CẬP NHẬT
                stl_predictions = taoSTL_V30_Bong(loto1, loto2)
                
                results.append(BridgeResult(
                    bridge_id=bridge_id,
                    predictions=stl_predictions,
                    prediction_type='STL'
                ))
            except Exception as e:
                # Ghi lại lỗi nhưng không dừng lại
                print(f"Lỗi khi chạy {bridge_id}: {e}")
                
        return results