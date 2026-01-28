"""
Decision Architecture Refactoring - Constants and Configuration
Separates signal_direction from execution_confidence
"""

# 🔥 CRITICAL THRESHOLDS
MIN_EXECUTION_CONFIDENCE = 0.55  # Hard gate: never execute below this
MIN_TECHNICAL_SCORE = 0.65  # Technical signal must be strong enough if AI unavailable
MAX_POSITION_CHANGE_PER_TRADE = 3  # Don't more than 3x position at once

# 🎯 RSI EXTREMES (Hard block logic)
RSI_OVERBOUGHT = 75  # Block BUY entries when RSI >= this
RSI_OVERSOLD = 25    # Block SELL entries when RSI <= this

# 💰 SPREAD VALIDATION (moved to first gate)
MAX_SPREAD_PIPS_FOREX = 5  # Max spread for forex pairs
MAX_SPREAD_PIPS_CRYPTO = 50  # Max spread for crypto (much wider)

# 📍 CURRENCY CLUSTER LIMITS
MAX_TRADES_PER_CURRENCY = 3  # Max trades with same base currency
MAX_TRADES_PER_CLUSTER = 6   # Max trades in a cluster (USD, JPY, GBP, Crypto)

CURRENCY_CLUSTERS = {
    "USD": ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCAD"],
    "JPY": ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CADJPY"],
    "GBP": ["GBPUSD", "GBPJPY", "GBPNZD", "GBPAUD", "GBPCAD"],
    "CRYPTO": ["BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD"]
}

# 🚀 CONFIDENCE SCORING (no AI bonus, just calculation)
TECHNICAL_WEIGHT = 0.60
AI_WEIGHT = 0.25
SENTIMENT_WEIGHT = 0.15
# Total = 1.00

# ✂️ AI DECISION MULTIPLIERS (only if confidence > threshold)
AI_CONFIRMATION_MULT = 1.0  # AI confirms technical → 100%
AI_NEUTRAL_MULT = 0.0       # AI HOLD and confidence < MIN → NO_OP
AI_OPPOSITE_MULT = 0.70     # AI opposite → 70% strength

# 📊 DYNAMIC RISK PROFILES (based on Profit Factor)
# ACCIÓN 4: Risk dinámico defensivo por defecto
# If profit_factor <= 1.1: force CONSERVATIVE, max 0.5% risk per trade
# If profit_factor > 1.1 and < 1.5: use BALANCED, max 1.0% risk
# If profit_factor >= 1.5: can use AGGRESSIVE, max 2.0% risk

RISK_PROFILES = {
    "CONSERVATIVE": {
        "max_risk_per_trade": 0.005,  # 0.5% per trade (DEFENSIVE)
        "max_daily_loss": 0.02,       # 2% daily max loss
        "max_drawdown": 0.05,         # 5% max drawdown
        "lot_multiplier": 0.5,        # 50% of normal lot
        "min_profit_factor": 1.1,     # Minimum PF to upgrade
    },
    "BALANCED": {
        "max_risk_per_trade": 0.01,   # 1.0% per trade
        "max_daily_loss": 0.03,       # 3% daily max loss
        "max_drawdown": 0.08,         # 8% max drawdown
        "lot_multiplier": 1.0,        # 100% of normal lot
        "min_profit_factor": 1.3,     # Minimum PF to upgrade
    },
    "AGGRESSIVE": {
        "max_risk_per_trade": 0.02,   # 2.0% per trade
        "max_daily_loss": 0.05,       # 5% daily max loss
        "max_drawdown": 0.12,         # 12% max drawdown
        "lot_multiplier": 2.0,        # 200% of normal lot
        "min_profit_factor": 1.5,     # Minimum PF to maintain
    }
}

# 📊 SKIP REASONS (for clear logging)
SKIP_REASONS = {
    "SPREAD_TOO_HIGH": "Spread exceeds maximum for symbol",
    "CONFIDENCE_TOO_LOW": "Execution confidence below minimum threshold",
    "LOT_TOO_SMALL": "Computed lot below broker minimum",
    "RSI_BLOCK": "RSI at extreme (overbought/oversold for entry direction)",
    "EXPOSURE_LIMIT": "Currency pair/cluster exposure limit reached",
    "INVALID_STOPS": "Stop loss or take profit validation failed",
    "AI_BLOCK": "AI explicitly blocks trade (risk_ok=False)",
    "NO_SIGNAL": "Technical signal is HOLD",
    "INSUFFICIENT_BALANCE": "Account balance insufficient for minimum position",
    "VOLUME_VALIDATION": "Position size calculation failed",
}


def get_risk_profile(profit_factor: float) -> str:
    """
    ACCIÓN 4: Get risk profile based on Profit Factor (defensive by default)
    
    If profit_factor <= 1.1:
        force CONSERVATIVE, max 0.5% risk per trade
    If 1.1 < profit_factor < 1.5:
        use BALANCED, max 1.0% risk
    If profit_factor >= 1.5:
        can use AGGRESSIVE, max 2.0% risk
    
    Args:
        profit_factor: (gross_profit / gross_loss) or 1.0 if no trades
    
    Returns:
        str: "CONSERVATIVE", "BALANCED", or "AGGRESSIVE"
    """
    if profit_factor <= 1.1:
        return "CONSERVATIVE"  # Force conservative with defensive 0.5% risk
    elif profit_factor < 1.5:
        return "BALANCED"  # Use balanced profile
    else:
        return "AGGRESSIVE"  # Can use aggressive profile
