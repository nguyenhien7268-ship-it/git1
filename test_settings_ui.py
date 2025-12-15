#!/usr/bin/env python3
"""
Test script to display the new Settings UI with tabs
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the settings window
from ui.ui_settings import SettingsWindow

class MockApp:
    """Mock app for testing"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Test Settings UI")
        self.root.geometry("800x700")
        
        # Mock logger
        class MockLogger:
            def log(self, msg):
                print(f"[LOG] {msg}")
        
        self.logger = MockLogger()
        self.settings_window = None
        
        # Create button to open settings
        btn = ttk.Button(
            self.root, 
            text="Open Settings Window",
            command=self.open_settings
        )
        btn.pack(pady=20)
        
    def open_settings(self):
        """Open settings window"""
        SettingsWindow(self)
    
    def run(self):
        """Run the app"""
        self.root.mainloop()

if __name__ == "__main__":
    print("Starting Settings UI Test...")
    app = MockApp()
    app.run()
