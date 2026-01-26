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
    
    # Crypto symbols (24/7 trading with higher spreads tolerance)
    CRYPTO_SYMBOLS = [
        'BTCUSD', 'ETHUSD', 'BNBUSD', 'SOLUSD', 'XRPUSD',
        'DOGEUSD', 'ADAUSD', 'DOTUSD', 'LTCUSD', 'AVAXUSD'
    ]
    
    # Spread limits by asset type (pips)
    FOREX_MAX_SPREAD_PIPS = 10.0      # Forex: tight spreads expected
    CRYPTO_MAX_SPREAD_PIPS = 300.0    # Crypto: much higher spreads are normal
    
    def __init__(self):
        self.config = get_config()
        self.mt5 = get_mt5_client()
        self.data = get_data_provider()
        self.portfolio = get_portfolio_manager()
        # Parámetros ajustados para demo
        self.risk_per_trade_pct = 2.0
        self.max_daily_loss_pct = 90.0
        self.max_drawdown_pct = 90.0
        self.max_positions = 100
        self.max_slippage_pips = 5.0
        self.max_trade_risk_pct = 50.0
        self.default_stop_loss_pct = 0.01
        self.hard_max_volume_lots = 1.0  # Seguridad: no permitir que la IA pida >1 lote
        self.crypto_max_volume_lots = 0.30  # Aún más bajo para cripto
        # Horario extendido: operar 24h
        self.trading_hours_start = time(0, 0)
        self.trading_hours_end = time(23, 59)
    
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
        
        # 7. Check spread (different limits for forex vs crypto)
        spread_pips = self.data.get_spread_pips(symbol)
        if spread_pips is not None:
            # Determine max spread based on asset type
            is_crypto = any(crypto in symbol.upper() for crypto in self.CRYPTO_SYMBOLS)
            max_spread = self.CRYPTO_MAX_SPREAD_PIPS if is_crypto else self.FOREX_MAX_SPREAD_PIPS
            
            if spread_pips > max_spread:
                asset_type = "crypto" if is_crypto else "forex"
                failures.append(
                    f"Spread too high for {asset_type}: {spread_pips:.2f} pips (max: {max_spread:.0f})"
                )
        
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
            # Hard cap independiente del broker
            if proposed_volume > self.hard_max_volume_lots:
                failures.append(
                    f"Volume above bot cap: {proposed_volume} > {self.hard_max_volume_lots} (safety cap)"
                )
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
        
        # Calculate risk amount (bounded by max_trade_risk_pct)
        if risk_amount is None:
            capped_pct = min(self.risk_per_trade_pct, self.max_trade_risk_pct)
            risk_amount = equity * (capped_pct / 100)
        
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
        max_volume = min(symbol_info.get('volume_max', 100.0), self.hard_max_volume_lots)
        volume_step = symbol_info.get('volume_step', 0.01)

        # Cap adicional para cripto
        if any(crypto in symbol.upper() for crypto in self.CRYPTO_SYMBOLS):
            max_volume = min(max_volume, self.crypto_max_volume_lots)
        
        # If calculated volume is less than minimum, return 0 (trade not viable)
        # This prevents forcing minimum volume which could be way too large for our capital
        if lots < min_volume:
            logger.info(f"Calculated volume {lots:.2f} < min_volume {min_volume}, trade not viable for {symbol}")
            return 0.0
        
        lots = min(max_volume, lots)
        
        # Round to volume step
        lots = round(lots / volume_step) * volume_step
        
        logger.debug(
            f"Position sizing: risk={risk_amount:.2f}, price_risk={price_risk:.5f}, "
            f"risk_per_lot={risk_per_lot:.2f}, lots={lots:.2f}"
        )
        
        return lots

    def get_default_stop_distance(self, entry_price: float, atr_value: Optional[float]) -> float:
        """Fallback stop distance when ATR is missing/invalid."""
        if atr_value and atr_value > 0:
            return self.calculate_stop_loss_atr(atr_value)
        return max(entry_price * self.default_stop_loss_pct, 0.0001)

    def cap_volume_by_risk(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: Optional[float],
        requested_volume: float
    ) -> float:
        """Cap volume so the trade risk does not exceed max_trade_risk_pct."""
        account_info = self.mt5.get_account_info()
        if not account_info:
            return requested_volume
        equity = account_info.get("equity", 0)
        if equity <= 0:
            return requested_volume

        if stop_loss_price is None:
            return requested_volume

        max_risk_amount = equity * (self.max_trade_risk_pct / 100)
        max_volume = self.calculate_position_size(
            symbol=symbol,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            risk_amount=max_risk_amount,
        )
        # Aplica cap duro incluso si el sizing devolvió algo mayor
        capped = min(requested_volume, max_volume, self.hard_max_volume_lots)

        # Cap adicional por margen disponible
        margin_capped = self.cap_volume_by_margin(symbol, entry_price, capped)
        return margin_capped

    def cap_volume_by_margin(self, symbol: str, entry_price: float, requested_volume: float) -> float:
        """Reduce volumen si el margen libre no alcanza (usa 50% del margen libre como techo)."""
        if requested_volume <= 0:
            return 0.0
        try:
            account_info = self.mt5.get_account_info()
            if not account_info:
                return requested_volume
            margin_free = account_info.get('margin_free', 0)
            if margin_free <= 0:
                return 0.0

            # Assume BUY for sizing; SELL margin similar for FX/crypto retail
            margin_calc = self.mt5.order_calc_margin(0, symbol, requested_volume, entry_price)
            if margin_calc is None or margin_calc <= 0:
                return requested_volume

            margin_per_lot = margin_calc / max(requested_volume, 1e-9)
            allowed = (margin_free * 0.5) / margin_per_lot  # Usa 50% del margen libre para holgura

            symbol_info = self.mt5.get_symbol_info(symbol)
            volume_step = symbol_info.get('volume_step', 0.01) if symbol_info else 0.01

            capped = min(requested_volume, allowed)
            capped = max(0.0, (int(capped / volume_step)) * volume_step)
            return capped
        except Exception as e:
            logger.warning(f"Failed margin cap for {symbol}: {e}")
            return requested_volume
    
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
