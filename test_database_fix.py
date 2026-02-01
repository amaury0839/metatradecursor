#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script para verificar que el fix de database logging funciona correctamente.
Ejecuta: python test_database_fix.py
"""

import sys
import os
from datetime import datetime, timedelta

# Configure encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import DatabaseManager

def test_database_fix():
    """Test that trades are saved correctly with new field names"""
    
    print("\n" + "="*60)
    print("TEST: Database Field Mapping Fix")
    print("="*60 + "\n")
    
    # Initialize database
    db = DatabaseManager()
    
    # Test trade record with CORRECTED field names
    test_trade = {
        "symbol": "BTCUSD",
        "type": "BUY",                          # ✅ Correct field name (was "action")
        "volume": 0.1,
        "open_price": 45250.50,                 # ✅ Correct field name (was "entry_price")
        "ticket": 999999999,                    # Unique ticket number
        "status": "OPEN",
        "comment": "Test trade for database fix",  # ✅ Correct field name (was "reason")
        "stop_loss": 45000.00,                  # ✅ Correct field name (was "sl_price")
        "take_profit": 45500.00,                # ✅ Correct field name (was "tp_price")
    }
    
    print("Record fields:")
    for key, value in test_trade.items():
        print(f"   {key}: {value}")
    
    print("\nSaving trade to database...")
    try:
        trade_id = db.save_trade(test_trade)
        if trade_id > 0:
            print(f"SUCCESS: Trade saved with ID={trade_id}")
        else:
            print(f"FAILED: save_trade returned {trade_id}")
            return False
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False
    
    print("\nQuerying database for saved trade...")
    try:
        trades = db.get_trades(days=1)
        print(f"Query returned {len(trades)} trades")
        
        if len(trades) == 0:
            print("ERROR: Database returned 0 trades (fix didn't work)")
            return False
        
        # Find our test trade
        test_found = False
        for trade in trades:
            if trade.get('ticket') == 999999999:
                test_found = True
                print(f"\nFOUND TEST TRADE:")
                print(f"   ID: {trade.get('id')}")
                print(f"   Symbol: {trade.get('symbol')}")
                print(f"   Type: {trade.get('type')}")
                print(f"   Volume: {trade.get('volume')}")
                print(f"   Open Price: {trade.get('open_price')}")
                print(f"   Stop Loss: {trade.get('stop_loss')}")
                print(f"   Take Profit: {trade.get('take_profit')}")
                print(f"   Status: {trade.get('status')}")
                break
        
        if not test_found:
            print("ERROR: Test trade not found in results")
            return False
            
    except Exception as e:
        print(f"EXCEPTION during query: {e}")
        return False
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED - Database fix is working!")
    print("="*60 + "\n")
    return True

if __name__ == "__main__":
    success = test_database_fix()
    sys.exit(0 if success else 1)
