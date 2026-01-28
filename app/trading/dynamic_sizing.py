"""
Dynamic position sizing and pyramiding system

Features:
- Dynamic min_volume based on account balance
- Pyramiding on +0.5R (adds 50% of original size)
- SL adjustment to breakeven after pyramid
- NO consolation trades (reject if doesn't meet minimum)
"""

from typing import Optional, Dict, Tuple
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client

logger = setup_logger("dynamic_sizing")


class DynamicSizingConfig:
    """Configuration for dynamic sizing based on balance"""
    
    # FOREX min_volume by balance (Forex-specific)
    # Si balance > 5k → min 0.05
    # Si balance > 10k → min 0.10
    FOREX_MIN_VOLUME_CONFIG = {
        "default": 0.01,      # Balance <= $5k: min 0.01
        "balance_5k": 0.05,   # Balance > $5k: min 0.05
        "balance_10k": 0.10,  # Balance > $10k: min 0.10
    }
    
    # Pyramid configuration
    PYRAMID_CONFIG = {
        "enabled": True,                      # Pyramiding ON
        "activation_profit_r": 0.5,          # Activates at +0.5R
        "add_size_percent": 0.50,            # Add 50% of original
        "max_pyramids_per_trade": 1,         # Max 1 pyramid per trade
        "move_sl_to_be": True,               # SL to breakeven after pyramid
    }


class DynamicSizer:
    """
    Manages dynamic position sizing based on account balance
    
    Determines minimum volumes based on:
    - Account balance
    - Symbol type (Forex vs Crypto)
    - Trading rules
    """
    
    def __init__(self):
        self.mt5 = get_mt5_client()
    
    def get_balance(self) -> float:
        """Get current account balance"""
        account_info = self.mt5.get_account_info()
        if account_info:
            return float(account_info.get("balance", 0))
        return 0
    
    def get_forex_min_volume(self) -> float:
        """
        🔥 DYNAMIC MIN VOLUME FOR FOREX
        
        Si balance > 10k → min 0.10
        Si balance > 5k → min 0.05
        Si balance <= 5k → min 0.01
        
        Returns:
            Minimum volume for Forex trades
        """
        balance = self.get_balance()
        
        if balance > 10000:
            return DynamicSizingConfig.FOREX_MIN_VOLUME_CONFIG["balance_10k"]  # 0.10
        elif balance > 5000:
            return DynamicSizingConfig.FOREX_MIN_VOLUME_CONFIG["balance_5k"]    # 0.05
        else:
            return DynamicSizingConfig.FOREX_MIN_VOLUME_CONFIG["default"]       # 0.01
    
    def get_crypto_min_volume(self) -> float:
        """
        For crypto, use symbol-specific minimums (from risk.py)
        Not dynamically scaled like Forex
        """
        # Crypto has fixed minimums per symbol (BTC, ETH, etc)
        return 0.01  # Fallback
    
    def is_valid_size(self, symbol: str, volume: float) -> Tuple[bool, Optional[str]]:
        """
        🔥 VALIDATE: If size < min_volume → REJECT
        NO consolation trades (no 0.01 if needs 0.05)
        
        Args:
            symbol: Trading symbol
            volume: Calculated position size
            
        Returns:
            (is_valid, reason_if_invalid)
        """
        is_crypto = any(c in symbol.upper() for c in ["BTC", "ETH", "XRP", "ADA"])
        
        if is_crypto:
            # Crypto: use fixed symbol minimums
            crypto_minimums = {
                "XRPUSD": 50,
                "ADAUSD": 1000,
                "ETHUSD": 0.05,
                "BTCUSD": 0.001,
            }
            min_vol = crypto_minimums.get(symbol, 0.01)
        else:
            # Forex: use dynamic minimum based on balance
            min_vol = self.get_forex_min_volume()
        
        if volume < min_vol:
            reason = f"Volume {volume:.4f} < minimum {min_vol:.4f} (balance: ${self.get_balance():.0f})"
            logger.warning(f"REJECT TRADE {symbol}: {reason}")
            return False, reason
        
        return True, None
    
    def validate_and_clamp_size(self, symbol: str, calculated_volume: float) -> Optional[float]:
        """
        🔥 CRITICAL: Validate size or REJECT (NO consolation trades)
        
        If volume < minimum:
        - REJECT (return None)
        - NO fallback to 0.01
        - NO forced reduction
        
        Args:
            symbol: Trading symbol
            calculated_volume: Position size from risk calculation
            
        Returns:
            Valid volume, or None if invalid
        """
        is_valid, reason = self.is_valid_size(symbol, calculated_volume)
        
        if not is_valid:
            logger.error(f"TRADE REJECTED: {symbol} - {reason}")
            return None
        
        logger.info(f"TRADE VALID: {symbol} volume {calculated_volume:.4f}")
        return calculated_volume


