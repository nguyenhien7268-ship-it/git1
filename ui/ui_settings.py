import tkinter as tk
from tkinter import ttk, messagebox
import traceback
import json

# (ĐÃ XÓA) Bỏ import logic.config_manager. VIEW không được truy cập SETTINGS trực tiếp

class SettingsWindow:
    """
    Cửa sổ Cài đặt Tham số (VIEW). 
    Lớp này chỉ chịu trách nhiệm hiển thị và thu thập input.
    """

    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.controller = app.controller # Lấy tham chiếu Controller
        
        if hasattr(self.app, 'settings_window') and self.app.settings_window and self.app.settings_window.window.winfo_exists():
            self.app.settings_window.window.lift()
            return

        self.app.logger.log("Đang mở cửa sổ Cài đặt Tham số...")
        
        self.window = tk.Toplevel(self.root)
        self.app.settings_window = self # Gán lại vào app chính
        self.window.title("Cài đặt Tham số Hệ thống (config.json)")
        self.window.geometry("600x650") # Tăng chiều cao

        self.main_frame = ttk.Frame(self.window, padding="15")
        self.main_frame.pack(expand=True, fill=tk.BOTH)
        self.main_frame.columnconfigure(1, weight=1)

        # Danh sách tham số cấu hình (tên Key trong config.json, tên hiển thị)
        self.config_fields = [
            ("STATS_DAYS", "Số ngày thống kê Loto Về Nhiều (Tab Quyết định)"),
            ("GAN_DAYS", "Ngưỡng tính Lô Gan (Số ngày)"),
            ("HIGH_WIN_THRESHOLD", "Ngưỡng % để nhận diện Cầu Tỷ lệ Cao (%)"),
            ("AI_SCORE_WEIGHT", "Trọng số điểm của AI (AI Score Weight)"),
            ("AI_LEARNING_RATE", "Tốc độ học của Mô hình AI (Learning Rate)"),
            ("AI_OBJECTIVE", "Hàm mục tiêu của Mô hình AI (Objective)"),
            ("K2N_RISK_START_THRESHOLD", "Ngưỡng khung thua K2N để bắt đầu trừ điểm (Risk Start)"),
            ("K2N_RISK_PENALTY_PER_FRAME", "Điểm phạt / khung thua (Penalty)"),
            ("AUTO_ADD_MIN_RATE", "Ngưỡng % để Tự động Thêm Cầu Mới"),
            ("AUTO_PRUNE_MIN_RATE", "Ngưỡng % để Tự động Lọc Cầu Yếu")
        ]
        
        self.entry_vars = {}
        
        # Tạo các trường Entry
        for i, (key, desc) in enumerate(self.config_fields):
            row = i * 2 # Hai hàng cho mỗi trường (Label + Entry)
            
            # Label (Hàng chẵn)
            ttk.Label(self.main_frame, text=f"{desc} ({key}):").grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 0), padx=5)
            
            # Entry (Hàng lẻ)
            self.entry_vars[key] = tk.StringVar()
            entry = ttk.Entry(self.main_frame, textvariable=self.entry_vars[key])
            entry.grid(row=row + 1, column=0, columnspan=2, sticky="ew", padx=5)
            
        # Nút Save
        ttk.Separator(self.main_frame, orient='horizontal').grid(row=len(self.config_fields) * 2, column=0, columnspan=2, sticky="ew", pady=15)
        self.save_button = ttk.Button(self.main_frame, text="✅ LƯU CẤU HÌNH (config.json)", command=self.save_settings)
        self.save_button.grid(row=len(self.config_fields) * 2 + 1, column=0, columnspan=2, sticky="ew", padx=5)

        # Tải dữ liệu ban đầu
        self.load_current_settings()
        
    def populate_settings(self, settings_dict):
        """
        [VIEW CALLBACK] Hàm được Controller gọi để điền dữ liệu vào các trường.
        settings_dict: dict chứa các cặp key: value từ config.
        """
        try:
            for key, var in self.entry_vars.items():
                value = settings_dict.get(key)
                if value is not None:
                    var.set(str(value))
            self.app.logger.log("Đã nạp thành công các tham số cấu hình.")
        except Exception as e:
            self.app.logger.log(f"LỖI nạp cấu hình: {e}")

    def load_current_settings(self):
        """[VIEW ACTION] Ủy quyền cho Controller để tải cấu hình."""
        # Gọi Controller để tải cấu hình. Controller sẽ gọi populate_settings() khi hoàn tất.
        self.controller.task_load_all_settings(self)

    def save_settings(self):
        """[VIEW ACTION] Ủy quyền cho Controller để lưu cấu hình."""
        
        # 1. Thu thập dữ liệu từ UI
        new_settings = {}
        try:
            for key, var in self.entry_vars.items():
                raw_value = var.get().strip()
                if not raw_value:
                    # Bỏ qua nếu trống (Controller sẽ sử dụng giá trị cũ)
                    continue
                    
                # Cố gắng chuyển đổi kiểu dữ liệu (Logic này là VIEW data validation)
                if key in ["STATS_DAYS", "GAN_DAYS", "K2N_RISK_START_THRESHOLD"]:
                    value = int(raw_value)
                elif key in ["HIGH_WIN_THRESHOLD", "AI_SCORE_WEIGHT", "AI_LEARNING_RATE", "K2N_RISK_PENALTY_PER_FRAME", "AUTO_ADD_MIN_RATE", "AUTO_PRUNE_MIN_RATE"]:
                    value = float(raw_value)
                else: # AI_OBJECTIVE và các chuỗi khác
                    value = raw_value

                new_settings[key] = value

            if not new_settings:
                messagebox.showwarning("Lỗi", "Không có tham số nào để lưu.", parent=self.window)
                return

        except ValueError:
            messagebox.showerror("Lỗi Giá trị", "Giá trị nhập vào không hợp lệ (cần là số nguyên/thập phân).", parent=self.window)
            return
        
        # 2. Ủy quyền cho Controller
        self.save_button.config(state=tk.DISABLED)
        self.controller.task_save_all_settings(new_settings, self.window)

    # Các hàm Callback cần thiết
    def _re_enable_save_button(self):
        """Callback để BẬT lại nút Lưu (được Controller gọi sau khi tác vụ hoàn tất)."""
        if self.save_button and self.save_button.winfo_exists():
            self.save_button.config(state=tk.NORMAL)