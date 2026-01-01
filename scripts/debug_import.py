
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

print(f"Added to path: {project_root}")
print(f"Contents of logic directory: {os.listdir(os.path.join(project_root, 'logic'))}")
print(f"Contents of logic/bridges directory: {os.listdir(os.path.join(project_root, 'logic', 'bridges'))}")

try:
    import logic
    print("Imported logic")
    import logic.bridges
    print("Imported logic.bridges")
    from logic.bridges import bridge_manager_de
    print("Imported logic.bridges.bridge_manager_de")
except ImportError as e:
    print(f"Import Failed: {e}")
except Exception as e:
    print(f"Exception: {e}")
