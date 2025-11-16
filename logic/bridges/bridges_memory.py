# TÊN FILE: logic/bridges/bridges_memory.py
# NỘI DUNG THAY THẾ TOÀN BỘ (SỬA LỖI .to_dict() -> .to_list())

import sqlite3
from typing import List, Dict, Any, Optional, Callable
import pandas as pd
from collections import defaultdict
from .base_bridge import BaseBridge, BridgeContext, BridgeResult

# (SỬA LỖI GĐ 4) Import DataService để lấy Cầu Đã Lưu
try:
    from ..data_service import DataService
except ImportError:
    print("Lỗi: bridges_memory không thể import DataService.")
    # Fallback rỗng
    class DummyDataService:
        def get_all_managed_bridges(self, only_enabled: bool = False) -> List[Dict[str, Any]]:
            return []
    DataService = type('obj', (object,), {'get_instance': lambda: DummyDataService()})

# ===================================================================================
# I. CÁC HÀM TIỆN ÍCH BẠC NHỚ (ĐÃ SỬA LỖI)
# ===================================================================================

# (SỬA LỖI GĐ 4) Import hàm helper từ file classic
try:
    from .bridges_classic import get_giai_value, getAllLoto_V30
except ImportError:
    print("Lỗi: bridges_memory không thể import helpers từ bridges_classic.")
    def get_giai_value(row_data: List[Any], giai_index: int) -> str: return ""
    def getAllLoto_V30(row: List[Any]) -> List[str]: return []

# Tên của 27 Giải (dùng cho Bạc Nhớ)
LOTO_27_NAMES = [
    "GDB",
    "G1",
    "G2.1", "G2.2",
    "G3.1", "G3.2", "G3.3", "G3.4", "G3.5", "G3.6",
    "G4.1", "G4.2", "G4.3", "G4.4",
    "G5.1", "G5.2", "G5.3", "G5.4", "G5.5", "G5.6",
    "G6.1", "G6.2", "G6.3",
    "G7.1", "G7.2", "G7.3", "G7.4"
]

def get_27_loto_names() -> List[str]:
    """Trả về 27 tên giải (đã sắp xếp)."""
    return LOTO_27_NAMES

def get_27_loto_positions(row: List[Any]) -> List[str]:
    """Lấy TẤT CẢ 27 loto (2 số cuối) từ 1 hàng dữ liệu (đã là list)."""
    lotos = []
    try:
        # GDB (index 2)
        lotos.append(get_giai_value(row, 2)[-2:])
        # G1 (index 3)
        lotos.append(get_giai_value(row, 3)[-2:])
        
        # G2 (index 4)
        g2_nums = [n.strip() for n in get_giai_value(row, 4).split(',') if n.strip()]
        lotos.extend([n[-2:] for n in g2_nums])
        
        # G3 (index 5)
        g3_nums = [n.strip() for n in get_giai_value(row, 5).split(',') if n.strip()]
        lotos.extend([n[-2:] for n in g3_nums])
        
        # G4 (index 6)
        g4_nums = [n.strip() for n in get_giai_value(row, 6).split(',') if n.strip()]
        lotos.extend([n[-2:] for n in g4_nums])
        
        # G5 (index 7)
        g5_nums = [n.strip() for n in get_giai_value(row, 7).split(',') if n.strip()]
        lotos.extend([n[-2:] for n in g5_nums])
        
        # G6 (index 8)
        g6_nums = [n.strip() for n in get_giai_value(row, 8).split(',') if n.strip()]
        lotos.extend([n[-2:] for n in g6_nums])
        
        # G7 (index 9)
        g7_nums = [n.strip() for n in get_giai_value(row, 9).split(',') if n.strip()]
        lotos.extend([n[-2:] for n in g7_nums])

    except Exception as e:
        print(f"Lỗi get_27_loto_positions: {e}")
        # Trả về 27 loto rỗng nếu lỗi
        return ["00"] * 27 
        
    # Đảm bảo luôn trả về 27
    if len(lotos) != 27:
        # (Xử lý nếu dữ liệu thiếu)
        lotos.extend(["00"] * (27 - len(lotos)))
        
    return lotos[:27]

def calculate_bridge_stl(loto1_str: str, loto2_str: str, bridge_type: str) -> List[str]:
    """
    Tính STL Bạc Nhớ (Tổng hoặc Hiệu) từ 2 loto (chuỗi).
    """
    try:
        loto1 = int(loto1_str)
        loto2 = int(loto2_str)
        
        val = 0
        if bridge_type == 'sum':
            val = (loto1 + loto2) % 100
        elif bridge_type == 'diff':
            val = abs(loto1 - loto2) % 100
        else:
            return ["00", "00"]
            
        loto_chinh = str(val).zfill(2)
        loto_lon = loto_chinh[::-1] # Lộn
        
        return sorted([loto_chinh, loto_lon])
        
    except (ValueError, TypeError):
        return ["00", "00"]
    except Exception:
        return ["00", "00"]

