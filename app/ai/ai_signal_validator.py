"""
AI-powered signal validator using composite indicators
Robustifies decisions with machine learning validation
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, Any
from datetime import datetime
from app.core.logger import setup_logger

logger = setup_logger("ai_signal_validator")


class AISignalValidator:
    """
    Composite AI-based signal validator combining:
    1. Market Strength Score (MSS) - multi-indicator confluence
    2. Volatility Regime Classification
    3. Trend Momentum Index (TMI)
    4. AI Confirmation Score
    """
    
    def __init__(self):
        self.min_mss_for_entry = 0.65  # Minimum Market Strength for trade entry
        self.min_confidence_for_ai = 0.55
    
    def calculate_market_strength_score(
        self,
        close: pd.Series,
        high: pd.Series,
        low: pd.Series,
        ema_fast: pd.Series,
        ema_slow: pd.Series,
        rsi: pd.Series,
        atr: pd.Series,
    ) -> pd.Series:
        """
        🎯 MARKET STRENGTH SCORE (MSS)
        
        Composite indicator combining:
        - EMA Alignment (trend strength)
        - RSI Positioning (momentum)
        - Price-EMA Proximity (confirmation)
        - Volatility Confidence (ATR-based)
        
        Returns: Series with values 0.0 to 1.0
        """
        
        # 1. EMA Alignment Score (40% weight)
        # How far apart are EMAs and in what direction?
        ema_diff = (ema_fast - ema_slow) / close * 100  # in basis points
        ema_gap = np.abs(ema_diff)  # Gap magnitude
        
        # Align direction: positive if fast > slow (bullish), negative if fast < slow (bearish)
        ema_alignment = np.clip(ema_diff / 0.5, -1, 1)  # Normalize to [-1, 1]
        ema_score = (ema_alignment + 1) / 2  # Convert to [0, 1]
        ema_strength = 1.0 - np.exp(-ema_gap / 0.5)  # Sigmoid-like strength
        ema_component = ema_score * ema_strength * 0.40
        
        # 2. RSI Positioning Score (30% weight)
        # Where is RSI and how extreme is it?
        rsi_normalized = rsi / 100.0  # [0, 1]
        
        # Distance from neutral (50)
        rsi_extreme = 1.0 - np.abs(rsi_normalized - 0.5) * 2  # [0, 1]
        # 0 if neutral, 1 if extreme (0 or 100)
        
        # Direction alignment with EMA
        rsi_bullish = (rsi_normalized > 0.5).astype(float)
        ema_bullish = (ema_fast > ema_slow).astype(float)
        rsi_alignment = 1.0 - np.abs(rsi_bullish - ema_bullish)
        
        rsi_component = rsi_extreme * rsi_alignment * 0.30
        
        # 3. Price-EMA Proximity Score (20% weight)
        # How well does price follow the trend?
        
        # Distance of price from fast EMA
        price_ema_dist = np.abs(close - ema_fast) / (atr + 0.00001)
        
        # Closer is better (normalized by ATR for scale invariance)
        proximity_score = 1.0 / (1.0 + price_ema_dist)  # Logistic curve
        proximity_component = proximity_score * 0.20
        
        # 4. Volatility Confidence Score (10% weight)
        # Is there enough volatility to trust the signal?
        
        # ATR as % of price
        volatility_ratio = atr / close
        
        # Confidence increases with volatility (0.0005 to 0.01 is ideal)
        vol_confidence = np.clip(volatility_ratio / 0.005, 0.3, 1.0)
        volatility_component = vol_confidence * 0.10
        
        # ============ COMPOSITE SCORE ============
        mss = (
            ema_component
            + rsi_component
            + proximity_component
            + volatility_component
        )
        
        # Normalize to [0, 1]
        mss = np.clip(mss, 0, 1)
        
        return mss
    
    def calculate_trend_momentum_index(
        self,
        close: pd.Series,
        ema_fast: pd.Series,
        ema_slow: pd.Series,
        rsi: pd.Series,
        volume: Optional[pd.Series] = None,
    ) -> pd.Series:
        """
        🚀 TREND MOMENTUM INDEX (TMI)
        
        Measures momentum and trend consistency:
        - Price acceleration (2nd derivative)
        - EMA slope
        - RSI momentum
        - Volume confirmation (if available)
        
        Returns: Series with values -1.0 (strong down) to +1.0 (strong up)
        """
        
        # 1. Price Momentum (rate of change)
        price_change = close.pct_change(periods=5)  # 5-bar momentum
        price_momentum = np.clip(price_change / (price_change.std() + 0.00001), -3, 3) / 3
        
        # 2. EMA Slope (trend direction)
        ema_trend = (ema_fast - ema_slow) / np.abs(ema_slow + 0.00001)
        ema_slope = np.clip(ema_trend / (ema_trend.std() + 0.00001), -3, 3) / 3
        
        # 3. RSI Momentum (RSI acceleration)
        rsi_momentum = rsi.diff(periods=3)
        rsi_mom_norm = np.clip(rsi_momentum / 20, -1, 1)
        
        # 4. Volume Confirmation (if available)
        vol_component = 0.0
        if volume is not None:
            vol_change = volume.pct_change()
            vol_confirmation = (vol_change > 0).astype(float) * 0.5 + 0.5  # [0.5, 1.0]
            vol_component = vol_confirmation * 0.15
        
        # Composite TMI
        tmi = (
            price_momentum * 0.35
            + ema_slope * 0.40
            + rsi_mom_norm * 0.25
            + vol_component
        )
        
        return np.clip(tmi, -1.0, 1.0)
    
    def classify_volatility_regime(
        self,
        atr: pd.Series,
        close: pd.Series,
        lookback: int = 20,
    ) -> Tuple[pd.Series, pd.Series]:
        """
        📊 VOLATILITY REGIME CLASSIFICATION
        
        Classifies market as:
        - LOW: Calm, tight spreads (scalping friendly)
        - MEDIUM: Normal volatility (standard trading)
        - HIGH: Choppy, wide spreads (trending mode)
        
        Returns:
        - regime_label: Series of ["LOW", "MEDIUM", "HIGH"]
        - volatility_score: Series of [0, 1] (0=calm, 1=extreme)
        """
        
        # Rolling volatility percentile
        atr_percentile = (atr / close).rolling(lookback).apply(
            lambda x: (x[-1] - x.min()) / (x.max() - x.min() + 0.00001),
            raw=True
        )
        
        vol_score = np.clip(atr_percentile, 0, 1)
        
        # Classify into regimes
        regime = pd.Series(index=atr.index, dtype=object)
        regime[vol_score < 0.33] = "LOW"
        regime[(vol_score >= 0.33) & (vol_score < 0.67)] = "MEDIUM"
        regime[vol_score >= 0.67] = "HIGH"
        
        return regime, vol_score
    
    def ai_signal_confirmation(
        self,
        mss: float,
        tmi: float,
        volatility_regime: str,
        rsi: float,
        ema_bullish: bool,
        signal_direction: str,  # "BUY" or "SELL"
    ) -> Tuple[bool, float]:
        """
        🤖 AI CONFIRMATION ENGINE
        
        Uses composite indicators to confirm or reject signals:
        - Market Strength Score (0.0-1.0)
        - Trend Momentum Index (-1.0 to +1.0)
        - Volatility Regime (LOW/MEDIUM/HIGH)
        - RSI position and EMA alignment
        
        Args:
            mss: Market Strength Score
            tmi: Trend Momentum Index
            volatility_regime: Current volatility regime
            rsi: Current RSI value
            ema_bullish: Is EMA in bullish alignment?
            signal_direction: Proposed signal direction
        
        Returns:
            (is_confirmed, confidence_score)
            - is_confirmed: bool (should execute?)
            - confidence_score: 0.0-1.0
        """
        
        confidence = 0.0
        
        # 1. Market Strength Requirement (40% weight)
        mss_score = mss * 0.40
        
        # 2. Trend Momentum Alignment (30% weight)
        if signal_direction == "BUY":
            tmi_score = np.clip((tmi + 1) / 2, 0, 1) * 0.30  # Positive TMI for BUY
        else:  # SELL
            tmi_score = np.clip((1 - tmi) / 2, 0, 1) * 0.30  # Negative TMI for SELL
        
        # 3. Volatility Regime Adjustment (20% weight)
        vol_scores = {
            "LOW": 0.7,      # Scalping regime - good for entries
            "MEDIUM": 1.0,   # Normal regime - ideal
            "HIGH": 0.8,     # Trending regime - ok but choppy
        }
        vol_score = vol_scores.get(volatility_regime, 0.6) * 0.20
        
        # 4. RSI + EMA Alignment (10% weight)
        rsi_normalized = rsi / 100.0
        
        if signal_direction == "BUY":
            # For BUY: want RSI < 70 and EMA bullish
            rsi_check = 1.0 if rsi_normalized < 0.70 else 0.3
            ema_check = 1.0 if ema_bullish else 0.5
        else:  # SELL
            # For SELL: want RSI > 30 and EMA bearish
            rsi_check = 1.0 if rsi_normalized > 0.30 else 0.3
            ema_check = 1.0 if not ema_bullish else 0.5
        
        alignment_score = (rsi_check + ema_check) / 2 * 0.10
        
        # ============ COMPOSITE CONFIDENCE ============
        confidence = mss_score + tmi_score + vol_score + alignment_score
        
        # Requirements for confirmation
        min_confidence = 0.55
        
        # Stricter requirements in HIGH volatility
        if volatility_regime == "HIGH":
            min_confidence = 0.65
        
        is_confirmed = confidence >= min_confidence
        
        logger.debug(
            f"AI Confirmation: {signal_direction}, "
            f"MSS={mss:.2f}, TMI={tmi:.2f}, Vol={volatility_regime}, "
            f"Confidence={confidence:.2f}, Confirmed={is_confirmed}"
        )
        
        return is_confirmed, confidence
    
    def validate_signal(
        self,
        df: pd.DataFrame,
        signal_type: str,  # "BUY" or "SELL"
        current_rsi: float,
        ema_bullish: bool,
    ) -> Dict[str, Any]:
        """
        🎯 COMPLETE SIGNAL VALIDATION
        
        Runs all indicators and returns comprehensive validation result.
        """
        
        try:
            # Extract latest values
            close = float(df.iloc[-1]["close"])
            high = float(df.iloc[-1]["high"])
            low = float(df.iloc[-1]["low"])
            mss = float(df.iloc[-1].get("mss", 0.5))
            tmi = float(df.iloc[-1].get("tmi", 0.0))
            vol_regime = str(df.iloc[-1].get("vol_regime", "MEDIUM"))
            
            # Run AI confirmation
            is_confirmed, confidence = self.ai_signal_confirmation(
                mss=mss,
                tmi=tmi,
                volatility_regime=vol_regime,
                rsi=current_rsi,
                ema_bullish=ema_bullish,
                signal_direction=signal_type,
            )
            
            return {
                "is_valid": is_confirmed,
                "confidence": confidence,
                "mss": mss,
                "tmi": tmi,
                "vol_regime": vol_regime,
                "reason": (
                    f"AI Validation: {signal_type} signal confirmed with "
                    f"confidence={confidence:.2f}, MSS={mss:.2f}, TMI={tmi:.2f}"
                    if is_confirmed
                    else f"Signal rejected: confidence={confidence:.2f} < threshold"
                ),
            }
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return {
                "is_valid": False,
                "confidence": 0.0,
                "reason": f"Validation error: {str(e)}",
            }


def get_ai_signal_validator() -> AISignalValidator:
    """Get or create AI signal validator instance"""
    if not hasattr(get_ai_signal_validator, "_instance"):
        get_ai_signal_validator._instance = AISignalValidator()
    return get_ai_signal_validator._instance
