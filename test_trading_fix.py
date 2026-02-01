#!/usr/bin/env python3
"""
Test that crypto trading now works after HOLD skip fix
"""
import sys
import os
sys.path.insert(0, r'c:\Users\Shadow\Downloads\Metatrade')

from app.trading.integrated_analysis import IntegratedAnalyzer
from app.trading.ai_optimization import should_call_ai
from app.core.logger import setup_logger

logger = setup_logger("test_fix")

# Initialize analyzer
analyzer = IntegratedAnalyzer()
timeframe = "M1"  # 1-minute timeframe

# Test crypto symbols
crypto_symbols = ["BTCUSD", "ETHUSD", "BNBUSD"]

logger.info("=" * 70)
logger.info("TESTING: Does HOLD signal now trigger AI re-analysis?")
logger.info("=" * 70)

for symbol in crypto_symbols:
    print(f"\n🔍 Testing {symbol}...")
    
    # Step 1: Preliminary analysis (skip_ai=True)
    preliminary = analyzer.analyze_symbol(symbol, timeframe, skip_ai=True)
    signal = preliminary["signal"]
    tech_data = preliminary.get("technical", {}).get("data", {})
    rsi = tech_data.get("rsi", 50.0)
    
    print(f"  📊 Preliminary (skip_ai=True): signal={signal}, RSI={rsi:.1f}")
    
    # Step 2: Check should_call_ai() with HOLD signal
    should_call, reason = should_call_ai(
        technical_signal=signal,
        signal_strength=0.75 if signal in ["BUY", "SELL"] else 0.0,
        rsi_value=rsi,
        trend_status="neutral",
        ema_distance=0
    )
    
    print(f"  🤖 should_call_ai() = {should_call} ({reason})")
    
    # Step 3: If should_call_ai is True, re-analyze with AI
    if should_call:
        print(f"  ✅ AI will be called for {symbol}!")
        ai_analysis = analyzer.analyze_symbol(symbol, timeframe, skip_ai=False)
        ai_signal = ai_analysis["signal"]
        print(f"  📊 AI-enhanced: signal={ai_signal}")
    else:
        print(f"  ⚠️  AI will NOT be called for {symbol}")

logger.info("\n" + "=" * 70)
logger.info("Test complete!")
logger.info("=" * 70)
