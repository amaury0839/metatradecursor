"""
Validación de Risk Profiles Architecture
Tests para verificar perfiles, selector y reglas
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.logger import setup_logger
from app.trading.risk_profiles import get_risk_profile_manager
from app.trading.profile_selector import get_profile_selector

logger = setup_logger("validate_risk_profiles")


def test_profiles_exist():
    """Test: Todos los perfiles están definidos"""
    logger.info("=" * 60)
    logger.info("TEST 1: Perfiles Definidos")
    logger.info("=" * 60)
    
    manager = get_risk_profile_manager()
    
    expected_profiles = ["CONSERVATIVE", "BALANCED", "AGGRESSIVE"]
    
    for profile_name in expected_profiles:
        profile = manager.get_profile(profile_name)
        assert profile is not None, f"Profile {profile_name} not found"
        logger.info(f"✅ {profile}")
    
    logger.info("✅ All profiles defined!")
    return True


def test_profile_hierarchy():
    """Test: Perfiles siguen jerarquía de riesgo"""
    logger.info("=" * 60)
    logger.info("TEST 2: Jerarquía de Riesgo")
    logger.info("=" * 60)
    
    manager = get_risk_profile_manager()
    
    conservative = manager.get_profile("CONSERVATIVE")
    balanced = manager.get_profile("BALANCED")
    aggressive = manager.get_profile("AGGRESSIVE")
    
    # Risk per trade debe aumentar
    assert conservative.risk_per_trade < balanced.risk_per_trade, "Risk debe aumentar"
    assert balanced.risk_per_trade < aggressive.risk_per_trade, "Risk debe aumentar"
    logger.info(f"✅ Risk hierarchy: {conservative.risk_per_trade}% < {balanced.risk_per_trade}% < {aggressive.risk_per_trade}%")
    
    # Max positions debe aumentar
    assert conservative.max_positions < balanced.max_positions, "Max positions debe aumentar"
    assert balanced.max_positions < aggressive.max_positions, "Max positions debe aumentar"
    logger.info(f"✅ Positions hierarchy: {conservative.max_positions} < {balanced.max_positions} < {aggressive.max_positions}")
    
    # SL multiplier debe disminuir (más agresivo = SL apretado)
    assert conservative.atr_sl_mult > balanced.atr_sl_mult, "SL multiplier debe disminuir"
    assert balanced.atr_sl_mult > aggressive.atr_sl_mult, "SL multiplier debe disminuir"
    logger.info(f"✅ SL hierarchy: {conservative.atr_sl_mult}x > {balanced.atr_sl_mult}x > {aggressive.atr_sl_mult}x")
    
    logger.info("✅ Hierarchy correct!")
    return True


def test_stability_rules():
    """Test: Reglas de estabilidad funcionan"""
    logger.info("=" * 60)
    logger.info("TEST 3: Reglas de Estabilidad")
    logger.info("=" * 60)
    
    manager = get_risk_profile_manager()
    
    # Primer cambio debe permitirse
    can_change, reason = manager.validate_profile_change()
    assert can_change, "Primer cambio debe permitirse"
    logger.info(f"✅ First change allowed: {reason}")
    
    # Después de cambiar, debe respetar 3 horas
    success, msg = manager.set_profile("CONSERVATIVE", reason="Test")
    assert success, "Cambio inicial debe ser exitoso"
    logger.info(f"✅ Changed to CONSERVATIVE: {msg}")
    
    # Intento inmediato debe fallar
    can_change, reason = manager.validate_profile_change()
    assert not can_change, "No debe permitir cambio inmediato"
    logger.info(f"✅ Immediate change blocked: {reason}")
    
    logger.info("✅ Stability rules working!")
    return True


def test_metrics_calculation():
    """Test: Cálculo de métricas"""
    logger.info("=" * 60)
    logger.info("TEST 4: Cálculo de Métricas")
    logger.info("=" * 60)
    
    selector = get_profile_selector()
    
    # Mock trades
    mock_trades = [
        {"profit": 100, "entry_price": 1.0, "stop_loss": 0.99},  # Win
        {"profit": 100, "entry_price": 1.0, "stop_loss": 0.99},  # Win
        {"profit": -50, "entry_price": 1.0, "stop_loss": 0.99},  # Loss
    ]
    
    metrics = selector.calculate_metrics(mock_trades)
    
    assert metrics["trade_count"] == 3, "Debe contar 3 trades"
    assert metrics["win_rate"] == 2/3, f"WR debe ser 66%, es {metrics['win_rate']:.1%}"
    logger.info(f"✅ Win rate: {metrics['win_rate']:.1%}")
    
    # Profit factor
    total_profit = 200
    total_loss = 50
    expected_pf = total_profit / total_loss  # 4.0
    assert abs(metrics["profit_factor"] - expected_pf) < 0.1, "PF debe ser ~4.0"
    logger.info(f"✅ Profit factor: {metrics['profit_factor']:.2f}")
    
    logger.info("✅ Metrics calculated correctly!")
    return True


def test_profile_selection_logic():
    """Test: Lógica de selección de perfil"""
    logger.info("=" * 60)
    logger.info("TEST 5: Lógica de Selección")
    logger.info("=" * 60)
    
    selector = get_profile_selector()
    
    # Test CONSERVATIVE (low WR)
    metrics_bad = {
        "win_rate": 0.35,  # < 40%
        "profit_factor": 1.0,
        "drawdown": 3.0,
        "expectancy": -0.5
    }
    profile, reason = selector.select_profile(metrics_bad)
    assert profile == "CONSERVATIVE", f"Debe seleccionar CONSERVATIVE, seleccionó {profile}"
    logger.info(f"✅ Low WR → CONSERVATIVE: {reason}")
    
    # Test AGGRESSIVE (high WR)
    metrics_good = {
        "win_rate": 0.60,   # > 55%
        "profit_factor": 1.5,  # > 1.4
        "drawdown": 0.8,    # < 1.0
        "expectancy": 1.2
    }
    profile, reason = selector.select_profile(metrics_good)
    assert profile == "AGGRESSIVE", f"Debe seleccionar AGGRESSIVE, seleccionó {profile}"
    logger.info(f"✅ High WR + PF → AGGRESSIVE: {reason}")
    
    # Test BALANCED (intermedio)
    metrics_mid = {
        "win_rate": 0.50,
        "profit_factor": 1.2,
        "drawdown": 1.5,
        "expectancy": 0.2
    }
    profile, reason = selector.select_profile(metrics_mid)
    assert profile == "BALANCED", f"Debe seleccionar BALANCED, seleccionó {profile}"
    logger.info(f"✅ Medium metrics → BALANCED: {reason}")
    
    logger.info("✅ Selection logic correct!")
    return True


def test_no_trades_handling():
    """Test: Manejo de falta de trades"""
    logger.info("=" * 60)
    logger.info("TEST 6: Manejo de No Trades")
    logger.info("=" * 60)
    
    selector = get_profile_selector()
    
    # Métricas con 0 trades
    metrics = selector.calculate_metrics([])
    
    assert metrics["trade_count"] == 0, "Debe reportar 0 trades"
    assert metrics["win_rate"] == 0.5, "Default WR debe ser 0.5"
    assert metrics["profit_factor"] == 1.0, "Default PF debe ser 1.0"
    logger.info(f"✅ Default metrics: WR=50%, PF=1.0")
    
    # Seleccionar con 0 trades = BALANCED
    profile, reason = selector.select_profile(metrics)
    assert profile == "BALANCED", "Sin trades debe ser BALANCED"
    logger.info(f"✅ No trades → BALANCED: {reason}")
    
    logger.info("✅ No-trades handling correct!")
    return True


def main():
    """Run all validation tests"""
    logger.info("")
    logger.info("🚀 VALIDATING RISK PROFILES ARCHITECTURE")
    logger.info("")
    
    tests = [
        ("Perfiles Definidos", test_profiles_exist),
        ("Jerarquía de Riesgo", test_profile_hierarchy),
        ("Reglas de Estabilidad", test_stability_rules),
        ("Cálculo de Métricas", test_metrics_calculation),
        ("Lógica de Selección", test_profile_selection_logic),
        ("Manejo No Trades", test_no_trades_handling),
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
            import traceback
            traceback.print_exc()
            logger.info("")
    
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"✅ Passed: {passed}/{len(tests)}")
    logger.info(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        logger.info("")
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ Architecture is robust and ready for production")
        logger.info("")
        return 0
    else:
        logger.error("")
        logger.error("⚠️  SOME TESTS FAILED!")
        logger.error("")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
