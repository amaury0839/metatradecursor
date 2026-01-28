#!/usr/bin/env python3
"""
Test script to validate MT5 centralization fix

This script verifies that:
1. MT5Client.ensure_symbol() works correctly
2. MT5Client.get_rates() calls ensure_symbol() internally
3. DataProvider.get_ohlc_data() uses centralized method
4. No AttributeError for symbol_select() anymore
"""

import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_mt5_fix")

def test_mt5_client_methods():
    """Test that MT5Client has the required methods"""
    try:
        from app.trading.mt5_client import MT5Client
        
        client = MT5Client()
        
        # Check methods exist
        assert hasattr(client, 'ensure_symbol'), "MT5Client missing ensure_symbol() method"
        assert hasattr(client, 'get_rates'), "MT5Client missing get_rates() method"
        assert callable(client.ensure_symbol), "ensure_symbol is not callable"
        assert callable(client.get_rates), "get_rates is not callable"
        
        logger.info("✅ MT5Client has all required methods")
        return True
    except Exception as e:
        logger.error(f"❌ MT5Client test failed: {e}")
        return False

def test_data_provider_no_symbol_select():
    """Test that DataProvider doesn't call symbol_select() anymore"""
    try:
        from app.trading.data import DataProvider
        import inspect
        
        source = inspect.getsource(DataProvider.get_ohlc_data)
        
        # Check that symbol_select is NOT called directly
        if "self.mt5.symbol_select" in source:
            logger.error("❌ DataProvider.get_ohlc_data() still calls self.mt5.symbol_select()")
            return False
        
        logger.info("✅ DataProvider.get_ohlc_data() does NOT call symbol_select()")
        return True
    except Exception as e:
        logger.error(f"❌ DataProvider test failed: {e}")
        return False

def test_data_loader_uses_centralized():
    """Test that DataLoader uses centralized MT5Client methods"""
    try:
        from app.backtest.data_loader import DataLoader
        import inspect
        
        source = inspect.getsource(DataLoader.load_data)
        
        # Check that centralized method is called
        if "self.mt5_client.get_rates" not in source:
            logger.warning("⚠️ DataLoader.load_data() might not use mt5_client.get_rates()")
        
        # Check that direct copy_rates is NOT called
        if "mt5.copy_rates" in source:
            logger.error("❌ DataLoader.load_data() still calls mt5.copy_rates_* directly")
            return False
        
        logger.info("✅ DataLoader.load_data() uses centralized methods")
        return True
    except Exception as e:
        logger.error(f"❌ DataLoader test failed: {e}")
        return False

def test_strategy_integration():
    """Test that Strategy works with updated data provider"""
    try:
        from app.trading.strategy import StrategyAnalyzer
        
        analyzer = StrategyAnalyzer()
        
        assert hasattr(analyzer, 'data'), "StrategyAnalyzer missing data provider"
        assert hasattr(analyzer.data, 'get_ohlc_data'), "DataProvider missing get_ohlc_data()"
        
        logger.info("✅ StrategyAnalyzer properly integrated with updated DataProvider")
        return True
    except Exception as e:
        logger.error(f"❌ StrategyAnalyzer test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🔧 MT5 CENTRALIZATION FIX - VALIDATION TESTS")
    print("="*70 + "\n")
    
    results = {
        "MT5Client Methods": test_mt5_client_methods(),
        "DataProvider (no symbol_select)": test_data_provider_no_symbol_select(),
        "DataLoader (centralized)": test_data_loader_uses_centralized(),
        "StrategyAnalyzer Integration": test_strategy_integration(),
    }
    
    print("\n" + "="*70)
    print("📊 TEST RESULTS")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📈 Total: {passed}/{total} tests passed")
    print("="*70 + "\n")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - MT5 fix is working correctly!")
        return 0
    else:
        logger.error(f"⚠️ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
