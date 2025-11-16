# TÊN FILE: logic/dashboard_analytics.py
# NỘI DUNG THAY THẾ TOÀN BỘ (SỬA LỖI GĐ 4 CHO TỐI ƯU HÓA)

import sqlite3
from collections import Counter, defaultdict
import math
import joblib 
import os 
import pandas as pd # (GĐ 4) Thêm Pandas để tạo BridgeContext
from typing import List, Dict, Any, Optional

# (MỚI V7.2 Caching) Đường dẫn file cache
CACHE_FILE_PATH = "logic/ml_model_files/optimization_cache.joblib"

# Import SETTINGS
try:
    from .config_manager import SETTINGS
except ImportError:
    from config_manager import SETTINGS
    SETTINGS = type('obj', (object,), {
        'STATS_DAYS': 7, 'GAN_DAYS': 15, 'HIGH_WIN_THRESHOLD': 47.0,
        'K2N_RISK_START_THRESHOLD': 4, 'K2N_RISK_PENALTY_PER_FRAME': 0.5,
        'AI_PROB_THRESHOLD': 45.0, 
        'AI_SCORE_WEIGHT': 0.2
    })

# (SỬA LỖI IMPORT)
def _parse_k2n_results(r): 
    if isinstance(r, tuple) and len(r) == 2:
        return r[0], r[1]
    return [], {}


# Import Bridge/DB Logic và Helpers
try:
    # (GĐ 2) Import các hàm/biến tiện ích từ file bridge gốc
    from .bridges.bridges_classic import ( 
        getAllLoto_V30
    )
    # (GĐ 1) Thay thế data_repository bằng DataService
    from .data_service import DataService
    data_service = DataService.get_instance()
    get_all_managed_bridges = data_service.get_all_managed_bridges
    
    # Import functions từ db_manager
    from .db_manager import DB_NAME

    # ===================================================================
    # (SỬA LỖI GĐ 4) IMPORT BRIDGE MANAGER ĐỂ MÔ PHỎNG
    # ===================================================================
    from .bridges.bridge_manager_core import BridgeManager
    from .bridges.base_bridge import BridgeContext, BridgeResult
    
    # Định nghĩa tên cột cho DataFrame (Giống hệt backtester.py)
    DF_COLUMNS = ['MaSoKy', 'Col_A_Ky', 'Col_B_GDB', 'Col_C_G1', 'Col_D_G2', 'Col_E_G3', 'Col_F_G4', 'Col_G_G5', 'Col_H_G6', 'Col_I_G7']
    # ===================================================================

    # (GĐ 4) Các hàm backtest V6 cũ đã bị xóa khỏi backtester.py
    # Định nghĩa Fallback (dự phòng) tại đây
    def BACKTEST_MANAGED_BRIDGES_K2N(a,b,c,d,e): 
        print("CẢNH BÁO: (Sim) BACKTEST_MANAGED_BRIDGES_K2N (V6) LỖI THỜI")
        return []
    def BACKTEST_15_CAU_K2N_V30_AI_V8(a,b,c,d): 
        print("CẢNH BÁO: (Sim) BACKTEST_15_CAU_K2N_V30_AI_V8 (V6) LỖI THỜI")
        return []

except ImportError as e_import:
    print(f"Lỗi: Không thể import helpers (GĐ 1/2/4): {e_import}")
    
    def getAllLoto_V30(r): return []
    def BACKTEST_MANAGED_BRIDGES_K2N(a,b,c,d,e): return []
    def BACKTEST_15_CAU_K2N_V30_AI_V8(a,b,c,d): return []
    DB_NAME = 'xo_so_prizes_all_logic.db'
    def get_all_managed_bridges(only_enabled=False): return []
    
    # Fallback cho GĐ 4
    class DummyBridgeManager:
        def run_all_bridges(self, context): return []
    BridgeManager = type('obj', (object,), {'get_instance': lambda: DummyBridgeManager()})
    class BridgeContext:
        def __init__(self, historical_data, parameters=None): pass
    DF_COLUMNS = ['MaSoKy', 'Col_A_Ky', 'Col_B_GDB', 'Col_C_G1', 'Col_D_G2', 'Col_E_G3', 'Col_F_G4', 'Col_G_G5', 'Col_H_G6', 'Col_I_G7']


