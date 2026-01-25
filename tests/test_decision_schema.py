"""Tests for decision schema validation"""

import pytest
from app.ai.schemas import TradingDecision, OrderDetails, ConstraintsUsed


def test_valid_decision():
    """Test valid decision schema"""
    decision = TradingDecision(
        action="BUY",
        confidence=0.75,
        symbol="EURUSD",
        timeframe="M15",
        reason=["Bullish trend", "RSI oversold"],
        risk_ok=True,
        order=OrderDetails(
            type="MARKET",
            volume_lots=0.1,
            sl_price=1.09500,
            tp_price=1.10500
        )
    )
    
    assert decision.action == "BUY"
    assert decision.confidence == 0.75
    assert decision.is_valid_for_execution(min_confidence=0.62)


def test_decision_without_order():
    """Test decision without order for HOLD action"""
    decision = TradingDecision(
        action="HOLD",
        confidence=0.5,
        symbol="EURUSD",
        timeframe="M15",
        reason=["Uncertain market conditions"],
        risk_ok=False
    )
    
    assert decision.action == "HOLD"
    assert decision.order is None
    assert not decision.is_valid_for_execution()


def test_low_confidence_rejection():
    """Test that low confidence decisions are rejected"""
    decision = TradingDecision(
        action="BUY",
        confidence=0.5,  # Below threshold
        symbol="EURUSD",
        timeframe="M15",
        reason=["Weak signal"],
        risk_ok=True,
        order=OrderDetails(
            type="MARKET",
            volume_lots=0.1,
            sl_price=1.09500,
            tp_price=1.10500
        )
    )
    
    assert not decision.is_valid_for_execution(min_confidence=0.62)


def test_risk_ok_false():
    """Test that risk_ok=False rejects execution"""
    decision = TradingDecision(
        action="BUY",
        confidence=0.8,
        symbol="EURUSD",
        timeframe="M15",
        reason=["Strong signal"],
        risk_ok=False,  # Risk check failed
        order=OrderDetails(
            type="MARKET",
            volume_lots=0.1,
            sl_price=1.09500,
            tp_price=1.10500
        )
    )
    
    assert not decision.is_valid_for_execution()


def test_volume_validation():
    """Test volume validation in order details"""
    # Valid volume
    order = OrderDetails(
        type="MARKET",
        volume_lots=0.1,
        sl_price=1.09500,
        tp_price=1.10500
    )
    assert order.volume_lots == 0.1
    
    # Invalid volume (negative)
    with pytest.raises(ValueError):
        OrderDetails(
            type="MARKET",
            volume_lots=-0.1,
            sl_price=1.09500,
            tp_price=1.10500
        )
    
    # Invalid volume (too large)
    with pytest.raises(ValueError):
        OrderDetails(
            type="MARKET",
            volume_lots=200.0,  # Exceeds max
            sl_price=1.09500,
            tp_price=1.10500
        )
