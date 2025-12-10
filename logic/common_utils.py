"""
logic/common_utils.py

Common utility functions used across multiple modules.
Contains: validation helpers, date/time utilities, shared helper functions.

Created during Phase 1 refactoring to reduce code duplication.
V11.2: Enhanced with retry decorator and timestamp helpers for K1N-primary flow.
"""

import re
import time
import functools
import sqlite3
from datetime import datetime
from typing import Any, List, Optional, Tuple, Callable


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def is_valid_loto(loto: str) -> bool:
    """
    Validate if a string is a valid 2-digit loto number.

    Args:
        loto: String to validate

    Returns:
        True if valid loto (2 digits, 00-99), False otherwise

    Examples:
        >>> is_valid_loto("05")
        True
        >>> is_valid_loto("99")
        True
        >>> is_valid_loto("123")
        False
        >>> is_valid_loto("ab")
        False
    """
    if not isinstance(loto, str):
        return False
    return bool(re.match(r'^\d{2}$', loto))


def is_valid_ky(ky: Any) -> bool:
    """
    Validate if a value is a valid ky (period) number.

    Args:
        ky: Value to validate (can be string or int)

    Returns:
        True if valid ky (positive integer), False otherwise

    Examples:
        >>> is_valid_ky(1)
        True
        >>> is_valid_ky("123")
        True
        >>> is_valid_ky(0)
        False
        >>> is_valid_ky(-5)
        False
        >>> is_valid_ky("abc")
        False
    """
    try:
        ky_int = int(ky)
        return ky_int > 0
    except (ValueError, TypeError):
        return False


def validate_row_range(start_row: int, end_row: int, data_length: int) -> Tuple[bool, Optional[str]]:
    """
    Validate backtest row range parameters.

    Args:
        start_row: Starting row index (1-based)
        end_row: Ending row index (1-based)
        data_length: Total length of data

    Returns:
        Tuple of (is_valid, error_message)
        If valid: (True, None)
        If invalid: (False, error_message)

    Examples:
        >>> validate_row_range(1, 10, 20)
        (True, None)
        >>> validate_row_range(10, 5, 20)
        (False, "Start row must be less than or equal to end row")
        >>> validate_row_range(0, 10, 20)
        (False, "Start row must be greater than 0")
    """
    if start_row <= 0:
        return False, "Start row must be greater than 0"

    if start_row > end_row:
        return False, "Start row must be less than or equal to end row"

    if end_row > data_length:
        return False, f"End row ({end_row}) exceeds data length ({data_length})"

    if start_row > data_length:
        return False, f"Start row ({start_row}) exceeds data length ({data_length})"

    return True, None


def validate_backtest_params(toan_bo_A_I: List, ky_bat_dau_kiem_tra: Any, ky_ket_thuc_kiem_tra: Any) -> Tuple[Optional[List], Optional[int], Optional[int], Optional[int], Optional[List]]:
    """
    Validate backtest parameters and return processed values.
    (Moved from backtester_helpers.py)

    Args:
        toan_bo_A_I: Complete data list
        ky_bat_dau_kiem_tra: Starting period for testing
        ky_ket_thuc_kiem_tra: Ending period for testing

    Returns:
        tuple: (allData, finalEndRow, startCheckRow, offset, error_list)
               If error_list is not None, other values will be None.
    """
    if not all([toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra]):
        return None, None, None, None, [["LỖI:", "Cần đủ tham số."]]

    try:
        startRow, endRow = int(ky_bat_dau_kiem_tra), int(ky_ket_thuc_kiem_tra)
    except ValueError:
        return None, None, None, None, [["LỖI:", "Kỳ BĐ/KT phải là số."]]

    if not (startRow > 1 and startRow <= endRow):
        return None, None, None, None, [["LỖI:", "Kỳ BĐ/KT không hợp lệ."]]

    allData = toan_bo_A_I
    finalEndRow = min(endRow, len(allData) + startRow - 1)
    startCheckRow = startRow + 1

    if startCheckRow > finalEndRow:
        return None, None, None, None, [["LỖI:", "Dữ liệu không đủ để chạy."]]

    offset = startRow
    return allData, finalEndRow, startCheckRow, offset, None


# =============================================================================
# DATE/TIME UTILITIES
# =============================================================================