# ===================================================================================
# I. HÀM ANALYTICS CƠ BẢN (CHUYỂN TỪ backtester.py)
# ===================================================================================
# (Các hàm get_loto_stats_last_n_days, get_loto_gan_stats, get_top_memory_bridge_predictions
#  được giữ nguyên. Chúng không bị ảnh hưởng bởi GĐ 4.)
# ===================================================================================

def get_loto_stats_last_n_days(all_data_ai, n=None):
    """ Lấy thống kê tần suất loto (hot/lạnh). """
    try:
        if n is None:
            n = SETTINGS.STATS_DAYS
            
        if not all_data_ai or len(all_data_ai) == 0:
            return []
            
        if len(all_data_ai) < n:
            n = len(all_data_ai)
        
        last_n_rows = all_data_ai[-n:]
        
        all_lotos_hits = [] 
        day_appearance_counter = Counter() 
        
        for row in last_n_rows:
            lotos_in_this_row = getAllLoto_V30(row)
            all_lotos_hits.extend(lotos_in_this_row)
            unique_lotos_in_this_row = set(lotos_in_this_row)
            day_appearance_counter.update(unique_lotos_in_this_row) 
        
        loto_hit_counts = Counter(all_lotos_hits)
        sorted_lotos_by_hits = sorted(loto_hit_counts.items(), key=lambda item: item[1], reverse=True)
        
        final_stats = []
        for loto, hit_count in sorted_lotos_by_hits:
            day_count = day_appearance_counter.get(loto, 0) 
            final_stats.append((loto, hit_count, day_count)) 
            
        return final_stats
        
    except Exception as e:
        print(f"Lỗi get_loto_stats_last_n_days: {e}")
        return []

def get_loto_gan_stats(all_data_ai, n_days=None):
    """ Tìm các loto (00-99) đã không xuất hiện trong n_days gần nhất (Lô Gan). """
    gan_stats = []
    try:
        if n_days is None:
            n_days = SETTINGS.GAN_DAYS
            
        if not all_data_ai or len(all_data_ai) < n_days:
            return []
            
        all_100_lotos = {str(i).zfill(2) for i in range(100)}
        
        recent_lotos = set()
        recent_rows = all_data_ai[-n_days:]
        for row in recent_rows:
            lotos_in_this_row = getAllLoto_V30(row)
            recent_lotos.update(lotos_in_this_row)
            
        gan_lotos = all_100_lotos - recent_lotos
        
        if not gan_lotos:
            return [] 

        full_history = all_data_ai[:] 
        full_history.reverse() 
        
        for loto in gan_lotos:
            days_gan = 0
            found = False
            for i, row in enumerate(full_history):
                if i < n_days: 
                    days_gan += 1
                    continue
                
                loto_set_this_day = set(getAllLoto_V30(row))
                if loto in loto_set_this_day:
                    found = True
                    break 
                else:
                    days_gan += 1 
            
            if found:
                gan_stats.append((loto, days_gan))
            else:
                gan_stats.append((loto, len(full_history)))

        gan_stats.sort(key=lambda x: x[1], reverse=True)
        return gan_stats

    except Exception as e:
        print(f"Lỗi get_loto_gan_stats: {e}")
        return []

