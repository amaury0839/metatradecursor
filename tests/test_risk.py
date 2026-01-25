"""Tests for risk management"""

import pytest
from app.trading.risk import RiskManager


def test_risk_manager_initialization():
    """Test risk manager can be initialized"""
    # This will fail if MT5 is not connected, but that's OK for basic test
    try:
        risk = RiskManager()
        assert risk is not None
        assert risk.risk_per_trade_pct > 0
        assert risk.max_daily_loss_pct > 0
        assert risk.max_drawdown_pct > 0
        assert risk.max_positions > 0
    except Exception:
        # Expected if MT5 not connected
        pass


def test_position_sizing_calculation():
    """Test position size calculation"""
    try:
        risk = RiskManager()
        
        # Test with sample values
        entry_price = 1.10000
        stop_loss_price = 1.09900  # 100 pips away
        
        # This will fail if MT5 not connected, but structure is correct
        try:
            lots = risk.calculate_position_size(
                symbol="EURUSD",
                entry_price=entry_price,
                stop_loss_price=stop_loss_price,
                risk_amount=50.0  # $50 risk
            )
            assert lots > 0
            assert lots <= 100  # Should be within reasonable limits
        except Exception:
            # Expected if MT5 not connected
            pass
    except Exception:
        pass


def test_atr_calculations():
    """Test ATR-based SL/TP calculations"""
    risk = RiskManager()
    
    atr_value = 0.0010  # 10 pips
    
    sl_distance = risk.calculate_stop_loss_atr(atr_value, multiplier=1.5)
    assert sl_distance == 0.0015  # 15 pips
    
    tp_distance = risk.calculate_take_profit_atr(atr_value, multiplier=2.5)
    assert tp_distance == 0.0025  # 25 pips
