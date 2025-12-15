# -*- coding: utf-8 -*-
"""
ui.ui_bridge_scanner
--------------------
Bridge Scanner UI for discovering and adding bridges to management.
Provides normalized bridge addition flow using service layer adapter.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import List, Tuple, Optional, Dict, Any

# Import service layer adapter
try:
    from lottery_service import add_managed_bridge_adapter, get_all_managed_bridges
except ImportError as e:
    logging.error(f"Failed to import lottery_service: {e}")
    # Fallback stubs
    def add_managed_bridge_adapter(bridge_name: str, description: str = "", **kwargs) -> Tuple[bool, str]:
        return False, "Service layer not available"
    
    def get_all_managed_bridges(db_name=None, only_enabled=False):
        return []


class BridgeScannerUI:
    """
    UI for scanning and adding bridges to management system.
    
    This class provides a user interface for:
    - Displaying discovered bridges
    - Selecting bridges to add to management
    - Normalizing bridge data before adding
    - Calling service layer for persistence
    """
    
    def __init__(self, parent_window: tk.Tk, app_context: Optional[Any] = None):
        """
        Initialize the Bridge Scanner UI.
        
        Args:
            parent_window: The parent tkinter window
            app_context: Optional application context for callbacks
        """
        self.parent = parent_window
        self.app = app_context
        self.logger = logging.getLogger(__name__)
        
        # Create top-level window
        self.window = tk.Toplevel(parent_window)
        self.window.title("Bridge Scanner")
        self.window.geometry("900x600")
        self.window.transient(parent_window)
        
        # Data storage
        self.scanned_bridges: List[Dict[str, Any]] = []
        self.selected_indices: List[int] = []
        
        # Build UI
        self._build_ui()
        
    def _build_ui(self):
        """Build the user interface components."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        title_label = ttk.Label(
            main_frame,
            text="Bridge Scanner - Discovered Bridges",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Treeview frame with scrollbar
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview for displaying bridges
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Name", "Type", "Description", "WinRate", "Status"),
            show="headings",
            selectmode="extended",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        
        # Configure scrollbars
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Define column headings
        self.tree.heading("Name", text="Bridge Name")
        self.tree.heading("Type", text="Type")
        self.tree.heading("Description", text="Description")
        self.tree.heading("WinRate", text="Win Rate")
        self.tree.heading("Status", text="Status")
        
        # Define column widths
        self.tree.column("Name", width=200)
        self.tree.column("Type", width=100)
        self.tree.column("Description", width=250)
        self.tree.column("WinRate", width=100)
        self.tree.column("Status", width=100)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))
        
        # Add selected button
        add_button = ttk.Button(
            button_frame,
            text="Add Selected to Management",
            command=self._add_selected_to_management
        )
        add_button.pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        refresh_button = ttk.Button(
            button_frame,
            text="Refresh Scan",
            command=self._refresh_scan
        )
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy
        )
        close_button.pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready", foreground="blue")
        self.status_label.pack(pady=(10, 0))
        
    def _normalize_selection_rows(self, selected_items: List[str]) -> List[Dict[str, str]]:
        """
        Normalize selected tree items into structured bridge data.
        
        This method extracts data from selected treeview items and normalizes
        it into a consistent dictionary format for service layer processing.
        
        Args:
            selected_items: List of treeview item IDs
            
        Returns:
            List of dictionaries containing normalized bridge data
            Each dict has keys: name, description, bridge_type, win_rate
        """
        normalized_rows = []
        
        for item_id in selected_items:
            try:
                # Get item values from treeview
                values = self.tree.item(item_id, "values")
                
                if not values or len(values) < 4:
                    self.logger.warning(f"Skipping item with insufficient data: {item_id}")
                    continue
                
                # Extract fields (Name, Type, Description, WinRate, Status)
                bridge_name = str(values[0]).strip() if values[0] else ""
                bridge_type = str(values[1]).strip() if values[1] else ""
                description = str(values[2]).strip() if values[2] else ""
                win_rate = str(values[3]).strip() if values[3] else ""
                
                # Validate required field
                if not bridge_name:
                    self.logger.warning(f"Skipping item with empty name: {item_id}")
                    continue
                
                # Create normalized dictionary
                normalized_row = {
                    "name": bridge_name,
                    "description": description,
                    "bridge_type": bridge_type,
                    "win_rate": win_rate if win_rate else None,
                }
                
                normalized_rows.append(normalized_row)
                self.logger.debug(f"Normalized row: {normalized_row}")
                
            except Exception as e:
                self.logger.error(f"Error normalizing row {item_id}: {e}", exc_info=True)
                continue
        
        return normalized_rows
    
    def _add_selected_to_management(self):
        """
        Add selected bridges to management using service layer adapter.
        
        This method:
        1. Gets selected items from treeview
        2. Normalizes the data
        3. Calls add_managed_bridge_adapter for each bridge
        4. Reports success/failure to user
        """
        # Get selected items
        selected_items = self.tree.selection()
        
        if not selected_items:
            messagebox.showwarning(
                "No Selection",
                "Please select at least one bridge to add."
            )
            return
        
        # Normalize selection
        self.logger.info(f"Processing {len(selected_items)} selected bridge(s)")
        normalized_rows = self._normalize_selection_rows(selected_items)
        
        if not normalized_rows:
            messagebox.showerror(
                "Normalization Error",
                "Could not normalize selected bridges. Please check the data."
            )
            return
        
        # Add each bridge using service adapter
        success_count = 0
        error_count = 0
        error_messages = []
        
        for row in normalized_rows:
            try:
                # Call service layer adapter
                success, message = add_managed_bridge_adapter(
                    bridge_name=row["name"],
                    description=row["description"],
                    bridge_type=row.get("bridge_type"),
                    win_rate=row.get("win_rate")
                )
                
                if success:
                    success_count += 1
                    self.logger.info(f"Successfully added bridge: {row['name']}")
                else:
                    error_count += 1
                    error_messages.append(f"{row['name']}: {message}")
                    self.logger.warning(f"Failed to add bridge {row['name']}: {message}")
                    
            except Exception as e:
                error_count += 1
                error_msg = f"{row['name']}: {str(e)}"
                error_messages.append(error_msg)
                self.logger.error(f"Exception adding bridge {row['name']}: {e}", exc_info=True)
        
        # Report results to user
        if error_count == 0:
            messagebox.showinfo(
                "Success",
                f"Successfully added {success_count} bridge(s) to management."
            )
            self.status_label.config(
                text=f"Added {success_count} bridge(s) successfully",
                foreground="green"
            )
        elif success_count == 0:
            messagebox.showerror(
                "Error",
                f"Failed to add all {error_count} bridge(s).\n\nErrors:\n" +
                "\n".join(error_messages[:5])  # Limit to first 5 errors
            )
            self.status_label.config(
                text=f"Failed to add {error_count} bridge(s)",
                foreground="red"
            )
        else:
            messagebox.showwarning(
                "Partial Success",
                f"Added {success_count} bridge(s), {error_count} failed.\n\nErrors:\n" +
                "\n".join(error_messages[:5])
            )
            self.status_label.config(
                text=f"Added {success_count}, {error_count} failed",
                foreground="orange"
            )
        
        # Refresh display if callback available
        if self.app and hasattr(self.app, 'refresh_bridge_list'):
            try:
                self.app.refresh_bridge_list()
            except Exception as e:
                self.logger.error(f"Error refreshing bridge list: {e}")
    
    def _refresh_scan(self):
        """Refresh the bridge scan (placeholder for actual scan logic)."""
        self.status_label.config(text="Refreshing scan...", foreground="blue")
        self.logger.info("Bridge scan refresh requested")
        
        # Clear current items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # This is a placeholder - actual scan logic would go here
        # For now, just show a message
        messagebox.showinfo(
            "Scan",
            "Bridge scanning functionality will be implemented here.\n"
            "This would typically call bridge discovery logic."
        )
        
        self.status_label.config(text="Ready", foreground="blue")
    
    def add_bridge_to_display(
        self,
        name: str,
        bridge_type: str = "",
        description: str = "",
        win_rate: str = "",
        status: str = "New"
    ):
        """
        Add a bridge to the display treeview.
        
        Args:
            name: Bridge name
            bridge_type: Bridge type classification
            description: Bridge description
            win_rate: Win rate percentage
            status: Status indicator
        """
        try:
            self.tree.insert(
                "",
                tk.END,
                values=(name, bridge_type, description, win_rate, status)
            )
            self.logger.debug(f"Added bridge to display: {name}")
        except Exception as e:
            self.logger.error(f"Error adding bridge to display: {e}", exc_info=True)
    
    def clear_display(self):
        """Clear all items from the display."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.logger.debug("Cleared bridge display")


# Export
__all__ = ["BridgeScannerUI"]
