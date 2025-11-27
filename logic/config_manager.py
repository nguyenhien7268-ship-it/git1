# Tên file: git1/logic/config_manager.py
import json
import os
import threading
import traceback

# Import nguồn chân lý (Source of Truth)
try:
    from logic.constants import DEFAULT_SETTINGS
except ImportError:
    print("Cảnh báo: Không thể import logic.constants. Sử dụng Fallback nội bộ.")
    # Fallback tối thiểu nếu mất file constants
    DEFAULT_SETTINGS = {
        "STATS_DAYS": 7,
        "GAN_DAYS": 15,
        "HIGH_WIN_THRESHOLD": 47.0,
        "AUTO_ADD_MIN_RATE": 50.0,
        "AUTO_PRUNE_MIN_RATE": 40.0,
        "K2N_RISK_START_THRESHOLD": 4,
        "K2N_RISK_PENALTY_PER_FRAME": 0.5,
        "AI_PROB_THRESHOLD": 45.0,
        "AI_MAX_DEPTH": 6,
        "AI_N_ESTIMATORS": 200,
        "AI_LEARNING_RATE": 0.05,
        "AI_OBJECTIVE": "binary:logistic",
        "AI_SCORE_WEIGHT": 0.2,
        "RECENT_FORM_PERIODS": 10,
        "RECENT_FORM_BONUS_HIGH": 3.0,
        "RECENT_FORM_BONUS_MED": 2.0,
        "RECENT_FORM_BONUS_LOW": 1.0,
        "RECENT_FORM_MIN_HIGH": 8,
        "RECENT_FORM_MIN_MED": 6,
        "RECENT_FORM_MIN_LOW": 5,
        "DATA_LIMIT_DASHBOARD": 2000,
        "DATA_LIMIT_RESEARCH": 0
    }

CONFIG_FILE = "config.json"

class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.config_file = CONFIG_FILE
        # 1. Khởi tạo bằng giá trị mặc định chuẩn (từ constants.py)
        self.settings = DEFAULT_SETTINGS.copy()
        
        # 2. Tải giá trị người dùng đã lưu (ghi đè lên mặc định)
        self.load_settings()
        
        self._initialized = True

    def load_settings(self):
        """Tải cài đặt từ file JSON, merge với mặc định."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_settings = json.load(f)
                    
                # Merge settings: Chỉ ghi đè những key có trong user_settings
                for key, value in user_settings.items():
                    self.settings[key] = value
                
                print(f"Đã tải cài đặt từ {self.config_file}")
            except Exception as e:
                print(f"Lỗi tải config: {e}. Sử dụng mặc định.")
        else:
            print(f"Chưa có file {self.config_file}, sẽ tạo mới khi lưu.")
        
        # Cập nhật attribute access (để dùng SETTINGS.KEY)
        self._update_attributes()

    def _update_attributes(self):
        """Gán các giá trị trong dict settings thành thuộc tính của object."""
        for key, value in self.settings.items():
            setattr(self, key, value)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def get_all_settings(self):
        return self.settings.copy()

    def update_setting(self, key, value):
        """Cập nhật một cài đặt (chưa lưu file)."""
        try:
            # Validate kiểu dữ liệu nếu key có trong DEFAULT
            if key in DEFAULT_SETTINGS:
                default_val = DEFAULT_SETTINGS[key]
                default_type = type(default_val)
                
                if type(value) != default_type:
                    try:
                        if default_type == int: value = int(value)
                        elif default_type == float: value = float(value)
                        elif default_type == bool: value = bool(value)
                        elif default_type == str: value = str(value)
                    except:
                        pass 

            self.settings[key] = value
            setattr(self, key, value)
            
            return self.save_settings()
        except Exception as e:
            return False, str(e)

    def save_settings(self):
        """Ghi cài đặt hiện tại xuống file JSON."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            return True, "Đã lưu cài đặt."
        except Exception as e:
            print(traceback.format_exc())
            return False, f"Lỗi ghi file: {e}"

    def reset_to_defaults(self):
        """Khôi phục về mặc định ban đầu."""
        self.settings = DEFAULT_SETTINGS.copy()
        self._update_attributes()
        self.save_settings()

# --- Khởi tạo Singleton (CÓ FALLBACK AN TOÀN) ---
try:
    SETTINGS = ConfigManager()
    print("ConfigManager (V7.8) đã khởi tạo thành công.")
except Exception as e:
    print(f"LỖI NGHIÊM TRỌNG khi khởi tạo ConfigManager: {e}")
    
    # Fallback thông minh: Tự động tạo object từ DEFAULT_SETTINGS
    # Giúp app không bị crash và vẫn có đủ tham số mới nhất
    class FallbackSettings:
        def __init__(self):
            self.settings = DEFAULT_SETTINGS.copy()
            for k, v in self.settings.items():
                setattr(self, k, v)
        
        def get_all_settings(self):
            return self.settings
            
        def update_setting(self, key, value):
            return False, "Chế độ Fallback (Không thể lưu)"
            
        def save_settings(self):
            return False, "Chế độ Fallback (Lỗi hệ thống)"
            
        def get(self, key, default=None):
            return self.settings.get(key, default)

    SETTINGS = FallbackSettings()
    print("-> Đã kích hoạt chế độ Fallback Settings (Sử dụng Default).")