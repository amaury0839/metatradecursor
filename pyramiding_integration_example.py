"""
Example of pyramiding integration in main bot loop

Shows how to integrate:
1. Dynamic sizing validation at entry
2. Pyramiding detection during monitoring
3. SL updates on pyramid activation
"""

from app.core.logger import setup_logger
from app.trading.risk import get_risk_manager, validate_trade_size_dynamic
from app.trading.dynamic_sizing import get_pyramiding_manager
from app.trading.mt5_client import get_mt5_client
from app.trading.data import get_data_provider

logger = setup_logger("pyramiding_example")


class PyramidingBotIntegration:
    """Integration example for pyramiding + dynamic sizing in main bot"""
    
    def __init__(self):
        self.risk = get_risk_manager()
        self.pyramid_mgr = get_pyramiding_manager()
        self.mt5 = get_mt5_client()
        self.data = get_data_provider()
    
    def enter_trade_with_validation(
        self,
        symbol: str,
        direction: str,
        confidence: float,
        sl_pips: float
    ) -> bool:
        """
        🟢 PHASE 1: Enter trade with DYNAMIC SIZE VALIDATION
        
        Steps:
        1. Calculate position size from risk
        2. VALIDATE with dynamic sizing (min volume by balance)
        3. REJECT if too small (no consolation trades)
        4. Execute if valid
        
        Args:
            symbol: Trading symbol
            direction: BUY or SELL
            confidence: Signal confidence (0-1)
            sl_pips: Stop loss in pips
            
        Returns:
            True if trade executed, False if rejected
        """
        # Get current price and ATR
        tick = self.data.get_current_tick(symbol)
        if not tick:
            logger.warning(f"Cannot get tick for {symbol}")
            return False
        
        bid = tick.get('bid', 0)
        ask = tick.get('ask', 0)
        current_price = (bid + ask) / 2 if bid and ask else 0
        
        if not current_price:
            logger.warning(f"Invalid price for {symbol}")
            return False
        
        atr = self.data.get_atr(symbol)
        if not atr:
            atr = current_price * 0.001  # Fallback: 0.1% of price
        
        # Calculate SL price
        if direction == "BUY":
            sl_price = current_price - (sl_pips * 0.0001)
            entry_price = ask
        else:  # SELL
            sl_price = current_price + (sl_pips * 0.0001)
            entry_price = bid
        
        # STEP 1: Calculate position size from risk
        calculated_lot = self.risk.calculate_position_size(
            symbol,
            entry_price,
            sl_price
        )
        
        if calculated_lot <= 0:
            logger.info(f"Position sizing returned 0, trade not viable for {symbol}")
            return False
        
        logger.info(f"{symbol}: Calculated lot = {calculated_lot:.4f}")
        
        # STEP 2: VALIDATE with dynamic sizing
        # 🔥 This is the critical check: min volume by balance
        final_lot = validate_trade_size_dynamic(symbol, calculated_lot)
        
        # STEP 3: REJECT if validation failed (None returned)
        if final_lot is None:
            logger.error(f"❌ {symbol}: TRADE REJECTED - insufficient size for account balance")
            logger.info(f"   Calculated: {calculated_lot:.4f}, but below minimum for balance")
            return False
        
        logger.info(f"✅ {symbol}: Lot validated = {final_lot:.4f}")
        
        # STEP 4: Execute trade
        try:
            if direction == "BUY":
                result = self.mt5.buy(
                    symbol,
                    final_lot,
                    entry_price,
                    sl_price,
                    None,  # TP: will manage with scale-out
                    comment=f"ENTRY: {direction} {final_lot:.2f} (dyn-validated)"
                )
            else:
                result = self.mt5.sell(
                    symbol,
                    final_lot,
                    entry_price,
                    sl_price,
                    None,
                    comment=f"ENTRY: {direction} {final_lot:.2f} (dyn-validated)"
                )
            
            if result:
                logger.info(f"✅ Trade executed: {symbol} {direction} {final_lot:.4f}")
                return True
            else:
                logger.error(f"❌ MT5 execution failed for {symbol}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Trade execution error: {e}")
            return False
    
    def monitor_position_for_pyramiding(
        self,
        symbol: str,
        position: Dict
    ) -> bool:
        """
        🟡 PHASE 2: Monitor open position for PYRAMIDING
        
        Steps:
        1. Get current price
        2. Check if +0.5R profit reached
        3. If yes: calculate pyramid, execute, update SL to BE
        4. If no: continue monitoring
        
        Args:
            symbol: Trading symbol
            position: Position dict with: symbol, direction, open_price, volume, sl
            
        Returns:
            True if pyramid was executed, False if not triggered
        """
        # Get current market data
        tick = self.data.get_current_tick(symbol)
        if not tick:
            logger.debug(f"Cannot get tick for pyramid check: {symbol}")
            return False
        
        bid = tick.get('bid', 0)
        ask = tick.get('ask', 0)
        current_price = (bid + ask) / 2 if bid and ask else 0
        
        if not current_price:
            return False
        
        atr = self.data.get_atr(symbol)
        if not atr:
            atr = position.get('entry_price', current_price) * 0.001
        
        direction = position.get('direction', 'BUY')
        entry_price = position.get('entry_price', position.get('open_price', 0))
        sl_price = position.get('sl', position.get('stoploss', 0))
        original_lot = position.get('volume', 0)
        
        # STEP 1: Check if pyramid should activate
        pyramid = self.pyramid_mgr.calculate_pyramid_activation(
            symbol=symbol,
            entry_price=entry_price,
            current_price=current_price,
            original_lot=original_lot,
            atr=atr,
            sl_price=sl_price,
            direction=direction
        )
        
        # STEP 2: If no pyramid yet, return False
        if pyramid is None:
            logger.debug(f"{symbol}: +0.5R not hit yet, continue monitoring")
            return False
        
        # STEP 3: Pyramid triggered! Execute it
        logger.warning(f"🧨 PYRAMID DETECTED for {symbol}!")
        logger.warning(f"   Entry: {entry_price:.5f}")
        logger.warning(f"   Current: {current_price:.5f}")
        logger.warning(f"   +0.5R: {pyramid['pyramid_entry']:.5f}")
        logger.warning(f"   Add: {pyramid['pyramid_lot']:.2f} lots")
        logger.warning(f"   Total: {pyramid['total_lot']:.2f} lots")
        logger.warning(f"   New SL: {pyramid['new_sl']:.5f} (BE)")
        
        # STEP 4: Execute pyramid
        success = self.pyramid_mgr.apply_pyramid(pyramid)
        
        if success:
            logger.info(f"✅ Pyramid executed: {symbol} +0.5R")
            return True
        else:
            logger.error(f"❌ Pyramid execution failed: {symbol}")
            return False
    
    def close_position_after_pyramid(self, symbol: str, direction: str):
        """
        🔴 PHASE 3: After pyramid, reset tracking
        
        When position is closed (by scale-out, hard close, etc):
        Reset the pyramid manager so this position can pyramid again if reopened
        
        Args:
            symbol: Trading symbol
            direction: BUY or SELL
        """
        self.pyramid_mgr.reset_pyramid(symbol, direction)
        logger.debug(f"Pyramid tracking reset for {symbol}")