class PyramidingManager:
    """
    Manages pyramiding: add position size on +0.5R
    
    Example:
    - Entry BUY 1.0 lot @ 1.0850, SL 1.0794
    - Price reaches +0.5R (1.0875)
    - ADD 0.5 lots @ 1.0875
    - Combined SL: move to 1.0850 (breakeven for both)
    """
    
    def __init__(self):
        self.mt5 = get_mt5_client()
        self.active_pyramids = {}  # Track pyramids per position
    
    def calculate_pyramid_activation(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        original_lot: float,
        atr: float,
        sl_price: float,
        direction: str
    ) -> Optional[Dict]:
        """
        🧨 AGGRESSIVE PYRAMIDING
        
        Check if position should be pyramided:
        - BUY: If current > entry + (atr * 2 * 0.5) → +0.5R hit
        - SELL: If current < entry - (atr * 2 * 0.5) → +0.5R hit
        
        If YES → Return pyramid action
        
        Args:
            symbol: Trading symbol
            entry_price: Original entry price
            current_price: Current market price
            original_lot: Original position size
            atr: ATR value
            sl_price: Original SL price
            direction: "BUY" or "SELL"
            
        Returns:
            Dict with pyramid details, or None
        """
        # Calculate +0.5R threshold
        tp_distance = atr * 2.0  # Full TP distance
        half_r = tp_distance * 0.5  # +0.5R
        
        # Check if +0.5R is hit
        if direction == "BUY":
            profit_threshold = entry_price + half_r
            is_hit = current_price >= profit_threshold
            pyramid_price = profit_threshold
            
        else:  # SELL
            profit_threshold = entry_price - half_r
            is_hit = current_price <= profit_threshold
            pyramid_price = profit_threshold
        
        if not is_hit:
            return None
        
        # Check if already pyramided
        position_key = f"{symbol}_{direction}"
        if self.active_pyramids.get(position_key, False):
            logger.debug(f"{symbol}: Already pyramided, skip")
            return None
        
        # Calculate pyramid size: 50% of original
        pyramid_lot = original_lot * DynamicSizingConfig.PYRAMID_CONFIG["add_size_percent"]
        
        logger.info(f"🧨 PYRAMID ACTIVATED: {symbol}")
        logger.info(f"   Original lot: {original_lot:.2f}")
        logger.info(f"   Add pyramid: {pyramid_lot:.2f} (50%)")
        logger.info(f"   Total: {original_lot + pyramid_lot:.2f} lots")
        
        pyramid_action = {
            "symbol": symbol,
            "direction": direction,
            "pyramid_lot": pyramid_lot,
            "total_lot": original_lot + pyramid_lot,
            "original_entry": entry_price,
            "pyramid_entry": pyramid_price,
            "original_sl": sl_price,
            "new_sl": entry_price,  # Move SL to BE
            "move_sl_to_be": True,
            "status": "pending_execution"
        }
        
        # Mark as pyramided
        self.active_pyramids[position_key] = True
        
        return pyramid_action
    
    def apply_pyramid(self, pyramid_action: Dict) -> bool:
        """
        Execute pyramid action in MT5
        
        - Open additional position (pyramid_lot)
        - Update SL of BOTH positions to breakeven
        
        Args:
            pyramid_action: Pyramid details from calculate_pyramid_activation
            
        Returns:
            True if successful
        """
        try:
            symbol = pyramid_action["symbol"]
            direction = pyramid_action["direction"]
            pyramid_lot = pyramid_action["pyramid_lot"]
            new_sl = pyramid_action["new_sl"]
            
            logger.info(f"Executing pyramid for {symbol}...")
            
            # Open new position (pyramid)
            result = self.mt5.buy(
                symbol,
                pyramid_lot,
                pyramid_action["pyramid_entry"],
                new_sl,
                None,  # TP: will manage with scale-out
                comment=f"PYRAMID: +0.5R add {pyramid_lot:.2f}",
                magic=99999  # Pyramid magic number
            ) if direction == "BUY" else self.mt5.sell(
                symbol,
                pyramid_lot,
                pyramid_action["pyramid_entry"],
                new_sl,
                None,
                comment=f"PYRAMID: +0.5R add {pyramid_lot:.2f}",
                magic=99999
            )
            
            if not result:
                logger.error(f"Pyramid failed for {symbol}")
                return False
            
            # Get original position and update SL
            positions = self.mt5.get_positions(symbol)
            for pos in positions:
                if pos["comment"] != f"PYRAMID: +0.5R add {pyramid_lot:.2f}":
                    # Update original position SL to BE
                    self.mt5.update_sl(pos["ticket"], new_sl)
                    logger.info(f"Updated original position {pos['ticket']} SL to {new_sl}")
            
            logger.info(f"✅ Pyramid executed: {pyramid_lot:.2f} added @ {new_sl}")
            return True
            
        except Exception as e:
            logger.error(f"Pyramid execution error: {e}")
            return False
    
    def reset_pyramid(self, symbol: str, direction: str):
        """Reset pyramid tracking for this position"""
        position_key = f"{symbol}_{direction}"
        self.active_pyramids.pop(position_key, None)
        logger.debug(f"Pyramid reset for {symbol}")


# Global instances
_dynamic_sizer = None
_pyramiding_manager = None


def get_dynamic_sizer() -> DynamicSizer:
    """Get global DynamicSizer instance"""
    global _dynamic_sizer
    if _dynamic_sizer is None:
        _dynamic_sizer = DynamicSizer()
    return _dynamic_sizer


def get_pyramiding_manager() -> PyramidingManager:
    """Get global PyramidingManager instance"""
    global _pyramiding_manager
    if _pyramiding_manager is None:
        _pyramiding_manager = PyramidingManager()
    return _pyramiding_manager
