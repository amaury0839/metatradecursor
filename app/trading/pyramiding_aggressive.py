"""
Aggressive Pyramiding + Dynamic Min Volume

Features:
1. Dynamic minimum volume based on account balance:
   - Balance > $5k → min 0.05 lots (Forex)
   - Balance > $10k → min 0.10 lots (Forex)
   - Below thresholds → NO TRADE (no 0.01 consolation trades)

2. Simple pyramiding strategy:
   - Entry: Initial position size
   - At +0.5R: Add 50% of initial size
   - Combined SL: Move to breakeven (no net risk increase)
   - Result: 1 good trade → trade that pays the day

3. Risk calculation with pyramiding:
   - Initial risk: Normal (2-3% per symbol)
   - Pyramid risk: Incremental only
   - Net risk: Same or lower (SL at BE protects)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple
from app.core.logger import setup_logger
from app.trading.risk import RiskManager

logger = setup_logger("pyramiding")


class PyramidingLevel(Enum):
    """Pyramiding entry levels"""
    INITIAL = 1         # First entry
    PYRAMID_1 = 2      # At +0.5R
    # Can add more levels (PYRAMID_2 at +1.0R, etc)


@dataclass
class PyramidPosition:
    """Tracks a pyramided position across multiple entries"""
    symbol: str
    direction: str          # "BUY" or "SELL"
    initial_entry: float    # First entry price
    initial_lot: float      # First lot size
    entries: list = None    # List of entry dicts: {price, lot, level}
    total_lot: float = 0.0  # Sum of all lots
    combined_sl: float = 0.0  # Combined SL (at BE after first +0.5R)
    
    def __post_init__(self):
        if self.entries is None:
            self.entries = []
        self.total_lot = self.initial_lot
    
    def add_entry(self, price: float, lot: float, level: PyramidingLevel):
        """Add a new entry to the pyramid"""
        self.entries.append({
            "price": price,
            "lot": lot,
            "level": level,
        })
        self.total_lot += lot
        logger.info(
            f"🔺 PYRAMID ADDED: {self.symbol} {self.direction} +{lot:.2f} lots @ {price:.5f} "
            f"(Level: {level.name}, Total: {self.total_lot:.2f})"
        )
    
    def get_weighted_entry_price(self) -> float:
        """Calculate volume-weighted average entry price"""
        if self.total_lot == 0:
            return self.initial_entry
        
        total_price_lot = self.initial_entry * self.initial_lot
        for entry in self.entries:
            total_price_lot += entry["price"] * entry["lot"]
        
        return total_price_lot / self.total_lot
    
    def calculate_combined_profit_r(self, current_price: float, initial_sl: float) -> float:
        """
        Calculate current profit in Risk units (R)
        
        R = (current_price - weighted_entry) / (weighted_entry - SL)
        """
        weighted_entry = self.get_weighted_entry_price()
        risk_per_unit = abs(weighted_entry - initial_sl)
        
        if risk_per_unit == 0:
            return 0.0
        
        if self.direction == "BUY":
            profit = current_price - weighted_entry
        else:  # SELL
            profit = weighted_entry - current_price
        
        return profit / risk_per_unit


class DynamicMinVolume:
    """
    Calculate minimum volume dynamically based on account balance
    
    Rules:
    - Balance > $10k → min 0.10 lots
    - Balance > $5k → min 0.05 lots
    - Balance < $5k → NO TRADE (return 0.0 = reject)
    """
    
    # Thresholds for Forex (in USD)
    BALANCE_THRESHOLD_HIGH = 10000  # $10k
    MIN_LOT_HIGH = 0.10             # 0.10 lot minimum
    
    BALANCE_THRESHOLD_MID = 5000    # $5k
    MIN_LOT_MID = 0.05              # 0.05 lot minimum
    
    @classmethod
    def get_min_lot(cls, account_balance: float, symbol: str) -> float:
        """
        Get minimum lot size based on account balance
        
        Args:
            account_balance: Current account balance in USD
            symbol: Trading symbol (to detect asset type)
            
        Returns:
            Minimum lot size, or 0.0 if balance below threshold (NO TRADE)
        """
        is_crypto = any(crypto in symbol.upper() 
                       for crypto in ["BTC", "ETH", "XRP", "ADA"])
        
        # Crypto uses different rules (can be smaller minimums)
        if is_crypto:
            # For crypto, use smaller minimums even with small balance
            if account_balance > 1000:
                return 0.01  # Crypto min can be very small
            else:
                return 0.0   # Too small account for crypto
        
        # Forex rules with balance thresholds
        if account_balance >= cls.BALANCE_THRESHOLD_HIGH:
            return cls.MIN_LOT_HIGH  # 0.10 lot minimum
        elif account_balance >= cls.BALANCE_THRESHOLD_MID:
            return cls.MIN_LOT_MID   # 0.05 lot minimum
        else:
            # Below threshold: NO TRADE (not even 0.01 consolation)
            logger.warning(
                f"Account balance ${account_balance:.2f} below minimum "
                f"threshold ${cls.BALANCE_THRESHOLD_MID}. NO TRADE."
            )
            return 0.0


class PyramidingEngine:
    """
    Orchestrates pyramiding strategy:
    1. Track initial entry + lot
    2. Monitor +0.5R target
    3. Add 50% of initial lot at +0.5R
    4. Move combined SL to breakeven
    5. Let combined position run with trailing or scaled exits
    """
    
    def __init__(self):
        self.risk_manager = RiskManager()
        self.pyramided_positions: Dict[str, PyramidPosition] = {}
        self.pyramid_profit_threshold_r = 0.5  # Add at +0.5R
        self.pyramid_size_percent = 0.50       # Add 50% of initial
    
    def initialize_pyramid(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        initial_lot: float,
        initial_sl: float,
    ) -> PyramidPosition:
        """
        Initialize a new pyramided position
        
        Args:
            symbol: Trading symbol
            direction: "BUY" or "SELL"
            entry_price: Entry price of first trade
            initial_lot: Lot size of first trade
            initial_sl: Stop loss price (will stay here until pyramid added)
            
        Returns:
            PyramidPosition object
        """
        position = PyramidPosition(
            symbol=symbol,
            direction=direction,
            initial_entry=entry_price,
            initial_lot=initial_lot,
        )
        position.combined_sl = initial_sl
        
        self.pyramided_positions[symbol] = position
        logger.info(
            f"🔺 PYRAMID INIT: {symbol} {direction} {initial_lot:.2f} lots @ "
            f"{entry_price:.5f} SL: {initial_sl:.5f}"
        )
        
        return position
    
    def check_pyramid_trigger(
        self,
        symbol: str,
        current_price: float,
    ) -> Tuple[bool, float, float]:
        """
        Check if current position hits +0.5R (pyramid trigger)
        
        Args:
            symbol: Trading symbol
            current_price: Current price
            
        Returns:
            Tuple of (should_pyramid, pyramid_lot, new_entry_price)
            or (False, 0.0, 0.0) if not triggered
        """
        if symbol not in self.pyramided_positions:
            return False, 0.0, 0.0
        
        position = self.pyramided_positions[symbol]
        
        # Calculate current profit in R
        profit_r = position.calculate_combined_profit_r(
            current_price, 
            position.combined_sl
        )
        
        if profit_r < self.pyramid_profit_threshold_r:
            # Not yet at +0.5R
            return False, 0.0, 0.0
        
        # Check if already pyramided at this level
        for entry in position.entries:
            if entry["level"] == PyramidingLevel.PYRAMID_1:
                # Already pyramided once, don't do it again
                return False, 0.0, 0.0
        
        # Calculate pyramid entry details
        pyramid_lot = position.initial_lot * self.pyramid_size_percent
        pyramid_entry = current_price  # Enter at current market price
        
        logger.info(
            f"🔺 PYRAMID TRIGGER at +{profit_r:.2f}R: "
            f"{symbol} {position.direction} will add {pyramid_lot:.2f} lots @ {pyramid_entry:.5f}"
        )
        
        return True, pyramid_lot, pyramid_entry
    
    def apply_pyramid(
        self,
        symbol: str,
        pyramid_lot: float,
        pyramid_entry: float,
    ) -> Tuple[bool, float, str]:
        """
        Apply the pyramid: add lot + move SL to BE
        
        Args:
            symbol: Trading symbol
            pyramid_lot: Lot size to add
            pyramid_entry: Entry price of pyramid (current market)
            
        Returns:
            Tuple of (success, new_combined_sl, status_message)
        """
        if symbol not in self.pyramided_positions:
            return False, 0.0, "Position not found"
        
        position = self.pyramded_positions[symbol]
        
        # Add the entry to pyramid
        position.add_entry(pyramid_entry, pyramid_lot, PyramidingLevel.PYRAMID_1)
        
        # Move SL to original entry price (breakeven)
        # This converts it to a "free trade" - no additional risk
        new_sl = position.initial_entry
        position.combined_sl = new_sl
        
        msg = (
            f"🔺 PYRAMID APPLIED: {symbol} {position.direction} "
            f"Total: {position.total_lot:.2f} lots, "
            f"Avg Entry: {position.get_weighted_entry_price():.5f}, "
            f"SL→BE: {new_sl:.5f}"
        )
        logger.info(msg)
        
        return True, new_sl, msg
    
    def calculate_pyramid_impact(self, symbol: str) -> Dict:
        """
        Calculate the impact of pyramiding on a position
        
        Returns dict with:
        - initial_lot: Original lot size
        - pyramid_lot: Size added at +0.5R
        - total_lot: Combined size
        - weighted_entry: Volume-weighted average entry
        - combined_sl: SL at BE
        - risk_increase_pct: % increase in capital at risk
        """
        if symbol not in self.pyramded_positions:
            return {}
        
        position = self.pyramded_positions[symbol]
        
        return {
            "initial_lot": position.initial_lot,
            "pyramid_lot": position.initial_lot * self.pyramid_size_percent,
            "total_lot": position.total_lot,
            "weighted_entry": position.get_weighted_entry_price(),
            "combined_sl": position.combined_sl,
            "risk_increase_pct": (position.total_lot - position.initial_lot) / position.initial_lot * 100,
        }
    
    def get_position_status(self, symbol: str, current_price: float) -> Optional[Dict]:
        """Get current status of pyramided position"""
        if symbol not in self.pyramded_positions:
            return None
        
        position = self.pyramded_positions[symbol]
        profit_r = position.calculate_combined_profit_r(current_price, position.combined_sl)
        
        return {
            "symbol": symbol,
            "direction": position.direction,
            "total_lot": position.total_lot,
            "weighted_entry": position.get_weighted_entry_price(),
            "combined_sl": position.combined_sl,
            "current_price": current_price,
            "profit_r": profit_r,
            "entries": len([position.initial_entry] + position.entries),
        }
    
    def close_pyramid(self, symbol: str) -> bool:
        """Close/clean up a pyramided position"""
        if symbol in self.pyramded_positions:
            position = self.pyramded_positions[symbol]
            logger.info(
                f"🔺 PYRAMID CLOSED: {symbol} {position.direction} "
                f"{position.total_lot:.2f} lots (had {len(position.entries)+1} entries)"
            )
            del self.pyramded_positions[symbol]
            return True
        return False


class PyramidingIntegration:
    """Integration layer for bot to use pyramiding + dynamic min volumes"""
    
    def __init__(self):
        self.engine = PyramidingEngine()
        self.risk_manager = RiskManager()
        self._instance = None
    
    def check_min_lot_requirement(self, symbol: str, balance: float) -> Tuple[float, bool]:
        """
        Check if account balance allows trading this symbol
        
        Returns:
            (min_lot, is_allowed) where is_allowed=False if balance too low
        """
        min_lot = DynamicMinVolume.get_min_lot(balance, symbol)
        
        if min_lot == 0.0:
            logger.warning(
                f"🚫 INSUFFICIENT BALANCE for {symbol}: ${balance:.2f} "
                f"(need ${DynamicMinVolume.BALANCE_THRESHOLD_MID})"
            )
            return 0.0, False
        
        return min_lot, True
    
    def should_allow_trade(
        self, 
        symbol: str,
        proposed_lot: float,
        account_balance: float,
    ) -> Tuple[bool, str]:
        """
        Final gate: check if trade should be allowed
        
        Rules:
        1. Check balance threshold
        2. Check proposed lot >= minimum
        3. If not, reject (NO TRADE, not 0.01 consolation)
        """
        min_lot, is_allowed = self.check_min_lot_requirement(symbol, account_balance)
        
        if not is_allowed:
            return False, f"Balance ${account_balance:.2f} below minimum threshold"
        
        if proposed_lot < min_lot:
            return False, f"Proposed lot {proposed_lot:.2f} < minimum {min_lot:.2f}"
        
        return True, "OK"
    
    def initialize_scalping_with_pyramid(
        self,
        symbol: str,
        direction: str,
        entry_price: float,
        initial_lot: float,
        initial_sl: float,
        account_balance: float,
    ) -> Tuple[bool, str]:
        """
        Initialize a scalping trade with pyramiding potential
        
        Returns:
            (success, message)
        """
        # First check dynamic minimum
        should_trade, reason = self.should_allow_trade(
            symbol, initial_lot, account_balance
        )
        
        if not should_trade:
            return False, f"Trade rejected: {reason}"
        
        # Initialize pyramid tracking
        self.engine.initialize_pyramid(
            symbol, direction, entry_price, initial_lot, initial_sl
        )
        
        logger.info(
            f"✅ SCALPING INITIALIZED with PYRAMID POTENTIAL: "
            f"{symbol} {direction} {initial_lot:.2f} lots "
            f"(min required: {DynamicMinVolume.get_min_lot(account_balance, symbol):.2f})"
        )
        
        return True, "Trade initialized"
    
    def check_pyramid_and_execute(
        self,
        symbol: str,
        current_price: float,
        account_balance: float,
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Check if pyramid should trigger, and if so, prepare execution data
        
        Returns:
            (should_pyramid, pyramid_details) or (False, None)
        """
        # Check pyramid trigger
        should_pyramid, pyramid_lot, pyramid_entry = self.engine.check_pyramid_trigger(
            symbol, current_price
        )
        
        if not should_pyramid:
            return False, None
        
        # Verify we still have room to add lot
        should_trade, reason = self.should_allow_trade(
            symbol, pyramid_lot, account_balance
        )
        
        if not should_trade:
            logger.warning(
                f"Pyramid trigger blocked for {symbol}: {reason}"
            )
            return False, None
        
        # Prepare pyramid details for execution
        success, new_sl, msg = self.engine.apply_pyramid(
            symbol, pyramid_lot, pyramid_entry
        )
        
        if success:
            impact = self.engine.calculate_pyramid_impact(symbol)
            
            return True, {
                "symbol": symbol,
                "pyramid_lot": pyramid_lot,
                "pyramid_entry": pyramid_entry,
                "new_combined_sl": new_sl,
                "total_position_lot": impact["total_lot"],
                "message": msg,
            }
        
        return False, None


# Singleton instance
_pyramiding_instance = None


def get_pyramiding_engine() -> PyramidingIntegration:
    """Get singleton instance of pyramiding engine"""
    global _pyramiding_instance
    if _pyramiding_instance is None:
        _pyramiding_instance = PyramidingIntegration()
    return _pyramiding_instance