# ============================================================================
# Example Usage in Main Bot Loop
# ============================================================================

def main_bot_loop_example():
    """
    Example of how to use pyramiding in main trading loop
    """
    
    integration = PyramidingBotIntegration()
    mt5 = get_mt5_client()
    
    # Main trading loop (simplified)
    while True:
        try:
            # === ENTRY PHASE ===
            # Check for signals
            signals = get_trading_signals()  # Your signal generation
            
            for signal in signals:
                symbol = signal['symbol']
                direction = signal['direction']
                confidence = signal['confidence']
                sl_pips = signal['sl_pips']
                
                # Try to enter with dynamic validation
                entered = integration.enter_trade_with_validation(
                    symbol, direction, confidence, sl_pips
                )
                
                if entered:
                    logger.info(f"✅ Trade entered: {symbol} {direction}")
                else:
                    logger.info(f"❌ Trade rejected: {symbol}")
            
            # === MONITORING PHASE ===
            # Get open positions
            positions = mt5.get_all_positions()
            
            for position in positions:
                symbol = position['symbol']
                
                # Check if pyramid should activate
                pyramid_executed = integration.monitor_position_for_pyramiding(
                    symbol, position
                )
                
                if pyramid_executed:
                    logger.warning(f"🧨 Pyramid added on {symbol}")
                    # Continue trading with new combined size
                
                # === SCALE-OUT / EXIT PHASE (from AGGRESSIVE_SCALPING) ===
                # This is handled by the scale-out manager (separate)
                # Check TP hits, trailing stop, hard close, etc.
                # Not shown here, but happens simultaneously
            
            # Sleep before next iteration
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            continue


def get_trading_signals():
    """Placeholder for signal generation"""
    return []


# ============================================================================
# Testing Example
# ============================================================================

if __name__ == "__main__":
    """
    Test dynamic sizing + pyramiding
    """
    
    # Example 1: Dynamic sizing validation
    print("\n=== Test 1: Dynamic Sizing Validation ===")
    
    calculated_lot = 0.035  # Small lot
    
    # If account balance > $10k, min is 0.10, so this should be REJECTED
    final_lot = validate_trade_size_dynamic("EURUSD", calculated_lot)
    
    if final_lot is None:
        print(f"❌ Trade rejected: 0.035 is below minimum (balance > $10k)")
    else:
        print(f"✅ Trade accepted: {final_lot}")
    
    # Example 2: Pyramiding on price movement
    print("\n=== Test 2: Pyramiding Activation ===")
    
    integration = PyramidingBotIntegration()
    
    # Simulate price movement
    position = {
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'entry_price': 1.0850,
        'volume': 0.10,
        'sl': 1.0794,
        'open_price': 1.0850
    }
    
    # Current price at +0.5R
    # Would need actual MT5 to test, but logic is:
    # pyramid = integration.monitor_position_for_pyramiding("EURUSD", position)
    # if pyramid:
    #     print("✅ Pyramid triggered at +0.5R")
    
    print("Pyramiding integration ready")
