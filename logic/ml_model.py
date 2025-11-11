import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import os
from collections import defaultdict, Counter

# Logic features are now prepared externally by lottery_service.py

try:
    from .config_manager import SETTINGS
except ImportError:
    from config_manager import SETTINGS

# ĐÃ SỬA: Cập nhật đường dẫn mới cho file mô hình và scaler
MODEL_FILE_PATH = "logic/ml_model_files/loto_model.joblib"
SCALER_FILE_PATH = "logic/ml_model_files/ai_scaler.joblib" 

ALL_LOTOS = [str(i).zfill(2) for i in range(100)]
MIN_DATA_TO_TRAIN = 50 

def _standardize_pair(stl_list):
    """Helper: ['30', '01'] -> '01-30'"""
    if not stl_list or len(stl_list) != 2: return None
    return "-".join(sorted(stl_list))

# --- HÀM NỘI BỘ HỖ TRỢ (ĐƯỢC GIỮ LẠI ĐỂ TÍNH LOTO/GAN) ---
try:
    # Cố gắng import bằng relative import (khi chạy trong package)
    from .bridges.bridges_classic import getAllLoto_V30 # ĐÃ SỬA
    from .dashboard_analytics import get_loto_stats_last_n_days, get_loto_gan_stats
except ImportError:
    # Fallback: cố gắng import bằng absolute path (khi chạy test hoặc lỗi package)
    try:
        from logic.bridges.bridges_classic import getAllLoto_V30 # ĐÃ SỬA
        from dashboard_analytics import get_loto_stats_last_n_days, get_loto_gan_stats
    except ImportError:
         print("LỖI KHÔNG THỂ IMPORT: bridges_classic hoặc dashboard_analytics.")
         def getAllLoto_V30(r): return []
         def get_loto_stats_last_n_days(a, b): return {}
         def get_loto_gan_stats(a, b): return {}


def prepare_training_data(all_data_ai, daily_bridge_predictions):
    """
    (V7.0 G2) Tạo bộ dữ liệu huấn luyện. Bổ sung 3 Q-Features.
    """
    if not all_data_ai or len(all_data_ai) < MIN_DATA_TO_TRAIN:
        print(f"Cần tối thiểu {MIN_DATA_TO_TRAIN} kỳ để huấn luyện AI.")
        return None, None
        
    print("... (AI V7.0 G2) Bước 2: Bắt đầu trích xuất đặc trưng (features) và nhãn (labels)...")

    X = [] # Features
    y = [] # Labels (Lô tô có về hay không)

    # Lặp qua tất cả các kỳ (trừ kỳ đầu tiên vì cần dữ liệu ngày hôm trước)
    for i in range(1, len(all_data_ai)):
        current_data = all_data_ai[i] 
        previous_data = all_data_ai[i-1] 

        current_ky = str(current_data[0])

        # 1. TÍNH NHÃN (LABELS) - Loto về trong kỳ hiện tại
        current_loto_results = set(getAllLoto_V30(current_data))
        
        # 2. TẠO TẬP ĐẶC TRƯNG (FEATURES)
        
        bridge_predictions = daily_bridge_predictions.get(current_ky, {})
        
        # FIX: Sửa truy cập SETTINGS (dùng getattr an toàn hơn)
        gan_max_days = getattr(SETTINGS, 'GAN_DAYS', 8)
        stats_days = getattr(SETTINGS, 'STATS_DAYS', 7) 
        
        # Tính Loto Hot/Gan từ lịch sử (dữ liệu từ 0 đến i-1)
        loto_gan_stats_list = get_loto_gan_stats(all_data_ai[:i], gan_max_days)
        loto_stats_last_7_list = get_loto_stats_last_n_days(all_data_ai[:i], stats_days)
        
        # FIX LOGIC: Chuyển List of Tuples thành Map để có thể dùng .get()
        loto_gan_stats_map = {loto: days for loto, days in loto_gan_stats_list}
        # loto_stats_last_7 trả về (loto, hit_count, day_count) -> chỉ cần hit_count
        loto_stats_last_7_map = {loto: hit_count for loto, hit_count, day_count in loto_stats_last_7_list}


        for loto in ALL_LOTOS:
            features = []
            
            # --- FEATURE CƠ BÁI (F1 -> F6) ---
            # F1: Tần suất Lô tô Hot (Về trong 7 ngày gần nhất)
            features.append(loto_stats_last_7_map.get(loto, 0) / stats_days)
            
            # F2: Tần suất Lô tô Gan (Số ngày Gan)
            features.append(loto_gan_stats_map.get(loto, 0) / gan_max_days) 

            # Lấy features về cầu cho loto này (ĐÃ ĐƯỢC CUNG CẤP TỪ BÊN NGOÀI)
            loto_features = bridge_predictions.get(loto, {})
            
            # F3: Số vote Cầu Cổ Điển (Bridges V5)
            features.append(loto_features.get('v5_count', 0))
            
            # F4: Số vote Cầu V17/Shadow
            features.append(loto_features.get('v17_count', 0))
            
            # F5: Số vote Cầu Bạc Nhớ (Memory)
            features.append(loto_features.get('memory_count', 0))
            
            # F6: Về ngày hôm trước 
            loto_came_yesterday = 1 if loto in set(getAllLoto_V30(previous_data)) else 0
            features.append(loto_came_yesterday)

            # --- [MỚI V7.0 G2] Q-FEATURES (F7 -> F9) ---
            # F7: Tỷ lệ thắng trung bình (Managed Bridges)
            features.append(loto_features.get('q_avg_win_rate', 0.0) / 100.0) # Chuẩn hóa về 0-1
            
            # F8: Rủi ro K2N tối thiểu (Sử dụng 1/Risk để Risk cao -> Feature thấp)
            min_k2n_risk = loto_features.get('q_min_k2n_risk', 999.0)
            features.append(1.0 / (min_k2n_risk + 1.0)) # (Risk=0 -> Feature=1.0. Risk=999 -> Feature gần 0)
            
            # F9: Chuỗi Thắng/Thua hiện tại tối đa (Max Current Streak)
            max_curr_streak = loto_features.get('q_max_curr_streak', -999.0)
            features.append(max_curr_streak / 100.0) # Chuẩn hóa dựa trên một ngưỡng max giả định 100

            X.append(features)
            y.append(1 if loto in current_loto_results else 0)

    print(f"... Đã tạo {len(X)} mẫu dữ liệu để huấn luyện (X.shape={len(X)}).")
    return np.array(X), np.array(y)


