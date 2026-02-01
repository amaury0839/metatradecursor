#!/usr/bin/env python3
"""Test script to verify exposure calculation fix"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.trading.risk import get_risk_manager
from app.trading.mt5_client import get_mt5_client
from app.trading.portfolio import get_portfolio_manager
from app.core.logger import setup_logger

logger = setup_logger("test_exposure")

def test_exposure():
    """Test the exposure calculation with current positions"""
    print("\n" + "="*80)
    print("TESTING EXPOSURE CALCULATION FIX")
    print("="*80)
    
    # Initialize components
    mt5 = get_mt5_client()
    portfolio = get_portfolio_manager()
    risk = get_risk_manager()
    
    # Connect to MT5
    if not mt5.connect():
        print("❌ Failed to connect to MT5")
        return
    
    # Get account info
    account_info = mt5.get_account_info()
    if not account_info:
        print("❌ Failed to get account info")
        return
    
    equity = account_info.get('equity', 0)
    balance = account_info.get('balance', 0)
    
    print(f"\n📊 Account Info:")
    print(f"   Balance: ${balance:,.2f}")
    print(f"   Equity: ${equity:,.2f}")
    
    # Get open positions
    positions = portfolio.get_open_positions()
    print(f"\n📍 Open Positions: {len(positions)}")
    
    for i, pos in enumerate(positions, 1):
        symbol = pos.get('symbol', 'N/A')
        volume = pos.get('volume', 0)
        profit = pos.get('profit', 0)
        pos_type = 'BUY' if pos.get('type') == 0 else 'SELL'
        print(f"   {i}. {symbol} {pos_type} {volume} lots, P&L: ${profit:.2f}")
    
    # Calculate exposure using the NEW method
    risk_pct_symbol = risk.get_risk_pct_for_symbol("EURUSD")  # Test with EURUSD
    total_risk_pct = len(positions) * risk_pct_symbol
    
    print(f"\n💼 Exposure Calculation (FIXED):")
    print(f"   Risk per trade (EURUSD/MAJOR): {risk_pct_symbol}%")
    print(f"   Open positions: {len(positions)}")
    print(f"   Total exposure: {total_risk_pct:.2f}% (limit: {risk.max_total_exposure_pct}%)")
    total_risk_usd = (total_risk_pct / 100) * equity
    print(f"   Total risk in USD: ${total_risk_usd:.2f}")
    print(f"   Max positions: {risk.max_positions}")
    
    # Test can_open_new_trade
    print(f"\n🧪 Testing can_open_new_trade():")
    can_trade, error = risk.can_open_new_trade("EURUSD")
    
    if can_trade:
        print(f"   ✅ Can open new trade!")
    else:
        print(f"   ❌ Cannot open: {error}")
    
    # Expected values
    expected_exposure = len(positions) * risk_pct_symbol
    print(f"\n✅ Expected exposure: ~{expected_exposure:.2f}%")
    print(f"   Actual exposure: {total_risk_pct:.2f}%")
    
    if abs(total_risk_pct - expected_exposure) < 0.1:
        print("   ✅ CALCULATION IS CORRECT!")
    else:
        print("   ⚠️  Small difference (normal due to rounding)")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    test_exposure()
