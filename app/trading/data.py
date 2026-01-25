"""Data fetching and caching for market data"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from functools import lru_cache

# Try to import MetaTrader5 - optional dependency
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    # Define constants for demo mode
    class MockMT5:
        TIMEFRAME_M1 = 1
        TIMEFRAME_M5 = 5
        TIMEFRAME_M15 = 15
        TIMEFRAME_M30 = 30
        TIMEFRAME_H1 = 60
        TIMEFRAME_H4 = 240
        TIMEFRAME_D1 = 1440
    mt5 = MockMT5()  # type: ignore

from app.trading.mt5_client import get_mt5_client
from app.core.logger import setup_logger

logger = setup_logger("data")


# Timeframe mapping
TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}


def get_timeframe_constant(timeframe_str: str) -> int:
    """Convert timeframe string to MT5 constant"""
    return TIMEFRAME_MAP.get(timeframe_str.upper(), mt5.TIMEFRAME_M15)


class DataProvider:
    """Provides market data with caching"""
    
    def __init__(self):
        self.mt5 = get_mt5_client()
        self._cache: Dict[str, tuple] = {}  # key -> (data, timestamp)
        self.cache_ttl_seconds = 30  # Cache for 30 seconds
    
    def get_ohlc_data(
        self, 
        symbol: str, 
        timeframe: str, 
        count: int = 500
    ) -> Optional[pd.DataFrame]:
        """
        Get OHLC data as DataFrame
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe string (e.g., 'M15')
            count: Number of candles
        
        Returns:
            DataFrame with columns: time, open, high, low, close, tick_volume, spread
        """
        cache_key = f"{symbol}_{timeframe}_{count}"
        now = datetime.now()
        
        # Check cache
        if cache_key in self._cache:
            data, cache_time = self._cache[cache_key]
            if (now - cache_time).total_seconds() < self.cache_ttl_seconds:
                return data.copy()
        
        # Fetch from MT5
        if not self.mt5.is_connected():
            logger.warning("MT5 not connected, cannot fetch data")
            return None
        
        try:
            tf_constant = get_timeframe_constant(timeframe)
            rates = self.mt5.get_rates(symbol, tf_constant, count)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No data returned for {symbol} {timeframe}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Rename columns for clarity
            df.columns = ['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
            
            # Cache result
            self._cache[cache_key] = (df.copy(), now)
            
            logger.debug(f"Fetched {len(df)} candles for {symbol} {timeframe}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLC data for {symbol}: {e}", exc_info=True)
            return None
    
    def get_current_tick(self, symbol: str) -> Optional[Dict]:
        """Get current tick (bid/ask) for symbol"""
        return self.mt5.get_tick(symbol)
    
    def get_spread(self, symbol: str) -> Optional[float]:
        """Get current spread in points"""
        tick = self.get_current_tick(symbol)
        if tick:
            return tick.get('ask', 0) - tick.get('bid', 0)
        return None
    
    def get_spread_pips(self, symbol: str) -> Optional[float]:
        """Get current spread in pips"""
        spread = self.get_spread(symbol)
        if spread is None:
            return None
        
        symbol_info = self.mt5.get_symbol_info(symbol)
        if symbol_info:
            point = symbol_info.get('point', 0.0001)
            if symbol_info.get('digits', 5) == 3 or symbol_info.get('digits', 5) == 2:
                # JPY pairs
                pip_value = point * 10
            else:
                pip_value = point * 10
            return spread / pip_value if pip_value > 0 else None
        return None
    
    def clear_cache(self):
        """Clear data cache"""
        self._cache.clear()
        logger.debug("Data cache cleared")


# Global data provider instance
_data_provider: Optional[DataProvider] = None


def get_data_provider() -> DataProvider:
    """Get global data provider instance"""
    global _data_provider
    if _data_provider is None:
        _data_provider = DataProvider()
    return _data_provider
