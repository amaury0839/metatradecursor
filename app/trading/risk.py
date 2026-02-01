"""Risk management and position sizing"""

from typing import Optional, Dict, Tuple, List
from datetime import datetime, time
from app.core.config import get_config
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client
from app.trading.data import get_data_provider
from app.trading.portfolio import get_portfolio_manager
from app.trading.dynamic_sizing import get_dynamic_sizer

logger = setup_logger("risk")


class RiskManager:
    """Manages risk checks and position sizing"""
    
    # Crypto symbols (24/7 trading with higher spreads tolerance)
    CRYPTO_SYMBOLS = [
        'BTCUSD', 'ETHUSD', 'BNBUSD', 'SOLUSD', 'XRPUSD',
        'DOGEUSD', 'ADAUSD', 'DOTUSD', 'LTCUSD', 'AVAXUSD'
    ]
    
    # 🔥 RISK CONFIG BY ASSET TYPE (dynamic risk per symbol)
    RISK_CONFIG = {
        "FOREX_MAJOR": 0.02,      # 2% - EURUSD, GBPUSD, USDJPY, etc
        "FOREX_CROSS": 0.025,     # 2.5% - AUDNZD, NZDUSD, etc
        "CRYPTO": 0.03            # 3% - BTC, ETH, XRP, etc (higher volatility OK)
    }
    
    # 🔥 AGGRESSIVE MINIMUM LOT (override for conservative risk management)
    # If calculated volume < symbol_minimum, clamp to AGGRESSIVE_MIN_LOT instead of rejecting
    AGGRESSIVE_MIN_LOT = 0.05   # 0.05 is moderate, 0.10 for more aggressive
    
    # 🔥 MINIMUM LOT BY SYMBOL (avoids 0.01 trap, clamps to minimum)
    MIN_LOT_BY_SYMBOL = {
        "EURUSD": 0.2,   # MAJOR: use at least 0.2 lots
        "GBPUSD": 0.2,   # MAJOR: use at least 0.2 lots
        "USDJPY": 0.3,   # MAJOR: use at least 0.3 lots (different pip value)
        "AUDUSD": 0.25,  # CROSS: use at least 0.25
        "NZDUSD": 0.25,  # CROSS: use at least 0.25
        "XRPUSD": 50,    # CRYPTO: 50 units minimum
        "ADAUSD": 1000,  # CRYPTO: 1000 units minimum
        "ETHUSD": 0.05,  # CRYPTO: 0.05 ETH minimum
        "BTCUSD": 0.001, # CRYPTO: 0.001 BTC minimum
    }
    
    # Spread limits by asset type (pips)
    FOREX_MAX_SPREAD_PIPS = 10.0      # Forex: tight spreads expected
    CRYPTO_MAX_SPREAD_PIPS = 300.0    # Crypto: much higher spreads are normal
    
    # Volume minimums (optimized for execution)
    MIN_VOLUME_FOREX = 0.01
    MIN_VOLUME_CRYPTO = 0.01
    
    # ATR multipliers (optimized risk/reward)
    ATR_MULTIPLIER_SL = 1.5
    ATR_MULTIPLIER_TP = 2.0
    
    def __init__(self):
        self.config = get_config()
        self.mt5 = get_mt5_client()
        self.data = get_data_provider()
        self.portfolio = get_portfolio_manager()
        # � CRITICAL: MAX 50 POSITIONS (user requirement, was 200)
        self.max_positions = 50                  # MAX 50 open trades
        # 🔥 BASE RISK: 2% (will be overridden by symbol-specific risk in RISK_CONFIG)
        self.risk_per_trade_pct = 2.0            # Base 2% (adjusted per symbol type)
        self.max_daily_loss_pct = 10.0           # 10% max daily loss
        self.max_drawdown_pct = 15.0             # 15% max drawdown
        self.max_trades_per_currency = 12        # 🔥 12 trades per currency (scalping aggressive)
        self.max_slippage_pips = 5.0             # Slippage flexible
        self.max_trade_risk_pct = 5.0            # 🔥 5% per trade max (increased for A+ setups)
        self.default_stop_loss_pct = 0.008       # Tighter SL for scalping
        self.hard_max_volume_lots = 2.0          # 🔥 Dynamic cap: 2.0 lots max (was 0.50)
        self.crypto_max_volume_lots = 1.0        # CRYPTOS: 1.0 max volume (was 0.50)
        self.max_total_exposure_pct = 15.0       # 🔥 15% max total open risk
        # Horario extendido: operar 24h
        self.trading_hours_start = time(0, 0)
        self.trading_hours_end = time(23, 59)
    
    def get_risk_pct_for_symbol(self, symbol: str) -> float:
        """
        🔥 Get dynamic risk % by symbol type (from RISK_CONFIG)
        
        Returns:
            Risk percentage for this symbol (2.0, 2.5, or 3.0)
        """
        is_crypto = any(crypto in symbol.upper() for crypto in self.CRYPTO_SYMBOLS)
        
        if is_crypto:
            return self.RISK_CONFIG["CRYPTO"]  # 3%
        
        # Determine forex type (MAJOR vs CROSS)
        major_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD"]
        is_major = any(pair in symbol.upper() for pair in major_pairs)
        
        if is_major:
            return self.RISK_CONFIG["FOREX_MAJOR"]  # 2%
        else:
            return self.RISK_CONFIG["FOREX_CROSS"]  # 2.5%
    
    def get_min_lot_for_symbol(self, symbol: str) -> float:
        """
        🔥 Get minimum lot size for this symbol (clamps calculation to minimum)
        
        Returns:
            Minimum lot size (from MIN_LOT_BY_SYMBOL, or 0.01 default)
        """
        return self.MIN_LOT_BY_SYMBOL.get(symbol.upper(), 0.01)
    
    def get_dynamic_min_lot(self, symbol: str, account_balance: float = None) -> float:
        """
        🔥 AGGRESSIVE: Get dynamic minimum lot based on account balance
        
        Rules for Forex:
        - Balance >= $10k → min 0.10 lots
        - Balance >= $5k  → min 0.05 lots
        - Balance < $5k   → NO TRADE (return 0.0, NO consolation 0.01)
        
        Args:
            symbol: Trading symbol
            account_balance: Current account balance (optional)
            
        Returns:
            Minimum lot size (0.0 if below threshold = NO TRADE)
        """
        is_crypto = any(crypto in symbol.upper() for crypto in self.CRYPTO_SYMBOLS)
        
        if account_balance is None:
            # If no balance provided, try to get from account
            account_info = self.mt5.get_account_info()
            account_balance = account_info.get('balance', 0) if account_info else 0
        
        # Crypto uses different rules
        if is_crypto:
            return 0.01  # Keep original crypto minimum
        
        # Forex: dynamic thresholds
        if account_balance >= 10000:
            return 0.10  # $10k+ → 0.10 lot minimum
        elif account_balance >= 5000:
            return 0.05  # $5k+ → 0.05 lot minimum
        else:
            logger.warning(
                f"🚫 INSUFFICIENT BALANCE for {symbol}: ${account_balance:.2f} < $5000. NO TRADE."
            )
            return 0.0  # Below $5k → NO TRADE
    
    def clamp_volume_to_minimum(self, symbol: str, calculated_volume: float) -> float:
        """
        🔥 SCALPING MODE: SKIP instead of CLAMP
        
        For scalping, if volume < minimum, we SKIP the trade instead of clamping.
        This ensures we only take trades with proper risk/reward ratios.
        
        Args:
            symbol: Trading symbol
            calculated_volume: Volume from position sizing calculation
            
        Returns:
            Original volume (NO CLAMP) or 0.0 if below minimum (SKIP)
        """
        min_lot = self.get_min_lot_for_symbol(symbol)
        
        if calculated_volume < min_lot:
            logger.info(
                f"🚫 SKIP: {symbol} volume {calculated_volume:.4f} < minimum {min_lot:.4f} - Trade skipped"
            )
            return 0.0  # Return 0.0 to signal SKIP
        
        return calculated_volume  # No clamping, return original
    
    def compute_valid_stops(
        self, 
        symbol: str, 
        entry_price: float, 
        atr: float, 
        direction: str
    ) -> Tuple[float, float]:
        """
        Calcula SL/TP válidos respetando límites del broker
        
        Args:
            symbol: Símbolo
            entry_price: Precio de entrada
            atr: ATR actual
            direction: "BUY" o "SELL"
            
        Returns:
            Tuple (sl_price, tp_price)
        """
        info = self.mt5.get_symbol_info(symbol)
        if not info:
            logger.warning(f"Cannot get symbol info for {symbol}, using defaults")
            # Fallback con valores conservadores
            sl_dist = atr * self.ATR_MULTIPLIER_SL
            tp_dist = atr * self.ATR_MULTIPLIER_TP
            if direction == "BUY":
                return entry_price - sl_dist, entry_price + tp_dist
            else:
                return entry_price + sl_dist, entry_price - tp_dist
        
        # ✅ PASO 1: Usar DIGITS en lugar de POINT
        digits = info.get('digits', 5)
        point = 10 ** (-digits)  # Calcular desde digits
        
        # Stop mínimo permitido por el broker
        trade_stops_level = info.get('trade_stops_level', 0)
        min_stop = trade_stops_level * point
        
        # Distancias dinámicas (siempre mayores al mínimo del broker)
        sl_dist = max(atr * self.ATR_MULTIPLIER_SL, min_stop * 1.2)
        tp_dist = max(atr * self.ATR_MULTIPLIER_TP, min_stop * 1.5)
        
        # Alinear a tick size para evitar errores de precisión
        tick = info.get('trade_tick_size', point)
        if tick > 0:
            sl_dist = round(sl_dist / tick) * tick
            tp_dist = round(tp_dist / tick) * tick
        
        # Calcular precios según dirección
        if direction == "BUY":
            sl = entry_price - sl_dist
            tp = entry_price + tp_dist
        else:
            sl = entry_price + sl_dist
            tp = entry_price - tp_dist
        
        # ✅ Redondear a DIGITS exactos para normalización
        sl = round(sl, digits)
        tp = round(tp, digits)
        
        logger.info(
            f"{symbol} computed stops (digits={digits}): entry={entry_price:.{digits}f}, "
            f"SL={sl:.{digits}f} (dist={sl_dist:.{digits}f}), TP={tp:.{digits}f} "
            f"(dist={tp_dist:.{digits}f}), min_stop={min_stop:.{digits}f}, "
            f"tick={tick:.{digits}f}, freeze_level={info.get('trade_freeze_level', 0)}"
        )
        
        return sl, tp
    
    def validate_stops(
        self, 
        symbol: str, 
        price: float, 
        sl: float, 
        tp: float,
        direction: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida que SL/TP cumplan con requisitos del broker ANTES de enviar orden
        
        Args:
            symbol: Símbolo
            price: Precio de entrada
            sl: Stop loss
            tp: Take profit
            direction: "BUY" o "SELL"
            
        Returns:
            Tuple (válido, mensaje_error)
        """
        info = self.mt5.get_symbol_info(symbol)
        if not info:
            return False, f"Cannot get symbol info for {symbol}"
        
        point = info.get('point', 0.00001)
        # Usar el nivel más restrictivo (stops o freeze) con un pequeño buffer
        stops_level = float(info.get('trade_stops_level', 0) or 0)
        freeze_level = float(info.get('trade_freeze_level', 0) or 0)
        min_points = max(stops_level, freeze_level)
        min_stop = min_points * point * 1.2
        
        # Validar distancia SL
        sl_distance = abs(price - sl)
        if sl_distance < min_stop:
            return False, f"SL too close: {sl_distance:.5f} < {min_stop:.5f}"
        
        # Validar distancia TP
        tp_distance = abs(price - tp)
        if tp_distance < min_stop:
            return False, f"TP too close: {tp_distance:.5f} < {min_stop:.5f}"
        
        # Validar que SL/TP estén en la dirección correcta
        if direction == "BUY":
            if sl >= price:
                return False, f"BUY: SL must be below entry ({sl:.5f} >= {price:.5f})"
            if tp <= price:
                return False, f"BUY: TP must be above entry ({tp:.5f} <= {price:.5f})"
        else:  # SELL
            if sl <= price:
                return False, f"SELL: SL must be above entry ({sl:.5f} <= {price:.5f})"
            if tp >= price:
                return False, f"SELL: TP must be below entry ({tp:.5f} >= {price:.5f})"
        
        return True, None
    
    def check_all_risk_conditions(
        self, 
        symbol: str, 
        action: str,
        proposed_volume: float,
        min_risk_usd: float = 1.0
    ) -> Tuple[bool, Dict[str, str], float]:
        """
        Run all risk checks and return a volume already clamped to safe limits.
        
        � REORDERED GATES (CRITICAL):
        1. Spread / market viability - Check FIRST (no point checking anything if market is bad)
        2. Symbol profile - Validate symbol exists and has proper config
        3. Position limits - Check account-wide limits
        4. Sizing - Calculate and validate trade size
        5. IA / Risk checks - Final validation with AI/ML signals
        
        Args:
            symbol: Symbol to trade
            action: BUY or SELL
            proposed_volume: Proposed volume in lots
            min_risk_usd: Minimum risk in USD to make trade viable (default $1.0)
        
        Returns:
            Tuple of (passed, reason_codes_dict, normalized_volume)
        """
        failures: Dict[str, str] = {}
        adjusted_volume = max(0.0, proposed_volume)
        
        # === GATE 1: SPREAD / MARKET VIABILITY (CHECK FIRST) ===
        spread_pips = self.data.get_spread_pips(symbol)
        if spread_pips is not None:
            is_crypto = any(crypto in symbol.upper() for crypto in self.CRYPTO_SYMBOLS)
            max_spread = self.CRYPTO_MAX_SPREAD_PIPS if is_crypto else self.FOREX_MAX_SPREAD_PIPS
            
            if spread_pips > max_spread:
                asset_type = "crypto" if is_crypto else "forex"
                failures["spread"] = (
                    f"Spread too high for {asset_type}: {spread_pips:.2f} pips (max: {max_spread:.0f})"
                )
                # Early exit - no point checking further if spread is bad
                return False, failures, 0.0
        
        # Check trading hours (part of market viability)
        if not self._is_trading_hours():
            failures["trading_hours"] = "Outside trading hours"
            return False, failures, 0.0
        
        # === GATE 2: SYMBOL PROFILE ===
        symbol_info = self.mt5.get_symbol_info(symbol)
        if not symbol_info:
            failures["symbol_info"] = f"Cannot get symbol info for {symbol}"
            return False, failures, 0.0
        
        # === GATE 3: POSITION LIMITS ===
        # Check MT5 connection
        if not self.mt5.is_connected():
            failures["mt5_connection"] = "MT5 not connected"
            return False, failures, 0.0
        
        # Check kill switch
        from app.core.state import get_state_manager
        if get_state_manager().is_kill_switch_active():
            failures["kill_switch"] = "Kill switch active"
            return False, failures, 0.0
        
        # Check max positions
        open_positions = self.portfolio.get_open_positions_count()
        if open_positions >= self.max_positions:
            failures["max_positions"] = f"Max positions limit reached: {open_positions}/{self.max_positions}"
            return False, failures, 0.0
        
        # === GATE 4: SIZING ===
        account_info = self.mt5.get_account_info()
        if not account_info:
            failures["account_info"] = "Cannot get account info"
            return False, failures, 0.0
        
        equity = account_info.get('equity', 0)
        balance = account_info.get('balance', 0)
        
        if equity <= 0:
            failures["invalid_equity"] = f"Invalid equity: {equity}"
            return False, failures, 0.0
        
        # Validate and normalize volume with symbol limits
        is_crypto = any(crypto in symbol.upper() for crypto in self.CRYPTO_SYMBOLS)
        bot_cap = self.crypto_max_volume_lots if is_crypto else self.hard_max_volume_lots
        min_volume = self.MIN_VOLUME_CRYPTO if is_crypto else self.MIN_VOLUME_FOREX
        max_volume = float(symbol_info.get('volume_max', 100.0))
        step = float(symbol_info.get('volume_step', 0.01)) or 0.01

        normalized = self.normalize_volume(symbol, adjusted_volume)
        capped = min(normalized, max_volume, bot_cap)
        if normalized != capped:
            logger.info(
                f"{symbol} volume capped from {normalized} to {capped} (limits applied)"
            )

        adjusted_volume = round(capped / step) * step
        adjusted_volume = max(0.0, adjusted_volume)

        # Try to find viable volume using min_risk_usd if current volume too small
        if adjusted_volume < min_volume and min_risk_usd > 0:
            logger.warning(
                f"{symbol}: Volume {adjusted_volume} < minimum {min_volume}. "
                f"Attempting to recalculate using min_risk_usd={min_risk_usd}..."
            )
            tick = self.data.get_current_tick(symbol)
            if tick:
                price = (tick.get('bid', 0) + tick.get('ask', 0)) / 2
                if price > 0 and account_info:
                    estimated_volume = min_risk_usd / (price * 10)
                    adjusted_volume = max(min_volume, min(estimated_volume, bot_cap))
                    logger.info(f"{symbol}: Recalculated volume to {adjusted_volume} based on min_risk")
            
            if adjusted_volume < min_volume:
                failures["min_volume"] = f"Volume {adjusted_volume} < minimum {min_volume} (unavoidable)"
                return False, failures, 0.0
        
        # === GATE 5: IA / RISK CHECKS (FINAL) ===
        # Check drawdown
        if equity < balance * (1 - self.max_drawdown_pct / 100):
            max_equity = get_state_manager().max_equity
            if max_equity > 0:
                drawdown_pct = ((max_equity - equity) / max_equity) * 100
                if drawdown_pct > self.max_drawdown_pct:
                    failures["drawdown"] = f"Max drawdown exceeded: {drawdown_pct:.2f}%"
                    return False, failures, 0.0
        
        # Check daily loss
        state = get_state_manager()
        daily_loss_pct = (state.daily_pnl / balance * 100) if balance > 0 else 0
        if daily_loss_pct < -self.max_daily_loss_pct:
            failures["daily_loss"] = f"Daily loss limit exceeded: {daily_loss_pct:.2f}%"
            return False, failures, 0.0
        
        passed = len(failures) == 0
        return passed, failures, adjusted_volume
    
    def calculate_position_size(
        self, 
        symbol: str, 
        entry_price: float, 
        stop_loss_price: float,
        risk_amount: Optional[float] = None,
        confidence: Optional[float] = None
    ) -> float:
        """
        Calculate position size based on risk
        
        🔧 FIXED: Better handling of crypto CFD minimum volumes and contract sizes
        - Handles both FX (standard contract) and crypto CFDs (variable contract size)
        - Accounts for point vs pip vs unit differences
        
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
        
        # 🔥 PALANCA 1: RIESGO DINÁMICO POR CALIDAD/CONFIANZA
        # Escala riesgo según calidad del setup
        risk_pct = self.risk_per_trade_pct  # Base: 2%
        
        # Multiplicador por confianza (confidence 0-1)
        if confidence is not None:
            if confidence >= 0.85:  # Setup A+ (85%+)
                risk_multiplier = 2.0   # 4% risk
                logger.info(f"🔥 {symbol}: A+ setup (confidence={confidence:.2f}) → risk x2.0")
            elif confidence >= 0.75:  # Setup A (75%+)
                risk_multiplier = 1.5   # 3% risk
                logger.info(f"🔥 {symbol}: A setup (confidence={confidence:.2f}) → risk x1.5")
            else:  # Setup normal
                risk_multiplier = 1.0   # 2% risk
            
            risk_pct = risk_pct * risk_multiplier
        
        # Boost adicional para FOREX en cuentas pequeñas
        is_forex = not any(crypto in symbol.upper() for crypto in self.CRYPTO_SYMBOLS)
        if is_forex and equity < 10000:
            risk_pct = min(risk_pct * 1.5, self.max_trade_risk_pct)
            logger.info(f"🥈 {symbol} FOREX small account boost: → {risk_pct:.1f}%")
        
        # Calculate risk amount (bounded by max_trade_risk_pct)
        if risk_amount is None:
            capped_pct = min(risk_pct, self.max_trade_risk_pct)
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
        
        # Get tick information (broker normalized)
        point = float(symbol_info.get('point') or 0.0001)
        contract_size = float(symbol_info.get('trade_contract_size') or 100000)
        min_volume = symbol_info.get('volume_min', 0.01)

        if point <= 0 or contract_size <= 0:
            logger.warning(f"Invalid contract data for {symbol}: point={point}, contract_size={contract_size}")
            return 0.01

        # 🔧 CLASSIFY INSTRUMENT TYPE
        # If volume_min >= 1, it's a CRYPTO CFD (contracts)
        # If volume_min < 1, it's FOREX (micro/mini lots)
        is_crypto_cfd = min_volume >= 1.0
        
        # Volume calculation: SEPARATE FORMULAS BY INSTRUMENT TYPE
        if is_crypto_cfd:
            # 🟠 CRYPTO CFDs (BTC, ETH, ADA, etc.)
            # Formula: volume = risk_amount / (price_risk * contract_size)
            # price_risk = movimiento de precio en puntos
            # contract_size = unidades por contrato
            volume = risk_amount / (price_risk * contract_size)
            logger.info(
                f"{symbol} [CRYPTO CFD] position sizing: "
                f"risk_amount={risk_amount:.2f}, price_risk={price_risk:.5f}, "
                f"contract_size={contract_size} → volume={volume:.6f} contracts"
            )
        else:
            # 🔵 FOREX (EUR/USD, GBP/USD, etc.)
            # Formula correcta: volume = risk_amount / (price_risk * contract_size)
            # price_risk ya está en precio, multiplicar por contract_size da USD por lote
            loss_per_lot = price_risk * contract_size
            if loss_per_lot > 0:
                volume = risk_amount / loss_per_lot
            else:
                return 0.01
            logger.info(
                f"{symbol} [FOREX] position sizing: "
                f"risk_amount={risk_amount:.2f}, price_risk={price_risk:.5f}, "
                f"loss_per_lot={loss_per_lot:.2f}, contract_size={contract_size} → "
                f"volume={volume:.6f} lots"
            )
        
        lots = volume
        
        # ✅ FACTOR DE CONGESTIÓN: Reducir lotes cuando hay muchas posiciones abiertas
        MAX_OPEN_TRADES = 12
        try:
            portfolio = self.portfolio_manager if hasattr(self, 'portfolio_manager') else None
            if portfolio is None:
                # Try to get it dynamically
                from app.trading.portfolio import get_portfolio_manager
                portfolio = get_portfolio_manager()
            
            open_positions = portfolio.get_open_positions() if portfolio else []
            num_open = len(open_positions)
            
            if num_open > 0:
                # Congestión: mientras más posiciones, más chico el lote
                # max=0 pos → 1.0x (volumen completo)
                # max=6 pos → 0.5x (mitad)
                # max=12 pos → 0.0x (nada)
                congestion_factor = max(0.3, 1.0 - (num_open / MAX_OPEN_TRADES))
                lots *= congestion_factor
                logger.info(f"📊 {symbol}: Congestion factor={congestion_factor:.2f} ({num_open} open positions). Volume: {volume:.2f} → {lots:.2f}")
        except Exception as e:
            logger.debug(f"Could not apply congestion factor: {e}")
        
        # 🔥 PALANCA 3: CAP DINÁMICO (no más cap duro de 0.50)
        # Cap crece con equity: equity/5000 = lotes máximos
        dynamic_cap = equity / 5000  # 11k → 2.2 lots, 50k → 10 lots
        max_volume = min(
            symbol_info.get('volume_max', 100.0),
            self.hard_max_volume_lots,
            dynamic_cap
        )
        volume_step = symbol_info.get('volume_step', 0.01)

        # Cap adicional para cripto
        if any(crypto in symbol.upper() for crypto in self.CRYPTO_SYMBOLS):
            max_volume = min(max_volume, self.crypto_max_volume_lots)
        
        logger.info(f"💼 {symbol}: dynamic_cap={dynamic_cap:.2f}, max_volume={max_volume:.2f}")
        
        # � SCALPING MODE: SKIP if below minimum (no clamp)
        if lots < min_volume:
            # 🔴 DETAILED SKIP REASON - VOLUME ANALYSIS
            account_info = self.mt5.get_account_info() if hasattr(self, 'mt5') else None
            balance = account_info.get('balance', 0) if account_info else 0
            max_allowed_risk = balance * (self.risk_per_trade_pct / 100) if balance > 0 else 0
            
            # Calculate implied risk at minimum volume
            # (This is calculated based on entry/SL from earlier in the call stack)
            implied_risk_at_min = "unknown"  # We don't have entry/SL here
            
            logger.warning(f"🔴 {symbol} VOLUME SKIP ANALYSIS:")
            logger.warning(f"   calculated_volume: {lots:.6f} lots")
            logger.warning(f"   broker_min_volume: {min_volume:.6f} lots")
            logger.warning(f"   implied_risk_if_min: {implied_risk_at_min}")
            logger.warning(f"   max_allowed_risk: ${max_allowed_risk:,.2f}")
            logger.warning(f"   ❌ SKIP: volume {lots:.6f} < {min_volume:.6f}")
            
            return 0.0  # Return 0.0 to signal SKIP
        
        lots = min(max_volume, lots)
        
        # Round to volume step
        lots = round(lots / volume_step) * volume_step
        
        logger.debug(
            f"Position sizing [{'CRYPTO' if is_crypto_cfd else 'FOREX'}]: "
            f"risk={risk_amount:.2f}, price_risk={price_risk:.5f}, "
            f"lots={lots:.2f}, min={min_volume}, max={max_volume}"
        )
        
        return lots

    def calculate_position_size_by_balance(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        balance: Optional[float] = None
    ) -> float:
        """
        🆕 ADAPTIVE SIZING: Calculate position size based on actual balance
        Reduces risk exposure when balance is low, allows more when balance is high
        
        Args:
            symbol: Symbol to trade
            entry_price: Entry price
            stop_loss_price: Stop loss price
            balance: Current balance (uses account balance if not provided)
            
        Returns:
            Position size in lots (adaptively scaled)
        """
        account_info = self.mt5.get_account_info()
        if not account_info:
            return 0.01
        
        current_balance = balance or account_info.get('balance', 0)
        if current_balance <= 0:
            return 0.01
        
        # 🔧 ADAPTIVE RISK SCALING BASED ON BALANCE
        # Higher balance = more aggressive (higher risk %)
        # Lower balance = more conservative (lower risk %)
        if current_balance < 1000:
            # Micro accounts: 0.25% per trade
            risk_pct = 0.25
        elif current_balance < 5000:
            # Small accounts: 0.4% per trade
            risk_pct = 0.4
        elif current_balance < 25000:
            # Standard accounts: 0.6% per trade
            risk_pct = 0.6
        else:
            # Large accounts: 0.8% per trade (still conservative)
            risk_pct = 0.8
        
        risk_amount = current_balance * (risk_pct / 100)
        
        logger.info(
            f"🔧 ADAPTIVE SIZING for {symbol}: balance=${current_balance:.2f} → "
            f"risk_pct={risk_pct}% → risk_amount=${risk_amount:.2f}"
        )
        
        # Use standard calculation with adaptive risk amount
        return self.calculate_position_size(
            symbol=symbol,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            risk_amount=risk_amount
        )

    def get_default_stop_distance(self, entry_price: float, atr_value: Optional[float]) -> float:
        """Fallback stop distance when ATR is missing/invalid."""
        if atr_value and atr_value > 0:
            return self.calculate_stop_loss_atr(atr_value)
        return max(entry_price * self.default_stop_loss_pct, 0.0001)

    def get_broker_min_stop_distance(self, symbol: str) -> float:
        """Return broker-enforced minimum stop distance in price units."""
        try:
            info = self.mt5.get_symbol_info(symbol)
            if not info:
                return 0.0
            points = info.get('trade_stops_level', info.get('stops_level', 0)) or 0
            point = info.get('point', 0.0001)
            return float(points) * float(point)
        except Exception:
            return 0.0

    def normalize_volume(self, symbol: str, requested_volume: float) -> float:
        """Normalize volume to broker limits and volume_step.

        Applies: volume = clamp(volume_min, requested, volume_max) and rounds to step.
        """
        try:
            info = self.mt5.get_symbol_info(symbol)
            if not info:
                return max(0.0, requested_volume)
            vmin = float(info.get('volume_min', 0.01))
            vmax = float(info.get('volume_max', 100.0))
            step = float(info.get('volume_step', 0.01)) or 0.01
            vol = max(vmin, min(float(requested_volume), vmax))
            vol = round(vol / step) * step
            return max(0.0, vol)
        except Exception:
            return max(0.0, requested_volume)

    def cap_volume_by_risk(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: Optional[float],
        requested_volume: float
    ) -> float:
        """Cap volume so the trade risk does not exceed max_trade_risk_pct."""
        # Fallback: si no hay cuenta (desconectado), al menos capear al máximo permitido
        account_info = self.mt5.get_account_info()
        symbol_info = self.mt5.get_symbol_info(symbol)
        is_crypto = any(c in symbol.upper() for c in self.CRYPTO_SYMBOLS)
        bot_cap = self.crypto_max_volume_lots if is_crypto else self.hard_max_volume_lots
        if not account_info:
            return self.normalize_volume(symbol, min(requested_volume, bot_cap))
        equity = account_info.get("equity", 0)
        if equity <= 0:
            return self.normalize_volume(symbol, min(requested_volume, bot_cap))

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
        capped = min(requested_volume, max_volume, bot_cap)

        # Cap adicional por margen disponible
        margin_capped = self.cap_volume_by_margin(symbol, entry_price, capped)
        # Ensure final normalization to broker constraints
        return self.normalize_volume(symbol, margin_capped)

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
        multiplier: float = None
    ) -> float:
        """Calculate stop loss distance based on ATR"""
        if multiplier is None:
            multiplier = self.ATR_MULTIPLIER_SL
        return atr_value * multiplier
    
    def calculate_take_profit_atr(
        self, 
        atr_value: float, 
        multiplier: float = None
    ) -> float:
        """Calculate take profit distance based on ATR"""
        if multiplier is None:
            multiplier = self.ATR_MULTIPLIER_TP
        return atr_value * multiplier


    def calculate_take_profit_atr(
        self, 
        atr_value: float, 
        multiplier: float = None
    ) -> float:
        """Calculate take profit distance based on ATR"""
        if multiplier is None:
            multiplier = self.ATR_MULTIPLIER_TP
        return atr_value * multiplier
    
    def can_open_new_trade(self, symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Quick check if a new trade can be opened for the symbol.
        
        Args:
            symbol: Symbol to trade
        
        Returns:
            Tuple of (can_trade, error_message)
        """
        # 🔥 PALANCA 5: CONTROL DE EXPOSICIÓN TOTAL (FIXED)
        # Calcular riesgo total real basado en risk_per_trade_pct configurado
        account_info = self.mt5.get_account_info()
        if account_info:
            equity = account_info.get('equity', 0)
            if equity > 0:
                open_positions = self.portfolio.get_open_positions()
                
                # ✅ FIX: Usar risk_per_trade_pct por posición, NO notional value
                # Cada posición abierta arriesga ~2-3% dependiendo del tipo (FOREX_MAJOR=2%, CRYPTO=3%)
                # Con max_positions=50, exposición máxima teórica = 50 * 2% = 100% (BUT capped at 15%)
                risk_pct_symbol = self.get_risk_pct_for_symbol(symbol)
                total_risk_pct = len(open_positions) * risk_pct_symbol
                
                if total_risk_pct >= self.max_total_exposure_pct:
                    return False, f"Max total exposure reached: {total_risk_pct:.1f}% >= {self.max_total_exposure_pct}%"
                
                total_risk_usd = (total_risk_pct / 100) * equity
                logger.info(f"💼 Total exposure: {total_risk_pct:.2f}% / {self.max_total_exposure_pct}% (${total_risk_usd:.0f}, {len(open_positions)} positions)")
        
        # Check position count limits
        open_positions = self.portfolio.get_open_positions_count()
        if open_positions >= self.max_positions:
            return False, f"Max positions limit reached: {open_positions}/{self.max_positions}"
        
        # Check currency conflict (max trades per currency pair)
        open_positions = self.portfolio.get_open_positions()
        same_currency_count = sum(
            1 for pos in open_positions
            if pos.get('symbol', '')[:3] == symbol[:3] or pos.get('symbol', '')[3:6] == symbol[3:6]
        )
        if same_currency_count >= self.max_trades_per_currency:
            return False, f"Max trades per currency exceeded: {same_currency_count}/{self.max_trades_per_currency}"
        
        return True, None


# Global risk manager instance
_risk_manager: Optional[RiskManager] = None


def get_risk_manager() -> RiskManager:
    """Get global risk manager instance"""
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager()
    return _risk_manager


# ============================================================================
# TRADING PRESETS - AGGRESSIVE_SCALPING
# ============================================================================

TRADING_PRESETS = {
    "AGGRESSIVE_SCALPING": {
        "mode": "AGGRESSIVE_SCALPING",
        "timeframe": "M15",
        "risk_percent": 0.75,
        "max_concurrent_positions": 6,
        "dynamic_lot": True,
        "scale_out_profile": "SCALPING",
        "trailing_stop_enabled": True,
        "trailing_atr_multiple": 1.0,
        "trailing_min_profit_r": 1.0,
        "rsi_hard_close_overbought": 85,
        "rsi_hard_close_oversold": 15,
        "sl_atr_multiple": 1.2,
        "tp_atr_multiple": 2.0,
        "ai_mode": "BIAS_ONLY",
        "ai_blocks_trade": False,
        "confidence_threshold": 0.35,
        "description": "Aggressive scalping con scale-out parcial y trailing stop dinámico",
        "tp_levels": [
            {"level": 1, "multiple": 0.5, "close_percent": 0.40, "move_sl_to_be": False, "desc": "TP1: +0.5R → 40%"},
            {"level": 2, "multiple": 1.0, "close_percent": 0.30, "move_sl_to_be": True, "desc": "TP2: +1.0R → 30% (SL→BE)"},
            {"level": 3, "multiple": 1.5, "close_percent": 1.00, "move_sl_to_be": False, "desc": "TP3: +1.5R → trailing"},
        ]
    },
    
    "STANDARD": {
        "mode": "STANDARD",
        "timeframe": "H1",
        "risk_percent": 1.0,
        "max_concurrent_positions": 3,
        "dynamic_lot": True,
        "scale_out_profile": "STANDARD",
        "trailing_stop_enabled": True,
        "trailing_atr_multiple": 1.5,
        "trailing_min_profit_r": 1.5,
        "rsi_hard_close_overbought": 80,
        "rsi_hard_close_oversold": 20,
        "sl_atr_multiple": 1.5,
        "tp_atr_multiple": 3.0,
        "ai_mode": "FULL",
        "ai_blocks_trade": False,
        "confidence_threshold": 0.40,
        "description": "Standard swing trading con scale-out conservador",
        "tp_levels": [
            {"level": 1, "multiple": 0.5, "close_percent": 0.30, "move_sl_to_be": False, "desc": "TP1: +0.5R → 30%"},
            {"level": 2, "multiple": 1.0, "close_percent": 0.50, "move_sl_to_be": True, "desc": "TP2: +1.0R → 50% (SL→BE)"},
            {"level": 3, "multiple": 2.0, "close_percent": 1.00, "move_sl_to_be": False, "desc": "TP3: +2.0R → trailing"},
        ]
    },
    
    "CONSERVATIVE": {
        "mode": "CONSERVATIVE",
        "timeframe": "D",
        "risk_percent": 0.5,
        "max_concurrent_positions": 2,
        "dynamic_lot": True,
        "scale_out_profile": "CONSERVATIVE",
        "trailing_stop_enabled": True,
        "trailing_atr_multiple": 2.0,
        "trailing_min_profit_r": 2.0,
        "rsi_hard_close_overbought": 80,
        "rsi_hard_close_oversold": 20,
        "sl_atr_multiple": 2.0,
        "tp_atr_multiple": 4.0,
        "ai_mode": "FULL",
        "ai_blocks_trade": True,
        "confidence_threshold": 0.50,
        "description": "Conservative daily trading con máxima protección",
        "tp_levels": [
            {"level": 1, "multiple": 0.5, "close_percent": 0.20, "move_sl_to_be": False, "desc": "TP1: +0.5R → 20%"},
            {"level": 2, "multiple": 1.0, "close_percent": 0.50, "move_sl_to_be": True, "desc": "TP2: +1.0R → 50% (SL→BE)"},
            {"level": 3, "multiple": 2.0, "close_percent": 1.00, "move_sl_to_be": False, "desc": "TP3: +2.0R → 100%"},
        ]
    }
}


def get_trading_preset(preset_name: str = "AGGRESSIVE_SCALPING") -> Dict:
    """Obtener configuración de preset de trading
    
    Args:
        preset_name: Nombre del preset (AGGRESSIVE_SCALPING, STANDARD, CONSERVATIVE)
    
    Returns:
        Diccionario con configuración del preset
    """
    return TRADING_PRESETS.get(preset_name, TRADING_PRESETS["AGGRESSIVE_SCALPING"])


def validate_trade_size_dynamic(symbol: str, calculated_volume: float) -> Optional[float]:
    """
    🔥 DYNAMIC VALIDATION: Validate position size based on account balance
    
    Uses dynamic_sizing to enforce:
    - Forex min volume by balance: 0.01 (≤$5k), 0.05 ($5k-$10k), 0.10 (>$10k)
    - NO consolation trades (rejects if too small)
    - Symbol-specific minimums for crypto
    
    Args:
        symbol: Trading symbol
        calculated_volume: Position size from risk calculation
        
    Returns:
        Valid volume (float), or None if rejected
        
    Example:
        lot = risk_manager.calculate_position_size(symbol, entry, sl)
        final_lot = validate_trade_size_dynamic(symbol, lot)
        if final_lot is None:
            logger.info("Trade rejected - insufficient size for balance")
            return False
        # Safe to trade with final_lot
    """
    try:
        sizer = get_dynamic_sizer()
        final_volume = sizer.validate_and_clamp_size(symbol, calculated_volume)
        return final_volume
    except Exception as e:
        logger.error(f"Dynamic validation error: {e}")
        # Fallback: if dynamic sizing fails, allow trade with original volume
        return calculated_volume
