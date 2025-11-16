# TÊN FILE: logic/bridges/bridge_manager_core.py
# NỘI DUNG THAY THẾ TOÀN BỘ
# (SỬA LỖI: Đồng bộ Dò Cầu V17 để quét 214 vị trí Gốc + Bóng)
# (SỬA LỖI: Truyền chỉ số (idx) cho DataService để tránh lỗi vòng)

import os
import inspect
import importlib
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict # (GĐ 5) Thêm defaultdict

# (GĐ 3) Import SETTINGS và DataService
try:
    from ..config_manager import SETTINGS
except ImportError:
    try:
        from config_manager import SETTINGS
    except ImportError:
        print("LỖI: không thể import config_manager trong bridge_manager_core.py")
        SETTINGS = type('obj', (object,), {
            'AUTO_ADD_MIN_RATE': 50.0, 
            'AUTO_PRUNE_MIN_RATE': 40.0,
            'get': lambda k, d: d # (SỬA LỖI) Thêm .get()
        })

# (GĐ 3) Thay thế DB/Repo imports bằng DataService
try:
    from ..data_service import DataService
    data_service = DataService.get_instance()
    
    # Lấy các hàm CRUD cần thiết từ DataService
    upsert_managed_bridge = data_service.upsert_managed_bridge
    update_managed_bridge = data_service.upsert_managed_bridge # (Alias)
    get_all_managed_bridges = data_service.get_all_managed_bridges
    
    from ..db_manager import DB_NAME
except ImportError as e:
    print(f"Lỗi: Không thể import DataService trong bridge_manager_core.py: {e}")
    DB_NAME = 'data/xo_so_prizes_all_logic.db' 
    def upsert_managed_bridge(n, d, r, p1n, p2n, p1i, p2i): return False, "Lỗi Import" # (Sửa)
    def update_managed_bridge(id, d, e): return False, "Lỗi Import"
    def get_all_managed_bridges(o): return []

# (GĐ 3) Import BaseBridge và các Bridge đã tạo (để đảm bảo chúng được tải)
from .base_bridge import BaseBridge, BridgeContext, BridgeResult
from .bridges_classic import ClassicBridge
from .bridges_v16 import ManagedBridgeV16
from .bridges_memory import MemoryBridge

# ===================================================================================
# (GĐ 5) IMPORT CÁC HÀM HELPERS ĐỂ DÒ CẦU
# ===================================================================================
try:
    from .bridges_classic import getAllLoto_V30, taoSTL_V30_Bong
    # (SỬA LỖI ĐỒNG BỘ) Import hàm 214 vị trí
    from .bridges_v16 import (
        getAllPositions_V17_Shadow, 
        getPositionName_V17_Shadow # <-- (Sửa) Lấy hàm 214 tên
    )
    from .bridges_memory import get_27_loto_positions, get_27_loto_names, calculate_bridge_stl
except ImportError as e:
    print(f"LỖI (GĐ 5): Không thể import helpers để Dò Cầu: {e}")
    def getAllLoto_V30(r): return []
    def taoSTL_V30_Bong(a, b): return ["00", "00"]
    def getAllPositions_V17_Shadow(r): return [None] * 214 # (Sửa) 214
    def getPositionName_V17_Shadow(i): return f"Loi{i}" # (Sửa)
    def get_27_loto_positions(r): return ["00"] * 27
    def get_27_loto_names(): return [f"Loi{i}" for i in range(27)]
    def calculate_bridge_stl(a, b, t): return ["00", "00"]
# ===================================================================================


# ===================================================================================
# I. (GĐ 3) BỘ QUẢN LÝ CẦU MỚI (PLUG-IN ARCHITECTURE)
# ===================================================================================

