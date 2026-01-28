"""
🟢 TEST SUITE - AI POSITION MANAGEMENT
Tests for 3 key AI rules:
1. EXIT GOVERNOR: AI evaluates exits for open positions
2. TIME FILTER: AI detects momentum dead zones
3. RISK CUTTER: AI controls risk exposure
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))

from app.trading.ai_position_management import (
    evaluate_position_for_exit,
    evaluate_entry_pause,
    adjust_risk_for_ai_confidence,
    should_tighten_stops,
    PositionContext,
    AIPositionSignal,
)
from app.core.logger import setup_logger

logger = setup_logger("test_ai_position_management")


def test_exit_governor():
    """Test Rule 1: AI EXIT GOVERNOR"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: EXIT GOVERNOR - AI evaluates exits for open positions")
    logger.info("="*80)
    
    tests_passed = 0
    
    # Test 1.1: Negative trade + AI HOLD + weak technical = CLOSE
    logger.info("\nTest 1.1: Losing trade + AI HOLD + weak technical")
    position = PositionContext(
        symbol="EURUSD",
        direction="BUY",
        entry_price=1.2000,
        current_price=1.1950,
        pnl=-50.00,
        pnl_percent=-0.42,
        lot_size=0.01,
        open_bars=5,
        is_negative=True,
        is_stagnant=False,
        signal_direction="HOLD",
        signal_strength=0.45,  # Weak
        trading_mode="SCALPING"
    )
    
    decision = evaluate_position_for_exit(
        position=position,
        ai_decision="HOLD",
        ai_confidence=0.50
    )
    
    if decision.signal == AIPositionSignal.CLOSE_POSITION:
        logger.info("  ✅ PASS: Correctly returned CLOSE_POSITION")
        tests_passed += 1
    else:
        logger.error(f"  ❌ FAIL: Expected CLOSE_POSITION, got {decision.signal}")
    
    # Test 1.2: Stagnant trade + AI HOLD + weak technical = REDUCE
    logger.info("\nTest 1.2: Stagnant trade + AI HOLD + weak technical")
    position = PositionContext(
        symbol="GBPUSD",
        direction="SELL",
        entry_price=1.3500,
        current_price=1.3498,
        pnl=2.00,
        pnl_percent=0.015,
        lot_size=0.01,
        open_bars=15,
        is_negative=False,
        is_stagnant=True,  # No movement
        signal_direction="HOLD",
        signal_strength=0.50,
        trading_mode="SCALPING"
    )
    
    decision = evaluate_position_for_exit(
        position=position,
        ai_decision="HOLD",
        ai_confidence=0.52
    )
    
    if decision.signal == AIPositionSignal.REDUCE_POSITION:
        logger.info("  ✅ PASS: Correctly returned REDUCE_POSITION")
        tests_passed += 1
    else:
        logger.error(f"  ❌ FAIL: Expected REDUCE_POSITION, got {decision.signal}")
    
    # Test 1.3: Opposite signal = CLOSE if negative
    logger.info("\nTest 1.3: Opposite signal (BUY position, AI says SELL) + negative")
    position = PositionContext(
        symbol="BTCUSD",
        direction="BUY",
        entry_price=45000.00,
        current_price=44500.00,
        pnl=-500.00,
        pnl_percent=-1.11,
        lot_size=0.01,
        open_bars=3,
        is_negative=True,
        is_stagnant=False,
        signal_direction="SELL",
        signal_strength=0.80,
        trading_mode="SCALPING"
    )
    
    decision = evaluate_position_for_exit(
        position=position,
        ai_decision="SELL",
        ai_confidence=0.75
    )
    
    if decision.signal == AIPositionSignal.CLOSE_POSITION:
        logger.info("  ✅ PASS: Correctly returned CLOSE_POSITION")
        tests_passed += 1
    else:
        logger.error(f"  ❌ FAIL: Expected CLOSE_POSITION, got {decision.signal}")
    
    # Test 1.4: All good = MAINTAIN
    logger.info("\nTest 1.4: Positive trade, AI BUY = MAINTAIN")
    position = PositionContext(
        symbol="ETHUSD",
        direction="BUY",
        entry_price=3000.00,
        current_price=3050.00,
        pnl=50.00,
        pnl_percent=1.67,
        lot_size=0.10,
        open_bars=2,
        is_negative=False,
        is_stagnant=False,
        signal_direction="BUY",
        signal_strength=0.75,
        trading_mode="SCALPING"
    )
    
    decision = evaluate_position_for_exit(
        position=position,
        ai_decision="BUY",
        ai_confidence=0.80
    )
    
    if decision.signal == AIPositionSignal.MAINTAIN_POSITION:
        logger.info("  ✅ PASS: Correctly returned MAINTAIN_POSITION")
        tests_passed += 1
    else:
        logger.error(f"  ❌ FAIL: Expected MAINTAIN_POSITION, got {decision.signal}")
    
    logger.info(f"\n  EXIT GOVERNOR RESULT: {tests_passed}/4 tests passed")
    return tests_passed, 4


