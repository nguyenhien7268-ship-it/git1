"""
Tests for Enhancement 4: Smart Filtering
Tests the filtering functionality that allows users to filter by confidence and AI probability
"""

import pytest
from logic.config_manager import AppSettings


def test_filter_settings_defaults():
    """Test default filter settings"""
    from logic.config_manager import SETTINGS
    
    # SỬA: Kiểm tra trong từ điển defaults thay vì giá trị instance hiện tại
    # Vì instance có thể đã load giá trị 5 từ file config.json
    assert SETTINGS.defaults["FILTER_MIN_CONFIDENCE"] == 0
    assert SETTINGS.defaults["FILTER_MIN_AI_PROB"] == 0
    assert SETTINGS.defaults["FILTER_ENABLED"] is False


def test_filter_settings_in_get_all_settings():
    """Test that filter settings are included in get_all_settings"""
    settings = AppSettings()
    all_settings = settings.get_all_settings()
    assert 'FILTER_MIN_CONFIDENCE' in all_settings
    assert 'FILTER_MIN_AI_PROB' in all_settings
    assert 'FILTER_ENABLED' in all_settings


def apply_filter(items, min_confidence, min_ai_prob, enabled):
    """
    Simulate the filtering logic from ui_dashboard.py
    """
    if not items or not enabled:
        return items
    
    filtered = []
    min_ai_prob_decimal = min_ai_prob / 100.0
    
    for item in items:
        sources = item.get("sources", 0)
        if min_confidence > 0 and sources < min_confidence:
            continue
        
        ai_prob = item.get("ai_probability", 0.0)
        if min_ai_prob > 0 and ai_prob < min_ai_prob_decimal:
            continue
        
        filtered.append(item)
    
    return filtered


def test_filter_disabled_returns_all():
    """Test that when filtering is disabled, all items are returned"""
    items = [
        {"sources": 2, "ai_probability": 0.3},
        {"sources": 5, "ai_probability": 0.7},
        {"sources": 1, "ai_probability": 0.1},
    ]
    
    result = apply_filter(items, min_confidence=4, min_ai_prob=50, enabled=False)
    assert len(result) == 3


def test_filter_by_confidence_only():
    """Test filtering by minimum confidence (sources)"""
    items = [
        {"sources": 2, "ai_probability": 0.8},
        {"sources": 5, "ai_probability": 0.3},
        {"sources": 4, "ai_probability": 0.2},
        {"sources": 1, "ai_probability": 0.9},
    ]
    
    result = apply_filter(items, min_confidence=4, min_ai_prob=0, enabled=True)
    assert len(result) == 2
    assert result[0]["sources"] == 5
    assert result[1]["sources"] == 4


def test_filter_by_ai_probability_only():
    """Test filtering by minimum AI probability"""
    items = [
        {"sources": 2, "ai_probability": 0.3},
        {"sources": 5, "ai_probability": 0.7},
        {"sources": 1, "ai_probability": 0.6},
        {"sources": 4, "ai_probability": 0.2},
    ]
    
    result = apply_filter(items, min_confidence=0, min_ai_prob=50, enabled=True)
    assert len(result) == 2
    assert result[0]["ai_probability"] == 0.7
    assert result[1]["ai_probability"] == 0.6


def test_filter_by_both_confidence_and_ai():
    """Test filtering by both confidence and AI probability (AND logic)"""
    items = [
        {"sources": 5, "ai_probability": 0.7},  # Pass both
        {"sources": 5, "ai_probability": 0.3},  # Pass confidence only
        {"sources": 2, "ai_probability": 0.7},  # Pass AI only
        {"sources": 2, "ai_probability": 0.3},  # Pass neither
    ]
    
    result = apply_filter(items, min_confidence=4, min_ai_prob=50, enabled=True)
    assert len(result) == 1
    assert result[0]["sources"] == 5
    assert result[0]["ai_probability"] == 0.7


def test_filter_boundary_confidence():
    """Test filtering at exact confidence boundary (4 stars)"""
    items = [
        {"sources": 3, "ai_probability": 0.5},
        {"sources": 4, "ai_probability": 0.5},
        {"sources": 5, "ai_probability": 0.5},
    ]
    
    result = apply_filter(items, min_confidence=4, min_ai_prob=0, enabled=True)
    assert len(result) == 2
    assert all(item["sources"] >= 4 for item in result)


def test_filter_boundary_ai_probability():
    """Test filtering at exact AI probability boundary (50%)"""
    items = [
        {"sources": 3, "ai_probability": 0.49},
        {"sources": 3, "ai_probability": 0.50},
        {"sources": 3, "ai_probability": 0.51},
    ]
    
    result = apply_filter(items, min_confidence=0, min_ai_prob=50, enabled=True)
    assert len(result) == 2
    assert all(item["ai_probability"] >= 0.50 for item in result)


def test_filter_empty_list():
    """Test that filtering an empty list returns empty"""
    result = apply_filter([], min_confidence=4, min_ai_prob=50, enabled=True)
    assert len(result) == 0


def test_filter_missing_fields():
    """Test filtering with items missing sources or ai_probability fields"""
    items = [
        {"sources": 5},  # Missing ai_probability
        {"ai_probability": 0.7},  # Missing sources
        {},  # Missing both
        {"sources": 5, "ai_probability": 0.7},  # Has both
    ]
    
    # With defaults (0 for missing fields), all should pass when filter is 0
    result = apply_filter(items, min_confidence=0, min_ai_prob=0, enabled=True)
    assert len(result) == 4


def test_filter_high_thresholds_filters_most():
    """Test that high thresholds filter out most items"""
    items = [
        {"sources": i, "ai_probability": i * 0.1} for i in range(1, 8)
    ]
    
    # With confidence=6 and AI=60%, should only get sources=6,7 with AI>=0.6
    result = apply_filter(items, min_confidence=6, min_ai_prob=60, enabled=True)
    assert len(result) == 2


def test_config_manager_update_filter_settings():
    """Test that filter settings can be updated and saved"""
    settings = AppSettings()
    
    # Update filter settings
    settings.FILTER_MIN_CONFIDENCE = 4
    settings.FILTER_MIN_AI_PROB = 50
    settings.FILTER_ENABLED = True
    
    # Verify they're set
    assert settings.FILTER_MIN_CONFIDENCE == 4
    assert settings.FILTER_MIN_AI_PROB == 50
    assert settings.FILTER_ENABLED == True
    
    # Get all settings should include them
    all_settings = settings.get_all_settings()
    assert all_settings['FILTER_MIN_CONFIDENCE'] == 4
    assert all_settings['FILTER_MIN_AI_PROB'] == 50
    assert all_settings['FILTER_ENABLED'] == True
