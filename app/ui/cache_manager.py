"""Advanced caching system for UI performance"""

import time
from typing import Any, Optional, Dict, Callable
from functools import wraps
import streamlit as st
from datetime import datetime, timedelta
import json

class CacheManager:
    """High-performance cache with TTL and compression"""
    
    def __init__(self):
        self.memory_cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}
        self.ttls: Dict[str, int] = {}
        
    def set(self, key: str, value: Any, ttl: int = 300):
        """Store with TTL (seconds)"""
        self.memory_cache[key] = value
        self.timestamps[key] = time.time()
        self.ttls[key] = ttl
        
    def get(self, key: str) -> Optional[Any]:
        """Retrieve if not expired"""
        if key not in self.memory_cache:
            return None
        
        age = time.time() - self.timestamps[key]
        if age > self.ttls.get(key, 300):
            del self.memory_cache[key]
            return None
        return self.memory_cache[key]
    
    def clear_expired(self):
        """Remove all expired entries"""
        now = time.time()
        expired = [
            k for k, ts in self.timestamps.items()
            if now - ts > self.ttls.get(k, 300)
        ]
        for k in expired:
            self.memory_cache.pop(k, None)
            self.timestamps.pop(k, None)
            self.ttls.pop(k, None)
    
    def clear(self):
        """Clear all cache"""
        self.memory_cache.clear()
        self.timestamps.clear()
        self.ttls.clear()


# Global cache instance
_cache = CacheManager()

def get_cache() -> CacheManager:
    """Get global cache manager"""
    return _cache


def streamlit_cache(ttl: int = 60, show_spinner: bool = False):
    """Decorator for cached Streamlit functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check cache
            cached = get_cache().get(key)
            if cached is not None:
                return cached
            
            # Execute function
            if show_spinner:
                with st.spinner(f"Loading {func.__name__}..."):
                    result = func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Store in cache
            get_cache().set(key, result, ttl)
            return result
        return wrapper
    return decorator


class HistoricalDataCache:
    """Optimized cache for historical trading data"""
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.access_count = {}
        self.last_update = {}
        
    def get(self, key: str, max_age_seconds: int = 3600) -> Optional[Any]:
        """Get with age validation"""
        if key not in self.cache:
            return None
        
        age = time.time() - self.last_update.get(key, 0)
        if age > max_age_seconds:
            self.cache.pop(key, None)
            return None
        
        self.access_count[key] = self.access_count.get(key, 0) + 1
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """Store with LRU eviction"""
        # Evict least recently used if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            lru_key = min(self.access_count, key=self.access_count.get)
            self.cache.pop(lru_key, None)
            self.access_count.pop(lru_key, None)
        
        self.cache[key] = value
        self.last_update[key] = time.time()
        self.access_count[key] = 0
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.access_count.clear()
        self.last_update.clear()


# Global historical cache
_historical_cache = HistoricalDataCache()

def get_historical_cache() -> HistoricalDataCache:
    """Get historical data cache"""
    return _historical_cache
