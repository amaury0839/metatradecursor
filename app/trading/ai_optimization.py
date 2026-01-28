"""
AI Call Optimization
Call AI only when technical signal is weak/ambiguous

Avoid calling AI when:
- Technical signal is STRONG_BUY or STRONG_SELL
- Trend is clearly bullish or bearish
- RSI is far from neutral range (< 30 or > 70)
"""

from typing import Tuple, Dict, Any
from app.core.logger import setup_logger

logger = setup_logger("ai_optimization")


def should_call_ai(
    technical_signal: str,
    signal_strength: float,
    rsi_value: float,
    trend_status: str,
    ema_distance: float,
    signal_direction: str = None  # Optional: for debugging/logging
) -> Tuple[bool, str]:
    """
    Determine if we should call AI for this signal
    
    Call AI when:
    ✅ Signal is weak (strength < 0.65)
    ✅ Signal is ambiguous/HOLD
    ✅ RSI is in neutral zone (30-70)
    ✅ Trend is unclear
    
    Skip AI (waste of latency) when:
    ❌ Signal is STRONG_BUY or STRONG_SELL (strength >= 0.75)
    ❌ RSI is extreme (< 25 or > 75)
    ❌ Trend is very clear (EMA distance > 50 pips)
    
    Args:
        technical_signal: BUY, SELL, HOLD
        signal_strength: 0.0-1.0
        rsi_value: 0-100
        trend_status: "bullish", "bearish", "neutral"
        ema_distance: Distance between fast/slow EMA in pips
        signal_direction: Optional (for compatibility/logging)
    
    Returns:
        (should_call, reason)
    """
    
    # STRONG SIGNAL: Skip AI (waste of latency)
    if signal_strength >= 0.75 and technical_signal in ["BUY", "SELL"]:
        reason = f"Strong signal (strength={signal_strength:.2f}), skip AI"
        return False, reason
    
    # CLEAR TREND: Skip AI
    if ema_distance > 50 and trend_status in ["bullish", "bearish"]:
        reason = f"Clear trend ({trend_status}, EMA distance={ema_distance:.1f} pips), skip AI"
        return False, reason
    
    # RSI EXTREME: Skip AI (too much noise)
    if rsi_value > 75 or rsi_value < 25:
        reason = f"RSI extreme ({rsi_value:.0f}), skip AI"
        return False, reason
    
    # WEAK SIGNAL: Call AI as arbitrator
    if signal_strength < 0.65 or technical_signal == "HOLD":
        reason = f"Weak signal (strength={signal_strength:.2f}), call AI for clarification"
        return True, reason
    
    # AMBIGUOUS: Call AI
    if trend_status == "neutral" and 30 <= rsi_value <= 70:
        reason = f"Ambiguous market (neutral trend, RSI={rsi_value:.0f}), call AI"
        return True, reason
    
    # Default: Call AI (conservative)
    return True, "Default (unclear conditions)"


def build_ai_context(
    symbol: str,
    timeframe: str,
    technical_signal: str,
    signal_strength: float,
    indicators: Dict[str, Any],
    rsi_value: float
) -> Dict[str, Any]:
    """
    Build context for AI call
    
    This context tells AI whether it's a gating decision (weak signal)
    or just a quality filter (strong signal).
    """
    
    context = {
        "symbol": symbol,
        "timeframe": timeframe,
        "technical_signal": technical_signal,
        "signal_strength": signal_strength,
        "rsi": rsi_value,
        "indicators": indicators,
        "ai_role": "",
    }
    
    # Tell AI whether it's "arbitrator" or "quality filter"
    if signal_strength < 0.65:
        context["ai_role"] = "ARBITRATOR"
        context["ai_instruction"] = (
            "Technical signal is weak. You are the tiebreaker. "
            "Make a clear decision: BUY, SELL, or HOLD."
        )
    else:
        context["ai_role"] = "QUALITY_FILTER"
        context["ai_instruction"] = (
            "Technical signal is reasonably strong. "
            "You are a quality gate. Confirm or reject the signal."
        )
    
    return context
