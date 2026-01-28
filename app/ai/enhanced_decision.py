"""Enhanced decision engine with combined scoring system"""

from app.ai.decision_engine import DecisionEngine
from app.core.logger import setup_logger

logger = setup_logger("enhanced_decision")


class EnhancedDecisionEngine(DecisionEngine):
    """
    Decision engine with combined weighted scoring
    
    🎯 IA ES FILTRO DE CALIDAD, NO PUNTO ÚNICO DE FALLO
    
    - Technical: 60% (signals de mercado reales)
    - AI: 25% (confirmación/filtro de calidad)
    - Sentiment: 15% (contexto de noticias)
    
    Si IA = HOLD pero técnica = BUY:
    ✅ Ejecutar con confianza reducida, IA actúa como "calidad filter"
    
    Si IA falla completamente:
    ✅ Ejecutar si técnica >= 0.65 (umbral alto)
    """
    
    # Scoring weights - Técnica dominante, IA como filtro
    TECHNICAL_WEIGHT = 0.60
    AI_WEIGHT = 0.25
    SENTIMENT_WEIGHT = 0.15
    
    # Execution threshold
    EXECUTION_THRESHOLD = 0.55
    
    # 🔥 AI Confidence multipliers (IA como filtro, no bloqueador)
    # Si AI confirma = full confidence
    # Si AI neutral = 0.00x (NO contribuye si confidence < 0.55)
    # Si AI dice lo opuesto = 0.60x (filtro de calidad fuerte)
    AI_CONFIRMATION_MULT = 1.0      # IA confirms technical → 100%
    AI_NEUTRAL_MULT = 0.00          # IA says HOLD pero confidence < 0.55 → NO_OP (0 weight)
    AI_OPPOSITE_MULT = 0.70         # IA says opposite → reduce a 70%
    AI_MIN_CONFIDENCE_THRESHOLD = 0.55  # Below this, AI doesn't influence score
    
    def calculate_combined_score(
        self,
        technical_signal: str,
        ai_confidence: float,
        ai_action: str,
        sentiment_score: float = 0.0
    ) -> tuple[float, str]:
        """
        Calculate combined score from multiple signals
        
        🎯 AI acts as a QUALITY FILTER, not a single point of failure
        ✅ FIX: If AI confidence < 0.55, treat as NO_OP (weight=0)
        
        Returns:
            (final_score, recommended_action)
        """
        # Technical score: BUY=1.0, SELL=-1.0, HOLD=0.0
        technical_score = {
            "BUY": 1.0,
            "SELL": -1.0,
            "HOLD": 0.0
        }.get(technical_signal, 0.0)
        
        # 🔑 AI QUALITY FILTER LOGIC (FIX: Threshold-based)
        ai_score = 0.0
        ai_adjustment_mult = 0.0  # Default: NO_OP
        ai_weight = self.AI_WEIGHT
        
        # CRITICAL FIX: If AI confidence too low, don't let it bias the score
        if ai_confidence < self.AI_MIN_CONFIDENCE_THRESHOLD:
            logger.info(
                f"AI confidence {ai_confidence:.2f} < {self.AI_MIN_CONFIDENCE_THRESHOLD} "
                f"threshold. Treating as NO_OP (no influence)."
            )
            ai_weight = 0.0  # Remove AI from calculation
            ai_score = 0.0
            ai_adjustment_mult = 0.0
        
        elif ai_action == technical_signal and ai_action != "HOLD":
            # ✅ AI CONFIRMS technical signal → full confidence
            ai_adjustment_mult = self.AI_CONFIRMATION_MULT
            ai_score = ai_confidence
            logger.info(f"AI CONFIRMS {ai_action}: using full confidence {ai_confidence:.2f}")
            
        elif ai_action == "HOLD":
            # ⚠️ AI says HOLD - applies quality filter with reduced weight
            ai_adjustment_mult = 0.50  # Soft penalty, not blocking
            ai_score = -ai_confidence * 0.25  # Slight drag only
            logger.info(
                f"AI neutral/HOLD: technical={technical_signal}. "
                f"Applying quality filter (x{ai_adjustment_mult})"
            )
            
        else:
            # ❌ AI says opposite to technical
            # Strong quality filter but still allow if technical > threshold
            ai_adjustment_mult = self.AI_OPPOSITE_MULT
            if ai_action == "BUY":
                ai_score = ai_confidence
            elif ai_action == "SELL":
                ai_score = -ai_confidence
            else:
                ai_score = 0.0
            logger.warning(
                f"AI {ai_action} vs technical {technical_signal}: "
                f"Applying strong quality filter (x{self.AI_OPPOSITE_MULT})"
            )
        
        # Sentiment score: normalize to [-1, 1]
        # FIX: If sentiment unavailable/unknown, don't contribute to weighting
        normalized_sentiment = max(-1.0, min(1.0, sentiment_score))
        sentiment_weight = self.SENTIMENT_WEIGHT
        if sentiment_score == 0.0:
            # Sentiment was unavailable → don't include in average
            sentiment_weight = 0.0
        
        # Reweight if removing components
        total_weight = self.TECHNICAL_WEIGHT + (ai_weight * ai_adjustment_mult) + sentiment_weight
        if total_weight == 0:
            total_weight = 1.0  # Prevent division by zero
        
        # Calculate weighted final score
        # Technical dominates (60%), AI is filter (25%), Sentiment context (15%)
        final_score = (
            (technical_score * self.TECHNICAL_WEIGHT +
             ai_score * ai_weight +
             normalized_sentiment * sentiment_weight) / total_weight
        )
        
        # Determine action based on final score
        if abs(final_score) >= self.EXECUTION_THRESHOLD:
            recommended_action = "BUY" if final_score > 0 else "SELL"
        else:
            recommended_action = "HOLD"
        
        logger.info(
            f"Combined scoring: tech={technical_score:.2f} (60%), "
            f"ai={ai_score:.2f}*{ai_adjustment_mult:.2f} (25%→{ai_weight*100:.0f}%), "
            f"sentiment={normalized_sentiment:.2f} (15%→{sentiment_weight*100:.0f}%) "
            f"→ final={final_score:.2f}, action={recommended_action}"
        )
        
        return abs(final_score), recommended_action


def get_enhanced_decision_engine():
    """Get enhanced decision engine singleton"""
    global _enhanced_engine
    if '_enhanced_engine' not in globals():
        _enhanced_engine = EnhancedDecisionEngine()
    return _enhanced_engine
