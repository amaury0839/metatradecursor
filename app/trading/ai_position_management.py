"""
🟢 AI POSITION MANAGEMENT - 3 Key Rules

1️⃣  EXIT GOVERNOR: AI evaluates open positions for exit
   If position is OPEN AND AI == HOLD AND technical != STRONG AND trade is negative/stagnant
   → CLOSE or REDUCE position

2️⃣  TIME FILTER: AI detects market momentum dead zones
   If AI says HOLD for N consecutive cycles
   → Close scalping positions, pause new entries on that symbol

3️⃣  RISK CUTTER: AI controls risk exposure
   If AI confidence < threshold
   → Reduce allowed risk to 0 or tighten stops
"""

from typing import NamedTuple, Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass
from app.core.logger import setup_logger

logger = setup_logger("ai_position_management")


class AIPositionSignal(Enum):
    """AI signal for position management"""
    HOLD_POSITION = "HOLD_POSITION"
    REDUCE_POSITION = "REDUCE_POSITION"
    CLOSE_POSITION = "CLOSE_POSITION"
    MAINTAIN_POSITION = "MAINTAIN_POSITION"
    TIGHT_STOP = "TIGHT_STOP"


@dataclass
class PositionContext:
    """Context for evaluating an open position"""
    symbol: str
    direction: str  # BUY or SELL
    entry_price: float
    current_price: float
    pnl: float  # Realized P&L in account currency
    pnl_percent: float
    lot_size: float
    open_bars: int  # How many bars this position has been open
    is_negative: bool  # P&L < 0
    is_stagnant: bool  # P&L near zero for N bars
    signal_direction: str  # What technical says (BUY/SELL/HOLD)
    signal_strength: float  # Technical signal strength (0-1)
    trading_mode: str  # SCALPING, SWING, PYRAMIDING


@dataclass
class AIPositionDecision:
    """AI decision about what to do with open position"""
    signal: AIPositionSignal
    reason: str
    confidence: float
    risk_adjustment: float  # 1.0 = no change, 0.5 = reduce 50%, 0.0 = block
    exit_fraction: Optional[float] = None  # How much to exit (0-1)


