# Tên file: code2/ui/task_manager.py
#
# (NỘI DUNG CHO FILE MỚI)
#
import threading
import traceback

class TaskManager:
    """
    Quản lý việc chạy các tác vụ nặng (như backtest, nạp file) 
    trong các luồng riêng biệt (Threads) để không làm treo giao diện (UI).
    """
    def __init__(self, main_app):
        # main_app là instance của MainWindow, dùng để gọi hàm log
        self.main_app = main_app

    def _task_wrapper(self, target_func, *args):
        """
        Hàm bọc (wrapper) để chạy trong luồng.
        Nó gọi hàm mục tiêu và bắt (catch) bất kỳ lỗi nào.
        """
        try:
            # Thực thi hàm logic nặng (ví dụ: controller.task_run_backtest)
            target_func(*args)
        except Exception as e:
            # Nếu có lỗi, ghi nó vào log chính của UI
            error_msg = f"LỖI LUỒNG TÁC VỤ: {e}\n{traceback.format_exc()}"
            self.main_app.log(error_msg)

    def run_task(self, target_func, *args):
        """
        Khởi chạy một tác vụ mới trong một luồng riêng.
        Các luồng được set là 'daemon' để chúng tự động tắt 
        khi cửa sổ chính đóng lại.
        """
        try:
            # Tạo một luồng mới
            task_thread = threading.Thread(
                target=self._task_wrapper, 
                args=(target_func,) + args
            )
            
            # Đặt là daemon = True
            # Điều này đảm bảo khi ta đóng cửa sổ chính (root.destroy()), 
            # luồng này sẽ tự động bị hủy mà không cần can thiệp.
            task_thread.daemon = True 
            
            # Bắt đầu luồng
            task_thread.start()
            
        except Exception as e:
            self.main_app.log(f"Lỗi khi khởi tạo luồng: {e}")

    def shutdown(self):
        """
        Xử lý tắt.
        Vì các luồng là daemon, chúng ta không cần làm gì đặc biệt ở đây.
        Chúng sẽ tự động tắt khi main_app gọi root.destroy().
        """
        self.main_app.log("TaskManager: Yêu cầu tắt. Các luồng daemon sẽ tự đóng.")
        # Không cần join() các luồng daemon.
        pass