import tkinter as tk
import traceback
from tkinter import messagebox, ttk

# (MỚI GĐ 9) Import SETTINGS để lấy giá trị hiện tại
try:
    from logic.config_manager import SETTINGS
except ImportError:
    print("LỖI: ui_tuner.py không thể import logic.config_manager.")
    SETTINGS = None


class TunerWindow:
    """
    (MỚI GĐ 9) Cửa sổ "Trợ lý Tinh chỉnh Tham số".
    Giúp người dùng backtest các tham số trong config.json.
    """

    def __init__(self, app):
        self.app = app
        self.root = app.root

        if (
            hasattr(self.app, "tuner_window")
            and self.app.tuner_window
            and self.app.tuner_window.window.winfo_exists()
        ):
            self.app.tuner_window.window.lift()
            return

        self.app.update_output("Đang mở Trợ lý Tinh chỉnh Tham số...")

        self.window = tk.Toplevel(self.root)
        self.app.tuner_window = self  # Gán lại vào app chính
        self.window.title("Trợ lý Tinh chỉnh Tham số")
        self.window.geometry("700x500")

        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.rowconfigure(2, weight=1)  # Khung log sẽ co giãn
        main_frame.columnconfigure(0, weight=1)

        # --- Khung Cài đặt ---
        settings_frame = ttk.Labelframe(
            main_frame, text="1. Chọn Tham số để Kiểm thử", padding="10"
        )
        settings_frame.grid(row=0, column=0, sticky="ew")
        settings_frame.columnconfigure(1, weight=1)

        # Danh sách các tham số có thể kiểm thử
        # (Key trong SETTINGS, Tên hiển thị)
        self.tunable_parameters = {
            "GAN_DAYS": "Số ngày tính Lô Gan",
            "HIGH_WIN_THRESHOLD": "Ngưỡng Cầu Tỷ Lệ Cao (%)",
            "AUTO_ADD_MIN_RATE": "Ngưỡng Thêm Cầu Mới (%)",
            "AUTO_PRUNE_MIN_RATE": "Ngưỡng Lọc Cầu Yếu (%)",
            "K2N_RISK_START_THRESHOLD": "Ngưỡng phạt K2N (khung thua)",
            "K2N_RISK_PENALTY_PER_FRAME": "Điểm phạt K2N / khung",
        }

        ttk.Label(settings_frame, text="Chọn tham số:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.param_var = tk.StringVar()
        param_dropdown = ttk.Combobox(
            settings_frame,
            textvariable=self.param_var,
            values=list(self.tunable_parameters.values()),
            state="readonly",
            width=30,
        )
        param_dropdown.grid(row=0, column=1, columnspan=3, sticky="ew", padx=5, pady=5)
        param_dropdown.bind("<<ComboboxSelected>>", self.on_param_select)

        # --- Khung Giá trị ---
        range_frame = ttk.Frame(settings_frame)
        range_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=5)
        range_frame.columnconfigure(1, weight=1)
        range_frame.columnconfigure(3, weight=1)
        range_frame.columnconfigure(5, weight=1)

        ttk.Label(range_frame, text="Từ:").grid(row=0, column=0, sticky="w", padx=5)
        self.from_var = tk.StringVar()
        self.from_entry = ttk.Entry(range_frame, textvariable=self.from_var, width=10)
        self.from_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        ttk.Label(range_frame, text="Đến:").grid(row=0, column=2, sticky="w", padx=5)
        self.to_var = tk.StringVar()
        self.to_entry = ttk.Entry(range_frame, textvariable=self.to_var, width=10)
        self.to_entry.grid(row=0, column=3, sticky="ew", padx=(0, 10))

        ttk.Label(range_frame, text="Bước nhảy:").grid(
            row=0, column=4, sticky="w", padx=5
        )
        self.step_var = tk.StringVar(value="1")  # Mặc định bước nhảy là 1
        self.step_entry = ttk.Entry(range_frame, textvariable=self.step_var, width=10)
        self.step_entry.grid(row=0, column=5, sticky="ew")

        # --- Nút Chạy ---
        self.run_button = ttk.Button(
            main_frame, text="Chạy Phân tích Tinh chỉnh", command=self.run_tuning
        )
        self.run_button.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        # --- Khung Log Kết quả ---
        log_frame = ttk.Labelframe(
            main_frame, text="2. Kết quả Phân tích", padding="10"
        )
        log_frame.grid(row=2, column=0, sticky="nsew", padx=10)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            log_frame,
            height=15,
            width=80,
            font=("Courier New", 10),
            yscrollcommand=log_scrollbar.set,
        )
        self.log_text.pack(expand=True, fill=tk.BOTH)
        log_scrollbar.config(command=self.log_text.yview)
        self.log_text.config(state=tk.DISABLED)

    def on_param_select(self, event):
        """Khi người dùng chọn một tham số, tự động điền giá trị hiện tại."""
        if not SETTINGS:
            return

        selected_name = self.param_var.get()
        # Tìm key từ value
        selected_key = next(
            (
                key
                for key, value in self.tunable_parameters.items()
                if value == selected_name
            ),
            None,
        )

        if selected_key:
            current_value = SETTINGS.get_all_settings().get(selected_key)
            if current_value is not None:
                self.from_var.set(str(current_value))
                self.to_var.set(str(current_value))
                # Gợi ý bước nhảy
                if isinstance(current_value, float):
                    self.step_var.set("0.1")
                else:
                    self.step_var.set("1")

    def log(self, message):
        """Ghi log an toàn vào Text box."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.window.update_idletasks()  # Cập nhật UI ngay

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    def run_tuning(self):
        """Lấy giá trị và gọi hàm logic trong app chính."""
        try:
            # 1. Lấy tham số
            selected_name = self.param_var.get()
            param_key = next(
                (
                    key
                    for key, value in self.tunable_parameters.items()
                    if value == selected_name
                ),
                None,
            )
            if not param_key:
                messagebox.showerror(
                    "Lỗi", "Vui lòng chọn một tham số.", parent=self.window
                )
                return

            # 2. Lấy giá trị (và kiểm tra)
            val_from = float(self.from_var.get())
            val_to = float(self.to_var.get())
            val_step = float(self.step_var.get())

            if val_step <= 0:
                messagebox.showerror(
                    "Lỗi", "Bước nhảy phải lớn hơn 0.", parent=self.window
                )
                return
            if val_from > val_to:
                messagebox.showerror(
                    "Lỗi",
                    "Giá trị 'Từ' không thể lớn hơn giá trị 'Đến'.",
                    parent=self.window,
                )
                return

            # 3. Xóa log cũ và chuẩn bị
            self.clear_log()
            self.log(f"--- BẮT ĐẦU KIỂM THỬ THAM SỐ ---")
            self.log(f"Tham số: {selected_name} ({param_key})")
            self.log(
                f"Khoảng kiểm thử: Từ {val_from} đến {val_to}, bước nhảy {val_step}"
            )
            self.log("Vui lòng chờ...")

            # 4. Tắt nút
            self.run_button.config(state=tk.DISABLED)

            # 5. Gọi hàm logic trong app chính (sẽ được tạo ở Bước 2)
            # Hàm này sẽ tự chạy đa luồng
            self.app.run_parameter_tuning(param_key, val_from, val_to, val_step, self)

        except ValueError:
            messagebox.showerror(
                "Lỗi Giá trị",
                "Giá trị 'Từ', 'Đến', 'Bước nhảy' phải là số.",
                parent=self.window,
            )
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}", parent=self.window)
            self.log(traceback.format_exc())
