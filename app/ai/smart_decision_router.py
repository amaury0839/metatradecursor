"""Smart AI Decision Router - tries enhanced, falls back to simple"""

from typing import Optional, Dict
from app.core.logger import setup_logger
from app.ai.schemas import TradingDecision, neutral_decision
from app.core.database import get_database_manager

# Import both engines
from app.ai.decision_engine import get_decision_engine
from app.ai.enhanced_decision_engine import get_enhanced_decision_engine

logger = setup_logger("ai_router")


def should_call_gemini(technical_signal: str) -> bool:
    """Only call Gemini when the technical layer is inconclusive (HOLD)."""
    return technical_signal == "HOLD"


def make_smart_decision(
    symbol: str,
    timeframe: str,
    technical_data: Dict,
    sentiment_data: Optional[Dict] = None,
    use_enhanced: bool = True
) -> Optional[TradingDecision]:
    """
    Smart decision router that tries enhanced engine first,
    falls back to simple engine if enhanced fails or is disabled.
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe string
        technical_data: Technical analysis data
        sentiment_data: Optional sentiment data
        use_enhanced: Try enhanced engine first (default True)
    
    Returns:
        TradingDecision or None
    """
    
    db = get_database_manager()
    tech_signal = technical_data.get('signal', 'HOLD') if technical_data else 'HOLD'

    # Skip Gemini completely when the technical layer already has a clear signal
    if not should_call_gemini(tech_signal):
        logger.info(
            f"Skipping AI for {symbol} {timeframe}: technical signal={tech_signal}"
        )
        return None
    
    # Try enhanced engine first if enabled
    if use_enhanced:
        try:
            logger.info(f"Attempting ENHANCED decision for {symbol}")
            enhanced_engine = get_enhanced_decision_engine()
            
            decision = enhanced_engine.make_enhanced_decision(
                symbol=symbol,
                timeframe=timeframe,
                technical_data=technical_data,
                sentiment_data=sentiment_data
            )
            
            if decision:
                logger.info(
                    f"✓ Enhanced decision succeeded: {decision.action} "
                    f"with confidence {decision.confidence:.2f}"
                )
                
                # Save to database
                try:
                    data_sources = technical_data.get('available_sources', []) if technical_data else []
                    db.save_ai_decision(symbol, timeframe, decision, 
                                       engine_type='enhanced', data_sources=data_sources)
                except Exception as e:
                    logger.warning(f"Failed to save enhanced decision to DB: {e}")
                
                return decision
            else:
                logger.warning("Enhanced decision returned None, falling back to simple")
                
        except Exception as e:
            logger.warning(f"Enhanced decision failed: {e}, falling back to simple")
    
    # Fallback to simple decision engine
    try:
        logger.info(f"Using SIMPLE decision engine for {symbol}")
        simple_engine = get_decision_engine()
        
        # Extract technical signal and indicators from technical_data
        tech_signal = technical_data.get('signal', 'HOLD') if technical_data else 'HOLD'
        indicators = technical_data.get('data', {}) if technical_data else {}
        
        decision, prompt_hash, error = simple_engine.make_decision(
            symbol=symbol,
            timeframe=timeframe,
            technical_signal=tech_signal,
            indicators=indicators
        )
        
        if decision:
            logger.info(
                f"✓ Simple decision succeeded: {decision.action} "
                f"with confidence {decision.confidence:.2f}"
            )
            
            # Save to database
            try:
                data_sources = technical_data.get('available_sources', []) if technical_data else []
                db.save_ai_decision(symbol, timeframe, decision, 
                                   engine_type='simple', data_sources=data_sources)
            except Exception as e:
                logger.warning(f"Failed to save simple decision to DB: {e}")
        else:
            logger.warning(f"Simple decision also returned None: {error}")
            return neutral_decision(symbol, timeframe)
        
        return decision
        
    except Exception as e:
        logger.error(f"Both enhanced and simple decisions failed: {e}", exc_info=True)
        return None
