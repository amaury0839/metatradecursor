"""Test Enhanced AI con datos mock (sin MT5)"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.logger import setup_logger
from app.ai.smart_decision_router import make_smart_decision
from app.ai.enhanced_decision_engine import get_enhanced_decision_engine

logger = setup_logger("test_mock")


def test_with_mock_data(symbol: str, scenario: str):
    """Test con datos técnicos mockeados"""
    print("\n" + "="*70)
    print(f"🔍 TEST: {symbol} - Escenario: {scenario}")
    print("="*70)
    
    # Mock technical data basado en escenario
    if scenario == "bullish":
        technical_data = {
            "signal": "BUY",
            "data": {
                "close": 1.90 if symbol == "XRPUSD" else 1.085,
                "rsi": 35.0,  # Oversold
                "ema_fast": 1.88 if symbol == "XRPUSD" else 1.083,
                "ema_slow": 1.86 if symbol == "XRPUSD" else 1.081,
                "atr": 0.05 if symbol == "XRPUSD" else 0.0008,
                "trend_bullish": True,
                "trend_bearish": False
            },
            "reason": "RSI oversold + EMAs bullish crossover"
        }
        sentiment_data = {
            "score": 0.3,
            "summary": "Positive market sentiment, institutional buying"
        }
    elif scenario == "bearish":
        technical_data = {
            "signal": "SELL",
            "data": {
                "close": 1.85 if symbol == "XRPUSD" else 1.080,
                "rsi": 75.0,  # Overbought
                "ema_fast": 1.86 if symbol == "XRPUSD" else 1.081,
                "ema_slow": 1.88 if symbol == "XRPUSD" else 1.083,
                "atr": 0.05 if symbol == "XRPUSD" else 0.0008,
                "trend_bullish": False,
                "trend_bearish": True
            },
            "reason": "RSI overbought + EMAs bearish crossover"
        }
        sentiment_data = {
            "score": -0.4,
            "summary": "Negative sentiment, profit taking"
        }
    else:  # neutral
        technical_data = {
            "signal": "HOLD",
            "data": {
                "close": 1.88 if symbol == "XRPUSD" else 1.083,
                "rsi": 50.0,  # Neutral
                "ema_fast": 1.88 if symbol == "XRPUSD" else 1.083,
                "ema_slow": 1.88 if symbol == "XRPUSD" else 1.083,
                "atr": 0.05 if symbol == "XRPUSD" else 0.0008,
                "trend_bullish": False,
                "trend_bearish": False
            },
            "reason": "Sideways movement, no clear trend"
        }
        sentiment_data = {
            "score": 0.0,
            "summary": "Neutral market sentiment"
        }
    
    print(f"\n📊 Mock Technical Data:")
    print(f"  Signal: {technical_data['signal']}")
    print(f"  Close: {technical_data['data']['close']}")
    print(f"  RSI: {technical_data['data']['rsi']}")
    print(f"  Trend: {'Bullish' if technical_data['data']['trend_bullish'] else 'Bearish' if technical_data['data']['trend_bearish'] else 'Neutral'}")
    print(f"  Reason: {technical_data['reason']}")
    
    print(f"\n📰 Mock Sentiment:")
    print(f"  Score: {sentiment_data['score']:.2f}")
    print(f"  Summary: {sentiment_data['summary']}")
    
    # Test web search
    print(f"\n🌐 Web Search Test...")
    enhanced_engine = get_enhanced_decision_engine()
    
    web_result = enhanced_engine.search_web_info(symbol, 'general')
    if web_result.get('success'):
        print(f"  ✓ Found {web_result['count']} snippets")
        if web_result.get('snippets'):
            print(f"  Sample: {web_result['snippets'][0][:150]}...")
    else:
        print(f"  ✗ Web search failed: {web_result.get('error')}")
    
    # Enhanced decision
    print(f"\n🤖 ENHANCED AI Decision...")
    decision_enhanced = make_smart_decision(
        symbol=symbol,
        timeframe="M15",
        technical_data=technical_data,
        sentiment_data=sentiment_data,
        use_enhanced=True
    )
    
    if decision_enhanced:
        print(f"\n  ✅ DECISIÓN ENHANCED:")
        print(f"     Action: {decision_enhanced.action}")
        print(f"     Confidence: {decision_enhanced.confidence:.2%}")
        print(f"     Reasoning:")
        # Print reasoning in chunks
        reasoning_lines = decision_enhanced.reasoning.split('. ')
        for line in reasoning_lines[:3]:  # First 3 sentences
            if line.strip():
                print(f"       - {line.strip()}.")
        
        if decision_enhanced.stop_loss:
            print(f"     Stop Loss: {decision_enhanced.stop_loss}")
        if decision_enhanced.take_profit:
            print(f"     Take Profit: {decision_enhanced.take_profit}")
        
        # Validation
        if decision_enhanced.confidence >= 0.40 and decision_enhanced.action != "HOLD":
            print(f"\n  ✅ ¡DECISIÓN EJECUTABLE! (confidence >= 0.40)")
        elif decision_enhanced.action == "HOLD":
            print(f"\n  ⚠️  Decisión: HOLD (no trade)")
        else:
            print(f"\n  ⚠️  Confidence insuficiente (< 0.40, no ejecutar)")
    else:
        print("  ✗ Enhanced decision failed")
    
    # Simple decision for comparison
    print(f"\n🔧 SIMPLE AI Decision (comparison)...")
    decision_simple = make_smart_decision(
        symbol=symbol,
        timeframe="M15",
        technical_data=technical_data,
        sentiment_data=sentiment_data,
        use_enhanced=False
    )
    
    if decision_simple:
        print(f"  Action: {decision_simple.action}")
        print(f"  Confidence: {decision_simple.confidence:.2%}")
        
        # Compare
        if decision_enhanced and decision_simple:
            print(f"\n  📊 COMPARACIÓN:")
            print(f"     Enhanced: {decision_enhanced.action} ({decision_enhanced.confidence:.1%})")
            print(f"     Simple:   {decision_simple.action} ({decision_simple.confidence:.1%})")
            
            if decision_enhanced.action == decision_simple.action:
                print(f"     ✓ AMBOS COINCIDEN en {decision_enhanced.action}")
            else:
                print(f"     ⚠️ DIFIEREN - Enhanced usa más información web")
    
    print("="*70)


def main():
    """Test diferentes escenarios"""
    print("\n" + "="*70)
    print("🚀 ENHANCED AI TEST - XRPUSD y EURUSD")
    print("   (Usando datos mock - no requiere MT5)")
    print("="*70)
    
    try:
        # XRPUSD Bullish
        test_with_mock_data("XRPUSD", "bullish")
        
        print("\n⏳ Pausa 3s para rate limiting...")
        import time
        time.sleep(3)
        
        # EURUSD Bearish
        test_with_mock_data("EURUSD", "bearish")
        
        print("\n⏳ Pausa 3s para rate limiting...")
        time.sleep(3)
        
        # XRPUSD Neutral
        test_with_mock_data("XRPUSD", "neutral")
        
        print("\n" + "="*70)
        print("✅ TEST COMPLETADO")
        print("="*70)
        print("\n💡 OBSERVACIONES:")
        print("  - Enhanced AI incorpora web search en decisiones")
        print("  - Busca información actual del mercado en internet")
        print("  - Combina technical + sentiment + web intelligence")
        print("  - Threshold de ejecución: confidence >= 0.40")
        print("  - Fallback automático a Simple AI si enhanced falla")
        print("\n📝 PRÓXIMO PASO:")
        print("  Conecta MT5 y reinicia el bot para usar datos reales")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ ERROR: {e}")


if __name__ == "__main__":
    main()