# ===================================================================================
# II. LỚP PLUG-IN CẦU BẠC NHỚ (GĐ 2)
# ===================================================================================

class MemoryBridge(BaseBridge):
    """
    (GĐ 2) Plug-in triển khai các Cầu Bạc Nhớ (Tổng/Hiệu)
    Lớp này sẽ tải danh sách Cầu Bạc Nhớ Đã Lưu từ DataService khi khởi tạo.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.data_service = DataService.get_instance()
        self.load_managed_bridges() # Tải cầu khi khởi tạo
        self.loto_names = get_27_loto_names()
        self.num_positions = len(self.loto_names)
        self._build_bridge_map()

    def _initialize(self):
        """Tải danh sách cầu khi khởi tạo."""
        self.managed_bridges: List[Dict[str, Any]] = []

    def _build_bridge_map(self):
        """Xây dựng map (tên cầu -> (idx1, idx2, type)) để tra cứu nhanh."""
        self.bridge_map: Dict[str, Tuple[int, int, str]] = {}
        
        for i in range(self.num_positions):
            for j in range(i, self.num_positions):
                # Tổng
                name_sum = f"Tổng({self.loto_names[i]}+{self.loto_names[j]})"
                self.bridge_map[name_sum] = (i, j, 'sum')
                
                # Hiệu
                name_diff = f"Hiệu(|{self.loto_names[i]}-{self.loto_names[j]}|)"
                self.bridge_map[name_diff] = (i, j, 'diff')

    def load_managed_bridges(self):
        """Tải (hoặc tải lại) danh sách cầu từ DataService."""
        all_bridges = self.data_service.get_all_managed_bridges(only_enabled=True)
        # Chỉ giữ lại các cầu Bạc Nhớ
        self.managed_bridges = [
            b for b in all_bridges 
            if b.get("pos1_idx") == -1 and b.get("pos2_idx") == -1
        ]
        print(f"... (MemoryBridge) Đã tải {len(self.managed_bridges)} cầu bạc nhớ đã lưu.")

    def get_bridge_name(self) -> str:
        return "Memory_Managed_Bridges"

    def get_bridge_version(self) -> str:
        return "v1.0"

    def calculate_predictions(self, context: BridgeContext) -> List[BridgeResult]:
        """
        Tính toán dự đoán cho TẤT CẢ các Cầu Bạc Nhớ Đã Lưu.
        """
        results: List[BridgeResult] = []
        
        if len(context.historical_data) == 0:
            return []
            
        # (SỬA LỖI GĐ 4) Chỉ lấy hàng CUỐI CÙNG (N-1)
        # ===================================================================
        # (SỬA LỖI .to_dict() -> .to_list())
        # Chuyển đổi hàng cuối cùng thành LIST (thay vì dict)
        last_row_list = context.historical_data.iloc[-1].to_list()
        # ===================================================================

        try:
            # Lấy 27 loto của hàng cuối (N-1)
            last_lotos = get_27_loto_positions(last_row_list)
        except Exception as e:
            print(f"Lỗi khi lấy 27 Loto Positions: {e}")
            return []

        # Tải lại danh sách cầu (để cập nhật nếu có thay đổi)
        self.load_managed_bridges()
        
        for bridge in self.managed_bridges:
            bridge_id = bridge["name"]
            try:
                # Tra cứu thông tin cầu (idx1, idx2, type) từ map
                bridge_info = self.bridge_map.get(bridge_id)
                
                if bridge_info is None:
                    # print(f"Cảnh báo: Không tìm thấy logic cho cầu Bạc Nhớ: {bridge_id}")
                    continue

                idx1, idx2, bridge_type = bridge_info
                
                loto1 = last_lotos[idx1]
                loto2 = last_lotos[idx2]

                stl_predictions = calculate_bridge_stl(loto1, loto2, bridge_type)
                
                results.append(BridgeResult(
                    bridge_id=bridge_id,
                    predictions=stl_predictions,
                    prediction_type='STL',
                    metadata={'source': 'Memory_Managed'}
                ))
            except Exception as e:
                print(f"Lỗi khi chạy Cầu Bạc Nhớ {bridge_id}: {e}")
                
        return results