def train_ai_model(all_data_ai, daily_bridge_predictions):
    """
    (V7.0 G2) Hàm huấn luyện AI. Sử dụng tham số tuning từ config.
    """
    if all_data_ai is None:
        return False, "Dữ liệu AI rỗng. Vui lòng kiểm tra lại DB."
        
    try:
        X, y = prepare_training_data(all_data_ai, daily_bridge_predictions)
        
        if X is None:
            return False, "Không đủ dữ liệu hoặc lỗi khi chuẩn bị tập huấn luyện."

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Chuẩn hóa dữ liệu (Scaling)
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
        
        # === [MỚI V7.0 G2] SỬ DỤNG THAM SỐ TỪ CONFIG ===
        # FIX: Sửa truy cập SETTINGS
        max_depth = getattr(SETTINGS, 'AI_MAX_DEPTH', 15)
        n_estimators = getattr(SETTINGS, 'AI_N_ESTIMATORS', 100)
        
        print(f"... Bắt đầu huấn luyện mô hình RandomForest: Depth={max_depth}, Est={n_estimators}")
        
        model = RandomForestClassifier(
            n_estimators=n_estimators, 
            max_depth=max_depth, 
            random_state=42, 
            class_weight='balanced',
            n_jobs=-1 # Sử dụng tất cả CPU
        )
        model.fit(X_train, y_train)
        
        # Lưu mô hình và Scaler (ĐÃ CẬP NHẬT ĐƯỜNG DẪN)
        joblib.dump(model, MODEL_FILE_PATH)
        joblib.dump(scaler, SCALER_FILE_PATH)
        
        # Đánh giá cơ bản
        accuracy = model.score(X_test, y_test)

        return True, f"Huấn luyện thành công (V7.0 G2)! Độ chính xác cơ bản: {accuracy:.4f}. Đã lưu mô hình vào {MODEL_FILE_PATH}"

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return False, f"Lỗi nghiêm trọng khi huấn luyện AI (V7.0 G2): {e}"