def test_time_filter():
    """Test Rule 2: AI TIME FILTER"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: TIME FILTER - AI detects momentum dead zones")
    logger.info("="*80)
    
    tests_passed = 0
    
    # Test 2.1: 1 HOLD = no pause
    logger.info("\nTest 2.1: 1 consecutive HOLD = no entry pause")
    should_pause, reason = evaluate_entry_pause(
        symbol="EURUSD",
        hold_streak_count=1,
        consecutive_hold_threshold=3
    )
    
    if not should_pause:
        logger.info("  ✅ PASS: No pause with only 1 HOLD")
        tests_passed += 1
    else:
        logger.error("  ❌ FAIL: Should not pause with only 1 HOLD")
    
    # Test 2.2: 3 HOLD = pause
    logger.info("\nTest 2.2: 3 consecutive HOLD = entry pause")
    should_pause, reason = evaluate_entry_pause(
        symbol="EURUSD",
        hold_streak_count=3,
        consecutive_hold_threshold=3
    )
    
    if should_pause:
        logger.info(f"  ✅ PASS: Pause triggered with 3 HOLD ({reason})")
        tests_passed += 1
    else:
        logger.error("  ❌ FAIL: Should pause with 3 HOLD")
    
    # Test 2.3: 5 HOLD = pause
    logger.info("\nTest 2.3: 5 consecutive HOLD = entry pause")
    should_pause, reason = evaluate_entry_pause(
        symbol="EURUSD",
        hold_streak_count=5,
        consecutive_hold_threshold=3
    )
    
    if should_pause:
        logger.info(f"  ✅ PASS: Pause triggered with 5 HOLD ({reason})")
        tests_passed += 1
    else:
        logger.error("  ❌ FAIL: Should pause with 5 HOLD")
    
    logger.info(f"\n  TIME FILTER RESULT: {tests_passed}/3 tests passed")
    return tests_passed, 3


def test_risk_cutter():
    """Test Rule 3: AI RISK CUTTER"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: RISK CUTTER - AI controls risk exposure")
    logger.info("="*80)
    
    tests_passed = 0
    
    # Test 3.1: High confidence = normal risk
    logger.info("\nTest 3.1: High AI confidence (0.80) = normal risk")
    result = adjust_risk_for_ai_confidence(
        base_risk_percent=1.0,
        ai_confidence=0.80
    )
    
    if (result["adjusted_risk_percent"] == 1.0 and 
        result["risk_multiplier"] == 1.0 and
        result["decision"] == "NORMAL"):
        logger.info("  ✅ PASS: Risk kept at 100%")
        tests_passed += 1
    else:
        logger.error(f"  ❌ FAIL: Expected normal risk, got {result}")
    
    # Test 3.2: Medium confidence = reduced risk
    logger.info("\nTest 3.2: Medium AI confidence (0.65) = 50% risk")
    result = adjust_risk_for_ai_confidence(
        base_risk_percent=1.0,
        ai_confidence=0.65
    )
    
    if (result["adjusted_risk_percent"] == 0.5 and 
        result["risk_multiplier"] == 0.5 and
        result["decision"] == "REDUCE"):
        logger.info("  ✅ PASS: Risk reduced to 50%")
        tests_passed += 1
    else:
        logger.error(f"  ❌ FAIL: Expected 50% risk, got {result}")
    
    # Test 3.3: Low confidence = blocked risk
    logger.info("\nTest 3.3: Low AI confidence (0.50) = 0% risk (BLOCKED)")
    result = adjust_risk_for_ai_confidence(
        base_risk_percent=1.0,
        ai_confidence=0.50,
        min_confidence_threshold=0.55
    )
    
    if (result["adjusted_risk_percent"] == 0.0 and 
        result["risk_multiplier"] == 0.0 and
        result["decision"] == "BLOCK"):
        logger.info("  ✅ PASS: Risk blocked at 0%")
        tests_passed += 1
    else:
        logger.error(f"  ❌ FAIL: Expected 0% risk, got {result}")
    
    # Test 3.4: Edge case: at threshold = reduced risk (defensive)
    logger.info("\nTest 3.4: Edge case (0.55) = reduced risk (defensive)")
    result = adjust_risk_for_ai_confidence(
        base_risk_percent=1.0,
        ai_confidence=0.55,
        min_confidence_threshold=0.55
    )
    
    # At threshold, system is conservative: reduce to 50% (safe)
    if result["adjusted_risk_percent"] == 0.5:
        logger.info("  ✅ PASS: At threshold = reduced risk (conservative)")
        tests_passed += 1
    else:
        logger.error(f"  ❌ FAIL: Expected 50%, got {result}")
    
    logger.info(f"\n  RISK CUTTER RESULT: {tests_passed}/4 tests passed")
    return tests_passed, 4


