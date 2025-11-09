import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Import các hàm logic cần thiết
try:
    from lottery_service import (
        get_all_managed_bridges, 
        add_managed_bridge, 
        update_managed_bridge, 
        delete_managed_bridge
    )
except ImportError:
    print("LỖI: ui_bridge_manager.py không thể import lottery_service.")
    # Hàm giả
    def get_all_managed_bridges(): return []
    def add_managed_bridge(n, d, w): return False, "Lỗi"
    def update_managed_bridge(i, d, s): return False, "Lỗi"
    def delete_managed_bridge(i): return False, "Lỗi"


class BridgeManagerWindow:
    """Quản lý cửa sổ Toplevel Quản lý Cầu."""

    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.all_bridges_cache = [] # Cache
        
        if hasattr(self.app, 'bridge_manager_window') and self.app.bridge_manager_window and self.app.bridge_manager_window.winfo_exists():
            self.app.bridge_manager_window.lift()
            return
            
        self.app.update_output("Đang mở cửa sổ Quản lý Cầu...")
        
        self.window = tk.Toplevel(self.root)
        self.app.bridge_manager_window = self.window # Gán lại vào app chính
        self.window.title("Quản lý Cầu Đã Lưu (Cache K2N)")
        self.window.geometry("1000x500") # (MỚI GĐ 4) Tăng chiều rộng

        manager_frame = ttk.Frame(self.window, padding="10")
        manager_frame.pack(expand=True, fill=tk.BOTH)
        manager_frame.rowconfigure(0, weight=1)
        manager_frame.columnconfigure(0, weight=3)
        manager_frame.columnconfigure(1, weight=2)

        # --- Khung trái (Treeview) ---
        tree_frame = ttk.Frame(manager_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # (SỬA GĐ 4) Thêm cột 'max_lose'
        cols = ('id', 'name', 'rate', 'streak', 'max_lose', 'next_pred', 'status')
        self.tree = ttk.Treeview(tree_frame, 
                                 columns=cols, 
                                 show="headings", 
                                 yscrollcommand=tree_scroll_y.set)
        tree_scroll_y.config(command=self.tree.yview)
        
        self.tree.heading('id', text='ID')
        self.tree.column('id', width=40, anchor=tk.W)
        self.tree.heading('name', text='Tên Cầu')
        self.tree.column('name', width=200, anchor=tk.W)
        
        self.tree.heading('rate', text='Tỷ lệ (K2N)')
        self.tree.column('rate', width=80, anchor=tk.W)
        self.tree.heading('streak', text='Chuỗi Thắng')
        self.tree.column('streak', width=80, anchor=tk.W)
        
        # (MỚI GĐ 4) Thêm cột Chuỗi Thua Max
        self.tree.heading('max_lose', text='Thua Max (K2N)')
        self.tree.column('max_lose', width=90, anchor=tk.W)
        
        self.tree.heading('next_pred', text='Dự đoán')
        self.tree.column('next_pred', width=100, anchor=tk.W)
        self.tree.heading('status', text='Trạng thái')
        self.tree.column('status', width=80, anchor=tk.W)
        
        self.tree.pack(expand=True, fill=tk.BOTH)
        
        self.tree.tag_configure('disabled', foreground='gray')
        self.tree.tag_configure('enabled', foreground='black')
        self.tree.tag_configure('pending_n2', background='#FFFFE0') 
        self.tree.tag_configure('high_risk', foreground='red') # (MỚI GĐ 4)
        
        # Gán treeview vào app chính để hàm _save_bridge... có thể gọi
        self.app.bridge_manager_tree = self.tree

        # --- Khung phải (Edit/Add) ---
        edit_frame = ttk.Labelframe(manager_frame, text="Chi tiết", padding="10")
        edit_frame.grid(row=0, column=1, sticky="nsew")
        edit_frame.columnconfigure(1, weight=1)

        ttk.Label(edit_frame, text="Tên Cầu:").grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        self.name_entry = ttk.Entry(edit_frame)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(edit_frame, text="Mô tả:").grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        self.desc_entry = ttk.Entry(edit_frame)
        self.desc_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        self.status_label = ttk.Label(edit_frame, text="Trạng thái: N/A", font=('TkDefaultFont', 9, 'bold'))
        self.status_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=10)

        # Frame cho các nút
        button_frame_edit = ttk.Frame(edit_frame)
        button_frame_edit.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        button_frame_edit.columnconfigure(0, weight=1)
        button_frame_edit.columnconfigure(1, weight=1)
        
        add_button = ttk.Button(button_frame_edit, text="Thêm Cầu Mới", 
                                command=self.add_new_bridge)
        add_button.grid(row=0, column=0, sticky="ew", padx=2)
        
        update_button = ttk.Button(button_frame_edit, text="Cập nhật Mô tả", 
                                   command=self.update_selected_bridge)
        update_button.grid(row=0, column=1, sticky="ew", padx=2)

        toggle_button = ttk.Button(button_frame_edit, text="Bật / Tắt Cầu", 
                                   command=self.toggle_bridge_status)
        toggle_button.grid(row=1, column=0, sticky="ew", padx=2, pady=5)
        
        delete_button = ttk.Button(button_frame_edit, text="XÓA Cầu Đã Chọn", 
                                   command=self.delete_selected_bridge)
        delete_button.grid(row=1, column=1, sticky="ew", padx=2, pady=5)
        
        update_rates_button = ttk.Button(edit_frame, text="Cập nhật Cache K2N Toàn bộ Cầu", 
                                         command=self.run_update_all_k2n_cache)
        update_rates_button.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=(15, 5))


        # --- Logic cho cửa sổ Quản lý ---
        self.tree.bind("<<TreeviewSelect>>", self.on_bridge_select)
        self.refresh_bridge_list()
        
    def refresh_bridge_list(self):
        """(SỬA GĐ 4) Tải lại dữ liệu cho Treeview Quản lý Cầu (cache K2N + Max Lose)."""
        if not self.tree: return
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.all_bridges_cache = get_all_managed_bridges()
        for bridge in self.all_bridges_cache:
            status_text = "Đang Bật" if bridge['is_enabled'] == 1 else "Đã Tắt"
            tag = 'enabled' if bridge['is_enabled'] == 1 else 'disabled'
            
            # (SỬA GĐ 4) Lấy dữ liệu cache
            rate = bridge.get('win_rate_text') or "N/A"
            streak = bridge.get('current_streak') or 0
            max_lose = bridge.get('max_lose_streak_k2n') or 0 # (MỚI GĐ 4)
            prediction = bridge.get('next_prediction_stl') or "N/A"
            
            tags = [tag]
            if "N2" in str(prediction):
                tags.append('pending_n2')
            if max_lose >= 5: # (MỚI GĐ 4) Cảnh báo rủi ro
                tags.append('high_risk')
            
            self.tree.insert("", tk.END, values=(
                bridge['id'],
                bridge['name'],
                rate,
                f"{streak} thắng", # (SỬA GĐ 4) Rõ nghĩa hơn
                f"{max_lose} thua", # (MỚI GĐ 4)
                prediction,
                status_text
            ), tags=tuple(tags))
            
        self.app.update_output(f"Đã làm mới danh sách Quản lý Cầu (tìm thấy {len(self.all_bridges_cache)} cầu).")
        
    def get_selected_bridge_info(self):
        """Helper: Lấy id và dữ liệu của cầu đang chọn."""
        if not self.tree: return None, None
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn một cầu từ danh sách.", parent=self.window)
            return None, None
        
        item = self.tree.item(selected_item)
        bridge_id = item['values'][0]
        
        for bridge_data in self.all_bridges_cache:
            if bridge_data['id'] == bridge_id:
                return bridge_id, bridge_data
        return None, None

    def add_new_bridge(self):
        """Logic nút 'Thêm Cầu Mới' (Thủ công)."""
        bridge_name = self.name_entry.get().strip()
        description = self.desc_entry.get().strip()
        if not bridge_name:
            messagebox.showwarning("Thiếu tên", "Tên cầu không được để trống.", parent=self.window)
            return
            
        success, message = add_managed_bridge(bridge_name, description, "Tự thêm")
        if success:
            self.app.update_output(message)
            self.refresh_bridge_list()
            self.name_entry.config(state=tk.NORMAL)
            self.name_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
        else:
            self.app.update_output(f"LỖI: {message}")
            messagebox.showerror("Lỗi", message, parent=self.window)

    def update_selected_bridge(self):
        """Logic nút 'Cập nhật Mô tả'."""
        bridge_id, bridge_data = self.get_selected_bridge_info()
        if not bridge_id: return
        
        new_description = self.desc_entry.get().strip()
        success, message = update_managed_bridge(bridge_id, new_description, bridge_data['is_enabled'])
        if success:
            self.app.update_output(f"Đã cập nhật mô tả cho cầu ID {bridge_id}.")
            self.refresh_bridge_list()
        else:
            self.app.update_output(f"LỖI: {message}")
            messagebox.showerror("Lỗi", message, parent=self.window)

    def toggle_bridge_status(self):
        """Logic nút 'Bật / Tắt Cầu'."""
        bridge_id, bridge_data = self.get_selected_bridge_info()
        if not bridge_id: return
        
        new_status = 0 if bridge_data['is_enabled'] == 1 else 1
        success, message = update_managed_bridge(bridge_id, bridge_data['description'], new_status)
        if success:
            self.app.update_output(f"Đã {'BẬT' if new_status==1 else 'TẮT'} cầu ID {bridge_id}.")
            self.refresh_bridge_list()
        else:
            self.app.update_output(f"LỖI: {message}")
            messagebox.showerror("Lỗi", message, parent=self.window)

    def delete_selected_bridge(self):
        """Logic nút 'XÓA Cầu'."""
        bridge_id, bridge_data = self.get_selected_bridge_info()
        if not bridge_id: return
        
        if not messagebox.askyesno("Xác nhận Xóa", 
                                   f"Bạn có chắc chắn muốn XÓA vĩnh viễn cầu:\n{bridge_data['name']}\n\nThao tác này không thể hoàn tác.",
                                   parent=self.window):
            return
            
        success, message = delete_managed_bridge(bridge_id)
        if success:
            self.app.update_output(f"Đã XÓA cầu ID {bridge_id}.")
            self.refresh_bridge_list()
        else:
            self.app.update_output(f"LỖI: {message}")
            messagebox.showerror("Lỗi", message, parent=self.window)

    def on_bridge_select(self, event):
        """(SỬA GĐ 4) Khi chọn cầu trong Treeview."""
        selected_item = self.tree.focus()
        if not selected_item: return
        item = self.tree.item(selected_item)
        values = item['values']
        
        bridge_id, bridge_data = self.get_selected_bridge_info()
        if not bridge_data:
            return

        self.name_entry.config(state=tk.NORMAL)
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, values[1]) # Tên Cầu
        self.name_entry.config(state=tk.DISABLED)
        
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, bridge_data.get('description', '')) 
        
        self.status_label.config(text=f"Trạng thái: {values[6]}") # (SỬA GĐ 4) Index 6 (Status)
        
    # (SỬA LỖI) GỌI ĐÚNG TÊN HÀM
    def run_update_all_k2n_cache(self):
        """Gọi hàm chạy K2N cache đa luồng từ app chính."""
        self.app.run_update_all_bridge_K2N_cache_from_main()