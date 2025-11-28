import os
import sys
from pathlib import Path

# Cấu hình gốc dự án (Giả sử script chạy từ thư mục gốc hoặc thư mục scripts)
# Điều chỉnh để trỏ về đúng root git1
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHECKS = {
    "PHASE_1_INFRASTRUCTURE": {
        "name": "Phase 1: Testing & Infrastructure",
        "checks": [
            {"type": "dir", "path": "tests", "desc": "Thư mục Tests"},
            {"type": "file", "path": "tests/conftest.py", "desc": "Cấu hình Pytest Fixtures"},
            {"type": "file", "path": "pytest.ini", "desc": "Cấu hình Pytest (pytest.ini)"},
            {"type": "file", "path": "logic/logger.py", "desc": "Hệ thống Logging tập trung"},
        ]
    },
    "PHASE_1_REFACTORING": {
        "name": "Phase 1: Code Refactoring (Separation of Concerns)",
        "checks": [
            # Kiểm tra việc tách file lớn
            {"type": "max_lines", "path": "logic/backtester.py", "limit": 500, "desc": "Backtester Core (< 500 dòng)"},
            {"type": "max_lines", "path": "app_controller.py", "limit": 500, "desc": "App Controller (< 500 dòng)"},
            {"type": "max_lines", "path": "logic/dashboard_analytics.py", "limit": 500, "desc": "Dashboard Analytics (< 500 dòng)"},
            
            # Kiểm tra cấu trúc module mới
            {"type": "dir", "path": "logic/backtest", "desc": "Package Backtest (logic/backtest/)"},
            {"type": "dir", "path": "logic/analytics", "desc": "Package Analytics (logic/analytics/)"},
            {"type": "dir", "path": "services", "desc": "Package Services (services/)"},
            
            # Kiểm tra các file con quan trọng (đảm bảo đã tách code vào đây)
            {"type": "file", "path": "services/data_service.py", "desc": "Service: Data Management"},
            {"type": "file", "path": "services/bridge_service.py", "desc": "Service: Bridge Management"},
        ]
    },
    "PHASE_2_STABILITY": {
        "name": "Phase 2: Security & Stability",
        "checks": [
            {"type": "file", "path": "logic/validators.py", "desc": "Module Input Validation"},
            {"type": "file", "path": "logic/resilience.py", "desc": "Module Resilience (Retry Logic)"},
            {"type": "content", "path": "requirements.txt", "contains": "==", "desc": "Dependencies được ghim version (==)"},
        ]
    }
}

def count_lines(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return -1
    except Exception:
        return 0

def check_file_content(filepath, search_str):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return search_str in content
    except:
        return False

def run_audit():
    print(f"Working Directory: {os.getcwd()}")
    print(f"Project Root Detected: {PROJECT_ROOT}")
    print("="*70)
    print("🚀 KIỂM TRA TIẾN ĐỘ NÂNG CẤP HỆ THỐNG (PHASE 1 & 2)")
    print("="*70)
    
    total_checks = 0
    passed_checks = 0
    
    for category, data in CHECKS.items():
        print(f"\n🔹 {data['name']}")
        print("-" * 70)
        for check in data['checks']:
            total_checks += 1
            status = "FAIL"
            details = ""
            
            path = PROJECT_ROOT / check['path']
            
            if check['type'] == 'dir':
                if path.is_dir():
                    status = "PASS"
                    # Đếm số file bên trong để đảm bảo không phải thư mục rỗng
                    count = len([f for f in path.glob('*.py') if f.is_file()])
                    details = f"(Chứa {count} modules Python)"
                else:
                    details = f"(Thư mục không tồn tại: {path})"
                    
            elif check['type'] == 'file':
                if path.is_file():
                    status = "PASS"
                else:
                    details = f"(File không tồn tại: {path})"
                    
            elif check['type'] == 'max_lines':
                lines = count_lines(path)
                if lines == -1:
                    status = "SKIP"
                    details = "(File gốc không tồn tại - Có thể đã xóa hoặc di chuyển)"
                elif lines <= check['limit']:
                    status = "PASS"
                    details = f"({lines} dòng)"
                else:
                    status = "FAIL"
                    details = f"(Vượt quá giới hạn: {lines}/{check['limit']} dòng)"

            elif check['type'] == 'content':
                if path.is_file():
                    if check_file_content(path, check['contains']):
                        status = "PASS"
                    else:
                        details = "(Nội dung không đạt yêu cầu)"
                else:
                    details = "(File không tồn tại)"

            # In kết quả
            icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            print(f"{icon} {check['desc']:<50} {status:<5} {details}")
            
            if status == "PASS":
                passed_checks += 1

    print("\n" + "="*70)
    print(f"TỔNG KẾT: {passed_checks}/{total_checks} hạng mục đạt yêu cầu.")
    
    if passed_checks == total_checks:
        print("\n🎉 XUẤT SẮC! HỆ THỐNG ĐÃ HOÀN TẤT PHASE 1 & 2.")
        print("👉 Bạn có thể chuyển sang Phase 3: Performance & Scalability.")
    else:
        print("\n⚠️ CẢNH BÁO: Vẫn còn hạng mục chưa hoàn thành.")
        print("👉 Vui lòng ưu tiên xử lý các mục [FAIL] trước khi nâng cấp tiếp.")
    print("="*70)

if __name__ == "__main__":
    run_audit()