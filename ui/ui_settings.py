import tkinter as tk
from tkinter import ttk, messagebox

# (MỚI GĐ 8) Import SETTINGS từ file config_manager
try:
    from logic.config_manager import SETTINGS
except ImportError:
    print("LỖI: ui_settings.py không thể import logic.config_manager.")
    # Tạo đối tượng giả để UI có thể render
    SETTINGS = type('obj', (object,), {
        'get_all_settings': lambda: {
            "STATS_DAYS": 7, "GAN_DAYS": 15, "HIGH_WIN_THRESHOLD": 47.0,
            "AUTO_ADD_MIN_RATE": 50.0, "AUTO_PRUNE_MIN_RATE": 40.0,
            "K2N_RISK_START_THRESHOLD": 4, "K2N_RISK_PENALTY_PER_FRAME": 0.5,
            "AI_PROB_THRESHOLD": 45.0 # (MỚI)
        },
        'update_setting': lambda k, v: (False, "Lỗi: Không tìm thấy config_manager")
    })


class SettingsWindow:
    """
    (MỚI GĐ 8) Cửa sổ Toplevel để quản lý file config.json.
    """

    def __init__(self, app):
        self.app = app
        self.root = app.root
        
        # Ngăn việc mở nhiều cửa sổ
        if hasattr(self.app, 'settings_window') and self.app.settings_window and self.app.settings_window.window.winfo_exists():
            self.app.settings_window.window.lift()
            return
            
        self.app.update_output("Đang mở cửa sổ Cài đặt...")
        
        self.window = tk.Toplevel(self.root)
        self.app.settings_window = self # Gán lại vào app chính
        self.window.title("Cài đặt Hệ thống")
        self.window.geometry("550x380") # (Cập nhật kích thước)

        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(1, weight=1)

        # Dictionary để giữ các biến Entry
        self.entries = {}

        # --- Định nghĩa các cài đặt ---
        # (Tên key trong SETTINGS, Tên hiển thị, Tooltip/Giải thích)
        self.setting_definitions = [
            ("Bảng Tổng Hợp", [
                ("STATS_DAYS", "Số ngày Thống kê Loto Hot", "Số ngày (ví dụ: 7) dùng để tính loto về nhiều."),
                ("GAN_DAYS", "Số ngày tính Lô Gan", "Loto không về trong số ngày này sẽ bị coi là Gan (ví dụ: 15)."),
                ("HIGH_WIN_THRESHOLD", "Ngưỡng Cầu Tỷ Lệ Cao (%)", "Tỷ lệ K2N tối thiểu để một cầu được coi là 'Tỷ Lệ Cao' (ví dụ: 47.0)."),
                ("AI_PROB_THRESHOLD", "Ngưỡng Kích Hoạt AI (%)", "Xác suất tối thiểu để dự đoán AI được tính điểm thưởng (ví dụ: 45.0).") # (MỚI)
            ]),
            ("Tự động Dò Cầu", [
                ("AUTO_ADD_MIN_RATE", "Ngưỡng Thêm Cầu Mới (%)", "Khi dò cầu (V17+BN), tự động thêm nếu tỷ lệ N1 > X (ví dụ: 50.0)."),
                ("AUTO_PRUNE_MIN_RATE", "Ngưỡng Lọc Cầu Yếu (%)", "Khi lọc cầu, tự động TẮT nếu tỷ lệ K2N < X (ví dụ: 40.0).")
            ]),
            ("Quản lý Rủi ro K2N", [
                ("K2N_RISK_START_THRESHOLD", "Ngưỡng bắt đầu phạt (khung)", "Bắt đầu trừ điểm nếu Chuỗi Thua Max > X (ví dụ: 4)."),
                ("K2N_RISK_PENALTY_PER_FRAME", "Điểm phạt / khung thua", "Trừ X điểm cho mỗi khung thua vượt ngưỡng (ví dụ: 0.5).")
            ])
        ]

        # --- Tạo các ô nhập liệu ---
        current_row = 0
        current_settings = SETTINGS.get_all_settings()
        
        for group_name, settings in self.setting_definitions:
            # Tiêu đề nhóm
            group_label = ttk.Label(main_frame, text=group_name, font=('TkDefaultFont', 11, 'bold'))
            group_label.grid(row=current_row, column=0, columnspan=3, sticky="w", padx=5, pady=(10, 2))
            current_row += 1
            
            for key, label, tooltip in settings:
                ttk.Label(main_frame, text=label + ":").grid(row=current_row, column=0, sticky="w", padx=5, pady=3)
                
                entry_var = tk.StringVar(value=current_settings.get(key, ""))
                entry_widget = ttk.Entry(main_frame, textvariable=entry_var)
                entry_widget.grid(row=current_row, column=1, sticky="ew", padx=5, pady=3)
                
                ttk.Label(main_frame, text=f"({tooltip})", style="TLabel", foreground="gray").grid(row=current_row, column=2, sticky="w", padx=5, pady=3)
                
                self.entries[key] = entry_var # Lưu biến, không phải widget
                current_row += 1

        # --- Nút Lưu ---
        save_button = ttk.Button(main_frame, text="Lưu Cài đặt", command=self.save_all_settings)
        save_button.grid(row=current_row, column=0, columnspan=3, sticky="ew", padx=5, pady=(15, 5))

    def save_all_settings(self):
        """Lặp qua tất cả các ô Entry và lưu cài đặt."""
        self.app.update_output("Đang lưu cài đặt...")
        try:
            any_errors = False
            for key, entry_var in self.entries.items():
                new_value = entry_var.get()
                
                # Gọi hàm update của config_manager
                success, message = SETTINGS.update_setting(key, new_value)
                
                if not success:
                    any_errors = True
                    self.app.update_output(f"LỖI: {message}") # Hiển thị lỗi ra log
            
            if any_errors:
                messagebox.showerror("Lỗi Lưu", "Một số cài đặt có lỗi. Vui lòng kiểm tra log.", parent=self.window)
            else:
                self.app.update_output("Đã lưu tất cả cài đặt vào config.json.")
                messagebox.showinfo("Thành công", "Đã lưu tất cả cài đặt thành công!", parent=self.window)
                self.window.destroy() # Đóng cửa sổ sau khi lưu
                
        except Exception as e:
            messagebox.showerror("Lỗi Nghiêm Trọng", f"Không thể lưu cài đặt: {e}", parent=self.window)
            self.app.update_output(traceback.format_exc())