class BridgeManager:
    """
    (GĐ 3) Bộ quản lý cầu Singleton.
    Nhiệm vụ: Tự động phát hiện, khởi tạo và điều hành tất cả các Bridge plug-in.
    """
    _instance: Optional['BridgeManager'] = None
    
    def __init__(self):
        # Ngăn chặn khởi tạo lại
        if hasattr(self, 'bridges'):
            return 
        
        self.bridges: List[BaseBridge] = []
        self._discover_bridges()

    @staticmethod
    def get_instance():
        """Lấy thể hiện duy nhất của BridgeManager."""
        if BridgeManager._instance is None:
            BridgeManager._instance = BridgeManager()
        return BridgeManager._instance

    def _discover_bridges(self):
        """
        (GĐ 3) Quét thư mục hiện tại (logic/bridges) để tìm tất cả các lớp
        kế thừa từ BaseBridge (trừ BaseBridge chính nó) và khởi tạo chúng.
        """
        print("... (BridgeManager) Bắt đầu tự động phát hiện Bridge plug-in...")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Danh sách các module chứa bridge cần kiểm tra
        bridge_modules = ["bridges_classic", "bridges_v16", "bridges_memory"]
        
        for module_name in bridge_modules:
            try:
                # Import module
                module = importlib.import_module(f".{module_name}", package='logic.bridges')
                
                # Duyệt qua các thành viên của module để tìm class Bridge
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BaseBridge) and obj != BaseBridge:
                        # Khởi tạo và thêm vào danh sách
                        try:
                            # Khởi tạo lớp cầu (plug-in)
                            self.bridges.append(obj()) 
                            print(f"  > Đã tải Plug-in: {obj().get_bridge_name()} (version: {obj().get_bridge_version()})")
                        except Exception as e:
                            print(f"  > Lỗi khởi tạo Bridge {name} từ {module_name}: {e}")

            except Exception as e:
                print(f"  > Lỗi Import module {module_name}: {e}")

        print(f"... (BridgeManager) Phát hiện hoàn tất. Tổng cộng {len(self.bridges)} Bridge Plug-in đã được tải.")

    def get_active_bridges(self) -> List[BaseBridge]:
        """Trả về danh sách tất cả các Bridge plug-in đã được tải."""
        return self.bridges

    def run_all_bridges(self, context: BridgeContext) -> List[BridgeResult]:
        """
        (GĐ 3) Chạy tất cả các Bridge plug-in đã tải và thu thập kết quả.
        """
        all_results: List[BridgeResult] = []
        
        for bridge in self.bridges:
            try:
                # Chạy tính toán
                bridge_results = bridge.calculate_predictions(context)
                all_results.extend(bridge_results)
            except Exception as e:
                print(f"Lỗi khi chạy Bridge Plug-in '{bridge.get_bridge_name()}': {e}")

        return all_results


# ===================================================================================
# II. (SỬA LỖI GĐ 5) CÁC HÀM DÒ CẦU (REFACTOR)
# ===================================================================================

# (SỬA LỖI ĐỒNG BỘ) Định nghĩa tổng số vị trí V6 là 214
TOTAL_V16_V6_POSITIONS = 214 

def TIM_CAU_TOT_NHAT_V16(all_data_ai, db_name=DB_NAME):
    """
    (SỬA LỖI GĐ 5 & ĐỒNG BỘ V6) 
    Tìm các cầu mới V17/Bong V17 tốt nhất (214 vị trí)
    """
    print(f"... (GĐ 5) Bắt đầu Dò Cầu V17/Bóng (Logic V6 - {TOTAL_V16_V6_POSITIONS} vị trí)...")
    
    # 1. Lấy cài đặt
    AUTO_ADD_MIN_RATE = SETTINGS.get('AUTO_ADD_MIN_RATE', 45.0)
    
    # 2. Xây dựng danh sách các cặp (i, j) để kiểm tra
    bridge_tasks: List[Tuple[int, int]] = []
    
    # (SỬA LỖI ĐỒNG BỘ) Lặp 214 vị trí
    for i in range(TOTAL_V16_V6_POSITIONS):
        for j in range(i, TOTAL_V16_V6_POSITIONS): # Lặp (i, i) -> (i, 213)
            bridge_tasks.append((i, j))
            
    print(f"... (GĐ 5) Sẽ quét {len(bridge_tasks)} cặp vị trí V17/Bóng (logic V6).")

    # 3. Khởi tạo bộ đếm
    win_counts = defaultdict(int)
    total_days = 0
    
    # 4. Lặp qua lịch sử (Bỏ qua 2 ngày đầu)
    if len(all_data_ai) < 3:
        return False, "Không đủ dữ liệu (cần > 2 ngày) để dò cầu V17."
        
    for k in range(2, len(all_data_ai)):
        try:
            row_n_minus_2 = all_data_ai[k-2] # (N-2)
            row_n_minus_1 = all_data_ai[k-1] # (N-1)
            row_n = all_data_ai[k]           # (N)
            
            actual_lotos = set(getAllLoto_V30(row_n))
            if not actual_lotos:
                continue

            # Lấy vị trí (chỉ 1 lần mỗi ngày)
            # (SỬA LỖI ĐỒNG BỘ) Hàm này đã trả về 214 vị trí
            pos_n_minus_2 = getAllPositions_V17_Shadow(row_n_minus_2)
            pos_n_minus_1 = getAllPositions_V17_Shadow(row_n_minus_1)
            
            total_days += 1
            
            # 5. Lặp qua các cặp (tasks)
            for (i, j) in bridge_tasks:
                a = pos_n_minus_1[i] # Lấy từ N-1 (0-213)
                b = pos_n_minus_2[j] # Lấy từ N-2 (0-213)
                
                if a is None or b is None:
                    continue
                    
                stl = taoSTL_V30_Bong(a, b) # (Sử dụng logic V6)
                
                if stl[0] in actual_lotos or stl[1] in actual_lotos:
                    win_counts[(i, j)] += 1
        except Exception:
            continue # Bỏ qua ngày bị lỗi

    if total_days == 0:
        return False, "Không có ngày hợp lệ nào để backtest."

    # 6. Xử lý kết quả và lưu vào DB
    added_count = 0
    updated_count = 0
    
    for (i, j), hits in win_counts.items():
        rate = (hits / total_days) * 100
        
        if rate >= AUTO_ADD_MIN_RATE:
            try:
                # (SỬA LỖI ĐỒNG BỘ) Sử dụng hàm 214 tên
                pos1_name = getPositionName_V17_Shadow(i)
                pos2_name = getPositionName_V17_Shadow(j)
                
                if pos1_name is None or pos2_name is None:
                    continue
                
                # Tên cầu V17/Bóng
                bridge_name = f"{pos1_name} + {pos2_name}"
                description = f"V17/Bóng Tự động (Tỷ lệ: {rate:.1f}%)"
                win_rate_text = f"{rate:.2f}%"
                
                # (SỬA LỖI CIRCULAR IMPORT)
                # Truyền đầy đủ 7 tham số cho hàm upsert mới
                success, msg = upsert_managed_bridge(
                    bridge_name, description, win_rate_text,
                    pos1_name, pos2_name, i, j # <-- i và j là pos1_idx, pos2_idx
                )
                if success:
                    if "Đã thêm" in msg:
                        added_count += 1
                    elif "Đã cập nhật" in msg:
                        updated_count += 1
            except Exception:
                continue

    return True, f"Dò cầu V17/Bóng (214) Hoàn tất. Đã thêm: {added_count} cầu. Đã cập nhật: {updated_count} cầu."


