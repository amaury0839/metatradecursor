"""Risk management and position sizing"""

from typing import Optional, Dict, Tuple, List
from datetime import datetime, time
from app.core.config import get_config
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client
from app.trading.data import get_data_provider
from app.trading.portfolio import get_portfolio_manager

logger = setup_logger("risk")


class RiskManager:
    """Manages risk checks and position sizing"""
    
    def __init__(self):
        self.config = get_config()
        self.mt5 = get_mt5_client()
        self.data = get_data_provider()
        self.portfolio = get_portfolio_manager()
        
        # Risk parameters (can be overridden from UI)
        self.risk_per_trade_pct = self.config.trading.default_risk_per_trade
        self.max_daily_loss_pct = self.config.trading.default_max_daily_loss
        self.max_drawdown_pct = self.config.trading.default_max_drawdown
        self.max_positions = self.config.trading.default_max_positions
        self.max_spread_pips = 1.5  # Default for major pairs
        self.max_slippage_pips = 0.5
        
        # Trading hours (default: avoid rollover window 4:55pm - 5:10pm NY)
        self.trading_hours_start = time(5, 10)  # 5:10 AM NY
        self.trading_hours_end = time(16, 55)   # 4:55 PM NY
    
    def check_all_risk_conditions(
        self, 
        symbol: str, 
        action: str,
        proposed_volume: float
    ) -> Tuple[bool, List[str]]:
        """
        Run all risk checks
        
        Args:
            symbol: Symbol to trade
            action: BUY or SELL
            proposed_volume: Proposed volume in lots
        
        Returns:
            Tuple of (passed, list of failure reasons)
        """
        failures = []
        
        # 1. Check MT5 connection
        if not self.mt5.is_connected():
            failures.append("MT5 not connected")
        
        # 2. Check kill switch
        from app.core.state import get_state_manager
        if get_state_manager().is_kill_switch_active():
            failures.append("Kill switch active")
        
        # 3. Check account equity
        account_info = self.mt5.get_account_info()
        if not account_info:
            failures.append("Cannot get account info")
        else:
            equity = account_info.get('equity', 0)
            balance = account_info.get('balance', 0)
            
            if equity <= 0:
                failures.append(f"Invalid equity: {equity}")
            
            # 4. Check drawdown
            if equity < balance * (1 - self.max_drawdown_pct / 100):
                max_equity = get_state_manager().max_equity
                if max_equity > 0:
                    drawdown_pct = ((max_equity - equity) / max_equity) * 100
                    if drawdown_pct > self.max_drawdown_pct:
                        failures.append(f"Max drawdown exceeded: {drawdown_pct:.2f}%")
            
            # 5. Check daily loss
            from app.core.state import get_state_manager
            state = get_state_manager()
            daily_loss_pct = (state.daily_pnl / balance * 100) if balance > 0 else 0
            if daily_loss_pct < -self.max_daily_loss_pct:
                failures.append(f"Daily loss limit exceeded: {daily_loss_pct:.2f}%")
        
        # 6. Check max positions
        open_positions = self.portfolio.get_open_positions_count()
        if open_positions >= self.max_positions:
            failures.append(f"Max positions limit reached: {open_positions}/{self.max_positions}")
        
        # 7. Check spread
        spread_pips = self.data.get_spread_pips(symbol)
        if spread_pips is not None and spread_pips > self.max_spread_pips:
            failures.append(f"Spread too high: {spread_pips:.2f} pips (max: {self.max_spread_pips})")
        
        # 8. Check trading hours
        if not self._is_trading_hours():
            failures.append("Outside trading hours")
        
        # 9. Check symbol info and volume limits
        symbol_info = self.mt5.get_symbol_info(symbol)
        if symbol_info:
            min_volume = symbol_info.get('volume_min', 0.01)
            max_volume = symbol_info.get('volume_max', 100.0)
            
            if proposed_volume < min_volume:
                failures.append(f"Volume below minimum: {proposed_volume} < {min_volume}")
            if proposed_volume > max_volume:
                failures.append(f"Volume above maximum: {proposed_volume} > {max_volume}")
        else:
            failures.append(f"Cannot get symbol info for {symbol}")
        
        passed = len(failures) == 0
        return passed, failures
    
    def calculate_position_size(
        self, 
        symbol: str, 
        entry_price: float, 
        stop_loss_price: float,
        risk_amount: Optional[float] = None
    ) -> float:
        """
        Calculate position size based on risk
        
        Args:
            symbol: Symbol name
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_amount: Risk amount in account currency (optional, uses % if not provided)
        
        Returns:
            Position size in lots
        """
        account_info = self.mt5.get_account_info()
        if not account_info:
            logger.warning("Cannot get account info for position sizing")
            return 0.01  # Minimum
        
        equity = account_info.get('equity', 0)
        if equity <= 0:
            return 0.01
        
        # Calculate risk amount
        if risk_amount is None:
            risk_amount = equity * (self.risk_per_trade_pct / 100)
        
        # Get symbol info
        symbol_info = self.mt5.get_symbol_info(symbol)
        if not symbol_info:
            logger.warning(f"Cannot get symbol info for {symbol}")
            return 0.01
        
        # Calculate price risk per lot
        price_risk = abs(entry_price - stop_loss_price)
        if price_risk <= 0:
            logger.warning("Invalid price risk (entry == stop loss)")
            return 0.01
        
        # Get contract size and tick value
        contract_size = symbol_info.get('trade_contract_size', 100000)
        tick_size = symbol_info.get('point', 0.0001)
        tick_value = symbol_info.get('trade_tick_value', 1.0)
        
        # Calculate lots
        # Risk per lot = price_risk * contract_size * tick_value / tick_size
        risk_per_lot = (price_risk / tick_size) * tick_value
        
        if risk_per_lot <= 0:
            logger.warning("Invalid risk per lot calculation")
            return 0.01
        
        lots = risk_amount / risk_per_lot
        
        # Apply limits
        min_volume = symbol_info.get('volume_min', 0.01)
        max_volume = symbol_info.get('volume_max', 100.0)
        volume_step = symbol_info.get('volume_step', 0.01)
        
        lots = max(min_volume, min(max_volume, lots))
        
        # Round to volume step
        lots = round(lots / volume_step) * volume_step
        
        logger.debug(
            f"Position sizing: risk={risk_amount:.2f}, price_risk={price_risk:.5f}, "
            f"risk_per_lot={risk_per_lot:.2f}, lots={lots:.2f}"
        )
        
        return lots
    
    def _is_trading_hours(self) -> bool:
        """Check if current time is within trading hours"""
        try:
            import pytz
            tz = pytz.timezone(self.config.trading.timezone)
            now = datetime.now(tz).time()
            return self.trading_hours_start <= now <= self.trading_hours_end
        except Exception:
            # If timezone handling fails, allow trading
            return True
    
    def calculate_stop_loss_atr(
        self, 
        atr_value: float, 
        multiplier: float = 1.5
    ) -> float:
        """Calculate stop loss distance based on ATR"""
        return atr_value * multiplier
    
    def calculate_take_profit_atr(
        self, 
        atr_value: float, 
        multiplier: float = 2.5
    ) -> float:
        """Calculate take profit distance based on ATR"""
        return atr_value * multiplier


# Global risk manager instance
_risk_manager: Optional[RiskManager] = None


def get_risk_manager() -> RiskManager:
    """Get global risk manager instance"""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager()
    return _risk_manager