def get_top_memory_bridge_predictions(all_data_ai, last_row, top_n=5):
    """ 
    (HÀM NÀY CHỈ DÙNG CHO DASHBOARD CHÍNH)
    Chạy backtest N1 756 cầu bạc nhớ ngầm.
    (SỬA LỖI GĐ 4) Cần import helper từ logic.bridges.bridges_memory
    """
    try:
        from .bridges.bridges_memory import ( 
            get_27_loto_names,
            get_27_loto_positions,
            calculate_bridge_stl
        )
    except ImportError:
        print("Lỗi: dashboard_analytics không thể import bridges_memory helpers.")
        def get_27_loto_names(): return []
        def get_27_loto_positions(r): return []
        def calculate_bridge_stl(l1, l2, type): return ['00', '00']

    print("... (BTH) Bắt đầu chạy backtest 756 cầu Bạc Nhớ ngầm...")
    
    def _validate_data(data):
        return not data or len(data) < 2
        
    if _validate_data(all_data_ai): return []

    loto_names = get_27_loto_names()
    num_positions = len(loto_names) 
    if num_positions == 0: return [] # Thoát nếu import lỗi
    
    algorithms = []
    for i in range(num_positions):
        for j in range(i, num_positions):
            algorithms.append((i, j, 'sum'))
            algorithms.append((i, j, 'diff'))

    num_algorithms = len(algorithms) 
    
    processedData = []
    startCheckRow = 2
    offset = 1
    finalEndRow = len(all_data_ai)
    
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(all_data_ai) or prevRow_idx < 0: continue
        prevRow, actualRow = all_data_ai[prevRow_idx], all_data_ai[actualRow_idx]
        if not prevRow or not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "" or len(actualRow) < 10 or not actualRow[9]:
            continue
        processedData.append({
          "prevLotos": get_27_loto_positions(prevRow),
          "actualLotoSet": set(getAllLoto_V30(actualRow))
        })
    
    totalTestDays = len(processedData)
    if totalTestDays == 0: return []
        
    win_counts = [0] * num_algorithms

    for dayData in processedData:
        actualLotoSet = dayData["actualLotoSet"]
        prevLotos = dayData["prevLotos"]
        
        for j in range(num_algorithms):
            alg = algorithms[j]
            idx1, idx2, alg_type = alg[0], alg[1], alg[2]
            loto1, loto2 = prevLotos[idx1], prevLotos[idx2]
            pred_stl = calculate_bridge_stl(loto1, loto2, alg_type)
            
            if pred_stl[0] in actualLotoSet or pred_stl[1] in actualLotoSet:
                win_counts[j] += 1

    bridge_stats = [] 
    for j in range(num_algorithms):
        rate = (win_counts[j] / totalTestDays) * 100
        bridge_stats.append( (rate, j) )
        
    bridge_stats.sort(key=lambda x: x[0], reverse=True) 
    
    top_n_bridges = bridge_stats[:top_n]
    
    predictions_for_dashboard = []
    last_lotos = get_27_loto_positions(last_row)
    
    for rate, alg_index in top_n_bridges:
        alg = algorithms[alg_index]
        idx1, idx2, alg_type = alg[0], alg[1], alg[2]
        
        loto1, loto2 = last_lotos[idx1], last_lotos[idx2]
        pred_stl = calculate_bridge_stl(loto1, loto2, alg_type)
        
        if alg_type == 'sum':
            name = f"Tổng({loto_names[idx1]}+{loto_names[idx2]})"
        else:
            name = f"Hiệu(|{loto_names[idx1]}-{loto_names[idx2]}|)"
            
        predictions_for_dashboard.append({
            'name': name,
            'stl': pred_stl,
            'rate': f"{rate:.2f}%"
        })
        
    return predictions_for_dashboard

# ===================================================================================
# II. HÀM ANALYTICS NÂNG CAO (ĐÃ SỬA GĐ 1)
# ===================================================================================

def _standardize_pair(stl_list):
    """Hàm nội bộ: Chuẩn hóa 1 cặp STL. Ví dụ ['30', '03'] -> '03-30'"""
    if not stl_list or len(stl_list) != 2:
        return None
    try:
        sorted_pair = sorted([str(l).zfill(2) for l in stl_list])
        return f"{sorted_pair[0]}-{sorted_pair[1]}" # Key: "03-30"
    except Exception:
        return None

def get_prediction_consensus(last_row=None, db_name=DB_NAME):
    """ Lấy dự đoán từ "Cầu Đã Lưu" (cache) để đếm vote THEO CẶP. """
    # (Hàm này đọc từ cache K2N của DataService, nó đã đúng GĐ 4)
    try:
        prediction_sources = {} 
        managed_bridges = get_all_managed_bridges(only_enabled=True)
        
        if not managed_bridges: return []
            
        for bridge in managed_bridges:
            try:
                prediction_stl_str = bridge.get('next_prediction_stl')
                
                if not prediction_stl_str or \
                    'N2' in prediction_stl_str or \
                    'LỖI' in prediction_stl_str or \
                    ',' not in prediction_stl_str:
                    continue
                    
                stl = prediction_stl_str.split(',')
                pair_key = _standardize_pair(stl)
                if not pair_key: continue
                    
                source_name = bridge["name"]
                if source_name.startswith("Cầu "):
                     source_name = f"C{source_name.split(' ')[1]}"
                     
                if pair_key not in prediction_sources:
                    prediction_sources[pair_key] = []
                if source_name not in prediction_sources[pair_key]:
                    prediction_sources[pair_key].append(source_name)
            except Exception as e:
                print(f"Lỗi dự đoán Cầu (consensus cache) {bridge.get('name')}: {e}")
        
        consensus_list = []
        for pair_key, sources in prediction_sources.items():
            count = len(sources)
            sources_str = ", ".join(sources)
            consensus_list.append((pair_key, count, sources_str))
            
        consensus_list.sort(key=lambda item: item[1], reverse=True)
        return consensus_list

    except Exception as e:
        print(f"Lỗi get_prediction_consensus: {e}")
        return []

