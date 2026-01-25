"""News sentiment analysis using Gemini"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
from app.news.provider_base import NewsProvider
from app.news.provider_stub import StubNewsProvider
from app.news.provider_newsapi import NewsAPIProvider
from app.ai.gemini_client import get_gemini_client
from app.core.config import get_config
from app.core.logger import setup_logger

logger = setup_logger("sentiment")


class SentimentAnalyzer:
    """Analyzes news sentiment using Gemini"""
    
    def __init__(self):
        self.config = get_config()
        self.gemini = get_gemini_client()
        
        # Initialize news provider
        if self.config.news.provider == "newsapi" and self.config.news.news_api_key:
            provider_instance: NewsProvider = NewsAPIProvider()
        else:
            provider_instance = StubNewsProvider()
        
        self.provider = provider_instance
        
        self.cache_ttl_minutes = self.config.news.cache_minutes
        self._cache: Dict[str, tuple] = {}  # key -> (result, timestamp)
    
    def get_sentiment(
        self,
        symbol: str,
        hours_back: int = 24
    ) -> Optional[Dict[str, Any]]:
        """
        Get sentiment analysis for symbol
        
        Args:
            symbol: Trading symbol
            hours_back: Hours to look back for news
        
        Returns:
            Dict with keys: score (-1 to +1), summary, headlines
        """
        cache_key = f"{symbol}_{hours_back}"
        now = datetime.now()
        
        # Check cache
        if cache_key in self._cache:
            result, cache_time = self._cache[cache_key]
            if (now - cache_time).total_seconds() < (self.cache_ttl_minutes * 60):
                return result
        
        # Fetch news
        if not self.provider.is_available():
            logger.warning("News provider not available")
            return None
        
        news_articles = self.provider.fetch_news(symbol, hours_back, max_results=10)
        
        if not news_articles:
            logger.debug(f"No news found for {symbol}")
            return {
                "score": 0.0,
                "summary": "No recent news available",
                "headlines": [],
            }
        
        # Analyze sentiment using Gemini
        sentiment_result = self._analyze_with_gemini(symbol, news_articles)
        
        # Cache result
        if sentiment_result:
            self._cache[cache_key] = (sentiment_result, now)
        
        return sentiment_result
    
    def _analyze_with_gemini(
        self,
        symbol: str,
        articles: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Analyze sentiment using Gemini"""
        try:
            # Build prompt
            headlines = [a.get("title", "") for a in articles[:5]]
            descriptions = [a.get("description", "") for a in articles[:5]]
            
            prompt = f"""Analyze the sentiment of the following Forex news for {symbol}:

Headlines:
{chr(10).join(f"- {h}" for h in headlines if h)}

Descriptions:
{chr(10).join(f"- {d}" for d in descriptions if d)}

Provide a JSON response with:
{{
  "score": -1.0 to 1.0 (negative = bearish, positive = bullish, 0 = neutral),
  "summary": "Brief summary of overall sentiment",
  "confidence": 0.0 to 1.0
}}

Be concise and focus on market impact."""
            
            response = self.gemini.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.5,
                    "max_output_tokens": 256,
                }
            )
            
            # Parse response
            response_text = response.text.strip()
            
            # Extract JSON
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            import json
            result = json.loads(response_text)
            
            # Validate and format
            score = float(result.get("score", 0.0))
            score = max(-1.0, min(1.0, score))  # Clamp to [-1, 1]
            
            return {
                "score": score,
                "summary": result.get("summary", "No summary available"),
                "headlines": headlines,
                "confidence": float(result.get("confidence", 0.5)),
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment with Gemini: {e}", exc_info=True)
            return {
                "score": 0.0,
                "summary": "Sentiment analysis failed",
                "headlines": [a.get("title", "") for a in articles[:3]],
            }
    
    def clear_cache(self):
        """Clear sentiment cache"""
        self._cache.clear()
        logger.debug("Sentiment cache cleared")


# Global sentiment analyzer instance
_sentiment_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get global sentiment analyzer instance"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer
