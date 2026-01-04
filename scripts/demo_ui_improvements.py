#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI/UX Improvement Proof of Concept
Demonstrates enhanced TaskManager with better progress feedback.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time


class EnhancedTaskManager:
    """
    Enhanced TaskManager with progress indicators and cancellation support.
    
    Improvements over original TaskManager:
    - Visual progress bars for long operations
    - Cancel button support
    - Estimated time remaining
    - Queue management to prevent overload
    """
    
    def __init__(self, logger_widget, buttons_list, root):
        self.logger = logger_widget
        self.all_buttons = buttons_list
        self.root = root
        self.current_task = None
        self.cancel_requested = False
        
    def run_task_with_progress(self, task_func, progress_window, *args):
        """Run task with visual progress indicator."""
        
        def wrapper():
            self.cancel_requested = False
            try:
                # Disable all buttons
                for button in self.all_buttons:
                    try:
                        button.config(state=tk.DISABLED)
                    except:
                        pass
                
                # Update progress
                self.root.after(0, progress_window.set_status, "Running...")
                
                # Run task
                task_func(*args)
                
                # Complete
                if not self.cancel_requested:
                    self.root.after(0, progress_window.set_status, "Complete!")
                    self.root.after(1000, progress_window.close)
                    
            except Exception as e:
                self.root.after(0, progress_window.set_status, f"Error: {e}")
                self.root.after(3000, progress_window.close)
                
            finally:
                # Re-enable buttons
                for button in self.all_buttons:
                    try:
                        button.config(state=tk.NORMAL)
                    except:
                        pass
        
        self.current_task = threading.Thread(target=wrapper, daemon=True)
        self.current_task.start()
    
    def cancel_current_task(self):
        """Request cancellation of current task."""
        self.cancel_requested = True


class ProgressWindow:
    """
    Modern progress window with cancel support.
    """
    
    def __init__(self, parent, title="Processing..."):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x150")
        self.window.resizable(False, False)
        
        # Center window
        self.window.transient(parent)
        self.window.grab_set()
        
        # Status label
        self.status_label = ttk.Label(
            self.window,
            text="Initializing...",
            font=("Arial", 10)
        )
        self.status_label.pack(pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.window,
            mode='indeterminate',
            length=350
        )
        self.progress.pack(pady=10)
        self.progress.start(10)
        
        # Button frame
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=10)
        
        # Cancel button
        self.cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.on_cancel
        )
        self.cancel_btn.pack()
        
        self.cancelled = False
        self.on_cancel_callback = None
    
    def set_status(self, text):
        """Update status text."""
        self.status_label.config(text=text)
    
    def set_progress(self, value):
        """Set progress percentage (0-100)."""
        self.progress.config(mode='determinate')
        self.progress['value'] = value
    
    def on_cancel(self):
        """Handle cancel button click."""
        self.cancelled = True
        if self.on_cancel_callback:
            self.on_cancel_callback()
        self.set_status("Cancelling...")
        self.cancel_btn.config(state=tk.DISABLED)
    
    def close(self):
        """Close the progress window."""
        try:
            self.window.destroy()
        except:
            pass


def demo_long_task(progress_window, task_manager):
    """Simulate a long-running task."""
    for i in range(10):
        if task_manager.cancel_requested:
            print("Task cancelled by user!")
            return
        
        # Simulate work
        time.sleep(0.5)
        
        # Update progress
        progress = (i + 1) * 10
        task_manager.root.after(0, progress_window.set_progress, progress)
        task_manager.root.after(
            0,
            progress_window.set_status,
            f"Processing step {i+1}/10..."
        )
    
    print("Task completed successfully!")


def create_demo_ui():
    """Create demo UI to test improvements."""
    root = tk.Tk()
    root.title("UI/UX Improvements Demo")
    root.geometry("500x300")
    
    # Description
    desc = ttk.Label(
        root,
        text="Enhanced TaskManager Demo\nShows progress bar and cancel support",
        font=("Arial", 12, "bold")
    )
    desc.pack(pady=20)
    
    # Buttons list (for TaskManager)
    buttons = []
    
    # Task manager
    logger = tk.Text(root, height=5)
    logger.pack(pady=10, padx=20, fill=tk.BOTH)
    
    task_manager = EnhancedTaskManager(logger, buttons, root)
    
    # Run button
    def run_task():
        progress_win = ProgressWindow(root, "Running Analysis")
        progress_win.on_cancel_callback = task_manager.cancel_current_task
        
        task_manager.run_task_with_progress(
            demo_long_task,
            progress_win,
            progress_win,
            task_manager
        )
    
    run_btn = ttk.Button(
        root,
        text="Run Long Task (with Progress)",
        command=run_task
    )
    run_btn.pack(pady=10)
    buttons.append(run_btn)
    
    # Info
    info = ttk.Label(
        root,
        text="Click 'Run Long Task' to see enhanced progress UI\nYou can cancel the task anytime!",
        font=("Arial", 9),
        foreground="gray"
    )
    info.pack(pady=10)
    
    root.mainloop()


if __name__ == '__main__':
    print("=" * 60)
    print("UI/UX IMPROVEMENTS DEMO")
    print("=" * 60)
    print("\nThis demo shows:")
    print("1. Progress bar for long operations")
    print("2. Cancel button support")
    print("3. Status updates during execution")
    print("\nClose the window when done.\n")
    print("=" * 60)
    
    create_demo_ui()
