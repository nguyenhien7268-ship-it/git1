import json
import os
import traceback

CONFIG_FILE = 'config.json'

class AppSettings:
    """
    (MỚI GĐ 8) Lớp Singleton để giữ cài đặt toàn cục.
    Lưu trữ tất cả các tham số có thể định cấu hình của hệ thống.
    """
    def __init__(self):
        # Giá trị mặc định
        self.defaults = {
            "STATS_DAYS": 7,
            "GAN_DAYS": 15,
            "HIGH_WIN_THRESHOLD": 47.0,
            "AUTO_ADD_MIN_RATE": 50.0,
            "AUTO_PRUNE_MIN_RATE": 40.0,
            "K2N_RISK_START_THRESHOLD": 4,
            "K2N_RISK_PENALTY_PER_FRAME": 0.5
        }
        
        # Tải cài đặt
        self.load_settings()

    def load_settings(self):
        """(SỬA LỖI) Tải cài đặt từ file JSON, nếu không có thì tạo mới."""
        file_existed = os.path.exists(CONFIG_FILE) # (SỬA LỖI)
        try:
            if file_existed:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Hợp nhất với mặc định (để thêm các khóa mới nếu file config cũ)
                self.settings = self.defaults.copy()
                self.settings.update(loaded_settings)
                
                print(f"Đã tải cài đặt từ {CONFIG_FILE}")
            else:
                print(f"Không tìm thấy {CONFIG_FILE}. Đang tạo file với cài đặt mặc định.")
                self.settings = self.defaults.copy()
                # (SỬA LỖI) Không save ở đây
                
        except Exception as e:
            print(f"Lỗi nghiêm trọng khi tải {CONFIG_FILE}. Sử dụng cài đặt mặc định. Lỗi: {e}")
            self.settings = self.defaults.copy()
            
        # (SỬA LỖI) Cập nhật thuộc tính NGAY LẬP TỨC
        self._update_class_attributes()
        
        # (SỬA LỖI) Chỉ lưu file MỚI sau khi thuộc tính đã được tạo
        if not file_existed:
            self.save_settings(log=False)

    def save_settings(self, log=True):
        """Lưu cài đặt hiện tại vào file JSON."""
        try:
            # (SỬA LỖI) Đọc từ các thuộc tính đã được tạo
            settings_to_save = {
                "STATS_DAYS": self.STATS_DAYS,
                "GAN_DAYS": self.GAN_DAYS,
                "HIGH_WIN_THRESHOLD": self.HIGH_WIN_THRESHOLD,
                "AUTO_ADD_MIN_RATE": self.AUTO_ADD_MIN_RATE,
                "AUTO_PRUNE_MIN_RATE": self.AUTO_PRUNE_MIN_RATE,
                "K2N_RISK_START_THRESHOLD": self.K2N_RISK_START_THRESHOLD,
                "K2N_RISK_PENALTY_PER_FRAME": self.K2N_RISK_PENALTY_PER_FRAME
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings_to_save, f, indent=4)
            
            if log:
                print(f"Đã lưu cài đặt vào {CONFIG_FILE}")
            return True, "Lưu thành công!"
            
        except Exception as e:
            print(f"Lỗi khi lưu {CONFIG_FILE}: {e}")
            print(traceback.format_exc())
            return False, f"Lỗi khi lưu file: {e}"

    def _update_class_attributes(self):
        """Cập nhật các thuộc tính của lớp từ dict đã tải."""
        self.STATS_DAYS = int(self.settings.get("STATS_DAYS", 7))
        self.GAN_DAYS = int(self.settings.get("GAN_DAYS", 15))
        self.HIGH_WIN_THRESHOLD = float(self.settings.get("HIGH_WIN_THRESHOLD", 47.0))
        self.AUTO_ADD_MIN_RATE = float(self.settings.get("AUTO_ADD_MIN_RATE", 50.0))
        self.AUTO_PRUNE_MIN_RATE = float(self.settings.get("AUTO_PRUNE_MIN_RATE", 40.0))
        self.K2N_RISK_START_THRESHOLD = int(self.settings.get("K2N_RISK_START_THRESHOLD", 4))
        self.K2N_RISK_PENALTY_PER_FRAME = float(self.settings.get("K2N_RISK_PENALTY_PER_FRAME", 0.5))

    def get_all_settings(self):
        """Trả về một dict của các cài đặt hiện tại (để UI sử dụng)."""
        return {
            "STATS_DAYS": self.STATS_DAYS,
            "GAN_DAYS": self.GAN_DAYS,
            "HIGH_WIN_THRESHOLD": self.HIGH_WIN_THRESHOLD,
            "AUTO_ADD_MIN_RATE": self.AUTO_ADD_MIN_RATE,
            "AUTO_PRUNE_MIN_RATE": self.AUTO_PRUNE_MIN_RATE,
            "K2N_RISK_START_THRESHOLD": self.K2N_RISK_START_THRESHOLD,
            "K2N_RISK_PENALTY_PER_FRAME": self.K2N_RISK_PENALTY_PER_FRAME
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
    SETTINGS = type('obj', (object,), {
        'STATS_DAYS': 7,
        'GAN_DAYS': 15,
        'HIGH_WIN_THRESHOLD': 47.0,
        'AUTO_ADD_MIN_RATE': 50.0,
        'AUTO_PRUNE_MIN_RATE': 40.0,
        'K2N_RISK_START_THRESHOLD': 4,
        'K2N_RISK_PENALTY_PER_FRAME': 0.5
    })