# TÊN FILE: logic/backtester.py
# NỘI DUNG THAY THẾ TOÀN BỘ (SỬA LỖI LOGIC 4%)

import sqlite3
# (V7.2 MP) Thêm thư viện Multi-Processing
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import traceback # Thêm để debug lỗi MP
# (V7.1) Chỉ giữ lại import Counter cho tiện ích chung
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Any, Optional
import pandas as pd # Cần thiết cho BridgeContext

# =======================================================================
# (GĐ 4) IMPORT BRIDGE MANAGER VÀ CÁC CẤU TRÚC BRIDGE
# =======================================================================
try:
    from .bridges.base_bridge import BridgeContext, BridgeResult
    from .bridges.bridge_manager_core import BridgeManager
    bridge_manager = BridgeManager.get_instance()
except ImportError as e:
    print(f"LỖI: backtester.py không thể import BridgeManager: {e}")
    # Fallback cho BridgeManager
    class DummyBridgeManager:
        def run_all_bridges(self, context): return []
    bridge_manager = DummyBridgeManager()


# =======================================================================
# (GĐ 1) THAY THẾ IMPORT CRUD CỦA DB_MANAGER BẰNG DATASERVICE
# =======================================================================
try:
    from .data_service import DataService
    # Khởi tạo DataService Singleton
    data_service = DataService.get_instance()
    
    # Lấy các hàm CRUD cần thiết từ DataService (đã được bao bọc)
    update_bridge_win_rate_batch = data_service.update_bridge_win_rate_batch
    update_bridge_k2n_cache_batch = data_service.update_bridge_k2n_cache_batch
    
    # Chỉ giữ lại DB_NAME từ db_manager (cho các hàm khác chưa refactor)
    from .db_manager import DB_NAME
    
    print(">>> (V7.0 - GĐ 1) Tải DataService cho backtester thành công.")
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: backtester.py không thể import DataService/DB_NAME: {e}")
    # Fallback cho các hàm CRUD (để tránh lỗi syntax)
    def update_bridge_win_rate_batch(*args, **kwargs): return False, "Lỗi DataService"
    def update_bridge_k2n_cache_batch(*args, **kwargs): return False, "Lỗi DataService"
    DB_NAME = 'data/xo_so_prizes_all_logic.db' 
# =======================================================================


# (V7.1) Chỉ giữ lại import config_manager
try:
    from .config_manager import SETTINGS
except ImportError:
    try:
        from config_manager import SETTINGS
    except ImportError:
        print("LỖI: backtester.py không thể import config_manager. Sử dụng giá trị mặc định.")
        SETTINGS = type('obj', (object,), {
            'STATS_DAYS': 7, 'GAN_DAYS': 15, 'HIGH_WIN_THRESHOLD': 47.0,
            'AUTO_ADD_MIN_RATE': 50.0, 'AUTO_PRUNE_MIN_RATE': 40.0,
            'K2N_RISK_START_THRESHOLD': 4, 'K2N_RISK_PENALTY_PER_FRAME': 0.5,
            'AI_PROB_THRESHOLD': 45.0, 
            'AI_SCORE_WEIGHT': 0.2
        })


# (V7.1) Giữ lại các Import Cần Thiết cho Backtest
try:
    # (GĐ 4) XÓA TẤT CẢ CÁC IMPORT HÀM CẦU TRỰC TIẾP
    from .data_repository import load_data_ai_from_db # Dù đã lỗi thời, giữ lại nếu code cũ vẫn gọi
    
    # (SỬA LỖI IMPORT) Thêm lại getAllLoto_V30 (cần thiết cho Backtest)
    from .bridges.bridges_classic import getAllLoto_V30
    
    # (SỬA LỖI IMPORT) Xóa toàn bộ khối 'from .utils import ...'
    # vì các hàm này không tồn tại trong file utils.py.
    # Logic sẽ được thay thế inline bên dưới.
    
    # (SỬA LỖI TIỀM ẨN) Xóa 'from .dashboard_analytics import get_top_scored_pairs'
    # để phá vỡ Import Vòng (Circular Import)

