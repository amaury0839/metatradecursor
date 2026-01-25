"""MetaTrader 5 client for connection and basic operations"""

# IMPORTANT: MetaTrader5 is OPTIONAL - wrapped in try/except for demo mode
# This allows the bot to run without MT5 installed (e.g., on Streamlit Cloud)

from typing import Optional, Dict, List, Tuple
from datetime import datetime
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import get_config
from app.core.logger import setup_logger

# Try to import MetaTrader5 - optional dependency
# This MUST be wrapped in try/except to allow demo mode without MT5
MT5_AVAILABLE = False
try:
    import MetaTrader5 as mt5  # type: ignore
    MT5_AVAILABLE = True
except (ImportError, ModuleNotFoundError, OSError):
    # MetaTrader5 not available - create mock for demo mode
    MT5_AVAILABLE = False
    # Create a minimal mock mt5 module for demo mode
    class MockMT5:
        """Mock MT5 module for demo mode when MetaTrader5 is not installed"""
        pass
    mt5 = MockMT5()  # type: ignore

logger = setup_logger("mt5_client")


class MT5Client:
    """MetaTrader 5 connection and operations client"""
    
    def __init__(self):
        self.config = get_config()
        self.connected = False
        self.account_info: Optional[Dict] = None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def connect(self) -> bool:
        """
        Connect to MetaTrader 5
        
        Returns:
            True if connection successful, False otherwise
        """
        if not MT5_AVAILABLE:
            logger.warning("MetaTrader5 package not available. Running in demo mode.")
            self.connected = True  # Simulate connection for demo
            self.account_info = {
                'login': 0,
                'balance': 10000.0,
                'equity': 10000.0,
                'server': 'Demo',
            }
            return True
        
        try:
            # Initialize MT5
            if not mt5.initialize(path=self.config.mt5.path):
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                return False
            
            # Login
            authorized = mt5.login(
                login=self.config.mt5.login,
                password=self.config.mt5.password,
                server=self.config.mt5.server
            )
            
            if not authorized:
                error = mt5.last_error()
                logger.error(f"MT5 login failed: {error}")
                mt5.shutdown()
                return False
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                logger.error("Failed to get account info")
                mt5.shutdown()
                return False
            
            self.account_info = account_info._asdict()
            self.connected = True
            
            logger.info(
                f"Connected to MT5 - Account: {account_info.login}, "
                f"Balance: {account_info.balance}, Equity: {account_info.equity}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}", exc_info=True)
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from MetaTrader 5"""
        if self.connected:
            if MT5_AVAILABLE:
                mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")
    
    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        if not self.connected:
            return False
        
        if not MT5_AVAILABLE:
            return True  # Demo mode - always "connected"
        
        # Verify connection is still alive
        try:
            account_info = mt5.account_info()
            if account_info is None:
                self.connected = False
                return False
            self.account_info = account_info._asdict()
            return True
        except Exception:
            self.connected = False
            return False
    
    def get_account_info(self) -> Optional[Dict]:
        """Get current account information"""
        if not self.is_connected():
            return None
        
        if not MT5_AVAILABLE:
            # Return demo account info
            return self.account_info
        
        try:
            account_info = mt5.account_info()
            if account_info:
                self.account_info = account_info._asdict()
                return self.account_info
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
        
        return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Get symbol information
        
        Args:
            symbol: Symbol name (e.g., 'EURUSD')
        
        Returns:
            Symbol info dict or None
        """
        if not self.is_connected():
            return None
        
        if not MT5_AVAILABLE:
            # Return mock symbol info for demo
            return {
                'name': symbol,
                'point': 0.0001,
                'digits': 5,
                'trade_mode': 4,  # Demo mode
                'volume_min': 0.01,
                'volume_max': 100.0,
                'volume_step': 0.01,
                'trade_contract_size': 100000,
                'trade_tick_value': 1.0,
            }
        
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                return symbol_info._asdict()
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
        
        return None
    
    def get_symbols(self) -> List[str]:
        """Get list of available symbols"""
        if not self.is_connected():
            return []
        
        if not MT5_AVAILABLE:
            # Return default symbols for demo
            return ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
        
        try:
            symbols = mt5.symbols_get()
            if symbols:
                return [s.name for s in symbols]
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
        
        return []
    
    def get_rates(
        self, 
        symbol: str, 
        timeframe: int, 
        count: int = 1000,
        start_time: Optional[datetime] = None
    ) -> Optional[List]:
        """
        Get historical rates (candles)
        
        Args:
            symbol: Symbol name
            timeframe: MT5 timeframe constant (e.g., mt5.TIMEFRAME_M15)
            count: Number of candles to retrieve
            start_time: Start time (optional)
        
        Returns:
            List of rate tuples or None
        """
        if not self.is_connected():
            return None
        
        if not MT5_AVAILABLE:
            # Return mock data for demo
            import random
            base_price = 1.10000 if "USD" in symbol else 100.0
            mock_rates = []
            for i in range(count):
                price = base_price + random.uniform(-0.01, 0.01)
                mock_rates.append({
                    'time': int((datetime.now().timestamp() - (count - i) * 900)),
                    'open': price,
                    'high': price + random.uniform(0, 0.001),
                    'low': price - random.uniform(0, 0.001),
                    'close': price + random.uniform(-0.0005, 0.0005),
                    'tick_volume': random.randint(100, 1000),
                    'spread': 2,
                    'real_volume': 0
                })
            return mock_rates
        
        try:
            if start_time:
                rates = mt5.copy_rates_from(symbol, timeframe, start_time, count)
            else:
                rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            
            return rates.tolist() if rates is not None and len(rates) > 0 else None
        except Exception as e:
            logger.error(f"Error getting rates for {symbol}: {e}")
            return None
    
    def get_tick(self, symbol: str) -> Optional[Dict]:
        """
        Get last tick for symbol
        
        Args:
            symbol: Symbol name
        
        Returns:
            Tick dict or None
        """
        if not self.is_connected():
            return None
        
        if not MT5_AVAILABLE:
            # Return mock tick for demo
            import random
            base_price = 1.10000 if "USD" in symbol else 100.0
            price = base_price + random.uniform(-0.01, 0.01)
            return {
                'time': int(datetime.now().timestamp()),
                'bid': price - 0.0001,
                'ask': price + 0.0001,
                'last': price,
                'volume': random.randint(100, 1000),
            }
        
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return tick._asdict()
        except Exception as e:
            logger.error(f"Error getting tick for {symbol}: {e}")
        
        return None
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get open positions
        
        Args:
            symbol: Filter by symbol (optional)
        
        Returns:
            List of position dicts
        """
        if not self.is_connected():
            return []
        
        if not MT5_AVAILABLE:
            # Return empty list in demo mode
            return []
        
        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions:
                return [p._asdict() for p in positions]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
        
        return []
    
    def get_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get pending orders
        
        Args:
            symbol: Filter by symbol (optional)
        
        Returns:
            List of order dicts
        """
        if not self.is_connected():
            return []
        
        if not MT5_AVAILABLE:
            # Return empty list in demo mode
            return []
        
        try:
            if symbol:
                orders = mt5.orders_get(symbol=symbol)
            else:
                orders = mt5.orders_get()
            
            if orders:
                return [o._asdict() for o in orders]
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
        
        return []


# Global MT5 client instance
_mt5_client: Optional[MT5Client] = None


def get_mt5_client() -> MT5Client:
    """Get global MT5 client instance"""
    global _mt5_client
    if _mt5_client is None:
        _mt5_client = MT5Client()
    return _mt5_client
