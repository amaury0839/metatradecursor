"""Tests for strategy signal generation"""

import pandas as pd
import numpy as np
from app.trading.strategy import TradingStrategy, calculate_ema, calculate_rsi, calculate_atr


def test_ema_calculation():
    """Test EMA calculation"""
    data = pd.Series([1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9])
    ema = calculate_ema(data, period=5)
    
    assert len(ema) == len(data)
    assert not pd.isna(ema.iloc[-1])  # Last value should be calculated
    assert ema.iloc[-1] > 0


def test_rsi_calculation():
    """Test RSI calculation"""
    # Create sample price data with trend
    prices = pd.Series([100, 101, 102, 103, 104, 105, 104, 103, 102, 101])
    rsi = calculate_rsi(prices, period=5)
    
    assert len(rsi) == len(prices)
    # RSI should be between 0 and 100
    assert 0 <= rsi.iloc[-1] <= 100


def test_atr_calculation():
    """Test ATR calculation"""
    high = pd.Series([1.10, 1.11, 1.12, 1.13, 1.14])
    low = pd.Series([1.09, 1.10, 1.11, 1.12, 1.13])
    close = pd.Series([1.095, 1.105, 1.115, 1.125, 1.135])
    
    atr = calculate_atr(high, low, close, period=3)
    
    assert len(atr) == len(close)
    assert atr.iloc[-1] > 0


def test_strategy_indicators():
    """Test strategy indicator calculation"""
    strategy = TradingStrategy()
    
    # Create sample OHLC data
    dates = pd.date_range('2024-01-01', periods=100, freq='15min')
    df = pd.DataFrame({
        'open': np.random.uniform(1.10, 1.11, 100),
        'high': np.random.uniform(1.11, 1.12, 100),
        'low': np.random.uniform(1.09, 1.10, 100),
        'close': np.random.uniform(1.10, 1.11, 100),
        'volume': 1000
    }, index=dates)
    
    # Calculate indicators
    df_with_indicators = strategy.calculate_indicators(df)
    
    assert 'ema_fast' in df_with_indicators.columns
    assert 'ema_slow' in df_with_indicators.columns
    assert 'rsi' in df_with_indicators.columns
    assert 'atr' in df_with_indicators.columns
    assert 'trend_bullish' in df_with_indicators.columns
    assert 'trend_bearish' in df_with_indicators.columns
