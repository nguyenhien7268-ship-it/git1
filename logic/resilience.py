# Tên file: logic/resilience.py
# Module Retry/Resilience Logic cho XS-DAS
import time
import functools
from typing import Callable, Any, Optional, Tuple

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple = (Exception,),
    on_failure: Optional[Callable] = None
):
    """
    Decorator để thử lại hàm khi gặp lỗi.
    
    Args:
        max_attempts: Số lần thử tối đa (mặc định: 3)
        delay: Thời gian chờ ban đầu giữa các lần thử (giây, mặc định: 1.0)
        backoff: Hệ số tăng thời gian chờ (mặc định: 2.0)
        exceptions: Tuple các exception cần bắt (mặc định: (Exception,))
        on_failure: Hàm callback khi tất cả lần thử đều thất bại (optional)
    
    Returns:
        Decorated function
    
    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(sqlite3.OperationalError,))
        def connect_database():
            return sqlite3.connect(DB_NAME)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        # Tất cả lần thử đều thất bại
                        if on_failure:
                            try:
                                on_failure(func, e, attempt)
                            except:
                                pass
                        raise
            
            # Fallback (không bao giờ đến đây, nhưng để type checker hài lòng)
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator

def retry_db_operation(max_attempts: int = 3):
    """
    Decorator chuyên dụng cho các thao tác database.
    
    Args:
        max_attempts: Số lần thử tối đa (mặc định: 3)
    
    Returns:
        Decorated function
    """
    try:
        import sqlite3
        db_exceptions = (sqlite3.OperationalError, sqlite3.DatabaseError, OSError)
    except ImportError:
        db_exceptions = (OSError, IOError)
    
    return retry(
        max_attempts=max_attempts,
        delay=0.5,
        backoff=2.0,
        exceptions=db_exceptions
    )

def retry_file_operation(max_attempts: int = 3):
    """
    Decorator chuyên dụng cho các thao tác file I/O.
    
    Args:
        max_attempts: Số lần thử tối đa (mặc định: 3)
    
    Returns:
        Decorated function
    """
    return retry(
        max_attempts=max_attempts,
        delay=0.3,
        backoff=1.5,
        exceptions=(OSError, IOError, PermissionError)
    )

