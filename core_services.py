# Tên file: du-an-backup/core_services.py
#
# (NỘI DUNG TỆP MỚI)
#
import threading
import traceback
import tkinter as tk

class Logger:
    """Quản lý việc log ra UI an toàn từ nhiều luồng."""
    def __init__(self, text_widget, root):
        self.widget = text_widget
        self.root = root

    def _safe_log(self, message):
        """Hàm cập nhật output an toàn (chỉ chạy trên luồng chính)."""
        try:
            self.widget.config(state=tk.NORMAL)
            self.widget.insert(tk.END, message + "\n")
            self.widget.see(tk.END)
            self.widget.config(state=tk.DISABLED)
            self.root.update_idletasks()
        except Exception:
            # Bỏ qua nếu UI đã bị hủy
            pass 

    def log(self, message):
        """Ghi log. Tự động kiểm tra luồng."""
        if threading.current_thread() is threading.main_thread():
            self._safe_log(message)
        else:
            # Nếu từ luồng khác, gọi an toàn qua root.after()
            self.root.after(0, self._safe_log, message)

class TaskManager:
    """Quản lý việc chạy tác vụ đa luồng và Bật/Tắt nút."""
    def __init__(self, logger, all_buttons_list, root):
        self.logger = logger
        self.all_buttons = all_buttons_list
        self.root = root
        self.optimizer_apply_button = None # Nút đặc biệt

    def set_buttons_state(self, state):
        """Bật/Tắt tất cả các nút."""
        for button in self.all_buttons:
            # (LOGIC TỪ UI_MAIN_WINDOW)
            # Đảm bảo nút "Áp dụng" chỉ bật khi có kết quả
            if button == self.optimizer_apply_button and state == tk.NORMAL:
                # Nút "Áp dụng" sẽ được bật riêng khi có kết quả
                continue
            
            button.config(state=state)
        self.root.update_idletasks()

    def run_task(self, target_function, *args):
        """
        Hàm bao bọc (wrapper) chung để chạy bất kỳ tác vụ nào trong một luồng riêng.
        Điều này ngăn chặn UI bị "Đơ" (Freeze).
        """
        self.set_buttons_state(tk.DISABLED)

        def _thread_wrapper():
            """Hàm này sẽ chạy trong luồng mới."""
            try:
                target_function(*args)
            except Exception as e:
                self.logger.log(f"LỖI LUỒNG: {e}")
                self.logger.log(traceback.format_exc())
            finally:
                self.root.after(0, self.set_buttons_state, tk.NORMAL)

        task_thread = threading.Thread(target=_thread_wrapper, daemon=True)
        task_thread.start()