
import unittest
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(f"Test Sys Path: {sys.path[0]}")

from logic.bridges.bridge_manager_de import de_manager

class TestBridgeParsing(unittest.TestCase):
    
    def test_standard_parsing(self):
        # Test standard DE_SET
        name = "DE_SET_G3.2.2_G5.5.3"
        parsed = de_manager._parse_bridge_id_v2(name, "DE_SET")
        self.assertIsNotNone(parsed)
        idx1, idx2, k, mode = parsed
        self.assertEqual(mode, "SET")
        # G3.2.2 -> Giai 3 (idx=20..), row 2, idx 2.
        # Based on V16 map, let's just ensure it's an integer
        self.assertIsInstance(idx1, int)
        self.assertIsInstance(idx2, int)

    def test_bong_parsing(self):
        # Test Bong(...) format
        name = "DE_DYN_G2.1.1_Bong(GDB.2)_K0"
        parsed = de_manager._parse_bridge_id_v2(name, "DE_DYNAMIC_K")
        self.assertIsNotNone(parsed)
        idx1, idx2, k, mode = parsed
        self.assertEqual(mode, "DYNAMIC")
        self.assertEqual(k, 0)
        self.assertIsInstance(idx1, int)
        self.assertIsInstance(idx2, int)
        # Bong index should be > 106
        self.assertGreaterEqual(idx2, 107)

    def test_k_offset_parsing(self):
        name = "DE_DYN_GDB.0_G7.4.0_K6"
        parsed = de_manager._parse_bridge_id_v2(name, "DE_DYNAMIC_K")
        self.assertIsNotNone(parsed)
        idx1, idx2, k, mode = parsed
        self.assertEqual(k, 6)

    def test_legacy_format(self):
        # Should NOT parse with v2, but fallback logic might handle it if we tested that.
        # Here we only test standard v2 inputs.
        pass

    def test_invalid_input(self):
        parsed = de_manager._parse_bridge_id_v2("INVALID_NAME", "DE_SET")
        self.assertIsNone(parsed)

if __name__ == '__main__':
    unittest.main()
