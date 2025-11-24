# tests/test_bridges_v16_unit.py
"""
Unit tests for bridges_v16.py - V16/V17 bridge functions
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logic.bridges.bridges_v16 import (
    getDigits_V16,
    getAllPositions_V16,
    getPositionName_V16,
    get_index_from_name_V16,
    getAllPositions_V17_Shadow,
    getPositionName_V17_Shadow,
)


class TestGetDigitsV16:
    """Test getDigits_V16 function"""
    
    def test_get_digits_v16_basic(self):
        """Test getDigits_V16 with basic string"""
        result = getDigits_V16("12345")
        assert result == [1, 2, 3, 4, 5]
    
    def test_get_digits_v16_with_non_digits(self):
        """Test getDigits_V16 filters non-digits"""
        result = getDigits_V16("12abc34")
        assert result == [1, 2, 3, 4]
    
    def test_get_digits_v16_empty_string(self):
        """Test getDigits_V16 with empty string"""
        result = getDigits_V16("")
        assert result == []
    
    def test_get_digits_v16_none(self):
        """Test getDigits_V16 with None"""
        result = getDigits_V16(None)
        assert result == []
    
    def test_get_digits_v16_no_digits(self):
        """Test getDigits_V16 with no digits"""
        result = getDigits_V16("abc")
        assert result == []
    
    def test_get_digits_v16_integer_input(self):
        """Test getDigits_V16 with integer input"""
        result = getDigits_V16(12345)
        assert result == [1, 2, 3, 4, 5]


class TestGetAllPositionsV16:
    """Test getAllPositions_V16 function"""
    
    def test_get_all_positions_v16_basic(self):
        """Test getAllPositions_V16 with basic row"""
        row = (None, None, "12345", "67890", "11111,22222", "33333", "4444,5555", "6666,7777", "888,999", "00,11")
        positions = getAllPositions_V16(row)
        
        assert len(positions) == 107
        assert positions[0] == 1  # GDB[0]
        assert positions[1] == 2  # GDB[1]
        assert positions[5] == 6  # G1[0]
    
    def test_get_all_positions_v16_empty_values(self):
        """Test getAllPositions_V16 with empty/None values"""
        row = (None, None, None, None, None, None, None, None, None, None)
        positions = getAllPositions_V16(row)
        
        assert len(positions) == 107
        # Should pad with None hoặc 0
        assert positions[0] == 0 or positions[0] is None
    
    def test_get_all_positions_v16_partial_data(self):
        """Test getAllPositions_V16 with partial data"""
        row = (None, None, "12345", "67890", None, None, None, None, None, None)
        positions = getAllPositions_V16(row)
        
        assert len(positions) == 107
        assert positions[0] == 1  # GDB[0]
        assert positions[5] == 6  # G1[0]
        # Later positions should be None hoặc 0
        assert positions[20] is None or positions[20] == 0
    
    def test_get_all_positions_v16_error_handling(self):
        """Test getAllPositions_V16 error handling"""
        row = None  # Invalid input
        positions = getAllPositions_V16(row)
        
        assert len(positions) == 107
        assert all(p is None for p in positions)


class TestGetPositionNameV16:
    """Test getPositionName_V16 function"""
    
    def test_get_position_name_v16_gdb(self):
        """Test getPositionName_V16 for GDB positions"""
        assert getPositionName_V16(0) == "GDB[0]"
        assert getPositionName_V16(1) == "GDB[1]"
        assert getPositionName_V16(4) == "GDB[4]"
    
    def test_get_position_name_v16_g1(self):
        """Test getPositionName_V16 for G1 positions"""
        assert getPositionName_V16(5) == "G1[0]"
        assert getPositionName_V16(6) == "G1[1]"
        assert getPositionName_V16(9) == "G1[4]"
    
    def test_get_position_name_v16_g2(self):
        """Test getPositionName_V16 for G2 positions"""
        assert getPositionName_V16(10) == "G2.1[0]"
        assert getPositionName_V16(14) == "G2.1[4]"
        assert getPositionName_V16(15) == "G2.2[0]"
        assert getPositionName_V16(19) == "G2.2[4]"
    
    def test_get_position_name_v16_g3(self):
        """Test getPositionName_V16 for G3 positions"""
        assert getPositionName_V16(20) == "G3.1[0]"
        assert getPositionName_V16(24) == "G3.1[4]"
        assert getPositionName_V16(25) == "G3.2[0]"
    
    def test_get_position_name_v16_g4(self):
        """Test getPositionName_V16 for G4 positions"""
        assert getPositionName_V16(50) == "G4.1[0]"
        assert getPositionName_V16(53) == "G4.1[3]"
        assert getPositionName_V16(54) == "G4.2[0]"
    
    def test_get_position_name_v16_g5(self):
        """Test getPositionName_V16 for G5 positions"""
        assert getPositionName_V16(66) == "G5.1[0]"
        assert getPositionName_V16(69) == "G5.1[3]"
        assert getPositionName_V16(70) == "G5.2[0]"
    
    def test_get_position_name_v16_g6(self):
        """Test getPositionName_V16 for G6 positions"""
        assert getPositionName_V16(90) == "G6.1[0]"
        assert getPositionName_V16(92) == "G6.1[2]"
        assert getPositionName_V16(93) == "G6.2[0]"
    
    def test_get_position_name_v16_g7(self):
        """Test getPositionName_V16 for G7 positions"""
        assert getPositionName_V16(99) == "G7.1[0]"
        assert getPositionName_V16(100) == "G7.1[1]"
        assert getPositionName_V16(101) == "G7.2[0]"
    
    def test_get_position_name_v16_invalid_index(self):
        """Test getPositionName_V16 with invalid index"""
        assert getPositionName_V16(-1) == "NULL"
        assert getPositionName_V16(107) == "NULL"
        assert getPositionName_V16(200) == "NULL"


class TestGetIndexFromNameV16:
    """Test get_index_from_name_V16 function"""
    
    def test_get_index_from_name_v16_gdb(self):
        """Test get_index_from_name_V16 for GDB names"""
        assert get_index_from_name_V16("GDB[0]") == 0
        assert get_index_from_name_V16("GDB[1]") == 1
        assert get_index_from_name_V16("GDB[4]") == 4
    
    def test_get_index_from_name_v16_g1(self):
        """Test get_index_from_name_V16 for G1 names"""
        assert get_index_from_name_V16("G1[0]") == 5
        assert get_index_from_name_V16("G1[1]") == 6
        assert get_index_from_name_V16("G1[4]") == 9
    
    def test_get_index_from_name_v16_g2(self):
        """Test get_index_from_name_V16 for G2 names"""
        assert get_index_from_name_V16("G2.1[0]") == 10
        assert get_index_from_name_V16("G2.1[4]") == 14
        assert get_index_from_name_V16("G2.2[0]") == 15
    
    def test_get_index_from_name_v16_g3(self):
        """Test get_index_from_name_V16 for G3 names"""
        assert get_index_from_name_V16("G3.1[0]") == 20
        assert get_index_from_name_V16("G3.6[4]") == 49
    
    def test_get_index_from_name_v16_g4(self):
        """Test get_index_from_name_V16 for G4 names"""
        assert get_index_from_name_V16("G4.1[0]") == 50
        assert get_index_from_name_V16("G4.4[3]") == 65
    
    def test_get_index_from_name_v16_g5(self):
        """Test get_index_from_name_V16 for G5 names"""
        assert get_index_from_name_V16("G5.1[0]") == 66
        assert get_index_from_name_V16("G5.6[3]") == 89
    
    def test_get_index_from_name_v16_g6(self):
        """Test get_index_from_name_V16 for G6 names"""
        assert get_index_from_name_V16("G6.1[0]") == 90
        assert get_index_from_name_V16("G6.3[2]") == 98
    
    def test_get_index_from_name_v16_g7(self):
        """Test get_index_from_name_V16 for G7 names"""
        assert get_index_from_name_V16("G7.1[0]") == 99
        assert get_index_from_name_V16("G7.4[1]") == 106
    
    def test_get_index_from_name_v16_bong(self):
        """Test get_index_from_name_V16 for Bong names"""
        assert get_index_from_name_V16("Bong(GDB[0])") == 107
        assert get_index_from_name_V16("Bong(G1[0])") == 112
        assert get_index_from_name_V16("Bong(G7.4[1])") == 213
    
    def test_get_index_from_name_v16_invalid(self):
        """Test get_index_from_name_V16 with invalid names"""
        assert get_index_from_name_V16("Invalid") is None
        assert get_index_from_name_V16("GDB[10]") is None  # Out of range
        assert get_index_from_name_V16("G2.3[0]") is None  # Invalid G2 number
        assert get_index_from_name_V16("") is None
    
    def test_get_index_from_name_v16_whitespace(self):
        """Test get_index_from_name_V16 handles whitespace"""
        assert get_index_from_name_V16("  GDB[0]  ") == 0
        assert get_index_from_name_V16("Bong( GDB[0] )") == 107


class TestGetAllPositionsV17Shadow:
    """Test getAllPositions_V17_Shadow function"""
    
    def test_get_all_positions_v17_shadow_basic(self):
        """Test getAllPositions_V17_Shadow returns 214 positions"""
        row = (None, None, "12345", "67890", "11111,22222", "33333", "4444,5555", "6666,7777", "888,999", "00,11")
        positions = getAllPositions_V17_Shadow(row)
        
        assert len(positions) == 214
        # First 107 are original positions
        assert positions[0] == 1  # GDB[0]
        # Last 107 are bong positions
        assert positions[107] == 6  # Bong of 1 is 6
    
    def test_get_all_positions_v17_shadow_bong_mapping(self):
        """Test getAllPositions_V17_Shadow bong mapping"""
        row = (None, None, "00000", None, None, None, None, None, None, None)
        positions = getAllPositions_V17_Shadow(row)
        
        # GDB[0] = 0, Bong of 0 is 5
        assert positions[0] == 0
        assert positions[107] == 5
    
    def test_get_all_positions_v17_shadow_none_handling(self):
        """Test getAllPositions_V17_Shadow handles None positions"""
        row = (None, None, None, None, None, None, None, None, None, None)
        positions = getAllPositions_V17_Shadow(row)
        
        assert len(positions) == 214
        assert positions[0] == 0 or positions[0] is None
        # Update: bóng của 0 là 5 hoặc None
        assert positions[107] == 5 or positions[107] is None


class TestGetPositionNameV17Shadow:
    """Test getPositionName_V17_Shadow function"""
    
    def test_get_position_name_v17_shadow_original(self):
        """Test getPositionName_V17_Shadow for original positions"""
        assert getPositionName_V17_Shadow(0) == "GDB[0]"
        assert getPositionName_V17_Shadow(5) == "G1[0]"
        assert getPositionName_V17_Shadow(106) == "G7.4[1]"
    
    def test_get_position_name_v17_shadow_bong(self):
        """Test getPositionName_V17_Shadow for bong positions"""
        assert getPositionName_V17_Shadow(107) == "Bong(GDB[0])"
        assert getPositionName_V17_Shadow(112) == "Bong(G1[0])"
        assert getPositionName_V17_Shadow(213) == "Bong(G7.4[1])"
    
    def test_get_position_name_v17_shadow_invalid(self):
        """Test getPositionName_V17_Shadow with invalid index"""
        assert getPositionName_V17_Shadow(-1) == "NULL"
        assert getPositionName_V17_Shadow(214) == "NULL"

