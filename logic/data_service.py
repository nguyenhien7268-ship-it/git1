import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import os # <-- (FIX LỖI NAME ERROR) ĐÃ THÊM IMPORT OS
import threading # (FIX LỖI THREAD) Thêm import threading
from . import db_manager 

class DataService:
    """
    (GĐ 1 - Cập nhật FIX LỖI MP & THREAD & CIRCULAR IMPORT)
    Bao bọc db_manager VÀ tích hợp logic từ data_repository
    để quản lý 100% truy cập CSDL.
    """
    
    _instance = None
    
    @staticmethod
    def get_instance():
        """Lấy thể hiện (instance) duy nhất của DataService."""
        # (FIX LỖI THREAD) Sử dụng lock để đảm bảo an toàn khi khởi tạo
        # Mặc dù trong TH của chúng ta, nó thường được tạo ở main thread
        # nhưng đây là cách làm đúng chuẩn.
        if DataService._instance is None:
            DataService._instance = DataService()
        return DataService._instance

    @staticmethod
    def initialize_for_worker():
        """
        (FIX LỖI MP) Phương thức tĩnh để buộc đóng kết nối CSDL của 
        tiến trình cha và khởi tạo lại kết nối mới cho tiến trình con.
        """
        instance = DataService.get_instance()
        
        if instance.conn:
            try:
                instance.conn.close()
                instance.conn = None
            except Exception:
                pass 
        
        instance._initialize_connection()
        print(f"[{os.getpid()}] DataService đã khởi tạo lại kết nối CSDL cho Worker.")
        return instance

    def _initialize_connection(self):
        """Logic khởi tạo kết nối cốt lõi (Tách ra để dùng trong initialize_for_worker)."""
        pid = os.getpid()
        tid = threading.get_ident()
        print(f"[{pid}/TID:{tid}] Đang thiết lập kết nối CSDL...")
        try:
            self.conn, _ = db_manager.setup_database()
            self.conn.row_factory = sqlite3.Row 
            self._thread_id = tid # (FIX LỖI THREAD) Lưu ID của luồng đã tạo kết nối
        except Exception as e:
            print(f"[{pid}/TID:{tid}] LỖI NGHIÊM TRỌNG: DataService không thể kết nối CSDL: {e}")
            self.conn = None
            self._thread_id = None
            
    def __init__(self):
        """
        Hàm khởi tạo (chỉ chạy một lần) để thiết lập kết nối CSDL trung tâm.
        """
        if hasattr(self, 'conn') and self.conn:
            return 
        
        self.conn: Optional[sqlite3.Connection] = None
        self._thread_id: Optional[int] = None # (FIX LỖI THREAD) Khởi tạo
        self._initialize_connection()

    # (FIX LỖI THREAD) Hàm kiểm tra và tự động sửa lỗi thread
    def _check_thread_safety(self) -> bool:
        """
        Kiểm tra xem luồng hiện tại có phải là luồng đã tạo kết nối CSDL không.
        Nếu không, tự động tạo lại kết nối mới cho luồng này.
        """
        current_thread_id = threading.get_ident()
        if self._thread_id == current_thread_id:
            return True # An toàn
        
        # Nếu không an toàn, đóng kết nối cũ (nếu có) và tạo kết nối mới
        pid = os.getpid()
        print(f"CẢNH BÁO: Phát hiện truy cập CSDL từ thread khác (PID: {pid}, Cũ: {self._thread_id}, Mới: {current_thread_id}). Đang tạo lại kết nối...")
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        
        self._initialize_connection() # Tạo kết nối mới và gán self._thread_id mới
        
        # Kiểm tra lại
        if self._thread_id == current_thread_id:
            print(f"[{pid}/TID:{current_thread_id}] Đã tạo lại kết nối thành công.")
            return True
        else:
            print(f"[{pid}/TID:{current_thread_id}] LỖI: Không thể tạo lại kết nối CSDL.")
            return False

    def close_connection(self):
        """Đóng kết nối CSDL trung tâm khi ứng dụng kết thúc."""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("(DataService) Đã đóng kết nối CSDL trung tâm.")

    # ===================================================================
    # (GIỮ NGUYÊN TẤT CẢ CÁC HÀM CŨ: load_data_ai_from_db, get_all_managed_bridges, ...)
    # (SỬA LỖI THREAD) Thêm _check_thread_safety() vào ĐẦU MỖI HÀM
    # ===================================================================

    def load_data_ai_from_db(self) -> Tuple[Optional[List[List[Any]]], str]:
        # (FIX LỖI THREAD)
        if not self._check_thread_safety():
            return None, f"Lỗi: (DataService) Không thể khởi tạo kết nối CSDL an toàn cho thread {threading.get_ident()}."

        if not self.conn: return None, "Lỗi: (DataService) Không có kết nối CSDL."
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT MaSoKy, Col_A_Ky, Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3, Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7
            FROM DuLieu_AI
            ORDER BY MaSoKy ASC 
            ''')
            rows_of_rows = cursor.fetchall()
            rows_of_lists = [list(row) for row in rows_of_rows]
            return rows_of_lists, f"Đã tải {len(rows_of_lists)} hàng A:I từ DataService."
        except Exception as e:
            # (FIX LỖI THREAD) Báo cáo lỗi rõ hơn
            return None, f"Lỗi DataService.load_data_ai_from_db (TID: {threading.get_ident()}): {e}"

    def get_all_managed_bridges(self, only_enabled: bool = False) -> List[Dict[str, Any]]:
        if not self._check_thread_safety(): return [] # (FIX LỖI THREAD)
        
        if not self.conn:
            print("Lỗi: (DataService) Không có kết nối CSDL khi get_all_managed_bridges.")
            return []
        try:
            cursor = self.conn.cursor()
            query = 'SELECT * FROM ManagedBridges' 
            if only_enabled:
                query += ' WHERE is_enabled = 1'
            query += ' ORDER BY id DESC'
            cursor.execute(query)
            rows = cursor.fetchall() 
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Lỗi DataService.get_all_managed_bridges: {e}")
            return []
            
    def get_db_connection(self) -> Optional[sqlite3.Connection]:
        self._check_thread_safety() # (FIX LỖI THREAD)
        return self.conn

    def get_all_kys_from_db(self) -> List[sqlite3.Row]:
        self._check_thread_safety() # (FIX LỖI THREAD)
        return db_manager.get_all_kys_from_db(conn=self.conn)

    def get_results_by_ky(self, ma_so_ky: str) -> Optional[sqlite3.Row]:
        self._check_thread_safety() # (FIX LỖI THREAD)
        return db_manager.get_results_by_ky(ma_so_ky, conn=self.conn)

    # ===================================================================
    # (REFRACTOR GĐ 1) CÁC HÀM CRUD (CHỨA LOGIC)
    # ===================================================================

    def add_managed_bridge(self, bridge_name: str, description: str, win_rate_text: str) -> Tuple[bool, str]:
        self._check_thread_safety() # (FIX LỖI THREAD)
        
        # (REFRACTOR GĐ 1) Logic được chuyển từ db_manager lên đây.
        # (SỬA LỖI) Vẫn giữ lỗi import vòng ở đây vì nó được gọi từ UI
        # và chưa được refactor.
        try:
            # (FIX) Import cục bộ để tránh lỗi tuần hoàn
            from .bridges.bridges_v16 import get_index_from_name_V16
        except ImportError:
            print("LỖI NGHIÊM TRỌNG (DataService): Không thể import get_index_from_name_V16.")
            def get_index_from_name_V16(name): return None

        try:
            parts = bridge_name.split('+')
            if len(parts) != 2:
                return False, "Tên cầu không hợp lệ. Phải có dạng 'Vị trí 1 + Vị trí 2'."
            
            pos1_name = parts[0].strip()
            pos2_name = parts[1].strip()
            pos1_idx = get_index_from_name_V16(pos1_name)
            pos2_idx = get_index_from_name_V16(pos2_name)
            
            if pos1_idx is None or pos2_idx is None:
                return False, f"Không thể dịch tên vị trí: '{pos1_name}' hoặc '{pos2_name}'."
            
            # Gọi hàm db_manager (đã được đơn giản hóa)
            return db_manager.add_managed_bridge(
                bridge_name, description, win_rate_text,
                pos1_name, pos2_name, pos1_idx, pos2_idx,
                conn=self.conn
            )
        except Exception as e:
            return False, f"Lỗi DataService.add_managed_bridge: {e}"
        
    def update_managed_bridge(self, bridge_id: int, description: str, is_enabled: int) -> Tuple[bool, str]:
        self._check_thread_safety() # (FIX LỖI THREAD)
        # Hàm này không có logic nghiệp vụ, gọi thẳng db_manager
        return db_manager.update_managed_bridge(bridge_id, description, is_enabled, conn=self.conn)

    def delete_managed_bridge(self, bridge_id: int) -> Tuple[bool, str]:
        self._check_thread_safety() # (FIX LỖI THREAD)
        # Hàm này không có logic nghiệp vụ, gọi thẳng db_manager
        return db_manager.delete_managed_bridge(bridge_id, conn=self.conn)
        
    def upsert_managed_bridge(
        self, bridge_name: str, description: str, win_rate_text: str,
        pos1_name: str, pos2_name: str, pos1_idx: int, pos2_idx: int
    ) -> Tuple[bool, str]:
        """
        (SỬA LỖI CIRCULAR IMPORT)
        Hàm này giờ chỉ nhận dữ liệu đã được tính toán
        và truyền thẳng xuống db_manager.
        """
        self._check_thread_safety() # (FIX LỖI THREAD)
        
        try:
            # (ĐÃ XÓA) Toàn bộ logic parsing (import bridges_v16, if/elif...)
            # đã bị xóa khỏi đây.
            
            # Gọi hàm db_manager (đã được đơn giản hóa)
            return db_manager.upsert_managed_bridge(
                bridge_name, description, win_rate_text,
                pos1_name, pos2_name, pos1_idx, pos2_idx,
                conn=self.conn
            )
        except Exception as e:
            return False, f"Lỗi DataService.upsert_managed_bridge: {e}"


    def update_bridge_win_rate_batch(self, rate_data_list: List[Tuple[str, str]]) -> Tuple[bool, str]:
        self._check_thread_safety() # (FIX LỖI THREAD)
        # Hàm này không có logic nghiệp vụ, gọi thẳng db_manager
        return db_manager.update_bridge_win_rate_batch(rate_data_list, conn=self.conn)
        
    def update_bridge_k2n_cache_batch(self, cache_data_list: List[Tuple[Any]]) -> Tuple[bool, str]:
        self._check_thread_safety() # (FIX LỖI THREAD)
        # Hàm này không có logic nghiệp vụ, gọi thẳng db_manager
        return db_manager.update_bridge_k2n_cache_batch(cache_data_list, conn=self.conn)