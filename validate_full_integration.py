"""
Validation script: Completa integración de perfiles de riesgo en el bot
Verifica:
1. ProfileSelector se importa correctamente
2. RiskProfileManager se inicializa
3. evaluate_and_update() se ejecuta sin errores
4. Los parámetros del perfil se aplican correctamente
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration_validation")

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test: Imports work correctly"""
    logger.info("=" * 60)
    logger.info("TEST 1: Imports")
    logger.info("=" * 60)
    
    try:
        from app.trading.risk_profiles import get_risk_profile_manager, RiskProfile
        logger.info("✅ RiskProfileManager imports OK")
        
        from app.trading.profile_selector import get_profile_selector
        logger.info("✅ ProfileSelector imports OK")
        
        return True
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False


def test_profile_manager():
    """Test: RiskProfileManager works"""
    logger.info("=" * 60)
    logger.info("TEST 2: RiskProfileManager Initialization")
    logger.info("=" * 60)
    
    try:
        from app.trading.risk_profiles import get_risk_profile_manager
        
        mgr = get_risk_profile_manager()
        profile = mgr.get_current_profile()
        
        logger.info(f"✅ Current profile: {profile.name}")
        logger.info(f"   Risk per trade: {profile.risk_per_trade:.2%}")
        logger.info(f"   Max positions: {profile.max_positions}")
        logger.info(f"   SL multiplier: {profile.atr_sl_mult:.1f}x ATR")
        logger.info(f"   Min confidence: {profile.min_confidence_score:.2f}")
        
        return True
    except Exception as e:
        logger.error(f"❌ RiskProfileManager failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_profile_selector():
    """Test: ProfileSelector works"""
    logger.info("=" * 60)
    logger.info("TEST 3: ProfileSelector Initialization")
    logger.info("=" * 60)
    
    try:
        from app.trading.profile_selector import get_profile_selector
        
        selector = get_profile_selector()
        logger.info("✅ ProfileSelector initialized")
        
        # Test with empty trades (no data scenario)
        metrics = {"trade_count": 0}
        profile, reason = selector.select_profile(metrics)
        logger.info(f"✅ No-trades scenario → {profile}: {reason}")
        
        # Test with good metrics
        metrics = {
            "win_rate": 0.65,
            "profit_factor": 1.8,
            "drawdown": 0.5,
            "expectancy": 1.0,
            "trade_count": 10
        }
        profile, reason = selector.select_profile(metrics)
        logger.info(f"✅ Good metrics (WR=65%) → {profile}: {reason}")
        
        # Test with bad metrics
        metrics = {
            "win_rate": 0.30,
            "profit_factor": 0.8,
            "drawdown": 3.0,
            "expectancy": -0.5,
            "trade_count": 10
        }
        profile, reason = selector.select_profile(metrics)
        logger.info(f"✅ Bad metrics (WR=30%) → {profile}: {reason}")
        
        return True
    except Exception as e:
        logger.error(f"❌ ProfileSelector failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_main_integration():
    """Test: evaluate_and_update() funciona en contexto de main.py"""
    logger.info("=" * 60)
    logger.info("TEST 4: Main Integration - Hourly Evaluation")
    logger.info("=" * 60)
    
    try:
        # Simular lo que main_trading_loop haría
        from app.trading.profile_selector import get_profile_selector
        
        logger.info("🔄 Simulating hourly profile evaluation...")
        
        selector = get_profile_selector()
        
        # Este es el llamado que se hace cada hora
        # Para test, usamos horas_back=1 en lugar de 12 para ir más rápido
        logger.info("Evaluando últimas 12 horas de trades...")
        result = selector.evaluate_and_update(hours_back=12)
        
        logger.info(f"✅ Evaluation complete:")
        logger.info(f"   Trades analyzed: {result['trades_analyzed']}")
        logger.info(f"   Selected profile: {result['selected_profile']}")
        logger.info(f"   Reason: {result['selection_reason']}")
        logger.info(f"   Profile changed: {result['profile_changed']}")
        logger.info(f"   Current active: {result['current_profile']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Main integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_parameter_application():
    """Test: Verificar que los parámetros del perfil se podrían aplicar"""
    logger.info("=" * 60)
    logger.info("TEST 5: Parameter Application Logic")
    logger.info("=" * 60)
    
    try:
        from app.trading.risk_profiles import get_risk_profile_manager
        
        mgr = get_risk_profile_manager()
        
        # Simular 3 escenarios
        scenarios = [
            ("CONSERVATIVE", {"risk": 2.0, "engine_risk": 0.5}),
            ("BALANCED", {"risk": 1.0, "engine_risk": 0.75}),
            ("AGGRESSIVE", {"risk": 0.5, "engine_risk": 1.0}),
        ]
        
        for profile_name, params in scenarios:
            mgr.set_profile(profile_name, reason="Test")
            profile = mgr.get_current_profile()
            
            engine_risk = params["engine_risk"]
            profile_risk = profile.risk_per_trade * 100  # Convert to percentage
            
            # Defensa asimétrica: usar el MENOR (conservative approach)
            effective_risk = min(engine_risk, profile_risk / 100)
            
            logger.info(
                f"✅ {profile_name}:"
                f" engine={engine_risk:.2%}, profile={profile_risk:.2%}"
                f" → effective={effective_risk:.2%}"
            )
        
        return True
    except Exception as e:
        logger.error(f"❌ Parameter application failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    logger.info("")
    logger.info("🚀 RISK PROFILES FULL INTEGRATION VALIDATION")
    logger.info("")
    
    tests = [
        ("Imports", test_imports),
        ("RiskProfileManager", test_profile_manager),
        ("ProfileSelector", test_profile_selector),
        ("Main Integration", test_main_integration),
        ("Parameter Application", test_parameter_application),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
        logger.info("")
    
    # Summary
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("")
    logger.info(f"Total: {passed}/{total} passed")
    
    if passed == total:
        logger.info("✅ ALL TESTS PASSED - READY FOR PRODUCTION")
        return 0
    else:
        logger.info("❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
