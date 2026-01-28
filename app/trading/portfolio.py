"""Portfolio management and position tracking"""

from typing import List, Dict, Optional
from app.trading.mt5_client import get_mt5_client
from app.core.logger import setup_logger

logger = setup_logger("portfolio")


class PortfolioManager:
    """Manages portfolio state and positions"""
    
    def __init__(self):
        self.mt5 = get_mt5_client()
    
    def get_open_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open positions"""
        return self.mt5.get_positions(symbol)
    
    def get_open_positions_count(self) -> int:
        """Get count of open positions"""
        return len(self.get_open_positions())
    
    def get_position_for_symbol(self, symbol: str) -> Optional[Dict]:
        """Get open position for specific symbol"""
        positions = self.get_open_positions(symbol)
        return positions[0] if positions else None
    
    def has_position(self, symbol: str) -> bool:
        """Check if there's an open position for symbol"""
        return self.get_position_for_symbol(symbol) is not None
    
    def get_total_exposure(self) -> Dict[str, float]:
        """
        Get total exposure by symbol
        
        Returns:
            Dict mapping symbol -> total volume in lots
        """
        positions = self.get_open_positions()
        exposure = {}
        
        for pos in positions:
            symbol = pos.get('symbol', '')
            volume = pos.get('volume', 0.0)
            if symbol:
                exposure[symbol] = exposure.get(symbol, 0.0) + volume
        
        return exposure
    
    def get_unrealized_pnl(self) -> float:
        """Get total unrealized PnL"""
        positions = self.get_open_positions()
        total_pnl = sum(pos.get('profit', 0.0) for pos in positions)
        return total_pnl
    
    def get_unrealized_pnl_by_symbol(self) -> Dict[str, float]:
        """Get unrealized PnL by symbol"""
        positions = self.get_open_positions()
        pnl_by_symbol = {}
        
        for pos in positions:
            symbol = pos.get('symbol', '')
            profit = pos.get('profit', 0.0)
            if symbol:
                pnl_by_symbol[symbol] = pnl_by_symbol.get(symbol, 0.0) + profit
        
        return pnl_by_symbol
    
    def get_exposure_by_currency(self, currency: str) -> int:
        """
        Get count of open positions for a specific currency
        
        Args:
            currency: 3-letter currency code (e.g., 'EUR')
        
        Returns:
            Count of positions with this currency as base
        """
        positions = self.get_open_positions()
        count = 0
        
        for pos in positions:
            symbol = pos.get('symbol', '')
            # Extract base currency from symbol (first 3 chars)
            if symbol.startswith(currency):
                count += 1
        
        return count


# Global portfolio manager instance
_portfolio_manager: Optional[PortfolioManager] = None


def get_portfolio_manager() -> PortfolioManager:
    """Get global portfolio manager instance"""
    global _portfolio_manager
    if _portfolio_manager is None:
        _portfolio_manager = PortfolioManager()
    return _portfolio_manager
