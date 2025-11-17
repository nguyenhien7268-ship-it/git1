# Tên file: du-an-backup/logic/ml_model.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA LỖI NameError 'X')
#
import os
import traceback  # (SỬA F821) Import traceback
# (SỬA F401) Xóa Counter, defaultdict
import joblib
import numpy as np
# (SỬA F401) Xóa 'import pandas as pd'
import xgboost as xgb  # <--- ĐÃ THAY THẾ RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Logic features are now prepared externally by lottery_service.py

# (SỬA F401) Xóa import SETTINGS không dùng

# ĐÃ SỬA: Cập nhật đường dẫn mới cho file mô hình và scaler
MODEL_FILE_PATH = "logic/ml_model_files/loto_model.joblib"
SCALER_FILE_PATH = "logic/ml_model_files/ai_scaler.joblib"

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
    Trả về: { 'ky_str': {'00': 0, '01': 5, ...}, ... }
    """
    print("... (AI Train) Bắt đầu tính toán Lịch sử Lô Gan (nặng)...")
    gan_history_map = {}
    current_gan = {loto: 0 for loto in ALL_LOTOS}

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

    print(f"... (AI Train) Đã tính xong Lịch sử Lô Gan ({len(gan_history_map)} ngày).")
    return gan_history_map


# ===================================================================
# II. HÀM TẠO BỘ DỮ LIỆU (TRAINING DATASET) (V7.0)
# ===================================================================


def _create_ai_dataset(all_data_ai, daily_bridge_predictions_map):
    """
    (V7.0) Tạo bộ dữ liệu X (features) và y (target) từ 2 nguồn:
    1. all_data_ai (dữ liệu KQXS)
    2. daily_bridge_predictions_map (dữ liệu features cầu đã tính toán trước)
    """
    X = []  # Features
    y = []  # Target (0 = trượt, 1 = trúng)

    # 1. Tính toán Lịch sử Gan (Feature F1)
    gan_history_map = _get_loto_gan_history(all_data_ai)

    # 2. Lặp qua các ngày (bỏ ngày đầu tiên, không có target)
    # Chúng ta dự đoán cho K(n) dựa trên dữ liệu K(n-1)
    for k in range(1, len(all_data_ai)):
        # Dữ liệu của ngày hôm trước (K(n-1))
        prev_row = all_data_ai[k - 1]
        prev_ky_str = str(prev_row[0])

        # Dữ liệu của ngày hôm nay (K(n)) - Dùng làm TARGET
        actual_row = all_data_ai[k]
        actual_ky_str = str(actual_row[0])
        actual_loto_set = set(getAllLoto_V30(actual_row))

        # Lấy features từ các nguồn đã tính toán trước
        gan_features_for_prev_ky = gan_history_map.get(prev_ky_str, {})
        bridge_features_for_actual_ky = daily_bridge_predictions_map.get(
            actual_ky_str, {}
        )

        if not gan_features_for_prev_ky or not bridge_features_for_actual_ky:
            # print(f"Bỏ qua kỳ {actual_ky_str}: Thiếu dữ liệu gan hoặc cầu.")
            continue

        # 3. Tạo 100 hàng dữ liệu (mỗi loto 1 hàng) cho ngày này
        for loto in ALL_LOTOS:
            features = []

            # === TARGET (y) ===
            # (Loto có về trong ngày K(n) không?)
            target = 1 if loto in actual_loto_set else 0
            y.append(target)

            # === FEATURES (X) ===
            # (Dựa trên dữ liệu của K(n-1))

            loto_features = bridge_features_for_actual_ky.get(loto, {})

            # --- FEATURE SET 1: GAN (F1) ---
            # F1: Loto này đã gan bao nhiêu ngày (tính đến K(n-1))
            features.append(gan_features_for_prev_ky.get(loto, 0))

            # --- FEATURE SET 2: VOTE COUNTS (F2 -> F4) ---
            # (Đây là dữ liệu của K(n), nhưng được tính bằng K(n-1))
            # F2: Số vote từ 15 Cầu Cổ Điển
            features.append(loto_features.get("v5_count", 0))
            # F3: Số vote từ Cầu Đã Lưu (V17)
            features.append(loto_features.get("v17_count", 0))
            # F4: Số vote từ Cầu Bạc Nhớ (756 cầu)
            features.append(loto_features.get("memory_count", 0))

            # --- FEATURE SET 3: TỔNG HỢP VOTE (F5 -> F6) ---
            # F5: Tổng số vote (F2+F3+F4)
            features.append(
                loto_features.get("v5_count", 0)
                + loto_features.get("v17_count", 0)
                + loto_features.get("memory_count", 0)
            )
            # F6: Số loại cầu vote (0-3)
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

            # Thêm hàng features này vào X
            X.append(features)

    return np.array(X), np.array(y)


# ===================================================================
# III. HÀM API CHÍNH (GỌI TỪ LOTTERY_SERVICE) (V7.0)
# ===================================================================


def train_ai_model(all_data_ai, daily_bridge_predictions_map):
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
        model = xgb.XGBClassifier(
            objective="binary:logistic",
            eval_metric="logloss",
            n_estimators=150,  # Tăng số cây
            learning_rate=0.05,
            max_depth=4,
            scale_pos_weight=scale_pos_weight,  # Cân bằng lớp
            use_label_encoder=False,
            random_state=42,
        )

        model.fit(X_train, y_train)
        print("... (AI Train) Huấn luyện hoàn tất.")

        # 5. Lưu mô hình và Scaler
        os.makedirs(os.path.dirname(MODEL_FILE_PATH), exist_ok=True)
        joblib.dump(model, MODEL_FILE_PATH)
        joblib.dump(scaler, SCALER_FILE_PATH)
        print(f"... (AI Train) Đã lưu mô hình vào '{MODEL_FILE_PATH}'")

        # 6. Đánh giá (Tùy chọn)
        accuracy = model.score(X_test, y_test)
        msg = f"Huấn luyện AI (V7.0) thành công! Độ chính xác (Test): {accuracy*100:.2f}%"
        print(f"... (AI Train) {msg}")
        return True, msg

    except Exception as e:
        # (SỬA F821) Thêm traceback.format_exc()
        return False, f"Lỗi nghiêm trọng khi Huấn luyện AI: {e}\n{traceback.format_exc()}"


def get_ai_predictions(all_data_ai, bridge_predictions_for_today):
    """
    (V7.0) API: Tải mô hình đã lưu và dự đoán 100 loto cho ngày mai.
    """
    try:
        # 1. Tải mô hình và Scaler
        if not os.path.exists(MODEL_FILE_PATH) or not os.path.exists(
            SCALER_FILE_PATH
        ):
            return (
                None,
                "Lỗi AI: Không tìm thấy file 'loto_model.joblib' hoặc 'ai_scaler.joblib'. Vui lòng Huấn luyện AI.",
            )
        model = joblib.load(MODEL_FILE_PATH)
        scaler = joblib.load(SCALER_FILE_PATH)

        # 2. Lấy dữ liệu Gan mới nhất (F1)
        # Chỉ cần tính cho ngày cuối cùng
        gan_history_map = _get_loto_gan_history(all_data_ai)
        last_ky_str = str(all_data_ai[-1][0])
        gan_features_today = gan_history_map.get(last_ky_str)

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

            # (SỬA LỖI V3) Thêm hàng features này vào X_new
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

        return results, "Dự đoán AI (V7.0) thành công."

    except Exception as e:
        # (SỬA F821) Thêm traceback.format_exc()
        return None, f"Lỗi nghiêm trọng khi Dự đoán AI: {e}\n{traceback.format_exc()}"

# (SỬA W292) Thêm dòng mới ở cuối file