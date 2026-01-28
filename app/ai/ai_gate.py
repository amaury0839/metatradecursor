"""
AI Gate - Regla de Oro: Solo llamar IA en zona gris técnica
Optimiza performance eliminando llamadas innecesarias a IA
"""

from typing import Dict, Any, Optional
from app.core.logger import setup_logger

logger = setup_logger("ai_gate")


class AIGate:
    """
    Determina cuándo es necesario consultar IA basado en zona gris técnica
    
    Regla de Oro: Solo llamar IA cuando análisis técnico es ambiguo/indeciso
    """
    
    # Umbrales para zona gris
    RSI_GRAY_ZONE_MIN = 45
    RSI_GRAY_ZONE_MAX = 55
    EMA_CONVERGENCE_THRESHOLD = 0.0005  # 0.05% de diferencia
    ATR_LOW_THRESHOLD = 0.0001  # ATR muy bajo = baja volatilidad
    
    def __init__(self):
        self.calls_saved = 0
        self.calls_made = 0
        logger.info("✅ AIGate initialized - Regla de Oro: Solo IA en zona gris")
    
    def needs_ai(
        self,
        tech_signal: str,
        indicators: Dict[str, Any],
        confidence: Optional[float] = None
    ) -> tuple[bool, str]:
        """
        Determina si se necesita consultar IA
        
        Args:
            tech_signal: Señal técnica (BUY, SELL, HOLD, STRONG_BUY, STRONG_SELL)
            indicators: Indicadores técnicos (rsi, ema_fast, ema_slow, atr, etc.)
            confidence: Confianza técnica (opcional)
        
        Returns:
            tuple[bool, str]: (necesita_ia, razón)
        """
        
        # 1️⃣ SEÑALES FUERTES → NO NECESITA IA
        if tech_signal in ["STRONG_BUY", "STRONG_SELL"]:
            self.calls_saved += 1
            reason = f"Señal técnica fuerte: {tech_signal}"
            logger.info(f"🚫 AI SKIP: {reason}")
            return False, reason
        
        # 2️⃣ CONFIANZA TÉCNICA ALTA → NO NECESITA IA
        if confidence is not None and confidence >= 0.75:
            self.calls_saved += 1
            reason = f"Confianza técnica alta: {confidence:.2f}"
            logger.info(f"🚫 AI SKIP: {reason}")
            return False, reason
        
        # Extraer indicadores con valores por defecto seguros
        rsi = indicators.get("rsi", 50)
        ema_fast = indicators.get("ema_fast", 0)
        ema_slow = indicators.get("ema_slow", 0)
        atr = indicators.get("atr", 0)
        close = indicators.get("close", 0)
        
        # 3️⃣ RSI EN ZONA GRIS (45-55) → NECESITA IA
        if self.RSI_GRAY_ZONE_MIN <= rsi <= self.RSI_GRAY_ZONE_MAX:
            self.calls_made += 1
            reason = f"RSI en zona gris: {rsi:.1f}"
            logger.info(f"✅ AI NEEDED: {reason}")
            return True, reason
        
        # 4️⃣ EMAS CONVERGIENDO → NECESITA IA
        if ema_fast > 0 and ema_slow > 0 and close > 0:
            ema_diff_pct = abs(ema_fast - ema_slow) / close
            if ema_diff_pct < self.EMA_CONVERGENCE_THRESHOLD:
                self.calls_made += 1
                reason = f"EMAs convergiendo: diff={ema_diff_pct:.4%}"
                logger.info(f"✅ AI NEEDED: {reason}")
                return True, reason
        
        # 5️⃣ ATR MUY BAJO (baja volatilidad) → NECESITA IA
        if atr > 0 and close > 0:
            atr_pct = atr / close
            if atr_pct < self.ATR_LOW_THRESHOLD:
                self.calls_made += 1
                reason = f"ATR muy bajo: {atr_pct:.4%}"
                logger.info(f"✅ AI NEEDED: {reason}")
                return True, reason
        
        # 6️⃣ SIGNAL HOLD CON TREND DEFINIDO → POSIBLE ZONA GRIS
        if tech_signal == "HOLD":
            trend_bullish = indicators.get("trend_bullish", False)
            trend_bearish = indicators.get("trend_bearish", False)
            
            if trend_bullish or trend_bearish:
                # Trend definido pero señal HOLD = conflicto → necesita IA
                self.calls_made += 1
                trend = "bullish" if trend_bullish else "bearish"
                reason = f"HOLD con trend {trend} = conflicto"
                logger.info(f"✅ AI NEEDED: {reason}")
                return True, reason
        
        # 7️⃣ CONFLICTO ENTRE INDICADORES → NECESITA IA
        macd_signal = indicators.get("macd_signal", "NEUTRAL")
        rsi_signal = indicators.get("rsi_signal", "NEUTRAL")
        ema_signal = indicators.get("ema_trend", "NEUTRAL")
        
        signals = [macd_signal, rsi_signal, ema_signal]
        unique_signals = set([s for s in signals if s not in ["NEUTRAL", "HOLD", None]])
        
        if len(unique_signals) >= 2:
            # 2 o más señales diferentes = conflicto
            self.calls_made += 1
            reason = f"Conflicto entre indicadores: {unique_signals}"
            logger.info(f"✅ AI NEEDED: {reason}")
            return True, reason
        
        # 8️⃣ POR DEFECTO: SEÑAL CLARA → NO NECESITA IA
        self.calls_saved += 1
        reason = f"Señal técnica clara: {tech_signal}"
        logger.info(f"🚫 AI SKIP: {reason}")
        return False, reason
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso"""
        total = self.calls_saved + self.calls_made
        if total == 0:
            return {
                "calls_saved": 0,
                "calls_made": 0,
                "total": 0,
                "savings_pct": 0.0
            }
        
        return {
            "calls_saved": self.calls_saved,
            "calls_made": self.calls_made,
            "total": total,
            "savings_pct": (self.calls_saved / total) * 100
        }
    
    def log_stats(self):
        """Log estadísticas de ahorro"""
        stats = self.get_stats()
        if stats["total"] > 0:
            logger.info(
                f"📊 AI Gate Stats: {stats['calls_saved']} skipped, "
                f"{stats['calls_made']} made, "
                f"{stats['savings_pct']:.1f}% saved"
            )


# Singleton instance
_ai_gate: Optional[AIGate] = None


def get_ai_gate() -> AIGate:
    """Get singleton AI gate instance"""
    global _ai_gate
    if _ai_gate is None:
        _ai_gate = AIGate()
    return _ai_gate
