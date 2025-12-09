import os
import sys

# Ensure project root is first in sys.path so `import logic` resolves to the real package,
# not tests/logic which pytest prepends to sys.path during collection.
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if not sys.path or sys.path[0] != _root:
    try:
        # Remove any duplicate occurrences of the project root to avoid clutter
        while _root in sys.path:
            sys.path.remove(_root)
    except Exception:
        pass
    sys.path.insert(0, _root)