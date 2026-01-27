"""Backtest-compatible strategy wrapper"""

import pandas as pd
from typing import Dict, Optional
from app.trading.strategy import TradingStrategy
from app.core.logger import setup_logger

logger = setup_logger("backtest_strategy")


class BacktestStrategy:
    """
    Wrapper around TradingStrategy for backtest compatibility
    Allows passing historical data directly instead of fetching from MT5
    """
    
    def __init__(self, strategy: TradingStrategy):
        """
        Initialize with a TradingStrategy instance
        
        Args:
            strategy: TradingStrategy to wrap
        """
        self.strategy = strategy
        self.profiles = strategy.profiles
    
    def analyze(self, symbol: str, timeframe: str, ohlc_data: pd.DataFrame) -> Dict:
        """
        Analyze historical data and generate trading signal
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe string  
            ohlc_data: DataFrame with columns [time, open, high, low, close, volume]
        
        Returns:
            Dict with 'signal', 'indicators', 'reasons'
        """
        if ohlc_data is None or len(ohlc_data) < 50:
            return {
                'signal': 'HOLD',
                'indicators': {},
                'reasons': ['Insufficient data']
            }
        
        try:
            # Calculate indicators
            df = ohlc_data.copy()
            
            # Select strategy profile
            profile = self.strategy._select_profile(timeframe, df)
            
            # Calculate indicators with profile
            df = self.strategy._calc_indicators_with_profile(df, profile)
            
            if df is None or len(df) == 0:
                return {
                    'signal': 'HOLD',
                    'indicators': {},
                    'reasons': ['Indicator calculation failed']
                }
            
            # Get latest values
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            # Extract indicators
            indicators = {
                'close': float(latest['close']),
                'ema_fast': float(latest['ema_fast']),
                'ema_slow': float(latest['ema_slow']),
                'rsi': float(latest['rsi']),
                'atr': float(latest['atr']),
                'trend_bullish': bool(latest['trend_bullish']),
                'trend_bearish': bool(latest['trend_bearish']),
                'rsi_prev': float(prev['rsi']) if len(df) > 1 else float(latest['rsi']),
                'strategy_profile': profile,
            }
            
            # Generate signal using strategy logic
            signal = "HOLD"
            reasons = []
            
            params = self.strategy.profiles[profile]
            
            # Scalping rules
            if profile == "SCALPING":
                ema_cross_up = prev['ema_fast'] <= prev['ema_slow'] and latest['ema_fast'] > latest['ema_slow']
                ema_cross_down = prev['ema_fast'] >= prev['ema_slow'] and latest['ema_fast'] < latest['ema_slow']
                
                if latest['trend_bullish'] and (ema_cross_up or latest['rsi'] >= params['rsi_buy']):
                    signal = "BUY"
                    reasons.append("EMA cross up" if ema_cross_up else f"RSI {latest['rsi']:.1f} >= {params['rsi_buy']}")
                elif latest['trend_bearish'] and (ema_cross_down or latest['rsi'] <= params['rsi_sell']):
                    signal = "SELL"
                    reasons.append("EMA cross down" if ema_cross_down else f"RSI {latest['rsi']:.1f} <= {params['rsi_sell']}")
            
            # Day Trading rules
            elif profile == "DAY_TRADING":
                if latest['trend_bullish'] and latest['rsi'] < params['rsi_overbought']:
                    signal = "BUY"
                    reasons.append(f"Bullish trend, RSI {latest['rsi']:.1f} < {params['rsi_overbought']}")
                elif latest['trend_bearish'] and latest['rsi'] > params['rsi_oversold']:
                    signal = "SELL"
                    reasons.append(f"Bearish trend, RSI {latest['rsi']:.1f} > {params['rsi_oversold']}")
            
            # Swing Trading rules
            elif profile == "SWING":
                ema_bullish_align = latest['ema_fast'] > latest['ema_slow']
                ema_bearish_align = latest['ema_fast'] < latest['ema_slow']
                
                if ema_bullish_align and latest['trend_bullish'] and params['rsi_oversold'] < latest['rsi'] < params['rsi_overbought']:
                    signal = "BUY"
                    reasons.append(f"EMA align bullish, RSI {latest['rsi']:.1f} neutral")
                elif ema_bearish_align and latest['trend_bearish'] and params['rsi_oversold'] < latest['rsi'] < params['rsi_overbought']:
                    signal = "SELL"
                    reasons.append(f"EMA align bearish, RSI {latest['rsi']:.1f} neutral")
            
            indicators['signal_reasons'] = ', '.join(reasons) if reasons else 'No clear signal'
            
            return {
                'signal': signal,
                'indicators': indicators,
                'reasons': reasons
            }
            
        except Exception as e:
            logger.error(f"Strategy analysis failed: {e}", exc_info=True)
            return {
                'signal': 'HOLD',
                'indicators': {},
                'reasons': [f'Error: {str(e)}']
            }


def get_backtest_strategy(strategy: Optional[TradingStrategy] = None) -> BacktestStrategy:
    """
    Get backtest-compatible strategy wrapper
    
    Args:
        strategy: Optional TradingStrategy instance, will create default if None
    
    Returns:
        BacktestStrategy instance
    """
    if strategy is None:
        # Create default strategy
        from app.trading.data import get_market_data
        from app.trading.risk import get_risk_manager
        strategy = TradingStrategy(get_market_data(), get_risk_manager())
    
    return BacktestStrategy(strategy)
