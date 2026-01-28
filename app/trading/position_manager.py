"""Position management: entries, exits, trailing stops, breakeven management"""

from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from app.trading.mt5_client import get_mt5_client
from app.trading.risk import get_risk_manager
from app.trading.data import get_data_provider
from app.core.logger import setup_logger

logger = setup_logger("position_manager")


class PositionManager:
    """Manages position exits: trailing stops, breakeven, opposite signal close"""
    
    def __init__(self):
        self.mt5 = get_mt5_client()
        self.risk = get_risk_manager()
        self.data = get_data_provider()
    
    def should_close_on_rsi_extreme(
        self,
        symbol: str,
        position_type: str,
        rsi_value: float,
        current_price: float,
        open_price: float
    ) -> Tuple[bool, Optional[str]]:
        """
        ⚔️ REGLA A - RSI EXTREMO SIN EXCEPCIONES
        
        BUY + RSI > 80 → CERRAR INMEDIATAMENTE
        SELL + RSI < 20 → CERRAR INMEDIATAMENTE
        
        ❌ NO hay excepciones por "making HH/LL"
        ❌ NO hay "holding for recovery"
        
        Args:
            symbol: Symbol
            position_type: 'BUY' or 'SELL'
            rsi_value: Current RSI value (0-100)
            current_price: Current market price
            open_price: Position open price (unused - for API compatibility)
        
        Returns:
            Tuple (should_close, reason)
        """
        # REGLA A.1: BUY + RSI > 80 → CERRAR SIN EXCEPCIONES
        if position_type == "BUY" and rsi_value > 80.0:
            return True, f"🔴 HARD CLOSE: RSI {rsi_value:.1f} > 80 (overbought) - BUY position closed immediately"
        
        # REGLA A.2: SELL + RSI < 20 → CERRAR SIN EXCEPCIONES
        if position_type == "SELL" and rsi_value < 20.0:
            return True, f"🔴 HARD CLOSE: RSI {rsi_value:.1f} < 20 (oversold) - SELL position closed immediately"
        
        return False, None
    
    def calculate_trailing_stop(
        self,
        symbol: str,
        position_type: str,
        current_price: float,
        entry_price: float,
        current_sl: float,
        atr: float
    ) -> Optional[float]:
        """
        Calculate trailing stop for profitable positions.
        
        Moves SL up for BUY (or down for SELL) as price improves.
        
        Args:
            symbol: Symbol
            position_type: 'BUY' or 'SELL'
            current_price: Current bid/ask
            entry_price: Position entry price
            current_sl: Current stop loss
            atr: Average True Range
        
        Returns:
            New SL price or None if SL should not move
        """
        if atr <= 0:
            return None
        
        # Only trail if position is in profit
        if position_type == "BUY":
            profit = current_price - entry_price
            if profit <= 0:
                return None  # Not in profit, don't trail
            
            # Trail SL to 1.0 ATR below current price (locking profit)
            trailing_sl = current_price - (atr * 1.0)
            
            # Only update if higher than current SL
            if trailing_sl > current_sl:
                logger.info(
                    f"{symbol} BUY: trailing SL from {current_sl:.5f} to {trailing_sl:.5f} "
                    f"(profit={profit:.5f}, atr={atr:.5f})"
                )
                return trailing_sl
        
        else:  # SELL
            profit = entry_price - current_price
            if profit <= 0:
                return None  # Not in profit, don't trail
            
            # Trail SL to 1.0 ATR above current price
            trailing_sl = current_price + (atr * 1.0)
            
            # Only update if lower than current SL
            if trailing_sl < current_sl:
                logger.info(
                    f"{symbol} SELL: trailing SL from {current_sl:.5f} to {trailing_sl:.5f} "
                    f"(profit={profit:.5f}, atr={atr:.5f})"
                )
                return trailing_sl
        
        return None
    
    def set_breakeven(
        self,
        position: Dict[str, Any],
        entry_price: float,
        atr: float,
        buffer_pips: float = 2.0
    ) -> Optional[float]:
        """
        Move SL to breakeven + buffer when profit threshold reached.
        
        Protects position after +X pips profit.
        
        Args:
            position: Position dict (from portfolio)
            entry_price: Entry price
            atr: Average True Range
            buffer_pips: Pips above BE to set SL (default 2.0)
        
        Returns:
            New SL price or None if BE shouldn't activate
        """
        current_sl = position.get('sl', 0)
        if current_sl <= 0:
            return None
        
        # Get position type
        position_type = 'BUY' if position.get('type', 0) == 0 else 'SELL'
        
        # Only activate BE after 1.5x ATR profit
        min_profit = atr * 1.5
        
        if position_type == "BUY":
            profit = position.get('price_current', entry_price) - entry_price
            if profit >= min_profit:
                # Set SL to entry + buffer
                new_sl = entry_price + (buffer_pips * 0.0001)  # Convert pips to price
                
                if new_sl > current_sl:
                    logger.info(
                        f"Position {position.get('ticket')}: Activating BE SL "
                        f"from {current_sl:.5f} to {new_sl:.5f} "
                        f"(profit={profit:.5f}, buffer={buffer_pips}pips)"
                    )
                    return new_sl
        
        else:  # SELL
            profit = entry_price - position.get('price_current', entry_price)
            if profit >= min_profit:
                # Set SL to entry - buffer
                new_sl = entry_price - (buffer_pips * 0.0001)
                
                if new_sl < current_sl:
                    logger.info(
                        f"Position {position.get('ticket')}: Activating BE SL "
                        f"from {current_sl:.5f} to {new_sl:.5f} "
                        f"(profit={profit:.5f}, buffer={buffer_pips}pips)"
                    )
                    return new_sl
        
        return None
    
    def should_close_on_opposite_signal(
        self,
        position_type: str,
        current_signal: str,
        confidence: float,
        min_confidence_to_reverse: float = 0.7
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if position should close due to opposite signal.
        
        Don't fight the trend if signal reverses with high confidence.
        
        Args:
            position_type: 'BUY' or 'SELL'
            current_signal: Current signal ('BUY', 'SELL', 'HOLD')
            confidence: Signal confidence (0-1)
            min_confidence_to_reverse: Threshold to trigger close
        
        Returns:
            Tuple (should_close, reason)
        """
        # BUY position + SELL signal with high confidence → close
        if position_type == "BUY" and current_signal == "SELL":
            if confidence >= min_confidence_to_reverse:
                return True, f"Opposite signal: SELL (confidence={confidence:.2f})"
        
        # SELL position + BUY signal with high confidence → close
        if position_type == "SELL" and current_signal == "BUY":
            if confidence >= min_confidence_to_reverse:
                return True, f"Opposite signal: BUY (confidence={confidence:.2f})"
        
        return False, None
    
    def should_close_on_candle_ttl(
        self,
        position: Dict[str, Any],
        current_price: float,
        entry_price: float,
        position_type: str,
        timeframe: str = "M15",
        max_candles_without_profit: int = 6
    ) -> Tuple[bool, Optional[str]]:
        """
        ⚔️ REGLA B - TIEMPO MÁXIMO EN TRADE (TTL)
        
        Si pasan N velas SIN IR A FAVOR → CERRAR INMEDIATAMENTE
        
        Ejemplo M15: Si pasan 6-8 velas sin ganancia → close
        
        Args:
            position: Position dict
            current_price: Current market price
            entry_price: Position entry price
            position_type: 'BUY' or 'SELL'
            timeframe: Timeframe (M15, M30, H1, etc)
            max_candles_without_profit: Max candles without moving in favor
        
        Returns:
            Tuple (should_close, reason)
        """
        open_time_str = position.get('time_open', None)
        if not open_time_str:
            return False, None
        
        try:
            open_time = datetime.fromisoformat(open_time_str)
            candles_held = None
            
            # Calculate minutes per candle based on timeframe
            if timeframe == "M15":
                minutes_per_candle = 15
            elif timeframe == "M30":
                minutes_per_candle = 30
            elif timeframe == "H1":
                minutes_per_candle = 60
            elif timeframe == "H4":
                minutes_per_candle = 240
            else:
                minutes_per_candle = 15  # default to M15
            
            hold_duration_minutes = (datetime.now() - open_time).total_seconds() / 60
            candles_held = int(hold_duration_minutes / minutes_per_candle)
            
            # Check if position moved in favor
            is_profitable = False
            if position_type == "BUY":
                is_profitable = current_price > entry_price * 1.0005  # At least 0.05% profit
            else:  # SELL
                is_profitable = current_price < entry_price * 0.9995  # At least 0.05% profit
            
            # If held too many candles WITHOUT profit → close
            if candles_held >= max_candles_without_profit and not is_profitable:
                return True, f"🔴 HARD CLOSE: {candles_held} candles ({timeframe}) without profit - close now"
            
        except Exception as e:
            logger.debug(f"Error checking candle TTL: {e}")
        
        return False, None
    
    def should_close_on_ema_invalidation(
        self,
        position_type: str,
        ema_fast: float,
        ema_slow: float,
        current_price: float
    ) -> Tuple[bool, Optional[str]]:
        """
        ⚔️ REGLA C - INVALIDACIÓN TÉCNICA (EMA CROSS)
        
        BUY: Si EMA_fast cruza POR DEBAJO de EMA_slow → CERRAR
        SELL: Si EMA_fast cruza POR ARRIBA de EMA_slow → CERRAR
        
        Args:
            position_type: 'BUY' or 'SELL'
            ema_fast: Fast EMA value
            ema_slow: Slow EMA value
            current_price: Current price (for logging context)
        
        Returns:
            Tuple (should_close, reason)
        """
        # BUY position: EMA_fast MUST stay above EMA_slow
        if position_type == "BUY":
            if ema_fast < ema_slow:
                return True, f"🔴 HARD CLOSE: EMA_fast ({ema_fast:.2f}) < EMA_slow ({ema_slow:.2f}) - BUY invalidated"
        
        # SELL position: EMA_fast MUST stay below EMA_slow
        if position_type == "SELL":
            if ema_fast > ema_slow:
                return True, f"🔴 HARD CLOSE: EMA_fast ({ema_fast:.2f}) > EMA_slow ({ema_slow:.2f}) - SELL invalidated"
        
        return False, None
    
    def rank_positions_for_closing(
        self,
        positions: list
    ) -> list:
        """
        ⚔️ PRIORIDAD 3 - RANKING DE POSICIONES PARA CIERRE
        
        Antes de buscar NUEVOS trades, cierra las PEORES posiciones:
        - Por P&L (worst first)
        - Por tiempo abierto (oldest first)
        - Por distancia a SL (closest first)
        
        Args:
            positions: List of position dicts
        
        Returns:
            Sorted list of positions (worst to best)
        """
        if not positions:
            return []
        
        def position_score(pos):
            """Lower score = worse position = close first"""
            pnl = pos.get('pnl', 0)
            time_open = pos.get('time_open', '')
            distance_to_sl = pos.get('distance_to_sl', float('inf'))
            
            # Parse open time
            try:
                open_time = datetime.fromisoformat(time_open)
                minutes_held = (datetime.now() - open_time).total_seconds() / 60
            except:
                minutes_held = 0
            
            # Composite score (lower = worse)
            # 60% weight on P&L, 25% on time held, 15% on distance to SL
            score = (pnl * 0.60) - (minutes_held * 0.25) + (distance_to_sl * 0.15)
            
            return score
        
        # Sort by score (ascending = worst first)
        ranked = sorted(positions, key=position_score)
        
        logger.info(f"Position ranking for closing:")
        for i, pos in enumerate(ranked[:5]):  # Show top 5 worst
            pnl = pos.get('pnl', 0)
            symbol = pos.get('symbol', '?')
            logger.info(f"  #{i+1}: {symbol} P&L=${pnl:.2f}")
        
        return ranked
    
    def should_close_on_time_limit(
        self,
        position: Dict[str, Any],
        max_hold_minutes: int = 240  # 4 hours for scalping
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if position should close after max hold time.
        
        Prevents "forever hold" of overnight positions on scalping accounts.
        
        Args:
            position: Position dict
            max_hold_minutes: Max minutes to hold (default 4 hours for scalping)
        
        Returns:
            Tuple (should_close, reason)
        """
        open_time_str = position.get('time_open', None)
        if not open_time_str:
            return False, None
        
        try:
            open_time = datetime.fromisoformat(open_time_str)
            hold_duration = datetime.now() - open_time
            
            if hold_duration.total_seconds() / 60 > max_hold_minutes:
                return True, f"Position held {hold_duration.total_seconds()/60:.0f}min > {max_hold_minutes}min limit"
        except:
            pass
        
        return False, None


# Global instance
_position_manager: Optional[PositionManager] = None


def get_position_manager() -> PositionManager:
    """Get global position manager instance"""
    global _position_manager
    if _position_manager is None:
        _position_manager = PositionManager()
    return _position_manager
