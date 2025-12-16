# Tên file: logic/logger.py
# Module Logging tập trung cho XS-DAS
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file='logs/xsdas.log', level=logging.INFO):
    """
    Thiết lập logger với RotatingFileHandler.
    
    Args:
        name: Tên logger (thường là __name__)
        log_file: Đường dẫn file log (mặc định: logs/xsdas.log)
        level: Log level (mặc định: INFO)
    
    Returns:
        logging.Logger: Logger instance đã được cấu hình
    """
    # Tạo thư mục logs nếu chưa có
    log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else 'logs'
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError:
            pass  # Bỏ qua nếu không tạo được
    
    # Tạo logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Tránh thêm handler nhiều lần (nếu logger đã có handlers)
    if logger.handlers:
        return logger
    
    # Tạo formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # RotatingFileHandler: Max 10MB, giữ 5 file backup
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, IOError) as e:
        # Fallback: dùng console handler nếu không ghi được file
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.warning(f"Không thể tạo file log '{log_file}': {e}. Sử dụng console logging.")
    
    return logger

# Logger mặc định cho toàn bộ ứng dụng
default_logger = setup_logger('xsdas')

