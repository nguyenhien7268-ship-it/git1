"""
==================================================================================
LOTTERY SERVICE API (BỘ ĐIỀU PHỐI) - (V7.2 MP & MLOps & Caching UPGRADE - GĐ 5 REF)
==================================================================================
"""
import os 
from collections import defaultdict, Counter
# (V7.2 MP) THAY THẾ threading BẰNG multiprocessing
import multiprocessing 
from multiprocessing import Process, Queue
from multiprocessing.queues import Empty # Cần cho việc quản lý Queue an toàn
import pandas as pd # Cần cho BridgeContext

# ==================================================================================
# (GĐ 5) IMPORT BRIDGE MANAGER VÀ CÁC CẤU TRÚC BRIDGE
# ==================================================================================
try:
    from logic.bridges.base_bridge import BridgeContext, BridgeResult
    from logic.bridges.bridge_manager_core import BridgeManager
    bridge_manager = BridgeManager.get_instance()
    print(">>> (V7.0 - GĐ 5) Tải BridgeManager và BridgeContext thành công.")
except ImportError as e:
    print(f"LỖI: Không thể import BridgeManager/Context trong lottery_service.py: {e}")
    class DummyBridgeManager:
        def run_all_bridges(self, context): return []
    bridge_manager = DummyBridgeManager()


# ==================================================================================
# (GĐ 1) THAY THẾ DB_MANAGER VÀ DATA_REPOSITORY BẰNG DATASERVICE
# ==================================================================================
try:
    from logic.data_service import DataService
    # Khởi tạo DataService Singleton
    data_service = DataService.get_instance()
    
    # Lấy các hàm đã được tích hợp/wrapped từ DataService
    load_data_ai_from_db = data_service.load_data_ai_from_db
    get_all_managed_bridges = data_service.get_all_managed_bridges
    
    # Vẫn cần DB_NAME và setup_database cho các hàm chưa refactor (như data_parser)
    from logic.db_manager import DB_NAME
    from logic.db_manager import setup_database 
    
    print(">>> (V7.0 - GĐ 1) Tải logic.data_service (Trung tâm) thành công.")
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.data_service: {e}")
    # Fallback
    def load_data_ai_from_db(): return None, f"Lỗi: Không tìm thấy DataService: {e}"
    def get_all_managed_bridges(only_enabled=False): return []
    data_service = None
    DB_NAME = 'data/xo_so_prizes_all_logic.db'
    def setup_database(): return None, None
# ==================================================================================


