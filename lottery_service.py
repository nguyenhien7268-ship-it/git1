"""
==================================================================================
LOTTERY SERVICE API (BỘ ĐIỀU PHỐI) - (V7.1 FIX - ĐỒNG BỘ TÁCH BIỆT LOGIC)
==================================================================================
"""
import threading
from collections import defaultdict, Counter
import os 

# 1. (FIX A) Từ logic.db_manager: GIỮ CÁC HÀM CRUD CẦN THIẾT
try:
    from logic.db_manager import (
        DB_NAME,
        setup_database,
        get_all_kys_from_db,
        get_results_by_ky,
        add_managed_bridge,
        update_managed_bridge,
        delete_managed_bridge,
        update_bridge_win_rate_batch,
        upsert_managed_bridge,
        update_bridge_k2n_cache_batch
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.db_manager: {e}")

# (MỚI V7.0) 1.1. TỪ LOGIC.DATA_REPOSITORY (Tải dữ liệu lớn)
try:
    from logic.data_repository import (
        load_data_ai_from_db, 
        get_all_managed_bridges, 
    )
    print(">>> (V7.0) Tải logic.data_repository (Tải dữ liệu) thành công.")
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.data_repository: {e}")


# 2. Từ logic.data_parser
try:
    from logic.data_parser import (
        parse_and_insert_data,
        parse_and_APPEND_data,
        parse_and_APPEND_data_TEXT
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.data_parser: {e}")

# 3. Từ logic.bridges_classic
try:
    from logic.bridges_classic import (
        getAllLoto_V30,
        calculate_loto_stats,
        ALL_15_BRIDGE_FUNCTIONS_V5 
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.bridges_classic: {e}")

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
    from logic.bridge_manager_core import (
        TIM_CAU_TOT_NHAT_V16, 
        TIM_CAU_BAC_NHO_TOT_NHAT,
        find_and_auto_manage_bridges,
        prune_bad_bridges
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.bridge_manager_core: {e}")

# 4.2. (MỚI - FIX C) TỪ LOGIC.DASHBOARD_ANALYTICS (Analytics & Chấm điểm)
try:
    from logic.dashboard_analytics import (
        get_top_scored_pairs, 
        get_loto_stats_last_n_days, 
        get_loto_gan_stats,
        get_prediction_consensus,
        get_high_win_rate_predictions,
        get_top_memory_bridge_predictions,
        get_historical_dashboard_data
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.dashboard_analytics: {e}")


# ==========================================================================
# (MỚI V6.0) 5. TỪ LOGIC.ML_MODEL (BỘ NÃO AI)
# ==========================================================================
try:
    from logic.ml_model import (
        train_ai_model,
        get_ai_predictions
    )
    print(">>> (V6.0) Tải logic.ml_model (AI) thành công.")
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.ml_model (AI): {e}")
    # Giả lập hàm nếu lỗi 
    def train_ai_model(all_data, daily_bridge_predictions): 
        return False, f"Lỗi: Không tìm thấy logic.ml_model.py hoặc lỗi import nội bộ: {e}"
    def get_ai_predictions(all_data, bridge_predictions_for_today): 
        return None, f"Lỗi: Không tìm thấy logic.ml_model.py hoặc lỗi import nội bộ: {e}"
# ==========================================================================


# ==========================================================================
# (MỚI V7.0) 0. IMPORTS VÀ LOGIC TÍNH FEATURE (Tách biệt khỏi ml_model.py)
# ==========================================================================
try:
    # Import các hàm cầu để tính features
    from logic.bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong
    from logic.bridges_memory import get_27_loto_positions, calculate_bridge_stl, get_27_loto_names
    from logic.config_manager import SETTINGS # Vẫn cần SETTINGS
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic cầu/repo: {e}")
    
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
    if not stl_list or len(stl_list) != 2: return None
    return "-".join(sorted(stl_list))

def _get_daily_bridge_predictions(all_data_ai):
    """
    (V7.0 - Tách biệt logic & Thêm Q-Features) 
    Lặp qua CSDL để lấy dự đoán N1 của TẤT CẢ các cầu cho TẤT CẢ các ngày. 
    Tính toán cả Feature Counts và Q-Features.
    """
    print("... (V7.0 G2 Feature Extraction) Bước 1: Tính toán dự đoán cầu cho toàn bộ lịch sử...")
    
    # ĐỊNH DẠNG MỚI: { 'Kỳ 123': { 'loto_01': {'v5_count': 1, 'q_avg_win_rate': 55.1, ...}, 'loto_02': {...} } }
    daily_predictions_by_loto = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    
    # Lấy managed_bridges từ Data Repository (chứa cả Q-Features)
    managed_bridges = get_all_managed_bridges(DB_NAME, only_enabled=True)
    
    # Xử lý Q-Features trên managed_bridges MỘT LẦN (Đã chấp nhận đơn giản hóa cho Backtest)
    for bridge in managed_bridges:
        bridge['win_rate_float'] = _parse_win_rate_text(bridge.get('win_rate_text'))
        # Giá trị mặc định nếu không có dữ liệu
        bridge['k2n_risk'] = bridge.get('max_lose_streak_k2n', 999) 
        bridge['current_streak_int'] = bridge.get('current_streak', -999) 
    
    memory_bridges = [] 
    loto_names = get_27_loto_names()
    for i in range(27):
        for j in range(i, 27):
            memory_bridges.append((i, j, 'sum', f"Tổng({loto_names[i]}+{loto_names[j]})"))
            memory_bridges.append((i, j, 'diff', f"Hiệu(|{loto_names[i]}-{loto_names[j]}|)"))

    # Lặp qua toàn bộ CSDL
    for k in range(1, len(all_data_ai)):
        prev_row = all_data_ai[k-1]
        current_row = all_data_ai[k]
        current_ky = str(current_row[0])
        
        if k % 100 == 0:
            print(f"... (V7.0 G2 Feature Extraction) Bước 1: Đã xử lý {k}/{len(all_data_ai)} ngày (dự đoán cầu)")

        # Map tạm thời cho kỳ hiện tại: { '01-10': ['C1', 'V17_A'] }
        temp_bridge_preds = defaultdict(list)

        # 1. 15 Cầu Cổ Điển
        for i, bridge_func in enumerate(ALL_15_BRIDGE_FUNCTIONS_V5):
            try:
                stl = bridge_func(prev_row)
                pair_key = _standardize_pair(stl)
                if pair_key:
                    temp_bridge_preds[pair_key].append(f'C{i+1}')
            except Exception:
                pass

        # 2. Cầu Đã Lưu (V17)
        prev_positions_v17 = getAllPositions_V17_Shadow(prev_row)
        for bridge in managed_bridges:
            try:
                if bridge["pos1_idx"] == -1: continue 
                idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                a, b = prev_positions_v17[idx1], prev_positions_v17[idx2]
                if a is None or b is None: continue
                stl = taoSTL_V30_Bong(a, b)
                pair_key = _standardize_pair(stl)
                if pair_key:
                    temp_bridge_preds[pair_key].append(bridge['name'])
            except Exception:
                pass
                
        # 3. Cầu Bạc Nhớ (756 cầu)
        prev_positions_mem = get_27_loto_positions(prev_row)
        for idx1, idx2, alg_type, alg_name in memory_bridges:
            try:
                loto1, loto2 = prev_positions_mem[idx1], prev_positions_mem[idx2]
                stl = calculate_bridge_stl(loto1, loto2, alg_type)
                pair_key = _standardize_pair(stl)
                if pair_key:
                    temp_bridge_preds[pair_key].append(alg_name)
            except Exception:
                pass
        
        # 4. CHUYỂN ĐỔI: TỪ CẶP (PAIR) SANG LOTO (FEATURE COUNT & Q-FEATURES)
        loto_to_pairs = defaultdict(list)
        for pair_key in temp_bridge_preds.keys():
            loto1, loto2 = pair_key.split('-')
            loto_to_pairs[loto1].append(pair_key)
            loto_to_pairs[loto2].append(pair_key)

        for loto in [str(i).zfill(2) for i in range(100)]:
            f_classic_votes = 0
            f_v17_votes = 0
            f_memory_votes = 0
            
            # Khởi tạo danh sách cho Q-Features
            q_win_rates = []
            q_k2n_risks = []
            q_current_streaks = []

            pairs_for_this_loto = loto_to_pairs.get(loto, [])
            
            if pairs_for_this_loto:
                all_bridges_for_loto = []
                for pair in pairs_for_this_loto:
                    for bridge_name in temp_bridge_preds[pair]:
                        all_bridges_for_loto.append(bridge_name)

                        # TÍNH Q-FEATURES: CHỈ CHO CẦU ĐÃ LƯU (ManagedBridge)
                        if not (bridge_name.startswith('C') or bridge_name.startswith('Tổng') or bridge_name.startswith('Hiệu')):
                            # Đây là Managed Bridge (V17/Shadow)
                            found_bridge = next((b for b in managed_bridges if b['name'] == bridge_name), None)
                            if found_bridge:
                                q_win_rates.append(found_bridge['win_rate_float'])
                                q_k2n_risks.append(found_bridge['k2n_risk'])
                                q_current_streaks.append(found_bridge['current_streak_int'])

                bridge_counts = Counter(all_bridges_for_loto)
                for bridge_name, count in bridge_counts.items():
                    if bridge_name.startswith('C'):
                        f_classic_votes += count
                    elif bridge_name.startswith('Tổng') or bridge_name.startswith('Hiệu'):
                        f_memory_votes += count
                    else: # Cầu V17/Shadow
                        f_v17_votes += count
            
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
                daily_predictions_by_loto[current_ky][loto]['q_min_k2n_risk'] = 999.0 # Dùng 999.0 để biểu thị rủi ro RẤT CAO
                daily_predictions_by_loto[current_ky][loto]['q_max_curr_streak'] = -999.0 # Dùng -999.0 để biểu thị chuỗi streak RẤT THẤP
                
    return daily_predictions_by_loto

# ==========================================================================
# (V7.0) HÀM WRAPPER SỬ DỤNG THREADING
# ==========================================================================

def run_ai_training_threaded(callback=None):
    """
    (V7.0) Wrapper chạy Huấn luyện AI trên luồng riêng để không làm đóng băng UI.
    callback: Hàm được gọi khi hoàn thành (ví dụ: callback(success, message)).
    """
    # Lấy dữ liệu lớn từ Data Repository
    all_data_ai, msg = load_data_ai_from_db()
    if all_data_ai is None:
        if callback: callback(False, msg)
        return False, msg
        
    def _train_target():
        # 1. Tách biệt logic: Tính toán features TẠI ĐÂY (lottery_service)
        try:
            daily_bridge_predictions = _get_daily_bridge_predictions(all_data_ai)
        except Exception as e:
            import traceback
            if callback: callback(False, f"Lỗi tính toán features: {e}\n{traceback.format_exc()}")
            return

        # 2. Gọi logic AI đã tách biệt (truyền features đã tính)
        success, result_msg = train_ai_model(all_data_ai, daily_bridge_predictions)
        
        # 3. Gọi lại hàm callback
        if callback:
            callback(success, result_msg)

    # Khởi chạy luồng
    thread = threading.Thread(target=_train_target)
    thread.start()
    return True, "Quá trình huấn luyện AI đã được khởi chạy trong nền. Vui lòng chờ..."


def run_ai_prediction_for_dashboard():
    """
    (V7.0) Hàm mới thay thế cho việc gọi trực tiếp get_ai_predictions
    """
    # Lấy dữ liệu lớn từ Data Repository
    all_data_ai, msg = load_data_ai_from_db()
    if all_data_ai is None or len(all_data_ai) < 2:
        return None, msg
        
    # 1. Tách biệt logic: Tính toán features cho ngày gần nhất
    try:
        # Chỉ truyền 2 hàng cuối cùng: [D-1, D] để tính dự đoán cho ngày D+1 (features của ngày D)
        last_two_rows = all_data_ai[-2:] 
        # _get_daily_bridge_predictions sẽ trả về dự đoán cho kỳ của last_two_rows[-1]
        daily_preds_map = _get_daily_bridge_predictions(last_two_rows) 
        
        current_ky = str(last_two_rows[-1][0])
        bridge_predictions_for_today = daily_preds_map.get(current_ky, {})
    except Exception as e:
        import traceback
        return None, f"Lỗi tính toán features dự đoán: {e}\n{traceback.format_exc()}"

    # 2. Gọi logic AI đã tách biệt
    # FIX: Gọi hàm lõi AI với đủ tham số
    return get_ai_predictions(all_data_ai, bridge_predictions_for_today)

# ==========================================================================
# CÁC HÀM HỖ TRỢ CŨ (Đảm bảo chữ ký/logic đúng)
# ==========================================================================

# Wrapper cho get_all_managed_bridges để tương thích
def get_all_managed_bridges_wrapper(db_name=DB_NAME, only_enabled=False):
    """
    Wrapper (Giữ lại hàm này cho tương thích)
    """
    # Gọi hàm mới từ data_repository.py đã được import
    return get_all_managed_bridges(db_name, only_enabled)

print("Lottery Service API (lottery_service.py) đã tải thành công (V7.0 G2).")