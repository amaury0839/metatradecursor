"""
Trading Engines - Separate strategies for Scalping, Swing, and Crypto
Each engine has its own rules, risk parameters, and decision logic
"""

from typing import Dict, Optional, Tuple
from abc import ABC, abstractmethod
from app.core.logger import setup_logger
from app.trading.risk import get_risk_manager
from app.trading.data import get_data_provider
from app.trading.mt5_client import get_mt5_client

logger = setup_logger("trading_engines")


class BaseTradingEngine(ABC):
    """Base class for all trading engines"""
    
    def __init__(self, name: str):
        self.name = name
        self.risk_manager = get_risk_manager()
        self.data_provider = get_data_provider()
        self.mt5_client = get_mt5_client()
        logger.info(f"✅ {self.name} initialized")
    
    @abstractmethod
    def get_max_spread(self) -> float:
        """Maximum spread allowed for this engine"""
        pass
    
    @abstractmethod
    def get_risk_percent(self) -> float:
        """Risk percentage per trade for this engine"""
        pass
    
    @abstractmethod
    def get_max_positions(self) -> int:
        """Maximum concurrent positions for this engine"""
        pass
    
    @abstractmethod
    def should_skip_low_volume(self, symbol: str, calculated_volume: float) -> bool:
        """Determine if trade should be skipped due to low volume"""
        pass
    
    @abstractmethod
    def get_stop_loss_multiplier(self) -> float:
        """ATR multiplier for stop loss"""
        pass
    
    @abstractmethod
    def get_take_profit_multiplier(self) -> float:
        """ATR multiplier for take profit"""
        pass
    
    def validate_trade(self, symbol: str, action: str, volume: float) -> Tuple[bool, Dict[str, str]]:
        """Common validation logic for all engines"""
        
        # Check spread first (Gate 1)
        spread_pips = self.data_provider.get_spread_pips(symbol)
        if spread_pips is not None and spread_pips > self.get_max_spread():
            return False, {"spread": f"Spread {spread_pips:.2f} > max {self.get_max_spread()}"}
        
        # Check if volume should be skipped
        if self.should_skip_low_volume(symbol, volume):
            return False, {"volume": f"Volume {volume:.4f} too low, skipped by {self.name}"}
        
        # Engine-specific checks passed
        return True, {}


class ScalpingEngine(BaseTradingEngine):
    """
    Scalping Engine - Fast trades, tight spreads, strict volume requirements
    
    Rules:
    - Max spread: 5 pips (forex) / 100 pips (crypto)
    - Risk: 1.5% per trade
    - Max positions: 30
    - SKIP if volume < minimum (NO CLAMP)
    - SL: 1.2x ATR (tight)
    - TP: 1.8x ATR (fast exits)
    """
    
    def __init__(self):
        super().__init__("ScalpingEngine")
        self.forex_max_spread = 5.0
        self.crypto_max_spread = 100.0
        self.risk_pct = 1.5
        self.max_positions = 30
        self.sl_multiplier = 1.2
        self.tp_multiplier = 1.8
    
    def get_max_spread(self) -> float:
        return self.forex_max_spread
    
    def get_risk_percent(self) -> float:
        return self.risk_pct
    
    def get_max_positions(self) -> int:
        return self.max_positions
    
    def should_skip_low_volume(self, symbol: str, calculated_volume: float) -> bool:
        """Scalping: SKIP if volume < minimum (strict requirement)"""
        min_lot = self.risk_manager.get_min_lot_for_symbol(symbol)
        if calculated_volume < min_lot:
            logger.info(f"🚫 SCALPING SKIP: {symbol} vol {calculated_volume:.4f} < min {min_lot:.4f}")
            return True
        return False
    
    def get_stop_loss_multiplier(self) -> float:
        return self.sl_multiplier
    
    def get_take_profit_multiplier(self) -> float:
        return self.tp_multiplier


