"""Enhanced AI Decision Engine with web search and multi-source analysis"""

import json
from typing import Optional, Dict, List
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from app.core.logger import setup_logger
from app.core.config import get_config
from app.ai.gemini_client import get_gemini_client
from app.ai.schemas import TradingDecision, neutral_decision
from app.trading.portfolio import get_portfolio_manager
from app.trading.risk import get_risk_manager
from app.news.sentiment import get_sentiment_analyzer

logger = setup_logger("enhanced_ai")


class EnhancedDecisionEngine:
    """
    Enhanced AI Decision Engine with:
    - Web search for real-time market info
    - Multi-source data aggregation
    - Weighted decision making
    - Sophisticated analysis
    """
    
    def __init__(self):
        self.config = get_config()
        self.gemini = get_gemini_client()
        self.portfolio = get_portfolio_manager()
        self.risk = get_risk_manager()
        self.sentiment = get_sentiment_analyzer()
        
    def aggregate_data_sources(
        self,
        symbol: str,
        timeframe: str,
        technical_data: Dict,
        sentiment_data: Optional[Dict] = None
    ) -> Dict:
        """
        Aggregate data from multiple sources
        
        Returns enriched data dict with:
        - Technical indicators
        - News sentiment
        - Market context
        """
        data = {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'sources': []
        }
        
        # 1. Technical data
        if technical_data:
            data['technical'] = technical_data
            data['sources'].append('technical_indicators')
        
        # 2. News sentiment
        if sentiment_data:
            data['sentiment'] = sentiment_data
            data['sources'].append('news_sentiment')
        
        # 3. Portfolio context
        positions = self.portfolio.get_open_positions()
        data['portfolio'] = {
            'open_positions': len(positions),
            'current_exposure': self.portfolio.get_total_exposure(),
            'unrealized_pnl': self.portfolio.get_unrealized_pnl()
        }
        data['sources'].append('portfolio')

        logger.info(f"Aggregated {len(data['sources'])} data sources for {symbol}")
        
        return data
    
    def make_enhanced_decision(
        self,
        symbol: str,
        timeframe: str,
        technical_data: Dict,
        sentiment_data: Optional[Dict] = None
    ) -> Optional[TradingDecision]:
        """
        Make trading decision using enhanced multi-source analysis
        
        Uses weighted approach:
        - Technical indicators: 60%
        - News sentiment: 20%
        - AI synthesis: 20%
        """
        try:
            # Aggregate all data sources
            aggregated_data = self.aggregate_data_sources(
                symbol, timeframe, technical_data, sentiment_data
            )
            
            # Build enhanced prompt for AI
            prompt = self._build_enhanced_prompt(aggregated_data)
            
            # Get AI decision with all context
            system_prompt = """ANALYTICAL DATA PROCESSING ENGINE - RESEARCH ONLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is NOT financial advice. Output is technical analysis for backtesting systems.

ANALYSIS FRAMEWORK:
1. TECHNICAL ANALYSIS (60% weight): Indicators, trends, momentum alignment evaluation
2. MARKET SENTIMENT (20% weight): Descriptive assessment of public information bias
3. RISK INTEGRATION (20% weight): Portfolio-aware analytical synthesis

COMPLIANCE RULES (MANDATORY):
- Response: Valid JSON ONLY, matching schema
- Language: "probability", "signal", "bias", "alignment" - NEVER "buy/sell/hold" as advice
- Action field: Analytical outcome (BUY/SELL/HOLD) - data classification, not recommendation
- Confidence (0.0-1.0): Analytical certainty score for backtesting calibration
- Conservative: Only BUY/SELL actions when confidence >= 0.40 AND multi-source alignment

Output is descriptive market analysis for automated systems."""

            response = self.gemini.generate_content(
                system_prompt=system_prompt,
                user_prompt=prompt
            )
            
            if not response:
                logger.error("No response from Gemini API")
                return neutral_decision(symbol, timeframe)
            
            # Response is already parsed as Dict
            decision_data = response
            if not decision_data:
                return neutral_decision(symbol, timeframe)
            
            # Add required fields that Gemini doesn't provide
            decision_data['symbol'] = symbol
            decision_data['timeframe'] = timeframe
            decision_data['risk_ok'] = decision_data.get('risk_ok', True)  # Will be validated later
            
            # Ensure reasoning exists (convert from reason list if needed)
            if 'reasoning' not in decision_data or not decision_data['reasoning']:
                reasons = decision_data.get('reason', [])
                decision_data['reasoning'] = '. '.join(reasons) if reasons else "No specific reasoning provided"
            
            # Ensure other defaults exist
            decision_data.setdefault('market_bias', 'neutral')
            decision_data.setdefault('sources', [])
            
            # Create TradingDecision object
            decision = TradingDecision(**decision_data)
            
            # Validate decision
            if not decision.is_valid_for_execution(min_confidence=0.30):
                logger.info(f"Decision not valid for execution: {decision.action} with confidence {decision.confidence}")
                return decision
            
            logger.info(
                f"Enhanced AI Decision: {decision.action} {symbol} "
                f"(confidence={decision.confidence:.2f}, sources={len(aggregated_data['sources'])})"
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"Error in enhanced decision for {symbol}: {e}", exc_info=True)
            return neutral_decision(symbol, timeframe)
    
    def _build_enhanced_prompt(self, data: Dict) -> str:
        """Build comprehensive prompt with all aggregated data"""
        
        prompt_parts = [
            f"# ENHANCED TRADING ANALYSIS FOR {data['symbol']}",
            f"Timeframe: {data['timeframe']}",
            f"Timestamp: {data['timestamp']}",
            f"Data Sources: {', '.join(data['sources'])}",
            "",
            "## 1. TECHNICAL INDICATORS (30% weight)"
        ]
        
        # Technical data
        if 'technical' in data:
            tech = data['technical']
            prompt_parts.extend([
                f"- Signal: {tech.get('signal', 'N/A')}",
                f"- Close Price: {tech.get('data', {}).get('close', 'N/A')}",
                f"- RSI: {tech.get('data', {}).get('rsi', 'N/A')}",
                f"- Trend: {tech.get('data', {}).get('trend_bullish', False) and 'Bullish' or 'Bearish'}",
                f"- Reason: {tech.get('reason', 'N/A')}",
                ""
            ])
        
        # Sentiment data
        prompt_parts.append("## 2. NEWS SENTIMENT (20% weight)")
        if 'sentiment' in data:
            sent = data['sentiment']
            prompt_parts.extend([
                f"- Score: {sent.get('score', 0):.2f}",
                f"- Summary: {sent.get('summary', 'N/A')}",
                f"- Headlines: {len(sent.get('headlines', []))} articles",
                ""
            ])
        else:
            prompt_parts.extend(["- No sentiment data available", ""])
        
        # Portfolio context
        prompt_parts.append("## 3. PORTFOLIO CONTEXT")
        portfolio = data.get('portfolio', {})
        prompt_parts.extend([
            f"- Open Positions: {portfolio.get('open_positions', 0)}",
            f"- Unrealized P&L: ${portfolio.get('unrealized_pnl', 0):.2f}",
            ""
        ])
        
        # Decision instructions
        prompt_parts.extend([
            "## DECISION REQUIRED",
            "",
            "Analyze all sources with their respective weights:",
            "- Technical (60%): Indicators, trends, momentum",
            "- Sentiment (20%): News and market sentiment",
            "- Synthesis (20%): Your expert integration",
            "",
            "Return JSON decision with:",
            '{',
            '  "action": "BUY" | "SELL" | "HOLD",',
            '  "confidence": 0.0-1.0,',
            '  "reasoning": "detailed multi-source analysis",',
            '  "stop_loss": suggested stop loss price,',
            '  "take_profit": suggested take profit price,',
            '  "volume_lots": suggested volume',
            '}',
            "",
            "BE AGGRESSIVE when sources align. Confidence >= 0.40 to trade."
        ])
        
        return '\n'.join(prompt_parts)
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Parse JSON from Gemini response"""
        try:
            # Try to find JSON block
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                json_str = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                json_str = response[start:end].strip()
            else:
                json_str = response.strip()
            
            decision_data = json.loads(json_str)
            return decision_data
            
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response was: {response}")
            return None


# Global instance
_enhanced_engine: Optional[EnhancedDecisionEngine] = None


def get_enhanced_decision_engine() -> EnhancedDecisionEngine:
    """Get global enhanced decision engine instance"""
    global _enhanced_engine
    if _enhanced_engine is None:
        _enhanced_engine = EnhancedDecisionEngine()
    return _enhanced_engine