def test_stop_tightening():
    """Test: Stop tightening logic"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: BONUS - Stop tightening based on AI signals")
    logger.info("="*80)
    
    tests_passed = 0
    
    # Test 4.1: AI HOLD = tighten stops
    logger.info("\nTest 4.1: AI says HOLD = tighten stops")
    should_tighten, stop_offset = should_tighten_stops(
        ai_decision="HOLD",
        ai_confidence=0.60,
        position_age_bars=5,
        pnl_percent=0.5
    )
    
    if should_tighten and stop_offset is not None:
        logger.info(f"  ✅ PASS: Stops tightened to {stop_offset:.1f}%")
        tests_passed += 1
    else:
        logger.error("  ❌ FAIL: Should tighten stops on HOLD")
    
    # Test 4.2: Old position + low confidence = tighten
    logger.info("\nTest 4.2: Old position (20 bars) + low AI confidence = tighten")
    should_tighten, stop_offset = should_tighten_stops(
        ai_decision="BUY",
        ai_confidence=0.60,
        position_age_bars=20,
        pnl_percent=0.5
    )
    
    if should_tighten and stop_offset is not None:
        logger.info(f"  ✅ PASS: Stops tightened to {stop_offset:.1f}%")
        tests_passed += 1
    else:
        logger.error("  ❌ FAIL: Should tighten old position stops")
    
    logger.info(f"\n  STOP TIGHTENING RESULT: {tests_passed}/2 tests passed")
    return tests_passed, 2


def main():
    """Run all tests"""
    logger.info("\n")
    logger.info("🟢" * 40)
    logger.info("🟢 AI POSITION MANAGEMENT TEST SUITE 🟢")
    logger.info("🟢" * 40)
    
    total_passed = 0
    total_tests = 0
    
    # Test each rule
    passed, total = test_exit_governor()
    total_passed += passed
    total_tests += total
    
    passed, total = test_time_filter()
    total_passed += passed
    total_tests += total
    
    passed, total = test_risk_cutter()
    total_passed += passed
    total_tests += total
    
    passed, total = test_stop_tightening()
    total_passed += passed
    total_tests += total
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("FINAL RESULTS")
    logger.info("="*80)
    logger.info(f"✅ PASSED: {total_passed}/{total_tests} tests")
    
    if total_passed == total_tests:
        logger.info("\n🎉 SUCCESS: All AI position management rules validated!")
        logger.info("   → EXIT GOVERNOR: ACTIVE")
        logger.info("   → TIME FILTER: ACTIVE")
        logger.info("   → RISK CUTTER: ACTIVE")
    else:
        logger.error(f"\n❌ FAILED: {total_tests - total_passed} tests failed")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