class SwingEngine(BaseTradingEngine):
    """
    Swing Engine - Medium-term trades, wider stops, flexible volume
    
    Rules:
    - Max spread: 10 pips (forex) / 200 pips (crypto)
    - Risk: 2.0% per trade
    - Max positions: 20
    - Allow smaller volumes (more flexible)
    - SL: 2.0x ATR (wider)
    - TP: 3.5x ATR (bigger targets)
    """
    
    def __init__(self):
        super().__init__("SwingEngine")
        self.forex_max_spread = 10.0
        self.crypto_max_spread = 200.0
        self.risk_pct = 2.0
        self.max_positions = 20
        self.sl_multiplier = 2.0
        self.tp_multiplier = 3.5
    
    def get_max_spread(self) -> float:
        return self.forex_max_spread
    
    def get_risk_percent(self) -> float:
        return self.risk_pct
    
    def get_max_positions(self) -> int:
        return self.max_positions
    
    def should_skip_low_volume(self, symbol: str, calculated_volume: float) -> bool:
        """Swing: More flexible, allow 80% of minimum"""
        min_lot = self.risk_manager.get_min_lot_for_symbol(symbol)
        flexible_min = min_lot * 0.8  # Allow 80% of minimum
        if calculated_volume < flexible_min:
            logger.info(f"🚫 SWING SKIP: {symbol} vol {calculated_volume:.4f} < flexible min {flexible_min:.4f}")
            return True
        return False
    
    def get_stop_loss_multiplier(self) -> float:
        return self.sl_multiplier
    
    def get_take_profit_multiplier(self) -> float:
        return self.tp_multiplier


class CryptoEngine(BaseTradingEngine):
    """
    Crypto Engine - 24/7 trading, high volatility, wider spreads acceptable
    
    Rules:
    - Max spread: 300 pips (crypto has wide spreads)
    - Risk: 2.5% per trade (higher volatility)
    - Max positions: 15
    - Very flexible volume (crypto has different lot sizes)
    - SL: 2.5x ATR (wide for volatility)
    - TP: 4.0x ATR (big moves)
    """
    
    def __init__(self):
        super().__init__("CryptoEngine")
        self.max_spread = 300.0
        self.risk_pct = 2.5
        self.max_positions = 15
        self.sl_multiplier = 2.5
        self.tp_multiplier = 4.0
    
    def get_max_spread(self) -> float:
        return self.max_spread
    
    def get_risk_percent(self) -> float:
        return self.risk_pct
    
    def get_max_positions(self) -> int:
        return self.max_positions
    
    def should_skip_low_volume(self, symbol: str, calculated_volume: float) -> bool:
        """Crypto: Very flexible, allow 50% of minimum (crypto lots vary greatly)"""
        min_lot = self.risk_manager.get_min_lot_for_symbol(symbol)
        flexible_min = min_lot * 0.5  # Allow 50% of minimum for crypto
        if calculated_volume < flexible_min:
            logger.info(f"🚫 CRYPTO SKIP: {symbol} vol {calculated_volume:.4f} < flexible min {flexible_min:.4f}")
            return True
        return False
    
    def get_stop_loss_multiplier(self) -> float:
        return self.sl_multiplier
    
    def get_take_profit_multiplier(self) -> float:
        return self.tp_multiplier


class TradingEngineSelector:
    """
    Selects the appropriate trading engine based on symbol and market conditions
    """
    
    CRYPTO_SYMBOLS = [
        'BTCUSD', 'ETHUSD', 'BNBUSD', 'SOLUSD', 'XRPUSD',
        'ADAUSD', 'DOTUSD', 'LTCUSD', 'UNIUSD', 'DOGEUSD'
    ]
    
    def __init__(self):
        self.scalping_engine = ScalpingEngine()
        self.swing_engine = SwingEngine()
        self.crypto_engine = CryptoEngine()
        logger.info("✅ TradingEngineSelector initialized with 3 engines")
    
    def select_engine(self, symbol: str, timeframe: str = "M15") -> BaseTradingEngine:
        """
        Select appropriate engine based on symbol and timeframe
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M1, M5, M15, H1, H4, D1)
        
        Returns:
            Appropriate trading engine
        """
        # Crypto symbols always use CryptoEngine
        if any(crypto in symbol.upper() for crypto in self.CRYPTO_SYMBOLS):
            logger.debug(f"Selected CryptoEngine for {symbol}")
            return self.crypto_engine
        
        # Timeframe-based selection for forex
        if timeframe in ["M1", "M5", "M15"]:
            # Short timeframes = scalping
            logger.debug(f"Selected ScalpingEngine for {symbol} on {timeframe}")
            return self.scalping_engine
        else:
            # Longer timeframes = swing
            logger.debug(f"Selected SwingEngine for {symbol} on {timeframe}")
            return self.swing_engine
    
    def get_all_engines(self) -> Dict[str, BaseTradingEngine]:
        """Get all available engines"""
        return {
            "scalping": self.scalping_engine,
            "swing": self.swing_engine,
            "crypto": self.crypto_engine
        }


# Singleton instance
_engine_selector: Optional[TradingEngineSelector] = None


def get_engine_selector() -> TradingEngineSelector:
    """Get singleton engine selector instance"""
    global _engine_selector
    if _engine_selector is None:
        _engine_selector = TradingEngineSelector()
    return _engine_selector
