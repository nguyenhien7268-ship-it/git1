# Tên file: git1/logic/ml_model.py
#
# (PHIÊN BẢN V7.9 - FIX PATH TUYỆT ĐỐI CHO MODEL FILES)
#
import os
import traceback

import joblib
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler

# --- CẤU HÌNH ĐƯỜNG DẪN TUYỆT ĐỐI ---
# Lấy thư mục hiện tại của file này (thư mục logic)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Đường dẫn tới thư mục lưu model (logic/ml_model_files)
MODEL_DIR = os.path.join(CURRENT_DIR, "ml_model_files")

# Đảm bảo thư mục tồn tại ngay khi import
if not os.path.exists(MODEL_DIR):
    try:
        os.makedirs(MODEL_DIR)
    except OSError:
        pass

# Cập nhật đường dẫn file
MODEL_FILE_PATH = os.path.join(MODEL_DIR, "loto_model.joblib")
SCALER_FILE_PATH = os.path.join(MODEL_DIR, "ai_scaler.joblib")
# -------------------------------------

ALL_LOTOS = [str(i).zfill(2) for i in range(100)]
MIN_DATA_TO_TRAIN = 50


def _standardize_pair(stl_list):
    """Helper: ['30', '01'] -> '01-30'"""
    if not stl_list or len(stl_list) != 2:
        return None
    return "-".join(sorted(stl_list))


# --- HÀM NỘI BỘ HỖ TRỢ (ĐƯỢC GIỮ LẠI ĐỂ TÍNH LOTO/GAN) ---
try:
    # Cố gắng import bằng relative import (khi chạy trong package)
    from .bridges.bridges_classic import getAllLoto_V30
except ImportError:
    # Fallback (nếu chạy độc lập hoặc lỗi)
    print("LỖI: ml_model.py không thể import getAllLoto_V30.")

    def getAllLoto_V30(row):
        return []


def _get_loto_gan_history(all_data_ai):
    """
    Nội bộ: Tính toán lịch sử gan (số ngày chưa về) cho TẤT CẢ loto TẤT CẢ các ngày.
    Rất nặng, chỉ chạy khi huấn luyện.
    (V7.7 Phase 2) Also calculates change in gan for F14 feature.
    Trả về:
        gan_history_map: { 'ky_str': {'00': 0, '01': 5, ...}, ... }
        gan_change_map: { 'ky_str': {'00': 0, '01': 1, ...}, ... }
    """
    print("... (AI Train) Bắt đầu tính toán Lịch sử Lô Gan (nặng)...")
    gan_history_map = {}
    gan_change_map = {}
    current_gan = {loto: 0 for loto in ALL_LOTOS}
    prev_gan = {loto: 0 for loto in ALL_LOTOS}

    # Bỏ qua ngày đầu tiên (không có gì để tính)
    for row in all_data_ai[1:]:
        ky_str = str(row[0])
        lotos_this_row = set(getAllLoto_V30(row))

        # 1. Cập nhật gan cho ngày HIỆN TẠI
        for loto in ALL_LOTOS:
            if loto in lotos_this_row:
                current_gan[loto] = 0  # Reset gan
            else:
                current_gan[loto] += 1  # Tăng gan

        # 2. Lưu trữ bản sao của gan (để dùng cho ngày MAI)
        # (Vì dự đoán cho ngày mai dựa trên gan của ngày hôm nay)
        gan_history_map[ky_str] = current_gan.copy()
        
        # (V7.7 Phase 2: F14) Calculate change in gan
        # Change = current_gan - prev_gan
        gan_change = {}
        for loto in ALL_LOTOS:
            gan_change[loto] = current_gan[loto] - prev_gan[loto]
        gan_change_map[ky_str] = gan_change
        
        # Update prev_gan for next iteration
        prev_gan = current_gan.copy()

    print(f"... (AI Train) Đã tính xong Lịch sử Lô Gan ({len(gan_history_map)} ngày).")
    return gan_history_map, gan_change_map


# ===================================================================
# II. HÀM TẠO BỘ DỮ LIỆU (TRAINING DATASET) (V7.0)
# ===================================================================


