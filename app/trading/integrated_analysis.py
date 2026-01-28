"""Integrated analysis combining technical, sentiment, and AI indicators"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.trading.strategy import get_strategy
from app.news.sentiment import get_sentiment_analyzer
from app.core.logger import setup_logger
from app.core.config import get_config
from app.trading.market_status import get_market_status
from app.ai.smart_decision_router import make_smart_decision
from app.core.database import get_database_manager
from app.ai.enhanced_decision import get_enhanced_decision_engine

logger = setup_logger("integrated_analysis")


class NewsCache:
    """Simple news sentiment cache with 1-hour TTL"""
    
    def __init__(self, ttl_minutes: int = 60):
        self.ttl_minutes = ttl_minutes
        self._cache: Dict[str, tuple] = {}  # symbol -> (sentiment_data, timestamp)
    
    def get(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached sentiment or None if expired"""
        if symbol not in self._cache:
            return None
        
        data, timestamp = self._cache[symbol]
        age_minutes = (datetime.now() - timestamp).total_seconds() / 60
        
        if age_minutes > self.ttl_minutes:
            del self._cache[symbol]
            return None
        
        return data
    
    def set(self, symbol: str, data: Dict[str, Any]):
        """Cache sentiment data"""
        self._cache[symbol] = (data, datetime.now())
        logger.info(f"Cached news sentiment for {symbol}")
    
    def clear_expired(self):
        """Remove expired cache entries"""
        now = datetime.now()
        expired = []
        for symbol, (_, timestamp) in self._cache.items():
            age_minutes = (now - timestamp).total_seconds() / 60
            if age_minutes > self.ttl_minutes:
                expired.append(symbol)
        
        for symbol in expired:
            del self._cache[symbol]
            logger.debug(f"Cleared expired cache for {symbol}")


