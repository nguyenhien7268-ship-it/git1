# tests/test_utils_unit.py
"""
Unit tests for utils.py - Utility functions
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logic.utils import (
    BONG_DUONG_V30,
    getBongDuong_V30,
    taoSTL_V30_Bong,
    getAllLoto_V30,
    checkHitSet_V30_K2N,
)


class TestBongDuongV30Utils:
    """Test Bong Duong V30 mapping in utils"""
    
    def test_bong_duong_mapping(self):
        """Test BONG_DUONG_V30 dictionary mapping"""
        assert BONG_DUONG_V30["0"] == "5"
        assert BONG_DUONG_V30["5"] == "0"
        assert BONG_DUONG_V30["9"] == "4"
    
    def test_get_bong_duong_v30(self):
        """Test getBongDuong_V30 function"""
        assert getBongDuong_V30(0) == "5"
        assert getBongDuong_V30(5) == "0"
        assert getBongDuong_V30("9") == "4"


class TestTaoSTLV30BongUtils:
    """Test taoSTL_V30_Bong function in utils"""
    
    def test_tao_stl_same_digits(self):
        """Test taoSTL_V30_Bong with same digits"""
        result = taoSTL_V30_Bong(2, 2)
        assert len(result) == 2
        assert "22" in result
        assert "77" in result  # Bong of 2 is 7
    
    def test_tao_stl_different_digits(self):
        """Test taoSTL_V30_Bong with different digits"""
        result = taoSTL_V30_Bong(3, 4)
        assert len(result) == 2
        assert "34" in result
        assert "43" in result
    
    def test_tao_stl_format(self):
        """Test taoSTL_V30_Bong returns properly formatted strings"""
        result = taoSTL_V30_Bong(0, 1)
        assert all(isinstance(stl, str) for stl in result)
        assert all(len(stl) == 2 for stl in result)


class TestGetAllLotoV30Utils:
    """Test getAllLoto_V30 function in utils"""
    
    def test_get_all_loto_v30_basic(self):
        """Test getAllLoto_V30 with basic row data"""
        # Format: (MaSoKy, Col_A_Ky, Col_B_GDB, Col_C_G1, Col_D_G2, Col_E_G3, Col_F_G4, Col_G_G5, Col_H_G6, Col_I_G7)
        row = (23001, "23001", "12345", "67890", "11,22", "33", "44,55,66", "77", "88,99", "00")
        lotos = getAllLoto_V30(row)
        
        assert isinstance(lotos, list)
        assert len(lotos) > 0
        # Should extract last 2 digits from each field
        assert "45" in lotos  # From GDB
        assert "90" in lotos  # From G1
    
    def test_get_all_loto_v30_empty_row(self):
        """Test getAllLoto_V30 with empty row"""
        row = (None, None, None, None, None, None, None, None, None, None)
        lotos = getAllLoto_V30(row)
        
        assert isinstance(lotos, list)
        # Should handle gracefully
    
    def test_get_all_loto_v30_filters_invalid(self):
        """Test getAllLoto_V30 filters invalid lotos"""
        row = (None, None, "abc", "xyz", "123", "45", None, None, None, None)
        lotos = getAllLoto_V30(row)
        
        # Should only include valid 2-digit lotos
        assert all(loto.isdigit() and len(loto) == 2 for loto in lotos)
    
    def test_get_all_loto_v30_comma_separated(self):
        """Test getAllLoto_V30 handles comma-separated values"""
        row = (None, None, "12345", "67890", "11,22,33", "44,55", None, None, None, None)
        lotos = getAllLoto_V30(row)
        
        # Should extract all comma-separated values
        assert "11" in lotos
        assert "22" in lotos
        assert "33" in lotos
    
    def test_get_all_loto_v30_error_handling(self):
        """Test getAllLoto_V30 error handling"""
        row = None  # Invalid input
        lotos = getAllLoto_V30(row)
        
        assert isinstance(lotos, list)
        # Should return empty list or handle gracefully


class TestCheckHitSetV30K2NUtils:
    """Test checkHitSet_V30_K2N function in utils"""
    
    def test_check_hit_both_match(self):
        """Test checkHitSet_V30_K2N when both STL match"""
        stl_pair = ["12", "21"]
        loto_set = {"12", "21", "34", "56"}
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        
        assert "Ăn 2" in result
    
    def test_check_hit_one_match(self):
        """Test checkHitSet_V30_K2N when one STL matches"""
        stl_pair = ["12", "21"]
        loto_set = {"12", "34"}
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        
        assert "Ăn 1" in result
    
    def test_check_hit_no_match(self):
        """Test checkHitSet_V30_K2N when no STL matches"""
        stl_pair = ["12", "21"]
        loto_set = {"34", "56", "78"}
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        
        assert result == "❌"
    
    def test_check_hit_empty_set(self):
        """Test checkHitSet_V30_K2N with empty loto set"""
        stl_pair = ["12", "21"]
        loto_set = set()
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        
        assert result == "❌"
    
    def test_check_hit_list_input(self):
        """Test checkHitSet_V30_K2N with list instead of set"""
        stl_pair = ["12", "21"]
        loto_list = ["12", "34", "56"]
        result = checkHitSet_V30_K2N(stl_pair, loto_list)
        
        # Should work with list too (in operator works)
        assert "Ăn 1" in result
    
    def test_check_hit_error_handling(self):
        """Test checkHitSet_V30_K2N error handling"""
        stl_pair = None
        loto_set = {"12"}
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        
        assert "Lỗi" in result
    
    def test_check_hit_invalid_stl_pair(self):
        """Test checkHitSet_V30_K2N with invalid STL pair"""
        stl_pair = ["12"]  # Only one element
        loto_set = {"12"}
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        
        # Should handle gracefully (may return error or partial match)
        assert isinstance(result, str)