def get_high_win_rate_predictions(last_row=None, threshold=None, db_name=DB_NAME):
    """ Lấy dự đoán từ Cầu Đã Lưu CÓ TỶ LỆ CAO (dựa trên cache K2N). """
    # (Hàm này đọc từ cache N1/K2N của DataService, nó đã đúng GĐ 4)
    try:
        if threshold is None:
            threshold = SETTINGS.HIGH_WIN_THRESHOLD
            
        high_win_bridges = []
        managed_bridges = get_all_managed_bridges(only_enabled=True)
        if not managed_bridges:
            return []
            
        for bridge in managed_bridges:
            try:
                rate_str = str(bridge.get('win_rate_text', '0%')).replace('%', '')
                if not rate_str or rate_str == "N/A":
                    continue
                
                win_rate = float(rate_str)
                
                if win_rate >= threshold:
                    prediction_stl_str = bridge.get('next_prediction_stl')
                    
                    if not prediction_stl_str or \
                       'N2' in prediction_stl_str or \
                       'LỖI' in prediction_stl_str or \
                       ',' not in prediction_stl_str:
                        continue
                        
                    stl = prediction_stl_str.split(',')
                    
                    high_win_bridges.append({
                        'name': bridge['name'],
                        'stl': stl,
                        'rate': f"{win_rate:.2f}%"
                    })
            except Exception as e:
                print(f"Lỗi kiểm tra tỷ lệ cầu {bridge['name']}: {e}")
                
        return high_win_bridges
        
    except Exception as e:
        print(f"Lỗi get_high_win_rate_predictions: {e}")
        return []

def get_pending_k2n_bridges(last_row, prev_row):
    """ (SỬA LỖI GĐ 4) VIẾT LẠI HOÀN TOÀN """
    # Lấy các cầu đã trượt N1 ở kỳ trước và đang chờ N2
    print("... (Sim) Chạy get_pending_k2n_bridges (GĐ 4)")
    pending_bridges = []
    try:
        if not last_row or not prev_row: return []
            
        actualLotoSet = set(getAllLoto_V30(last_row))
        if not actualLotoSet: return []
        
        # Chạy BridgeManager trên (prev_row) để lấy dự đoán cho (last_row)
        bridge_manager = BridgeManager.get_instance()
        
        # (SỬA LỖI) Cần tạo DataFrame từ (prev_row)
        prev_row_df = pd.DataFrame([prev_row], columns=DF_COLUMNS)
        context = BridgeContext(historical_data=prev_row_df)
        
        all_bridge_results: List[BridgeResult] = bridge_manager.run_all_bridges(context)

        for result in all_bridge_results:
            if result.prediction_type != 'STL' or not result.predictions:
                continue

            # Kiểm tra hit
            is_hit = False
            for pred_loto in result.predictions:
                if pred_loto in actualLotoSet:
                    is_hit = True
                    break
            
            # Nếu KHÔNG HIT, nó đang chờ N2
            if not is_hit:
                pending_bridges.append({
                    'name': result.bridge_id, 
                    'stl': result.predictions
                })
                    
        return pending_bridges

    except Exception as e:
        print(f"Lỗi get_pending_k2n_bridges (GĐ 4): {e}")
        return []

# ===================================================================================
# III. HÀM CHẤM ĐIỂM CỐT LÕI (V7.1 - HOÀN THIỆN LOGIC TRỌNG SỐ)
# ===================================================================================