def _create_ai_dataset(all_data_ai, daily_bridge_predictions_map):
    X = []
    y = []
    gan_history_map, gan_change_map = _get_loto_gan_history(all_data_ai)

    for k in range(1, len(all_data_ai)):
        # Dữ liệu ngày hôm trước (Input Features)
        prev_row = all_data_ai[k - 1]
        prev_ky_str = str(prev_row[0])

        # Dữ liệu ngày hôm nay (Target)
        actual_row = all_data_ai[k]
        actual_ky_str = str(actual_row[0])
        actual_loto_set = set(getAllLoto_V30(actual_row))

        # Lấy Features từ QUÁ KHỨ (Ngày K-1)
        gan_features_for_prev_ky = gan_history_map.get(prev_ky_str, {})
        
        # [SỬA LỖI DATA LEAKAGE]
        # F14 phải lấy Change Gan của ngày hôm trước (K-1), không phải ngày hiện tại (K)
        # Change Gan (K-1) cho biết hôm qua nó vừa về hay vừa trượt -> Trend quá khứ
        gan_change_for_prev_ky = gan_change_map.get(prev_ky_str, {})
        
        bridge_features_for_actual_ky = daily_bridge_predictions_map.get(actual_ky_str, {})

        if not gan_features_for_prev_ky or not bridge_features_for_actual_ky:
            continue

        for loto in ALL_LOTOS:
            features = []
            target = 1 if loto in actual_loto_set else 0
            y.append(target)

            loto_features = bridge_features_for_actual_ky.get(loto, {})

            # F1: Gan (tính đến hôm qua)
            features.append(gan_features_for_prev_ky.get(loto, 0))
            
            # F2-F12: Các chỉ số cầu (đã tính từ hôm qua)
            features.append(loto_features.get("v5_count", 0))
            features.append(loto_features.get("v17_count", 0))
            features.append(loto_features.get("memory_count", 0))
            features.append(loto_features.get("v5_count", 0) + loto_features.get("v17_count", 0) + loto_features.get("memory_count", 0))
            f6 = (1 if loto_features.get("v5_count", 0) > 0 else 0) + \
                 (1 if loto_features.get("v17_count", 0) > 0 else 0) + \
                 (1 if loto_features.get("memory_count", 0) > 0 else 0)
            features.append(f6)
            features.append(loto_features.get("q_avg_win_rate", 0.0))
            features.append(loto_features.get("q_min_k2n_risk", 999.0))
            features.append(loto_features.get("q_max_curr_streak", -999.0))
            features.append(loto_features.get("q_max_current_lose_streak", 0))
            features.append(loto_features.get("q_is_k2n_risk_close", 0))
            features.append(loto_features.get("q_avg_win_rate_stddev_100", 0.0))
            features.append(loto_features.get("q_hit_in_last_3_days", 0))

            # F14: [ĐÃ SỬA] Change In Gan của ngày HÔM QUA (K-1)
            features.append(gan_change_for_prev_ky.get(loto, 0))

            X.append(features)

    return np.array(X), np.array(y)


# ===================================================================
# III. HÀM API CHÍNH (GỌI TỪ LOTTERY_SERVICE) (V7.0)
# ===================================================================


