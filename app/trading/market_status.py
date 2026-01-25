"""Market status detector - handles Forex market hours and 24/7 crypto"""

from typing import Dict, Tuple
from datetime import datetime, time
from app.core.config import get_config
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client
from datetime import timedelta

logger = setup_logger("market_status")


class MarketStatus:
    """Detects market open/close status for Forex and Crypto"""
    
    # Forex market hours (all times in GMT/UTC)
    FOREX_MARKET_HOURS = {
        0: (21, 0),  # Sunday: 21:00 to 23:59
        1: (0, 21),  # Monday-Friday: 00:00 to 21:00
        2: (0, 21),
        3: (0, 21),
        4: (0, 21),
        5: (0, 21),
        6: (0, 21),  # Saturday: 00:00 to 21:00
    }
    
    # Cryptocurrencies - always open
    # Crypto symbols that should always be tradable (used to bypass Forex hours)
    CRYPTO_24_7 = [
        "BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "XRPUSD",
        "DOGEUSD", "ADAUSD", "DOTUSD", "LTCUSD", "AVAXUSD",
        # Legacy/extra coverage
        "XMRUSD", "BSVUSD", "BCHUSD", "EOSPUSD"
    ]
    
    def __init__(self):
        self.config = get_config()
        self.mt5 = get_mt5_client()
        self._blocked_until: Dict[str, datetime] = {}

    def block_symbol(self, symbol: str, minutes: int = 60):
        """Temporarily block a symbol after broker rejects for market closed."""
        # Do not block crypto; they trade 24/7 and broker closures are often transient
        if symbol in self.CRYPTO_24_7:
            return
        until = datetime.utcnow() + timedelta(minutes=minutes)
        self._blocked_until[symbol] = until
        logger.warning(f"Symbol {symbol} blocked until {until.isoformat()} (broker reported closed)")

    def _is_blocked(self, symbol: str) -> bool:
        expires = self._blocked_until.get(symbol)
        if not expires:
            return False
        if datetime.utcnow() > expires:
            self._blocked_until.pop(symbol, None)
            return False
        return True
    
    def is_forex_market_open(self, symbol: str) -> bool:
        """
        Check if market is open for symbol.
        Crypto: always open.
        Forex: requires BOTH broker trade_mode open AND time window open (UTC).
        """
        if symbol in self.CRYPTO_24_7:
            return True  # Crypto always open

        if self._is_blocked(symbol):
            return False

        time_open = self._is_market_open_by_time()

        # If time window says cerrado (e.g., fin de semana), short-circuit
        if not time_open:
            return False

        # Broker check
        if self.mt5.is_connected():
            try:
                symbol_info = self.mt5.get_symbol_info(symbol)
                if symbol_info:
                    trade_mode = symbol_info.get('trade_mode', 0)
                    # trade_mode: 2 or 4 = market open, others = closed
                    return trade_mode in [2, 4]
            except Exception as e:
                logger.warning(f"Error checking MT5 trade_mode for {symbol}: {e}")

        # If broker info not available, fall back to time check
        return time_open

    def is_symbol_open(self, symbol: str) -> bool:
        """Unified open check including temporary blocks."""
        # Crypto bypasses block and time checks (24/7)
        if symbol in self.CRYPTO_24_7:
            return True
        if self._is_blocked(symbol):
            return False
        return self.is_forex_market_open(symbol)
    
    def _is_market_open_by_time(self) -> bool:
        """Check if Forex is open based on current GMT time"""
        now = datetime.utcnow()
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        current_hour = now.hour
        
        # Convert to GMT/UTC weekday (0=Sunday, 6=Saturday for FOREX_MARKET_HOURS)
        gmt_weekday = (weekday + 1) % 7
        
        if gmt_weekday not in self.FOREX_MARKET_HOURS:
            return False
        
        start_hour, end_hour = self.FOREX_MARKET_HOURS[gmt_weekday]
        
        if start_hour < end_hour:
            # Normal range (e.g., 9-17)
            return start_hour <= current_hour < end_hour
        else:
            # Spans midnight (e.g., 21-00)
            return current_hour >= start_hour or current_hour < end_hour
    
    def get_market_status_text(self, symbol: str) -> str:
        """Get human-readable market status"""
        if symbol in self.CRYPTO_24_7:
            return f"{symbol}: 24/7 OPEN 💰"
        
        if self.is_forex_market_open(symbol):
            return f"{symbol}: OPEN ✅"
        else:
            return f"{symbol}: CLOSED ❌"
    
    def get_all_status(self) -> Dict[str, Tuple[str, bool]]:
        """Get status for all configured symbols"""
        all_symbols = self.config.trading.default_symbols + self.config.trading.crypto_symbols
        status = {}
        
        for symbol in all_symbols:
            is_open = self.is_forex_market_open(symbol)
            status_text = self.get_market_status_text(symbol)
            status[symbol] = (status_text, is_open)
        
        return status
    
    def get_tradeable_symbols(self) -> list:
        """Get list of symbols currently open for trading"""
        all_symbols = self.config.trading.default_symbols + self.config.trading.crypto_symbols
        tradeable = [s for s in all_symbols if self.is_forex_market_open(s)]
        
        logger.info(f"Tradeable symbols: {tradeable}")
        return tradeable


# Global instance
_market_status = None


def get_market_status() -> MarketStatus:
    """Get global market status instance"""
    global _market_status
    if _market_status is None:
        _market_status = MarketStatus()
    return _market_status
