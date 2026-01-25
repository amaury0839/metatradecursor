"""Trading strategy: technical indicators and signals"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple
from app.trading.data import get_data_provider
from app.core.logger import setup_logger

logger = setup_logger("strategy")


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


class TradingStrategy:
    """Trading strategy with technical indicators"""
    
    def __init__(self):
        self.data = get_data_provider()
        
        # Strategy parameters
        self.ema_fast_period = 20
        self.ema_slow_period = 50
        self.rsi_period = 14
        self.atr_period = 14
        
        # Signal thresholds
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.rsi_neutral_low = 45
        self.rsi_neutral_high = 55
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators
        
        Args:
            df: DataFrame with OHLC data
        
        Returns:
            DataFrame with added indicator columns
        """
        if df is None or len(df) < self.ema_slow_period:
            return df
        
        df = df.copy()
        
        # EMAs
        df['ema_fast'] = calculate_ema(df['close'], self.ema_fast_period)
        df['ema_slow'] = calculate_ema(df['close'], self.ema_slow_period)
        
        # RSI
        df['rsi'] = calculate_rsi(df['close'], self.rsi_period)
        
        # ATR
        df['atr'] = calculate_atr(df['high'], df['low'], df['close'], self.atr_period)
        
        # Trend bias
        df['trend_bullish'] = df['ema_fast'] > df['ema_slow']
        df['trend_bearish'] = df['ema_fast'] < df['ema_slow']
        
        return df
    
    def get_signal(
        self, 
        symbol: str, 
        timeframe: str, 
        lookback: int = 100
    ) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
        """
        Get trading signal based on technical analysis
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe string
            lookback: Number of candles to analyze
        
        Returns:
            Tuple of (signal, indicators_dict, error_message)
            signal: "BUY", "SELL", or "HOLD"
        """
        # Get data
        df = self.data.get_ohlc_data(symbol, timeframe, lookback)
        if df is None or len(df) < self.ema_slow_period:
            return None, None, "Insufficient data"
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        # Get latest values
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # Extract indicator values
        indicators = {
            'close': float(latest['close']),
            'ema_fast': float(latest['ema_fast']),
            'ema_slow': float(latest['ema_slow']),
            'rsi': float(latest['rsi']),
            'atr': float(latest['atr']),
            'trend_bullish': bool(latest['trend_bullish']),
            'trend_bearish': bool(latest['trend_bearish']),
            'rsi_prev': float(prev['rsi']) if len(df) > 1 else float(latest['rsi']),
        }
        
        # Generate signal
        signal = "HOLD"
        reasons = []
        
        # Long signal conditions
        if latest['trend_bullish']:
            if prev['rsi'] < 50 and latest['rsi'] >= 50:
                signal = "BUY"
                reasons.append("EMA crossover bullish + RSI crossing above 50")
            elif latest['rsi'] > self.rsi_neutral_low and latest['rsi'] < self.rsi_neutral_high:
                # RSI in neutral zone with bullish trend
                signal = "BUY"
                reasons.append("Bullish trend + RSI in neutral zone")
        
        # Short signal conditions
        elif latest['trend_bearish']:
            if prev['rsi'] > 50 and latest['rsi'] <= 50:
                signal = "SELL"
                reasons.append("EMA crossover bearish + RSI crossing below 50")
            elif latest['rsi'] > self.rsi_neutral_low and latest['rsi'] < self.rsi_neutral_high:
                # RSI in neutral zone with bearish trend
                signal = "SELL"
                reasons.append("Bearish trend + RSI in neutral zone")
        
        # Add reasons to indicators
        indicators['signal_reasons'] = reasons
        indicators['signal'] = signal
        
        logger.debug(
            f"Signal for {symbol}: {signal}, "
            f"EMA fast={indicators['ema_fast']:.5f}, "
            f"EMA slow={indicators['ema_slow']:.5f}, "
            f"RSI={indicators['rsi']:.2f}"
        )
        
        return signal, indicators, None
    
    def get_atr_value(self, symbol: str, timeframe: str) -> Optional[float]:
        """Get current ATR value"""
        df = self.data.get_ohlc_data(symbol, timeframe, 100)
        if df is None or len(df) < self.atr_period:
            return None
        
        df = self.calculate_indicators(df)
        latest_atr = df.iloc[-1]['atr']
        return float(latest_atr) if not pd.isna(latest_atr) else None


# Global strategy instance
_strategy: Optional[TradingStrategy] = None


def get_strategy() -> TradingStrategy:
    """Get global strategy instance"""
    global _strategy
    if _strategy is None:
        _strategy = TradingStrategy()
    return _strategy
