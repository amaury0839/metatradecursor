"""Trading strategy: technical indicators and signals"""

import os
import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple
from app.trading.data import get_data_provider
from app.core.logger import setup_logger
from app.ai.onnx_model import load_onnx_classifier, OnnxClassifier

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
    """Trading strategy with configurable modes (scalping / swing)"""
    
    def __init__(self):
        self.data = get_data_provider()
        self.regime_model_path = os.getenv("ONNX_REGIME_MODEL")
        self.regime_clf: Optional[OnnxClassifier] = load_onnx_classifier(self.regime_model_path) if self.regime_model_path else None

        # Defaults (used by swing profile)
        self.ema_fast_period = 20
        self.ema_slow_period = 50
        self.rsi_period = 14
        self.atr_period = 14
        
        # Signal thresholds (swing)
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.rsi_neutral_low = 45
        self.rsi_neutral_high = 55

        # Profiles
        self.profiles = {
            "SCALPING": {
                "ema_fast": 5,
                "ema_slow": 20,
                "rsi_period": 14,
                "atr_period": 14,
                # Make scalping more decisive: slightly easier entries, wider extremes
                "rsi_buy": 48,
                "rsi_sell": 52,
                "rsi_overbought": 80,
                "rsi_oversold": 20,
                "volatility_floor": 0.0005,  # ATR/close mínimo para usar scalping
            },
            "SWING": {
                "ema_fast": 20,
                "ema_slow": 50,
                "rsi_period": 14,
                "atr_period": 14,
                "rsi_buy": 55,
                "rsi_sell": 45,
                "rsi_overbought": 70,
                "rsi_oversold": 30,
                "volatility_floor": 0.0,
            },
            "TREND": {  # Momentum/trend-following clásico (50/200)
                "ema_fast": 50,
                "ema_slow": 200,
                "rsi_period": 14,
                "atr_period": 14,
                "rsi_buy": 55,
                "rsi_sell": 45,
                "rsi_overbought": 75,
                "rsi_oversold": 25,
                "volatility_floor": 0.0,
            },
        }
    
    def _classify_regime(self, df: pd.DataFrame) -> Optional[str]:
        """Detect market regime via ONNX if available, else heuristic."""
        try:
            close_val = float(df.iloc[-1]["close"])
            ema_fast = float(df.iloc[-1]["ema_fast"])
            ema_slow = float(df.iloc[-1]["ema_slow"])
            rsi_val = float(df.iloc[-1]["rsi"])
            atr_val = float(df.iloc[-1]["atr"])
        except Exception:
            return None

        if self.regime_clf:
            try:
                signal, _ = self.regime_clf.predict([
                    close_val,
                    ema_fast,
                    ema_slow,
                    rsi_val,
                    atr_val,
                    ema_fast - ema_slow,
                ])
                sig = signal.lower()
                if sig in {"trend", "range"}:
                    return sig
            except Exception:
                pass

        # Heuristic fallback
        vol_ratio = abs(atr_val) / close_val if close_val else 0.0
        ema_gap = abs(ema_fast - ema_slow) / close_val if close_val else 0.0
        if ema_gap > 0.0005 or vol_ratio > 0.002:
            return "trend"
        return "range"

    def _select_profile(self, timeframe: str, df: pd.DataFrame) -> str:
        """Choose profile using timeframe bias, regime detection and volatility."""
        tf = timeframe.upper()

        # Baseline by timeframe
        if tf in {"M1", "M5", "M15"}:
            profile = "SCALPING"
        elif tf in {"H1", "H4", "D1", "W1"}:
            profile = "TREND"
        else:
            profile = "SWING"

        # Regime detection
        regime = self._classify_regime(df)
        if regime == "trend":
            profile = "TREND" if tf not in {"M1", "M5", "M15"} else profile
        elif regime == "range":
            if profile != "SCALPING":
                profile = "SWING"

        # Volatility bias for lower TF
        if len(df) >= 2 and tf in {"M1", "M5", "M15"}:
            close_val = float(df.iloc[-1]["close"])
            atr_val = calculate_atr(df["high"], df["low"], df["close"], self.profiles["SCALPING"]["atr_period"]).iloc[-1]
            vol_ratio = abs(atr_val) / close_val if close_val else 0.0
            if vol_ratio >= self.profiles["SCALPING"]["volatility_floor"]:
                profile = "SCALPING"

        return profile

    def _calc_indicators_with_profile(self, df: pd.DataFrame, profile: str) -> pd.DataFrame:
        """Compute indicators using profile-specific params."""
        params = self.profiles[profile]
        df = df.copy()
        df['ema_fast'] = calculate_ema(df['close'], params['ema_fast'])
        df['ema_slow'] = calculate_ema(df['close'], params['ema_slow'])
        df['rsi'] = calculate_rsi(df['close'], params['rsi_period'])
        df['atr'] = calculate_atr(df['high'], df['low'], df['close'], params['atr_period'])
        df['trend_bullish'] = df['ema_fast'] > df['ema_slow']
        df['trend_bearish'] = df['ema_fast'] < df['ema_slow']
        return df
    
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
        return self._calc_indicators_with_profile(df, "SWING")
    
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

        # Select strategy profile and calculate indicators accordingly
        profile = self._select_profile(timeframe, df)
        df = self._calc_indicators_with_profile(df, profile)
        
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
            'strategy_profile': profile,
        }
        
        # Generate signal
        signal = "HOLD"
        reasons = []
        
        # Log análisis antes de generar la señal
        logger.info(
            f"[ANALYSIS] Mode: {profile}, Symbol: {symbol}, Timeframe: {timeframe}, Close: {indicators['close']:.5f}, "
            f"EMA_fast: {indicators['ema_fast']:.5f}, EMA_slow: {indicators['ema_slow']:.5f}, "
            f"RSI: {indicators['rsi']:.2f}, ATR: {indicators['atr']:.5f}, "
            f"Trend Bullish: {indicators['trend_bullish']}, Trend Bearish: {indicators['trend_bearish']}, "
            f"Signal: {signal}, Reasons: {indicators.get('signal_reasons', 'N/A')}"
        )

        params = self.profiles[profile]
        # Scalping rules: cruces rápidos y filtro RSI
        if profile == "SCALPING":
            ema_cross_up = prev['ema_fast'] <= prev['ema_slow'] and latest['ema_fast'] > latest['ema_slow']
            ema_cross_down = prev['ema_fast'] >= prev['ema_slow'] and latest['ema_fast'] < latest['ema_slow']

            if latest['trend_bullish'] and (ema_cross_up or latest['rsi'] >= params['rsi_buy']):
                signal = "BUY"
                reasons.append("Scalping: EMA 5/20 al alza o RSI fuerte")
            elif latest['trend_bearish'] and (ema_cross_down or latest['rsi'] <= params['rsi_sell']):
                signal = "SELL"
                reasons.append("Scalping: EMA 5/20 a la baja o RSI débil")

            # 🔥 SMART OVERBOUGHT/OVERSOLD RULES FOR CRYPTO SCALPING
            # RSI > 75 puede ser oportuno en trend fuerte (momentum)
            # Pero reducir posición y TP para limitar riesgo
            is_crypto = any(crypto in symbol.upper() for crypto in ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOT', 'LTC', 'AVAX', 'DOGE'])
            
            if latest['rsi'] >= params['rsi_overbought']:
                # Standard: RSI 70-75 → HOLD (riesgo alto de reversal)
                if latest['rsi'] < 75:
                    signal = "HOLD"
                    reasons.append(f"Scalping: RSI {latest['rsi']:.1f} sobrecomprado, pausa")
                # 🟢 CRYPTO EXCEPTION: RSI 75+ en trend fuerte → permitir BUY con posición reducida
                elif is_crypto and latest['trend_bullish'] and latest['rsi'] >= 75:
                    # Permitir BUY pero con flageos especiales para reducción de posición
                    if signal != "BUY":
                        signal = "BUY"
                        reasons.append(f"CRYPTO SCALP: RSI {latest['rsi']:.1f} overbought pero trend bullish fuerte → SCALP con posición x0.7")
                    # Mark for position reduction
                    indicators['crypto_overbought_scalp'] = True
                    indicators['position_size_multiplier'] = 0.7  # Reduce 30%
                    indicators['tp_multiplier'] = 0.8  # Reduce TP 20%
            
            if latest['rsi'] <= params['rsi_oversold']:
                if latest['rsi'] > 25:
                    signal = "HOLD"
                    reasons.append(f"Scalping: RSI {latest['rsi']:.1f} sobrevendido, pausa")
                # Similar para oversold: crypto + trend bearish fuerte
                elif is_crypto and latest['trend_bearish'] and latest['rsi'] <= 25:
                    if signal != "SELL":
                        signal = "SELL"
                        reasons.append(f"CRYPTO SCALP: RSI {latest['rsi']:.1f} oversold pero trend bearish fuerte → SCALP con posición x0.7")
                    indicators['crypto_oversold_scalp'] = True
                    indicators['position_size_multiplier'] = 0.7
                    indicators['tp_multiplier'] = 0.8

            # Permitir entradas por pullback en tendencia
            # Buy: tendencia alcista y RSI en zona neutral con retroceso respecto al previo
            if signal == "HOLD" and latest['trend_bullish']:
                if params['rsi_oversold'] < latest['rsi'] < params['rsi_overbought'] and latest['rsi'] < indicators['rsi_prev']:
                    signal = "BUY"
                    reasons.append("Scalping: pullback en tendencia alcista (RSI neutral y retroceso)")
            # Sell: tendencia bajista y RSI neutral con rebote respecto al previo
            if signal == "HOLD" and latest['trend_bearish']:
                if params['rsi_oversold'] < latest['rsi'] < params['rsi_overbought'] and latest['rsi'] > indicators['rsi_prev']:
                    signal = "SELL"
                    reasons.append("Scalping: pullback en tendencia bajista (RSI neutral y rebote)")

        # Swing rules: seguir tendencia + RSI moderado
        elif profile == "SWING":
            if latest['trend_bullish'] and latest['rsi'] >= params['rsi_buy']:
                signal = "BUY"
                reasons.append("Swing: Tendencia alcista + RSI confirma")
            elif latest['trend_bearish'] and latest['rsi'] <= params['rsi_sell']:
                signal = "SELL"
                reasons.append("Swing: Tendencia bajista + RSI confirma")
            else:
                signal = "HOLD"
                reasons.append("Swing: Sin confirmación de RSI/tendencia")

        # Trend-following clásico: dejar correr, cortar pérdidas
        else:  # TREND
            ema_cross_up = prev['ema_fast'] <= prev['ema_slow'] and latest['ema_fast'] > latest['ema_slow']
            ema_cross_down = prev['ema_fast'] >= prev['ema_slow'] and latest['ema_fast'] < latest['ema_slow']

            if latest['trend_bullish'] and (ema_cross_up or latest['rsi'] >= params['rsi_buy']):
                signal = "BUY"
                reasons.append("Trend: cruce 50/200 o RSI confirma momentum alcista")
            elif latest['trend_bearish'] and (ema_cross_down or latest['rsi'] <= params['rsi_sell']):
                signal = "SELL"
                reasons.append("Trend: cruce 50/200 o RSI confirma momentum bajista")
            else:
                signal = "HOLD"
                reasons.append("Trend: sin confirmación de cruce/RSI")
        
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
