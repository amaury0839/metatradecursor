#!/usr/bin/env python3
"""
Check if UI is getting real data from the API
"""
import sys
import requests
import json

sys.path.insert(0, r'c:\Users\Shadow\Downloads\Metatrade')

print("\n" + "=" * 80)
print("UI/API DATA STATUS DIAGNOSTIC")
print("=" * 80)

# Check API endpoints
api_endpoints = [
    ("Account Info", "http://localhost:8002/api/account"),
    ("Positions", "http://localhost:8002/api/positions"),
    ("Symbols Status", "http://localhost:8002/api/symbols/status"),
    ("Crypto Status", "http://localhost:8002/api/symbols/crypto"),
    ("Market Status", "http://localhost:8002/api/market/status"),
]

print("\n1. API ENDPOINT STATUS:")
for name, url in api_endpoints:
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            # Check if data is default/empty
            if isinstance(data, dict) and len(data) > 0:
                # Show first few keys
                keys = list(data.keys())[:3]
                print(f"   {name}: OK - has data")
                if 'balance' in data or 'account' in data:
                    print(f"     └─ Sample: {json.dumps({k: data[k] for k in keys if k in data}, indent=6)}")
            else:
                print(f"   {name}: WARNING - empty data")
        else:
            print(f"   {name}: ERROR {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"   {name}: NOT RUNNING - API server not responding")
    except Exception as e:
        print(f"   {name}: ERROR - {type(e).__name__}")

# Check UI health
print("\n2. STREAMLIT UI STATUS:")
ui_url = "http://localhost:8504"
try:
    response = requests.get(ui_url, timeout=3)
    if response.status_code == 200:
        print(f"   Streamlit UI: RUNNING at {ui_url}")
    else:
        print(f"   Streamlit UI: ERROR {response.status_code}")
except requests.exceptions.ConnectionError:
    print(f"   Streamlit UI: NOT RUNNING at {ui_url}")
except Exception as e:
    print(f"   Streamlit UI: ERROR - {type(e).__name__}")

# Check bot status
print("\n3. BOT TRADING LOOP STATUS:")
from app.core.database import get_database_manager

try:
    db = get_database_manager()
    
    # Get last trade
    trades = db.get_trades(limit=1)
    if trades:
        last_trade = trades[0]
        print(f"   Last trade recorded: {last_trade.get('symbol')} - {last_trade.get('action')} at {last_trade.get('timestamp')}")
        print(f"   Status: Bot IS trading")
    else:
        print(f"   No trades recorded: Bot may not have run yet")
        
    # Get trade history count
    all_trades = db.get_trades(limit=100)
    print(f"   Total trades in database: {len(all_trades)}")
    
except Exception as e:
    print(f"   ERROR accessing database: {e}")

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("=" * 80)
print("""
If API is NOT RUNNING:
  → Start API with: python app/api/server.py
  
If Streamlit UI is NOT RUNNING:
  → Start UI with: streamlit run app/main_ui.py --server.port 8504
  
If API is running but showing default data:
  → Check API code for hardcoded defaults
  → Verify MT5 client initialization in API
  
If UI is running but showing default data:
  → Refresh the UI (Ctrl+Shift+R or reload page)
  → Check browser console for errors
  → Verify API is responding with real data
""")