def TIM_CAU_BAC_NHO_TOT_NHAT(all_data_ai, db_name=DB_NAME):
    """
    (SỬA LỖI GĐ 5) Tìm các cầu Bạc Nhớ tốt nhất.
    (Hàm này giữ nguyên, không thay đổi)
    """
    print("... (GĐ 5) Bắt đầu Dò Cầu Bạc Nhớ (Tối ưu)...")
    
    # 1. Lấy cài đặt
    AUTO_ADD_MIN_RATE = SETTINGS.get('AUTO_ADD_MIN_RATE', 45.0)
    
    # 2. Xây dựng danh sách các cặp (i, j, type) để kiểm tra
    loto_names = get_27_loto_names()
    num_positions = len(loto_names)
    if num_positions != 27:
        return False, "Lỗi: Không thể tải 27 vị trí Bạc Nhớ."
        
    bridge_tasks: List[Tuple[int, int, str]] = []
    for i in range(num_positions):
        for j in range(i, num_positions):
            bridge_tasks.append((i, j, 'sum'))
            bridge_tasks.append((i, j, 'diff'))
            
    print(f"... (GĐ 5) Sẽ quét {len(bridge_tasks)} cặp vị trí Bạc Nhớ.")

    # 3. Khởi tạo bộ đếm
    win_counts = defaultdict(int)
    total_days = 0
    
    # 4. Lặp qua lịch sử (Bỏ qua 1 ngày đầu)
    if len(all_data_ai) < 2:
        return False, "Không đủ dữ liệu (cần > 1 ngày) để dò cầu Bạc Nhớ."
        
    for k in range(1, len(all_data_ai)):
        try:
            row_n_minus_1 = all_data_ai[k-1] # (N-1)
            row_n = all_data_ai[k]           # (N)
            
            actual_lotos = set(getAllLoto_V30(row_n))
            if not actual_lotos:
                continue

            # Lấy vị trí (chỉ 1 lần mỗi ngày)
            lotos_n_minus_1 = get_27_loto_positions(row_n_minus_1)
            
            total_days += 1
            
            # 5. Lặp qua các cặp (tasks)
            for (i, j, type) in bridge_tasks:
                loto1 = lotos_n_minus_1[i]
                loto2 = lotos_n_minus_1[j]
                
                stl = calculate_bridge_stl(loto1, loto2, type)
                
                if stl[0] in actual_lotos or stl[1] in actual_lotos:
                    win_counts[(i, j, type)] += 1
        except Exception:
            continue # Bỏ qua ngày bị lỗi

    if total_days == 0:
        return False, "Không có ngày hợp lệ nào để backtest (BN)."

    # 6. Xử lý kết quả và lưu vào DB
    added_count = 0
    updated_count = 0
    
    for (i, j, type), hits in win_counts.items():
        rate = (hits / total_days) * 100
        
        if rate >= AUTO_ADD_MIN_RATE:
            try:
                # Tạo tên cầu
                name1 = loto_names[i]
                name2 = loto_names[j]
                if type == 'sum':
                    bridge_name = f"Tổng({name1}+{name2})"
                else:
                    bridge_name = f"Hiệu(|{name1}-{name2}|)"
                
                description = f"BN Tự động (Tỷ lệ: {rate:.1f}%)"
                win_rate_text = f"{rate:.2f}%"
                
                # (SỬA LỖI CIRCULAR IMPORT)
                # Truyền đầy đủ 7 tham số cho hàm upsert mới
                success, msg = upsert_managed_bridge(
                    bridge_name, description, win_rate_text,
                    "BAC_NHO", "BAC_NHO", -1, -1 # <-- Thêm 4 tham số
                )
                if success:
                    if "Đã thêm" in msg:
                        added_count += 1
                    elif "Đã cập nhật" in msg:
                        updated_count += 1
            except Exception:
                continue

    return True, f"Dò cầu Bạc Nhớ Hoàn tất. Đã thêm: {added_count} cầu. Đã cập nhật: {updated_count} cầu."