def parse_date_string(date_str: str, default_year: Optional[int] = None) -> Optional[datetime]:
    """
    Parse date string from multiple formats.

    Supports:
    - DD/MM/YYYY (Vietnamese format)
    - DD-MM-YYYY
    - DD-MM HH:MM:SS (with auto year)

    Args:
        date_str: Date string to parse
        default_year: Year to use if not in string (defaults to current year)

    Returns:
        datetime object if successful, None if failed

    Examples:
        >>> parse_date_string("25/12/2024")
        datetime.datetime(2024, 12, 25, 0, 0)
        >>> parse_date_string("25-12-2024")
        datetime.datetime(2024, 12, 25, 0, 0)
    """
    if not date_str:
        return None

    date_str = str(date_str).strip()
    if default_year is None:
        default_year = datetime.now().year

    # Try format 1: DD/MM/YYYY
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        pass

    # Try format 2: DD-MM-YYYY
    try:
        return datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        pass

    # Try format 3: DD-MM HH:MM:SS (partial date)
    try:
        partial_date = date_str.split(" ")[0]  # Get "DD-MM"
        full_date_str = f"{partial_date}-{default_year}"
        return datetime.strptime(full_date_str, "%d-%m-%Y")
    except ValueError:
        pass

    # Try format 4: MM-DD-YYYY (alternative)
    try:
        partial_date = date_str.split(" ")[0]
        full_date_str = f"{partial_date}-{default_year}"
        return datetime.strptime(full_date_str, "%m-%d-%Y")
    except ValueError:
        pass

    return None


def format_date_sql(dt: datetime) -> str:
    """
    Format datetime object to SQL date format (YYYY-MM-DD).

    Args:
        dt: datetime object

    Returns:
        Date string in SQL format

    Examples:
        >>> format_date_sql(datetime(2024, 12, 25))
        '2024-12-25'
    """
    return dt.strftime("%Y-%m-%d")


# =============================================================================
# DATA STRUCTURE UTILITIES
# =============================================================================

def safe_get_list_item(lst: List, index: int, default: Any = None) -> Any:
    """
    Safely get item from list with default value.

    Args:
        lst: List to get item from
        index: Index to access
        default: Default value if index out of range

    Returns:
        Item at index or default value

    Examples:
        >>> safe_get_list_item([1, 2, 3], 1)
        2
        >>> safe_get_list_item([1, 2, 3], 5, default=0)
        0
    """
    try:
        return lst[index] if 0 <= index < len(lst) else default
    except (IndexError, TypeError):
        return default


def clean_stl_string(stl_text: str) -> str:
    """
    Clean STL (Soi Tránh Lô) string by removing annotations.

    Removes parentheses content like "(N1)", "(N2)", etc.

    Args:
        stl_text: STL string to clean

    Returns:
        Cleaned STL string

    Examples:
        >>> clean_stl_string("12-34 (N1)")
        '12-34'
        >>> clean_stl_string("05-06")
        '05-06'
    """
    if not stl_text:
        return ""

    stl_text = str(stl_text).strip()
    if "(" in stl_text:
        return stl_text.split("(")[0].strip()
    return stl_text


# =============================================================================
# STRING UTILITIES
# =============================================================================

def normalize_bridge_name(name: str) -> str:
    """
    Normalize bridge name for comparison and storage.

    - Strips whitespace
    - Converts to lowercase
    - Removes special characters and Vietnamese diacritics
    - Normalizes to ASCII-safe form

    Args:
        name: Bridge name to normalize

    Returns:
        Normalized bridge name (ASCII-safe)

    Examples:
        >>> normalize_bridge_name("  Bridge 1  ")
        'bridge1'
        >>> normalize_bridge_name("Cầu-Đẹp")
        'caudep'
    """
    if not name:
        return ""

    import unicodedata
    
    name = str(name).strip().lower()
    
    # Vietnamese character mapping to ASCII
    vietnamese_map = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'đ': 'd',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y'
    }
    
    # Replace Vietnamese characters
    for viet_char, ascii_char in vietnamese_map.items():
        name = name.replace(viet_char, ascii_char)
    
    # Normalize Unicode and remove remaining diacritics
    name = unicodedata.normalize('NFD', name)
    name = ''.join(char for char in name if unicodedata.category(char) != 'Mn')
    
    # Remove all non-alphanumeric characters (including underscore)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name


# =============================================================================
# RETRY DECORATOR (V11.2)
# =============================================================================

def retry_on_db_lock(max_retries: int = 3, initial_delay: float = 0.1):
    """
    Decorator to retry database operations on sqlite3.OperationalError.
    
    Uses exponential backoff for retries.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (doubles each retry)
        
    Example:
        >>> @retry_on_db_lock(max_retries=3)
        ... def my_db_operation():
        ...     # Database code here
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_exception = e
                    if "locked" in str(e).lower() and attempt < max_retries - 1:
                        print(f"[WARN] Database locked, retrying in {delay}s... (attempt {attempt+1}/{max_retries})")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        raise
                except Exception:
                    raise
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator


# =============================================================================
# TIMESTAMP HELPERS (V11.2)
# =============================================================================

def get_current_timestamp() -> str:
    """
    Get current timestamp in SQL format.
    
    Returns:
        Timestamp string in format 'YYYY-MM-DD HH:MM:SS'
        
    Example:
        >>> get_current_timestamp()
        '2024-12-09 15:30:45'
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_current_date() -> str:
    """
    Get current date in SQL format.
    
    Returns:
        Date string in format 'YYYY-MM-DD'
        
    Example:
        >>> get_current_date()
        '2024-12-09'
    """
    return datetime.now().strftime("%Y-%m-%d")
