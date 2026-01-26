"""Enhanced decision engine with combined scoring system"""

from app.ai.decision_engine import DecisionEngine
from app.core.logger import setup_logger

logger = setup_logger("enhanced_decision")


class EnhancedDecisionEngine(DecisionEngine):
    """Decision engine with combined weighted scoring"""
    
    # Scoring weights
    TECHNICAL_WEIGHT = 0.60
    AI_WEIGHT = 0.25
    SENTIMENT_WEIGHT = 0.15
    
    # Execution threshold
    EXECUTION_THRESHOLD = 0.55
    
    def calculate_combined_score(
        self,
        technical_signal: str,
        ai_confidence: float,
        ai_action: str,
        sentiment_score: float = 0.0
    ) -> tuple[float, str]:
        """
        Calculate combined score from multiple signals
        
        Returns:
            (final_score, recommended_action)
        """
        # Technical score: BUY=1.0, SELL=-1.0, HOLD=0.0
        technical_score = {
            "BUY": 1.0,
            "SELL": -1.0,
            "HOLD": 0.0
        }.get(technical_signal, 0.0)
        
        # AI score: aligned with action direction
        if ai_action == "BUY":
            ai_score = ai_confidence
        elif ai_action == "SELL":
            ai_score = -ai_confidence
        else:
            ai_score = 0.0
        
        # Sentiment score: normalize to [-1, 1]
        # Assuming sentiment_score is already in [-1, 1] range
        normalized_sentiment = max(-1.0, min(1.0, sentiment_score))
        
        # Calculate weighted final score
        final_score = (
            technical_score * self.TECHNICAL_WEIGHT +
            ai_score * self.AI_WEIGHT +
            normalized_sentiment * self.SENTIMENT_WEIGHT
        )
        
        # Determine action based on final score
        if abs(final_score) >= self.EXECUTION_THRESHOLD:
            recommended_action = "BUY" if final_score > 0 else "SELL"
        else:
            recommended_action = "HOLD"
        
        logger.info(
            f"Combined scoring: tech={technical_score:.2f}, ai={ai_score:.2f}, "
            f"sentiment={normalized_sentiment:.2f} → final={final_score:.2f}, action={recommended_action}"
        )
        
        return abs(final_score), recommended_action


def get_enhanced_decision_engine():
    """Get enhanced decision engine singleton"""
    global _enhanced_engine
    if '_enhanced_engine' not in globals():
        _enhanced_engine = EnhancedDecisionEngine()
    return _enhanced_engine