def get_top_scored_pairs(stats, consensus, high_win, pending_k2n, gan_stats, top_memory_bridges, ai_predictions=None):
    """
    (V7.1) Tính toán, chấm điểm và xếp hạng các cặp số.
    (SỬA LỖI GĐ 4) Sửa logic đọc pending_k2n (giờ là LIST thay vì DICT)
    """
    try:
        scores = {}
        
        K2N_RISK_START_THRESHOLD = SETTINGS.K2N_RISK_START_THRESHOLD
        K2N_RISK_PENALTY_PER_FRAME = SETTINGS.K2N_RISK_PENALTY_PER_FRAME
        ai_score_weight = SETTINGS.AI_SCORE_WEIGHT
        
        loto_prob_map = {}
        if ai_predictions:
            for pred in ai_predictions:
                loto_prob_map[pred['loto']] = pred['probability'] / 100.0 
        
        top_hot_lotos = {loto for loto, count, days in stats if count > 0}
        gan_map = {loto: days for loto, days in gan_stats}
        
        # Nguồn 2: Consensus
        for pair_key, count, _ in consensus:
            if pair_key not in scores:
                scores[pair_key] = {'score': 0.0, 'reasons': [], 'is_gan': False, 'gan_days': 0}
            scores[pair_key]['score'] += count * 0.5
            scores[pair_key]['reasons'].append(f"Vote x{count}")

        # Nguồn 3: Cầu Tỷ Lệ Cao
        for bridge in high_win:
            pair_key = _standardize_pair(bridge['stl'])
            if pair_key:
                if pair_key not in scores:
                    scores[pair_key] = {'score': 0.0, 'reasons': [], 'is_gan': False, 'gan_days': 0}
                scores[pair_key]['score'] += 2.0 
                scores[pair_key]['reasons'].append(f"Cao ({bridge['rate']})")

        # Nguồn 4: Cầu K2N Đang Chờ (Trừ điểm rủi ro K2N)
        # (SỬA LỖI GĐ 4)
        # pending_k2n giờ là LIST (từ get_pending_k2n_bridges)
        
        if isinstance(pending_k2n, list):
            # Chạy logic cho LIST (Dashboard & Worker GĐ 4)
            for data in pending_k2n:
                try:
                    pair_key = _standardize_pair(data['stl'])
                    if pair_key:
                        if pair_key not in scores:
                            scores[pair_key] = {'score': 0.0, 'reasons': [], 'is_gan': False, 'gan_days': 0}
                        # Chỉ trừ điểm nhẹ vì đang chờ N2
                        scores[pair_key]['score'] -= K2N_RISK_PENALTY_PER_FRAME 
                        scores[pair_key]['reasons'].append(f"Chờ N2 (-{K2N_RISK_PENALTY_PER_FRAME})")
                except KeyError:
                    pass # Bỏ qua nếu data (từ list) thiếu 'stl'
        
        elif isinstance(pending_k2n, dict):
            # (Giữ lại logic cũ) Chạy logic cho DICT (Worker GĐ 1)
            for bridge_name, data in pending_k2n.items():
                try:
                    # Chú ý: Worker GĐ 1 trả 'stl' là string, GĐ 4 trả list
                    stl_data = data['stl']
                    if isinstance(stl_data, str):
                        pair_key = _standardize_pair(stl_data.split(','))
                    else:
                        pair_key = _standardize_pair(stl_data)
                        
                    if pair_key and data['max_lose'] >= K2N_RISK_START_THRESHOLD:
                        if pair_key not in scores:
                            scores[pair_key] = {'score': 0.0, 'reasons': [], 'is_gan': False, 'gan_days': 0}
                        penalty = (data['max_lose'] - K2N_RISK_START_THRESHOLD + 1) * K2N_RISK_PENALTY_PER_FRAME
                        scores[pair_key]['score'] -= penalty
                        scores[pair_key]['reasons'].append(f"Rủi ro K2N (-{penalty})")
                except KeyError:
                    pass 


        # Nguồn 5: Cầu Bạc Nhớ (Top N)
        for bridge in top_memory_bridges:
            pair_key = _standardize_pair(bridge['stl'])
            if pair_key:
                if pair_key not in scores:
                    scores[pair_key] = {'score': 0.0, 'reasons': [], 'is_gan': False, 'gan_days': 0}
                scores[pair_key]['score'] += 1.5 
                scores[pair_key]['reasons'].append(f"BN ({bridge['rate']})")
        
        # --- 4. Chấm điểm cộng và AI (Trọng số liên tục) ---
        
        for pair_key in list(scores.keys()):
            loto1, loto2 = pair_key.split('-')
            
            if loto1 in top_hot_lotos or loto2 in top_hot_lotos:
                scores[pair_key]['score'] += 1.0
                scores[pair_key]['reasons'].append("Loto Hot")
                
            gan_days_1 = gan_map.get(loto1, 0)
            gan_days_2 = gan_map.get(loto2, 0)
            max_gan = max(gan_days_1, gan_days_2)
            if max_gan > 0:
                scores[pair_key]['is_gan'] = True
                scores[pair_key]['gan_days'] = max_gan

            if loto_prob_map:
                prob_1 = loto_prob_map.get(loto1, 0.0)
                prob_2 = loto_prob_map.get(loto2, 0.0)
                max_prob = max(prob_1, prob_2) 
                
                ai_score_contribution = max_prob * ai_score_weight 
                scores[pair_key]['score'] += ai_score_contribution
                scores[pair_key]['reasons'].append(f"AI: +{ai_score_contribution:.2f} ({max_prob*100.0:.1f}%)")


        # --- 5. Thêm các cặp SẠCH (Chỉ AI phát hiện - STL) ---
        if loto_prob_map:
            for loto1_str in [str(i).zfill(2) for i in range(100)]:
                if loto1_str[0] == loto1_str[1]: continue
                loto2_str = str(int(loto1_str[::-1])).zfill(2)
                stl_pair = _standardize_pair([loto1_str, loto2_str]) 
                
                if stl_pair in scores: continue
                
                prob1 = loto_prob_map.get(loto1_str, 0.0)
                prob2 = loto_prob_map.get(loto2_str, 0.0)
                max_prob = max(prob1, prob2)
                
                if max_prob > 0.0:
                    ai_score_contribution = max_prob * ai_score_weight 
                    
                    if stl_pair not in scores:
                        scores[stl_pair] = {'score': 0.0, 'reasons': [], 'is_gan': False, 'gan_days': 0}
                    
                    scores[stl_pair]['score'] += ai_score_contribution
                    scores[stl_pair]['reasons'].append(f"AI SẠCH: +{ai_score_contribution:.2f} ({max_prob*100.0:.1f}%)")

                    l1, l2 = stl_pair.split('-')
                    max_gan = max(gan_map.get(l1, 0), gan_map.get(l2, 0))
                    if max_gan > 0:
                        scores[stl_pair]['is_gan'] = True
                        scores[stl_pair]['gan_days'] = max_gan


        # --- 6. Định dạng lại và Sắp xếp ---
        final_list = []
        for pair_key, data in scores.items():
            final_list.append({
                'pair': pair_key,
                'score': round(data['score'], 2),
                'reasons': ", ".join(data['reasons']),
                'is_gan': data['is_gan'],
                'gan_days': data['gan_days']
            })
            
        final_list.sort(key=lambda x: x['score'], reverse=True)
        
        return final_list

    except Exception as e:
        import traceback
        print(f"LỖI get_top_scored_pairs: {e}")
        print(traceback.format_exc())
        return []

