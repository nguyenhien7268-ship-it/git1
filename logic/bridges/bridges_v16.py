# TÊN FILE: logic/bridges/bridges_v16.py
# NỘI DUNG THAY THẾ TOÀN BỘ
# (SỬA LỖI IMPORT: Thêm TOTAL_V17_POSITIONS và alias get_name_from_index_V16)

import sqlite3
import re
from typing import List, Dict, Any, Optional, Callable
import pandas as pd
from .base_bridge import BaseBridge, BridgeContext, BridgeResult

# (SỬA LỖI GĐ 4) Import DataService để lấy Cầu Đã Lưu
try:
    from ..data_service import DataService
except ImportError:
    print("Lỗi: bridges_v16 không thể import DataService.")
    # Fallback rỗng
    class DummyDataService:
        def get_all_managed_bridges(self, only_enabled: bool = False) -> List[Dict[str, Any]]:
            return []
    DataService = type('obj', (object,), {'get_instance': lambda: DummyDataService()})

# ===================================================================================
# I. CÁC HÀM TIỆN ÍCH VÀ LOGIC TỪ V6 (ĐÃ CẬP NHẬT)
# ===================================================================================

# (SỬA LỖI GĐ 4) Import hàm helper từ file classic
try:
    # (CẬP NHẬT V8) Import BONG_DUONG_V30 để dùng cho V17_Shadow
    from .bridges_classic import get_giai_value, taoSTL_V30_Bong, BONG_DUONG_V30, getAllLoto_V30
except ImportError:
    print("Lỗi: bridges_v16 không thể import helpers từ bridges_classic.")
    def get_giai_value(row_data: List[Any], giai_index: int) -> str: return ""
    def taoSTL_V30_Bong(loto1_str: str, loto2_str: str) -> List[str]: return ["00", "00"]
    def getAllLoto_V30(r): return []
    BONG_DUONG_V30 = {} # Giả lập


def getDigits_V16(s: Any) -> List[int]:
    """(LOGIC V6) Lấy các chữ số từ một chuỗi/số."""
    if not s: return []
    return [int(d) for d in str(s) if d.isdigit()]

def getAllPositions_V16(row: List[Any]) -> List[Optional[int]]:
    """(LOGIC V6) Lấy 107 vị trí GỐC từ 1 hàng dữ liệu (list)."""
    positions = []
    try:
        # row[2] = GDB, row[3] = G1, ..., row[9] = G7
        positions.extend(getDigits_V16(str(row[2] or '0').strip().zfill(5))) # GĐB (row[2])
        positions.extend(getDigits_V16(str(row[3] or '0').strip().zfill(5))) # G1 (row[3])
        g2 = str(row[4] or '').split(',') # G2
        for g in g2: positions.extend(getDigits_V16(g.strip().zfill(5)))
        while len(positions) < 20: positions.append(None) # 5+5+10
        g3 = str(row[5] or '').split(',') # G3
        for g in g3: positions.extend(getDigits_V16(g.strip().zfill(5)))
        while len(positions) < 50: positions.append(None) # 20 + 30
        g4 = str(row[6] or '').split(',') # G4
        for g in g4: positions.extend(getDigits_V16(g.strip().zfill(4)))
        while len(positions) < 66: positions.append(None) # 50 + 16
        g5 = str(row[7] or '').split(',') # G5
        for g in g5: positions.extend(getDigits_V16(g.strip().zfill(4)))
        while len(positions) < 90: positions.append(None) # 66 + 24
        g6 = str(row[8] or '').split(',') # G6
        for g in g6: positions.extend(getDigits_V16(g.strip().zfill(3)))
        while len(positions) < 99: positions.append(None) # 90 + 9
        g7 = str(row[9] or '').split(',') # G7
        for g in g7: positions.extend(getDigits_V16(g.strip().zfill(2)))
        while len(positions) < 107: positions.append(None) # 99 + 8
        
        return positions[:107]
    except Exception as e:
        print(f"Lỗi getAllPositions_V16: {e}")
        return [None] * 107

# ===================================================================
# (SỬA LỖI IMPORT)
# Định nghĩa các biến mà bridge_manager_core.py cần
# ===================================================================
TOTAL_V17_POSITIONS = 107 # (1) Thêm hằng số 107