except ImportError as e:
    print(f"LỖI: backtester.py không thể import các module logic: {e}")


# ===================================================================================
# HÀM BACKTEST CƠ SỞ (CORE BACKTEST) - ĐÃ TÁI CẤU TRÚC (GĐ 4)
# ===================================================================================

# --- TONGHOP_TOP_CAU_RATE_V5 (Backtest N1) ---
def TONGHOP_TOP_CAU_RATE_V5(all_data_ai: List[List[Any]], managed_bridges: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, str]], str]:
    """
    (GĐ 4 - TÁI CẤU TRÚC) Thực hiện Backtest N1 BẰNG BridgeManager.
    """
    # (SỬA LỖI 4%) Yêu cầu ít nhất 3 hàng (N-2, N-1, N)
    if not all_data_ai or len(all_data_ai) < 3:
        return {}, "Không đủ dữ liệu lịch sử (cần ít nhất 3 ngày)."
        
    print("... (GĐ 4) Backtest N1 bằng BridgeManager: Bắt đầu...")
    
    bridge_performance: Dict[str, Dict[str, Any]] = defaultdict(lambda: {'hits': 0, 'total': 0, 'win_rate_text': '0.00%'})
    
    # Tạo DataFrame từ all_data_ai (list of lists) MỘT LẦN để tối ưu
    columns = ['MaSoKy', 'Col_A_Ky', 'Col_B_GDB', 'Col_C_G1', 'Col_D_G2', 'Col_E_G3', 'Col_F_G4', 'Col_G_G5', 'Col_H_G6', 'Col_I_G7']
    all_data_df = pd.DataFrame(all_data_ai, columns=columns)
    
    # ===================================================================
    # (SỬA LỖI 4%)
    # Bắt đầu lặp từ i = 2 (để có [i-2] và [i-1])
    # ===================================================================
    for i in range(2, len(all_data_ai)):
        current_row = all_data_ai[i] # Kỳ kết quả thực tế (N)
        
        actual_lotos = getAllLoto_V30(current_row) 
        
        # (SỬA LỖI 4%) Cung cấp 2 HÀNG (N-2 và N-1) cho Context
        # Lấy lát cắt (slice) [i-2:i] (bao gồm hàng i-2 và i-1)
        context_df = all_data_df.iloc[i-2:i]
        context = BridgeContext(historical_data=context_df)
        
        all_bridge_results: List[BridgeResult] = bridge_manager.run_all_bridges(context)
        # ===================================================================
        
        # Xử lý kết quả (Chấm điểm N1)
        for result in all_bridge_results:
            bridge_id = result.bridge_id
            
            if result.prediction_type != 'STL':
                continue

            bridge_performance[bridge_id]['total'] += 1
            
            is_hit = False
            for pred_loto in result.predictions:
                if pred_loto in actual_lotos: 
                    is_hit = True
                    break
            
            if is_hit:
                bridge_performance[bridge_id]['hits'] += 1

    # (SỬA LỖI HIỂN THỊ N1)
    # Tính toán Win Rate cuối cùng và trả về ĐẦY ĐỦ THÔNG TIN
    final_results: Dict[str, Dict[str, str]] = {}
    for bridge_id, perf in bridge_performance.items():
        if perf['total'] > 0:
            rate = (perf['hits'] / perf['total']) * 100
            win_rate_text = f"{rate:.2f}%"
            final_results[bridge_id] = {
                'win_rate_text': win_rate_text,
                'total_wins': perf['hits'],
                'total_days': perf['total']
            }
        else:
            final_results[bridge_id] = {
                'win_rate_text': '0.00%',
                'total_wins': 0,
                'total_days': 0
            }
            
    return final_results, f"Backtest N1 (GĐ 4) hoàn tất: {len(final_results)} cầu được xử lý."


