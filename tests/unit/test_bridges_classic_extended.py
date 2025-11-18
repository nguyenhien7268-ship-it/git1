"""
Extended unit tests for bridges_classic.py to reach 30% coverage milestone.
"""

import pytest


class TestBongDuongMapping:
    """Test Bong Duong mapping and functions."""
    
    def test_bong_duong_constant_exists(self):
        """Test that BONG_DUONG_V30 constant exists."""
        from logic.bridges import bridges_classic
        
        assert hasattr(bridges_classic, 'BONG_DUONG_V30')
        assert isinstance(bridges_classic.BONG_DUONG_V30, dict)
        assert len(bridges_classic.BONG_DUONG_V30) == 10

    def test_get_bong_duong_valid_digits(self):
        """Test getBongDuong_V30 with valid digits."""
        from logic.bridges.bridges_classic import getBongDuong_V30
        
        # Test all mappings
        assert getBongDuong_V30('0') == '5'
        assert getBongDuong_V30('1') == '6'
        assert getBongDuong_V30('5') == '0'
        assert getBongDuong_V30('9') == '4'

    def test_get_bong_duong_invalid_digit(self):
        """Test getBongDuong_V30 with invalid digit."""
        from logic.bridges.bridges_classic import getBongDuong_V30
        
        # Should return the digit itself
        result = getBongDuong_V30('x')
        assert result == 'x'


class TestTaoSTLBong:
    """Test taoSTL_V30_Bong function."""
    
    def test_tao_stl_same_digits(self):
        """Test creating STL with same digits (kép)."""
        from logic.bridges.bridges_classic import taoSTL_V30_Bong
        
        result = taoSTL_V30_Bong('3', '3')
        
        assert isinstance(result, list)
        assert len(result) == 2
        # Should return kép and bong kép
        assert result[0] == '33'
        assert result[1] == '88'  # Bong of 3 is 8

    def test_tao_stl_different_digits(self):
        """Test creating STL with different digits."""
        from logic.bridges.bridges_classic import taoSTL_V30_Bong
        
        result = taoSTL_V30_Bong('1', '2')
        
        assert isinstance(result, list)
        assert len(result) == 2
        # Should return both permutations
        assert '12' in result
        assert '21' in result

    def test_tao_stl_with_zero(self):
        """Test creating STL with zero."""
        from logic.bridges.bridges_classic import taoSTL_V30_Bong
        
        result = taoSTL_V30_Bong('0', '5')
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert '05' in result
        assert '50' in result


class TestGetAllLoto:
    """Test getAllLoto_V30 function."""
    
    def test_get_all_loto_valid_row(self):
        """Test extracting loto from valid row."""
        from logic.bridges.bridges_classic import getAllLoto_V30
        
        # Mock row with prizes
        row = [None, None, '12345', '67890', '11,22', '33', '44', '55', '66', '77']
        
        result = getAllLoto_V30(row)
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Should extract last 2 digits
        assert '45' in result  # from row[2]
        assert '90' in result  # from row[3]

    def test_get_all_loto_with_comma_separated(self):
        """Test extracting loto with comma-separated values."""
        from logic.bridges.bridges_classic import getAllLoto_V30
        
        # Row with comma-separated values
        row = [None, None, '12', '34', '56,78,90', '11', '22', '33', '44', '55']
        
        result = getAllLoto_V30(row)
        
        assert isinstance(result, list)
        # Should handle comma-separated values
        assert '56' in result
        assert '78' in result
        assert '90' in result

    def test_get_all_loto_with_none_values(self):
        """Test extracting loto with None values."""
        from logic.bridges.bridges_classic import getAllLoto_V30
        
        # Row with None values
        row = [None, None, '12', None, None, '56', None, None, None, None]
        
        result = getAllLoto_V30(row)
        
        assert isinstance(result, list)
        # Should skip None values
        assert '12' in result
        assert '56' in result