def get_ai_predictions(all_data_ai, bridge_predictions_for_today):
    """
    (V7.0 G2) Hàm dự đoán. Sử dụng 3 Q-Features mới.
    """
    
    # ĐÃ SỬA: Dùng hằng số mới
    if not os.path.exists(MODEL_FILE_PATH) or not os.path.exists(SCALER_FILE_PATH):
        return None, "Lỗi: Không tìm thấy tệp mô hình `loto_model.joblib` hoặc `ai_scaler.joblib`. Vui lòng chạy 'Huấn luyện AI' trước."
        
    if not all_data_ai or len(all_data_ai) < 2:
        return None, "Không đủ dữ liệu lịch sử để dự đoán."
        
    try:
        # Tải bằng hằng số mới
        model = joblib.load(MODEL_FILE_PATH)
        scaler = joblib.load(SCALER_FILE_PATH)
        
        print("... (AI V7.0 G2) Đang trích xuất đặc trưng dự đoán...")

        X_new = []
        last_data = all_data_ai[-1] # Dữ liệu kỳ gần nhất (D)
        
        # FIX: Sửa truy cập SETTINGS (dùng getattr an toàn hơn)
        gan_max_days = getattr(SETTINGS, 'GAN_DAYS', 8)
        stats_days = getattr(SETTINGS, 'STATS_DAYS', 7) 
        
        # Tính Loto Hot/Gan từ toàn bộ lịch sử
        loto_gan_stats_list = get_loto_gan_stats(all_data_ai, gan_max_days)
        loto_stats_last_7_list = get_loto_stats_last_n_days(all_data_ai, stats_days)
        
        # FIX LOGIC: Chuyển List of Tuples thành Map để có thể dùng .get()
        loto_gan_stats_map = {loto: days for loto, days in loto_gan_stats_list}
        loto_stats_last_7_map = {loto: hit_count for loto, hit_count, day_count in loto_stats_last_7_list}
        
        # Loto về ngày hôm qua (D)
        loto_came_yesterday_set = set(getAllLoto_V30(last_data))

        for loto in ALL_LOTOS:
            features = []
            
            # --- FEATURE CƠ BẢI (F1 -> F6) ---
            # F1: Tần suất Lô tô Hot 
            features.append(loto_stats_last_7_map.get(loto, 0) / stats_days)
            
            # F2: Tần suất Lô tô Gan 
            features.append(loto_gan_stats_map.get(loto, 0) / gan_max_days) 

            # Lấy features về cầu cho loto này 
            loto_features = bridge_predictions_for_today.get(loto, {})
            
            # F3: Số vote Cầu Cổ Điển 
            features.append(loto_features.get('v5_count', 0))
            
            # F4: Số vote Cầu V17/Shadow
            features.append(loto_features.get('v17_count', 0))
            
            # F5: Số vote Cầu Bạc Nhớ 
            features.append(loto_features.get('memory_count', 0))
            
            # F6: Về ngày hôm trước 
            loto_came_yesterday = 1 if loto in loto_came_yesterday_set else 0
            features.append(loto_came_yesterday)

            # --- [MỚI V7.0 G2] Q-FEATURES (F7 -> F9) ---
            # F7: Tỷ lệ thắng trung bình (Managed Bridges)
            features.append(loto_features.get('q_avg_win_rate', 0.0) / 100.0) 
            
            # F8: Rủi ro K2N tối thiểu (Sử dụng 1/Risk để Risk cao -> Feature thấp)
            min_k2n_risk = loto_features.get('q_min_k2n_risk', 999.0)
            features.append(1.0 / (min_k2n_risk + 1.0))
            
            # F9: Chuỗi Thắng/Thua hiện tại tối đa (Max Current Streak)
            max_curr_streak = loto_features.get('q_max_curr_streak', -999.0)
            features.append(max_curr_streak / 100.0)
            
            X_new.append(features)

        X_new_scaled = scaler.transform(np.array(X_new))
        
        # Dự đoán xác suất (Probability)
        probabilities = model.predict_proba(X_new_scaled)[:, 1] # Lấy xác suất của lớp 1 (Có về)
        
        results = []
        for i, loto in enumerate(ALL_LOTOS):
            results.append({
                'loto': loto,
                'probability': probabilities[i] * 100 # Chuyển sang %
            })

        results.sort(key=lambda x: x['probability'], reverse=True)
        print("... (AI V7.0 G2) Dự đoán hoàn tất.")
        
        return results, f"AI (Q-Features V7.0 G2) đã dự đoán (Top 1: {results[0]['loto']} - {results[0]['probability']:.1f}%)"

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return None, f"Lỗi khi dự đoán AI (V7.0 G2): {e}"