def evaluate_position_for_exit(
    position: PositionContext,
    ai_decision: str,  # What AI said about the market
    ai_confidence: float,
    hold_streak_count: int = 0,
) -> AIPositionDecision:
    """
    🟢 EXIT GOVERNOR: Use AI to evaluate exits for open positions
    
    Key rule:
    If position is OPEN
    AND AI decision == HOLD
    AND technical signal != STRONG (strength < 0.70)
    AND trade is negative or stagnant
    → CLOSE or REDUCE position
    
    Args:
        position: Current open position context
        ai_decision: What AI said (BUY/SELL/HOLD)
        ai_confidence: AI confidence in that decision (0-1)
        hold_streak_count: How many consecutive HOLD decisions (for time filter)
    
    Returns:
        AIPositionDecision with action and risk adjustment
    """
    
    logger.info(f"📍 Evaluating position {position.symbol}: {position.direction} PnL=${position.pnl:.2f}")
    
    # Rule 1: AI HOLD + weak technical + negative trade = EXIT
    if (ai_decision == "HOLD" and 
        position.signal_strength < 0.70 and 
        position.is_negative):
        
        logger.warning(
            f"  🔴 EXIT SIGNAL: AI=HOLD + weak technical + negative trade"
            f" (PnL=${position.pnl:.2f}, strength={position.signal_strength:.2f})"
        )
        
        return AIPositionDecision(
            signal=AIPositionSignal.CLOSE_POSITION,
            reason=f"AI HOLD + weak technical ({position.signal_strength:.2f}) + losing trade",
            confidence=min(1.0, ai_confidence + 0.20),
            risk_adjustment=0.0,
            exit_fraction=1.0  # Close entire position
        )
    
    # Rule 2: AI HOLD + stagnant trade = REDUCE
    if (ai_decision == "HOLD" and 
        position.is_stagnant and 
        position.signal_strength < 0.70):
        
        logger.info(
            f"  🟡 REDUCE SIGNAL: AI=HOLD + stagnant trade"
            f" (PnL=${position.pnl:.2f}, bars open={position.open_bars})"
        )
        
        return AIPositionDecision(
            signal=AIPositionSignal.REDUCE_POSITION,
            reason=f"AI HOLD + stagnant trade after {position.open_bars} bars",
            confidence=min(1.0, ai_confidence + 0.15),
            risk_adjustment=0.5,
            exit_fraction=0.5  # Close 50%
        )
    
    # Rule 3: Scalping mode + AI HOLD streak = CLOSE
    if (position.trading_mode == "SCALPING" and
        ai_decision == "HOLD" and
        hold_streak_count >= 3):  # N consecutive HOLD decisions
        
        logger.warning(
            f"  🔴 TIME FILTER: Scalping + {hold_streak_count} consecutive AI HOLD"
            f" - momentum dead zone detected"
        )
        
        return AIPositionDecision(
            signal=AIPositionSignal.CLOSE_POSITION,
            reason=f"Scalping mode: {hold_streak_count} consecutive AI HOLD = momentum void",
            confidence=min(1.0, ai_confidence + 0.25),
            risk_adjustment=0.0,
            exit_fraction=1.0  # Close entire position
        )
    
    # Rule 4: AI confidence too low = TIGHT STOP
    if ai_confidence < 0.55:
        
        logger.info(
            f"  🟡 RISK CUTTER: AI confidence {ai_confidence:.2f} < 0.55"
            f" - tightening risk controls"
        )
        
        return AIPositionDecision(
            signal=AIPositionSignal.TIGHT_STOP,
            reason=f"AI confidence {ai_confidence:.2f} below threshold",
            confidence=0.5,
            risk_adjustment=0.25,  # Reduce allowed risk to 25%
            exit_fraction=None
        )
    
    # Rule 5: Opposite signal from AI = REDUCE or CLOSE
    if ((position.direction == "BUY" and ai_decision == "SELL") or
        (position.direction == "SELL" and ai_decision == "BUY")):
        
        logger.warning(
            f"  🟡 COUNTER-SIGNAL: Position is {position.direction}"
            f" but AI says {ai_decision}"
        )
        
        # If trade is already negative, close it
        if position.is_negative:
            return AIPositionDecision(
                signal=AIPositionSignal.CLOSE_POSITION,
                reason=f"AI counter-signal ({ai_decision}) + losing trade",
                confidence=ai_confidence,
                risk_adjustment=0.0,
                exit_fraction=1.0
            )
        else:
            # If trade is positive/small, reduce it
            return AIPositionDecision(
                signal=AIPositionSignal.REDUCE_POSITION,
                reason=f"AI counter-signal ({ai_decision}) - reducing exposure",
                confidence=ai_confidence,
                risk_adjustment=0.5,
                exit_fraction=0.5
            )
    
    # Default: Maintain position if everything looks OK
    logger.info(f"  ✅ MAINTAIN: Position looks OK (AI={ai_decision}, PnL=${position.pnl:.2f})")
    
    return AIPositionDecision(
        signal=AIPositionSignal.MAINTAIN_POSITION,
        reason="All checks passed",
        confidence=ai_confidence,
        risk_adjustment=1.0,  # No change
        exit_fraction=None
    )


def evaluate_entry_pause(
    symbol: str,
    hold_streak_count: int,
    consecutive_hold_threshold: int = 3
) -> tuple[bool, str]:
    """
    🟢 TIME FILTER: Pause new entries if AI detects momentum dead zone
    
    If AI says HOLD for N consecutive cycles:
        return (should_pause=True, reason="momentum_void")
    
    Args:
        symbol: Trading symbol
        hold_streak_count: How many HOLD decisions in a row
        consecutive_hold_threshold: Threshold to trigger pause (default=3)
    
    Returns:
        (should_pause_entries, reason)
    """
    
    if hold_streak_count >= consecutive_hold_threshold:
        reason = f"Momentum void: {hold_streak_count} consecutive AI HOLD"
        logger.warning(f"  ⏸️  ENTRY PAUSE {symbol}: {reason}")
        return True, reason
    
    return False, "Normal"


