
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from services.data_service import DataService
from logic.db_manager import DB_NAME

def inspect_data():
    service = DataService(DB_NAME)
    data = service.load_data()
    
    if not data:
        print("No data found.")
        return

    # Inspect the last row
    last_row = data[-1]
    print(f"Data Row Length: {len(last_row)}")
    print(f"Sample Row (Last): {last_row}")
    
    # Check G5 (Index 7 based on bridge_executor comments)
    # "GDB": 2, "G1": 3, "G2": 4, "G3": 5, "G4": 6, "G5": 7
    if len(last_row) > 7:
        print(f"G5 Content (Index 7): '{last_row[7]}'")
    
    if len(last_row) > 8:
        print(f"G6 Content (Index 8): '{last_row[8]}'")

if __name__ == "__main__":
    inspect_data()
