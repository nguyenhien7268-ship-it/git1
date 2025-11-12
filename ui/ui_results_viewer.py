import tkinter as tk
from tkinter import ttk

class ResultsViewerWindow:
    """Quản lý cửa sổ Toplevel hiển thị kết quả backtest (Treeview) - VIEW."""
    
    def __init__(self, app, title, results_data, show_save_button=False):
        self.app = app  # Tham chiếu đến DataAnalysisApp chính
        self.root = app.root
        
        if not results_data:
            # SỬA: Thay thế update_output bằng logger.log
            self.app.logger.log(f"Lỗi: Không có kết quả để hiển thị cho {title}.")
            return

        self.window = tk.Toplevel(self.root)
        self.window.title(title)
        self.window.geometry("1000x600")

        frame = ttk.Frame(self.window, padding="5")
        frame.pack(expand=True, fill=tk.BOTH)

        headers = results_data[0]
        num_cols = len(headers)
        
        self.tree = ttk.Treeview(frame, columns=headers, show="headings")
        
        yscroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        copy_button = ttk.Button(button_frame, text="Copy Toàn Bộ Bảng (dán vào Excel)", 
                                 command=lambda: self.copy_all_to_clipboard(results_data))
        copy_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        if show_save_button:
            save_button = ttk.Button(button_frame, text="Lưu Cầu Đã Chọn...", 
                                     command=self.save_selected_bridge)
            save_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10,0))
        
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        
        for col in headers:
            self.tree.heading(col, text=col)
            if col == headers[0]:
                self.tree.column(col, width=150, anchor=tk.W)
            elif "Chuỗi K2N" in col:
                self.tree.column(col, width=150, anchor=tk.W)
            else:
                self.tree.column(col, width=120, anchor=tk.W)

        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.show_save_button = show_save_button
        
        self.tree.bind("<Button-3>", self.on_right_click)
        self.tree.bind("<Button-2>", self.on_right_click)
        
        self.tree.tag_configure('rate_row', background='lightyellow', font=('TkDefaultFont', 9, 'bold'))
        self.tree.tag_configure('streak_row', background='#E8F0E0', font=('TkDefaultFont', 9, 'bold'))
        self.tree.tag_configure('header_row', background='lightgray', font=('TkDefaultFont', 9, 'bold'))
        self.tree.tag_configure('final_row', background='#E0E8F0', font=('TkDefaultFont', 9, 'bold'))
            
        for i, row in enumerate(results_data[1:]):
            if len(row) < num_cols:
                row.extend([""] * (num_cols - len(row)))
            elif len(row) > num_cols:
                row = row[:num_cols]
            
            tags_to_apply = ()
            if i == 0 and ("Tỷ Lệ %" in str(row[0])):
                tags_to_apply = ('rate_row',)
            elif i == 1 and ("Chuỗi K2N" in str(row[0])):
                tags_to_apply = ('streak_row',)
            elif i == 0 and "Hạng" in str(row[0]):
                 tags_to_apply = ('header_row',)
            elif i == 2 and (str(row[0]).startswith("Kỳ") or str(row[0]).startswith("(Chờ Kỳ)")):
                 tags_to_apply = ('final_row',)
            
            self.tree.insert("", tk.END, values=row, tags=tags_to_apply)

        self.tree.pack(expand=True, fill=tk.BOTH)

    def copy_all_to_clipboard(self, data):
        """[VIEW UTILITY] Copy dữ liệu bảng."""
        try:
            tsv_string = ""
            for row in data:
                tsv_string += "\t".join(map(str, row)) + "\n"
            self.root.clipboard_clear()
            self.root.clipboard_append(tsv_string)
            self.app.logger.log(f"Đã copy {len(data)} hàng vào clipboard (dạng TSV).")
        except Exception as e:
            self.app.logger.log(f"Lỗi khi copy toàn bộ: {e}")

    def on_right_click(self, event):
        """[VIEW ACTION] Menu chuột phải."""
        try:
            item_id = self.tree.identify_row(event.y)
            column_id = self.tree.identify_column(event.x)
            if not item_id: return
            col_index = int(column_id.replace('#', '')) - 1
            if col_index < 0: return
            cell_value = self.tree.item(item_id, 'values')[col_index]

            self.context_menu.delete(0, 'end')
            
            def copy_cell_to_clipboard():
                self.root.clipboard_clear()
                self.root.clipboard_append(cell_value)
                self.app.logger.log(f"Đã copy: {cell_value}")

            self.context_menu.add_command(label=f"Copy '{cell_value}'", command=copy_cell_to_clipboard)
            
            if self.show_save_button:
                self.context_menu.add_separator()
                self.context_menu.add_command(label="Lưu cầu này...", command=self.save_selected_bridge)
            
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            self.app.logger.log(f"Lỗi menu chuột phải: {e}")
            
    def save_selected_bridge(self):
        """[VIEW ACTION] Ủy quyền cho View chính để khởi tạo lưu cầu."""
        # Gọi lại hàm _save_bridge_from_treeview của app chính (đã được refactor)
        self.app._save_bridge_from_treeview(self.tree)