# ===================================================================================
# IV. HÀM MÔ PHỎNG LỊCH SỬ (SỬA LỖI GĐ 4)
# ===================================================================================

def get_consensus_simulation(all_data_df: pd.DataFrame, last_row_df: pd.DataFrame) -> List[Tuple[str, int, str]]:
    """ (SỬA LỖI GĐ 4) Bản sao của get_prediction_consensus (chạy N1 trong bộ nhớ). """
    print("... (Sim) Chạy get_consensus_simulation (GĐ 4)")
    prediction_sources = {} 
    
    bridge_manager = BridgeManager.get_instance()
    context = BridgeContext(historical_data=last_row_df)
    
    all_bridge_results: List[BridgeResult] = bridge_manager.run_all_bridges(context)

    for result in all_bridge_results:
        if result.prediction_type != 'STL' or not result.predictions:
            continue
            
        pair_key = _standardize_pair(result.predictions)
        if not pair_key: continue
            
        source_name = result.bridge_id
        if source_name.startswith("Cầu "):
            source_name = f"C{source_name.split(' ')[1]}"
            
        if pair_key not in prediction_sources:
            prediction_sources[pair_key] = []
        if source_name not in prediction_sources[pair_key]:
            prediction_sources[pair_key].append(source_name)
    
    consensus_list = []
    for pair_key, sources in prediction_sources.items():
        count = len(sources)
        sources_str = ", ".join(sources)
        consensus_list.append((pair_key, count, sources_str))
        
    consensus_list.sort(key=lambda item: item[1], reverse=True)
    return consensus_list

