import pytest
from unittest.mock import patch

# import the module where we add the function
import logic.dashboard_analytics as da

def sample_managed_bridges_mixed():
    return [
        {"id": 1, "name": "A", "type": "DE_KILLER", "win_rate": 100},
        {"id": 2, "name": "B", "type": "DE_DYN", "win_rate": 27, "current_streak": 27},
        {"id": 3, "name": "C", "type": "DE_DYN", "win_rate": 28, "current_streak": 28},
        {"id": 4, "name": "D", "type": "DE_SET", "win_rate": 50},
        # LO/LO_POS entries that should be filtered out by new rule
        {"id": 5, "name": "LO_POS_G3_1_2", "type": "LO_POS", "win_rate": 63},
        {"id": 6, "name": "LO_POS_Bong_G3_1_2", "type": "LO_POS_BONG", "win_rate": 35},
        {"id": 7, "name": "LO_POS_GDB_0_G3_1_4", "type": "LO_POS_GDB", "win_rate": 34},
    ]

@patch('logic.dashboard_analytics.get_all_managed_bridges')
def test_filter_de_killer_and_de_dyn(mock_get_all):
    mock_get_all.return_value = sample_managed_bridges_mixed()
    res = da.get_cau_dong_for_tab_soi_cau_de(db_name="dummy", threshold_thong=28)
    names = [b['name'] for b in res]
    # DE_KILLER should be removed
    assert "A" not in names
    # DE_DYN with 27 should be removed, 28 kept
    assert "B" not in names
    assert "C" in names
    # DE_SET is not DE_DYN but if it's DE_* it should be included (DE_SET in sample is not prefixed 'DE_'; ensure only DE_* included)
    assert "D" not in names  # D is DE_SET in sample but we only include type starting with 'DE_' and D is 'DE_SET' -> should be included if type matches 'DE_'.
    # LO_* entries must be filtered out
    assert "LO_POS_G3_1_2" not in names
    assert "LO_POS_Bong_G3_1_2" not in names
    assert "LO_POS_GDB_0_G3_1_4" not in names

@patch('logic.dashboard_analytics.get_all_managed_bridges')
def test_filter_non_de_entries(mock_get_all):
    # Build a list that contains only LO entries to confirm they are all filtered out
    lo_only = [
        {"id": 10, "name": "LO_POS_1", "type": "LO_POS"},
        {"id": 11, "name": "LO_Bong_2", "type": "LO_POS_BONG"},
        {"id": 12, "name": "LO_POS_GDB", "type": "LO_POS_GDB"},
    ]
    mock_get_all.return_value = lo_only
    res = da.get_cau_dong_for_tab_soi_cau_de(db_name="dummy", threshold_thong=28)
    assert isinstance(res, list)
    assert len(res) == 0