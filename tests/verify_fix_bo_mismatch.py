# Tên file: tests/diagnose_bo_key.py
import sys
import os

# Thêm đường dẫn để import logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from logic.de_utils import BO_SO_DE
except ImportError:
    print("❌ LỖI: Không thể import BO_SO_DE từ logic.de_utils")
    print("Giả lập BO_SO_DE chuẩn để test...")
    BO_SO_DE = {'Bo 00': [], 'Bo 01': [], 'Bo 12': []}

def _normalize_bo_key_v2(val):
    """Phiên bản nâng cấp: Hỗ trợ số đơn (0 -> 00) và bất quy tắc"""
    val_str = str(val).strip()
    
    print(f"   🔎 Checking input: '{val}' (Type: {type(val).__name__})")
    
    # 1. Kiểm tra trực tiếp
    if val_str in BO_SO_DE:
        return val_str
    
    # 2. Thử thêm tiền tố "Bo "
    prefix_try = f"Bo {val_str}"
    if prefix_try in BO_SO_DE:
        return prefix_try
        
    # 3. 🔥 FIX QUAN TRỌNG: Thử thêm số 0 (Zero-padding) nếu là số
    # Ví dụ: "0" -> "00" -> "Bo 00"
    if val_str.isdigit():
        val_padded = val_str.zfill(2) # 0 -> 00
        padded_try = f"Bo {val_padded}"
        print(f"      ➡ Thử padding: '{val_str}' -> '{val_padded}' -> '{padded_try}'")
        if padded_try in BO_SO_DE:
            return padded_try

    return None

# --- CHẠY TEST CÁC TRƯỜNG HỢP ---
print("--- BẮT ĐẦU CHẨN ĐOÁN ---")
print(f"Danh sách Key mẫu trong BO_SO_DE: {list(BO_SO_DE.keys())[:5]}...")

test_cases = [
    "00",       # Chuẩn
    "0",        # ⚠️ Số đơn (Nguyên nhân nghi ngờ)
    0,          # ⚠️ Dạng Int
    "Bo 00",    # Đã chuẩn
    "12",       # Chuẩn
    "5"         # ⚠️ Số đơn
]

for case in test_cases:
    print(f"\n🧪 Test Case: {case}")
    result = _normalize_bo_key_v2(case)
    if result:
        print(f"✅ PASS: Nhận diện thành '{result}'")
    else:
        print(f"❌ FAIL: Không nhận diện được!")

print("\n--- KẾT THÚC ---")