def get_high_win_simulation(all_data_ai: List[List[Any]], all_data_df: pd.DataFrame, last_row_df: pd.DataFrame, threshold: float) -> List[Dict[str, Any]]:
    """ (SỬA LỖI GĐ 4) Bản sao của TONGHOP_TOP_CAU_RATE_V5 (chạy N1 trong bộ nhớ). """
    print("... (Sim) Chạy get_high_win_simulation (GĐ 4)")
    high_win_bridges = []
    bridge_manager = BridgeManager.get_instance()

    # 1. Chạy Backtest N1 (Giống hệt TONGHOP_TOP_CAU_RATE_V5)
    bridge_performance: Dict[str, Dict[str, Any]] = defaultdict(lambda: {'hits': 0, 'total': 0})
    
    for i in range(1, len(all_data_ai)):
        current_row = all_data_ai[i] # Kỳ kết quả thực tế
        actual_lotos = getAllLoto_V30(current_row) 
        
        # Tạo BridgeContext
        context_df = all_data_df.iloc[[i-1]]
        context = BridgeContext(historical_data=context_df)
        
        all_bridge_results: List[BridgeResult] = bridge_manager.run_all_bridges(context)
        
        for result in all_bridge_results:
            bridge_id = result.bridge_id
            if result.prediction_type != 'STL': continue

            bridge_performance[bridge_id]['total'] += 1
            
            is_hit = False
            for pred_loto in result.predictions:
                if pred_loto in actual_lotos: 
                    is_hit = True
                    break
            
            if is_hit:
                bridge_performance[bridge_id]['hits'] += 1

    # 2. Lấy dự đoán cho ngày tiếp theo (dựa trên hàng cuối cùng)
    context_today = BridgeContext(historical_data=last_row_df)
    results_today: List[BridgeResult] = bridge_manager.run_all_bridges(context_today)
    
    # 3. Lọc các cầu có tỷ lệ cao
    for result in results_today:
        if result.prediction_type != 'STL' or not result.predictions:
            continue
        
        bridge_id = result.bridge_id
        perf = bridge_performance.get(bridge_id)
        
        if perf and perf['total'] > 0:
            rate = (perf['hits'] / perf['total']) * 100
            
            if rate >= threshold:
                high_win_bridges.append({
                    'name': bridge_id,
                    'stl': result.predictions,
                    'rate': f"{rate:.2f}%"
                })
            
    return high_win_bridges

# ===================================================================================
# (MỚI V7.2 Caching) HÀM TẠO CACHE TỐI ƯU HÓA
# ===================================================================================

def generate_full_optimization_cache(all_data_ai, progress_callback=None):
    """
    (SỬA LỖI GĐ 4)
    Tạo file cache chứa TOÀN BỘ dữ liệu backtest (Memory, K2N, Consensus, v.v.)
    cho TẤT CẢ các ngày trong lịch sử.
    """
    
    print(f"Bắt đầu tạo Cache Tối ưu hóa (GĐ 4) (sẽ mất thời gian)...")
    full_cache_data = {} 
    
    total_days = len(all_data_ai)
    
    # Tạo DataFrame MỘT LẦN
    all_data_df = pd.DataFrame(all_data_ai, columns=DF_COLUMNS)
    
    for day_index in range(50, total_days):
        
        if progress_callback and day_index % 10 == 0:
            progress_callback(day_index, total_days)
            
        # 1. Cắt lát dữ liệu (list) và (DataFrame)
        data_slice_list = all_data_ai[:day_index + 1]
        data_slice_df = all_data_df.iloc[:day_index + 1]
        
        last_row_list = data_slice_list[-1]
        last_row_df = data_slice_df.iloc[[-1]] # Lấy hàng cuối cùng của DF
        
        # 2. Lấy cài đặt mặc định
        n_days_stats = SETTINGS.STATS_DAYS
        n_days_gan = SETTINGS.GAN_DAYS
        high_win_thresh = SETTINGS.HIGH_WIN_THRESHOLD

        # 3. Chạy TẤT CẢ các hàm mô phỏng (GĐ 4)
        
        # (1) Loto Hot (Nhanh)
        stats_n_day = get_loto_stats_last_n_days(data_slice_list, n=n_days_stats)
        
        # (2) Cache K2N (Chờ N2) (GĐ 4 - Nhanh)
        # (SỬA LỖI) Lấy 2 hàng cuối
        if day_index > 0:
             pending_k2n_data = get_pending_k2n_bridges(all_data_ai[day_index], all_data_ai[day_index-1])
        else:
             pending_k2n_data = []
        
        # (3) Consensus (Vote) (GĐ 4 - Nhanh)
        consensus = get_consensus_simulation(data_slice_df, last_row_df)
        
        # (4) Cầu Tỷ Lệ Cao (GĐ 4 - RẤT NẶNG)
        high_win = get_high_win_simulation(data_slice_list, data_slice_df, last_row_df, threshold=high_win_thresh)

        # (5) Cầu Bạc Nhớ (CỰC KỲ NẶNG)
        top_memory_bridges = get_top_memory_bridge_predictions(data_slice_list, last_row_list, top_n=5)
        
        # (6) Lô Gan (Nhanh)
        gan_stats = get_loto_gan_stats(data_slice_list, n_days=n_days_gan)
        
        # 4. Lưu tất cả vào cache
        full_cache_data[day_index] = {
            'stats': stats_n_day,
            'pending_k2n': pending_k2n_data, # (GĐ 4) Giờ là LIST
            'consensus': consensus,
            'high_win': high_win,
            'memory': top_memory_bridges,
            'gan': gan_stats
        }

    # 5. Lưu vào file
    try:
        joblib.dump(full_cache_data, CACHE_FILE_PATH)
        print(f"Đã lưu Cache Tối ưu hóa (GĐ 4) vào {CACHE_FILE_PATH}")
        return True, f"Tạo cache (GĐ 4) thành công! ({len(full_cache_data)} ngày)"
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi LƯU cache: {e}")
        return False, f"Lỗi khi lưu cache: {e}"

