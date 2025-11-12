# Tên file: du-an-backup/logic/ai_feature_extractor.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA LỖI IMPORT TƯƠNG ĐỐI)
#
import threading
from collections import defaultdict, Counter
import os 
import traceback

# (SỬA LỖI) Sử dụng import TƯƠNG ĐỐI (dấu . ở trước)
try:
    # 1. DB và Repo
    from .db_manager import DB_NAME
    from .data_repository import load_data_ai_from_db, get_all_managed_bridges
    
    # 2. Logic Cầu (để tính toán)
    from .bridges.bridges_classic import ALL_15_BRIDGE_FUNCTIONS_V5
    from .bridges.bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong
    from .bridges.bridges_memory import get_27_loto_positions, calculate_bridge_stl, get_27_loto_names
    
    # 3. Logic AI (để gọi)
    from .ml_model import train_ai_model, get_ai_predictions
    
    # 4. Config
    from .config_manager import SETTINGS
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: ai_feature_extractor.py không thể import: {e}")
    # Tạo hàm giả để tránh lỗi ở tầng cao hơn
    def run_ai_training_threaded(callback=None): return False, f"Lỗi Import: {e}"
    def run_ai_prediction_for_dashboard(): return None, f"Lỗi Import: {e}"

# ==========================================================================
# (DI CHUYỂN TỪ LOTTERY_SERVICE) HÀM TIỆN ÍCH TÍNH TOÁN
# ==========================================================================

def _parse_win_rate_text(win_rate_text):
    if not win_rate_text:
        return 0.0
    try:
        return float(win_rate_text.strip().replace('%', ''))
    except ValueError:
        return 0.0

def _standardize_pair(stl_list):
    if not stl_list or len(stl_list) != 2: return None
    return "-".join(sorted(stl_list))

# ==========================================================================
# (DI CHUYỂN TỪ LOTTERY_SERVICE) LOGIC TRÍCH XUẤT ĐẶC TRƯNG CỐT LÕI
# ==========================================================================

def _get_daily_bridge_predictions(all_data_ai):
    print("... (V7.0 G2 Feature Extraction) Bước 1: Tính toán dự đoán cầu cho toàn bộ lịch sử...")
    
    daily_predictions_by_loto = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    
    managed_bridges = get_all_managed_bridges(DB_NAME, only_enabled=True)
    
    for bridge in managed_bridges:
        bridge['win_rate_float'] = _parse_win_rate_text(bridge.get('win_rate_text'))
        bridge['k2n_risk'] = bridge.get('max_lose_streak_k2n', 999) 
        bridge['current_streak_int'] = bridge.get('current_streak', -999) 
    
    memory_bridges = [] 
    loto_names = get_27_loto_names()
    for i in range(27):
        for j in range(i, 27):
            memory_bridges.append((i, j, 'sum', f"Tổng({loto_names[i]}+{loto_names[j]})"))
            memory_bridges.append((i, j, 'diff', f"Hiệu(|{loto_names[i]}-{loto_names[j]}|)"))

    for k in range(1, len(all_data_ai)):
        prev_row = all_data_ai[k-1]
        current_row = all_data_ai[k]
        current_ky = str(current_row[0])
        
        if k % 100 == 0:
            print(f"... (V7.0 G2 Feature Extraction) Bước 1: Đã xử lý {k}/{len(all_data_ai)} ngày (dự đoán cầu)")

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
            
            q_win_rates = []
            q_k2n_risks = []
            q_current_streaks = []

            pairs_for_this_loto = loto_to_pairs.get(loto, [])
            
            if pairs_for_this_loto:
                all_bridges_for_loto = []
                for pair in pairs_for_this_loto:
                    for bridge_name in temp_bridge_preds[pair]:
                        all_bridges_for_loto.append(bridge_name)

                        if not (bridge_name.startswith('C') or bridge_name.startswith('Tổng') or bridge_name.startswith('Hiệu')):
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
                    else: 
                        f_v17_votes += count
            
            daily_predictions_by_loto[current_ky][loto]['v5_count'] = f_classic_votes
            daily_predictions_by_loto[current_ky][loto]['v17_count'] = f_v17_votes
            daily_predictions_by_loto[current_ky][loto]['memory_count'] = f_memory_votes
            
            if q_win_rates:
                daily_predictions_by_loto[current_ky][loto]['q_avg_win_rate'] = sum(q_win_rates) / len(q_win_rates)
                daily_predictions_by_loto[current_ky][loto]['q_min_k2n_risk'] = min(q_k2n_risks)
                daily_predictions_by_loto[current_ky][loto]['q_max_curr_streak'] = max(q_current_streaks)
            else:
                daily_predictions_by_loto[current_ky][loto]['q_avg_win_rate'] = 0.0
                daily_predictions_by_loto[current_ky][loto]['q_min_k2n_risk'] = 999.0 
                daily_predictions_by_loto[current_ky][loto]['q_max_curr_streak'] = -999.0 
                
    return daily_predictions_by_loto

# ==========================================================================
# (DI CHUYỂN TỪ LOTTERY_SERVICE) HÀM WRAPPER SỬ DỤNG THREADING
# ==========================================================================

def run_ai_training_threaded(callback=None):
    """
    (V7.0) Wrapper chạy Huấn luyện AI trên luồng riêng để không làm đóng băng UI.
    """
    all_data_ai, msg = load_data_ai_from_db()
    if all_data_ai is None:
        if callback: callback(False, msg)
        return False, msg
        
    def _train_target():
        try:
            daily_bridge_predictions = _get_daily_bridge_predictions(all_data_ai)
        except Exception as e:
            if callback: callback(False, f"Lỗi tính toán features: {e}\n{traceback.format_exc()}")
            return

        success, result_msg = train_ai_model(all_data_ai, daily_bridge_predictions)
        
        if callback:
            callback(success, result_msg)

    thread = threading.Thread(target=_train_target)
    thread.start()
    return True, "Quá trình huấn luyện AI đã được khởi chạy trong nền. Vui lòng chờ..."


def run_ai_prediction_for_dashboard():
    """
    (V7.0) Hàm mới thay thế cho việc gọi trực tiếp get_ai_predictions
    """
    all_data_ai, msg = load_data_ai_from_db()
    if all_data_ai is None or len(all_data_ai) < 2:
        return None, msg
        
    try:
        last_two_rows = all_data_ai[-2:] 
        daily_preds_map = _get_daily_bridge_predictions(last_two_rows) 
        
        current_ky = str(last_two_rows[-1][0])
        bridge_predictions_for_today = daily_preds_map.get(current_ky, {})
    except Exception as e:
        return None, f"Lỗi tính toán features dự đoán: {e}\n{traceback.format_exc()}"

    return get_ai_predictions(all_data_ai, bridge_predictions_for_today)