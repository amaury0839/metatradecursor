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
    import sys
    print(f"✅ MetaTrader5 imported successfully from {mt5.__file__}", file=sys.stderr)
except (ImportError, ModuleNotFoundError, OSError) as e:
    # MetaTrader5 not available - create mock for demo mode
    MT5_AVAILABLE = False
    import sys
    print(f"⚠️ MetaTrader5 import failed: {e}", file=sys.stderr)
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
        # Check if MT5 credentials are configured
        if not self.config.mt5.login or not self.config.mt5.password or not self.config.mt5.server:
            logger.warning("MT5 credentials not configured (cloud mode). Running in demo mode.")
            self.connected = True  # Simulate connection for demo
            self.account_info = {
                'login': 0,
                'balance': 10000.0,
                'equity': 10000.0,
                'server': 'Demo',
            }
            return True
            
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
            # Initialize MT5 (prefer explicit terminal path when provided)
            init_result = False
            if self.config.mt5.path:
                logger.info(f"Attempting MT5 connection with path: {self.config.mt5.path}")
                init_result = mt5.initialize(path=self.config.mt5.path)
            else:
                logger.info("Attempting MT5 connection (no explicit path)")

            if not init_result:
                logger.info("Retrying MT5 initialization without explicit path...")
                init_result = mt5.initialize()
            
            if not init_result:
                error_code, error_msg = mt5.last_error()
                # Only fail if it's NOT an authorization error
                # Authorization errors can happen if MT5 needs reconnection
                if error_code != -6:  # -6 is "Authorization failed"
                    logger.error(f"MT5 initialization failed: ({error_code}, '{error_msg}')")
                    logger.info("MT5 must be running. Make sure MT5 is open and not minimized.")
                    return False
                else:
                    # Authorization error - try to reconnect despite this
                    logger.info(f"MT5 returned authorization error, but continuing to try login...")
            
            # Give the terminal a moment to finish IPC setup
            time.sleep(1)
            logger.info("✅ MT5 initialized successfully")
            
            # Login - try multiple methods
            logger.info(f"Attempting MT5 login for account {self.config.mt5.login}...")
            
            # Method 1: Try with password from config
            authorized = mt5.login(
                login=self.config.mt5.login,
                password=self.config.mt5.password,
                server=self.config.mt5.server
            )
            
            if not authorized:
                # Method 2: Try without password (uses saved credentials in MT5)
                logger.warning(f"Login with password failed, trying without password...")
                authorized = mt5.login(
                    login=self.config.mt5.login,
                    server=self.config.mt5.server
                )
            
            if not authorized:
                error = mt5.last_error()
                logger.error(f"MT5 login failed: {error}")
                # Don't shutdown - keep trying
                return False
            
            logger.info("✅ MT5 Login successful!")
            
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
        if not MT5_AVAILABLE:
            return True  # Demo mode - always "connected"
        
        # Try to get account info to verify MT5 is running and logged in
        try:
            # Initialize if needed
            if not mt5.initialize():
                # Try anyway - it might already be initialized
                pass
            
            account_info = mt5.account_info()
            if account_info is not None:
                self.account_info = account_info._asdict()
                self.connected = True
                return True
            else:
                self.connected = False
                return False
        except Exception as e:
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
    
    def ensure_symbol(self, symbol: str) -> bool:
        """
        Ensure symbol is available and selected in MT5
        
        🔧 CRITICAL: Must be called BEFORE copy_rates_from_pos() to ensure rates exist
        
        Args:
            symbol: Symbol name (e.g., 'EURUSD')
        
        Returns:
            True if symbol is available, False otherwise
        """
        if not self.is_connected():
            logger.warning(f"Cannot ensure symbol {symbol}: MT5 not connected")
            return False
        
        if not MT5_AVAILABLE:
            # Demo mode - always return True
            return True
        
        try:
            # First check if symbol is visible in Market Watch
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.warning(f"{symbol}: Not found in MT5")
                return False
            
            # If not visible, try to add to Market Watch
            if not symbol_info.visible:
                logger.info(f"{symbol}: Hidden in Market Watch, attempting to show...")
                if not mt5.symbol_select(symbol, True):
                    logger.error(f"{symbol}: Failed to add to Market Watch")
                    return False
                logger.info(f"{symbol}: ✅ Added to Market Watch")
            else:
                logger.debug(f"{symbol}: Already visible in Market Watch")
            
            return True
        except Exception as e:
            logger.error(f"Error ensuring symbol {symbol}: {e}")
            return False
    
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
            # 🔧 CRITICAL: Ensure symbol is visible/selected BEFORE fetching rates
            if not self.ensure_symbol(symbol):
                logger.error(f"{symbol}: Cannot fetch rates - symbol not available in MT5")
                return None
            
            if start_time:
                rates = mt5.copy_rates_from(symbol, timeframe, start_time, count)
            else:
                rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"{symbol}: No OHLC data returned from MT5 (rates=None or empty)")
                return None
            
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

    def symbol_info_tick(self, symbol: str) -> Optional[Dict]:
        """Compatibility helper returning symbol_info_tick as dict (or None)."""
        if not self.is_connected():
            return None
        if not MT5_AVAILABLE:
            return self.get_tick(symbol)
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return tick._asdict()
        except Exception as e:
            logger.error(f"Error getting symbol_info_tick for {symbol}: {e}")
        return None
    
    def order_calc_margin(self, order_type: int, symbol: str, volume: float, price: float) -> Optional[float]:
        """Proxy for mt5.order_calc_margin; returns None in demo mode."""
        if not self.is_connected() or not MT5_AVAILABLE:
            return None
        try:
            return mt5.order_calc_margin(order_type, symbol, volume, price)
        except Exception as e:
            logger.warning(f"order_calc_margin failed for {symbol}: {e}")
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
    
    def get_history_deals(self, from_date: datetime, to_date: Optional[datetime] = None) -> List[Dict]:
        """
        Get historical deals (closed positions)
        
        Args:
            from_date: Start date for history
            to_date: End date for history (defaults to now)
        
        Returns:
            List of deal dicts
        """
        if not self.is_connected():
            return []
        
        if not MT5_AVAILABLE:
            # Return empty list in demo mode
            return []
        
        try:
            if to_date is None:
                to_date = datetime.now()
            
            deals = mt5.history_deals_get(from_date, to_date)
            
            if deals:
                return [d._asdict() for d in deals]
        except Exception as e:
            logger.error(f"Error getting history deals: {e}")
        
        return []
    
    def get_history_orders(self, from_date: datetime, to_date: Optional[datetime] = None) -> List[Dict]:
        """
        Get historical orders
        
        Args:
            from_date: Start date for history
            to_date: End date for history (defaults to now)
        
        Returns:
            List of order dicts
        """
        if not self.is_connected():
            return []
        
        if not MT5_AVAILABLE:
            # Return empty list in demo mode
            return []
        
        try:
            if to_date is None:
                to_date = datetime.now()
            
            orders = mt5.history_orders_get(from_date, to_date)
            
            if orders:
                return [o._asdict() for o in orders]
        except Exception as e:
            logger.error(f"Error getting history orders: {e}")
        
        return []


# Global MT5 client instance
_mt5_client: Optional[MT5Client] = None


def get_mt5_client() -> MT5Client:
    """Get global MT5 client instance"""
    global _mt5_client
    if _mt5_client is None:
        _mt5_client = MT5Client()
    return _mt5_client
