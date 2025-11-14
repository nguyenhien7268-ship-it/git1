import sqlite3
import re
from . import db_manager # Sử dụng import relative
from datetime import datetime

class DataService:
    """
    (MỚI - GĐ 1) Lớp Dịch vụ Dữ liệu.
    Nhiệm vụ: Tải toàn bộ dữ liệu từ DB lên bộ nhớ (cache) khi khởi tạo
    và cung cấp các phương thức truy cập nhanh vào dữ liệu này.
    Tất cả các mô-đun khác (Backtester, Bridges, Analytics)
    PHẢI sử dụng lớp này thay vì gọi db_manager trực tiếp.
    """
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Triển khai mẫu Singleton để đảm bảo chỉ có MỘT
        # thực thể của DataService (và chỉ tải dữ liệu một lần)
        if not cls._instance:
            cls._instance = super(DataService, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_path=None):
        # Ngăn chặn việc khởi tạo lại
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        print("Đang khởi tạo DataService...")
        self.db_path = db_path if db_path else db_manager.DB_NAME
        
        # _raw_data: List các dict, giữ toàn bộ lịch sử (sắp xếp TĂNG DẦN theo MaSoKy)
        self._raw_data = []
        
        # _data_by_ky: Dict để truy cập nhanh bằng MaSoKy
        self._data_by_ky = {}
        
        # _ky_list: List các MaSoKy (sắp xếp TĂNG DẦN)
        self._ky_list = []
        
        # _ky_to_date: Dict map MaSoKy sang NgayThang (YYYY-MM-DD)
        self._ky_to_date = {}

        self.load_data()
        self._initialized = True
        print(f"DataService đã khởi tạo. Tải {len(self._raw_data)} kỳ quay.")

    def load_data(self):
        """
Tải dữ liệu từ DB vào bộ nhớ."""
        try:
            # 1. Tải dữ liệu DuLieu_AI
            # get_all_data_ai_results() đã trả về list[dict] và sắp xếp ASC
            self._raw_data = db_manager.get_all_data_ai_results(self.db_path)
            
            if not self._raw_data:
                print("Cảnh báo DataService: Không tải được dữ liệu DuLieu_AI.")
                return

            # 2. Xử lý và lập chỉ mục (index) dữ liệu
            for row_dict in self._raw_data:
                ma_so_ky = row_dict.get('MaSoKy')
                if ma_so_ky:
                    self._data_by_ky[ma_so_ky] = row_dict
                    self._ky_list.append(ma_so_ky)
            
            # 3. Tải dữ liệu KyQuay (để lấy NgayThang)
            # get_all_kys_from_db() trả về sắp xếp DESC, chúng ta cần xử lý
            ky_quay_rows = db_manager.get_all_kys_from_db(self.db_path)
            temp_date_map = {}
            for ky_row in ky_quay_rows:
                # ky_row[0] = MaSoKy, ky_row[1] = NgayThang (DD/MM/YYYY)
                ma_so_ky = ky_row[0]
                ngay_thang_str = ky_row[1]
                
                # Chuẩn hóa ngày tháng về YYYY-MM-DD
                try:
                    date_obj = datetime.strptime(ngay_thang_str, '%d/%m/%Y')
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                    temp_date_map[ma_so_ky] = formatted_date
                except ValueError:
                    temp_date_map[ma_so_ky] = None # Nếu định dạng sai

            # 4. Gán ngày tháng vào _ky_to_date theo thứ tự của _ky_list
            for ky in self._ky_list:
                self._ky_to_date[ky] = temp_date_map.get(ky)

        except Exception as e:
            print(f"Lỗi nghiêm trọng khi tải dữ liệu trong DataService: {e}")
            self._raw_data = []
            self._data_by_ky = {}
            self._ky_list = []

    def reload_data(self):
        """Tải lại dữ liệu từ DB. Dùng khi có cập nhật mới."""
        print("Đang tải lại dữ liệu DataService...")
        # Xóa cache cũ
        self._raw_data = []
        self._data_by_ky = {}
        self._ky_list = []
        self._ky_to_date = {}
        # Tải lại
        self.load_data()
        print(f"Đã tải lại. Tổng cộng {len(self._raw_data)} kỳ quay.")

    def get_full_history(self):
        """
        Trả về toàn bộ lịch sử (dạng list các dict), 
        sắp xếp TĂNG DẦN theo MaSoKy.
        """
        return self._raw_data

    def get_results_by_ky(self, ma_so_ky):
        """
        Trả về kết quả của 1 MaSoKy (dạng dict) từ bộ nhớ cache.
        Nhanh hơn rất nhiều so với truy vấn DB.
        """
        return self._data_by_ky.get(ma_so_ky)

    def get_ky_list(self, sort_order='asc'):
        """
        Trả về list các MaSoKy.
        sort_order: 'asc' (tăng dần - mặc định) hoặc 'desc' (giảm dần).
        """
        if sort_order == 'desc':
            return self.get_ky_list_desc()
        return self._ky_list

    def get_ky_list_asc(self):
        """Trả về list MaSoKy, sắp xếp TĂNG DẦN (theo thời gian)."""
        return self._ky_list
        
    def get_ky_list_desc(self):
        """Trả về list MaSoKy, sắp xếp GIẢM DẦN (mới nhất trước)."""
        # Trả về một bản sao đã đảo ngược
        return self._ky_list[::-1]

    def get_date_from_ky(self, ma_so_ky):
        """Trả về ngày tháng (YYYY-MM-DD) của một MaSoKy."""
        return self._ky_to_date.get(ma_so_ky)

    def get_latest_ky(self):
        """Trả về MaSoKy mới nhất."""
        if self._ky_list:
            return self._ky_list[-1]
        return None

    def get_data_by_date_range(self, start_date_str, end_date_str):
        """
        Lấy dữ liệu trong một khoảng ngày (YYYY-MM-DD).
        Bao gồm cả ngày bắt đầu và ngày kết thúc.
        """
        try:
            results = []
            for ky in self._ky_list: # Duyệt theo thứ tự tăng dần
                ky_date = self._ky_to_date.get(ky)
                if ky_date and start_date_str <= ky_date <= end_date_str:
                    results.append(self._data_by_ky[ky])
            return results
        except Exception as e:
            print(f"Lỗi get_data_by_date_range: {e}")
            return []

    def get_previous_ky(self, ma_so_ky):
        """Lấy kỳ quay TRƯỚC của một kỳ đã cho."""
        try:
            # Sử dụng _data_by_ky để tìm index nhanh hơn (nếu list lớn)
            # Nhưng ở đây _ky_list đã được sắp xếp, dùng index() là đủ nhanh
            current_index = self._ky_list.index(ma_so_ky)
            if current_index > 0:
                return self._ky_list[current_index - 1]
        except ValueError:
            print(f"Cảnh báo: Không tìm thấy ky {ma_so_ky} trong get_previous_ky")
        except Exception as e:
            print(f"Lỗi get_previous_ky: {e}")
        return None

# --- Khởi tạo một thực thể (instance) toàn cục ---
# Các file khác chỉ cần `from .data_service import global_data_service`
# để truy cập mà không cần khởi tạo lại.

try:
    global_data_service = DataService()
except Exception as e:
    print(f"Lỗi nghiêm trọng khi khởi tạo global_data_service: {e}")
    global_data_service = None

# Hàm trợ giúp để tải lại dữ liệu từ bên ngoài
def reload_global_data():
    if global_data_service:
        global_data_service.reload_data()
        return True
    return False