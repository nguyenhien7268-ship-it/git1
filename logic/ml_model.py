import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import os
from collections import defaultdict, Counter

# Import các hàm nghiệp vụ (logic) hiện có
try:
    from .backtester import (
        get_loto_stats_last_n_days, # Giữ lại
        get_loto_gan_stats,       # Giữ lại
        run_and_update_all_bridge_K2N_cache, # Dùng 1 lần
        get_prediction_consensus,            # Dùng 1 lần
        get_high_win_rate_predictions,       # Dùng 1 lần
        get_top_memory_bridge_predictions    # Dùng 1 lần
    )
    from .bridges_classic import getAllLoto_V30, ALL_15_BRIDGE_FUNCTIONS_V5
    from .bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong
    from .bridges_memory import get_27_loto_positions, calculate_bridge_stl, get_27_loto_names
    from .config_manager import SETTINGS
    from .db_manager import get_all_managed_bridges, DB_NAME
except ImportError:
    print("LỖI: ml_model (V2) không thể import. Đang chạy fallback...")
    from backtester import (
        get_loto_stats_last_n_days, get_loto_gan_stats, 
        run_and_update_all_bridge_K2N_cache, get_prediction_consensus,
        get_high_win_rate_predictions, get_top_memory_bridge_predictions
    )
    from bridges_classic import getAllLoto_V30, ALL_15_BRIDGE_FUNCTIONS_V5
    from bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong
    from bridges_memory import get_27_loto_positions, calculate_bridge_stl, get_27_loto_names
    from config_manager import SETTINGS
    from db_manager import get_all_managed_bridges, DB_NAME


MODEL_FILE_PATH = "loto_model.joblib"
ALL_LOTOS = [str(i).zfill(2) for i in range(100)]
MIN_DATA_TO_TRAIN = 50 # Số ngày tối thiểu để bắt đầu tính toán

def _standardize_pair(stl_list):
    """Helper: ['30', '01'] -> '01-30'"""
    if not stl_list or len(stl_list) != 2: return None
    return "-".join(sorted(stl_list))

def _get_daily_bridge_predictions(all_data_ai):
    """
    (MỚI - TỐI ƯU) Lặp qua CSDL 1 LẦN DUY NHẤT
    để lấy dự đoán N1 của TẤT CẢ các cầu cho TẤT CẢ các ngày.
    """
    print("... (AI Optimize) Bước 1: Tính toán dự đoán cầu cho toàn bộ lịch sử...")
    
    # { 'Kỳ 123': { '01-10': ['C1', 'V17_A'], '55-66': ['C2'] } }
    daily_predictions = defaultdict(lambda: defaultdict(list))
    
    managed_bridges = get_all_managed_bridges(DB_NAME, only_enabled=True)
    memory_bridges = [] # (idx1, idx2, type, name)
    
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
            print(f"... (AI Optimize) Bước 1: Đã xử lý {k}/{len(all_data_ai)} ngày (dự đoán cầu)")

        # 1. 15 Cầu Cổ Điển
        for i, bridge_func in enumerate(ALL_15_BRIDGE_FUNCTIONS_V5):
            try:
                stl = bridge_func(prev_row)
                pair_key = _standardize_pair(stl)
                if pair_key:
                    daily_predictions[current_ky][pair_key].append(f'C{i+1}')
            except Exception:
                pass

        # 2. Cầu Đã Lưu (V17)
        prev_positions_v17 = getAllPositions_V17_Shadow(prev_row)
        for bridge in managed_bridges:
            try:
                if bridge["pos1_idx"] == -1: continue # Bỏ qua cầu Bạc Nhớ (nếu lỡ lưu)
                idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                a, b = prev_positions_v17[idx1], prev_positions_v17[idx2]
                if a is None or b is None: continue
                stl = taoSTL_V30_Bong(a, b)
                pair_key = _standardize_pair(stl)
                if pair_key:
                    daily_predictions[current_ky][pair_key].append(bridge['name'])
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
                    daily_predictions[current_ky][pair_key].append(alg_name)
            except Exception:
                pass
                
    return daily_predictions