# --- BACKTEST_MANAGED_BRIDGES_K2N (Backtest K2N) ---
def BACKTEST_MANAGED_BRIDGES_K2N(all_data_ai: List[List[Any]], managed_bridges: List[Dict[str, Any]], history: bool = True) -> Tuple[Dict[str, Dict[str, Any]], str]:
    """
    (GĐ 4 - TÁI CẤU TRÚC) Thực hiện Backtest K2N BẰNG BridgeManager.
    """
    # (SỬA LỖI 4%) Yêu cầu ít nhất 2 hàng cho lịch sử, 3 hàng nếu tính streak
    min_rows = 3 if history else 2
    if not all_data_ai or len(all_data_ai) < min_rows:
        return {}, f"Không đủ dữ liệu lịch sử (cần ít nhất {min_rows} ngày) để backtest K2N."
    
    print("... (GĐ 4) Backtest K2N bằng BridgeManager: Bắt đầu...")

    # 1. Tạo DataFrame
    columns = ['MaSoKy', 'Col_A_Ky', 'Col_B_GDB', 'Col_C_G1', 'Col_D_G2', 'Col_E_G3', 'Col_F_G4', 'Col_G_G5', 'Col_H_G6', 'Col_I_G7']
    all_data_df = pd.DataFrame(all_data_ai, columns=columns)

    # 2. Khởi tạo bộ theo dõi K2N cho *chỉ* các cầu Managed
    k2n_trackers: Dict[str, Dict[str, Any]] = {}
    managed_bridge_names = {b['name'] for b in managed_bridges}
    
    for name in managed_bridge_names:
        k2n_trackers[name] = {
            'win_rate_text': '0.00%', 
            'current_streak': 0,
            'max_lose_streak_k2n': 0,
            'next_prediction_stl': None
        }

    # 3. Lặp qua lịch sử để tính Streak
    # ===================================================================
    # (SỬA LỖI 4%)
    # ===================================================================
    if history and len(all_data_ai) > 2:
        # Bắt đầu lặp từ i = 2 (để có [i-2] và [i-1])
        for i in range(2, len(all_data_ai)):
            current_row = all_data_ai[i] # (N)
            
            # (SỬA LỖI 4%) Cung cấp 2 HÀNG (N-2 và N-1) cho Context
            context_df = all_data_df.iloc[i-2:i]
            
            actual_lotos = getAllLoto_V30(current_row)
            context = BridgeContext(historical_data=context_df)
            all_bridge_results: List[BridgeResult] = bridge_manager.run_all_bridges(context)

            managed_results = [r for r in all_bridge_results if r.bridge_id in managed_bridge_names]

            for result in managed_results:
                bridge_id = result.bridge_id
                
                is_hit_k2n = False
                for pred_loto in result.predictions:
                    if pred_loto in actual_lotos:
                        is_hit_k2n = True
                        break
                
                if is_hit_k2n:
                    k2n_trackers[bridge_id]['current_streak'] = 0 
                else:
                    k2n_trackers[bridge_id]['current_streak'] += 1 
                    if k2n_trackers[bridge_id]['current_streak'] > k2n_trackers[bridge_id]['max_lose_streak_k2n']:
                        k2n_trackers[bridge_id]['max_lose_streak_k2n'] = k2n_trackers[bridge_id]['current_streak']

    # 4. Lấy dự đoán cho ngày tiếp theo (dựa trên 2 hàng cuối cùng)
    # (SỬA LỖI 4%) Cung cấp 2 HÀNG cuối
    context_df_today = all_data_df.iloc[max(0, len(all_data_df)-2):]
    context_today = BridgeContext(historical_data=context_df_today)
    results_today: List[BridgeResult] = bridge_manager.run_all_bridges(context_today)
    # ===================================================================
    
    managed_results_today = [r for r in results_today if r.bridge_id in managed_bridge_names]
    
    for result in managed_results_today:
        bridge_id = result.bridge_id
        if bridge_id in k2n_trackers:
            if result.predictions:
                k2n_trackers[bridge_id]['next_prediction_stl'] = ",".join(sorted(result.predictions))
            else:
                k2n_trackers[bridge_id]['next_prediction_stl'] = None

    # 5. Cập nhật Tỷ lệ thắng (Lấy từ Backtest N1)
    for bridge in managed_bridges:
        if bridge['name'] in k2n_trackers:
            k2n_trackers[bridge['name']]['win_rate_text'] = bridge.get('win_rate_text', '0.00%')

    return k2n_trackers, f"Backtest K2N (GĐ 4) hoàn tất: {len(k2n_trackers)} cầu được xử lý."

