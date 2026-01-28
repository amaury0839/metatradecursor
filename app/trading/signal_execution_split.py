"""
Signal Direction vs Execution Decision Separation
Refactor: Separate signal direction (BUY/SELL/HOLD) from execution_confidence

Key principle: A CLEAR direction doesn't guarantee EXECUTION.
Direction = "BUY" + Confidence = 0.40 → DON'T EXECUTE
"""

from typing import NamedTuple, Optional, Dict, Any
from enum import Enum
from app.core.logger import setup_logger

logger = setup_logger("signal_execution_split")


class SignalDirection(Enum):
    """Pure directional signal (no confidence)"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE = "CLOSE"


class SignalAnalysis(NamedTuple):
    """
    Pure technical signal WITHOUT execution decision
    
    Separates:
    - signal_direction: What the market is telling us (BUY/SELL/HOLD)
    - signal_strength: How clear/strong the signal is (0.0-1.0)
    - reasons: WHY we think this direction
    
    Does NOT include:
    - Execution decision (that's separate)
    - Confidence (that's separate)
    - Risk assessment (that's separate)
    """
    direction: str  # BUY, SELL, HOLD, CLOSE
    strength: float  # 0.0 (weak) to 1.0 (very strong)
    reasons: list  # Technical reasons for this direction
    key_indicators: Dict[str, Any]  # RSI, EMA, ATR, etc for reference


class ExecutionDecision(NamedTuple):
    """
    Execution decision AFTER signal is confirmed
    
    This is the hard gate:
    - Can execute: confidence >= MIN_EXECUTION_CONFIDENCE
    - Cannot execute: confidence < MIN_EXECUTION_CONFIDENCE
    
    Even if signal_direction == "BUY", if execution_confidence < 0.55:
    DO NOT OPEN TRADE.
    """
    should_execute: bool
    execution_confidence: float  # 0.0-1.0 (hard gate at MIN_EXECUTION_CONFIDENCE)
    execution_reason: str  # WHY we're executing (or not)
    required_checks: Dict[str, bool]  # spread, stops, balance, exposure, etc
    skip_reason: Optional[str] = None  # If not executing, why


def split_decision(
    signal_direction: str,
    signal_strength: float,
    technical_score: float,
    ai_score: float = 0.0,
    sentiment_score: float = 0.0,
    ai_call_made: bool = False,
    ai_action: str = "HOLD",
    min_exec_confidence: float = 0.55
) -> tuple[SignalAnalysis, ExecutionDecision]:
    """
    SEPARATE signal_direction from execution_confidence
    
    This is the core refactoring: you can have a clear BUY signal
    but insufficient execution confidence to actually open the trade.
    
    Args:
        signal_direction: BUY, SELL, HOLD from technical analysis
        signal_strength: How clear (0.0-1.0)
        technical_score: Technical analysis score (0.0-1.0)
        ai_score: AI analysis score (0.0-1.0), or 0 if AI not called
        sentiment_score: News sentiment (-1.0 to 1.0)
        ai_call_made: Whether we actually called AI
        ai_action: What AI said (BUY/SELL/HOLD)
        min_exec_confidence: Minimum to execute (typically 0.55)
    
    Returns:
        (SignalAnalysis, ExecutionDecision)
    """
    
    logger.info(f"🔄 SPLIT DECISION: {signal_direction} (strength={signal_strength:.2f})")
    
    # STEP 1: Pure signal analysis (no execution decision yet)
    signal = SignalAnalysis(
        direction=signal_direction,
        strength=signal_strength,
        reasons=[],
        key_indicators={}
    )
    
    logger.info(f"  ✓ Signal direction: {signal.direction} (strength={signal.strength:.2f})")
    
    # STEP 2: Calculate execution confidence (separate from direction)
    # If AI not called, its score is 0
    if not ai_call_made:
        ai_score = 0.0
        ai_weight = 0.0  # AI doesn't contribute if not called
        logger.info(f"  ℹ️  AI not called, weight=0")
    else:
        ai_weight = 0.25
        logger.info(f"  ✓ AI called, score={ai_score:.2f}")
    
    # Weighted confidence
    execution_confidence = (
        0.60 * technical_score +
        ai_weight * ai_score +
        0.15 * max(0.0, sentiment_score)  # Only positive sentiment contributes
    )
    
    # Normalize to 0-1
    execution_confidence = max(0.0, min(1.0, execution_confidence))
    
    logger.info(
        f"  📊 Execution confidence = "
        f"0.60*{technical_score:.2f} + "
        f"{ai_weight:.2f}*{ai_score:.2f} + "
        f"0.15*{max(0.0, sentiment_score):.2f} = {execution_confidence:.2f}"
    )
    
    # STEP 3: Make execution decision (HARD GATE)
    should_exec = execution_confidence >= min_exec_confidence
    
    required_checks = {
        "technical_signal": signal_direction in ["BUY", "SELL"],
        "confidence_threshold": execution_confidence >= min_exec_confidence,
        "ai_approved": True,  # Will be set by caller after risk checks
        "spread_ok": True,    # Will be set by caller
        "stops_valid": True,  # Will be set by caller
        "exposure_ok": True,  # Will be set by caller
        "balance_ok": True,   # Will be set by caller
    }
    
    if should_exec:
        exec_reason = f"Confidence {execution_confidence:.2f} >= threshold {min_exec_confidence:.2f}"
        skip_reason = None
        logger.info(f"  ✅ EXECUTE: {exec_reason}")
    else:
        skip_reason = f"CONFIDENCE_TOO_LOW ({execution_confidence:.2f} < {min_exec_confidence:.2f})"
        exec_reason = f"Cannot execute: {skip_reason}"
        logger.info(f"  ❌ SKIP: {skip_reason}")
    
    execution = ExecutionDecision(
        should_execute=should_exec,
        execution_confidence=execution_confidence,
        execution_reason=exec_reason,
        required_checks=required_checks,
        skip_reason=skip_reason
    )
    
    return signal, execution


def log_skip_reason(symbol: str, primary_reason: str, details: str = ""):
    """
    Log exactly ONE primary reason for skipping a trade
    
    This prevents log spam and makes debugging easier
    """
    msg = f"⏭️  SKIP {symbol}: {primary_reason}"
    if details:
        msg += f" ({details})"
    logger.warning(msg)
