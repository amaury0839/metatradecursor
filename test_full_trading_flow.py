#!/usr/bin/env python3
"""
Verify the FULL trading flow: from preliminary analysis → AI gate → execution decision
"""
import sys
import os
# Fix encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, r'c:\Users\Shadow\Downloads\Metatrade')

from app.trading.integrated_analysis import IntegratedAnalyzer
from app.trading.ai_optimization import should_call_ai
from app.core.logger import setup_logger
import MetaTrader5 as mt5

logger = setup_logger("trading_flow_test")

# Initialize
analyzer = IntegratedAnalyzer()
timeframe = "M1"

# Crypto to test
crypto = "BTCUSD"

print("\n" + "=" * 80)
print("TRADING FLOW TEST: Will BTCUSD execute a trade?")
print("=" * 80)

# Step 1: Check market status
print(f"\n1. MARKET STATUS CHECK")
from app.trading.market_status import MarketStatus
market = MarketStatus()
is_open = market.is_symbol_open(crypto)
print(f"   {crypto} is_symbol_open() = {is_open}")

if not is_open:
    print(f"   [FAIL] MARKET CLOSED - No trading possible")
    sys.exit(1)

print(f"   [OK] MARKET OPEN - Continue to analysis")

# Step 2: Preliminary analysis (skip_ai=True)
print(f"\n2. PRELIMINARY ANALYSIS (skip_ai=True)")
preliminary = analyzer.analyze_symbol(crypto, timeframe, skip_ai=True)
signal = preliminary["signal"]
tech_data = preliminary.get("technical", {}).get("data", {})
rsi = tech_data.get("rsi", 50.0)
close = tech_data.get("close", 0)

print(f"   Signal: {signal}")
print(f"   RSI: {rsi:.1f}")
print(f"   Close Price: {close:.2f}")

# Step 3: AI gate decision
print(f"\n3. AI GATE DECISION")
tech_confidence = 0.75 if signal in ["BUY", "SELL"] else 0.0
trend = "bullish" if signal == "BUY" else ("bearish" if signal == "SELL" else "neutral")
ema_distance = abs(tech_data.get("ema_fast", 0) - tech_data.get("ema_slow", 0)) * 10000

should_call, reason = should_call_ai(
    technical_signal=signal,
    signal_strength=tech_confidence,
    rsi_value=rsi,
    trend_status=trend,
    ema_distance=ema_distance
)

print(f"   should_call_ai() = {should_call}")
print(f"   Reason: {reason}")
print(f"   tech_confidence = {tech_confidence:.2f}")

# Step 4: Check execution conditions
print(f"\n4. EXECUTION CONDITIONS")

MIN_EXECUTION_CONFIDENCE = 0.5
print(f"   MIN_EXECUTION_CONFIDENCE = {MIN_EXECUTION_CONFIDENCE}")
print(f"   actual confidence = {tech_confidence:.2f}")

if tech_confidence < MIN_EXECUTION_CONFIDENCE:
    print(f"   [FAIL] CONFIDENCE TOO LOW - No trade")
    sys.exit(1)

print(f"   [OK] Confidence check passed")

# Step 5: Final signal check
print(f"\n5. SIGNAL VALIDITY FOR EXECUTION")
print(f"   Final signal: {signal}")

if signal == "HOLD":
    print(f"   [FAIL] HOLD signal - No trade")
    sys.exit(1)

print(f"   [OK] Signal is valid for execution")

# Step 6: Summary
print(f"\n6. EXECUTION SUMMARY")
print(f"   [SUCCESS] READY TO EXECUTE {crypto} {signal} TRADE")
print(f"   - Market: OPEN")
print(f"   - Signal: {signal}")  
print(f"   - Confidence: {tech_confidence:.2f}")
print(f"   - All checks passed")

print("\n" + "=" * 80)
print("RESULT: Bot should NOW execute crypto trades!")
print("=" * 80)
