"""
Trade Validation Module - Implements 10-point refactoring

Priority gates (in order):
1. SPREAD CHECK (first gate - skip immediately)
2. EXECUTION CONFIDENCE (no execute if < threshold)
3. RSI BLOCK (no entry at extremes)
4. STOP/TP VALIDATION (with proper Bid/Ask and rounding)
5. VOLUME/LOT VALIDATION (reject if below minimum, never force)
6. EXPOSURE LIMITS (currency cluster)
7. BALANCE CHECK
"""

from typing import Dict, Any, Tuple, Optional
from app.core.logger import setup_logger
from app.trading.decision_constants import (
    MAX_SPREAD_PIPS_FOREX,
    MAX_SPREAD_PIPS_CRYPTO,
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    MIN_EXECUTION_CONFIDENCE,
    MAX_TRADES_PER_CURRENCY,
    SKIP_REASONS,
    CURRENCY_CLUSTERS,
)
from app.trading.signal_execution_split import log_skip_reason

logger = setup_logger("trade_validation")


class TradeValidationGates:
    """
    Implement validation gates in order of priority
    Each gate returns (is_valid, skip_reason)
    """
    
    @staticmethod
    def validate_spread(
        symbol: str,
        current_spread_pips: float,
        is_crypto: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        GATE 1: Spread validation (first gate - do NOT proceed if fails)
        
        This should be checked BEFORE any AI, scoring, or position sizing.
        """
        max_spread = MAX_SPREAD_PIPS_CRYPTO if is_crypto else MAX_SPREAD_PIPS_FOREX
        
        if current_spread_pips > max_spread:
            reason = f"SPREAD_TOO_HIGH ({current_spread_pips:.1f} > {max_spread:.1f} pips)"
            logger.warning(f"  ❌ {symbol}: {reason}")
            return False, reason
        
        logger.info(f"  ✅ {symbol}: Spread OK ({current_spread_pips:.1f} <= {max_spread:.1f} pips)")
        return True, None
    
    @staticmethod
    def validate_execution_confidence(
        symbol: str,
        execution_confidence: float,
        min_confidence: float = MIN_EXECUTION_CONFIDENCE
    ) -> Tuple[bool, Optional[str]]:
        """
        GATE 2: Execution confidence hard gate
        
        Even if signal is STRONG BUY, if confidence < 0.55: DO NOT EXECUTE
        """
        if execution_confidence < min_confidence:
            reason = f"CONFIDENCE_TOO_LOW ({execution_confidence:.2f} < {min_confidence:.2f})"
            logger.warning(f"  ❌ {symbol}: {reason}")
            return False, reason
        
        logger.info(f"  ✅ {symbol}: Confidence OK ({execution_confidence:.2f} >= {min_confidence:.2f})")
        return True, None
    
    @staticmethod
    def validate_rsi_entry_block(
        symbol: str,
        direction: str,
        rsi_value: float
    ) -> Tuple[bool, Optional[str]]:
        """
        GATE 3: RSI extreme blocks entry (not hard close)
        
        - If direction == "BUY" and RSI >= RSI_OVERBOUGHT: BLOCK
        - If direction == "SELL" and RSI <= RSI_OVERSOLD: BLOCK
        
        This prevents entering at extremes that will immediately hit stop.
        """
        if direction == "BUY" and rsi_value >= RSI_OVERBOUGHT:
            reason = f"RSI_BLOCK (RSI={rsi_value:.0f} >= {RSI_OVERBOUGHT} for BUY)"
            logger.warning(f"  ❌ {symbol}: {reason}")
            return False, reason
        
        if direction == "SELL" and rsi_value <= RSI_OVERSOLD:
            reason = f"RSI_BLOCK (RSI={rsi_value:.0f} <= {RSI_OVERSOLD} for SELL)"
            logger.warning(f"  ❌ {symbol}: {reason}")
            return False, reason
        
        logger.info(f"  ✅ {symbol}: RSI OK for {direction} (RSI={rsi_value:.0f})")
        return True, None
    
    @staticmethod
    def validate_stops_with_proper_pricing(
        symbol: str,
        direction: str,
        bid_price: float,
        ask_price: float,
        sl_price: float,
        tp_price: float,
        tick_size: float = 0.0001
    ) -> Tuple[bool, Optional[str]]:
        """
        GATE 4: Stop/TP validation with proper Bid/Ask and rounding
        
        For BUY:
        - entry_price = ASK
        - TP must be > entry_price
        - SL must be < entry_price
        
        For SELL:
        - entry_price = BID
        - TP must be < entry_price
        - SL must be > entry_price
        
        All prices must be rounded to tick size BEFORE validation.
        """
        
        # Round all prices to tick size
        bid_rounded = round(bid_price / tick_size) * tick_size
        ask_rounded = round(ask_price / tick_size) * tick_size
        sl_rounded = round(sl_price / tick_size) * tick_size
        tp_rounded = round(tp_price / tick_size) * tick_size
        
        if direction == "BUY":
            entry = ask_rounded  # BUY at ask
            
            # TP > entry, SL < entry
            if tp_rounded <= entry:
                reason = f"INVALID_STOPS (TP={tp_rounded:.5f} not > entry={entry:.5f})"
                logger.warning(f"  ❌ {symbol}: {reason}")
                return False, reason
            
            if sl_rounded >= entry:
                reason = f"INVALID_STOPS (SL={sl_rounded:.5f} not < entry={entry:.5f})"
                logger.warning(f"  ❌ {symbol}: {reason}")
                return False, reason
        
        else:  # SELL
            entry = bid_rounded  # SELL at bid
            
            # TP < entry, SL > entry
            if tp_rounded >= entry:
                reason = f"INVALID_STOPS (TP={tp_rounded:.5f} not < entry={entry:.5f})"
                logger.warning(f"  ❌ {symbol}: {reason}")
                return False, reason
            
            if sl_rounded <= entry:
                reason = f"INVALID_STOPS (SL={sl_rounded:.5f} not > entry={entry:.5f})"
                logger.warning(f"  ❌ {symbol}: {reason}")
                return False, reason
        
        logger.info(
            f"  ✅ {symbol}: Stops valid ({direction} entry={entry:.5f}, SL={sl_rounded:.5f}, TP={tp_rounded:.5f})"
        )
        return True, None
    
    @staticmethod
    def validate_lot_size(
        symbol: str,
        computed_lot: float,
        broker_min_lot: float,
        broker_max_lot: float
    ) -> Tuple[bool, Optional[str], float]:
        """
        GATE 5: Lot size validation
        
        If computed_lot < broker_min_lot:
        SKIP TRADE, do NOT force to broker_min_lot
        
        This prevents false "risk" where we size down then force up.
        
        Returns: (is_valid, skip_reason, validated_lot)
        """
        
        if computed_lot < broker_min_lot:
            reason = f"LOT_TOO_SMALL ({computed_lot:.4f} < {broker_min_lot:.4f})"
            logger.warning(f"  ❌ {symbol}: {reason} - Trade rejected, NOT forced to minimum")
            return False, reason, 0.0
        
        if computed_lot > broker_max_lot:
            validated = broker_max_lot
            logger.warning(
                f"  ⚠️  {symbol}: Lot capped ({computed_lot:.4f} > {broker_max_lot:.4f}), using {validated:.4f}"
            )
            return True, None, validated
        
        logger.info(f"  ✅ {symbol}: Lot size OK ({computed_lot:.4f})")
        return True, None, computed_lot
    
    @staticmethod
    def validate_exposure_limits(
        symbol: str,
        open_positions: list,
        max_per_currency: int = MAX_TRADES_PER_CURRENCY,
        max_per_cluster: int = 6
    ) -> Tuple[bool, Optional[str]]:
        """
        GATE 6: Currency cluster exposure limits
        
        Prevent correlatedclusters like:
        - 6 trades in USD cluster (EURUSD, GBPUSD, USDJPY...)
        - Too many trades with same base currency
        """
        
        base_currency = symbol[:3]
        
        # Count trades with same base currency
        currency_count = sum(
            1 for pos in open_positions 
            if pos.get('symbol', '').startswith(base_currency)
        )
        
        if currency_count >= max_per_currency:
            reason = f"EXPOSURE_LIMIT (currency {base_currency}: {currency_count} >= {max_per_currency})"
            logger.warning(f"  ❌ {symbol}: {reason}")
            return False, reason
        
        # Count trades in symbol's cluster
        symbol_cluster = None
        for cluster_name, symbols in CURRENCY_CLUSTERS.items():
            if symbol in symbols:
                symbol_cluster = cluster_name
                break
        
        if symbol_cluster:
            cluster_count = sum(
                1 for pos in open_positions
                if pos.get('symbol', '') in CURRENCY_CLUSTERS.get(symbol_cluster, [])
            )
            
            if cluster_count >= max_per_cluster:
                reason = f"EXPOSURE_LIMIT (cluster {symbol_cluster}: {cluster_count} >= {max_per_cluster})"
                logger.warning(f"  ❌ {symbol}: {reason}")
                return False, reason
        
        logger.info(
            f"  ✅ {symbol}: Exposure OK (currency={currency_count}, cluster={symbol_cluster})"
        )
        return True, None
    
    @staticmethod
    def validate_balance(
        symbol: str,
        current_balance: float,
        required_margin: float
    ) -> Tuple[bool, Optional[str]]:
        """
        GATE 7: Account balance check
        
        Ensure we have enough margin for position + buffer
        """
        
        # Require 20% buffer above minimum margin
        required_with_buffer = required_margin * 1.2
        
        if current_balance < required_with_buffer:
            reason = f"INSUFFICIENT_BALANCE (${current_balance:.2f} < ${required_with_buffer:.2f} needed)"
            logger.warning(f"  ❌ {symbol}: {reason}")
            return False, reason
        
        logger.info(
            f"  ✅ {symbol}: Balance OK (${current_balance:.2f} >= ${required_with_buffer:.2f})"
        )
        return True, None


def run_validation_gates(
    symbol: str,
    direction: str,
    execution_confidence: float,
    bid_price: float,
    ask_price: float,
    sl_price: float,
    tp_price: float,
    rsi_value: float,
    spread_pips: float,
    computed_lot: float,
    broker_min_lot: float,
    broker_max_lot: float,
    open_positions: list,
    account_balance: float,
    required_margin: float,
    is_crypto: bool = False,
    tick_size: float = 0.0001
) -> Tuple[bool, Optional[str], float]:
    """
    Run all validation gates in order
    Return immediately on first failure
    
    Returns: (is_valid, skip_reason, validated_lot)
    """
    
    logger.info(f"🔍 VALIDATION GATES: {symbol} {direction}")
    
    # GATE 1: Spread (first gate)
    valid, reason = TradeValidationGates.validate_spread(symbol, spread_pips, is_crypto)
    if not valid:
        log_skip_reason(symbol, reason)
        return False, reason, 0.0
    
    # GATE 2: Execution confidence (hard gate)
    valid, reason = TradeValidationGates.validate_execution_confidence(symbol, execution_confidence)
    if not valid:
        log_skip_reason(symbol, reason)
        return False, reason, 0.0
    
    # GATE 3: RSI block
    valid, reason = TradeValidationGates.validate_rsi_entry_block(symbol, direction, rsi_value)
    if not valid:
        log_skip_reason(symbol, reason)
        return False, reason, 0.0
    
    # GATE 4: Stops with proper pricing
    valid, reason = TradeValidationGates.validate_stops_with_proper_pricing(
        symbol, direction, bid_price, ask_price, sl_price, tp_price, tick_size
    )
    if not valid:
        log_skip_reason(symbol, reason)
        return False, reason, 0.0
    
    # GATE 5: Lot size
    valid, reason, validated_lot = TradeValidationGates.validate_lot_size(
        symbol, computed_lot, broker_min_lot, broker_max_lot
    )
    if not valid:
        log_skip_reason(symbol, reason)
        return False, reason, 0.0
    
    # GATE 6: Exposure limits
    valid, reason = TradeValidationGates.validate_exposure_limits(symbol, open_positions)
    if not valid:
        log_skip_reason(symbol, reason)
        return False, reason, 0.0
    
    # GATE 7: Balance
    valid, reason = TradeValidationGates.validate_balance(symbol, account_balance, required_margin)
    if not valid:
        log_skip_reason(symbol, reason)
        return False, reason, 0.0
    
    logger.info(f"✅ ALL GATES PASSED: {symbol} {direction} (lot={validated_lot:.4f})")
    return True, None, validated_lot