def getPositionName_V16(index: int) -> str:
    """(LOGIC V6) Lấy tên vị trí GỐC (0-106)."""
    if index < 0 or index > 106: return "NULL"
    if index < 5: return f"GDB[{index}]"
    if index < 10: return f"G1[{index - 5}]"
    if index < 20: return f"G2.{(index - 10) // 5 + 1}[{(index - 10) % 5}]"
    if index < 50: return f"G3.{(index - 20) // 5 + 1}[{(index - 20) % 5}]"
    if index < 66: return f"G4.{(index - 50) // 4 + 1}[{(index - 50) % 4}]"
    if index < 90: return f"G5.{(index - 66) // 4 + 1}[{(index - 66) % 4}]"
    if index < 99: return f"G6.{(index - 90) // 3 + 1}[{(index - 90) % 3}]"
    if index < 107: return f"G7.{(index - 99) // 2 + 1}[{(index - 99) % 2}]"
    return "ERROR"

get_name_from_index_V16 = getPositionName_V16 # (2) Thêm alias (bí danh)
# ===================================================================

def get_index_from_name_V16(name_str: str) -> Optional[int]:
    """
    (LOGIC V6) Lấy index (0-213) từ tên cầu (ví dụ GDB[0] hoặc Bong(GDB[0])).
    """
    processed_name = name_str.strip()
    is_bong = False
    
    # 1. Kiểm tra xem có phải cầu bóng không
    if processed_name.startswith("Bong(") and processed_name.endswith(")"):
        is_bong = True
        # Lấy phần tên gốc bên trong, ví dụ: "Bong(GDB[0])" -> "GDB[0]"
        processed_name = processed_name[5:-1].strip()

    # 2. Phân tích tên gốc
    match = re.match(r'(G\d+|GDB)\.?(\d+)?\[(\d+)\]', processed_name)
    if not match:
        print(f"Lỗi regex: Không thể phân tích '{name_str}'")
        return None
        
    g_name, g_num, g_idx = match.groups()
    base_index = None
    
    try:
        g_num = int(g_num) if g_num else 1
        g_idx = int(g_idx)
        
        if g_name == "GDB":
            if 0 <= g_idx <= 4: base_index = g_idx
        elif g_name == "G1":
            if 0 <= g_idx <= 4: base_index = 5 + g_idx
        elif g_name == "G2":
            if 1 <= g_num <= 2 and 0 <= g_idx <= 4: base_index = 10 + (g_num - 1) * 5 + g_idx
        elif g_name == "G3":
            if 1 <= g_num <= 6 and 0 <= g_idx <= 4: base_index = 20 + (g_num - 1) * 5 + g_idx
        elif g_name == "G4":
            if 1 <= g_num <= 4 and 0 <= g_idx <= 3: base_index = 50 + (g_num - 1) * 4 + g_idx
        elif g_name == "G5":
            if 1 <= g_num <= 6 and 0 <= g_idx <= 3: base_index = 66 + (g_num - 1) * 4 + g_idx
        elif g_name == "G6":
            if 1 <= g_num <= 3 and 0 <= g_idx <= 2: base_index = 90 + (g_num - 1) * 3 + g_idx
        elif g_name == "G7":
            if 1 <= g_num <= 4 and 0 <= g_idx <= 1: base_index = 99 + (g_num - 1) * 2 + g_idx
        
        if base_index is None:
            print(f"Lỗi logic: Tên cầu không hợp lệ '{name_str}'")
            return None
            
        # 3. Trả về chỉ số cuối cùng
        if is_bong:
            return base_index + 107 # Trả về chỉ số trong dải bóng (107-213)
        else:
            return base_index # Trả về chỉ số gốc (0-106)
            
    except Exception as e:
        print(f"Lỗi get_index_from_name_V16: {e}")
        return None

def getAllPositions_V17_Shadow(row: List[Any]) -> List[Optional[int]]:
    """
    (LOGIC V6) Lấy 214 vị trí = 107 vị trí gốc + 107 vị trí bóng.
    (Hàm này trả về list các SỐ NGUYÊN hoặc None)
    """
    # 1. Lấy 107 vị trí gốc (dùng hàm đã có)
    positions_goc = getAllPositions_V16(row)
    
    # 2. Tạo 107 vị trí bóng
    positions_bong = []
    for digit in positions_goc:
        if digit is None:
            positions_bong.append(None)
        else:
            try:
                # Chuyển số (int) về chuỗi (str) để tra cứu bóng
                bong_digit_str = BONG_DUONG_V30.get(str(digit), str(digit))
                positions_bong.append(int(bong_digit_str))
            except Exception:
                positions_bong.append(None)
                
    # 3. Nối hai danh sách lại
    positions_goc.extend(positions_bong)
    return positions_goc # Trả về danh sách 214 vị trí

