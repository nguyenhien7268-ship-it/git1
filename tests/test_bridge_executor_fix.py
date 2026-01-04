
import unittest
import sys
import os

# Add the project root directory to sys.path
# Assuming the tests folder is one level deep, so we go up one level
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.bridge_executor import DynamicKBridgeStrategy, _extract_digit_from_col

class TestBridgeExecutorFix(unittest.TestCase):
    
    def setUp(self):
        # Sample data row similar to what we saw in inspection
        # 0:Id, 1:Date, 2:GDB, 3:G1, 4:G2, 5:G3, 6:G4, 7:G5, 8:G6, 9:G7
        # G5 Content: '6253,9091,6727,1248,8766,3207'
        # G6 Content: '021,909,522'
        self.mock_row = [
            2512170330, '2512170330', '93656', '06722', 
            '90781,84991',                      # G2
            '70072,38941,34876,81223,83583,43254', # G3 (Index 5)
            '9242,7739,2527,0393',              # G4 (Index 6)
            '6253,9091,6727,1248,8766,3207',    # G5 (Index 7)
            '021,909,522',                      # G6 (Index 8)
            '15,09,41,01'                       # G7 (Index 9)
        ]
        self.strategy = DynamicKBridgeStrategy()

    def test_extract_simple_column(self):
        # G1 is '06722' -> index 3
        # Should take last digit '2' if no sub-index provided (legacy behavior)
        # or if we implement robust parsing, it might default differently?
        # Current implementation just joins all digits and takes last.
        val = _extract_digit_from_col(self.mock_row, "G1")
        self.assertEqual(val, 2)

    def test_extract_multiprize_column_specific_index(self):
        # G5.1.0 -> G5 (index 7), 1st prize (index 0 in 0-based), 0th char
        # G5 value: '6253,9091,6727,1248,8766,3207'
        # Prizes: p0=6253, p1=9091, p2=6727...
        # G5.1.0 should typically mean: Column G5, 1st prize (p0 or p1? Usually 1-based in naming: G5.1 means first prize -> index 0)
        # Wait, standard naming convention in this system usually uses 1-based for naming (e.g. G5.1)
        # but let's assume the extraction logic needs to handle whatever string is passed.
        # If the input is "G5.1.0", we want 1st prize "6253", character 0 -> '6'.
        
        # NOTE: Current Implementation fails here, it parses "G5" and takes last digit of EVERYTHING (7)
        # We Expect: 6
        
        val = _extract_digit_from_col(self.mock_row, "G5.1.0")
        print(f"Extracted G5.1.0: {val}")
        self.assertEqual(val, 6, "Should extract 1st digit of 1st prize of G5")

    def test_extract_multiprize_column_second_prize(self):
        # G5.2.3 -> 2nd prize '9091', 3rd character (index 3) -> '1'
        val = _extract_digit_from_col(self.mock_row, "G5.2.3")
        print(f"Extracted G5.2.3: {val}")
        self.assertEqual(val, 1)

    def test_bridge_prediction_execution(self):
        # Test a full bridge prediction
        # Bridge: DE_DYN_G5.1.0_G6.1.0_K4
        # G5.1.0 -> '6' (from 6253) -> int 6
        # G6.1.0 -> '0' (from 021) -> int 0
        # Sum = (6+0) % 10 = 6
        # K4 -> TONG logic: (Sum + K) = 10 -> 0; (Sum+K+1) = 11 -> 1
        # Touches: 0, 5, 1, 6
        
        pred = self.strategy.execute("DE_DYN_G5.1.0_G6.1.0_K4", self.mock_row)
        print(f"Prediction for DE_DYN_G5.1.0_G6.1.0_K4: {pred}")
        self.assertIsNotNone(pred)
        self.assertIn("0", pred)
        self.assertIn("6", pred)

if __name__ == '__main__':
    unittest.main()
