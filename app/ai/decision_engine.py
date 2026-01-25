"""Decision engine that combines technical signals with AI decisions"""

import hashlib
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from app.ai.gemini_client import get_gemini_client
from app.ai.schemas import TradingDecision
from app.ai.prompt_templates import build_system_prompt, build_user_prompt
from app.core.config import get_config
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client
from app.trading.data import get_data_provider
from app.trading.portfolio import get_portfolio_manager
from app.trading.risk import get_risk_manager
from app.news.sentiment import get_sentiment_analyzer

logger = setup_logger("decision_engine")


class DecisionEngine:
    """Engine that makes trading decisions using AI"""
    
    def __init__(self):
        self.config = get_config()
        self.gemini = get_gemini_client()
        self.mt5 = get_mt5_client()
        self.data = get_data_provider()
        self.portfolio = get_portfolio_manager()
        self.risk = get_risk_manager()
        self.sentiment = get_sentiment_analyzer()
    
    def make_decision(
        self,
        symbol: str,
        timeframe: str,
        technical_signal: str,
        indicators: Dict[str, Any]
    ) -> Tuple[Optional[TradingDecision], Optional[str], Optional[str]]:
        """
        Make trading decision using AI
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe
            technical_signal: Base technical signal
            indicators: Technical indicators
        
        Returns:
            Tuple of (decision, prompt_hash, error_message)
        """
        try:
            # Get account state
            account_info = self.mt5.get_account_info()
            if not account_info:
                return None, None, "Cannot get account info"
            
            # Get current tick
            tick = self.data.get_current_tick(symbol)
            if not tick:
                return None, None, f"Cannot get current tick for {symbol}"
            
            current_price = (tick.get('bid', 0) + tick.get('ask', 0)) / 2
            spread_pips = self.data.get_spread_pips(symbol) or 0
            
            # Build market snapshot
            market_snapshot = {
                'current_price': current_price,
                'bid': tick.get('bid', 0),
                'ask': tick.get('ask', 0),
                'spread_pips': spread_pips,
                'atr': indicators.get('atr', 0),
            }
            
            # Build account state
            account_state = {
                'equity': account_info.get('equity', 0),
                'balance': account_info.get('balance', 0),
                'open_positions_count': self.portfolio.get_open_positions_count(),
                'unrealized_pnl': self.portfolio.get_unrealized_pnl(),
            }
            
            # Get news sentiment
            news_sentiment = None
            try:
                sentiment_result = self.sentiment.get_sentiment(symbol)
                if sentiment_result:
                    news_sentiment = {
                        'score': sentiment_result.get('score', 0.0),
                        'summary': sentiment_result.get('summary', ''),
                        'headlines': sentiment_result.get('headlines', []),
                    }
            except Exception as e:
                logger.warning(f"Error getting news sentiment: {e}")
            
            # Build risk constraints
            risk_constraints = {
                'risk_per_trade_pct': self.risk.risk_per_trade_pct,
                'max_daily_loss_pct': self.risk.max_daily_loss_pct,
                'max_drawdown_pct': self.risk.max_drawdown_pct,
                'max_positions': self.risk.max_positions,
                'max_spread_pips': self.risk.max_spread_pips,
            }
            
            # Get current positions
            current_positions = self.portfolio.get_open_positions()
            positions_data = [
                {
                    'symbol': p.get('symbol', ''),
                    'type': 'BUY' if p.get('type', 0) == 0 else 'SELL',
                    'volume': p.get('volume', 0),
                    'profit': p.get('profit', 0),
                }
                for p in current_positions
            ]
            
            # Build prompts
            system_prompt = build_system_prompt()
            user_prompt = build_user_prompt(
                symbol=symbol,
                timeframe=timeframe,
                market_snapshot=market_snapshot,
                account_state=account_state,
                technical_signal=technical_signal,
                indicators=indicators,
                news_sentiment=news_sentiment,
                risk_constraints=risk_constraints,
                current_positions=positions_data
            )
            
            # Generate prompt hash
            prompt_hash = hashlib.md5(
                f"{system_prompt}{user_prompt}".encode()
            ).hexdigest()
            
            # Call Gemini
            logger.info(f"Requesting AI decision for {symbol} {timeframe}")
            gemini_response = self.gemini.generate_content(
                system_prompt, 
                user_prompt,
                use_cache=False  # Don't cache for live decisions
            )
            
            if gemini_response is None:
                return None, prompt_hash, "Gemini API returned no response"
            
            # Validate and parse response
            try:
                decision = TradingDecision(**gemini_response)
                
                # Additional validation
                if decision.action in ["BUY", "SELL"]:
                    if decision.order is None:
                        return None, prompt_hash, "Order details missing for BUY/SELL action"
                    
                    # Check if decision is valid for execution
                    if not decision.is_valid_for_execution(
                        min_confidence=self.config.ai.min_confidence_threshold
                    ):
                        logger.info(
                            f"Decision rejected: confidence={decision.confidence:.2f}, "
                            f"risk_ok={decision.risk_ok}"
                        )
                        # Override to HOLD if invalid
                        decision.action = "HOLD"
                        decision.risk_ok = False
                
                logger.info(
                    f"AI Decision: {decision.action} {symbol} "
                    f"(confidence={decision.confidence:.2f}, risk_ok={decision.risk_ok})"
                )
                
                return decision, prompt_hash, None
                
            except Exception as e:
                logger.error(f"Failed to validate Gemini response: {e}")
                logger.error(f"Response: {gemini_response}")
                return None, prompt_hash, f"Invalid response schema: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error in decision engine: {e}", exc_info=True)
            return None, None, str(e)
