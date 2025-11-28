# Tên file: services/data_service.py
# Service layer: Logic tải và xử lý dữ liệu xổ số

import os
import traceback

class DataService:
    """Service xử lý dữ liệu xổ số"""
    
    def __init__(self, db_name, logger=None):
        self.db_name = db_name
        self.logger = logger
    
    def _log(self, message):
        """Helper để log messages"""
        if self.logger:
            self.logger.log(message)
    
    def load_data(self):
        """
        Tải dữ liệu A:I từ database.
        
        Returns:
            list hoặc None: Dữ liệu A:I hoặc None nếu lỗi
        """
        try:
            from lottery_service import load_data_ai_from_db
            rows_of_lists, message = load_data_ai_from_db(self.db_name)
            self._log(message)
            return rows_of_lists
        except ImportError:
            try:
                from logic.data_repository import load_data_ai_from_db
                rows_of_lists, message = load_data_ai_from_db(self.db_name)
                self._log(message)
                return rows_of_lists
            except ImportError as e:
                self._log(f"Lỗi: Không thể import load_data_ai_from_db: {e}")
                return None
    
    def import_data_from_file(self, input_file, callback_on_success=None):
        """
        Import dữ liệu từ file, xóa database cũ và chèn dữ liệu mới.
        
        Args:
            input_file: Đường dẫn file input
            callback_on_success: Hàm callback khi thành công
        
        Returns:
            tuple: (success: bool, message: str)
        """
        conn = None
        try:
            with open(input_file, "r", encoding="utf-8-sig") as f:
                raw_data = f.read()
            self._log(f"Đã đọc tệp tin '{input_file}' thành công.")

            if os.path.exists(self.db_name):
                os.remove(self.db_name)
                self._log(f"Đã xóa database cũ: {self.db_name}")

            from lottery_service import setup_database, parse_and_insert_data
            conn, cursor = setup_database()
            total_records_ai = parse_and_insert_data(raw_data, conn, cursor)

            if total_records_ai == 0:
                return False, "Không thể phân tích dữ liệu. File có thể không đúng định dạng."
            else:
                self._log("Phân tích và chèn dữ liệu hoàn tất.")
                self._log(f"- Đã chèn {total_records_ai} hàng A:I (backtest).")
                self._log("- Đã xóa mọi Cầu Đã Lưu (do nạp lại).")
                self._log(">>> Sẵn sàng cho Chức Năng Soi Cầu.")
                if callback_on_success:
                    callback_on_success()
                return True, f"Đã chèn {total_records_ai} hàng A:I"

        except Exception as e:
            error_msg = f"LỖI trong import data: {e}"
            self._log(error_msg)
            self._log(traceback.format_exc())
            return False, error_msg
        finally:
            if conn:
                conn.close()
                self._log("Đã đóng kết nối database.")
    
    def append_data_from_file(self, input_file, callback_on_success=None):
        """
        Thêm dữ liệu mới từ file vào database hiện có.
        
        Args:
            input_file: Đường dẫn file input
            callback_on_success: Hàm callback khi thành công
        
        Returns:
            tuple: (success: bool, message: str)
        """
        conn = None
        try:
            with open(input_file, "r", encoding="utf-8-sig") as f:
                raw_data = f.read()
            self._log(f"Đã đọc tệp tin '{input_file}' thành công.")

            from lottery_service import setup_database, parse_and_APPEND_data
            conn, cursor = setup_database()
            total_keys_added = parse_and_APPEND_data(raw_data, conn, cursor)

            if total_keys_added == 0:
                return False, "Không có kỳ nào được thêm (có thể do trùng lặp hoặc file rỗng)."
            else:
                self._log("Thêm dữ liệu hoàn tất.")
                self._log(f"- Đã thêm {total_keys_added} kỳ mới vào DB.")
                self._log(">>> Sẵn sàng cho Chức Năng Soi Cầu.")
                if callback_on_success:
                    callback_on_success()
                return True, f"Đã thêm {total_keys_added} kỳ mới"

        except Exception as e:
            error_msg = f"LỖI trong append data: {e}"
            self._log(error_msg)
            self._log(traceback.format_exc())
            return False, error_msg
        finally:
            if conn:
                conn.close()
                self._log("Đã đóng kết nối database.")
    
    def update_from_text(self, raw_data, callback_on_success=None):
        """
        Cập nhật dữ liệu từ text input.
        
        Args:
            raw_data: Dữ liệu dạng text
            callback_on_success: Hàm callback khi thành công
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            from logic.data_parser import run_and_update_from_text
            success, message = run_and_update_from_text(raw_data)
            self._log(message)
            
            if success and callback_on_success:
                callback_on_success()
            
            return success, message
        except Exception as e:
            error_msg = f"LỖI khi cập nhật từ text: {e}"
            self._log(error_msg)
            self._log(traceback.format_exc())
            return False, error_msg
