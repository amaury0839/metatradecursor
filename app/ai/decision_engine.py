"""Decision engine that combines technical signals with AI decisions"""

import hashlib
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from app.ai.gemini_client import get_gemini_client
from app.ai.schemas import TradingDecision, neutral_decision
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
            # Use forex max spread as default for display (crypto uses higher limits)
            risk_constraints = {
                'risk_per_trade_pct': self.risk.risk_per_trade_pct,
                'max_daily_loss_pct': self.risk.max_daily_loss_pct,
                'max_drawdown_pct': self.risk.max_drawdown_pct,
                'max_positions': self.risk.max_positions,
                'max_spread_pips': self.risk.FOREX_MAX_SPREAD_PIPS,  # Display forex limit (crypto uses higher)
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

            # If technical layer already has a decisive signal, skip Gemini entirely
            if technical_signal in ["BUY", "SELL"]:
                logger.info(
                    f"Bypassing Gemini for {symbol} {timeframe}: technical signal={technical_signal}"
                )
                decision = self._build_technical_decision(
                    symbol=symbol,
                    timeframe=timeframe,
                    action=technical_signal,
                    indicators=indicators,
                    current_price=current_price,
                )
                return decision, None, None
            
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
            
            # Fallback to technical signal if AI unavailable
            if gemini_response is None:
                logger.warning(f"AI unavailable, returning neutral decision for {symbol}")
                return neutral_decision(symbol, timeframe), prompt_hash, "ai_unavailable"
            
            # Validate and parse response
            try:
                # Ensure required fields exist even when Gemini returns partial/fallback payloads
                gemini_response.setdefault('symbol', symbol)
                gemini_response.setdefault('timeframe', timeframe)

                # Ensure reasoning exists (convert from reason list if needed)
                if 'reasoning' not in gemini_response or not gemini_response['reasoning']:
                    reasons = gemini_response.get('reason', [])
                    gemini_response['reasoning'] = '. '.join(reasons) if reasons else "No specific reasoning provided"
                
                # Ensure other defaults exist
                gemini_response.setdefault('market_bias', 'neutral')
                gemini_response.setdefault('sources', [])
                
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

    def _build_technical_decision(
        self,
        symbol: str,
        timeframe: str,
        action: str,
        indicators: Dict[str, Any],
        current_price: float,
    ) -> TradingDecision:
        """Create a TradingDecision purely from technical data, sizing the order."""
        decision = TradingDecision(
            action=action,
            confidence=0.6,
            symbol=symbol,
            timeframe=timeframe,
            reasoning="Technical signal strong enough; AI context skipped.",
            market_bias="neutral",
            risk_ok=True,
            sources=["technical"],
        )

        if action in ["BUY", "SELL"]:
            account_info = self.mt5.get_account_info()
            equity = account_info.get("equity", 1000) if account_info else 1000
            risk_amount = equity * (min(self.risk.risk_per_trade_pct, self.risk.max_trade_risk_pct) / 100)

            # Usar ATR para calcular stops válidos
            atr = float(indicators.get("atr", 0) or 0)
            if atr <= 0:
                # Fallback: usar un ATR por defecto basado en el precio
                atr = current_price * 0.01
            
            # NUEVA FUNCIÓN: Calcular SL/TP válidos automáticamente
            sl_price, tp_price = self.risk.compute_valid_stops(
                symbol=symbol,
                entry_price=current_price,
                atr=atr,
                direction=action
            )
            
            # Validar stops antes de continuar
            valid, error_msg = self.risk.validate_stops(
                symbol=symbol,
                price=current_price,
                sl=sl_price,
                tp=tp_price,
                direction=action
            )
            
            if not valid:
                logger.warning(f"Invalid stops for {symbol}: {error_msg}. Forcing HOLD.")
                decision.action = "HOLD"
                decision.risk_ok = False
                decision.reasoning = f"Stops validation failed: {error_msg}"
                return decision

            # Position sizing, then cap by risk/margin and normalize
            volume = self.risk.calculate_position_size(
                symbol=symbol,
                entry_price=current_price,
                stop_loss_price=sl_price,
                risk_amount=risk_amount,
            )
            if volume > 0:
                volume = self.risk.cap_volume_by_risk(
                    symbol=symbol,
                    entry_price=current_price,
                    stop_loss_price=sl_price,
                    requested_volume=volume,
                )
                volume = self.risk.normalize_volume(symbol, volume)

            if volume <= 0:
                # No sizing possible -> force HOLD to avoid invalid orders
                decision.action = "HOLD"
                decision.risk_ok = False
                decision.reasoning = "Sizing returned 0; holding to avoid invalid order."
                decision.order = None
                return decision

            from app.ai.schemas import OrderDetails

            decision.order = OrderDetails(
                volume_lots=volume,
                sl_price=sl_price,
                tp_price=tp_price,
            )

        return decision


# Global instance
_decision_engine: Optional[DecisionEngine] = None


def get_decision_engine() -> DecisionEngine:
    """Get global decision engine instance"""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine
