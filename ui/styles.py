# ui/styles.py
"""
Theme Engine for Xổ Số Data Analysis App.
Centralizes all colors, fonts, and layout configurations.
"""

class ThemeColor:
    # Primary Colors
    PRIMARY = "#007AFF"          # Blue (iOS-like)
    PRIMARY_DARK = "#0056b3"
    SECONDARY = "#5856D6"        # Purple
    
    # Backgrounds
    BG_MAIN = "#F5F5F7"          # Light Gray (Apple-like)
    BG_WHITE = "#FFFFFF"
    BG_SIDEBAR = "#E8E8ED"
    
    # Text
    TEXT_MAIN = "#1D1D1F"
    TEXT_SECONDARY = "#86868B"
    TEXT_WHITE = "#FFFFFF"
    
    # Status
    SUCCESS = "#34C759"          # Green
    WARNING = "#FF9500"          # Orange
    ERROR = "#FF3B30"            # Red
    INFO = "#5AC8FA"             # Light Blue
    
    # Borders & Separators
    BORDER = "#D1D1D6"
    SEPARATOR = "#E5E5EA"

class AppFont:
    # Font Families
    MAIN = "Segoe UI"  # Windows Standard
    MONO = "Consolas"
    
    # Font Configs (Family, Size, Weight)
    TITLE_LARGE = (MAIN, 16, "bold")
    TITLE_NORMAL = (MAIN, 12, "bold")
    BODY_NORMAL = (MAIN, 10, "normal")
    BODY_BOLD = (MAIN, 10, "bold")
    SMALL = (MAIN, 9, "normal")
    TINY = (MAIN, 8, "normal")
    
    TABLE_HEADER = (MAIN, 9, "bold")
    TABLE_ROW = (MAIN, 9, "normal")

class LayoutConfig:
    # Padding
    PAD_XS = 2
    PAD_S = 5
    PAD_M = 10
    PAD_L = 20
    PAD_XL = 30
    
    # Dimensions
    BTN_HEIGHT = 30
    SIDEBAR_WIDTH = 250
    CORNER_RADIUS = 8
