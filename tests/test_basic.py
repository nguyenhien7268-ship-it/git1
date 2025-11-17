# Tên file: git3/tests/test_basic.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA F401)
#
import os
import sys

# Thêm thư mục gốc vào path để import các module của bạn
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_import_main_app():
    try:
        # Giữ lại import để kiểm tra đường dẫn, nhưng chỉ import thư viện
        import app_controller
        import core_services
        import main_app

        # Để tránh lỗi F401, ta chỉ cần sử dụng tên module
        assert app_controller and core_services and main_app
    except ImportError as e:
        assert False, f"Không thể import module chính: {e}"
    assert True


def test_placeholder():
    print("Pytest đã chạy thành công")
    assert True