def prepare_training_data(all_data_ai):
    """
    (V2 - TỐI ƯU HÓA) 
    Tạo bộ dữ liệu huấn luyện bằng cách lặp 1 lần, không mô phỏng.
    """
    if not all_data_ai or len(all_data_ai) < MIN_DATA_TO_TRAIN:
        return None, None

    # Tối ưu hóa: Lấy TẤT CẢ dự đoán cầu (V17, BN, CĐ) cho TẤT CẢ các ngày
    # Đây là phần nặng nhất, nhưng chỉ chạy 1 lần.
    daily_bridge_predictions = _get_daily_bridge_predictions(all_data_ai)
    
    print("... (AI Optimize) Bước 2: Bắt đầu trích xuất đặc trưng (features) và nhãn (labels)...")

    X_data = [] # List các dict đặc trưng
    y_data = [] # List các nhãn (0 hoặc 1)

    all_loto_sets = {str(row[0]): set(getAllLoto_V30(row)) for row in all_data_ai}
    
    # Lặp từ ngày 50 đến ngày cuối cùng
    for k in range(MIN_DATA_TO_TRAIN, len(all_data_ai)):
        # Dữ liệu ngày D (để tạo đặc trưng)
        current_row = all_data_ai[k]
        current_ky = str(current_row[0])
        
        # Dữ liệu ngày D-1 (để lấy Loto về)
        prev_ky = str(all_data_ai[k-1][0])
        prev_loto_set = all_loto_sets.get(prev_ky, set())
        
        if k % 100 == 0:
            print(f"... (AI Optimize) Bước 2: Đã xử lý {k}/{len(all_data_ai)} ngày (tạo X, y)")

        # Lấy các đặc trưng tại ngày D
        
        # 1. Đặc trưng Tần suất (Loto Hot)
        data_slice_stats = all_data_ai[:k] # Lấy lịch sử đến ngày D
        stats_n_day = get_loto_stats_last_n_days(data_slice_stats, n=SETTINGS.STATS_DAYS)
        hot_loto_map = {loto: count for loto, count, _ in stats_n_day}
        
        # 2. Đặc trưng Lô Gan
        gan_stats = get_loto_gan_stats(data_slice_stats, n_days=SETTINGS.GAN_DAYS)
        gan_map = {loto: days for loto, days in gan_stats}
        
        # 3. Đặc trưng Cầu (Lấy từ dữ liệu đã tính toán ở Bước 1)
        # { '01-10': ['C1', 'V17_A'], '55-66': ['C2'] }
        bridge_preds_today = daily_bridge_predictions.get(current_ky, {})
        
        # Xây dựng map tra cứu ngược (loto -> list[cặp])
        loto_to_pairs = defaultdict(list)
        for pair_key in bridge_preds_today.keys():
            loto1, loto2 = pair_key.split('-')
            loto_to_pairs[loto1].append(pair_key)
            loto_to_pairs[loto2].append(pair_key)
        
        # 4. Đặc trưng Nhãn (y) - Kết quả của ngày D
        actual_loto_set = all_loto_sets.get(current_ky, set())

        # Lặp qua 100 loto để tạo 100 mẫu dữ liệu
        for loto in ALL_LOTOS:
            
            # --- TÍNH TOÁN ĐẶC TRƯNG (X) ---
            f_hot_count = hot_loto_map.get(loto, 0)
            f_gan_days = gan_map.get(loto, 0)
            
            # Đặc trưng Cầu
            f_classic_votes = 0
            f_v17_votes = 0
            f_memory_votes = 0
            
            pairs_for_this_loto = loto_to_pairs.get(loto, [])
            if pairs_for_this_loto:
                all_bridges_for_loto = []
                for pair in pairs_for_this_loto:
                    all_bridges_for_loto.extend(bridge_preds_today[pair])
                
                bridge_counts = Counter(all_bridges_for_loto)
                for bridge_name, count in bridge_counts.items():
                    if bridge_name.startswith('C'):
                        f_classic_votes += count
                    elif bridge_name.startswith('Tổng') or bridge_name.startswith('Hiệu'):
                        f_memory_votes += count
                    else:
                        f_v17_votes += count
            
            # Đặc trưng Loto về hôm qua
            f_hit_yesterday = 1 if loto in prev_loto_set else 0
            
            # Gộp đặc trưng
            features = {
                'f_hot_count': f_hot_count,
                'f_gan_days': f_gan_days,
                'f_classic_votes': f_classic_votes,
                'f_v17_votes': f_v17_votes,
                'f_memory_votes': f_memory_votes,
                'f_hit_yesterday': f_hit_yesterday
            }
            X_data.append(features)
            
            # --- TÍNH TOÁN NHÃN (y) ---
            label = 1 if loto in actual_loto_set else 0
            y_data.append(label)

    if not X_data:
        return None, None

    # Chuyển đổi sang DataFrame
    X_train = pd.DataFrame(X_data)
    y_train = pd.Series(y_data)
    
    print(f"Tạo dữ liệu huấn luyện hoàn tất. Tổng số mẫu: {len(y_train)}.")
    return X_train, y_train


def train_ai_model(all_data_ai):
    """
    (V2) Hàm được gọi từ Giao diện (UI) để bắt đầu huấn luyện.
    """
    try:
        X, y = prepare_training_data(all_data_ai)
        
        if X is None or y is None or X.empty:
            return False, "Không thể tạo dữ liệu huấn luyện (có thể do quá ít dữ liệu)."

        print("... (AI Optimize) Bước 3: Bắt đầu huấn luyện mô hình RandomForest...")
        
        model = RandomForestClassifier(
            n_estimators=100,       # Giảm số lượng cây (100 là đủ)
            max_depth=15,           
            min_samples_leaf=10,    # Tăng min_samples_leaf để chống quá khớp
            random_state=42,
            n_jobs=-1               # Sử dụng tất cả các CPU
        )
        
        model.fit(X, y)
        
        print("... (AI Optimize) Bước 4: Huấn luyện hoàn tất. Đang lưu mô hình...")
        
        joblib.dump(model, MODEL_FILE_PATH)
        
        return True, f"Huấn luyện thành công (Tối ưu hóa V2)! Đã lưu mô hình vào {MODEL_FILE_PATH}"

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return False, f"Lỗi nghiêm trọng khi huấn luyện AI (V2): {e}"


