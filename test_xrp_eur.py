"""Test Enhanced AI Decision System con XRPUSD y EURUSD"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.logger import setup_logger
from app.ai.smart_decision_router import make_smart_decision
from app.ai.enhanced_decision_engine import get_enhanced_decision_engine
from app.trading.strategy import get_strategy
from app.news.sentiment import get_sentiment_analyzer

logger = setup_logger("test_xrp_eur")


def test_symbol_complete(symbol: str):
    """Test completo de un símbolo con enhanced AI"""
    print("\n" + "="*70)
    print(f"🔍 ANÁLISIS COMPLETO: {symbol}")
    print("="*70)
    
    strategy = get_strategy()
    sentiment = get_sentiment_analyzer()
    enhanced_engine = get_enhanced_decision_engine()
    
    # 1. Technical Analysis
    print(f"\n📊 [1/4] Technical Analysis...")
    signal_result = strategy.get_signal(symbol, "M15")
    
    if signal_result and signal_result[0]:
        tech_signal, tech_data, tech_reason = signal_result
        technical_data = {
            "signal": tech_signal,
            "data": tech_data,
            "reason": tech_reason
        }
        
        print(f"  ✓ Signal: {tech_signal}")
        print(f"  ✓ Close: {tech_data.get('close', 'N/A')}")
        print(f"  ✓ RSI: {tech_data.get('rsi', 'N/A')}")
        print(f"  ✓ Trend: {'Bullish' if tech_data.get('trend_bullish') else 'Bearish'}")
        print(f"  ✓ Reason: {tech_reason}")
    else:
        print("  ✗ No technical data available")
        return
    
    # 2. Sentiment Analysis
    print(f"\n📰 [2/4] News Sentiment...")
    sentiment_data = sentiment.get_sentiment(symbol, hours_back=24)
    
    if sentiment_data and sentiment_data.get("score") is not None:
        print(f"  ✓ Score: {sentiment_data['score']:.2f}")
        print(f"  ✓ Summary: {sentiment_data.get('summary', 'N/A')}")
        print(f"  ✓ Headlines: {len(sentiment_data.get('headlines', []))} articles")
    else:
        print("  ⚠ No sentiment data available")
        sentiment_data = None
    
    # 3. Web Search (Enhanced)
    print(f"\n🌐 [3/4] Web Intelligence...")
    
    # Test web search
    web_general = enhanced_engine.search_web_info(symbol, 'general')
    web_news = enhanced_engine.search_web_info(symbol, 'news')
    web_technical = enhanced_engine.search_web_info(symbol, 'technical')
    
    print(f"  General Market: {web_general.get('count', 0)} snippets")
    if web_general.get('success') and web_general.get('snippets'):
        print(f"    → {web_general['snippets'][0][:120]}...")
    
    print(f"  Latest News: {web_news.get('count', 0)} snippets")
    if web_news.get('success') and web_news.get('snippets'):
        print(f"    → {web_news['snippets'][0][:120]}...")
    
    print(f"  Technical Web: {web_technical.get('count', 0)} snippets")
    if web_technical.get('success') and web_technical.get('snippets'):
        print(f"    → {web_technical['snippets'][0][:120]}...")
    
    # 4. Enhanced AI Decision
    print(f"\n🤖 [4/4] Enhanced AI Decision...")
    
    # Try enhanced first
    print("\n  → Intentando ENHANCED engine...")
    decision_enhanced = make_smart_decision(
        symbol=symbol,
        timeframe="M15",
        technical_data=technical_data,
        sentiment_data=sentiment_data,
        use_enhanced=True
    )
    
    if decision_enhanced:
        print(f"  ✓ ENHANCED DECISION:")
        print(f"    Action: {decision_enhanced.action}")
        print(f"    Confidence: {decision_enhanced.confidence:.2%}")
        print(f"    Reasoning: {decision_enhanced.reasoning[:200]}...")
        if decision_enhanced.stop_loss:
            print(f"    Stop Loss: {decision_enhanced.stop_loss}")
        if decision_enhanced.take_profit:
            print(f"    Take Profit: {decision_enhanced.take_profit}")
        
        # Validar si sería ejecutada
        if decision_enhanced.confidence >= 0.40 and decision_enhanced.action != "HOLD":
            print(f"\n  ✅ DECISIÓN EJECUTABLE (confidence >= 0.40)")
        else:
            print(f"\n  ⚠ DECISIÓN NO EJECUTABLE (confidence < 0.40 o HOLD)")
    else:
        print("  ✗ Enhanced decision failed")
    
    # Try simple for comparison
    print("\n  → Comparando con SIMPLE engine...")
    decision_simple = make_smart_decision(
        symbol=symbol,
        timeframe="M15",
        technical_data=technical_data,
        sentiment_data=sentiment_data,
        use_enhanced=False
    )
    
    if decision_simple:
        print(f"  ✓ SIMPLE DECISION:")
        print(f"    Action: {decision_simple.action}")
        print(f"    Confidence: {decision_simple.confidence:.2%}")
        print(f"    Reasoning: {decision_simple.reasoning[:150]}...")
    
    # Compare decisions
    if decision_enhanced and decision_simple:
        print(f"\n  📊 COMPARACIÓN:")
        print(f"    Enhanced: {decision_enhanced.action} ({decision_enhanced.confidence:.2%})")
        print(f"    Simple:   {decision_simple.action} ({decision_simple.confidence:.2%})")
        
        if decision_enhanced.action == decision_simple.action:
            print(f"    ✓ AMBOS COINCIDEN en {decision_enhanced.action}")
        else:
            print(f"    ⚠ DIFIEREN: Enhanced={decision_enhanced.action}, Simple={decision_simple.action}")
    
    print("\n" + "="*70)


def main():
    """Test XRPUSD y EURUSD"""
    print("\n" + "="*70)
    print("🚀 TEST ENHANCED AI - XRPUSD vs EURUSD")
    print("="*70)
    print("\nEste test compara:")
    print("  1. Technical indicators (RSI, EMAs, trends)")
    print("  2. News sentiment")
    print("  3. Web search intelligence")
    print("  4. Enhanced AI vs Simple AI decisions")
    
    try:
        # Test XRPUSD
        test_symbol_complete("XRPUSD")
        
        # Wait a bit to avoid rate limiting
        print("\n⏳ Esperando 5 segundos para evitar rate limiting...")
        import time
        time.sleep(5)
        
        # Test EURUSD
        test_symbol_complete("EURUSD")
        
        print("\n" + "="*70)
        print("✅ TEST COMPLETADO")
        print("="*70)
        print("\nRevisa las decisiones arriba para determinar si:")
        print("  - Enhanced AI agrega valor con web search")
        print("  - Confidence levels son adecuados (>= 0.40 para ejecutar)")
        print("  - Decisiones son consistentes y lógicas")
        print("  - Web intelligence complementa análisis técnico")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ TEST FAILED: {e}")


if __name__ == "__main__":
    main()