# ===================================================================================
# (SỬA V7.2 Caching) HÀM WORKER MÔ PHỎNG LỊCH SỬ
# ===================================================================================

def get_historical_dashboard_data(all_data_ai, day_index, temp_settings, optimization_cache=None):
    """ 
    (V7.2 MP Caching UPGRADE)
    (SỬA LỖI GĐ 4) Viết lại chế độ CHẬM để dùng GĐ 4
    """
    
    # 1. Lấy dữ liệu (Hoặc từ Cache, hoặc tính toán)
    
    if optimization_cache:
        # === CHẾ ĐỘ CACHE (NHANH) ===
        try:
            cached_data = optimization_cache[day_index]
        except KeyError:
            return None 
            
        stats_n_day = cached_data['stats']
        pending_k2n_data = cached_data['pending_k2n']
        consensus = cached_data['consensus']
        high_win = cached_data['high_win']
        top_memory_bridges = cached_data['memory']
        gan_stats = cached_data['gan']

    else:
        # === CHẾ ĐỘ MÔ PHỎNG (CHẬM - SỬA LỖI GĐ 4) ===
        print("CẢNH BÁO: Chạy Tối ưu hóa ở chế độ CHẬM (Không có Cache).")
        
        # 1. Cắt lát dữ liệu (list) và (DataFrame)
        data_slice_list = all_data_ai[:day_index + 1]
        if len(data_slice_list) < 2: return None 
        
        # Tạo DataFrame cho lát cắt này
        data_slice_df = pd.DataFrame(data_slice_list, columns=DF_COLUMNS)
        
        last_row_list = data_slice_list[-1]
        last_row_df = data_slice_df.iloc[[-1]]
        
        # 2. Lấy các giá trị cài đặt tạm thời
        n_days_stats = int(temp_settings.get("STATS_DAYS", 7))
        n_days_gan = int(temp_settings.get("GAN_DAYS", 15))
        high_win_thresh = float(temp_settings.get("HIGH_WIN_THRESHOLD", 47.0))
        
        # 3. Chạy 7 hệ thống (phiên bản mô phỏng GĐ 4)
        stats_n_day = get_loto_stats_last_n_days(data_slice_list, n=n_days_stats)
        
        # (SỬA LỖI) Lấy 2 hàng cuối
        if day_index > 0:
             pending_k2n_data = get_pending_k2n_bridges(all_data_ai[day_index], all_data_ai[day_index-1])
        else:
             pending_k2n_data = []

        consensus = get_consensus_simulation(data_slice_df, last_row_df)
        
        high_win = get_high_win_simulation(data_slice_list, data_slice_df, last_row_df, threshold=high_win_thresh)
        
        # (Vô hiệu hóa Bạc Nhớ trong chế độ CHẬM vì quá nặng)
        top_memory_bridges = [] 
        
        gan_stats = get_loto_gan_stats(data_slice_list, n_days=n_days_gan)
    
    # === PHẦN CHUNG: CHẤM ĐIỂM ===
    top_scores = get_top_scored_pairs(
        stats_n_day,
        consensus, 
        high_win, 
        pending_k2n_data, # Dữ liệu pending K2N
        gan_stats,
        top_memory_bridges, # (Sẽ có dữ liệu nếu chạy bằng cache)
        ai_predictions=None # Tối ưu hóa không test AI
    )
    
    return top_scores