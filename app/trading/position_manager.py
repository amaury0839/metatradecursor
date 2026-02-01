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
        max_hold_minutes: int = 60  # 4 velas de M15
    ) -> Tuple[bool, Optional[str]]:
        """
        ⏱️ CIERRE POR TIEMPO (CRÍTICO EN SCALPING)
        
        Si una posición lleva X minutos sin cambios significativos,
        el mercado ya no te está dando lo que querías → CIERRA.
        
        Para scalping en M15: máximo 60 minutos (4 velas).
        
        NOTA: Si hold_minutes es negativo, significa que el reloj de MT5
        está adelantado respecto a la hora local. En ese caso, se asume
        que la posición fue abierta justo ahora y no cierra.
        
        Args:
            position: Position dict
            max_hold_minutes: Max minutos para hold (default 60 min = 4 velas M15)
        
        Returns:
            Tuple (should_close, reason)
        """
        # MT5 devuelve 'time' como Unix timestamp en segundos
        # También está disponible 'time_msc' (milliseconds) que es más preciso
        
        # Preferir time_msc si disponible (más preciso)
        time_val = position.get('time_msc', None)
        if time_val:
            # Timestamp en millisegundos
            try:
                open_time_dt = datetime.fromtimestamp(time_val / 1000.0)
            except:
                open_time_dt = None
        else:
            # Fallback a 'time' en segundos
            time_val = open_time
            if isinstance(time_val, (int, float)):
                try:
                    open_time_dt = datetime.fromtimestamp(time_val)
                except:
                    open_time_dt = None
            elif isinstance(time_val, str):
                try:
                    open_time_dt = datetime.fromisoformat(time_val)
                except:
                    open_time_dt = None
            else:
                open_time_dt = None
        
        if open_time_dt is None:
            return False, None
        
        try:
            # Calcular minutos desde apertura
            now_local = datetime.now()
            hold_duration = now_local - open_time_dt
            hold_minutes = hold_duration.total_seconds() / 60
            
            # ⚠️ IMPORTANTE: Si hold_minutes es negativo, el reloj de MT5 está adelantado
            # En este caso, NO cerramos automáticamente
            if hold_minutes < 0:
                logger.debug(f"{position.get('symbol')}: hold_minutes={hold_minutes:.0f} (MT5 clock ahead), NOT closing")
                return False, None
            
            # Si lleva más de max_hold_minutes → CERRAR
            if hold_minutes > max_hold_minutes:
                profit = position.get('profit', 0)
                symbol = position.get('symbol', 'N/A')
                logger.info(f"⏱️  {symbol} TIME_LIMIT: {hold_minutes:.0f}min > {max_hold_minutes}min (profit=${profit:.2f})")
                return True, f"⏱️ TIME LIMIT: {hold_minutes:.0f}min > {max_hold_minutes}min (profit=${profit:.2f})"
        except Exception as e:
            logger.warning(f"Error in TIME_LIMIT check: {e}")
            return False, None
        
        return False, None
    
    def should_close_on_profit_target(
        self,
        symbol: str,
        position: Dict[str, Any],
        atr: float,
        partial_close_enabled: bool = True
    ) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        ⭐ CIERRE POR R-MULTIPLE (TOMA DE GANANCIAS)
        
        Define R = abs(entry - SL)
        - Si profit >= 1.0R → cierra 50% (parcial)
        - Si profit >= 1.5R → cierra el resto
        
        TAMBIÉN cierra por PÉRDIDA:
        - Si profit <= -1.0R → CIERRE TOTAL (stop loss por drawdown)
        
        Args:
            symbol: Symbol
            position: Position dict
            atr: Average True Range
            partial_close_enabled: Si True, permite cierre parcial
        
        Returns:
            Tuple (should_close, reason, close_percent)
            - close_percent: None = full close, 0.5 = 50%, etc.
        """
        entry_price = position.get('price_open', 0)
        current_price = position.get('price_current', 0)
        sl_price = position.get('sl', 0)
        pos_type = 'BUY' if position.get('type', 0) == 0 else 'SELL'
        profit_usd = position.get('profit', 0)
        
        # Si no hay SL definido, no podemos calcular R
        if entry_price == 0 or sl_price == 0:
            return False, None, None
        
        # Calculate R (risk per share/lot)
        R = abs(entry_price - sl_price)
        if R <= 0:
            return False, None, None
        
        # Calculate profit in R-multiples
        if pos_type == 'BUY':
            profit_r = (current_price - entry_price) / R
        else:  # SELL
            profit_r = (entry_price - current_price) / R
        
        # 🚨 REGLA 0: PÉRDIDA >= 1R → CIERRE TOTAL (emergencia)
        if profit_r <= -1.0 and profit_usd < 0:
            return True, f"🚨 LOSS LIMIT: {profit_r:.2f}R <= -1R (${profit_usd:.2f}) - STOP LOSS", None
        
        # 🎯 REGLA 1: Si profit >= 1.5R → CIERRE TOTAL
        if profit_r >= 1.5:
            return True, f"💰 PROFIT TARGET: {profit_r:.2f}R >= 1.5R (${profit_usd:.2f}) - FULL CLOSE", None
        
        # 🎯 REGLA 2: Si profit >= 1.0R → CIERRE PARCIAL 50%
        if profit_r >= 1.0 and partial_close_enabled:
            return True, f"💵 PROFIT TARGET: {profit_r:.2f}R >= 1.0R (${profit_usd:.2f}) - PARTIAL CLOSE 50%", 0.5
        
        return False, None, None
    
    def should_close_on_profit_retrace(
        self,
        position: Dict[str, Any],
        max_profit_seen: float,
        retrace_threshold: float = 0.35
    ) -> Tuple[bool, Optional[str]]:
        """
        ⚠️ CIERRE POR PROFIT RETRACE
        
        Si la operación marcó un máximo de ganancia y luego retrocede
        30-40% de ese máximo → cierra (protege el scalp).
        
        Args:
            position: Position dict
            max_profit_seen: Máxima ganancia vista en USD
            retrace_threshold: % de retroceso para cerrar (default 0.35 = 35%)
        
        Returns:
            Tuple (should_close, reason)
        """
        current_profit = position.get('profit', 0)
        
        # Solo aplica si vimos profit positivo antes
        if max_profit_seen <= 0:
            return False, None
        
        # Calcular retroceso
        profit_lost = max_profit_seen - current_profit
        retrace_pct = profit_lost / max_profit_seen if max_profit_seen > 0 else 0
        
        # Si retrocedió más del threshold
        if retrace_pct >= retrace_threshold:
            return True, f"⚠️ PROFIT RETRACE: Lost {retrace_pct*100:.1f}% (${profit_lost:.2f}) from peak ${max_profit_seen:.2f}"
        
        return False, None
    
    def review_position_full(
        self,
        position: Dict[str, Any],
        current_signal: str,
        signal_confidence: float,
        analysis: Dict[str, Any],
        max_profit_tracker: Dict[int, float]  # ticket -> max_profit_usd
    ) -> Dict[str, Any]:
        """
        🔍 REVISIÓN COMPLETA DE POSICIÓN (TODAS LAS REGLAS DE SALIDA)
        
        Evalúa TODAS las reglas de salida en orden de prioridad:
        1. Profit target (R-multiple)
        2. Profit retrace (proteger ganancias)
        3. RSI extreme
        4. Opposite signal
        5. Time limit
        6. Trailing stop
        
        Returns:
            Dict con:
                - should_close: bool
                - close_percent: Optional[float] (None=full, 0.5=50%)
                - reason: str
                - update_sl: Optional[float] (nuevo SL para trailing)
        """
        symbol = position.get('symbol', '')
        ticket = position.get('ticket', 0)
        pos_type = 'BUY' if position.get('type', 0) == 0 else 'SELL'
        current_price = position.get('price_current', 0)
        entry_price = position.get('price_open', 0)
        current_sl = position.get('sl', 0)
        current_profit = position.get('profit', 0)
        
        # Actualizar max profit tracker
        if ticket not in max_profit_tracker:
            max_profit_tracker[ticket] = current_profit
        else:
            max_profit_tracker[ticket] = max(max_profit_tracker[ticket], current_profit)
        
        max_profit_seen = max_profit_tracker[ticket]
        
        # Get ATR
        atr = analysis.get('atr', 0)
        rsi = analysis.get('rsi', 50)
        
        result = {
            'should_close': False,
            'close_percent': None,
            'reason': None,
            'update_sl': None
        }
        
        # 🔍 DEBUG: Log entry rules evaluation
        logger.debug(f"[REVIEW] {symbol} T{ticket}: {pos_type}, Profit=${current_profit:.2f}, RSI={rsi:.1f}")
        
        # ✅ REGLA 1: PROFIT TARGET (R-multiple) - MÁXIMA PRIORIDAD
        close, reason, close_pct = self.should_close_on_profit_target(
            symbol, position, atr, partial_close_enabled=True
        )
        if close:
            logger.info(f"🟢 {symbol} T{ticket}: CLOSING - {reason}")
            result['should_close'] = True
            result['reason'] = reason
            result['close_percent'] = close_pct
            return result
        else:
            logger.debug(f"✅ {symbol}: REGLA 1 (PROFIT_TARGET) passed (hold)")
        
        # ✅ REGLA 2: PROFIT RETRACE (proteger ganancias)
        close, reason = self.should_close_on_profit_retrace(
            position, max_profit_seen, retrace_threshold=0.35
        )
        if close:
            logger.info(f"🟡 {symbol} T{ticket}: CLOSING - {reason}")
            result['should_close'] = True
            result['reason'] = reason
            return result
        else:
            logger.debug(f"✅ {symbol}: REGLA 2 (PROFIT_RETRACE) passed (hold)")
        
        # ✅ REGLA 3: RSI EXTREME
        close, reason = self.should_close_on_rsi_extreme(
            symbol, pos_type, rsi, current_price, entry_price
        )
        if close:
            logger.info(f"🟠 {symbol} T{ticket}: CLOSING - {reason}")
            result['should_close'] = True
            result['reason'] = reason
            return result
        else:
            logger.debug(f"✅ {symbol}: REGLA 3 (RSI_EXTREME) passed (hold)")
        
        # ✅ REGLA 4: OPPOSITE SIGNAL
        close, reason = self.should_close_on_opposite_signal(
            pos_type, current_signal, signal_confidence, min_confidence_to_reverse=0.7
        )
        if close:
            logger.info(f"🔵 {symbol} T{ticket}: CLOSING - {reason}")
            result['should_close'] = True
            result['reason'] = reason
            return result
        else:
            logger.debug(f"✅ {symbol}: REGLA 4 (OPPOSITE_SIGNAL) passed (hold) - Signal={current_signal}, Conf={signal_confidence:.2f}")
        
        # ✅ REGLA 5: TIME LIMIT (CRÍTICO - cierre por tiempo)
        close, reason = self.should_close_on_time_limit(
            position, max_hold_minutes=60  # 4 velas M15 = 60 minutos
        )
        if close:
            logger.info(f"⏱️  {symbol} T{ticket}: CLOSING - {reason}")
            result['should_close'] = True
            result['reason'] = reason
            return result
        else:
            logger.debug(f"✅ {symbol}: REGLA 5 (TIME_LIMIT) passed (hold) - time={position.get('time', 'N/A')}")
        
        # ✅ REGLA 6: TRAILING STOP (si está en profit)
        if current_profit > 0 and atr > 0:
            new_sl = self.calculate_trailing_stop(
                symbol, pos_type, current_price, entry_price, current_sl, atr
            )
            if new_sl is not None:
                result['update_sl'] = new_sl
                logger.info(f"📈 {symbol} trailing SL: {current_sl:.5f} → {new_sl:.5f}")
        
        return result


# Global instance
_position_manager: Optional[PositionManager] = None


def get_position_manager() -> PositionManager:
    """Get global position manager instance"""
    global _position_manager
    if _position_manager is None:
        _position_manager = PositionManager()
    return _position_manager
