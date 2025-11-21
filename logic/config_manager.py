import json
import os
import traceback

CONFIG_FILE = "config.json"


class AppSettings:
    """
    (SỬA LỖI V7.0 GĐ3) Lớp Singleton để giữ cài đặt toàn cục.
    Lưu trữ tất cả các tham số có thể định cấu hình của hệ thống.
    """

    def __init__(self):
        # Giá trị mặc định (ĐÃ THÊM AI_LEARNING_RATE, AI_OBJECTIVE, RECENT_FORM)
        self.defaults = {
            "STATS_DAYS": 7,
            "GAN_DAYS": 15,
            "HIGH_WIN_THRESHOLD": 47.0,
            "AUTO_ADD_MIN_RATE": 50.0,
            "AUTO_PRUNE_MIN_RATE": 40.0,
            "K2N_RISK_START_THRESHOLD": 4,
            "K2N_RISK_PENALTY_PER_FRAME": 0.5,
            "AI_PROB_THRESHOLD": 45.0,
            "AI_MAX_DEPTH": 15,
            "AI_N_ESTIMATORS": 100,
            "AI_LEARNING_RATE": 0.1,  # MỚI: Learning Rate cho GBM
            "AI_OBJECTIVE": "binary:logistic",  # MỚI: Objective cho XGBoost/LightGBM
            "AI_SCORE_WEIGHT": 0.3,  # IMPROVED: Tăng từ 0.2 → 0.3
            "RECENT_FORM_PERIODS": 10,
            "RECENT_FORM_BONUS_VERY_HIGH": 4.0,  # MỚI: Tier Very High
            "RECENT_FORM_BONUS_HIGH": 3.0,
            "RECENT_FORM_BONUS_MED": 2.0,
            "RECENT_FORM_BONUS_LOW": 1.0,
            "RECENT_FORM_MIN_VERY_HIGH": 9,  # MỚI: Ngưỡng Very High
            "RECENT_FORM_MIN_HIGH": 7,  # IMPROVED: Giảm từ 8 → 7
            "RECENT_FORM_MIN_MED": 5,  # IMPROVED: Giảm từ 6 → 5
            "RECENT_FORM_MIN_LOW": 3,  # IMPROVED: Giảm từ 5 → 3
            "VOTE_SCORE_WEIGHT": 0.5,  # MỚI: Trọng số vote với decay
            "HIGH_WIN_SCORE_BONUS": 2.5,  # IMPROVED: Tăng từ 2.0 → 2.5
            "K2N_RISK_PROGRESSIVE": True,  # MỚI: Bật progressive penalty
        }

        # Tải cài đặt
        self.load_settings()

    def load_settings(self):
        """(SỬA LỖI) Tải cài đặt từ file JSON, nếu không có thì tạo mới."""
        file_existed = os.path.exists(CONFIG_FILE)
        try:
            if file_existed:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded_settings = json.load(f)

                # Hợp nhất với mặc định (để thêm các khóa mới nếu file config cũ)
                self.settings = self.defaults.copy()
                self.settings.update(loaded_settings)

                print(f"Đã tải cài đặt từ {CONFIG_FILE}")
            else:
                print(
                    f"Không tìm thấy {CONFIG_FILE}. Đang tạo file với cài đặt mặc định."
                )
                self.settings = self.defaults.copy()

        except Exception as e:
            print(
                f"Lỗi nghiêm trọng khi tải {CONFIG_FILE}. Sử dụng cài đặt mặc định. Lỗi: {e}"
            )
            self.settings = self.defaults.copy()

        # Cập nhật thuộc tính NGAY LẬP TỨC
        self._update_class_attributes()

        # Chỉ lưu file MỚI sau khi thuộc tính đã được tạo
        if not file_existed:
            self.save_settings(log=False)

    def save_settings(self, log=True):
        """Lưu cài đặt hiện tại vào file JSON. (ĐÃ THÊM AI_LEARNING_RATE, AI_OBJECTIVE, RECENT_FORM)"""
        try:
            settings_to_save = {
                "STATS_DAYS": self.STATS_DAYS,
                "GAN_DAYS": self.GAN_DAYS,
                "HIGH_WIN_THRESHOLD": self.HIGH_WIN_THRESHOLD,
                "AUTO_ADD_MIN_RATE": self.AUTO_ADD_MIN_RATE,
                "AUTO_PRUNE_MIN_RATE": self.AUTO_PRUNE_MIN_RATE,
                "K2N_RISK_START_THRESHOLD": self.K2N_RISK_START_THRESHOLD,
                "K2N_RISK_PENALTY_PER_FRAME": self.K2N_RISK_PENALTY_PER_FRAME,
                "AI_PROB_THRESHOLD": self.AI_PROB_THRESHOLD,
                "AI_MAX_DEPTH": self.AI_MAX_DEPTH,
                "AI_N_ESTIMATORS": self.AI_N_ESTIMATORS,
                "AI_LEARNING_RATE": self.AI_LEARNING_RATE,
                "AI_OBJECTIVE": self.AI_OBJECTIVE,
                "AI_SCORE_WEIGHT": self.AI_SCORE_WEIGHT,
                "RECENT_FORM_PERIODS": self.RECENT_FORM_PERIODS,
                "RECENT_FORM_BONUS_VERY_HIGH": self.RECENT_FORM_BONUS_VERY_HIGH,
                "RECENT_FORM_BONUS_HIGH": self.RECENT_FORM_BONUS_HIGH,
                "RECENT_FORM_BONUS_MED": self.RECENT_FORM_BONUS_MED,
                "RECENT_FORM_BONUS_LOW": self.RECENT_FORM_BONUS_LOW,
                "RECENT_FORM_MIN_VERY_HIGH": self.RECENT_FORM_MIN_VERY_HIGH,
                "RECENT_FORM_MIN_HIGH": self.RECENT_FORM_MIN_HIGH,
                "RECENT_FORM_MIN_MED": self.RECENT_FORM_MIN_MED,
                "RECENT_FORM_MIN_LOW": self.RECENT_FORM_MIN_LOW,
                "VOTE_SCORE_WEIGHT": self.VOTE_SCORE_WEIGHT,
                "HIGH_WIN_SCORE_BONUS": self.HIGH_WIN_SCORE_BONUS,
                "K2N_RISK_PROGRESSIVE": self.K2N_RISK_PROGRESSIVE,
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(settings_to_save, f, indent=4)

            if log:
                print(f"Đã lưu cài đặt vào {CONFIG_FILE}")
            return True, "Lưu thành công!"

        except Exception as e:
            print(f"Lỗi khi lưu {CONFIG_FILE}: {e}")
            print(traceback.format_exc())
            return False, f"Lỗi khi lưu file: {e}"

    def _update_class_attributes(self):
        """Cập nhật các thuộc tính của lớp từ dict đã tải. (ĐÃ THÊM AI_LEARNING_RATE, AI_OBJECTIVE, RECENT_FORM)"""
        self.STATS_DAYS = int(self.settings.get("STATS_DAYS", 7))
        self.GAN_DAYS = int(self.settings.get("GAN_DAYS", 15))
        self.HIGH_WIN_THRESHOLD = float(self.settings.get("HIGH_WIN_THRESHOLD", 47.0))
        self.AUTO_ADD_MIN_RATE = float(self.settings.get("AUTO_ADD_MIN_RATE", 50.0))
        self.AUTO_PRUNE_MIN_RATE = float(self.settings.get("AUTO_PRUNE_MIN_RATE", 40.0))
        self.K2N_RISK_START_THRESHOLD = int(
            self.settings.get("K2N_RISK_START_THRESHOLD", 4)
        )
        self.K2N_RISK_PENALTY_PER_FRAME = float(
            self.settings.get("K2N_RISK_PENALTY_PER_FRAME", 0.5)
        )
        self.AI_PROB_THRESHOLD = float(self.settings.get("AI_PROB_THRESHOLD", 45.0))
        self.AI_MAX_DEPTH = int(self.settings.get("AI_MAX_DEPTH", 15))
        self.AI_N_ESTIMATORS = int(self.settings.get("AI_N_ESTIMATORS", 100))
        self.AI_LEARNING_RATE = float(self.settings.get("AI_LEARNING_RATE", 0.1))  # MỚI
        self.AI_OBJECTIVE = str(
            self.settings.get("AI_OBJECTIVE", "binary:logistic")
        )  # MỚI
        self.AI_SCORE_WEIGHT = float(self.settings.get("AI_SCORE_WEIGHT", 0.3))
        self.RECENT_FORM_PERIODS = int(self.settings.get("RECENT_FORM_PERIODS", 10))
        self.RECENT_FORM_BONUS_VERY_HIGH = float(self.settings.get("RECENT_FORM_BONUS_VERY_HIGH", 4.0))
        self.RECENT_FORM_BONUS_HIGH = float(self.settings.get("RECENT_FORM_BONUS_HIGH", 3.0))
        self.RECENT_FORM_BONUS_MED = float(self.settings.get("RECENT_FORM_BONUS_MED", 2.0))
        self.RECENT_FORM_BONUS_LOW = float(self.settings.get("RECENT_FORM_BONUS_LOW", 1.0))
        self.RECENT_FORM_MIN_VERY_HIGH = int(self.settings.get("RECENT_FORM_MIN_VERY_HIGH", 9))
        self.RECENT_FORM_MIN_HIGH = int(self.settings.get("RECENT_FORM_MIN_HIGH", 7))
        self.RECENT_FORM_MIN_MED = int(self.settings.get("RECENT_FORM_MIN_MED", 5))
        self.RECENT_FORM_MIN_LOW = int(self.settings.get("RECENT_FORM_MIN_LOW", 3))
        self.VOTE_SCORE_WEIGHT = float(self.settings.get("VOTE_SCORE_WEIGHT", 0.5))
        self.HIGH_WIN_SCORE_BONUS = float(self.settings.get("HIGH_WIN_SCORE_BONUS", 2.5))
        self.K2N_RISK_PROGRESSIVE = bool(self.settings.get("K2N_RISK_PROGRESSIVE", True))

    def get_all_settings(self):
        """Trả về một dict của các cài đặt hiện tại (để UI sử dụng). (ĐÃ THÊM AI_LEARNING_RATE, AI_OBJECTIVE, RECENT_FORM)"""
        return {
            "STATS_DAYS": self.STATS_DAYS,
            "GAN_DAYS": self.GAN_DAYS,
            "HIGH_WIN_THRESHOLD": self.HIGH_WIN_THRESHOLD,
            "AUTO_ADD_MIN_RATE": self.AUTO_ADD_MIN_RATE,
            "AUTO_PRUNE_MIN_RATE": self.AUTO_PRUNE_MIN_RATE,
            "K2N_RISK_START_THRESHOLD": self.K2N_RISK_START_THRESHOLD,
            "K2N_RISK_PENALTY_PER_FRAME": self.K2N_RISK_PENALTY_PER_FRAME,
            "AI_PROB_THRESHOLD": self.AI_PROB_THRESHOLD,
            "AI_MAX_DEPTH": self.AI_MAX_DEPTH,
            "AI_N_ESTIMATORS": self.AI_N_ESTIMATORS,
            "AI_LEARNING_RATE": self.AI_LEARNING_RATE,  # MỚI
            "AI_OBJECTIVE": self.AI_OBJECTIVE,  # MỚI
            "AI_SCORE_WEIGHT": self.AI_SCORE_WEIGHT,
            "RECENT_FORM_PERIODS": self.RECENT_FORM_PERIODS,
            "RECENT_FORM_BONUS_VERY_HIGH": self.RECENT_FORM_BONUS_VERY_HIGH,
            "RECENT_FORM_BONUS_HIGH": self.RECENT_FORM_BONUS_HIGH,
            "RECENT_FORM_BONUS_MED": self.RECENT_FORM_BONUS_MED,
            "RECENT_FORM_BONUS_LOW": self.RECENT_FORM_BONUS_LOW,
            "RECENT_FORM_MIN_VERY_HIGH": self.RECENT_FORM_MIN_VERY_HIGH,
            "RECENT_FORM_MIN_HIGH": self.RECENT_FORM_MIN_HIGH,
            "RECENT_FORM_MIN_MED": self.RECENT_FORM_MIN_MED,
            "RECENT_FORM_MIN_LOW": self.RECENT_FORM_MIN_LOW,
            "VOTE_SCORE_WEIGHT": self.VOTE_SCORE_WEIGHT,
            "HIGH_WIN_SCORE_BONUS": self.HIGH_WIN_SCORE_BONUS,
            "K2N_RISK_PROGRESSIVE": self.K2N_RISK_PROGRESSIVE,
        }

    def update_setting(self, key, value):
        """Cập nhật một cài đặt và lưu ngay lập tức."""
        if hasattr(self, key):
            try:
                # Chuyển đổi kiểu dữ liệu
                default_val = self.defaults.get(key)
                if isinstance(default_val, int):
                    value = int(value)
                elif isinstance(default_val, float):
                    value = float(value)
                elif isinstance(default_val, str):  # Xử lý string cho AI_OBJECTIVE
                    value = str(value)

                setattr(self, key, value)
                self.settings[key] = value
                return self.save_settings()
            except ValueError:
                return False, f"Lỗi: '{value}' không phải là số hợp lệ cho {key}."
            except Exception as e:
                return False, f"Lỗi cập nhật {key}: {e}"
        else:
            return False, f"Lỗi: Khóa cài đặt '{key}' không tồn tại."


# --- Khởi tạo Singleton ---
try:
    SETTINGS = AppSettings()
    print("ConfigManager đã khởi tạo và tải cài đặt.")
except Exception as e:
    print(f"LỖI NGHIÊM TRỌNG khi khởi tạo ConfigManager: {e}")
    # Fallback nếu có lỗi nghiêm trọng
    SETTINGS = type(
        "obj",
        (object,),
        {
            "STATS_DAYS": 7,
            "GAN_DAYS": 15,
            "HIGH_WIN_THRESHOLD": 47.0,
            "AUTO_ADD_MIN_RATE": 50.0,
            "AUTO_PRUNE_MIN_RATE": 40.0,
            "K2N_RISK_START_THRESHOLD": 4,
            "K2N_RISK_PENALTY_PER_FRAME": 0.5,
            "AI_PROB_THRESHOLD": 45.0,
            "AI_MAX_DEPTH": 15,
            "AI_N_ESTIMATORS": 100,
            "AI_LEARNING_RATE": 0.1,
            "AI_OBJECTIVE": "binary:logistic",
            "AI_SCORE_WEIGHT": 0.2,
        },
    )