class IntegratedAnalyzer:
    """Combines technical, sentiment, and risk analysis"""
    
    def __init__(self):
        self.config = get_config()
        self.strategy = get_strategy()
        self.sentiment_analyzer = get_sentiment_analyzer()
        self.news_cache = NewsCache(ttl_minutes=240)  # Increased from 60m to 4 hours for better perf
        self.market_status = get_market_status()
        self.db = get_database_manager()  # Database manager
    
    def analyze_symbol(
        self,
        symbol: str,
        timeframe: str = "M15",
        use_enhanced_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Perform integrated analysis on symbol
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            use_enhanced_ai: Use enhanced AI decision engine (default True)
        
        Returns dict with keys:
        - technical: RSI, EMA, trend data
        - sentiment: news sentiment if available
        - ai_decision: AI trading decision (if available)
        - combined_score: integrated score (-1 to +1)
        - signal: BUY/SELL/HOLD recommendation
        - confidence: Overall confidence level
        """
        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "technical": None,
            "sentiment": None,
            "ai_decision": None,
            "combined_score": 0.0,
            "signal": "HOLD",
            "confidence": 0.0,
            "available_sources": []
        }
        
        # OPTIMIZATION: Skip market open check (saves 200ms per symbol)
        # Forex is open most of the time, and MT5 will reject trades if closed
        # This avoids expensive market_status checks
        # if not self.market_status.is_symbol_open(symbol):
        #     result["signal"] = "HOLD"
        #     result["confidence"] = 0.0
        #     result["available_sources"].append("MARKET_CLOSED")
        #     logger.info(f"{symbol} - mercado cerrado, se omite análisis")
        #     return result

        # 1. Get technical analysis
        try:
            signal_result = self.strategy.get_signal(symbol, timeframe)
            if signal_result and signal_result[0]:
                technical_signal, technical_data, technical_reason = signal_result
                result["technical"] = {
                    "signal": technical_signal,
                    "data": technical_data,
                    "reason": technical_reason
                }
                result["available_sources"].append("TECHNICAL")
                logger.info(f"{symbol} - Technical: {technical_signal} ({technical_reason})")
        except Exception as e:
            logger.warning(f"Technical analysis failed for {symbol}: {e}")
        
        # 2. Get sentiment analysis (with cache)
        try:
            sentiment = self.news_cache.get(symbol)
            
            if sentiment is None:
                # Not in cache, fetch new data
                sentiment = self.sentiment_analyzer.get_sentiment(symbol, hours_back=24)
                
                if sentiment and sentiment.get("score") is not None:
                    self.news_cache.set(symbol, sentiment)
                    result["available_sources"].append("SENTIMENT")
                    logger.info(
                        f"{symbol} - Sentiment: {sentiment['score']:.2f} "
                        f"({sentiment.get('summary', 'N/A')})"
                    )
            else:
                result["available_sources"].append("SENTIMENT")
                logger.info(f"{symbol} - Sentiment (cached): {sentiment.get('score', 0):.2f}")
            
            result["sentiment"] = sentiment
        except Exception as e:
            logger.warning(f"Sentiment analysis failed for {symbol}: {e}")
        
        # 3. Get AI decision (enhanced or simple)
        if use_enhanced_ai:
            try:
                ai_decision = make_smart_decision(
                    symbol=symbol,
                    timeframe=timeframe,
                    technical_data=result["technical"],
                    sentiment_data=result["sentiment"],
                    use_enhanced=True
                )
                
                if ai_decision:
                    result["ai_decision"] = {
                        "action": ai_decision.action,
                        "confidence": ai_decision.confidence,
                        "reasoning": getattr(ai_decision, 'reasoning', '. '.join(getattr(ai_decision, 'reason', []))),
                        "risk_ok": getattr(ai_decision, 'risk_ok', True),
                        "stop_loss": getattr(ai_decision, 'stop_loss', None),
                        "take_profit": getattr(ai_decision, 'take_profit', None)
                    }
                    result["available_sources"].append("AI_ENHANCED")
                    logger.info(
                        f"{symbol} - AI Decision: {ai_decision.action} "
                        f"(confidence={ai_decision.confidence:.2f})"
                    )
            except Exception as e:
                logger.warning(f"AI decision failed for {symbol}: {e}")
        
        # 4. Calculate combined score using enhanced engine (AI as score, no veto)
        try:
            engine = get_enhanced_decision_engine()
            tech_sig = (result["technical"] or {}).get("signal", "HOLD")
            ai_action = (result["ai_decision"] or {}).get("action", "HOLD")
            ai_conf = float((result["ai_decision"] or {}).get("confidence", 0.0) or 0.0)
            
            # 🔧 FIXED: Handle None vs 0.0 sentiment
            sent_score = 0.0
            if result["sentiment"] and result["sentiment"].get("score") is not None:
                sent_score = float(result["sentiment"]["score"])
            else:
                # Unknown sentiment → don't contribute to weighting
                logger.info(f"{symbol}: Sentiment unknown, using neutral (0.0)")
                sent_score = 0.0
            
            final_score_abs, action = engine.calculate_combined_score(
                technical_signal=tech_sig,
                ai_confidence=ai_conf,
                ai_action=ai_action,
                sentiment_score=sent_score,
            )
            # Store signed combined score for UI (-1..+1)
            signed = final_score_abs if action == "BUY" else (-final_score_abs if action == "SELL" else 0.0)
            result["combined_score"] = signed
            result["signal"] = action
            result["confidence"] = final_score_abs
        except Exception as e:
            logger.warning(f"Enhanced scoring failed, falling back: {e}")
            combined_score = self._calculate_combined_score(result)
            result["combined_score"] = combined_score
            result["signal"], result["confidence"] = self._get_integrated_signal(
                result, combined_score
            )
        
        # 5. Save analysis to database
        try:
            result["timeframe"] = timeframe
            analysis_id = self.db.save_analysis(result)
            result["analysis_id"] = analysis_id
        except Exception as e:
            logger.warning(f"Failed to save analysis to database: {e}")
        
        return result
    
    def _calculate_combined_score(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate integrated score from available sources
        Score range: -1.0 (strong SELL) to +1.0 (strong BUY)
        """
        scores = []
        weights = []
        
        # Technical score (weight: 0.7)
        if analysis["technical"]:
            tech_signal = analysis["technical"]["signal"]
            if tech_signal == "BUY":
                scores.append(1.0)
                weights.append(0.7)
            elif tech_signal == "SELL":
                scores.append(-1.0)
                weights.append(0.7)
            elif tech_signal == "HOLD":
                scores.append(0.0)
                weights.append(0.7)
        
        # Sentiment score (weight: 0.3)
        if analysis["sentiment"] and analysis["sentiment"].get("score") is not None:
            sentiment_score = analysis["sentiment"]["score"]  # Already -1 to +1
            scores.append(sentiment_score)
            weights.append(0.3)
        
        # Calculate weighted average
        if not scores:
            return 0.0
        
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0
        
        combined = sum(s * w for s, w in zip(scores, weights)) / total_weight
        return round(combined, 2)
    
    def _get_integrated_signal(
        self, 
        analysis: Dict[str, Any], 
        combined_score: float
    ) -> tuple:
        """
        Get signal and confidence from combined score and AI decision
        
        Returns: (signal, confidence)
        """
        # If AI explicitly says risk is not OK (blocked/unavailable), do not open new trades
        if analysis.get("ai_decision") and analysis["ai_decision"].get("risk_ok") is False:
            logger.info("AI layer unavailable/blocked; forcing HOLD to avoid new entries")
            return "HOLD", 0.05

        # 🔧 FIX: Signal MUST MASTER - Priority 1: If technical says HOLD, we HOLD
        if analysis["technical"]:
            tech_signal = analysis["technical"]["signal"]
            
            # If technical says HOLD, we HOLD (no matter what AI says)
            if tech_signal == "HOLD":
                logger.info(f"Technical signal is HOLD → forcing HOLD (signal masters)")
                return "HOLD", 0.05
            
            # Tech signal is BUY or SELL, calculate confidence
            tech_conf = (analysis["technical"].get("confidence", 0.0) or 0.0)
            ai_conf = 0.0
            if analysis.get("ai_decision"):
                ai_conf = analysis["ai_decision"].get("confidence", 0.0) or 0.0
            
            # Weighted confidence: 60% technical, 40% AI if available
            if analysis.get("ai_decision"):
                weighted_conf = 0.6 * tech_conf + 0.4 * ai_conf
            else:
                weighted_conf = tech_conf
            
            # Only BUY/SELL if confidence is strong enough (>= 0.7)
            if weighted_conf >= 0.7:
                logger.info(
                    f"Using technical signal: {tech_signal} (weighted_conf={weighted_conf:.2f})"
                )
                return tech_signal, weighted_conf
            else:
                logger.info(
                    f"Technical signal {tech_signal} but confidence too low ({weighted_conf:.2f} < 0.7), forcing HOLD"
                )
                return "HOLD", weighted_conf
        
        # Fallback: use combined score threshold (más agresivo)
        if combined_score > 0.2:
            return "BUY", min(combined_score + 0.2, 1.0)
        elif combined_score < -0.2:
            return "SELL", abs(min(combined_score - 0.2, -1.0))
        else:
            return "HOLD", 0.4
    
    def get_analysis_summary(self, symbol: str) -> str:
        """Get human-readable analysis summary"""
        analysis = self.analyze_symbol(symbol)
        
        summary = f"\n{'='*50}\n"
        summary += f"ANALYSIS: {symbol}\n"
        summary += f"{'='*50}\n"
        
        if analysis["technical"]:
            tech = analysis["technical"]
            summary += f"\n📊 TECHNICAL:\n"
            summary += f"  Signal: {tech['signal']}\n"
            summary += f"  Reason: {tech['reason']}\n"
            if tech['data']:
                for key, value in tech['data'].items():
                    summary += f"  {key}: {value}\n"
        
        if analysis["sentiment"]:
            sent = analysis["sentiment"]
            if sent.get("score") is not None:
                summary += f"\n📰 SENTIMENT:\n"
                summary += f"  Score: {sent['score']:.2f}\n"
                summary += f"  Summary: {sent.get('summary', 'N/A')}\n"
                if sent.get('headlines'):
                    summary += f"  Headlines: {len(sent['headlines'])} found\n"
        
        if analysis.get("ai_decision"):
            ai = analysis["ai_decision"]
            summary += f"\n🤖 AI DECISION:\n"
            summary += f"  Action: {ai['action']}\n"
            summary += f"  Confidence: {ai['confidence']:.1%}\n"
            summary += f"  Reasoning: {ai['reasoning'][:150]}...\n"
            if ai.get('stop_loss'):
                summary += f"  Stop Loss: {ai['stop_loss']}\n"
            if ai.get('take_profit'):
                summary += f"  Take Profit: {ai['take_profit']}\n"
        
        summary += f"\n{'─'*50}\n"
        summary += f"📈 COMBINED ANALYSIS:\n"
        summary += f"  Score: {analysis['combined_score']:.2f}\n"
        summary += f"  Signal: {analysis['signal']}\n"
        summary += f"  Confidence: {analysis['confidence']:.1%}\n"
        summary += f"  Sources: {', '.join(analysis['available_sources'])}\n"
        summary += f"{'='*50}\n"
        
        return summary


# Global instance
_analyzer: Optional[IntegratedAnalyzer] = None


def get_integrated_analyzer() -> IntegratedAnalyzer:
    """Get global analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = IntegratedAnalyzer()
    return _analyzer
