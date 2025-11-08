import tkinter as tk
import os

# Đảm bảo thư mục logic và ui được thêm vào
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from ui.ui_main_window import DataAnalysisApp
except ImportError as e:
    print(f"LỖI: Không thể import DataAnalysisApp từ ui.ui_main_window: {e}")
    print("Hãy chắc chắn bạn đã tạo thư mục /ui và các file bên trong nó.")
    input("Nhấn Enter để thoát...")
    sys.exit()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = DataAnalysisApp(root)
        root.mainloop()
    except Exception as e:
        print(f"LỖI KHÔNG XÁC ĐỊNH KHI CHẠY APP: {e}")
        import traceback
        print(traceback.format_exc())
        input("Nhấn Enter để thoát...")