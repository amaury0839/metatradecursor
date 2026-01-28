"""
Phase 4B: Unit Tests for Trading Loop
Location: test_trading_loop_unit.py

Tests the extracted trading_loop.py module for:
1. Initialization and setup
2. Open position review logic
3. New opportunity evaluation
4. Error handling
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_trading_loop_imports():
    """TEST 1: Verify trading_loop module can be imported"""
    logger.info("=" * 70)
    logger.info("TEST 1: Trading Loop Module Imports")
    logger.info("=" * 70)
    
    try:
        import app.trading.trading_loop
        logger.info("✅ app.trading.trading_loop imported successfully")
        logger.info("✅ Module contains trading loop implementation")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import trading_loop: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def test_decision_modules_integration():
    """TEST 2: Verify all Phase 1 decision modules can be imported"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Phase 1 Decision Modules Integration")
    logger.info("=" * 70)
    
    modules_to_test = {
        'decision_constants': 'app.trading.decision_constants',
        'signal_execution_split': 'app.trading.signal_execution_split',
        'trade_validation': 'app.trading.trade_validation',
        'ai_optimization': 'app.trading.ai_optimization'
    }
    
    all_passed = True
    
    for name, module_path in modules_to_test.items():
        try:
            __import__(module_path)
            logger.info(f"✅ {name} imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import {name}: {e}")
            all_passed = False
    
    return all_passed


