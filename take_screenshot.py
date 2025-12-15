#!/usr/bin/env python3
"""
Script to take screenshots of the Settings UI tabs
"""
import tkinter as tk
from tkinter import ttk
import sys
import os
from PIL import ImageGrab, Image
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the settings window
from ui.ui_settings import SettingsWindow

class ScreenshotApp:
    """App for taking screenshots"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Settings UI Screenshots")
        self.root.withdraw()  # Hide main window
        
        # Mock logger
        class MockLogger:
            def log(self, msg):
                print(f"[LOG] {msg}")
        
        self.logger = MockLogger()
        self.settings_window = None
        self.screenshot_count = 0
        
        # Open settings immediately
        self.root.after(500, self.open_and_capture)
        
    def open_and_capture(self):
        """Open settings and capture screenshots"""
        try:
            # Create settings window
            settings = SettingsWindow(self)
            window = settings.window
            
            # Wait for window to render
            window.update()
            time.sleep(0.5)
            
            # Get window geometry
            window.update_idletasks()
            x = window.winfo_rootx()
            y = window.winfo_rooty()
            w = window.winfo_width()
            h = window.winfo_height()
            
            print(f"Window geometry: {x}, {y}, {w}, {h}")
            
            # Capture Tab 1 (Lo/De Management)
            settings.notebook.select(0)
            window.update()
            time.sleep(0.3)
            self.capture_window(window, "tab1_lo_de_management.png")
            
            # Capture Tab 2 (AI Config)
            settings.notebook.select(1)
            window.update()
            time.sleep(0.3)
            self.capture_window(window, "tab2_ai_config.png")
            
            # Capture Tab 3 (Performance)
            settings.notebook.select(2)
            window.update()
            time.sleep(0.3)
            self.capture_window(window, "tab3_performance.png")
            
            print("\n✅ Screenshots captured successfully!")
            print("Files saved in current directory:")
            print("  - tab1_lo_de_management.png")
            print("  - tab2_ai_config.png")
            print("  - tab3_performance.png")
            
            # Close after capturing
            self.root.after(500, self.root.destroy)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            self.root.destroy()
    
    def capture_window(self, window, filename):
        """Capture a window screenshot"""
        try:
            window.update()
            x = window.winfo_rootx()
            y = window.winfo_rooty()
            w = window.winfo_width()
            h = window.winfo_height()
            
            # Take screenshot
            bbox = (x, y, x + w, y + h)
            img = ImageGrab.grab(bbox)
            img.save(filename)
            print(f"📸 Captured: {filename}")
            self.screenshot_count += 1
            
        except Exception as e:
            print(f"❌ Failed to capture {filename}: {e}")
    
    def run(self):
        """Run the app"""
        self.root.mainloop()

if __name__ == "__main__":
    print("Starting screenshot capture...")
    app = ScreenshotApp()
    app.run()