# 2. Từ logic.data_parser
try:
    from logic.data_parser import (
        parse_and_insert_data,
        parse_and_APPEND_data,
        parse_and_APPEND_data_TEXT
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.data_parser: {e}")

# 3. Từ logic.bridges_classic (Chỉ cần hàm thống kê nếu có, không cần hàm cầu)
try:
    from logic.bridges.bridges_classic import ( # ĐÃ SỬA
        getAllLoto_V30,
        calculate_loto_stats,
        # ALL_15_BRIDGE_FUNCTIONS_V5 # ĐÃ XÓA
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.bridges.bridges_classic: {e}") # ĐÃ SỬA

# 4. (FIX B & C) Từ logic.backtester: CHỈ GIỮ LẠI CÁC HÀM BACKTEST THUẦN
try:
    from logic.backtester import (
        TONGHOP_TOP_CAU_N1_V5,
        TONGHOP_TOP_CAU_RATE_V5,
        BACKTEST_15_CAU_K2N_V30_AI_V8,
        BACKTEST_15_CAU_N1_V31_AI_V8,
        BACKTEST_CUSTOM_CAU_V16,
        BACKTEST_MANAGED_BRIDGES_N1,
        BACKTEST_MANAGED_BRIDGES_K2N, 
        run_and_update_all_bridge_rates,
        run_and_update_all_bridge_K2N_cache,
        BACKTEST_MEMORY_BRIDGES,
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.backtester: {e}")

# 4.1. (MỚI - FIX B) TỪ LOGIC.BRIDGE_MANAGER_CORE (Quản lý Cầu)
try:
    from logic.bridges.bridge_manager_core import ( # ĐÃ SỬA
        TIM_CAU_TOT_NHAT_V16, 
        TIM_CAU_BAC_NHO_TOT_NHAT,
        find_and_auto_manage_bridges,
        prune_bad_bridges
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.bridges.bridge_manager_core: {e}") # ĐÃ SỬA

# 4.2. (MỚI - FIX C) TỪ LOGIC.DASHBOARD_ANALYTICS (Analytics & Chấm điểm)
try:
    from logic.dashboard_analytics import (
        get_top_scored_pairs, 
        get_loto_stats_last_n_days, 
        get_loto_gan_stats,
        get_prediction_consensus,
        get_high_win_rate_predictions,
        get_top_memory_bridge_predictions,
        get_historical_dashboard_data,
        generate_full_optimization_cache, # (MỚI V7.2 Caching)
        CACHE_FILE_PATH # (MỚI V7.2 Caching)
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.dashboard_analytics: {e}")


# ==========================================================================
# (MỚI V6.0) 5. TỪ LOGIC.ML_MODEL (BỘ NÃO AI)
# ==========================================================================
try:
    from logic.ml_model import (
        train_ai_model,
        get_ai_predictions,
        evaluate_current_model # (MỚI V7.2 MLOps) Import hàm đánh giá
    )
    print(">>> (V6.0) Tải logic.ml_model (AI) thành công.")
except ImportError as e:
    print(f"LỖỖI NGHIÊM TRỌNG: Không thể import logic.ml_model (AI): {e}")
    # Giả lập hàm nếu lỗi 
    def train_ai_model(all_data, daily_bridge_predictions): 
        return False, f"Lỗi: Không tìm thấy logic.ml_model.py hoặc lỗi import nội bộ: {e}"
    def get_ai_predictions(all_data, bridge_predictions_for_today): 
        return None, f"Lỗi: Không tìm thấy logic.ml_model.py hoặc lỗi import nội bộ: {e}"
    # (MỚI V7.2 MLOps) Giả lập hàm đánh giá nếu lỗi
    def evaluate_current_model():
        return None, None, f"Lỗi: Không tìm thấy logic.ml_model.py: {e}"
# ==========================================================================


# ==========================================================================
# (MỚI V7.0 GĐ 5) HÀM TÍNH FEATURE MỚI DÙNG BRIDGE MANAGER
# ==========================================================================
try:
    # (GĐ 5) XÓA CÁC IMPORT CẦU CŨ KHÔNG CẦN THIẾT
    from logic.config_manager import SETTINGS # Vẫn cần SETTINGS
    # XÓA: from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong
    # XÓA: from logic.bridges.bridges_memory import get_27_loto_positions, calculate_bridge_stl, get_27_loto_names
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic cầu/repo: {e}")
    # Cần định nghĩa lại các hàm hỗ trợ cơ bản đã bị xóa/thay đổi
    def _parse_win_rate_text(win_rate_text): return 0.0
    def _standardize_pair(stl_list): return None
    # End Fallback

def _parse_win_rate_text(win_rate_text):
    """(V7.0 G2) Parses '55.10%' to 55.10 or 0.0 if invalid."""
    if not win_rate_text:
        return 0.0
    try:
        # Remove '%' và convert to float
        return float(win_rate_text.strip().replace('%', ''))
    except ValueError:
        return 0.0

def _standardize_pair(stl_list):
    """Helper: ['30', '01'] -> '01-30'. (Di chuyển từ ml_model.py)"""
    # Hàm này không còn được dùng trong logic _get_daily_bridge_predictions mới. Giữ lại cho tương thích.
    if not stl_list or len(stl_list) != 2: return None
    return "-".join(sorted(stl_list))

def _get_daily_bridge_predictions(all_data_ai):
    """
    (V7.0 GĐ 5 - TÁI CẤU TRÚC) 
    Lặp qua CSDL để lấy dự đoán N1 của TẤT CẢ các cầu cho TẤT CẢ các ngày bằng BridgeManager. 
    Tính toán cả Feature Counts và Q-Features.
    """
    print("... (V7.0 GĐ 5 Feature Extraction) Bước 1: Tính toán dự đoán cầu cho toàn bộ lịch sử bằng BridgeManager...")
    
    # ĐỊNH DẠNG MỚI: { 'Kỳ 123': { 'loto_01': {'v5_count': 1, 'q_avg_win_rate': 55.1, ...}, 'loto_02': {...} } }
    daily_predictions_by_loto = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    
    # Lấy managed_bridges từ DataService (chứa cả Q-Features)
    managed_bridges = get_all_managed_bridges(only_enabled=True) 
    
    # Xử lý Q-Features trên managed_bridges MỘT LẦN 
    managed_bridges_map = {}
    for bridge in managed_bridges:
        bridge['win_rate_float'] = _parse_win_rate_text(bridge.get('win_rate_text'))
        bridge['k2n_risk'] = bridge.get('max_lose_streak_k2n', 999) 
        bridge['current_streak_int'] = bridge.get('current_streak', -999)
        managed_bridges_map[bridge['name']] = bridge

    # Lặp qua toàn bộ CSDL
    for k in range(1, len(all_data_ai)):
        prev_row = all_data_ai[k-1]
        current_row = all_data_ai[k]
        current_ky = str(current_row[0])
        
        if k % 100 == 0:
            print(f"... (V7.0 GĐ 5 Feature Extraction) Bước 1: Đã xử lý {k}/{len(all_data_ai)} ngày (dự đoán cầu)")

        # 1. TẠO CONTEXT VÀ CHẠY BRIDGE MANAGER
        # Chuyển List[List] về DataFrame
        context_df = pd.DataFrame([prev_row], columns=[f'Col_{j}' for j in range(len(prev_row))])
        context = BridgeContext(historical_data=context_df)
        
        # Chạy TẤT CẢ các cầu thông qua BridgeManager
        all_bridge_results: List[BridgeResult] = bridge_manager.run_all_bridges(context)
        
        # 2. CHUYỂN ĐỔI: TỪ BRIDGE RESULT SANG LOTO (FEATURE COUNT & Q-FEATURES)
        
        # Map tạm thời: { 'loto_01': ['Classic_C1', 'V17_A', ...] }
        loto_to_bridge_names = defaultdict(list)
        
        # Phân loại Bridge Type cho Feature Counting
        for result in all_bridge_results:
            bridge_id = result.bridge_id
            
            for pred_loto in result.predictions:
                if len(pred_loto) == 2 and pred_loto.isdigit(): # Chỉ xử lý lô hợp lệ
                    loto_to_bridge_names[pred_loto].append(bridge_id)

        
        # 3. TÍNH FEATURE COUNTS VÀ Q-FEATURES
        for loto in [str(i).zfill(2) for i in range(100)]:
            f_classic_votes = 0
            f_v17_votes = 0
            f_memory_votes = 0
            
            q_win_rates = []
            q_k2n_risks = []
            q_current_streaks = []

            # Lấy tất cả các bridge dự đoán lô này
            all_bridges_for_loto = loto_to_bridge_names.get(loto, [])
            
            for bridge_name in all_bridges_for_loto:
                # Phân loại và đếm Feature Votes dựa trên tên cầu (Bridge ID)
                if bridge_name.startswith('Classic_C'):
                    f_classic_votes += 1
                elif bridge_name.startswith('Tổng(') or bridge_name.startswith('Hiệu('):
                    f_memory_votes += 1
                elif bridge_name in managed_bridges_map: # Cầu V17/Shadow
                    f_v17_votes += 1
                    
                    # LẤY Q-FEATURES TỪ MAP ĐÃ CHUẨN BỊ TRƯỚC VÒNG LẶP NGÀY
                    q_data = managed_bridges_map.get(bridge_name)
                    if q_data:
                        q_win_rates.append(q_data['win_rate_float'])
                        q_k2n_risks.append(q_data['k2n_risk'])
                        q_current_streaks.append(q_data['current_streak_int'])

            
            # LƯU VÀO ĐỊNH DẠNG MỚI (features) - Feature Counts
            daily_predictions_by_loto[current_ky][loto]['v5_count'] = f_classic_votes
            daily_predictions_by_loto[current_ky][loto]['v17_count'] = f_v17_votes
            daily_predictions_by_loto[current_ky][loto]['memory_count'] = f_memory_votes
            
            # LƯU VÀO ĐỊNH DẠNG MỚI (features) - Q-Features (F7, F8, F9)
            if q_win_rates:
                daily_predictions_by_loto[current_ky][loto]['q_avg_win_rate'] = sum(q_win_rates) / len(q_win_rates)
                daily_predictions_by_loto[current_ky][loto]['q_min_k2n_risk'] = min(q_k2n_risks)
                daily_predictions_by_loto[current_ky][loto]['q_max_curr_streak'] = max(q_current_streaks)
            else:
                # Giá trị mặc định khi không có cầu Managed Bridge nào dự đoán
                daily_predictions_by_loto[current_ky][loto]['q_avg_win_rate'] = 0.0
                daily_predictions_by_loto[current_ky][loto]['q_min_k2n_risk'] = 999.0 
                daily_predictions_by_loto[current_ky][loto]['q_max_curr_streak'] = -999.0 
                
    return daily_predictions_by_loto


# ==========================================================================
# (MỚI V7.2 MP) HÀM MỤC TIÊU CHO TIẾN TRÌNH
# ==========================================================================

def _train_ai_process_target(all_data_ai, result_queue):
    """
    (V7.2 MP) Hàm mục tiêu CPU-bound chạy trong tiến trình riêng (Process).
    result_queue: Queue để gửi kết quả (success, message) về cho tiến trình cha (AppController).
    """
    success, result_msg = False, "Lỗi chưa xác định."
    try:
        # 1. Tách biệt logic: Tính toán features TẠI ĐÂY (lottery_service)
        daily_bridge_predictions = _get_daily_bridge_predictions(all_data_ai)
        
        # 2. Gọi logic AI đã tách biệt (truyền features đã tính)
        success, result_msg = train_ai_model(all_data_ai, daily_bridge_predictions)
        
    except Exception as e:
        import traceback
        result_msg = f"Lỗi tính toán features hoặc huấn luyện: {e}\n{traceback.format_exc()}"
        
    # 3. Gửi kết quả (success, message) vào Queue
    result_queue.put(('done', success, result_msg))


# (MỚI V7.2 Caching) HÀM MỤC TIÊU CHO TẠO CACHE
def _generate_cache_process_target(all_data_ai, result_queue):
    """
    (V7.2 Caching) Hàm mục tiêu (rất nặng) chạy trong tiến trình riêng.
    Gọi hàm lõi từ dashboard_analytics và báo cáo tiến độ.
    """
    try:
        # 1. Định nghĩa callback để gửi tiến độ qua Queue
        def progress_callback(current, total):
            # Gửi thông điệp 'progress'
            result_queue.put(('progress', current, total))
            
        # 2. Gọi hàm lõi (nặng)
        # (Hàm generate_full_optimization_cache đã được import)
        success, result_msg = generate_full_optimization_cache(
            all_data_ai, 
            progress_callback=progress_callback
        )
        
        # 3. Gửi kết quả cuối cùng
        result_queue.put(('done', success, result_msg))

    except Exception as e:
        import traceback
        result_msg = f"Lỗi nghiêm trọng khi tạo cache: {e}\n{traceback.format_exc()}"
        result_queue.put(('done', False, result_msg))


# ==========================================================================
# (V7.2 MP) HÀM WRAPPER SỬ DỤNG MULTI-PROCESSING (Thay thế run_ai_training_threaded)
# ==========================================================================

def run_ai_training_multiprocessing():
    """
    (V7.2 MP) Wrapper chạy Huấn luyện AI trên tiến trình riêng (Process)
    (GĐ 1) Đã chuyển sang dùng load_data_ai_from_db từ DataService
    """
    all_data_ai, msg = load_data_ai_from_db() # Đã được map tới DataService
    if all_data_ai is None:
        return None, None, False, msg
        
    result_queue = Queue()
    process = Process(
        target=_train_ai_process_target, # <<< ĐÃ SỬA LỖI (thay : bằng =)
        args=(all_data_ai, result_queue)
    )
    process.start()
    return process, result_queue, True, "Quá trình huấn luyện AI đã được khởi chạy trong nền (Multi-Processing). Vui lòng chờ..."

# Giữ lại tên cũ để đảm bảo các module khác không bị lỗi import nếu chưa được sửa
run_ai_training_threaded = run_ai_training_multiprocessing

# (MỚI V7.2 Caching) HÀM WRAPPER TẠO CACHE
def run_optimization_cache_generation():
    """
    (V7.2 Caching) Wrapper chạy tác vụ tạo Cache (rất nặng) trong tiến trình riêng.
    (GĐ 1) Đã chuyển sang dùng load_data_ai_from_db từ DataService
    """
    all_data_ai, msg = load_data_ai_from_db() # Đã được map tới DataService
    if all_data_ai is None:
        return None, None, False, msg
        
    result_queue = Queue()
    process = Process(
        target=_generate_cache_process_target, 
        args=(all_data_ai, result_queue)
    )
    process.start()
    return process, result_queue, True, "Bắt đầu tạo Cache Tối ưu hóa (tác vụ này rất nặng, 15-30 phút). Vui lòng chờ..."

def run_ai_prediction_for_dashboard():
    """
    (V7.0) Hàm mới thay thế cho việc gọi trực tiếp get_ai_predictions
    (GĐ 1) Đã chuyển sang dùng load_data_ai_from_db từ DataService
    """
    all_data_ai, msg = load_data_ai_from_db() # Đã được map tới DataService
    if all_data_ai is None or len(all_data_ai) < 2:
        return None, msg
        
    try:
        last_two_rows = all_data_ai[-2:] 
        daily_preds_map = _get_daily_bridge_predictions(last_two_rows) 
        
        current_ky = str(last_two_rows[-1][0])
        bridge_predictions_for_today = daily_preds_map.get(current_ky, {})
    except Exception as e:
        import traceback
        return None, f"Lỗi tính toán features dự đoán: {e}\n{traceback.format_exc()}"

    return get_ai_predictions(all_data_ai, bridge_predictions_for_today)

# ==========================================================================
# (MỚI V7.2 MLOps) HÀM WRAPPER ĐÁNH GIÁ MODEL
# ==========================================================================
def run_model_evaluation():
    """
    (V7.2 MLOps) Wrapper gọi hàm đánh giá mô hình, so sánh và trả về
    trạng thái (OK/WARN) cùng thông điệp.
    """
    DRIFT_THRESHOLD = 0.03 
    
    try:
        current_acc, prev_acc, message = evaluate_current_model()
        
        if current_acc is None:
            return 'ERROR', message

        prev_acc = prev_acc or 0.0
            
        if current_acc < (prev_acc - DRIFT_THRESHOLD):
            return 'WARN', f"CẢNH BÁO Model Drift! Độ chính xác giảm từ {prev_acc:.3f} xuống {current_acc:.3f}."
        else:
            return 'OK', f"Độ chính xác AI ổn định: {current_acc:.3f} (Lần trước: {prev_acc:.3f})"
            
    except Exception as e:
        return 'ERROR', f"Lỗi nghiêm trọng khi chạy MLOps evaluation: {e}"

# ==========================================================================
# CÁC HÀM HỖ TRỢ CŨ (Đảm bảo chữ ký/logic đúng)
# ==========================================================================

def get_all_managed_bridges_wrapper(db_name=None, only_enabled=False): # (THAY ĐỔI GĐ 1) Bỏ qua db_name
    """
    Wrapper (Giữ lại hàm này cho tương thích)
    (GĐ 1) Đã chuyển hướng để gọi DataService.
    """
    # (THAY ĐỔI GĐ 1) Gọi hàm đã map (không cần db_name)
    return get_all_managed_bridges(only_enabled=only_enabled)

print("Lottery Service API (lottery_service.py) đã tải thành công (V7.2 MP & MLOps & Caching).")

# ==========================================================================
# (V7.1 - FIX BẢO TRÌ) HÀM THÊM DATA TỪ TEXT
# ==========================================================================

def run_and_update_from_text(raw_data):
    """
    (V7.1) Thực hiện Nạp và Thêm data kỳ mới từ text.
    (GĐ 1) Sửa đổi để sử dụng kết nối CSDL trung tâm từ DataService.
    """
    conn = None
    try:
        # (THAY ĐỔI GĐ 1) Sử dụng DataService để lấy kết nối (conn)
        conn = data_service.get_db_connection() # Lấy kết nối đang hoạt động
        if not conn:
            return False, "Lỗi nghiêm trọng: Không thể lấy kết nối CSDL từ DataService."
            
        cursor = conn.cursor()
        
        total_keys_added = parse_and_APPEND_data_TEXT(raw_data, conn, cursor)
        
        # (THAY ĐỔI GĐ 1) Không cần conn.close() vì DataService quản lý, nhưng PHẢI commit
        conn.commit() 
        
        if total_keys_added > 0:
            return True, f"Đã thêm thành công {total_keys_added} kỳ mới."
        else:
            return False, "Không có kỳ nào được thêm (có thể do trùng lặp hoặc định dạng sai)."
            
    except Exception as e:
        # (THAY ĐỔI GĐ 1) Nếu có lỗi, rollback
        if conn: 
            try:
                conn.rollback()
            except Exception:
                pass # Kết nối có thể đã chết
        import traceback
        return False, f"Lỗi nghiêm trọng khi thêm data kỳ mới: {e}\n{traceback.format_exc()}"