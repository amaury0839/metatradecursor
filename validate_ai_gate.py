"""
Validación de AI Gate - Regla de Oro
Tests para verificar que solo se consulta IA en zona gris
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.logger import setup_logger
from app.ai.ai_gate import get_ai_gate

logger = setup_logger("validate_ai_gate")


def test_strong_signal_skips_ai():
    """Test: Señales fuertes NO necesitan IA"""
    logger.info("=" * 60)
    logger.info("TEST 1: Señales Fuertes → Skip IA")
    logger.info("=" * 60)
    
    gate = get_ai_gate()
    
    # STRONG_BUY debe skipear
    needs_ai, reason = gate.needs_ai(
        tech_signal="STRONG_BUY",
        indicators={"rsi": 70, "ema_fast": 100, "ema_slow": 98, "close": 100}
    )
    assert not needs_ai, "STRONG_BUY debe skipear IA"
    logger.info(f"✅ STRONG_BUY → Skip: {reason}")
    
    # STRONG_SELL debe skipear
    needs_ai, reason = gate.needs_ai(
        tech_signal="STRONG_SELL",
        indicators={"rsi": 25, "ema_fast": 100, "ema_slow": 102, "close": 100}
    )
    assert not needs_ai, "STRONG_SELL debe skipear IA"
    logger.info(f"✅ STRONG_SELL → Skip: {reason}")
    
    logger.info("✅ Test señales fuertes passed!")
    return True


def test_high_confidence_skips_ai():
    """Test: Confianza técnica alta NO necesita IA"""
    logger.info("=" * 60)
    logger.info("TEST 2: Confianza Alta → Skip IA")
    logger.info("=" * 60)
    
    gate = get_ai_gate()
    
    # Confianza 0.80 debe skipear
    needs_ai, reason = gate.needs_ai(
        tech_signal="BUY",
        indicators={"rsi": 60, "close": 100},
        confidence=0.80
    )
    assert not needs_ai, "Confianza 0.80 debe skipear IA"
    logger.info(f"✅ Confidence 0.80 → Skip: {reason}")
    
    # Confianza 0.60 con RSI gris debe necesitar IA
    needs_ai, reason = gate.needs_ai(
        tech_signal="BUY",
        indicators={"rsi": 50, "close": 100},
        confidence=0.60
    )
    assert needs_ai, "Confianza 0.60 con RSI gris debe necesitar IA"
    logger.info(f"✅ Confidence 0.60 + RSI 50 → Needs AI: {reason}")
    
    logger.info("✅ Test confianza passed!")
    return True


def test_rsi_gray_zone_needs_ai():
    """Test: RSI 45-55 necesita IA"""
    logger.info("=" * 60)
    logger.info("TEST 3: RSI Zona Gris → Needs IA")
    logger.info("=" * 60)
    
    gate = get_ai_gate()
    
    # RSI 50 debe necesitar IA
    needs_ai, reason = gate.needs_ai(
        tech_signal="BUY",
        indicators={"rsi": 50, "close": 100}
    )
    assert needs_ai, "RSI 50 debe necesitar IA"
    logger.info(f"✅ RSI 50 → Needs AI: {reason}")
    
    # RSI 45 debe necesitar IA
    needs_ai, reason = gate.needs_ai(
        tech_signal="SELL",
        indicators={"rsi": 45, "close": 100}
    )
    assert needs_ai, "RSI 45 debe necesitar IA"
    logger.info(f"✅ RSI 45 → Needs AI: {reason}")
    
    # RSI 70 NO debe necesitar IA
    needs_ai, reason = gate.needs_ai(
        tech_signal="BUY",
        indicators={"rsi": 70, "close": 100}
    )
    assert not needs_ai, "RSI 70 NO debe necesitar IA"
    logger.info(f"✅ RSI 70 → Skip: {reason}")
    
    logger.info("✅ Test RSI zona gris passed!")
    return True


def test_ema_convergence_needs_ai():
    """Test: EMAs convergiendo necesita IA"""
    logger.info("=" * 60)
    logger.info("TEST 4: EMAs Convergiendo → Needs IA")
    logger.info("=" * 60)
    
    gate = get_ai_gate()
    
    # EMAs casi iguales (diff < 0.05%) debe necesitar IA
    needs_ai, reason = gate.needs_ai(
        tech_signal="BUY",
        indicators={
            "rsi": 60,
            "ema_fast": 1.0000,
            "ema_slow": 1.0004,  # diff = 0.04%
            "close": 1.0000
        }
    )
    assert needs_ai, "EMAs convergiendo debe necesitar IA"
    logger.info(f"✅ EMAs diff 0.04% → Needs AI: {reason}")
    
    # EMAs separadas NO debe necesitar IA
    needs_ai, reason = gate.needs_ai(
        tech_signal="BUY",
        indicators={
            "rsi": 60,
            "ema_fast": 1.00,
            "ema_slow": 0.99,  # diff = 1%
            "close": 1.00
        }
    )
    assert not needs_ai, "EMAs separadas NO debe necesitar IA"
    logger.info(f"✅ EMAs diff 1% → Skip: {reason}")
    
    logger.info("✅ Test EMA convergencia passed!")
    return True


def test_conflicting_indicators_needs_ai():
    """Test: Indicadores en conflicto necesita IA"""
    logger.info("=" * 60)
    logger.info("TEST 5: Conflicto Indicadores → Needs IA")
    logger.info("=" * 60)
    
    gate = get_ai_gate()
    
    # MACD bullish + RSI bearish = conflicto
    needs_ai, reason = gate.needs_ai(
        tech_signal="BUY",
        indicators={
            "rsi": 65,
            "macd_signal": "bullish",
            "rsi_signal": "bearish",
            "ema_trend": "bullish",
            "close": 100
        }
    )
    assert needs_ai, "Indicadores conflictivos debe necesitar IA"
    logger.info(f"✅ Conflicto MACD/RSI → Needs AI: {reason}")
    
    # Indicadores alineados NO necesita IA
    needs_ai, reason = gate.needs_ai(
        tech_signal="BUY",
        indicators={
            "rsi": 65,
            "macd_signal": "bullish",
            "rsi_signal": "bullish",
            "ema_trend": "bullish",
            "close": 100
        }
    )
    assert not needs_ai, "Indicadores alineados NO debe necesitar IA"
    logger.info(f"✅ Indicadores alineados → Skip: {reason}")
    
    logger.info("✅ Test conflicto indicadores passed!")
    return True


def test_stats_tracking():
    """Test: Estadísticas de ahorro"""
    logger.info("=" * 60)
    logger.info("TEST 6: Tracking de Estadísticas")
    logger.info("=" * 60)
    
    gate = get_ai_gate()
    
    # Get stats
    stats = gate.get_stats()
    logger.info(f"📊 Stats: {stats['calls_saved']} saved, {stats['calls_made']} made")
    
    assert stats["calls_saved"] > 0, "Debe haber llamadas ahorradas"
    assert stats["total"] > 0, "Debe haber total de llamadas"
    assert 0 <= stats["savings_pct"] <= 100, "Porcentaje debe estar entre 0-100"
    
    logger.info(f"✅ Savings: {stats['savings_pct']:.1f}%")
    logger.info("✅ Test estadísticas passed!")
    return True


def main():
    """Run all validation tests"""
    logger.info("")
    logger.info("🚀 VALIDATING AI GATE - REGLA DE ORO")
    logger.info("")
    
    tests = [
        ("Señales Fuertes Skip", test_strong_signal_skips_ai),
        ("Confianza Alta Skip", test_high_confidence_skips_ai),
        ("RSI Zona Gris", test_rsi_gray_zone_needs_ai),
        ("EMA Convergencia", test_ema_convergence_needs_ai),
        ("Conflicto Indicadores", test_conflicting_indicators_needs_ai),
        ("Stats Tracking", test_stats_tracking),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                logger.info("")
        except Exception as e:
            failed += 1
            logger.error(f"❌ {test_name} FAILED: {e}")
            logger.info("")
    
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Passed: {passed}/{len(tests)}")
    logger.info(f"❌ Failed: {failed}/{len(tests)}")
    
    # Log final stats
    gate = get_ai_gate()
    gate.log_stats()
    
    if failed == 0:
        logger.info("")
        logger.info("🎉 ALL TESTS PASSED! AI Gate ready for production.")
        logger.info("📊 Estimated savings: 50-70% of AI calls")
        logger.info("")
        return 0
    else:
        logger.error("")
        logger.error("⚠️  SOME TESTS FAILED! Review errors above.")
        logger.error("")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