# ===================================================================================
# WRAPPER: CẬP NHẬT TỶ LỆ THẮNG HÀNG LOẠT (N1)
# ===================================================================================

def run_and_update_all_bridge_rates(all_data_ai: List[List[Any]], 
                                    managed_bridges: List[Dict[str, Any]], 
                                    write_to_db: bool = True, 
                                    db_name: str = DB_NAME) -> Tuple[Dict[str, float], str]:
    """
    (V7.1 - GĐ 4) Wrapper Backtest N1. Gọi TONGHOP (đã refactor) và DataService.
    """
    if not all_data_ai:
        return {}, "Không có dữ liệu lịch sử để backtest."
    
    print("... Bắt đầu Backtest N1 (GĐ 4) cho tất cả các cầu...")
    
    # 1. Backtest N1 (Sử dụng hàm TONGHOP đã refactor GĐ 4)
    # (SỬA LỖI 4%) Hàm này giờ sẽ chạy đúng
    total_results_dict, message = TONGHOP_TOP_CAU_RATE_V5(
        all_data_ai=all_data_ai,
        managed_bridges=managed_bridges
    )
    
    # 2. Xử lý kết quả và tạo list cập nhật
    rate_data_list: List[Tuple[str, str]] = []
    
    # (SỬA LỖI HIỂN THỊ N1) Lọc kết quả để CHỈ CẬP NHẬT các cầu managed
    final_filtered_dict = {}
    
    for bridge in managed_bridges:
        bridge_name = bridge['name']
        if bridge_name in total_results_dict:
            # Lấy data của cầu managed
            bridge_data = total_results_dict[bridge_name]
            # Thêm vào list để cập nhật DB
            rate_data_list.append((bridge_data['win_rate_text'], bridge_name))
            # Thêm vào dict để trả về cho UI
            final_filtered_dict[bridge_name] = bridge_data
        else:
            # (Xử lý) Cầu managed nhưng không có kết quả (ví dụ: cầu mới)
            final_filtered_dict[bridge_name] = {
                'win_rate_text': '0.00%',
                'total_wins': 0,
                'total_days': 0
            }


    # 3. Cập nhật CSDL (Nếu được phép)
    if not rate_data_list:
        return final_filtered_dict, "Không có dữ liệu tỷ lệ thắng (Managed) để cập nhật DB."
        
    if write_to_db:
        print(f"... (GĐ 1) Đang cập nhật {len(rate_data_list)} bản ghi (Managed) vào CSDL qua DataService...")
        success, message_db = update_bridge_win_rate_batch(rate_data_list)
        
        if success:
            return final_filtered_dict, message_db
        else:
            return {}, message_db
    else:
        # (SỬA LỖI HIỂN THỊ N1) Trả về dict đã lọc
        return final_filtered_dict, f"Mô phỏng Backtest N1 hoàn tất ({len(final_filtered_dict)} cầu)."

# ===================================================================================
# WRAPPER: CẬP NHẬT CACHE K2N HÀNG LOẠT
# ===================================================================================

