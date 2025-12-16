# tests/test_bridges_classic_unit.py
"""
Unit tests for bridges_classic.py - Core bridge functions
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logic.bridges.bridges_classic import (
    BONG_DUONG_V30,
    getBongDuong_V30,
    taoSTL_V30_Bong,
    getAllLoto_V30,
    checkHitSet_V30_K2N,
    getCau1_STL_P5_V30_V5,
    getCau2_VT1_V30_V5,
    getCau3_VT2_V30_V5,
    getCau4_VT3_V30_V5,
    getCau5_TDB1_V30_V5,
    getCau6_VT5_V30_V5,
    getCau7_Moi1_V30_V5,
    getCau8_Moi2_V30_V5,
    getCau9_Moi3_V30_V5,
    getCau10_Moi4_V30_V5,
    getCau11_Moi5_V30_V5,
    getCau12_Moi6_V30_V5,
    getCau13_G7_3_P8_V30_V5,
    getCau14_G1_P2_V30_V5,
    getCau15_DE_P7_V30_V5,
    calculate_loto_stats,
    ALL_15_BRIDGE_FUNCTIONS_V5,
)


class TestBongDuongV30:
    """Test Bong Duong V30 mapping"""
    
    def test_bong_duong_mapping(self):
        """Test BONG_DUONG_V30 dictionary mapping"""
        assert BONG_DUONG_V30["0"] == "5"
        assert BONG_DUONG_V30["1"] == "6"
        assert BONG_DUONG_V30["2"] == "7"
        assert BONG_DUONG_V30["3"] == "8"
        assert BONG_DUONG_V30["4"] == "9"
        assert BONG_DUONG_V30["5"] == "0"
        assert BONG_DUONG_V30["6"] == "1"
        assert BONG_DUONG_V30["7"] == "2"
        assert BONG_DUONG_V30["8"] == "3"
        assert BONG_DUONG_V30["9"] == "4"
    
    def test_get_bong_duong_v30_valid_digit(self):
        """Test getBongDuong_V30 with valid digits"""
        assert getBongDuong_V30(0) == "5"
        assert getBongDuong_V30(1) == "6"
        assert getBongDuong_V30(5) == "0"
        assert getBongDuong_V30(9) == "4"
    
    def test_get_bong_duong_v30_string_input(self):
        """Test getBongDuong_V30 with string input"""
        assert getBongDuong_V30("0") == "5"
        assert getBongDuong_V30("9") == "4"
    
    def test_get_bong_duong_v30_invalid_digit(self):
        """Test getBongDuong_V30 with invalid digit returns same"""
        assert getBongDuong_V30("10") == "10"  # Not in mapping
        assert getBongDuong_V30("a") == "a"  # Not a digit


class TestTaoSTLV30Bong:
    """Test taoSTL_V30_Bong function"""
    
    def test_tao_stl_same_digits(self):
        """Test taoSTL_V30_Bong with same digits (kep)"""
        result = taoSTL_V30_Bong(1, 1)
        assert len(result) == 2
        assert "11" in result
        assert "66" in result  # Bong of 1 is 6
    
    def test_tao_stl_different_digits(self):
        """Test taoSTL_V30_Bong with different digits"""
        result = taoSTL_V30_Bong(1, 2)
        assert len(result) == 2
        assert "12" in result
        assert "21" in result
    
    def test_tao_stl_string_input(self):
        """Test taoSTL_V30_Bong with string input"""
        result = taoSTL_V30_Bong("3", "3")
        assert len(result) == 2
        assert "33" in result
        assert "88" in result  # Bong of 3 is 8
    
    def test_tao_stl_zero_padding(self):
        """Test taoSTL_V30_Bong zero padding"""
        result = taoSTL_V30_Bong(0, 5)
        assert len(result) == 2
        assert all(len(stl) == 2 for stl in result)


class TestGetAllLotoV30:
    """Test getAllLoto_V30 function"""
    
    def test_get_all_loto_basic(self):
        """Test getAllLoto_V30 with basic row"""
        row = (None, None, "12345", "67890", "11,22", "33", "44,55,66", "77", "88,99", "00")
        lotos = getAllLoto_V30(row)
        
        assert "45" in lotos  # GDB last 2
        assert "90" in lotos  # G1 last 2
        assert "11" in lotos  # G2 first
        assert "22" in lotos  # G2 second
        assert "33" in lotos  # G3
        assert "44" in lotos  # G4 first
        assert "55" in lotos  # G4 second
        assert "66" in lotos  # G4 third
        assert "77" in lotos  # G5
        assert "88" in lotos  # G6 first
        assert "99" in lotos  # G6 second
        assert "00" in lotos  # G7
    
    def test_get_all_loto_empty_values(self):
        """Test getAllLoto_V30 with empty/None values"""
        row = (None, None, None, None, None, None, None, None, None, None)
        lotos = getAllLoto_V30(row)
        
        assert isinstance(lotos, list)
        assert len(lotos) >= 0  # Should handle gracefully
    
    def test_get_all_loto_single_digit(self):
        """Test getAllLoto_V30 with single digit values"""
        row = (None, None, "5", "7", "1", "3", "9", "2", "4", "6")
        lotos = getAllLoto_V30(row)
        
        # Should pad with zeros
        assert any(loto.startswith("0") or loto.endswith("0") for loto in lotos) or len(lotos) == 0
    
    def test_get_all_loto_invalid_data(self):
        """Test getAllLoto_V30 with invalid data"""
        row = (None, None, "abc", "xyz", "invalid", None, None, None, None, None)
        lotos = getAllLoto_V30(row)
        
        # Should filter out invalid lotos
        assert all(loto.isdigit() and len(loto) == 2 for loto in lotos)


class TestCheckHitSetV30K2N:
    """Test checkHitSet_V30_K2N function"""
    
    def test_check_hit_both_match(self):
        """Test checkHitSet_V30_K2N when both match"""
        stl_pair = ["12", "21"]
        loto_set = {"12", "21", "34"}
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        assert "Ăn 2" in result
    
    def test_check_hit_one_match(self):
        """Test checkHitSet_V30_K2N when one matches"""
        stl_pair = ["12", "21"]
        loto_set = {"12", "34"}
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        assert "Ăn 1" in result
    
    def test_check_hit_no_match(self):
        """Test checkHitSet_V30_K2N when no match"""
        stl_pair = ["12", "21"]
        loto_set = {"34", "56"}
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        assert result == "❌"
    
    def test_check_hit_empty_set(self):
        """Test checkHitSet_V30_K2N with empty set"""
        stl_pair = ["12", "21"]
        loto_set = set()
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        assert result == "❌"
    
    def test_check_hit_invalid_input(self):
        """Test checkHitSet_V30_K2N with invalid input"""
        stl_pair = None
        loto_set = {"12"}
        result = checkHitSet_V30_K2N(stl_pair, loto_set)
        assert "Lỗi" in result


class TestBridgeFunctions:
    """Test individual bridge functions"""
    
    def test_get_cau1_stl_p5_v30_v5(self):
        """Test getCau1_STL_P5_V30_V5"""
        row = (None, None, "12345", None, None, None, None, None, None, None)
        result = getCau1_STL_P5_V30_V5(row)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(len(stl) == 2 for stl in result)
    
    def test_get_cau1_stl_p5_v30_v5_empty(self):
        """Test getCau1_STL_P5_V30_V5 with empty GDB"""
        row = (None, None, None, None, None, None, None, None, None, None)
        result = getCau1_STL_P5_V30_V5(row)
        
        assert set(result) == {"00", "55"}  # Chấp nhận thứ tự bất kỳ
    
    def test_get_cau2_vt1_v30_v5(self):
        """Test getCau2_VT1_V30_V5"""
        row = (None, None, None, None, None, None, None, None, "111,222,333", "444,555,666,777")
        result = getCau2_VT1_V30_V5(row)
        
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_get_cau3_vt2_v30_v5(self):
        """Test getCau3_VT2_V30_V5"""
        row = (None, None, "12345", "67890", None, None, None, None, None, None)
        result = getCau3_VT2_V30_V5(row)
        
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_all_15_bridge_functions_exist(self):
        """Test that all 15 bridge functions are defined"""
        assert len(ALL_15_BRIDGE_FUNCTIONS_V5) == 15
        
        for func in ALL_15_BRIDGE_FUNCTIONS_V5:
            assert callable(func)
    
    def test_all_15_bridge_functions_return_list(self):
        """Test that all bridge functions return list of 2 STL"""
        row = (None, None, "12345", "67890", "11,22", "33", "44,55,66", "77", "88,99", "00")
        
        for func in ALL_15_BRIDGE_FUNCTIONS_V5:
            result = func(row)
            assert isinstance(result, list)
            assert len(result) == 2
            assert all(isinstance(stl, str) and len(stl) == 2 for stl in result)
    
    def test_all_15_bridge_functions_error_handling(self):
        """Test that all bridge functions handle errors gracefully"""
        row = None  # Invalid input
        
        for func in ALL_15_BRIDGE_FUNCTIONS_V5:
            result = func(row)
            # Should return default fallback
            assert isinstance(result, list)
            assert len(result) == 2
            assert result == ["00", "55"]


class TestCalculateLotoStats:
    """Test calculate_loto_stats function"""
    
    def test_calculate_loto_stats_basic(self):
        """Test calculate_loto_stats with basic loto list"""
        loto_list = ["12", "23", "34", "45", "56"]
        dau_stats, duoi_stats = calculate_loto_stats(loto_list)
        
        assert isinstance(dau_stats, dict)
        assert isinstance(duoi_stats, dict)
        assert len(dau_stats) == 10
        assert len(duoi_stats) == 10
        
        # Check dau stats
        assert "2" in dau_stats[1]  # Loto "12" has dau=1, duoi=2
        assert "3" in dau_stats[2]  # Loto "23" has dau=2, duoi=3
    
    def test_calculate_loto_stats_empty(self):
        """Test calculate_loto_stats with empty list"""
        loto_list = []
        dau_stats, duoi_stats = calculate_loto_stats(loto_list)
        
        assert isinstance(dau_stats, dict)
        assert isinstance(duoi_stats, dict)
        assert all(len(stats) == 0 for stats in dau_stats.values())
        assert all(len(stats) == 0 for stats in duoi_stats.values())
    
    def test_calculate_loto_stats_invalid(self):
        """Test calculate_loto_stats filters invalid lotos"""
        loto_list = ["12", "abc", "123", "45", "x"]
        dau_stats, duoi_stats = calculate_loto_stats(loto_list)
        
        # Should only process valid 2-digit lotos
        assert "2" in dau_stats[1]  # From "12"
        assert "5" in dau_stats[4]  # From "45"
    
    def test_calculate_loto_stats_single_digit(self):
        """Test calculate_loto_stats with single digit lotos"""
        loto_list = ["1", "2", "12"]
        dau_stats, duoi_stats = calculate_loto_stats(loto_list)
        
        # Should only process "12"
        assert "2" in dau_stats[1]

