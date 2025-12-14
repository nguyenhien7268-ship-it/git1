# Tên file: git3/ui/ui_settings.py
#
# (PHIÊN BẢN V8.1 - UI 3 TAB: Quản lý Lô/Đề, Cấu hình AI, Hiệu năng & Phong Độ)
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
                "lo_config": {"remove_threshold": 43.0, "add_threshold": 45.0},
                "de_config": {"remove_threshold": 80.0, "add_threshold": 88.0},
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
    Cửa sổ Toplevel để quản lý file config.json với 3 Tab.
    Tab 1: Quản lý Lô/Đề (lo_config, de_config)
    Tab 2: Cấu hình AI 
    Tab 3: Hiệu năng & Phong Độ
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
        self.window.title("Cài đặt Hệ thống (V8.1 - Dual Config)")
        self.window.geometry("650x600")  # Tăng kích thước cho tab view

        # Dictionary để giữ các biến Entry
        self.entries = {}
        
        # Tải cài đặt hiện tại
        self.current_settings = SETTINGS.get_all_settings()

        # Tạo Notebook (Tab container)
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Tạo 3 tabs
        self.create_lo_de_tab()
        self.create_ai_tab()
        self.create_performance_tab()
        
        # Nút lưu và nạp cầu ở dưới cùng
        self.create_bottom_buttons()

    def create_lo_de_tab(self):
        """Tab 1: Quản lý Lô/Đề - Dual Config Thresholds"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎯 Quản lý Lô/Đề")
        
        # Canvas + Scrollbar for this tab
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        scrollable_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # === Cấu hình Cầu Lô (lo_config) ===
        lo_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ Cấu hình Cầu Lô (Lo Config)", padding="15")
        lo_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        lo_frame.columnconfigure(1, weight=1)
        row += 1
        
        # Get lo_config values
        lo_config = self.current_settings.get('lo_config', {})
        
        # Lo Remove Threshold
        ttk.Label(lo_frame, text="🔴 Ngưỡng TẮT Cầu Lô (%):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        lo_remove_var = tk.StringVar(value=str(lo_config.get('remove_threshold', 43.0)))
        ttk.Entry(lo_frame, textvariable=lo_remove_var, width=15).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(lo_frame, text="Tắt cầu khi K1N & K2N < ngưỡng này", foreground="#666", 
                 font=("Arial", 9, "italic")).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.entries['lo_config_remove'] = lo_remove_var
        
        # Lo Add Threshold
        ttk.Label(lo_frame, text="🟢 Ngưỡng BẬT Lại Cầu Lô (%):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        lo_add_var = tk.StringVar(value=str(lo_config.get('add_threshold', 45.0)))
        ttk.Entry(lo_frame, textvariable=lo_add_var, width=15).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(lo_frame, text="Bật lại cầu khi K1N >= ngưỡng này", foreground="#666",
                 font=("Arial", 9, "italic")).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.entries['lo_config_add'] = lo_add_var
        
        # Info box
        info_frame = ttk.Frame(lo_frame)
        info_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=(10, 5))
        ttk.Label(info_frame, text="💡 Lưu ý:", foreground="blue", font=("Arial", 9, "bold")).pack(anchor="w")
        ttk.Label(info_frame, text="• Cầu Lô thường linh hoạt hơn, ngưỡng thấp hơn (40-50%)", 
                 foreground="#444", font=("Arial", 8)).pack(anchor="w", padx=15)
        ttk.Label(info_frame, text="• Buffer zone (khoảng cách giữa 2 ngưỡng) giúp tránh dao động", 
                 foreground="#444", font=("Arial", 8)).pack(anchor="w", padx=15)
        
        # === Cấu hình Cầu Đề (de_config) ===
        de_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ Cấu hình Cầu Đề (De Config)", padding="15")
        de_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        de_frame.columnconfigure(1, weight=1)
        row += 1
        
        # Get de_config values
        de_config = self.current_settings.get('de_config', {})
        
        # De Remove Threshold
        ttk.Label(de_frame, text="🔴 Ngưỡng TẮT Cầu Đề (%):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        de_remove_var = tk.StringVar(value=str(de_config.get('remove_threshold', 80.0)))
        ttk.Entry(de_frame, textvariable=de_remove_var, width=15).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(de_frame, text="Tắt cầu khi K1N & K2N < ngưỡng này", foreground="#666",
                 font=("Arial", 9, "italic")).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.entries['de_config_remove'] = de_remove_var
        
        # De Add Threshold
        ttk.Label(de_frame, text="🟢 Ngưỡng BẬT Lại Cầu Đề (%):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        de_add_var = tk.StringVar(value=str(de_config.get('add_threshold', 88.0)))
        ttk.Entry(de_frame, textvariable=de_add_var, width=15).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        ttk.Label(de_frame, text="Bật lại cầu khi K1N >= ngưỡng này", foreground="#666",
                 font=("Arial", 9, "italic")).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.entries['de_config_add'] = de_add_var
        
        # Info box
        info_frame = ttk.Frame(de_frame)
        info_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=(10, 5))
        ttk.Label(info_frame, text="💡 Lưu ý:", foreground="blue", font=("Arial", 9, "bold")).pack(anchor="w")
        ttk.Label(info_frame, text="• Cầu Đề rủi ro cao hơn, nên dùng ngưỡng bảo thủ (75-90%)", 
                 foreground="#444", font=("Arial", 8)).pack(anchor="w", padx=15)
        ttk.Label(info_frame, text="• Buffer zone lớn hơn (8%) giúp chỉ giữ cầu thực sự tốt", 
                 foreground="#444", font=("Arial", 8)).pack(anchor="w", padx=15)
        
        # === Legacy Settings (deprecated but kept for compatibility) ===
        legacy_frame = ttk.LabelFrame(scrollable_frame, text="⚠️ Cài đặt Cũ (Legacy - Không khuyến nghị)", padding="15")
        legacy_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        legacy_frame.columnconfigure(1, weight=1)
        
        ttk.Label(legacy_frame, text="Ngưỡng Thêm Cầu Mới (AUTO_ADD):").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        auto_add_var = tk.StringVar(value=str(self.current_settings.get('AUTO_ADD_MIN_RATE', 50.0)))
        ttk.Entry(legacy_frame, textvariable=auto_add_var, state='readonly').grid(row=0, column=1, sticky="w", padx=5, pady=3)
        ttk.Label(legacy_frame, text="⚠️ Deprecated - Dùng lo_config thay thế", foreground="orange",
                 font=("Arial", 8)).grid(row=0, column=2, sticky="w", padx=5, pady=3)
        self.entries['AUTO_ADD_MIN_RATE'] = auto_add_var
        
        ttk.Label(legacy_frame, text="Ngưỡng Lọc Cầu Yếu (AUTO_PRUNE):").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        auto_prune_var = tk.StringVar(value=str(self.current_settings.get('AUTO_PRUNE_MIN_RATE', 40.0)))
        ttk.Entry(legacy_frame, textvariable=auto_prune_var, state='readonly').grid(row=1, column=1, sticky="w", padx=5, pady=3)
        ttk.Label(legacy_frame, text="⚠️ Deprecated - Dùng lo_config thay thế", foreground="orange",
                 font=("Arial", 8)).grid(row=1, column=2, sticky="w", padx=5, pady=3)
        self.entries['AUTO_PRUNE_MIN_RATE'] = auto_prune_var

    def create_ai_tab(self):
        """Tab 2: Cấu hình AI - Model Parameters"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🤖 Cấu hình AI")
        
        # Canvas + Scrollbar
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        scrollable_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # === AI Model Parameters ===
        ai_frame = ttk.LabelFrame(scrollable_frame, text="🧠 Tham số Mô hình AI (XGBoost)", padding="15")
        ai_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        ai_frame.columnconfigure(1, weight=1)
        row += 1
        
        ai_settings = [
            ("AI_MAX_DEPTH", "Độ Sâu Cây (Max Depth):", "Độ sâu tối đa của cây (6-12) - Cần huấn luyện lại"),
            ("AI_N_ESTIMATORS", "Số lượng Cây (Estimators):", "Số cây trong mô hình (100-300) - Cần huấn luyện lại"),
            ("AI_LEARNING_RATE", "Tốc độ Học (Learning Rate):", "Tốc độ học của GBM (0.01-0.1) - Cần huấn luyện lại"),
            ("AI_SCORE_WEIGHT", "Trọng số Điểm AI:", "Ảnh hưởng của AI lên điểm tổng (0.0-1.0)"),
            ("AI_PROB_THRESHOLD", "Ngưỡng Kích Hoạt AI (%):", "Xác suất tối thiểu để tính điểm thưởng (40-60)"),
        ]
        
        for idx, (key, label, tooltip) in enumerate(ai_settings):
            ttk.Label(ai_frame, text=label).grid(row=idx, column=0, sticky="w", padx=5, pady=5)
            var = tk.StringVar(value=str(self.current_settings.get(key, "")))
            ttk.Entry(ai_frame, textvariable=var, width=20).grid(row=idx, column=1, sticky="w", padx=5, pady=5)
            ttk.Label(ai_frame, text=tooltip, foreground="#666", font=("Arial", 9, "italic")).grid(
                row=idx, column=2, sticky="w", padx=5, pady=5)
            self.entries[key] = var
        
        # Info box
        info_frame = ttk.Frame(ai_frame)
        info_frame.grid(row=len(ai_settings), column=0, columnspan=3, sticky="ew", padx=5, pady=(10, 5))
        ttk.Label(info_frame, text="⚠️ Lưu ý quan trọng:", foreground="red", font=("Arial", 9, "bold")).pack(anchor="w")
        ttk.Label(info_frame, text="• Thay đổi Max Depth, Estimators, Learning Rate cần HUẤN LUYỆN LẠI mô hình", 
                 foreground="#444", font=("Arial", 8)).pack(anchor="w", padx=15)
        ttk.Label(info_frame, text="• Chỉ nên thay đổi AI Score Weight và Threshold mà không cần train lại", 
                 foreground="#444", font=("Arial", 8)).pack(anchor="w", padx=15)

    def create_performance_tab(self):
        """Tab 3: Hiệu năng & Phong Độ - Performance Settings"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚡ Hiệu năng & Phong Độ")
        
        # Canvas + Scrollbar
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        scrollable_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # === Performance Settings ===
        perf_frame = ttk.LabelFrame(scrollable_frame, text="⚡ Cấu hình Hiệu năng (Data Slicing)", padding="15")
        perf_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        perf_frame.columnconfigure(1, weight=1)
        row += 1
        
        perf_settings = [
            ("DATA_LIMIT_DASHBOARD", "Giới hạn Dashboard (0 = Full):", "Số kỳ hiển thị trên Dashboard"),
            ("DATA_LIMIT_RESEARCH", "Giới hạn Tối ưu hóa (0 = Full):", "Số kỳ dùng cho tối ưu hóa"),
            ("DATA_LIMIT_SCANNER", "Giới hạn Quét Cầu (0 = Full):", "Số kỳ dùng khi dò cầu mới"),
        ]
        
        for idx, (key, label, tooltip) in enumerate(perf_settings):
            ttk.Label(perf_frame, text=label).grid(row=idx, column=0, sticky="w", padx=5, pady=5)
            var = tk.StringVar(value=str(self.current_settings.get(key, "0")))
            ttk.Entry(perf_frame, textvariable=var, width=20).grid(row=idx, column=1, sticky="w", padx=5, pady=5)
            ttk.Label(perf_frame, text=tooltip, foreground="#666", font=("Arial", 9, "italic")).grid(
                row=idx, column=2, sticky="w", padx=5, pady=5)
            self.entries[key] = var
        
        ttk.Label(perf_frame, text="💡 Giảm số kỳ giúp tăng tốc độ xử lý đáng kể", 
                 foreground="blue", font=("Arial", 8, "italic")).grid(
                     row=len(perf_settings), column=0, columnspan=3, sticky="w", padx=5, pady=(10, 0))
        
        # === Recent Form Settings ===
        form_frame = ttk.LabelFrame(scrollable_frame, text="📊 Chấm Điểm Phong Độ (Recent Form)", padding="15")
        form_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        form_frame.columnconfigure(1, weight=1)
        row += 1
        
        form_settings = [
            ("RECENT_FORM_PERIODS", "Số kỳ xét phong độ:", "Xét phong độ trong X kỳ gần nhất (VD: 10)"),
            ("RECENT_FORM_MIN_HIGH", "Ngưỡng phong độ cao:", "Số lần ăn tối thiểu cho phong độ cao (VD: 8)"),
            ("RECENT_FORM_BONUS_HIGH", "Điểm thưởng phong độ cao:", "Điểm cộng cho phong độ cao (VD: 3.0)"),
            ("RECENT_FORM_MIN_MED", "Ngưỡng phong độ trung bình:", "Số lần ăn cho phong độ TB (VD: 6)"),
            ("RECENT_FORM_BONUS_MED", "Điểm thưởng phong độ TB:", "Điểm cộng cho phong độ TB (VD: 2.0)"),
            ("RECENT_FORM_MIN_LOW", "Ngưỡng phong độ thấp:", "Số lần ăn cho phong độ thấp (VD: 5)"),
            ("RECENT_FORM_BONUS_LOW", "Điểm thưởng phong độ thấp:", "Điểm cộng cho phong độ thấp (VD: 1.0)"),
        ]
        
        for idx, (key, label, tooltip) in enumerate(form_settings):
            ttk.Label(form_frame, text=label).grid(row=idx, column=0, sticky="w", padx=5, pady=3)
            var = tk.StringVar(value=str(self.current_settings.get(key, "")))
            ttk.Entry(form_frame, textvariable=var, width=20).grid(row=idx, column=1, sticky="w", padx=5, pady=3)
            ttk.Label(form_frame, text=tooltip, foreground="#666", font=("Arial", 8, "italic")).grid(
                row=idx, column=2, sticky="w", padx=5, pady=3)
            self.entries[key] = var
        
        # === Other Settings ===
        other_frame = ttk.LabelFrame(scrollable_frame, text="📋 Cài đặt Khác", padding="15")
        other_frame.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        other_frame.columnconfigure(1, weight=1)
        row += 1
        
        other_settings = [
            ("STATS_DAYS", "Số ngày Thống kê Loto Hot:", "Số ngày tính loto về nhiều (VD: 7)"),
            ("GAN_DAYS", "Số ngày tính Lô Gan:", "Loto không về trong X ngày = Gan (VD: 15)"),
            ("HIGH_WIN_THRESHOLD", "Ngưỡng Cầu Tỷ Lệ Cao (%):", "Tỷ lệ K2N tối thiểu = 'Tỷ Lệ Cao' (VD: 47.0)"),
            ("K2N_RISK_START_THRESHOLD", "Ngưỡng Bắt đầu Phạt (khung):", "Phạt điểm nếu chuỗi thua > X (VD: 6)"),
            ("K2N_RISK_PENALTY_PER_FRAME", "Điểm Phạt Cố định:", "Trừ X điểm nếu vượt ngưỡng (VD: 1.0)"),
        ]
        
        for idx, (key, label, tooltip) in enumerate(other_settings):
            ttk.Label(other_frame, text=label).grid(row=idx, column=0, sticky="w", padx=5, pady=3)
            var = tk.StringVar(value=str(self.current_settings.get(key, "")))
            ttk.Entry(other_frame, textvariable=var, width=20).grid(row=idx, column=1, sticky="w", padx=5, pady=3)
            ttk.Label(other_frame, text=tooltip, foreground="#666", font=("Arial", 8, "italic")).grid(
                row=idx, column=2, sticky="w", padx=5, pady=3)
            self.entries[key] = var

    def create_bottom_buttons(self):
        """Tạo các nút ở dưới cùng của window"""
        button_frame = ttk.Frame(self.window)
        button_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        # Nút Lưu Cài đặt
        save_button = ttk.Button(
            button_frame, text="💾 Lưu Tất cả Cài đặt", command=self.save_all_settings
        )
        save_button.pack(side="left", padx=5, fill="x", expand=True)
        
        # Nút Nạp 756 Cầu Bạc Nhớ
        load_memory_button = ttk.Button(
            button_frame, text="📥 Nạp 756 Cầu Bạc Nhớ", command=self.load_756_memory_bridges
        )
        load_memory_button.pack(side="left", padx=5, fill="x", expand=True)

    def save_all_settings(self):
        """Lặp qua tất cả các ô Entry và lưu cài đặt (bao gồm dual-config)."""
        self.app.logger.log("Đang lưu cài đặt...")
        try:
            any_errors = False
            
            # Build lo_config and de_config from entries
            lo_config = {}
            de_config = {}
            
            # Process entries
            for key, entry_var in self.entries.items():
                new_value = entry_var.get()
                
                # Handle dual-config entries specially
                if key == 'lo_config_remove':
                    lo_config['remove_threshold'] = float(new_value)
                    continue
                elif key == 'lo_config_add':
                    lo_config['add_threshold'] = float(new_value)
                    continue
                elif key == 'de_config_remove':
                    de_config['remove_threshold'] = float(new_value)
                    continue
                elif key == 'de_config_add':
                    de_config['add_threshold'] = float(new_value)
                    continue
                
                # Regular settings
                success, message = SETTINGS.update_setting(key, new_value)
                if not success:
                    any_errors = True
                    self.app.logger.log(f"LỖI: {message}")
            
            # Save lo_config and de_config as nested dicts
            if lo_config:
                success, message = SETTINGS.update_setting('lo_config', lo_config)
                if not success:
                    any_errors = True
                    self.app.logger.log(f"LỖI lo_config: {message}")
                else:
                    self.app.logger.log(f"✅ Đã lưu lo_config: {lo_config}")
            
            if de_config:
                success, message = SETTINGS.update_setting('de_config', de_config)
                if not success:
                    any_errors = True
                    self.app.logger.log(f"LỖI de_config: {message}")
                else:
                    self.app.logger.log(f"✅ Đã lưu de_config: {de_config}")

            if any_errors:
                messagebox.showerror(
                    "Lỗi Lưu",
                    "Một số cài đặt có lỗi. Vui lòng kiểm tra log.",
                    parent=self.window,
                )
            else:
                self.app.logger.log("✅ Đã lưu tất cả cài đặt vào config.json.")
                messagebox.showinfo(
                    "Thành công",
                    "Đã lưu tất cả cài đặt thành công!\n\n"
                    "📋 Cập nhật:\n"
                    f"• Lo Config: Remove={lo_config.get('remove_threshold')}%, Add={lo_config.get('add_threshold')}%\n"
                    f"• De Config: Remove={de_config.get('remove_threshold')}%, Add={de_config.get('add_threshold')}%",
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
