#!/usr/bin/env python
"""Diagnose why the bot is not making trades"""

import sys
from datetime import datetime

print("=" * 60)
print("🔍 TRADING BOT DIAGNOSTIC")
print("=" * 60)
print(f"Timestamp: {datetime.now().isoformat()}\n")

# Test 1: Config loading
print("1️⃣  CONFIGURATION CHECK")
print("-" * 60)
try:
    from app.core.config import get_config
    config = get_config()
    
    print(f"✅ Config loaded successfully")
    print(f"   Trading Mode: {config.trading.mode}")
    print(f"   Symbols: {config.trading.default_symbols}")
    print(f"   Timeframe: {config.trading.default_timeframe}")
    print(f"   Polling Interval: {config.trading.polling_interval_seconds}s")
    print(f"   Risk per trade: {config.trading.default_risk_per_trade}%")
    print(f"   Max daily loss: {config.trading.default_max_daily_loss}%")
    print(f"   Max positions: {config.trading.default_max_positions}")
    
    if config.is_live_mode():
        print(f"   ⚠️  MODE IS LIVE - Real trading ENABLED")
    elif config.is_paper_mode():
        print(f"   ℹ️  MODE IS PAPER - Paper trading (simulated)")
    
except Exception as e:
    print(f"❌ Config error: {e}")
    sys.exit(1)

# Test 2: Kill switch
print("\n2️⃣  KILL SWITCH STATUS")
print("-" * 60)
try:
    from app.core.state import get_state_manager
    state = get_state_manager()
    
    is_active = state.is_kill_switch_active()
    if is_active:
        print(f"🚨 KILL SWITCH IS ACTIVE - Trading PAUSED")
        print(f"   Run: state.deactivate_kill_switch() to enable trading")
    else:
        print(f"✅ Kill switch is INACTIVE - Trading allowed")
        
except Exception as e:
    print(f"❌ State error: {e}")

# Test 3: MT5 Connection
print("\n3️⃣  MT5 CONNECTION STATUS")
print("-" * 60)
try:
    from app.trading.mt5_client import get_mt5_client
    mt5 = get_mt5_client()
    
    if mt5.is_connected():
        print(f"✅ MT5 is CONNECTED")
        info = mt5.get_account_info()
        if info:
            print(f"   Login: {info.get('login', 'N/A')}")
            print(f"   Balance: ${info.get('balance', 0):.2f}")
            print(f"   Equity: ${info.get('equity', 0):.2f}")
            print(f"   Server: {info.get('server', 'N/A')}")
    else:
        print(f"⚠️  MT5 is NOT connected")
        print(f"   Status: {mt5.connected}")
        print(f"   Action: Check if MT5 terminal is running and accessible")
        
except Exception as e:
    print(f"❌ MT5 error: {e}")

# Test 4: Strategy Signals
print("\n4️⃣  STRATEGY SIGNAL GENERATION")
print("-" * 60)
try:
    from app.trading.strategy import get_strategy
    strategy = get_strategy()
    
    # Test first symbol
    symbol = config.trading.default_symbols[0]
    timeframe = config.trading.default_timeframe
    
    signal, indicators, error = strategy.get_signal(symbol, timeframe)
    
    if error:
        print(f"❌ Error getting signal for {symbol}: {error}")
    else:
        print(f"✅ Signal generated for {symbol}/{timeframe}")
        print(f"   Signal: {signal}")
        if indicators:
            print(f"   Indicators available:")
            for key in ['ema_fast', 'ema_slow', 'rsi', 'atr']:
                if key in indicators:
                    val = indicators.get(key)
                    if isinstance(val, (int, float)):
                        print(f"      {key}: {val:.4f}" if isinstance(val, float) else f"      {key}: {val}")
                        
except Exception as e:
    print(f"❌ Strategy error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Risk Management
print("\n5️⃣  RISK MANAGEMENT")
print("-" * 60)
try:
    from app.trading.risk import get_risk_manager
    risk = get_risk_manager()
    
    symbol = config.trading.default_symbols[0]
    
    # Check risk conditions
    risk_ok, failures, norm_volume = risk.check_all_risk_conditions(
        symbol, "BUY", volume=0.01
    )
    
    if risk_ok:
        print(f"✅ Risk checks PASSED for {symbol} (volume used: {norm_volume})")
    else:
        print(f"❌ Risk checks FAILED for {symbol}")
        for failure in failures:
            print(f"   - {failure}")
            
except Exception as e:
    print(f"❌ Risk error: {e}")

# Test 6: Decision Engine
print("\n6️⃣  AI DECISION ENGINE")
print("-" * 60)
try:
    from app.ai.decision_engine import DecisionEngine
    from app.ai.gemini_client import GeminiClient
    
    # Check Gemini availability
    gemini = GeminiClient()
    if gemini.model:
        print(f"✅ Gemini API is AVAILABLE")
    else:
        print(f"⚠️  Gemini API is NOT available (using fallback)")
        
    # Try to make a decision
    engine = DecisionEngine()
    print(f"✅ Decision engine initialized")
    print(f"   Note: Full decision test requires valid signal and technical data")
    
except Exception as e:
    print(f"⚠️  Decision engine issue: {e}")

# Test 7: Execution Manager
print("\n7️⃣  EXECUTION MANAGER")
print("-" * 60)
try:
    from app.trading.execution import get_execution_manager
    execution = get_execution_manager()
    
    if config.is_paper_mode():
        print(f"✅ Paper mode ACTIVE")
        print(f"   Orders will be simulated, not sent to MT5")
    elif config.is_live_mode():
        print(f"⚠️  LIVE mode ACTIVE")
        print(f"   Orders WILL be sent to real MT5 account!")
        print(f"   Make sure risk management is properly configured")
        
except Exception as e:
    print(f"❌ Execution error: {e}")

# Summary
print("\n" + "=" * 60)
print("📊 DIAGNOSIS SUMMARY")
print("=" * 60)

print("\n🎯 CHECKLIST FOR TRADING TO WORK:")
print("   ✓ Config loads without errors")
print("   ✓ Kill switch is INACTIVE")
print("   ✓ MODE is set to LIVE or PAPER")
print("   ✓ MT5 is CONNECTED (if using live data)")
print("   ✓ Strategy generates BUY/SELL signals")
print("   ✓ Risk checks PASS")
print("   ✓ Decision engine is ACTIVE")
print("   ✓ Execution manager is READY")

print("\n💡 COMMON ISSUES:")
print("   1. Kill switch is ACTIVE → Deactivate it")
print("   2. TRADING_MODE=DEMO in .env → Change to MODE=LIVE")
print("   3. MT5 not running → Start MetaTrader 5")
print("   4. Risk checks failing → Adjust risk parameters")
print("   5. Strategy no signal → Market might be closed or no setup")
print("   6. Gemini unavailable → Set GEMINI_API_KEY in .env")

print("\n" + "=" * 60)