def find_and_auto_manage_bridges(all_data_ai: List[List[Any]], db_name: str = DB_NAME) -> Tuple[bool, str]:
    """
    (SỬA LỖI GĐ 5) Wrapper tổng hợp: Chạy tìm cầu V17 và Bạc Nhớ.
    """
    # 1. Chạy tìm cầu V17
    success_v16, msg_v16 = TIM_CAU_TOT_NHAT_V16(all_data_ai, db_name) 
    
    # 2. Chạy tìm cầu Bạc Nhớ
    success_bn, msg_bn = TIM_CAU_BAC_NHO_TOT_NHAT(all_data_ai, db_name)
    
    return True, f"Tìm cầu V17/Bóng (V6): {msg_v16}\nTìm cầu BN: {msg_bn}"


def prune_bad_bridges(db_name: str = DB_NAME) -> str:
    """
    (V7.1) Vô hiệu hóa các cầu đã lưu (Managed Bridges) có tỷ lệ thắng thấp.
    (GĐ 3) Đã sử dụng DataService (không cần db_name)
    """
    
    AUTO_PRUNE_MIN_RATE = SETTINGS.get('AUTO_PRUNE_MIN_RATE', 40.0)
    
    # Gọi hàm đã map (get_all_managed_bridges) không cần db_name
    managed_bridges = get_all_managed_bridges(only_enabled=True) 
    
    managed_bridges_map = {b['name']: b for b in managed_bridges}
    
    if not managed_bridges_map:
         return "Lỗi: Không có cầu nào được Bật để lọc."

    print(f"... (Lọc Cầu Yếu) Đang kiểm tra {len(managed_bridges_map)} cầu đã bật...")
    disabled_count = 0
    
    for bridge_name, bridge_data in managed_bridges_map.items():
        try:
            win_rate_str = str(bridge_data.get('win_rate_text', '0%')).replace('%', '')
            
            if not win_rate_str or win_rate_str == "N/A":
                continue
                
            win_rate = float(win_rate_str)
            
            if win_rate < AUTO_PRUNE_MIN_RATE:
                bridge_id = bridge_data['id']
                old_desc = bridge_data['description']
                
                # (SỬA LỖI) Hàm update_managed_bridge chỉ cần 3 tham số
                # (nó đã được trỏ đến upsert_managed_bridge ở Dòng 35 là sai)
                # Tạm thời, chúng ta gọi thẳng DataService
                data_service.update_managed_bridge(bridge_id, old_desc, 0) # 0 = Vô hiệu hóa
                disabled_count += 1
                
        except Exception as e_row:
            print(f"Lỗi xử lý lọc cầu: {bridge_name}, Lỗi: {e_row}")

    return f"Hoàn tất: Đã tự động vô hiệu hóa {disabled_count} cầu kém hiệu quả (dưới {AUTO_PRUNE_MIN_RATE}%)."