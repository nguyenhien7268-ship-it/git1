import sys
import os

# Thêm thư mục gốc vào path để import các module của bạn
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_import_main_app():
    try:
        import main_app
        import app_controller
        import core_services
    except ImportError as e:
        assert False, f"Không thể import module chính: {e}"
    assert True

def test_placeholder():
    print("Pytest đã chạy thành công")
    assert True
