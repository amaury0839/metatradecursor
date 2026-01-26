"""News sentiment analysis (lightweight, no Gemini)"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
from app.news.provider_base import NewsProvider
from app.news.provider_stub import StubNewsProvider
from app.news.provider_newsapi import NewsAPIProvider
from app.core.config import get_config
from app.core.logger import setup_logger

logger = setup_logger("sentiment")


class SentimentAnalyzer:
    """Analyzes news sentiment using Gemini"""
    
    def __init__(self):
        self.config = get_config()
        
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
        
        # Lightweight sentiment: neutral default; simple headline-based hint
        sentiment_result = self._analyze_light(symbol, news_articles)
        self._cache[cache_key] = (sentiment_result, now)
        return sentiment_result
    
    def _analyze_light(self, symbol: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Lightweight sentiment without Gemini; neutral baseline."""
        headlines = [a.get("title", "") for a in articles[:5] if a.get("title")]
        summary = "Sentiment analysis unavailable" if not headlines else "Neutral sentiment (AI disabled)"
        return {
            "score": 0.0,
            "summary": summary,
            "headlines": headlines,
            "confidence": 0.0,
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