def _tune_hyperparameters(X_train, y_train, scale_pos_weight):
    """
    (Phase 3: Model Optimization) Tự động tìm hyperparameters tối ưu với GridSearchCV.
    
    Args:
        X_train: Training features
        y_train: Training labels
        scale_pos_weight: Weight for positive class
        
    Returns:
        dict: Best hyperparameters found
    """
    print("... (Phase 3) Bắt đầu Hyperparameter Tuning với GridSearchCV...")
    
    # Define parameter grid to search
    param_grid = {
        'n_estimators': [100, 150, 200],
        'max_depth': [3, 4, 5, 6],
        'learning_rate': [0.01, 0.05, 0.1],
        'min_child_weight': [1, 3, 5],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }
    
    # Base model for grid search
    base_model = xgb.XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        scale_pos_weight=scale_pos_weight,
        random_state=42
    )
    
    # GridSearchCV with 3-fold cross-validation
    grid_search = GridSearchCV(
        estimator=base_model,
        param_grid=param_grid,
        cv=3,
        scoring='accuracy',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    print(f"... (Phase 3) Best hyperparameters: {grid_search.best_params_}")
    print(f"... (Phase 3) Best CV score: {grid_search.best_score_:.4f}")
    
    return grid_search.best_params_


def train_ai_model(all_data_ai, daily_bridge_predictions_map, use_hyperparameter_tuning=False):
    """
    (V7.0) API: Huấn luyện, chuẩn hóa (scale), và lưu mô hình AI.
    """
    try:
        if not all_data_ai or len(all_data_ai) < MIN_DATA_TO_TRAIN:
            return (
                False,
                f"Lỗi Huấn luyện AI: Cần ít nhất {MIN_DATA_TO_TRAIN} kỳ dữ liệu.",
            )

        # 1. Tạo bộ dữ liệu
        print("... (AI Train) Đang tạo bộ dữ liệu X, y...")
        X, y = _create_ai_dataset(all_data_ai, daily_bridge_predictions_map)
        if X.shape[0] == 0 or y.shape[0] == 0:
            return False, "Lỗi Huấn luyện AI: Không thể tạo bộ dữ liệu (X, y rỗng)."
        print(f"... (AI Train) Đã tạo bộ dữ liệu (Shape: {X.shape}, {y.shape})")

        # 2. Chuẩn hóa (Scaling)
        print("... (AI Train) Đang chuẩn hóa (StandardScaler)...")
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # 3. Phân chia Train/Test
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )

        # 4. Huấn luyện (XGBoost)
        print("... (AI Train) Bắt đầu huấn luyện mô hình XGBoost...")
        # (V7.0) Tinh chỉnh XGBoost
        # Cân bằng trọng số lớp (vì lớp 1 (trúng) ít hơn lớp 0 (trượt))
        scale_pos_weight = (len(y) - sum(y)) / sum(y)
        
        # (Phase 3: Model Optimization) Hyperparameter tuning option
        if use_hyperparameter_tuning:
            best_params = _tune_hyperparameters(X_train, y_train, scale_pos_weight)
            model = xgb.XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                scale_pos_weight=scale_pos_weight,
                random_state=42,
                **best_params  # Use optimized hyperparameters
            )
        else:
            # Use default good parameters from config
            try:
                from .config_manager import SETTINGS
                n_estimators = getattr(SETTINGS, "AI_N_ESTIMATORS", 200)
                learning_rate = getattr(SETTINGS, "AI_LEARNING_RATE", 0.05)
                max_depth = getattr(SETTINGS, "AI_MAX_DEPTH", 6)
            except ImportError:
                n_estimators = 200
                learning_rate = 0.05
                max_depth = 6
                
            model = xgb.XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                n_estimators=n_estimators,
                learning_rate=learning_rate,
                max_depth=max_depth,
                scale_pos_weight=scale_pos_weight,
                random_state=42,
            )

        model.fit(X_train, y_train)
        print("... (AI Train) Huấn luyện hoàn tất.")
        
        # (Phase 3: Model Optimization) Cross-validation score
        print("... (Phase 3) Đang tính Cross-Validation score...")
        cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='accuracy')
        print(f"... (Phase 3) CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

        # 5. (Phase 3: Model Optimization) Extract and save feature importance
        print("... (Phase 3) Trích xuất Feature Importance...")
        feature_names = [
            "F1_Gan",
            "F2_V5_Count",
            "F3_V17_Count",
            "F4_Memory_Count",
            "F5_Total_Votes",
            "F6_Source_Diversity",
            "F7_Avg_Win_Rate",
            "F8_Min_K2N_Risk",
            "F9_Max_Curr_Streak",
            "F10_Max_Lose_Streak",
            "F11_Is_K2N_Risk_Close",
            "F12_Win_Rate_StdDev",
            "F13_Hit_Last_3_Days",
            "F14_Change_In_Gan"
        ]
        
        feature_importance = dict(zip(feature_names, model.feature_importances_))
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        print("... (Phase 3) Top 5 Features quan trọng nhất:")
        for i, (feature, importance) in enumerate(sorted_features[:5], 1):
            print(f"    {i}. {feature}: {importance:.4f}")
        
        # [FIX] Đảm bảo thư mục tồn tại trước khi lưu
        os.makedirs(MODEL_DIR, exist_ok=True)
        feature_importance_file = os.path.join(MODEL_DIR, "feature_importance.joblib")
        joblib.dump(feature_importance, feature_importance_file)
        
        # 6. Lưu mô hình và Scaler
        # os.makedirs(os.path.dirname(MODEL_FILE_PATH), exist_ok=True) # Đã làm ở trên
        joblib.dump(model, MODEL_FILE_PATH)
        joblib.dump(scaler, SCALER_FILE_PATH)
        print(f"... (AI Train) Đã lưu mô hình vào '{MODEL_FILE_PATH}'")

        # 7. Đánh giá (Tùy chọn)
        test_accuracy = model.score(X_test, y_test)
        cv_mean = cv_scores.mean()
        msg = (f"Huấn luyện AI (V7.7 - Phase 2) thành công!\n"
               f"Test Accuracy: {test_accuracy * 100:.2f}%\n"
               f"CV Accuracy: {cv_mean * 100:.2f}% (+/- {cv_scores.std() * 2 * 100:.2f}%)\n"
               f"Features: 14 (F13: Hit_Last_3_Days, F14: Change_In_Gan added)")
        print(f"... (AI Train) {msg}")
        return True, msg

    except Exception as e:
        return (
            False,
            f"Lỗi nghiêm trọng khi Huấn luyện AI: {e}\n{traceback.format_exc()}",
        )


def get_ai_predictions(all_data_ai, bridge_predictions_for_today):
    """
    (V7.0) API: Tải mô hình đã lưu và dự đoán 100 loto cho ngày mai.
    """
    try:
        # 1. Tải mô hình và Scaler
        if not os.path.exists(MODEL_FILE_PATH) or not os.path.exists(SCALER_FILE_PATH):
            return (
                None,
                "Lỗi AI: Không tìm thấy file 'loto_model.joblib' hoặc 'ai_scaler.joblib'. Vui lòng Huấn luyện AI.",
            )
        model = joblib.load(MODEL_FILE_PATH)
        scaler = joblib.load(SCALER_FILE_PATH)

        # 2. Lấy dữ liệu Gan mới nhất (F1) and Gan Change (F14)
        # Chỉ cần tính cho ngày cuối cùng
        gan_history_map, gan_change_map = _get_loto_gan_history(all_data_ai)
        last_ky_str = str(all_data_ai[-1][0])
        gan_features_today = gan_history_map.get(last_ky_str)
        gan_change_today = gan_change_map.get(last_ky_str, {})

        if not gan_features_today:
            return None, "Lỗi AI: Không thể tính Lô Gan cho ngày dự đoán."

        # 3. Tạo 100 hàng (loto) features (X_new)
        X_new = []
        for loto in ALL_LOTOS:
            features = []
            loto_features = bridge_predictions_for_today.get(loto, {})

            # --- FEATURE SET 1: GAN (F1) ---
            features.append(gan_features_today.get(loto, 0))

            # --- FEATURE SET 2: VOTE COUNTS (F2 -> F4) ---
            features.append(loto_features.get("v5_count", 0))
            features.append(loto_features.get("v17_count", 0))
            features.append(loto_features.get("memory_count", 0))

            # --- FEATURE SET 3: TỔNG HỢP VOTE (F5 -> F6) ---
            features.append(
                loto_features.get("v5_count", 0)
                + loto_features.get("v17_count", 0)
                + loto_features.get("memory_count", 0)
            )
            f6 = (
                (1 if loto_features.get("v5_count", 0) > 0 else 0)
                + (1 if loto_features.get("v17_count", 0) > 0 else 0)
                + (1 if loto_features.get("memory_count", 0) > 0 else 0)
            )
            features.append(f6)

            # --- FEATURE SET 4: CHẤT LƯỢNG (Q) FEATURES (F7 -> F9) ---
            # F7: Tỷ lệ thắng trung bình (Managed Bridges)
            features.append(loto_features.get("q_avg_win_rate", 0.0))

            # F8: Rủi ro K2N tối thiểu
            features.append(loto_features.get("q_min_k2n_risk", 999.0))

            # F9: Chuỗi Thắng/Thua hiện tại tối đa (Max Current Streak)
            features.append(loto_features.get("q_max_curr_streak", -999.0))

            # --- FEATURE SET 5: PHASE 2 NEW Q-FEATURES (F10 -> F12) ---
            # F10: Chuỗi thua liên tiếp hiện tại tối đa (Max Current Lose Streak)
            features.append(loto_features.get("q_max_current_lose_streak", 0))

            # F11: Binary indicator - Gần ngưỡng phạt K2N (Is K2N Risk Close)
            features.append(loto_features.get("q_is_k2n_risk_close", 0))

            # F12: Độ lệch chuẩn Win Rate (100 kỳ) - Đo ổn định của cầu
            features.append(loto_features.get("q_avg_win_rate_stddev_100", 0.0))

            # --- FEATURE SET 6: V7.7 PHASE 2 NEW FEATURES (F13 -> F14) ---
            # F13: Binary indicator - Loto có về trong 3 kỳ gần đây không
            features.append(loto_features.get("q_hit_in_last_3_days", 0))

            # F14: Thay đổi giá trị Gan (Change_in_Gan)
            features.append(gan_change_today.get(loto, 0))

            # Thêm hàng features này vào X_new
            X_new.append(features)

        X_new_scaled = scaler.transform(np.array(X_new))

        # Dự đoán xác suất (Probability)
        probabilities = model.predict_proba(X_new_scaled)[
            :, 1
        ]  # Lấy xác suất của lớp 1 (Có về)

        results = []
        for i, loto in enumerate(ALL_LOTOS):
            results.append(
                {"loto": loto, "probability": probabilities[i] * 100}  # Chuyển sang %
            )

        # Sắp xếp theo xác suất giảm dần
        results.sort(key=lambda x: x["probability"], reverse=True)

        return results, "Dự đoán AI (V7.7 - 14 Features) thành công."

    except Exception as e:
        return None, f"Lỗi nghiêm trọng khi Dự đoán AI: {e}\n{traceback.format_exc()}"