def get_ai_predictions(all_data_ai):
    """
    (V2) Hàm được gọi bởi Bảng Tổng Hợp để lấy dự đoán cho ngày mai.
    """
    
    if not os.path.exists(MODEL_FILE_PATH):
        return None, "Lỗi: Không tìm thấy tệp mô hình `loto_model.joblib`. Vui lòng chạy 'Huấn luyện AI' trước."
        
    try:
        model = joblib.load(MODEL_FILE_PATH)
        
        print("... (AI V2) Đang trích xuất đặc trưng cho dữ liệu mới nhất...")
        
        # --- Trích xuất đặc trưng cho DỮ LIỆU MỚI NHẤT (D) ---
        
        # 1. Lấy dữ liệu D và D-1
        current_row = all_data_ai[-1]
        prev_row = all_data_ai[-2]
        prev_loto_set = set(getAllLoto_V30(prev_row))
        current_ky = str(current_row[0]) # Kỳ D

        # 2. Đặc trưng Tần suất (Loto Hot)
        stats_n_day = get_loto_stats_last_n_days(all_data_ai, n=SETTINGS.STATS_DAYS)
        hot_loto_map = {loto: count for loto, count, _ in stats_n_day}
        
        # 3. Đặc trưng Lô Gan
        gan_stats = get_loto_gan_stats(all_data_ai, n_days=SETTINGS.GAN_DAYS)
        gan_map = {loto: days for loto, days in gan_stats}
        
        # 4. Đặc trưng Cầu (Chỉ tính cho ngày D)
        # Chúng ta cần dự đoán cho ngày D+1, vì vậy chúng ta cần đặc trưng của ngày D
        # Dự đoán cầu được tạo từ prev_row (D-1) cho current_row (D)
        
        # Lấy dự đoán cầu cho ngày D
        daily_preds = _get_daily_bridge_predictions([prev_row, current_row])
        bridge_preds_today = daily_preds.get(current_ky, {}) # Lấy dự đoán cho ngày D
        
        loto_to_pairs = defaultdict(list)
        for pair_key in bridge_preds_today.keys():
            loto1, loto2 = pair_key.split('-')
            loto_to_pairs[loto1].append(pair_key)
            loto_to_pairs[loto2].append(pair_key)
            
        # --- Tạo 100 mẫu (X_predict) ---
        X_predict_data = []
        for loto in ALL_LOTOS:
            f_hot_count = hot_loto_map.get(loto, 0)
            f_gan_days = gan_map.get(loto, 0)
            
            f_classic_votes = 0
            f_v17_votes = 0
            f_memory_votes = 0
            
            pairs_for_this_loto = loto_to_pairs.get(loto, [])
            if pairs_for_this_loto:
                all_bridges_for_loto = []
                for pair in pairs_for_this_loto:
                    all_bridges_for_loto.extend(bridge_preds_today[pair])
                
                bridge_counts = Counter(all_bridges_for_loto)
                for bridge_name, count in bridge_counts.items():
                    if bridge_name.startswith('C'):
                        f_classic_votes += count
                    elif bridge_name.startswith('Tổng') or bridge_name.startswith('Hiệu'):
                        f_memory_votes += count
                    else:
                        f_v17_votes += count
            
            f_hit_yesterday = 1 if loto in prev_loto_set else 0
            
            features = {
                'f_hot_count': f_hot_count,
                'f_gan_days': f_gan_days,
                'f_classic_votes': f_classic_votes,
                'f_v17_votes': f_v17_votes,
                'f_memory_votes': f_memory_votes,
                'f_hit_yesterday': f_hit_yesterday
            }
            X_predict_data.append(features)

        X_predict = pd.DataFrame(X_predict_data)
        
        # 5. Yêu cầu mô hình dự đoán XÁC SUẤT
        probabilities = model.predict_proba(X_predict)[:, 1]
        
        # 6. Gộp kết quả
        results = []
        for i, loto in enumerate(ALL_LOTOS):
            results.append({
                'loto': loto,
                'probability': probabilities[i] * 100 
            })
            
        results.sort(key=lambda x: x['probability'], reverse=True)
        
        print("... (AI V2) Dự đoán hoàn tất.")
        return results, f"AI (Tối ưu V2) đã dự đoán (Top 1: {results[0]['loto']} - {results[0]['probability']:.1f}%)"

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return None, f"Lỗi khi dự đoán AI (V2): {e}"