def run_and_update_all_bridge_K2N_cache(all_data_ai: List[List[Any]], 
                                        managed_bridges: List[Dict[str, Any]], 
                                        write_to_db: bool = True, 
                                        db_name: str = DB_NAME) -> Tuple[Dict[str, Any], str]:
    """
    (V7.1 - GĐ 4) Wrapper Backtest K2N. Gọi BACKTEST (đã refactor) và DataService.
    """
    if not all_data_ai:
        return {}, "Không có dữ liệu lịch sử để backtest K2N."
    
    print("... Bắt đầu Backtest K2N (GĐ 4) cho Cầu Đã Lưu (ManagedBridges)...")
    
    try:
        # 1. Backtest K2N (Sử dụng hàm đã refactor GĐ 4)
        # (SỬA LỖI 4%) Hàm này giờ sẽ chạy đúng
        full_pending_k2n_dict, message = BACKTEST_MANAGED_BRIDGES_K2N(
            all_data_ai=all_data_ai,
            managed_bridges=managed_bridges,
            history=True # Yêu cầu tính toán lại toàn bộ streak
        )
        
        # 2. Xử lý kết quả và tạo list cập nhật
        full_cache_data_list: List[Tuple[Any, ...]] = []
        
        for bridge_name, data in full_pending_k2n_dict.items():
            managed_bridge_data = next((b for b in managed_bridges if b['name'] == bridge_name), None)
            win_rate_text = managed_bridge_data.get('win_rate_text', '0.00%') if managed_bridge_data else '0.00%'

            cache_tuple = (
                win_rate_text,
                data.get('current_streak', 0),
                data.get('next_prediction_stl', None),
                data.get('max_lose_streak_k2n', 0), 
                bridge_name
            )
            full_cache_data_list.append(cache_tuple)
            
        if not full_cache_data_list:
            print("... (Cache K2N) Bỏ qua Cầu Đã Lưu (không có cầu nào hoặc bị lỗi).")
            return {}, "Không có dữ liệu cache K2N nào để cập nhật."

        # 3. Cập nhật CSDL (Nếu được phép)
        if write_to_db:
            print(f"... (GĐ 1) Đang cập nhật {len(full_cache_data_list)} bản ghi cache K2N vào CSDL qua DataService...")
            success, message_db = update_bridge_k2n_cache_batch(full_cache_data_list)
            
            if success:
                return full_pending_k2n_dict, message_db
            else:
                return {}, message_db
        else:
            return full_pending_k2n_dict, f"Mô phỏng Cache K2N hoàn tất ({len(full_cache_data_list)} cầu)."

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {}, f"Lỗi nghiêm trọng trong run_and_update_all_bridge_K2N_cache: {e}"

# ===================================================================================
# CÁC HÀM BACKTEST CŨ (ĐÃ LỖI THỜI - GIỮ LẠI LÀM STUB)
# ===================================================================================

def BACKTEST_15_CAU_K2N_V30_AI_V8(*args, **kwargs):
    """(GĐ 4) LỖI THỜI. Logic đã chuyển sang BridgeManager."""
    print("CẢNH BÁO: Hàm BACKTEST_15_CAU_K2N_V30_AI_V8 đã lỗi thời (V7.0).")
    return {}

def BACKTEST_15_CAU_N1_V31_AI_V8(*args, **kwargs):
    """(GĐ 4) LỖI THỜI. Logic đã chuyển sang BridgeManager."""
    print("CẢNH BÁO: Hàm BACKTEST_15_CAU_N1_V31_AI_V8 đã lỗi thời (V7.0).")
    return {}

def BACKTEST_CUSTOM_CAU_V16(*args, **kwargs):
    """(GĐ 4) LỖI THỜI. Logic đã chuyển sang BridgeManager."""
    print("CẢNH BÁO: Hàm BACKTEST_CUSTOM_CAU_V16 đã lỗi thời (V7.0).")
    return {}

def BACKTEST_MANAGED_BRIDGES_N1(*args, **kwargs):
    """(GĐ 4) LỖI THỜI. Logic đã chuyển sang BridgeManager."""
    print("CẢNH BÁO: Hàm BACKTEST_MANAGED_BRIDGES_N1 đã lỗi thời (V7.0).")
    return {}

def BACKTEST_MEMORY_BRIDGES(*args, **kwargs):
    """(GĐ 4) LỖI THỜI. Logic đã chuyển sang BridgeManager."""
    print("CẢNH BÁO: Hàm BACKTEST_MEMORY_BRIDGES đã lỗi thời (V7.0).")
    return {}

def TONGHOP_TOP_CAU_N1_V5(*args, **kwargs):
    """(GĐ 4) LỖI THỜI. Logic đã chuyển sang TONGHOP_TOP_CAU_RATE_V5 (V7.0)."""
    print("CẢNH BÁO: Hàm TONGHOP_TOP_CAU_N1_V5 đã lỗi thời (V7.0).")
    return {}