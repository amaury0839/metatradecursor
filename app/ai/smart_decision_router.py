"""Smart AI Decision Router - tries enhanced, falls back to simple"""

from typing import Optional, Dict
from app.core.logger import setup_logger
from app.ai.schemas import TradingDecision, neutral_decision
from app.core.database import get_database_manager

# Import both engines
from app.ai.decision_engine import get_decision_engine
from app.ai.enhanced_decision_engine import get_enhanced_decision_engine

logger = setup_logger("ai_router")


def should_call_gemini(technical_signal: str, has_executable_signal: bool = True) -> bool:
    """
    Determine if Gemini should be consulted.
    
    🔧 FIXED: Always call Gemini when trade is executable.
    - Use Gemini as quality filter/confirmation, not replacement
    - Only skip if technical=HOLD and no other context
    
    Args:
        technical_signal: BUY/SELL/HOLD
        has_executable_signal: True if trade is close to execution (spread/vol/time ok)
    
    Returns:
        True if Gemini should confirm
    """
    # If technical already says HOLD → skip IA (neutral context)
    if technical_signal == "HOLD":
        return False
    
    # If technical says BUY/SELL and trade is executable → CALL IA to confirm
    if technical_signal in ["BUY", "SELL"] and has_executable_signal:
        return True
    
    # Default: call Gemini for validation
    return True


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

    # 🔧 FIXED: Always try to get IA confirmation when technical signal is actionable
    # Previously: skipped IA entirely if technical=BUY/SELL
    # Now: use IA as quality filter (veto/confirm), not replacement
    
    has_executable_signal = tech_signal in ["BUY", "SELL"]
    should_use_ai = should_call_gemini(tech_signal, has_executable_signal)
    
    if not should_use_ai:
        logger.info(
            f"Skipping AI for {symbol}: technical signal=HOLD (neutral context)"
        )
        return None
    
    logger.info(
        f"Consulting AI for {symbol}: technical signal={tech_signal} "
        f"(using as quality filter/confirmation)"
    )
    
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