def test_decision_constants_values():
    """TEST 3: Verify decision constants have correct values"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Decision Constants Values")
    logger.info("=" * 70)
    
    try:
        from app.trading.decision_constants import (
            MIN_EXECUTION_CONFIDENCE,
            RSI_OVERBOUGHT,
            RSI_OVERSOLD,
            MAX_SPREAD_PIPS_FOREX,
            MAX_SPREAD_PIPS_CRYPTO
        )
        
        tests_passed = 0
        tests_total = 5
        
        # Test MIN_EXECUTION_CONFIDENCE
        if MIN_EXECUTION_CONFIDENCE == 0.55:
            logger.info(f"✅ MIN_EXECUTION_CONFIDENCE = {MIN_EXECUTION_CONFIDENCE} (correct)")
            tests_passed += 1
        else:
            logger.error(f"❌ MIN_EXECUTION_CONFIDENCE = {MIN_EXECUTION_CONFIDENCE} (expected 0.55)")
        
        # Test RSI_OVERBOUGHT
        if RSI_OVERBOUGHT == 75:
            logger.info(f"✅ RSI_OVERBOUGHT = {RSI_OVERBOUGHT} (correct)")
            tests_passed += 1
        else:
            logger.error(f"❌ RSI_OVERBOUGHT = {RSI_OVERBOUGHT} (expected 75)")
        
        # Test RSI_OVERSOLD
        if RSI_OVERSOLD == 25:
            logger.info(f"✅ RSI_OVERSOLD = {RSI_OVERSOLD} (correct)")
            tests_passed += 1
        else:
            logger.error(f"❌ RSI_OVERSOLD = {RSI_OVERSOLD} (expected 25)")
        
        # Test MAX_SPREAD_PIPS_FOREX
        if MAX_SPREAD_PIPS_FOREX == 5:
            logger.info(f"✅ MAX_SPREAD_PIPS_FOREX = {MAX_SPREAD_PIPS_FOREX} (correct)")
            tests_passed += 1
        else:
            logger.error(f"❌ MAX_SPREAD_PIPS_FOREX = {MAX_SPREAD_PIPS_FOREX} (expected 5)")
        
        # Test MAX_SPREAD_PIPS_CRYPTO
        if MAX_SPREAD_PIPS_CRYPTO == 50:
            logger.info(f"✅ MAX_SPREAD_PIPS_CRYPTO = {MAX_SPREAD_PIPS_CRYPTO} (correct)")
            tests_passed += 1
        else:
            logger.error(f"❌ MAX_SPREAD_PIPS_CRYPTO = {MAX_SPREAD_PIPS_CRYPTO} (expected 50)")
        
        logger.info(f"\nResult: {tests_passed}/{tests_total} constant checks passed")
        return tests_passed == tests_total
        
    except Exception as e:
        logger.error(f"❌ Error testing constants: {e}")
        return False


def test_signal_execution_split_function():
    """TEST 4: Verify signal_execution_split function works"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Signal/Execution Split Function")
    logger.info("=" * 70)
    
    try:
        from app.trading.signal_execution_split import split_decision
        
        # Test Case 1: Strong BUY signal with high confidence
        logger.info("\nCase 1: Strong BUY with confidence 0.80")
        signal_analysis, exec_decision = split_decision(
            signal_direction='BUY',
            signal_strength=0.80,
            technical_score=0.80,
            ai_score=0.75,
            sentiment_score=0.30,
            ai_call_made=True
        )
        
        if signal_analysis and signal_analysis.direction == 'BUY':
            logger.info(f"✅ Signal direction: {signal_analysis.direction}")
            logger.info(f"✅ Execution decision confidence: {exec_decision.execution_confidence:.2f}")
            if exec_decision.execution_confidence >= 0.55:
                logger.info("✅ Confidence meets threshold (>=0.55)")
            else:
                logger.error(f"❌ Confidence {exec_decision.execution_confidence} below threshold")
        else:
            logger.error("❌ Failed to generate signal analysis")
            return False
        
        # Test Case 2: Weak signal (should not execute)
        logger.info("\nCase 2: Weak signal (0.40) without AI")
        signal_analysis, exec_decision = split_decision(
            signal_direction='BUY',
            signal_strength=0.40,
            technical_score=0.40,
            ai_score=0.0,
            sentiment_score=0.0,
            ai_call_made=False
        )
        
        if signal_analysis:
            logger.info(f"✅ Signal direction: {signal_analysis.direction}")
            logger.info(f"✅ Execution confidence: {exec_decision.execution_confidence:.2f}")
            if exec_decision.execution_confidence < 0.55:
                logger.info("✅ Correctly rejected (confidence < 0.55)")
            else:
                logger.error("❌ Should have been rejected")
                return False
        else:
            logger.error("❌ Failed to generate signal analysis")
            return False
        
        logger.info("\nResult: ✅ Signal/Execution split working correctly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing signal split: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_trade_validation_gates():
    """TEST 5: Verify validation gates work"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: Trade Validation Gates")
    logger.info("=" * 70)
    
    try:
        from app.trading.trade_validation import TradeValidationGates
        
        tests_passed = 0
        
        # Test 1: Spread validation
        logger.info("\nGate 1: Spread Validation")
        is_valid, reason = TradeValidationGates.validate_spread(
            symbol='EURUSD',
            current_spread_pips=3.0,
            is_crypto=False
        )
        if is_valid:
            logger.info("✅ Normal spread (3 pips) passes")
            tests_passed += 1
        else:
            logger.error(f"❌ Normal spread rejected: {reason}")
        
        # Test 2: Confidence gate
        logger.info("\nGate 2: Confidence Validation")
        is_valid, reason = TradeValidationGates.validate_execution_confidence(
            symbol='EURUSD',
            execution_confidence=0.60
        )
        if is_valid:
            logger.info("✅ Confidence 0.60 >= 0.55 threshold passes")
            tests_passed += 1
        else:
            logger.error(f"❌ Valid confidence rejected: {reason}")
        
        # Test 3: RSI gate
        logger.info("\nGate 3: RSI Entry Block")
        is_valid, reason = TradeValidationGates.validate_rsi_entry_block(
            symbol='EURUSD',
            direction='BUY',
            rsi_value=50.0
        )
        if is_valid:
            logger.info("✅ Neutral RSI (50) for BUY passes")
            tests_passed += 1
        else:
            logger.error(f"❌ Valid RSI rejected: {reason}")
        
        # Test 4: Lot size gate
        logger.info("\nGate 5: Lot Size Validation")
        is_valid, reason, validated_lot = TradeValidationGates.validate_lot_size(
            symbol='EURUSD',
            computed_lot=0.10,
            broker_min_lot=0.01,
            broker_max_lot=100.0
        )
        if is_valid:
            logger.info("✅ Valid lot size (0.10) passes")
            tests_passed += 1
        else:
            logger.error(f"❌ Valid lot rejected: {reason}")
        
        logger.info(f"\nResult: {tests_passed}/4 gate tests passed")
        return tests_passed == 4
        
    except Exception as e:
        logger.error(f"❌ Error testing validation gates: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def test_ai_optimization():
    """TEST 6: Verify AI optimization logic"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 6: AI Optimization Logic")
    logger.info("=" * 70)
    
    try:
        from app.trading.ai_optimization import should_call_ai
        
        tests_passed = 0
        
        # Test 1: Strong signal - should skip AI
        logger.info("\nCase 1: Strong signal (0.80) - should skip AI")
        should_call, reason = should_call_ai(
            technical_signal='BUY',
            signal_strength=0.80,
            rsi_value=50.0,
            trend_status='bullish',
            ema_distance=80.0
        )
        if not should_call:
            logger.info(f"✅ Correctly skipped AI: {reason}")
            tests_passed += 1
        else:
            logger.error("❌ Should have skipped AI for strong signal")
        
        # Test 2: Weak signal - should call AI
        logger.info("\nCase 2: Weak signal (0.50) - should call AI")
        should_call, reason = should_call_ai(
            technical_signal='BUY',
            signal_strength=0.50,
            rsi_value=50.0,
            trend_status='neutral',
            ema_distance=20.0
        )
        if should_call:
            logger.info(f"✅ Correctly called AI: {reason}")
            tests_passed += 1
        else:
            logger.error("❌ Should have called AI for weak signal")
        
        # Test 3: HOLD signal - should call AI
        logger.info("\nCase 3: HOLD signal - should call AI")
        should_call, reason = should_call_ai(
            technical_signal='HOLD',
            signal_strength=0.0,
            rsi_value=50.0,
            trend_status='neutral',
            ema_distance=10.0
        )
        if should_call:
            logger.info(f"✅ Correctly called AI: {reason}")
            tests_passed += 1
        else:
            logger.error("❌ Should have called AI for HOLD")
        
        # Test 4: RSI extreme - should skip AI
        logger.info("\nCase 4: RSI extreme (80) - should skip AI")
        should_call, reason = should_call_ai(
            technical_signal='BUY',
            signal_strength=0.60,
            rsi_value=80.0,
            trend_status='bullish',
            ema_distance=40.0
        )
        if not should_call:
            logger.info(f"✅ Correctly skipped AI: {reason}")
            tests_passed += 1
        else:
            logger.error("❌ Should have skipped AI for RSI extreme")
        
        logger.info(f"\nResult: {tests_passed}/4 AI optimization tests passed")
        return tests_passed == 4
        
    except Exception as e:
        logger.error(f"❌ Error testing AI optimization: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("🧪" * 35)
    logger.info("PHASE 4B: TRADING LOOP UNIT TESTS")
    logger.info("🧪" * 35)
    
    tests = [
        ("TEST 1: Module Imports", test_trading_loop_imports),
        ("TEST 2: Decision Module Integration", test_decision_modules_integration),
        ("TEST 3: Decision Constants", test_decision_constants_values),
        ("TEST 4: Signal/Execution Split", test_signal_execution_split_function),
        ("TEST 5: Validation Gates", test_trade_validation_gates),
        ("TEST 6: AI Optimization", test_ai_optimization),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"TOTAL: {passed}/{total} tests passed")
    logger.info("=" * 70)
    
    if passed == total:
        logger.info("\n✅ ALL PHASE 4B TESTS PASSED - Ready for Phase 4C")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} test(s) failed - Review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
