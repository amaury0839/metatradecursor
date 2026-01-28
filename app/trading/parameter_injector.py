"""Risk parameter injection - applies adaptive parameters to trading decisions"""

from typing import Optional
from app.trading.adaptive_optimizer import get_adaptive_optimizer
from app.trading.risk import RiskManager
from app.core.logger import setup_logger

logger = setup_logger("risk_injection")


class ParameterInjector:
    """Injects adaptive risk parameters into trading decisions per ticker"""
    
    def __init__(self):
        self.optimizer = get_adaptive_optimizer()
        self.risk_manager = RiskManager()
    
    def get_max_risk_pct_for_symbol(self, symbol: str) -> float:
        """Get adaptive max risk % for a symbol using RISK_CONFIG (2%, 2.5%, or 3%)"""
        # 🔥 USE DYNAMIC RISK FROM RISK_CONFIG BASED ON ASSET TYPE
        dynamic_risk = self.risk_manager.get_risk_pct_for_symbol(symbol) * 100
        
        # Also check optimizer for symbol-specific overrides (if applicable)
        params = self.optimizer.get_ticker_params(symbol)
        override_risk = params.get('max_risk_pct', None)
        
        # Use override if available, otherwise use dynamic risk
        return override_risk if override_risk else dynamic_risk
    
    def get_max_positions_for_symbol(self, symbol: str) -> int:
        """Get adaptive max positions for a symbol"""
        params = self.optimizer.get_ticker_params(symbol)
        return params.get('max_positions_per_ticker', 2)
    
    def get_min_win_rate_for_symbol(self, symbol: str) -> float:
        """Get minimum required win rate for a symbol"""
        params = self.optimizer.get_ticker_params(symbol)
        return params.get('min_win_rate_pct', 45.0)
    
    def should_trade_symbol(self, symbol: str) -> tuple[bool, Optional[str]]:
        """Check if trading this symbol is allowed based on adaptive parameters"""
        try:
            params = self.optimizer.get_ticker_params(symbol)
            
            # Check if symbol has been optimized
            if not params.get('last_updated'):
                # New symbol, allow trading
                return True, None
            
            # Check if performance meets minimum thresholds
            win_rate = params.get('win_rate', 0.0)
            min_wr = params.get('min_win_rate_pct', 45.0)
            
            if win_rate < (min_wr - 10):  # Allow 10% buffer
                return False, f"Win rate {win_rate:.1f}% < minimum {min_wr:.1f}%"
            
            return True, None
        
        except Exception as e:
            logger.warning(f"Error checking if should trade {symbol}: {e}")
            return True, None  # Default to allowing if error


# Global instance
_injector: Optional[ParameterInjector] = None


def get_parameter_injector() -> ParameterInjector:
    """Get global parameter injector"""
    global _injector
    if _injector is None:
        _injector = ParameterInjector()
    return _injector
