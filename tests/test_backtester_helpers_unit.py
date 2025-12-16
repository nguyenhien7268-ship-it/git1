# tests/test_backtester_helpers_unit.py
"""
Unit tests for backtester_helpers.py - Core helper functions
"""
import pytest

# validate_backtest_params moved to common_utils
# parse_k2n_results moved to backtester_core
from logic.common_utils import validate_backtest_params
from logic.backtester_core import parse_k2n_results


class TestValidateBacktestParams:
    """Test backtest parameter validation"""
    
    def test_valid_params(self, sample_lottery_data):
        """Test valid backtest parameters"""
        result = validate_backtest_params(
            sample_lottery_data, 2, 5
        )
        
        allData, finalEndRow, startCheckRow, offset, error = result
        
        assert error is None
        assert allData == sample_lottery_data
        # finalEndRow = min(5, len(sample_lottery_data) + 2 - 1) = min(5, 4) = 4
        assert finalEndRow == 4
        assert startCheckRow == 3
        assert offset == 2
    
    def test_missing_params(self):
        """Test missing parameters"""
        result = validate_backtest_params(None, 2, 5)
        
        _, _, _, _, error = result
        assert error is not None
        assert "Cần đủ tham số" in str(error[0])
    
    def test_invalid_start_row(self, sample_lottery_data):
        """Test invalid start row (must be > 1)"""
        result = validate_backtest_params(
            sample_lottery_data, 1, 5
        )
        
        _, _, _, _, error = result
        assert error is not None
        assert "không hợp lệ" in str(error[0])
    
    def test_start_greater_than_end(self, sample_lottery_data):
        """Test start row greater than end row"""
        result = validate_backtest_params(
            sample_lottery_data, 5, 2
        )
        
        _, _, _, _, error = result
        assert error is not None
    
    def test_non_numeric_params(self, sample_lottery_data):
        """Test non-numeric parameters"""
        result = validate_backtest_params(
            sample_lottery_data, "invalid", 5
        )
        
        _, _, _, _, error = result
        assert error is not None
        assert "phải là số" in str(error[0])
    
    def test_end_exceeds_data_length(self, sample_lottery_data):
        """Test end row exceeds data length"""
        result = validate_backtest_params(
            sample_lottery_data, 2, 100  # End exceeds data length
        )
        
        allData, finalEndRow, startCheckRow, offset, error = result
        
        assert error is None
        # finalEndRow should be capped at available data
        assert finalEndRow <= len(sample_lottery_data) + 1
    
    def test_insufficient_data(self, sample_lottery_data):
        """Test insufficient data for backtest"""
        # Start and end are too close
        result = validate_backtest_params(
            sample_lottery_data, 2, 2
        )
        
        _, _, _, _, error = result
        assert error is not None
        assert "không đủ" in str(error[0])


class TestParseK2NResults:
    """Test K2N results parsing"""
    
    def test_empty_results(self):
        """Test parsing empty results"""
        cache_data, pending_k2n = parse_k2n_results([])
        
        assert cache_data == []
        assert pending_k2n == {}
    
    def test_minimal_results(self):
        """Test parsing minimal valid results"""
        results = [
            ["Kỳ", "Bridge1", "Bridge2"],
            ["Tỷ Lệ %", "50%", "60%"],
        ]
        
        cache_data, pending_k2n = parse_k2n_results(results)
        
        # Should parse without error
        assert len(cache_data) == 2
    
    def test_full_results_structure(self):
        """Test parsing full results structure"""
        results = [
            ["Kỳ", "Bridge1 (N1)", "Bridge2 (N1)"],
            ["Tỷ Lệ %", "50.00%", "60.00%"],
            ["Chuỗi", "2 thắng/0 thua", "1 thắng/1 thua"],
            ["Phong Độ", "5/10", "7/10"],
            ["Kỳ Next", "12,34", "56,78"],
        ]
        
        cache_data, pending_k2n = parse_k2n_results(results)
        
        assert len(cache_data) == 2
        assert len(pending_k2n) == 2
        
        # Check first bridge
        assert cache_data[0][5] == "Bridge1"  # bridge_name
        assert "12" in cache_data[0][2]  # stl contains "12"
        
        # Check pending predictions
        assert "Bridge1" in pending_k2n
        assert pending_k2n["Bridge1"]["stl"] == "12,34"
    
    def test_results_with_n2_status(self):
        """Test parsing results with N2 (waiting) status"""
        results = [
            ["Kỳ", "Bridge1 (N1)", "Bridge2 (N1)"],
            ["Tỷ Lệ %", "50%", "60%"],
            ["Chuỗi", "2 thắng", "1 thắng"],
            ["Phong Độ", "5/10", "7/10"],
            ["Kỳ Next", "12,34 (chờ N2)", "56,78"],
        ]
        
        cache_data, pending_k2n = parse_k2n_results(results)
        
        # Check N2 status detection
        assert pending_k2n["Bridge1"]["is_n2"] is True
        assert pending_k2n["Bridge2"]["is_n2"] is False
    
    def test_results_missing_rows(self):
        """Test parsing results with missing optional rows"""
        results = [
            ["Kỳ", "Bridge1"],
            ["Tỷ Lệ %", "50%"],
            # Missing Chuỗi, Phong Độ, Kỳ Next rows
        ]
        
        cache_data, pending_k2n = parse_k2n_results(results)
        
        # Should still parse without error
        assert len(cache_data) == 1
        # When rows are missing, win_rate_text should be "50%" from row_rates
        # But if row_rates is None, it defaults to "0"
        # Check that we have the data structure
        assert len(cache_data[0]) >= 6  # Should have at least 6 elements
        # win_rate_text is at index 0, should be "50%" if row_rates exists
        assert cache_data[0][0] == "50%"  # win_rate_text
    
    def test_results_with_malformed_data(self):
        """Test parsing results with malformed data"""
        results = [
            ["Kỳ", "Bridge1"],
            ["Tỷ Lệ %", "invalid"],
            ["Chuỗi", "invalid format"],
            ["Phong Độ", "invalid/format"],
        ]
        
        cache_data, pending_k2n = parse_k2n_results(results)
        
        # Should handle gracefully
        assert len(cache_data) == 1
        # Should default to 0 for invalid values
        assert cache_data[0][0] == "invalid"  # win_rate_text as-is
    
    def test_bridge_name_extraction(self):
        """Test bridge name extraction from headers"""
        results = [
            ["Kỳ", "Bridge1 (N1)", "Bridge2 (K2N)"],
            ["Tỷ Lệ %", "50%", "60%"],
        ]
        
        cache_data, _ = parse_k2n_results(results)
        
        # Bridge names should be extracted without suffix
        assert cache_data[0][5] == "Bridge1"
        assert cache_data[1][5] == "Bridge2"