def getPositionName_V17_Shadow(index: int) -> str:
    """
    (LOGIC V6) Lấy tên của vị trí trong 214 vị trí.
    """
    if index < 0 or index > 213: return "NULL"
    
    if index < 107:
        # 0-106 là vị trí gốc
        return getPositionName_V16(index) # Dùng hàm đã có
    else:
        # 107-213 là vị trí bóng
        index_goc = index - 107
        name_goc = getPositionName_V16(index_goc)
        return f"Bong({name_goc})"

# ===================================================================================
# II. LỚP PLUG-IN CẦU ĐÃ LƯU (GĐ 2)
# (Giữ nguyên cấu trúc V8, nhưng giờ sẽ gọi logic V6)
# ===================================================================================

class ManagedBridgeV16(BaseBridge):
    """
    (GĐ 2) Plug-in triển khai các Cầu Đã Lưu (V16/V17)
    Lớp này sẽ tải danh sách Cầu Đã Lưu từ DataService khi khởi tạo.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.data_service = DataService.get_instance()
        # (CẬP NHẬT) Tắt load_managed_bridges() ở đây,
        # vì nó sẽ được gọi trong calculate_predictions
        # self.load_managed_bridges() 
        self.managed_bridges: List[Dict[str, Any]] = []

    def load_managed_bridges(self):
        """Tải (hoặc tải lại) danh sách cầu từ DataService."""
        # (SỬA LỖI GĐ 4) Tải cầu từ DataService
        self.managed_bridges = self.data_service.get_all_managed_bridges(only_enabled=True)
        print(f"... (ManagedBridgeV16) Đã tải {len(self.managed_bridges)} cầu đã lưu.")

    def get_bridge_name(self) -> str:
        return "V17_Managed_Bridges"

    def get_bridge_version(self) -> str:
        # (CẬP NHẬT) Đổi tên phiên bản để phản ánh logic V6 (214 pos)
        return "v1.6_shadow_214"

    def calculate_predictions(self, context: BridgeContext) -> List[BridgeResult]:
        """
        Tính toán dự đoán cho TẤT CẢ các Cầu Đã Lưu (V16/V17).
        (Đã cập nhật để sử dụng logic 214 vị trí V6)
        """
        results: List[BridgeResult] = []
        
        # (SỬA LỖI 4%) Cần ít nhất 2 hàng (N-2, N-1)
        historical_data = context.historical_data
        if len(historical_data) < 2:
            return []
            
        # (SỬA LỖI GĐ 4) Lấy 2 hàng (N-2) và (N-1)
        prev_row = historical_data.iloc[0].to_list()
        last_row = historical_data.iloc[1].to_list()

        try:
            # (CẬP NHẬT) Gọi hàm V6 (214 vị trí)
            prev_positions = getAllPositions_V17_Shadow(prev_row)
            last_positions = getAllPositions_V17_Shadow(last_row)
        except Exception as e:
            print(f"Lỗi khi lấy V17 Positions (V6 logic): {e}")
            return []

        # Tải lại danh sách cầu (để cập nhật nếu có thay đổi)
        self.load_managed_bridges()
        
        for bridge in self.managed_bridges:
            bridge_id = bridge["name"]
            try:
                idx1 = bridge.get("pos1_idx")
                idx2 = bridge.get("pos2_idx")
                
                # Bỏ qua nếu không phải cầu V16 (ví dụ: Bạc NhNớ)
                if idx1 is None or idx2 is None or idx1 == -1:
                    continue

                # (LOGIC V16)
                # Vị trí 1 lấy ở HÀNG CUỐI (last_row / N-1)
                # Vị trí 2 lấy ở HÀNG TRƯỚC (prev_row / N-2)
                
                # (CẬP NHẬT) Kiểm tra trong phạm vi 214 vị trí
                if 0 <= idx1 < len(last_positions) and 0 <= idx2 < len(prev_positions):
                    a = last_positions[idx1]
                    b = prev_positions[idx2]
                else:
                    # Ghi log lỗi chỉ số nếu nó nằm ngoài phạm vi 0-213
                    print(f"Lỗi Chỉ Số (Index) cho cầu {bridge_id}: idx1={idx1}, idx2={idx2}. (Ngoài 0-213). Bỏ qua.")
                    continue

                if a is None or b is None:
                    continue

                # Gọi hàm `taoSTL_V30_Bong` (V6) đã được import từ classic
                stl_predictions = taoSTL_V30_Bong(a, b)
                
                results.append(BridgeResult(
                    bridge_id=bridge_id,
                    predictions=stl_predictions,
                    prediction_type='STL',
                    metadata={'source': 'V17_Managed (V6_Logic)'}
                ))
            except Exception as e:
                print(f"Lỗi khi chạy Cầu Đã Lưu {bridge_id} (idx1={idx1}, idx2={idx2}): {e}")
                
        return results