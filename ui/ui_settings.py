# Tên file: git3/ui/ui_settings.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - CẬP NHẬT NHÃN HIỂN THỊ CHO ĐÚNG LOGIC MỚI)
#
import tkinter as tk
import traceback
import threading
from tkinter import messagebox, ttk

# Import SETTINGS từ file config_manager
try:
    from logic.config_manager import SETTINGS
except ImportError:
    print("LỖI: ui_settings.py không thể import logic.config_manager.")
    # Tạo đối tượng giả để UI có thể render
    SETTINGS = type(
        "obj",
        (object,),
        {
            "get_all_settings": lambda: {
                "STATS_DAYS": 7,
                "GAN_DAYS": 15,
                "HIGH_WIN_THRESHOLD": 47.0,
                "AUTO_ADD_MIN_RATE": 50.0,
                "AUTO_PRUNE_MIN_RATE": 40.0,
                "K2N_RISK_START_THRESHOLD": 6,
                "K2N_RISK_PENALTY_PER_FRAME": 1.0,
                "AI_PROB_THRESHOLD": 45.0,
                "AI_MAX_DEPTH": 6,
                "AI_N_ESTIMATORS": 200,
                "AI_LEARNING_RATE": 0.05,
                "AI_SCORE_WEIGHT": 0.2,
            },
            "update_setting": lambda k, v: (
                False,
                "Lỗi: Không tìm thấy config_manager",
            ),
        },
    )


