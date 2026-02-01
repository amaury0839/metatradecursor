#!/usr/bin/env python3
"""
Validate symbols and build optimal trading symbol list for MT5
Filters out symbols that don't exist or aren't tradeable
"""
import MetaTrader5 as mt5
import json
import sys

def validate_symbols():
    """Validate all symbols against MT5 account"""
    
    # Initialize MT5
    print("🔌 Connecting to MT5...")
    if not mt5.initialize(
        path="C:\\Program Files\\MetaTrader 5\\terminal64.exe",
        login=52704771,
        password="Leonis1122",
        server="ICMarkets-Demo"
    ):
        print("❌ Failed to initialize MT5")
        print(f"   Error: {mt5.last_error()}")
        return
    
    print("✅ MT5 connected\n")
    
    # Candidate symbols to test
    candidates = {
        'FOREX': [
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
            "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDSGD", "CADCHF", "CADJPY",
            "CHFJPY", "CHFSGD", "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY",
            "EURNOK", "EURNZD", "EURPLN", "EURSEK", "EURSGD", "GBPAUD", "GBPCAD",
            "GBPCHF", "GBPJPY", "GBPSGD", "NZDCAD", "NZDCHF", "NZDJPY", "USDHKD",
            "USDMXN", "USDSGD", "USDTRY", "USDZAR",
        ],
        'INDICES': [
            "US500", "US100", "NAS100", "UK100", "GER40", "FRA40", "AUS200", "HK50",
            "SGX", "NIFTYCOIN",
        ],
        'COMMODITIES': [
            "GOLD", "SILVER", "COPPER",
            "CRUDE", "NATGAS", "BRENT",
            "CORN", "WHEAT", "SUGAR", "COCOA", "COFFEE",
        ],
        'FUTURES': [
            "ES", "NQ", "YM", "MES", "MNQ", "MYM",
            "CL", "NG", "BRENT",
            "GC", "SI", "HG",
            "ZC", "ZS", "ZW",
        ],
        'CRYPTO': [
            "BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "XRPUSD", "ADAUSD", "DOTUSD", 
            "LTCUSD", "UNIUSD", "XLMUSD", "DOGEUSD", "AVAXUSD", "POLKAUSD",
            "LINKUSD", "MATICUSD", "ATOMUSD", "VETUSD", "FILUSD", "ARBUSD", "OPUSD", "GMXUSD",
        ],
        'STOCKS': [
            "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "TSLA", "META", "ADBE", 
            "INTC", "AMD", "JPM", "GS", "BAC", "WFC", "USB", "NFLX", "DIS", "PARA",
            "JNJ", "UNH", "PFE", "LLY", "XOM", "CVX", "COP",
        ],
    }
    
    # Validate each symbol
    valid = {}
    invalid = {}
    
    for category, symbols in candidates.items():
        print(f"🔍 Validating {category}...")
        valid[category] = []
        invalid[category] = []
        
        for symbol in symbols:
            try:
                # Get symbol info
                info = mt5.symbol_info(symbol)
                
                if info is None:
                    invalid[category].append(symbol)
                elif info.trade_mode == mt5.SYMBOL_TRADE_MODE_DISABLED:
                    invalid[category].append(symbol)
                else:
                    valid[category].append(symbol)
                    print(f"   ✅ {symbol}")
            except Exception as e:
                invalid[category].append(symbol)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 VALIDATION SUMMARY")
    print("=" * 80)
    
    total_valid = 0
    total_invalid = 0
    
    for category in sorted(valid.keys()):
        v = valid[category]
        i = invalid[category]
        total_valid += len(v)
        total_invalid += len(i)
        
        print(f"\n{category}:")
        print(f"  ✅ Valid: {len(v)}")
        if v:
            print(f"     {', '.join(v[:10])}")
            if len(v) > 10:
                print(f"     ... and {len(v) - 10} more")
        print(f"  ❌ Invalid: {len(i)}")
        if i:
            print(f"     {', '.join(i[:5])}")
            if len(i) > 5:
                print(f"     ... and {len(i) - 5} more")
    
    print(f"\n{'=' * 80}")
    print(f"TOTAL: {total_valid} valid | {total_invalid} invalid")
    
    # Save results
    results = {
        'valid': valid,
        'invalid': invalid,
        'total_valid': total_valid,
        'total_invalid': total_invalid,
        'all_valid_symbols': sorted([s for v in valid.values() for s in v])
    }
    
    with open('validated_symbols.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to validated_symbols.json")
    
    # Generate config update
    print("\n" + "=" * 80)
    print("📝 RECOMMENDED CONFIG UPDATE")
    print("=" * 80)
    
    all_valid = results['all_valid_symbols']
    print(f"\nTotal tradeable symbols: {len(all_valid)}")
    print(f"\nAdd to config.py default_symbols: {len(all_valid)} symbols")
    
    mt5.shutdown()

if __name__ == "__main__":
    validate_symbols()
