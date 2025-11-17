"""Cache manager for improving system performance.

This module implements caching strategies to speed up expensive operations:
- LRU cache for pure functions
- Disk cache for large computations
"""
import pickle
import os
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from pathlib import Path
import hashlib
import json


# Cache directory configuration
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


def get_cache_key(*args, **kwargs):
    """Generate a unique cache key from arguments."""
    key_data = {
        'args': str(args),
        'kwargs': str(sorted(kwargs.items()))
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


def disk_cache(ttl_hours=24):
    """Disk cache decorator with TTL (time-to-live).
    
    Args:
        ttl_hours: Cache validity in hours (default: 24 hours)
    
    Example:
        @disk_cache(ttl_hours=12)
        def expensive_function(arg1, arg2):
            # ... expensive computation
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}_{get_cache_key(*args, **kwargs)}"
            cache_file = CACHE_DIR / f"{cache_key}.pkl"
            
            # Check if cache exists and is valid
            if cache_file.exists():
                # Check TTL
                file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - file_mtime < timedelta(hours=ttl_hours):
                    try:
                        with open(cache_file, 'rb') as f:
                            return pickle.load(f)
                    except Exception as e:
                        print(f"Cache load error: {e}")
                        # Fall through to compute
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Save to cache
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(result, f)
            except Exception as e:
                print(f"Cache save error: {e}")
            
            return result
        
        return wrapper
    return decorator


def clear_cache(func_name=None):
    """Clear cache files.
    
    Args:
        func_name: If provided, only clear cache for this function.
                   If None, clear all cache files.
    """
    if func_name:
        pattern = f"{func_name}_*.pkl"
        for cache_file in CACHE_DIR.glob(pattern):
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"Error deleting cache file {cache_file}: {e}")
    else:
        for cache_file in CACHE_DIR.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"Error deleting cache file {cache_file}: {e}")


def get_cache_stats():
    """Get cache statistics.
    
    Returns:
        dict: Cache statistics including file count and total size
    """
    cache_files = list(CACHE_DIR.glob("*.pkl"))
    total_size = sum(f.stat().st_size for f in cache_files)
    
    return {
        'file_count': len(cache_files),
        'total_size_mb': total_size / (1024 * 1024),
        'cache_dir': str(CACHE_DIR)
    }


# Convenience function for daily predictions cache
def get_daily_predictions_cache_key(data_hash):
    """Get cache key for daily predictions.
    
    Args:
        data_hash: Hash of the data (e.g., last MaSoKy)
    
    Returns:
        Path to cache file
    """
    date_str = datetime.now().date().isoformat()
    return CACHE_DIR / f"daily_predictions_{date_str}_{data_hash}.pkl"


def save_daily_predictions(predictions, data_hash):
    """Save daily predictions to cache.
    
    Args:
        predictions: The predictions data to cache
        data_hash: Hash of the data used to generate predictions
    """
    cache_file = get_daily_predictions_cache_key(data_hash)
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(predictions, f)
    except Exception as e:
        print(f"Error saving daily predictions cache: {e}")


def load_daily_predictions(data_hash):
    """Load daily predictions from cache.
    
    Args:
        data_hash: Hash of the data used to generate predictions
    
    Returns:
        Cached predictions if available and valid, None otherwise
    """
    cache_file = get_daily_predictions_cache_key(data_hash)
    
    if cache_file.exists():
        # Check if cache is from today
        file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if file_mtime.date() == datetime.now().date():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Error loading daily predictions cache: {e}")
    
    return None


# Add cache/ to .gitignore if not already there
def ensure_cache_in_gitignore():
    """Ensure cache directory is in .gitignore."""
    gitignore_path = Path(".gitignore")
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        if 'cache/' not in content:
            with open(gitignore_path, 'a') as f:
                f.write('\n# Cache directory\ncache/\n')
    else:
        with open(gitignore_path, 'w') as f:
            f.write('# Cache directory\ncache/\n')


# Initialize cache directory and gitignore
ensure_cache_in_gitignore()


if __name__ == '__main__':
    # Test cache functionality
    print("Cache Manager Test")
    print("-" * 50)
    
    @disk_cache(ttl_hours=1)
    def test_function(x, y):
        print(f"Computing {x} + {y}...")
        return x + y
    
    # First call - should compute
    result1 = test_function(1, 2)
    print(f"Result 1: {result1}")
    
    # Second call - should use cache
    result2 = test_function(1, 2)
    print(f"Result 2: {result2}")
    
    # Get stats
    stats = get_cache_stats()
    print(f"\nCache stats: {stats}")
    
    # Clear cache
    clear_cache()
    print("\nCache cleared!")
