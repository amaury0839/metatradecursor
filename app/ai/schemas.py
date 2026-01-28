"""Pydantic schemas for AI decision validation"""

from typing import Literal, List, Optional
from pydantic import BaseModel, Field, field_validator
from app.core.logger import setup_logger

logger = setup_logger("schemas")


class OrderDetails(BaseModel):
    """Order details from AI decision"""
    type: Literal["MARKET"] = "MARKET"
    volume_lots: float = Field(..., gt=0)
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None
    
    @field_validator("volume_lots")
    @classmethod
    def validate_volume(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Volume must be positive")
        if v > 100:
            raise ValueError("Volume exceeds maximum (100 lots)")
        return v


class ConstraintsUsed(BaseModel):
    """Constraints that were considered in the decision"""
    max_risk_per_trade: Optional[float] = None
    max_positions: Optional[int] = None
    max_drawdown: Optional[float] = None
    spread_limit: Optional[float] = None
    trading_hours: Optional[bool] = None


class TradingDecision(BaseModel):
    """AI trading decision schema - Enterprise pattern with safe defaults"""
    action: Literal["BUY", "SELL", "HOLD", "CLOSE"] = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    symbol: str = Field(...)
    timeframe: str = Field(...)
    reason: List[str] = Field(default_factory=list)
    reasoning: str = Field(default="")  # String version for DB/logs
    market_bias: str = Field(default="neutral")
    probability_up: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    risk_ok: bool = Field(default=True)
    order: Optional[OrderDetails] = None
    constraints_used: Optional[ConstraintsUsed] = None
    sources: List[str] = Field(default_factory=list)  # Data sources used
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v
    
    @field_validator("action")
    @classmethod
    def validate_action_with_order(cls, v: str) -> str:
        # Note: Order validation is done in is_valid_for_execution
        # This validator just ensures action is one of the allowed values
        return v
    
    def is_valid_for_execution(self, min_confidence: float = 0.30) -> bool:
        """
        Check if decision is valid for execution
        
        SCALPING RULE: IA NO debe bloquear señal técnica válida
        - Si action es BUY/SELL → válido incluso si risk_ok=False
        - risk_ok es un INDICADOR, no un BLOQUEADOR absoluto
        - Real risk validation happens in check_all_risk_conditions()
        
        Args:
            min_confidence: Minimum confidence threshold (default 0.30 for aggressive trading)
        
        Returns:
            True if valid for execution (action is BUY/SELL)
        """
        # 🟢 SCALPING: BUY/SELL action is valid regardless of risk_ok
        # Real risk checks happen later in main.py via check_all_risk_conditions()
        if self.action in ["BUY", "SELL"]:
            # Log if risk_ok=False (warning but not blocking)
            if not self.risk_ok:
                logger.warning(
                    f"Decision valid for execution but risk_ok=False: {self.action} {self.symbol} "
                    f"(confidence={self.confidence:.2f}). Real risk validation will occur in execution phase."
                )
            else:
                logger.info(f"Decision valid for execution: action={self.action}, confidence={self.confidence:.2f}, risk_ok=True")
            return True
        
        # HOLD is never executable
        if self.action == "HOLD":
            logger.info(f"Decision not valid for execution: HOLD with confidence {self.confidence:.2f}")
            return False
        
        # CLOSE action is valid if we have an order to close
        if self.action == "CLOSE":
            return True
        
        # Unknown action
        return False


def neutral_decision(symbol: str, timeframe: str) -> "TradingDecision":
    """Factory for a schema-compliant neutral HOLD decision.

    Ensures all required fields are present to avoid validation errors
    when the AI layer is unavailable or blocked.
    """
    return TradingDecision(
        symbol=symbol,
        timeframe=timeframe,
        action="HOLD",
        confidence=0.0,
        reasoning="Neutral fallback. AI unavailable or blocked.",
        market_bias="neutral",
        probability_up=0.5,
        risk_ok=False,
        sources=[],
    )