def adjust_risk_for_ai_confidence(
    base_risk_percent: float,
    ai_confidence: float,
    min_confidence_threshold: float = 0.55
) -> Dict[str, Any]:
    """
    🟢 RISK CUTTER: Adjust allowed risk based on AI confidence
    
    If AI confidence < threshold:
        allowed_risk = 0 (or very tight)
    
    If AI confidence medium (0.55-0.70):
        allowed_risk = 0.5x (reduced)
    
    If AI confidence high (>0.70):
        allowed_risk = 1.0x (normal)
    
    Args:
        base_risk_percent: Normal risk (e.g., 1.0%)
        ai_confidence: AI confidence (0-1)
        min_confidence_threshold: Below this, risk = 0
    
    Returns:
        Dict with adjusted_risk and multiplier
    """
    
    if ai_confidence < min_confidence_threshold:
        # Confidence too low: block risk entirely
        adjustment = 0.0
        adjusted_risk = 0.0
        logger.critical(
            f"  🔴 RISK BLOCKED: AI confidence {ai_confidence:.2f} < {min_confidence_threshold:.2f}"
        )
    
    elif ai_confidence >= 0.70:
        # High confidence: normal risk
        adjustment = 1.0
        adjusted_risk = base_risk_percent
        logger.info(
            f"  ✅ RISK NORMAL: AI confidence {ai_confidence:.2f} → "
            f"allowed_risk = {adjusted_risk:.2f}%"
        )
    
    else:
        # Medium confidence (0.55-0.70): reduce risk
        adjustment = 0.5
        adjusted_risk = base_risk_percent * adjustment
        logger.info(
            f"  🟡 RISK REDUCED: AI confidence {ai_confidence:.2f} → "
            f"allowed_risk = {adjusted_risk:.2f}% (50% of {base_risk_percent:.2f}%)"
        )
    
    return {
        "adjusted_risk_percent": adjusted_risk,
        "risk_multiplier": adjustment,
        "ai_confidence": ai_confidence,
        "base_risk_percent": base_risk_percent,
        "decision": "BLOCK" if adjustment == 0.0 else ("REDUCE" if adjustment < 1.0 else "NORMAL")
    }


def should_tighten_stops(
    ai_decision: str,
    ai_confidence: float,
    position_age_bars: int,
    pnl_percent: float
) -> tuple[bool, Optional[float]]:
    """
    Determine if stops should be tightened based on AI signals
    
    Args:
        ai_decision: What AI said (BUY/SELL/HOLD)
        ai_confidence: AI confidence (0-1)
        position_age_bars: How long position is open
        pnl_percent: Current P&L %
    
    Returns:
        (should_tighten, new_stop_offset_percent)
    """
    
    # If AI says HOLD, tighten stops
    if ai_decision == "HOLD":
        new_stop = min(2.0, 5.0 - ai_confidence * 5.0)  # Tighter as confidence increases
        logger.info(f"  🔧 TIGHTEN STOPS: AI=HOLD → stop at {new_stop:.1f}%")
        return True, new_stop
    
    # If old position (>= 20 bars) + AI uncertain (<= 0.65), tighten stops
    if position_age_bars >= 20 and ai_confidence <= 0.65:
        logger.info(f"  🔧 TIGHTEN STOPS: Old position ({position_age_bars} bars) + low AI confidence")
        return True, 3.0
    
    # If stagnant, tighten stops
    if abs(pnl_percent) < 0.1 and position_age_bars > 10:
        logger.info(f"  🔧 TIGHTEN STOPS: Stagnant position for {position_age_bars} bars")
        return True, 2.5
    
    return False, None
