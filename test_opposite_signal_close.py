"""
Test: Verify that Amelia Bot closes positions on opposite signals
regardless of profit/loss status.

Scenario:
- BUY position is OPEN with profit or loss
- Signal changes to SELL with high confidence
- Position should CLOSE (regardless of P&L)

This test verifies the position_manager logic.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def test_opposite_signal_close():
    """Test that opposite signals trigger closes"""
    from app.trading.position_manager import PositionManager
    
    pm = PositionManager()
    
    # Test 1: BUY position + SELL signal → should close
    print("\n✅ TEST 1: BUY position with SELL signal (high confidence)")
    should_close, reason = pm.should_close_on_opposite_signal(
        position_type="BUY",
        current_signal="SELL",
        confidence=0.75,
        min_confidence_to_reverse=0.7
    )
    print(f"  Should close: {should_close} ({reason})")
    assert should_close, "BUY + SELL should trigger close!"
    
    # Test 2: SELL position + BUY signal → should close
    print("\n✅ TEST 2: SELL position with BUY signal (high confidence)")
    should_close, reason = pm.should_close_on_opposite_signal(
        position_type="SELL",
        current_signal="BUY",
        confidence=0.75,
        min_confidence_to_reverse=0.7
    )
    print(f"  Should close: {should_close} ({reason})")
    assert should_close, "SELL + BUY should trigger close!"
    
    # Test 3: Low confidence should NOT close
    print("\n✅ TEST 3: Low confidence signal (should NOT close)")
    should_close, reason = pm.should_close_on_opposite_signal(
        position_type="BUY",
        current_signal="SELL",
        confidence=0.5,  # Below threshold
        min_confidence_to_reverse=0.7
    )
    print(f"  Should close: {should_close} ({reason})")
    assert not should_close, "Low confidence should NOT trigger close!"
    
    # Test 4: HOLD signal should NOT close
    print("\n✅ TEST 4: HOLD signal (should NOT close)")
    should_close, reason = pm.should_close_on_opposite_signal(
        position_type="BUY",
        current_signal="HOLD",
        confidence=0.75,
        min_confidence_to_reverse=0.7
    )
    print(f"  Should close: {should_close} ({reason})")
    assert not should_close, "HOLD signal should NOT trigger close!"
    
    print("\n" + "="*60)
    print("✅ ALL OPPOSITE SIGNAL TESTS PASSED!")
    print("="*60)


def test_review_position_full():
    """Test full position review logic"""
    from app.trading.position_manager import PositionManager
    
    pm = PositionManager()
    
    # Mock position (BUY with some profit)
    position = {
        'symbol': 'EURUSD',
        'ticket': 123456,
        'type': 0,  # BUY
        'price_open': 1.1800,
        'price_current': 1.1820,  # In profit
        'profit': 100.0,  # $100 profit
        'sl': 1.1750,
        'tp': 1.1900,
        'volume': 1.0
    }
    
    # Analysis with opposite signal
    analysis = {
        'signal': 'SELL',
        'confidence': 0.80,
        'rsi': 45,
        'atr': 0.0050
    }
    
    print("\n✅ TEST: Full position review with opposite signal")
    result = pm.review_position_full(
        position=position,
        current_signal='SELL',
        signal_confidence=0.80,
        analysis=analysis,
        max_profit_tracker={123456: 100.0}
    )
    
    print(f"  Should close: {result['should_close']}")
    print(f"  Reason: {result['reason']}")
    
    assert result['should_close'], "Should close on opposite signal!"
    assert "Opposite signal" in result['reason'], "Reason should mention opposite signal!"
    
    print("\n" + "="*60)
    print("✅ FULL POSITION REVIEW TEST PASSED!")
    print("="*60)


def verify_trading_loop_behavior():
    """Check trading_loop.py to confirm it uses the close logic"""
    from pathlib import Path
    
    trading_loop = Path("app/trading/trading_loop.py")
    content = trading_loop.read_text()
    
    print("\n✅ CHECKING trading_loop.py INTEGRATION")
    print("="*60)
    
    checks = [
        ("Uses review_position_full", "review_position_full" in content),
        ("Checks should_close", "should_close" in content),
        ("Closes positions", "close_position" in content),
        ("Logs closing reasons", "CLOSING" in content),
    ]
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            raise AssertionError(f"{check_name} not found in trading_loop.py!")
    
    print("="*60)
    print("✅ TRADING LOOP INTEGRATION VERIFIED!")
    print("="*60)


if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("🤖 AMELIA BOT - OPPOSITE SIGNAL CLOSE VERIFICATION")
        print("="*60)
        
        test_opposite_signal_close()
        test_review_position_full()
        verify_trading_loop_behavior()
        
        print("\n" + "🎉 "*20)
        print("✅ ALL TESTS PASSED - BOT CORRECTLY CLOSES ON OPPOSITE SIGNALS!")
        print("🎉 "*20)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
