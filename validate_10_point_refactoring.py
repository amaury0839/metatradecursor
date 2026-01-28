"""
Validation: 10-Point Refactoring
Tests the new modules before integration into main.py
"""

import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("validation_10_point")


def test_imports():
    """Test 1: All new modules import correctly"""
    logger.info("=" * 70)
    logger.info("TEST 1: Module Imports")
    logger.info("=" * 70)
    
    try:
        from app.trading.decision_constants import MIN_EXECUTION_CONFIDENCE, RSI_OVERBOUGHT
        logger.info("✅ decision_constants imported")
        
        from app.trading.signal_execution_split import split_decision, SignalDirection
        logger.info("✅ signal_execution_split imported")
        
        from app.trading.trade_validation import TradeValidationGates, run_validation_gates
        logger.info("✅ trade_validation imported")
        
        from app.trading.ai_optimization import should_call_ai
        logger.info("✅ ai_optimization imported")
        
        logger.info("✅ All imports successful")
        return True
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False


def test_signal_execution_split():
    """Test 2: Signal/Execution separation works"""
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST 2: Signal/Execution Split")
    logger.info("=" * 70)
    
    try:
        from app.trading.signal_execution_split import split_decision
        
        # Case 1: Strong signal, high confidence
        signal, execution = split_decision(
            signal_direction="BUY",
            signal_strength=0.80,
            technical_score=0.80,
            ai_score=0.75,
            sentiment_score=0.3,
            ai_call_made=True,
            ai_action="BUY",
            min_exec_confidence=0.55
        )
        
        assert signal.direction == "BUY"
        assert execution.should_execute == True
        assert execution.execution_confidence >= 0.55
        logger.info("✅ Case 1: Strong signal + high confidence → EXECUTE")
        
        # Case 2: Clear signal, low confidence
        signal, execution = split_decision(
            signal_direction="BUY",
            signal_strength=0.80,
            technical_score=0.40,  # Low technical
            ai_score=0.0,  # AI not called
            sentiment_score=0.0,
            ai_call_made=False,
            ai_action="HOLD",
            min_exec_confidence=0.55
        )
        
        assert signal.direction == "BUY"
        assert execution.should_execute == False
        assert execution.execution_confidence < 0.55
        logger.info("✅ Case 2: BUY signal but low confidence (0.40*0.6) → SKIP")
        
        # Case 3: HOLD signal, no matter what
        signal, execution = split_decision(
            signal_direction="HOLD",
            signal_strength=0.0,
            technical_score=0.0,
            ai_score=0.0,
            sentiment_score=0.0,
            ai_call_made=False,
            ai_action="HOLD",
            min_exec_confidence=0.55
        )
        
        assert signal.direction == "HOLD"
        assert execution.should_execute == False
        logger.info("✅ Case 3: HOLD → never execute")
        
        return True
    except Exception as e:
        logger.error(f"❌ Split decision test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_gates():
    """Test 3: Validation gates work correctly"""
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST 3: Validation Gates")
    logger.info("=" * 70)
    
    try:
        from app.trading.trade_validation import TradeValidationGates
        
        # Test spread gate
        valid, reason = TradeValidationGates.validate_spread("EURUSD", 2.5, is_crypto=False)
        assert valid == True
        logger.info("✅ Spread gate: Normal spread passes")
        
        valid, reason = TradeValidationGates.validate_spread("EURUSD", 10.0, is_crypto=False)
        assert valid == False
        logger.info("✅ Spread gate: High spread blocked")
        
        # Test execution confidence gate
        valid, reason = TradeValidationGates.validate_execution_confidence("EURUSD", 0.60)
        assert valid == True
        logger.info("✅ Confidence gate: 0.60 >= 0.55 passes")
        
        valid, reason = TradeValidationGates.validate_execution_confidence("EURUSD", 0.40)
        assert valid == False
        logger.info("✅ Confidence gate: 0.40 < 0.55 blocked")
        
        # Test RSI block
        valid, reason = TradeValidationGates.validate_rsi_entry_block("EURUSD", "BUY", 50)
        assert valid == True
        logger.info("✅ RSI gate: Neutral RSI for BUY passes")
        
        valid, reason = TradeValidationGates.validate_rsi_entry_block("EURUSD", "BUY", 80)
        assert valid == False
        logger.info("✅ RSI gate: Overbought blocks BUY")
        
        valid, reason = TradeValidationGates.validate_rsi_entry_block("EURUSD", "SELL", 15)
        assert valid == False
        logger.info("✅ RSI gate: Oversold blocks SELL")
        
        # Test stops validation
        valid, reason = TradeValidationGates.validate_stops_with_proper_pricing(
            "EURUSD", "BUY",
            bid_price=1.0950,
            ask_price=1.0955,
            sl_price=1.0940,
            tp_price=1.0970
        )
        assert valid == True
        logger.info("✅ Stops gate: Valid BUY stops (SL < entry < TP)")
        
        valid, reason = TradeValidationGates.validate_stops_with_proper_pricing(
            "EURUSD", "BUY",
            bid_price=1.0950,
            ask_price=1.0955,
            sl_price=1.0960,  # SL above entry - wrong!
            tp_price=1.0970
        )
        assert valid == False
        logger.info("✅ Stops gate: Invalid stops rejected")
        
        # Test lot validation
        valid, reason, lot = TradeValidationGates.validate_lot_size("EURUSD", 0.05, 0.01, 10.0)
        assert valid == True and lot == 0.05
        logger.info("✅ Lot gate: Normal lot passes")
        
        valid, reason, lot = TradeValidationGates.validate_lot_size("EURUSD", 0.005, 0.01, 10.0)
        assert valid == False
        logger.info("✅ Lot gate: Too small lot rejected (not forced to minimum)")
        
        # Test exposure limits
        open_pos = [
            {"symbol": "EURUSD"},
            {"symbol": "GBPUSD"},
        ]
        valid, reason = TradeValidationGates.validate_exposure_limits("AUDUSD", open_pos, max_per_currency=3, max_per_cluster=6)
        assert valid == True
        logger.info("✅ Exposure gate: Below limits passes")
        
        return True
    except Exception as e:
        logger.error(f"❌ Validation gates test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_optimization():
    """Test 4: AI call optimization works"""
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST 4: AI Optimization")
    logger.info("=" * 70)
    
    try:
        from app.trading.ai_optimization import should_call_ai
        
        # Case 1: Strong BUY signal - skip AI
        call_ai, reason = should_call_ai(
            technical_signal="BUY",
            signal_strength=0.80,
            rsi_value=50,
            trend_status="bullish",
            ema_distance=100
        )
        assert call_ai == False
        logger.info("✅ Strong signal + clear trend → skip AI (save latency)")
        
        # Case 2: Weak signal - call AI
        call_ai, reason = should_call_ai(
            technical_signal="BUY",
            signal_strength=0.50,
            rsi_value=50,
            trend_status="neutral",
            ema_distance=5
        )
        assert call_ai == True
        logger.info("✅ Weak signal + ambiguous market → call AI (clarify)")
        
        # Case 3: HOLD signal - call AI
        call_ai, reason = should_call_ai(
            technical_signal="HOLD",
            signal_strength=0.0,
            rsi_value=50,
            trend_status="neutral",
            ema_distance=5
        )
        assert call_ai == True
        logger.info("✅ HOLD signal → call AI (arbitrate)")
        
        # Case 4: RSI extreme - skip AI
        call_ai, reason = should_call_ai(
            technical_signal="BUY",
            signal_strength=0.60,
            rsi_value=80,  # Extreme
            trend_status="bullish",
            ema_distance=10
        )
        assert call_ai == False
        logger.info("✅ RSI extreme → skip AI (too much noise)")
        
        return True
    except Exception as e:
        logger.error(f"❌ AI optimization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_combined_validation_gates():
    """Test 5: Full validation gate pipeline"""
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST 5: Combined Validation Pipeline")
    logger.info("=" * 70)
    
    try:
        from app.trading.trade_validation import run_validation_gates
        
        # Case 1: All gates pass
        valid, reason, lot = run_validation_gates(
            symbol="EURUSD",
            direction="BUY",
            execution_confidence=0.65,
            bid_price=1.0950,
            ask_price=1.0955,
            sl_price=1.0940,
            tp_price=1.0970,
            rsi_value=50,
            spread_pips=3.0,
            computed_lot=0.1,
            broker_min_lot=0.01,
            broker_max_lot=10.0,
            open_positions=[],
            account_balance=10000,
            required_margin=200
        )
        
        assert valid == True
        assert lot == 0.1
        logger.info("✅ All gates pass → execute with lot=0.1")
        
        # Case 2: Spread too high
        valid, reason, lot = run_validation_gates(
            symbol="EURUSD",
            direction="BUY",
            execution_confidence=0.65,
            bid_price=1.0950,
            ask_price=1.0955,
            sl_price=1.0940,
            tp_price=1.0970,
            rsi_value=50,
            spread_pips=10.0,  # Too high!
            computed_lot=0.1,
            broker_min_lot=0.01,
            broker_max_lot=10.0,
            open_positions=[],
            account_balance=10000,
            required_margin=200
        )
        
        assert valid == False
        assert "SPREAD_TOO_HIGH" in reason
        logger.info("✅ Spread gate blocked → skip immediately")
        
        # Case 3: Confidence too low
        valid, reason, lot = run_validation_gates(
            symbol="EURUSD",
            direction="BUY",
            execution_confidence=0.40,  # Too low!
            bid_price=1.0950,
            ask_price=1.0955,
            sl_price=1.0940,
            tp_price=1.0970,
            rsi_value=50,
            spread_pips=3.0,
            computed_lot=0.1,
            broker_min_lot=0.01,
            broker_max_lot=10.0,
            open_positions=[],
            account_balance=10000,
            required_margin=200
        )
        
        assert valid == False
        assert "CONFIDENCE_TOO_LOW" in reason
        logger.info("✅ Confidence gate blocked → skip early")
        
        return True
    except Exception as e:
        logger.error(f"❌ Combined validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    logger.info("")
    logger.info("🧪 TESTING 10-POINT REFACTORING")
    logger.info("")
    
    tests = [
        ("Imports", test_imports),
        ("Signal/Execution Split", test_signal_execution_split),
        ("Validation Gates", test_validation_gates),
        ("AI Optimization", test_ai_optimization),
        ("Combined Pipeline", test_combined_validation_gates),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        logger.info("\n✅ ALL TESTS PASSED - Ready for main.py integration")
        return 0
    else:
        logger.info("\n❌ SOME TESTS FAILED - Fix issues before integration")
        return 1


if __name__ == "__main__":
    sys.exit(main())
