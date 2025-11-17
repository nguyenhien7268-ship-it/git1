"""Unit tests for logic/cache_manager.py module."""

import pytest
import os
import sys
import time
from pathlib import Path
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from logic.cache_manager import (
    disk_cache,
    clear_cache,
    get_cache_stats,
    get_cache_key,
    save_daily_predictions,
    load_daily_predictions,
    CACHE_DIR,
)


class TestCacheKey:
    """Tests for cache key generation."""

    def test_get_cache_key_same_args(self):
        """Test that same arguments produce same key."""
        key1 = get_cache_key(1, 2, 3)
        key2 = get_cache_key(1, 2, 3)
        assert key1 == key2

    def test_get_cache_key_different_args(self):
        """Test that different arguments produce different keys."""
        key1 = get_cache_key(1, 2, 3)
        key2 = get_cache_key(1, 2, 4)
        assert key1 != key2

    def test_get_cache_key_with_kwargs(self):
        """Test cache key with keyword arguments."""
        key1 = get_cache_key(x=1, y=2)
        key2 = get_cache_key(x=1, y=2)
        key3 = get_cache_key(y=2, x=1)  # Different order, should be same
        assert key1 == key2
        assert key1 == key3


class TestDiskCache:
    """Tests for disk_cache decorator."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Clear cache before test
        clear_cache()
        yield
        # Clear cache after test
        clear_cache()

    def test_disk_cache_saves_result(self):
        """Test that disk cache saves and retrieves results."""
        call_count = {"count": 0}

        @disk_cache(ttl_hours=1)
        def test_func(x):
            call_count["count"] += 1
            return x * 2

        # First call - should compute
        result1 = test_func(5)
        assert result1 == 10
        assert call_count["count"] == 1

        # Second call - should use cache
        result2 = test_func(5)
        assert result2 == 10
        assert call_count["count"] == 1  # Should not increment

    def test_disk_cache_different_args(self):
        """Test that different args create different cache entries."""
        call_count = {"count": 0}

        @disk_cache(ttl_hours=1)
        def test_func(x):
            call_count["count"] += 1
            return x * 2

        result1 = test_func(5)
        result2 = test_func(10)

        assert result1 == 10
        assert result2 == 20
        assert call_count["count"] == 2  # Both computed

        # Cache should work for both
        result3 = test_func(5)
        result4 = test_func(10)
        assert call_count["count"] == 2  # No new computations

    def test_disk_cache_with_complex_types(self):
        """Test caching with lists and dicts."""

        @disk_cache(ttl_hours=1)
        def test_func(items):
            return sum(items)

        result1 = test_func([1, 2, 3])
        result2 = test_func([1, 2, 3])

        assert result1 == 6
        assert result2 == 6


class TestCacheManagement:
    """Tests for cache management functions."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        clear_cache()
        yield
        clear_cache()

    def test_clear_cache_all(self):
        """Test clearing all cache files."""

        @disk_cache(ttl_hours=1)
        def test_func(x):
            return x * 2

        # Create some cache entries
        test_func(1)
        test_func(2)
        test_func(3)

        # Check cache exists
        stats_before = get_cache_stats()
        assert stats_before["file_count"] == 3

        # Clear all cache
        clear_cache()

        # Check cache cleared
        stats_after = get_cache_stats()
        assert stats_after["file_count"] == 0

    def test_clear_cache_specific_function(self):
        """Test clearing cache for specific function."""

        @disk_cache(ttl_hours=1)
        def func1(x):
            return x * 2

        @disk_cache(ttl_hours=1)
        def func2(x):
            return x * 3

        # Create cache entries
        func1(1)
        func2(1)

        stats_before = get_cache_stats()
        assert stats_before["file_count"] == 2

        # Clear only func1 cache
        clear_cache("func1")

        stats_after = get_cache_stats()
        assert stats_after["file_count"] == 1

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        stats = get_cache_stats()

        assert "file_count" in stats
        assert "total_size_mb" in stats
        assert "cache_dir" in stats
        assert isinstance(stats["file_count"], int)
        assert isinstance(stats["total_size_mb"], float)


class TestDailyPredictionsCache:
    """Tests for daily predictions caching."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        clear_cache()
        yield
        clear_cache()

    def test_save_and_load_daily_predictions(self):
        """Test saving and loading daily predictions."""
        test_data = {"23001": {"loto": "01", "prob": 0.75}, "23002": {"loto": "02", "prob": 0.65}}
        data_hash = "test_hash_123"

        # Save predictions
        save_daily_predictions(test_data, data_hash)

        # Load predictions
        loaded_data = load_daily_predictions(data_hash)

        assert loaded_data == test_data

    def test_load_nonexistent_predictions(self):
        """Test loading predictions that don't exist."""
        result = load_daily_predictions("nonexistent_hash")
        assert result is None

    def test_daily_predictions_different_hash(self):
        """Test that different hashes don't interfere."""
        data1 = {"key1": "value1"}
        data2 = {"key2": "value2"}

        save_daily_predictions(data1, "hash1")
        save_daily_predictions(data2, "hash2")

        loaded1 = load_daily_predictions("hash1")
        loaded2 = load_daily_predictions("hash2")

        assert loaded1 == data1
        assert loaded2 == data2


class TestCachePerformance:
    """Tests for cache performance benefits."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        clear_cache()
        yield
        clear_cache()

    def test_cache_improves_performance(self):
        """Test that caching actually improves performance."""
        import time

        @disk_cache(ttl_hours=1)
        def slow_function(x):
            time.sleep(0.1)  # Simulate slow computation
            return x * 2

        # First call - should be slow
        start1 = time.time()
        result1 = slow_function(5)
        duration1 = time.time() - start1

        # Second call - should be fast (from cache)
        start2 = time.time()
        result2 = slow_function(5)
        duration2 = time.time() - start2

        assert result1 == result2 == 10
        assert duration2 < duration1 * 0.5  # Cached call should be much faster


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
