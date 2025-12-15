# ui/ui_bridge_scanner.py
"""
Bridge Scanner Tab - UI for scanning and adding bridges to management.

This module provides a UI interface for:
- Scanning bridges using various algorithms
- Displaying scan results
- Adding selected bridges to management with robust validation
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Any, Optional, Tuple

try:
    from lottery_service import upsert_managed_bridge
except ImportError:
    print("ERROR: Cannot import upsert_managed_bridge from lottery_service")
    
    def upsert_managed_bridge(name, desc, rate):
        """Fallback function"""
        return False, "lottery_service not available"


class BridgeScannerTab:
    """
    UI Tab for scanning bridges and adding them to management.
    
    Provides robust validation and normalization for bridge data.
    """
    
    def __init__(self, parent, logger=None):
        """
        Initialize the Bridge Scanner Tab.
        
        Args:
            parent: Parent tkinter widget
            logger: Optional logger instance for logging operations
        """
        self.parent = parent
        self.logger = logger
        self.scan_results = []  # Store scan results
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results display area
        self._create_results_area()
        
        # Action buttons
        self._create_action_buttons()
        
    def _create_results_area(self):
        """Create the results display area with treeview."""
        # Label
        label = ttk.Label(self.frame, text="Kết quả quét cầu:")
        label.pack(anchor=tk.W, pady=(0, 5))
        
        # Treeview for results
        columns = ("name", "type", "description", "rate", "streak")
        self.results_tree = ttk.Treeview(
            self.frame, 
            columns=columns, 
            show="headings",
            selectmode="extended"
        )
        
        # Configure columns
        self.results_tree.heading("name", text="Tên cầu")
        self.results_tree.heading("type", text="Loại")
        self.results_tree.heading("description", text="Mô tả")
        self.results_tree.heading("rate", text="Tỷ lệ")
        self.results_tree.heading("streak", text="Chuỗi")
        
        self.results_tree.column("name", width=200)
        self.results_tree.column("type", width=100)
        self.results_tree.column("description", width=250)
        self.results_tree.column("rate", width=80)
        self.results_tree.column("streak", width=80)
        
        # Scrollbars
        vsb = ttk.Scrollbar(self.frame, orient="vertical", command=self.results_tree.yview)
        hsb = ttk.Scrollbar(self.frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Pack
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
    def _create_action_buttons(self):
        """Create action buttons."""
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(pady=10)
        
        # Add selected bridges button
        add_btn = ttk.Button(
            button_frame,
            text="Thêm cầu đã chọn vào quản lý",
            command=self._add_selected_to_management
        )
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # Select all button
        select_all_btn = ttk.Button(
            button_frame,
            text="Chọn tất cả",
            command=self._select_all_results
        )
        select_all_btn.pack(side=tk.LEFT, padx=5)
        
    def _select_all_results(self):
        """Select all items in the results tree."""
        for item in self.results_tree.get_children():
            self.results_tree.selection_add(item)
    
    def _normalize_bridge_info(self, bridge: Any) -> Optional[Dict[str, Any]]:
        """
        Normalize bridge information from various input formats.
        
        Handles dict, object, tuple, list formats and validates required fields.
        
        Args:
            bridge: Bridge data in various formats
            
        Returns:
            Dict with normalized fields (name, type, description, rate, streak)
            or None if validation fails
        """
        normalized = {
            "name": None,
            "type": None,
            "description": None,
            "rate": None,
            "streak": None
        }
        
        # Extract name - priority order: normalized_name, name, first element
        if isinstance(bridge, dict):
            # Dict format
            normalized["name"] = (
                bridge.get("normalized_name") or 
                bridge.get("name") or 
                bridge.get("bridge_name")
            )
            normalized["type"] = bridge.get("type") or bridge.get("bridge_type")
            normalized["description"] = bridge.get("description") or bridge.get("desc")
            normalized["rate"] = bridge.get("rate") or bridge.get("win_rate")
            normalized["streak"] = bridge.get("streak") or bridge.get("current_streak")
            
        elif hasattr(bridge, '__dict__'):
            # Object format - has attributes
            normalized["name"] = (
                getattr(bridge, "normalized_name", None) or
                getattr(bridge, "name", None) or
                getattr(bridge, "bridge_name", None) or
                str(bridge)
            )
            normalized["type"] = (
                getattr(bridge, "type", None) or
                getattr(bridge, "bridge_type", None)
            )
            normalized["description"] = (
                getattr(bridge, "description", None) or
                getattr(bridge, "desc", None)
            )
            normalized["rate"] = (
                getattr(bridge, "rate", None) or
                getattr(bridge, "win_rate", None)
            )
            normalized["streak"] = (
                getattr(bridge, "streak", None) or
                getattr(bridge, "current_streak", None)
            )
            
        elif isinstance(bridge, (list, tuple)) and len(bridge) > 0:
            # List/tuple format - extract by index
            normalized["name"] = str(bridge[0]) if len(bridge) > 0 else None
            normalized["type"] = str(bridge[1]) if len(bridge) > 1 else None
            normalized["description"] = str(bridge[2]) if len(bridge) > 2 else None
            normalized["rate"] = bridge[3] if len(bridge) > 3 else None
            normalized["streak"] = bridge[4] if len(bridge) > 4 else None
            
        else:
            # Fallback - convert to string
            normalized["name"] = str(bridge) if bridge else None
        
        # Validate name
        if not normalized["name"]:
            return None
            
        normalized["name"] = str(normalized["name"]).strip()
        
        # Check for invalid name values
        if (not normalized["name"] or 
            normalized["name"] in ["", "N/A", "None", "null"] or
            normalized["name"].isspace()):
            return None
        
        # Validate and normalize type
        if normalized["type"]:
            normalized["type"] = str(normalized["type"]).strip()
            # Check against whitelist
            valid_types = ["LÔ_V17", "LÔ_BN", "LÔ_STL_FIXED", "ĐỀ", "MEMORY", "CLASSIC"]
            if normalized["type"] not in valid_types:
                # Allow but mark as unknown
                normalized["type"] = f"UNKNOWN_{normalized['type']}"
        else:
            normalized["type"] = "UNKNOWN"
        
        # Normalize description
        if not normalized["description"]:
            normalized["description"] = normalized["name"]
        else:
            normalized["description"] = str(normalized["description"]).strip()
        
        # Normalize rate
        if normalized["rate"] is not None:
            try:
                if isinstance(normalized["rate"], str):
                    # Remove % sign if present
                    rate_str = normalized["rate"].replace("%", "").strip()
                    normalized["rate"] = float(rate_str)
                else:
                    normalized["rate"] = float(normalized["rate"])
            except (ValueError, TypeError):
                normalized["rate"] = 0.0
        else:
            normalized["rate"] = 0.0
        
        # Normalize streak
        if normalized["streak"] is not None:
            try:
                normalized["streak"] = int(normalized["streak"])
            except (ValueError, TypeError):
                normalized["streak"] = 0
        else:
            normalized["streak"] = 0
            
        return normalized
    
    def _add_selected_to_management(self):
        """
        Add selected bridges to management with robust validation.
        
        This method:
        1. Gets selected items from the results tree
        2. Normalizes and validates each bridge's data
        3. Attempts to add valid bridges to management via upsert_managed_bridge
        4. Collects and displays errors for invalid bridges
        5. Shows summary of success/failures
        """
        # Get selected items
        selected_items = self.results_tree.selection()
        
        if not selected_items:
            messagebox.showwarning(
                "Không có lựa chọn",
                "Vui lòng chọn ít nhất một cầu để thêm vào quản lý.",
                parent=self.parent
            )
            return
        
        # Track results
        success_count = 0
        error_list = []
        log_entries = []
        
        # Process each selected item
        for item_id in selected_items:
            try:
                # Get item values from treeview
                item_values = self.results_tree.item(item_id)["values"]
                
                # Create bridge dict from treeview values
                # Columns: name, type, description, rate, streak
                if not item_values or len(item_values) < 5:
                    error_list.append(f"- Cầu (ID: {item_id}): Dữ liệu không đầy đủ")
                    log_entries.append(f"[ERROR] Item {item_id}: Insufficient data")
                    continue
                
                bridge_data = {
                    "name": item_values[0],
                    "type": item_values[1],
                    "description": item_values[2],
                    "rate": item_values[3],
                    "streak": item_values[4]
                }
                
                # Normalize and validate bridge info
                normalized = self._normalize_bridge_info(bridge_data)
                
                if not normalized:
                    error_msg = f"- Cầu '{bridge_data.get('name', 'UNKNOWN')}': Tên không hợp lệ hoặc thiếu thông tin"
                    error_list.append(error_msg)
                    log_entries.append(f"[ERROR] Bridge normalization failed: {bridge_data}")
                    continue
                
                # Additional validation checks
                bridge_name = normalized["name"]
                bridge_type = normalized["type"]
                bridge_desc = normalized["description"]
                bridge_rate = normalized["rate"]
                
                # Check if type is unknown/invalid
                if bridge_type.startswith("UNKNOWN"):
                    error_msg = f"- Cầu '{bridge_name}': Loại không xác định ('{bridge_type}')"
                    error_list.append(error_msg)
                    log_entries.append(f"[WARNING] Bridge '{bridge_name}': Unknown type '{bridge_type}'")
                    # Don't skip, but log warning
                
                # Format rate for display
                rate_text = f"{bridge_rate:.2f}%" if bridge_rate > 0 else "0%"
                
                # Attempt to add to management
                try:
                    success, message = upsert_managed_bridge(
                        bridge_name,
                        bridge_desc,
                        rate_text
                    )
                    
                    if success:
                        success_count += 1
                        log_entries.append(f"[SUCCESS] Added bridge '{bridge_name}': {message}")
                    else:
                        error_msg = f"- Cầu '{bridge_name}': {message}"
                        error_list.append(error_msg)
                        log_entries.append(f"[ERROR] Failed to add bridge '{bridge_name}': {message}")
                        
                except Exception as e_upsert:
                    error_msg = f"- Cầu '{bridge_name}': Lỗi khi thêm vào DB ({str(e_upsert)})"
                    error_list.append(error_msg)
                    log_entries.append(f"[EXCEPTION] Bridge '{bridge_name}': {str(e_upsert)}")
                    
            except Exception as e_item:
                error_msg = f"- Lỗi xử lý item {item_id}: {str(e_item)}"
                error_list.append(error_msg)
                log_entries.append(f"[EXCEPTION] Processing item {item_id}: {str(e_item)}")
        
        # Log all entries if logger available
        if self.logger:
            for entry in log_entries:
                self.logger.log(entry)
        
        # Prepare and show result message
        total_selected = len(selected_items)
        failed_count = len(error_list)
        
        if success_count == total_selected:
            # All successful
            messagebox.showinfo(
                "Thành công",
                f"Đã thêm thành công {success_count} cầu vào quản lý.",
                parent=self.parent
            )
        elif success_count > 0:
            # Partial success
            message_parts = [
                f"Đã thêm thành công {success_count}/{total_selected} cầu.",
                f"\nCó {failed_count} cầu bị bỏ qua do lỗi:\n"
            ]
            
            # Add error details (limit to first 10 errors)
            error_display = error_list[:10]
            message_parts.append("\n".join(error_display))
            
            if failed_count > 10:
                message_parts.append(f"\n... và {failed_count - 10} lỗi khác.")
            
            messagebox.showwarning(
                "Hoàn thành có lỗi",
                "".join(message_parts),
                parent=self.parent
            )
        else:
            # All failed
            message_parts = [
                f"Không thể thêm cầu nào. Tất cả {total_selected} cầu đều bị lỗi:\n\n"
            ]
            
            # Add error details (limit to first 10 errors)
            error_display = error_list[:10]
            message_parts.append("\n".join(error_display))
            
            if failed_count > 10:
                message_parts.append(f"\n... và {failed_count - 10} lỗi khác.")
            
            messagebox.showerror(
                "Lỗi",
                "".join(message_parts),
                parent=self.parent
            )
    
    def load_scan_results(self, results: List[Any]):
        """
        Load scan results into the treeview.
        
        Args:
            results: List of bridge data in various formats
        """
        # Clear existing items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.scan_results = results
        
        # Add results to treeview
        for bridge in results:
            normalized = self._normalize_bridge_info(bridge)
            
            if normalized:
                self.results_tree.insert(
                    "",
                    tk.END,
                    values=(
                        normalized["name"],
                        normalized["type"],
                        normalized["description"],
                        f"{normalized['rate']:.2f}%" if normalized["rate"] > 0 else "0%",
                        normalized["streak"]
                    )
                )


# Module-level test helper
if __name__ == "__main__":
    """Simple test of the BridgeScannerTab class."""
    root = tk.Tk()
    root.title("Bridge Scanner Test")
    root.geometry("900x600")
    
    # Create mock logger
    class MockLogger:
        def log(self, message):
            print(f"[LOG] {message}")
    
    # Create scanner tab
    scanner = BridgeScannerTab(root, logger=MockLogger())
    
    # Load test data
    test_results = [
        {"name": "Test Bridge 1", "type": "LÔ_V17", "description": "Test 1", "rate": 45.5, "streak": 3},
        {"name": "Test Bridge 2", "type": "LÔ_BN", "description": "Test 2", "rate": 50.0, "streak": 5},
        {"name": "", "type": "LÔ_V17", "description": "Invalid", "rate": 0, "streak": 0},  # Invalid - empty name
        ("Test Bridge 3", "ĐỀ", "Test 3", 60.0, 2),  # Tuple format
        None,  # Invalid - None
    ]
    
    scanner.load_scan_results(test_results)
    
    root.mainloop()
