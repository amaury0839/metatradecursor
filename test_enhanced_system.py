"""Test script for Enhanced AI Decision System"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.logger import setup_logger
from app.ai.enhanced_decision_engine import get_enhanced_decision_engine
from app.ai.smart_decision_router import make_smart_decision
from app.trading.strategy import get_strategy

logger = setup_logger("test_enhanced")


def test_web_search():
    """Test web search functionality"""
    print("\n" + "="*60)
    print("TEST 1: Web Search")
    print("="*60)
    
    engine = get_enhanced_decision_engine()
    
    symbols = ["EURUSD", "BTCUSD", "ETHUSD"]
    
    for symbol in symbols:
        print(f"\n🔍 Testing web search for {symbol}...")
        
        # General search
        result = engine.search_web_info(symbol, "general")
        if result.get('success'):
            print(f"✓ Found {result['count']} snippets")
            if result.get('snippets'):
                print(f"  First snippet: {result['snippets'][0][:100]}...")
        else:
            print(f"✗ Search failed: {result.get('error')}")


def test_data_aggregation():
    """Test multi-source data aggregation"""
    print("\n" + "="*60)
    print("TEST 2: Data Aggregation")
    print("="*60)
    
    engine = get_enhanced_decision_engine()
    strategy = get_strategy()
    
    symbol = "EURUSD"
    timeframe = "M15"
    
    print(f"\n📊 Aggregating data for {symbol}...")
    
    # Get technical data
    signal_result = strategy.get_signal(symbol, timeframe)
    if signal_result and signal_result[0]:
        tech_signal, tech_data, tech_reason = signal_result
        technical_data = {
            "signal": tech_signal,
            "data": tech_data,
            "reason": tech_reason
        }
        
        # Aggregate all sources
        aggregated = engine.aggregate_data_sources(
            symbol=symbol,
            timeframe=timeframe,
            technical_data=technical_data,
            sentiment_data={"score": 0.1, "summary": "Slightly positive"}
        )
        
        print(f"✓ Aggregated {len(aggregated['sources'])} sources:")
        for source in aggregated['sources']:
            print(f"  - {source}")
        
        # Print web search results
        if 'web_general' in aggregated:
            print(f"\n🌐 Web General: {aggregated['web_general']['count']} snippets")
        if 'web_news' in aggregated:
            print(f"📰 Web News: {aggregated['web_news']['count']} snippets")
        if 'web_technical' in aggregated:
            print(f"📈 Web Technical: {aggregated['web_technical']['count']} snippets")


def test_enhanced_decision():
    """Test enhanced AI decision making"""
    print("\n" + "="*60)
    print("TEST 3: Enhanced AI Decision")
    print("="*60)
    
    engine = get_enhanced_decision_engine()
    strategy = get_strategy()
    
    symbols = ["EURUSD", "BTCUSD"]
    
    for symbol in symbols:
        print(f"\n🤖 Making enhanced decision for {symbol}...")
        
        # Get technical data
        signal_result = strategy.get_signal(symbol, "M15")
        if signal_result and signal_result[0]:
            tech_signal, tech_data, tech_reason = signal_result
            technical_data = {
                "signal": tech_signal,
                "data": tech_data,
                "reason": tech_reason
            }
            
            # Make enhanced decision
            decision = engine.make_enhanced_decision(
                symbol=symbol,
                timeframe="M15",
                technical_data=technical_data,
                sentiment_data={"score": 0.2, "summary": "Positive sentiment"}
            )
            
            if decision:
                print(f"✓ Decision: {decision.action}")
                print(f"  Confidence: {decision.confidence:.2f}")
                print(f"  Reasoning: {decision.reasoning[:150]}...")
            else:
                print("✗ No decision generated")


def test_smart_router():
    """Test smart decision router (enhanced + fallback)"""
    print("\n" + "="*60)
    print("TEST 4: Smart Decision Router")
    print("="*60)
    
    strategy = get_strategy()
    
    symbol = "GBPUSD"
    print(f"\n🔀 Testing smart router for {symbol}...")
    
    # Get technical data
    signal_result = strategy.get_signal(symbol, "M15")
    if signal_result and signal_result[0]:
        tech_signal, tech_data, tech_reason = signal_result
        technical_data = {
            "signal": tech_signal,
            "data": tech_data,
            "reason": tech_reason
        }
        
        # Test with enhanced enabled
        print("\n→ Trying with enhanced engine...")
        decision = make_smart_decision(
            symbol=symbol,
            timeframe="M15",
            technical_data=technical_data,
            sentiment_data={"score": -0.1, "summary": "Slightly negative"},
            use_enhanced=True
        )
        
        if decision:
            print(f"✓ Got decision: {decision.action} (confidence={decision.confidence:.2f})")
        else:
            print("✗ No decision")
        
        # Test with enhanced disabled (simple only)
        print("\n→ Trying with simple engine only...")
        decision_simple = make_smart_decision(
            symbol=symbol,
            timeframe="M15",
            technical_data=technical_data,
            sentiment_data={"score": -0.1, "summary": "Slightly negative"},
            use_enhanced=False
        )
        
        if decision_simple:
            print(f"✓ Got decision: {decision_simple.action} (confidence={decision_simple.confidence:.2f})")
        else:
            print("✗ No decision")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ENHANCED AI SYSTEM - TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: Web search
        test_web_search()
        
        # Test 2: Data aggregation
        test_data_aggregation()
        
        # Test 3: Enhanced decision
        test_enhanced_decision()
        
        # Test 4: Smart router
        test_smart_router()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ TEST FAILED: {e}")


if __name__ == "__main__":
    main()