class TestCheckHitSet:
    """Test checkHitSet_V30_K2N function."""
    
    def test_check_hit_both(self):
        """Test when both numbers hit."""
        from logic.bridges.bridges_classic import checkHitSet_V30_K2N
        
        stl_pair = ['12', '34']
        loto_set = {'12', '34', '56'}
        
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        
        assert '2' in result  # Should indicate 2 hits

    def test_check_hit_one(self):
        """Test when one number hits."""
        from logic.bridges.bridges_classic import checkHitSet_V30_K2N
        
        stl_pair = ['12', '34']
        loto_set = {'12', '56'}
        
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        
        assert '1' in result  # Should indicate 1 hit

    def test_check_hit_none(self):
        """Test when no numbers hit."""
        from logic.bridges.bridges_classic import checkHitSet_V30_K2N
        
        stl_pair = ['12', '34']
        loto_set = {'56', '78'}
        
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        
        assert '❌' in result  # Should indicate miss

    def test_check_hit_invalid_input(self):
        """Test with invalid input."""
        from logic.bridges.bridges_classic import checkHitSet_V30_K2N
        
        # Invalid input should return error
        result = checkHitSet_V30_K2N(None, None)
        
        assert 'Lỗi' in result or '❌' in result


class TestBridgeFunctionsList:
    """Test ALL_15_BRIDGE_FUNCTIONS_V5 list."""
    
    def test_bridge_functions_list_exists(self):
        """Test that bridge functions list exists."""
        from logic.bridges import bridges_classic
        
        assert hasattr(bridges_classic, 'ALL_15_BRIDGE_FUNCTIONS_V5')
        assert isinstance(bridges_classic.ALL_15_BRIDGE_FUNCTIONS_V5, list)

    def test_bridge_functions_are_callable(self):
        """Test that bridge functions in list are callable."""
        from logic.bridges.bridges_classic import ALL_15_BRIDGE_FUNCTIONS_V5
        
        # List should contain functions
        if len(ALL_15_BRIDGE_FUNCTIONS_V5) > 0:
            for func in ALL_15_BRIDGE_FUNCTIONS_V5:
                assert callable(func)


class TestAdditionalBridgeFunctions:
    """Additional tests to reach 30% milestone."""
    
    def test_get_bong_duong_all_digits(self):
        """Test getBongDuong_V30 with all 10 digits."""
        from logic.bridges.bridges_classic import getBongDuong_V30
        
        # Test all 10 digits
        mappings = {
            '0': '5', '1': '6', '2': '7', '3': '8', '4': '9',
            '5': '0', '6': '1', '7': '2', '8': '3', '9': '4'
        }
        
        for digit, expected in mappings.items():
            result = getBongDuong_V30(digit)
            assert result == expected, f"Digit {digit} should map to {expected}, got {result}"
    
    def test_tao_stl_with_string_numbers(self):
        """Test taoSTL with string numbers."""
        from logic.bridges.bridges_classic import taoSTL_V30_Bong
        
        result = taoSTL_V30_Bong('7', '8')
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert '78' in result
        assert '87' in result
    
    def test_get_all_loto_with_empty_string(self):
        """Test getAllLoto with empty string values."""
        from logic.bridges.bridges_classic import getAllLoto_V30
        
        row = [None, None, '', '12', '', '34', '', '', '', '']
        result = getAllLoto_V30(row)
        
        assert isinstance(result, list)
        # Should skip empty strings
        assert '12' in result
        assert '34' in result
    
    def test_check_hit_with_empty_set(self):
        """Test checkHitSet with empty loto set."""
        from logic.bridges.bridges_classic import checkHitSet_V30_K2N
        
        stl_pair = ['12', '34']
        loto_set = set()
        
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        
        # Should indicate miss
        assert '❌' in result
    
    def test_tao_stl_single_digit_numbers(self):
        """Test taoSTL with single digit numbers."""
        from logic.bridges.bridges_classic import taoSTL_V30_Bong
        
        result1 = taoSTL_V30_Bong(1, 2)
        assert len(result1) == 2
        
        result2 = taoSTL_V30_Bong(5, 5)
        assert len(result2) == 2
        assert result2[0] == '55'
