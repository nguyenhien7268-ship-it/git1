
import re

def map_safe_name_to_index(safe_name):
    print(f"Parsing: '{safe_name}'")
    try:
        # Regex exactly from bridge_manager_de.py
        match = re.match(r"(G\d+\.?\d*|GDB)[\[\.]?(\d+)", safe_name)
        
        if match:
            g_name, g_idx = match.groups()
            print(f"  Match: g_name='{g_name}', g_idx='{g_idx}'")
            reconstructed = f"{g_name}[{g_idx}]"
            print(f"  Reconstructed: {reconstructed}")
            return reconstructed
        print("  No match")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def parse_bridge_id_v2(name, b_type):
    print(f"\n--- Testing Name: '{name}' Type: '{b_type}' ---")
    try:
        if "DE_SET" in name or b_type == "DE_SET":
            match = re.search(r"DE_SET_(.+)_([^_]+)", name)
            if match:
                p1_str, p2_str = match.groups()
                print(f"  Split: p1='{p1_str}', p2='{p2_str}'")
                
                idx1 = map_safe_name_to_index(p1_str)
                idx2 = map_safe_name_to_index(p2_str)
                
                if idx1 is not None and idx2 is not None:
                    print("  SUCCESS")
                    return idx1, idx2, 0, "SET"
                else:
                    print("  FAILED mapping")
            else:
                print("  FAILED regex split")
    except Exception as e:
        print(f"  Exception: {e}")
    return None

# Test cases
parse_bridge_id_v2("DE_SET_G3.2.2_G5.5.3", "DE_SET")
map_safe_name_to_index("G3.2.2")
map_safe_name_to_index("GDB.1")
map_safe_name_to_index("G1.1.1")