class SettingsWindow:
    """
    Cửa sổ Toplevel để quản lý file config.json.
    """

    def __init__(self, app):
        self.app = app
        self.root = app.root

        # Ngăn việc mở nhiều cửa sổ
        if (
            hasattr(self.app, "settings_window")
            and self.app.settings_window
            and self.app.settings_window.window.winfo_exists()
        ):
            self.app.settings_window.window.lift()
            return

        self.app.logger.log("Đang mở cửa sổ Cài đặt...")

        self.window = tk.Toplevel(self.root)
        self.app.settings_window = self  # Gán lại vào app chính
        self.window.title("Cài đặt Hệ thống")
        self.window.geometry("550x500")  # Tăng chiều cao một chút

        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(1, weight=1)

        # Dictionary để giữ các biến Entry
        self.entries = {}

        # --- Định nghĩa các cài đặt ---
        # (Tên key trong SETTINGS, Tên hiển thị, Tooltip/Giải thích)
        self.setting_definitions = [
            (
                "Bảng Tổng Hợp",
                [
                    (
                        "STATS_DAYS",
                        "Số ngày Thống kê Loto Hot",
                        "Số ngày (ví dụ: 7) dùng để tính loto về nhiều.",
                    ),
                    (
                        "GAN_DAYS",
                        "Số ngày tính Lô Gan",
                        "Loto không về trong số ngày này sẽ bị coi là Gan (ví dụ: 15).",
                    ),
                    (
                        "HIGH_WIN_THRESHOLD",
                        "Ngưỡng Cầu Tỷ Lệ Cao (%)",
                        "Tỷ lệ K2N tối thiểu để một cầu được coi là 'Tỷ Lệ Cao' (ví dụ: 47.0).",
                    ),
                    (
                        "AI_PROB_THRESHOLD",
                        "Ngưỡng Kích Hoạt AI (%)",
                        "Xác suất tối thiểu để dự đoán AI được tính điểm thưởng (ví dụ: 45.0).",
                    ),
                ],
            ),
            (
                "Cài đặt Mô hình AI (XGBoost V7.1)",
                [
                    (
                        "AI_MAX_DEPTH",
                        "Độ Sâu Cây Max",
                        "Độ sâu tối đa của cây (ví dụ: 6) - Cần Huấn luyện lại.",
                    ),
                    (
                        "AI_N_ESTIMATORS",
                        "Số lượng Cây (Estimators)",
                        "Số lượng cây trong rừng (ví dụ: 200) - Cần Huấn luyện lại.",
                    ),
                    (
                        "AI_LEARNING_RATE",
                        "Tốc độ học (Learning Rate)",
                        "Tốc độ học của mô hình GBM (ví dụ: 0.05) - Cần Huấn luyện lại.",
                    ),
                    (
                        "AI_SCORE_WEIGHT",
                        "Trọng số Điểm AI",
                        "Mức độ ảnh hưởng của xác suất AI lên điểm tổng lực (ví dụ: 0.2).",
                    ),
                ],
            ),
            (
                "Tự động Dò Cầu",
                [
                    (
                        "AUTO_ADD_MIN_RATE",
                        "Ngưỡng Thêm Cầu Mới (%)",
                        "Khi dò cầu (V17+BN), tự động thêm nếu tỷ lệ N1 > X (ví dụ: 50.0).",
                    ),
                    (
                        "AUTO_PRUNE_MIN_RATE",
                        "Ngưỡng Lọc Cầu Yếu (%)",
                        "Khi lọc cầu, tự động TẮT nếu tỷ lệ K2N < X (ví dụ: 40.0).",
                    ),
                ],
            ),
            (
                "Quản lý Rủi ro K2N",
                [
                    (
                        "K2N_RISK_START_THRESHOLD",
                        "Ngưỡng bắt đầu phạt (khung)",
                        "Bắt đầu trừ điểm nếu Chuỗi Thua Max > X (ví dụ: 6).",
                    ),
                    # (SỬA ĐỔI NHÃN HIỂN THỊ CHO ĐÚNG LOGIC MỚI)
                    (
                        "K2N_RISK_PENALTY_PER_FRAME",
                        "Điểm phạt CỐ ĐỊNH",
                        "Trừ X điểm cố định 1 lần nếu cầu vượt ngưỡng rủi ro (ví dụ: 1.0).",
                    ),
                ],
            ),
            (
                "Chấm Điểm Phong Độ",
                [
                    (
                        "RECENT_FORM_PERIODS",
                        "Số kỳ xét phong độ",
                        "Xét phong độ trong X kỳ gần nhất (ví dụ: 10).",
                    ),
                    (
                        "RECENT_FORM_MIN_HIGH",
                        "Ngưỡng phong độ rất cao",
                        "Số lần ăn tối thiểu cho phong độ rất cao (ví dụ: 8).",
                    ),
                    (
                        "RECENT_FORM_BONUS_HIGH",
                        "Điểm thưởng phong độ rất cao",
                        "Điểm cộng cho phong độ rất cao (ví dụ: 3.0).",
                    ),
                    (
                        "RECENT_FORM_MIN_MED",
                        "Ngưỡng phong độ tốt",
                        "Số lần ăn tối thiểu cho phong độ tốt (ví dụ: 6).",
                    ),
                    (
                        "RECENT_FORM_BONUS_MED",
                        "Điểm thưởng phong độ tốt",
                        "Điểm cộng cho phong độ tốt (ví dụ: 2.0).",
                    ),
                    (
                        "RECENT_FORM_MIN_LOW",
                        "Ngưỡng phong độ ổn",
                        "Số lần ăn tối thiểu cho phong độ ổn (ví dụ: 5).",
                    ),
                    (
                        "RECENT_FORM_BONUS_LOW",
                        "Điểm thưởng phong độ ổn",
                        "Điểm cộng cho phong độ ổn (ví dụ: 1.0).",
                    ),
                ],
            ),
        ]

        # --- Tạo các ô nhập liệu ---
        current_row = 0
        current_settings = SETTINGS.get_all_settings()

        for group_name, settings in self.setting_definitions:
            # Tiêu đề nhóm
            group_label = ttk.Label(
                main_frame, text=group_name, font=("TkDefaultFont", 11, "bold")
            )
            group_label.grid(
                row=current_row,
                column=0,
                columnspan=3,
                sticky="w",
                padx=5,
                pady=(10, 2),
            )
            current_row += 1

            for key, label, tooltip in settings:
                ttk.Label(main_frame, text=label + ":").grid(
                    row=current_row, column=0, sticky="w", padx=5, pady=3
                )

                # Lấy giá trị hiện tại
                val = current_settings.get(key, "")
                entry_var = tk.StringVar(value=str(val))

                entry_widget = ttk.Entry(main_frame, textvariable=entry_var)
                entry_widget.grid(
                    row=current_row, column=1, sticky="ew", padx=5, pady=3
                )

                ttk.Label(
                    main_frame, text=f"({tooltip})", style="TLabel", foreground="gray"
                ).grid(row=current_row, column=2, sticky="w", padx=5, pady=3)

                self.entries[key] = entry_var  # Lưu biến, không phải widget
                current_row += 1

        # --- 4. Cấu Hình Hiệu Năng (MỚI) ---
        grp_perf = ttk.LabelFrame(main_frame, text="4. Cấu Hình Hiệu Năng (Data Slicing)", padding="10")
        grp_perf.grid(row=current_row, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        grp_perf.columnconfigure(1, weight=1)
        current_row += 1

        # Giới hạn dữ liệu Dashboard
        ttk.Label(grp_perf, text="Giới hạn dữ liệu Dashboard (0 = Full):").grid(
            row=0, column=0, sticky="w", padx=5, pady=3
        )
        val_dashboard = current_settings.get("DATA_LIMIT_DASHBOARD", "0")
        entry_dashboard_var = tk.StringVar(value=str(val_dashboard))
        entry_dashboard = ttk.Entry(grp_perf, textvariable=entry_dashboard_var)
        entry_dashboard.grid(
            row=0, column=1, sticky="ew", padx=5, pady=3
        )
        self.entries["DATA_LIMIT_DASHBOARD"] = entry_dashboard_var

        # Giới hạn dữ liệu Tối Ưu Hóa
        ttk.Label(grp_perf, text="Giới hạn dữ liệu Tối Ưu Hóa (0 = Full):").grid(
            row=1, column=0, sticky="w", padx=5, pady=3
        )
        val_research = current_settings.get("DATA_LIMIT_RESEARCH", "0")
        entry_research_var = tk.StringVar(value=str(val_research))
        entry_research = ttk.Entry(grp_perf, textvariable=entry_research_var)
        entry_research.grid(
            row=1, column=1, sticky="ew", padx=5, pady=3
        )
        self.entries["DATA_LIMIT_RESEARCH"] = entry_research_var

        # Giới hạn dữ liệu Quét Cầu
        ttk.Label(grp_perf, text="Giới hạn dữ liệu Quét Cầu (0 = Full):").grid(
            row=2, column=0, sticky="w", padx=5, pady=3
        )
        val_scanner = current_settings.get("DATA_LIMIT_SCANNER", "2")
        entry_scanner_var = tk.StringVar(value=str(val_scanner))
        entry_scanner = ttk.Entry(grp_perf, textvariable=entry_scanner_var)
        entry_scanner.grid(
            row=2, column=1, sticky="ew", padx=5, pady=3
        )
        self.entries["DATA_LIMIT_SCANNER"] = entry_scanner_var

        # Label giải thích chung
        ttk.Label(
            grp_perf, 
            text="* Giảm số lượng kỳ giúp tăng tốc độ xử lý.", 
            font=("Arial", 8, "italic"), 
            foreground="gray"
        ).grid(row=3, column=1, sticky="w", padx=5, pady=(0, 5))

        # --- Nút Lưu ---
        save_button = ttk.Button(
            main_frame, text="Lưu Cài đặt", command=self.save_all_settings
        )
        save_button.grid(
            row=current_row, column=0, columnspan=3, sticky="ew", padx=5, pady=(15, 5)
        )

        current_row += 1

        # --- Nút Nạp 756 Cầu Bạc Nhớ ---
        load_memory_button = ttk.Button(
            main_frame, text="Nạp 756 Cầu Bạc Nhớ", command=self.load_756_memory_bridges
        )
        load_memory_button.grid(
            row=current_row, column=0, columnspan=3, sticky="ew", padx=5, pady=(5, 5)
        )

    def save_all_settings(self):
        """Lặp qua tất cả các ô Entry và lưu cài đặt."""
        self.app.logger.log("Đang lưu cài đặt...")
        try:
            any_errors = False
            for key, entry_var in self.entries.items():
                new_value = entry_var.get()

                # Gọi hàm update của config_manager
                success, message = SETTINGS.update_setting(key, new_value)

                if not success:
                    any_errors = True
                    self.app.logger.log(f"LỖI: {message}")

            if any_errors:
                messagebox.showerror(
                    "Lỗi Lưu",
                    "Một số cài đặt có lỗi. Vui lòng kiểm tra log.",
                    parent=self.window,
                )
            else:
                self.app.logger.log("Đã lưu tất cả cài đặt vào config.json.")
                messagebox.showinfo(
                    "Thành công",
                    "Đã lưu tất cả cài đặt thành công!",
                    parent=self.window,
                )
                self.window.destroy()  # Đóng cửa sổ sau khi lưu

        except Exception as e:
            messagebox.showerror(
                "Lỗi Nghiêm Trọng", f"Không thể lưu cài đặt: {e}", parent=self.window
            )
            self.app.logger.log(traceback.format_exc())

    def load_756_memory_bridges(self):
        """Nạp 756 cầu Bạc Nhớ vào database với progress bar."""
        # Create a custom dialog with options
        dialog = tk.Toplevel(self.window)
        dialog.title("Nạp 756 Cầu Bạc Nhớ")
        dialog.geometry("500x250")
        dialog.transient(self.window)
        dialog.grab_set()

        # Dialog content
        ttk.Label(
            dialog,
            text="Bạn có chắc muốn thêm 756 cầu Bạc Nhớ vào database?",
            font=("TkDefaultFont", 10, "bold")
        ).pack(pady=(20, 10))

        ttk.Label(
            dialog,
            text="Lưu ý: Cầu trùng sẽ được bỏ qua",
            font=("TkDefaultFont", 9)
        ).pack(pady=5)

        # Option for enabling all bridges
        enable_var = tk.BooleanVar(value=False)
        enable_check = ttk.Checkbutton(
            dialog,
            text="BẬT tất cả cầu để phân tích ngay (khuyến nghị)",
            variable=enable_var
        )
        enable_check.pack(pady=10)

        ttk.Label(
            dialog,
            text="💡 Nếu bật: Tất cả 756 cầu sẽ được BẬT để backtest tính tỷ lệ ăn.\n"
                 "Sau đó dùng 'Lọc Cầu Yếu' để tự động TẮT cầu có tỷ lệ thấp.",
            font=("TkDefaultFont", 8),
            foreground="blue",
            wraplength=450,
            justify="left"
        ).pack(pady=5)

        ttk.Label(
            dialog,
            text="Nếu không bật: Cầu sẽ TẮT, bạn phải BẬT thủ công từng cầu.",
            font=("TkDefaultFont", 8),
            foreground="gray",
            wraplength=450,
            justify="left"
        ).pack(pady=5)

        # Store result
        result = {"confirmed": False, "enable_all": False}

        def on_ok():
            result["confirmed"] = True
            result["enable_all"] = enable_var.get()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Hủy", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

        # Wait for dialog to close
        self.window.wait_window(dialog)

        if not result["confirmed"]:
            return

        enable_all = result["enable_all"]

        # Tạo progress window
        progress_window = tk.Toplevel(self.window)
        progress_window.title("Đang nạp cầu...")
        progress_window.geometry("400x150")
        progress_window.transient(self.window)
        progress_window.grab_set()

        # Progress label
        progress_label = ttk.Label(
            progress_window,
            text="Đang chuẩn bị...",
            font=("TkDefaultFont", 10)
        )
        progress_label.pack(pady=(20, 10))

        # Progress bar
        progress_bar = ttk.Progressbar(
            progress_window,
            mode="determinate",
            length=350
        )
        progress_bar.pack(pady=10, padx=25)

        # Status label
        status_label = ttk.Label(
            progress_window,
            text="0/756",
            font=("TkDefaultFont", 9)
        )
        status_label.pack(pady=5)

        # Import the function
        try:
            from logic.bridges.bridge_manager_core import init_all_756_memory_bridges_to_db
        except ImportError as e:
            messagebox.showerror(
                "Lỗi Import",
                f"Không thể import hàm nạp cầu: {e}",
                parent=self.window
            )
            progress_window.destroy()
            return

        # Progress callback
        def update_progress(current, total, message):
            progress_bar["maximum"] = total
            progress_bar["value"] = current
            progress_label["text"] = message
            status_label["text"] = f"{current}/{total}"
            progress_window.update()

        # Run the import in a separate thread to keep UI responsive

        result_container = {}

        def do_import():
            try:
                success, message, added, skipped = init_all_756_memory_bridges_to_db(
                    progress_callback=update_progress,
                    enable_all=enable_all
                )
                result_container["success"] = success
                result_container["message"] = message
                result_container["added"] = added
                result_container["skipped"] = skipped
                result_container["enable_all"] = enable_all
            except Exception as e:
                result_container["success"] = False
                result_container["message"] = f"Lỗi: {e}"
                result_container["error"] = str(e)

        # Start import thread
        import_thread = threading.Thread(target=do_import)
        import_thread.start()

        # Wait for thread to complete
        while import_thread.is_alive():
            progress_window.update()
            import_thread.join(timeout=0.1)

        # Close progress window
        progress_window.destroy()

        # Show result
        if result_container.get("success"):
            self.app.logger.log(result_container["message"])

            # Build success message with next steps
            success_msg = result_container["message"]
            if result_container.get("enable_all"):
                success_msg += "\n\n✅ Tất cả cầu đã được BẬT.\n\n"
                success_msg += "🔄 Bước tiếp theo:\n"
                success_msg += "1. Chạy 'Cập Nhật Cache K2N' để tính tỷ lệ ăn\n"
                success_msg += "2. Dùng 'Lọc Cầu Yếu' để TẮT cầu có tỷ lệ thấp\n"
                success_msg += "3. Chạy Backtest với các cầu còn lại"
            else:
                success_msg += "\n\n⚠️ Cầu đang ở trạng thái TẮT.\n\n"
                success_msg += "Bạn cần BẬT cầu thủ công trong 'Quản Lý Cầu' trước khi backtest."

            messagebox.showinfo(
                "Thành công",
                success_msg,
                parent=self.window
            )
        else:
            error_msg = result_container.get("message", "Lỗi không xác định")
            self.app.logger.log(f"LỖI: {error_msg}")
            messagebox.showerror(
                "Lỗi",
                error_msg,
                parent=self.window
            )
