#!/usr/bin/env python3
"""
Check why can_open_new_trade is returning False
"""
import sys
sys.path.insert(0, r'c:\Users\Shadow\Downloads\Metatrade')

from app.trading.mt5_client import get_mt5_client
from app.trading.portfolio import PortfolioManager
from app.trading.risk import RiskManager
from app.core.config import get_config
from app.core.logger import setup_logger

logger = setup_logger("risk_diag")

print("\n" + "=" * 80)
print("RISK MANAGER DIAGNOSTIC")
print("=" * 80)

# Initialize
mt5 = get_mt5_client()
portfolio = PortfolioManager()
risk = RiskManager()
config = get_config()

# Check 1: Account Info
print("\n1. ACCOUNT INFO:")
account = mt5.get_account_info()
if account:
    print(f"   Equity: ${account.get('equity', 0):.2f}")
    print(f"   Balance: ${account.get('balance', 0):.2f}")
    print(f"   Margin Free: ${account.get('margin_free', 0):.2f}")

# Check 2: Open Positions
print("\n2. OPEN POSITIONS:")
open_pos = portfolio.get_open_positions()
print(f"   Count: {len(open_pos)}")
for pos in open_pos:
    print(f"     - {pos.get('symbol')}: {pos.get('type')} {pos.get('volume')} lots")

# Check 3: Risk Manager Config
print("\n3. RISK MANAGER CONFIG:")
print(f"   max_positions: {risk.max_positions}")
print(f"   max_total_exposure_pct: {risk.max_total_exposure_pct}%")
print(f"   max_trades_per_currency: {risk.max_trades_per_currency}")

# Check 4: Try can_open_new_trade for crypto
print("\n4. CAN_OPEN_NEW_TRADE TEST:")
test_symbols = ["BTCUSD", "ETHUSD", "BNBUSD", "EURUSD"]
for symbol in test_symbols:
    can_trade, error = risk.can_open_new_trade(symbol)
    if can_trade:
        print(f"   {symbol}: CAN TRADE")
    else:
        print(f"   {symbol}: BLOCKED - {error}")

# Check 5: Exposure calculation
print("\n5. EXPOSURE ANALYSIS:")
if account:
    equity = account.get('equity', 0)
    open_count = len(open_pos)
    
    # Simulate adding one more trade
    if open_pos:
        first_symbol = open_pos[0].get('symbol')
        risk_pct = risk.get_risk_pct_for_symbol(first_symbol)
        total_risk = (open_count + 1) * risk_pct
        print(f"   Current positions: {open_count}")
        print(f"   Risk per position (~{risk_pct}%)")
        print(f"   If add 1 more: {total_risk:.2f}% total risk")
        print(f"   Max allowed: {risk.max_total_exposure_pct}%")
        
        if total_risk >= risk.max_total_exposure_pct:
            print(f"   => HITTING EXPOSURE LIMIT")

print("\n" + "=" * 80)
