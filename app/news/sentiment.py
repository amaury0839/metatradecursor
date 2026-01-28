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
    
    # 🔧 Symbol mapping: map trading symbols to news query terms
    SYMBOL_MAPPING = {
        'BTCUSD': ['BTC', 'Bitcoin'],
        'ETHUSD': ['ETH', 'Ethereum'],
        'BNBUSD': ['BNB', 'Binance'],
        'XRPUSD': ['XRP', 'Ripple'],
        'ADAUSD': ['ADA', 'Cardano'],
        'DOGEUSD': ['DOGE', 'Dogecoin'],
        'SOLUSD': ['SOL', 'Solana'],
        'DOTUSD': ['DOT', 'Polkadot'],
        'LTCUSD': ['LTC', 'Litecoin'],
        'AVAXUSD': ['AVAX', 'Avalanche'],
        'MATICUSD': ['MATIC', 'Polygon'],
        'LINKUSD': ['LINK', 'Chainlink'],
        'UNIUSD': ['UNI', 'Uniswap'],
        'FTMUSD': ['FTM', 'Fantom'],
        'ARBUSD': ['ARB', 'Arbitrum'],
        'EURUSD': ['EUR', 'Euro', 'European'],
        'GBPUSD': ['GBP', 'Pound', 'UK'],
        'USDJPY': ['JPY', 'Yen', 'Japan'],
        'AUDUSD': ['AUD', 'Australian', 'Australia'],
        'USDCAD': ['CAD', 'Canadian', 'Canada'],
        'USDCHF': ['CHF', 'Swiss', 'Switzerland'],
    }
    
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
    
    def _get_query_terms(self, symbol: str) -> List[str]:
        """Get news query terms for symbol with mapping"""
        return self.SYMBOL_MAPPING.get(symbol, [symbol, symbol[:3].upper()])
    
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
            Dict with keys: score (-1 to +1), summary, headlines, status
            
        🔧 FIXED: Log cache hit/miss, handle None vs 0.0
        """
        cache_key = f"{symbol}_{hours_back}"
        now = datetime.now()
        
        # Check cache
        if cache_key in self._cache:
            result, cache_time = self._cache[cache_key]
            cache_age = (now - cache_time).total_seconds() / 60
            if cache_age < self.cache_ttl_minutes:
                logger.info(f"Sentiment: CACHE HIT {symbol} (age={cache_age:.1f}m, score={result.get('score', 0.0)})")
                return result
            else:
                logger.info(f"Sentiment: CACHE EXPIRED {symbol} (age={cache_age:.1f}m > {self.cache_ttl_minutes}m)")
                del self._cache[cache_key]
        
        logger.info(f"Sentiment: CACHE MISS {symbol}, fetching fresh")
        
        # Fetch news
        if not self.provider.is_available():
            logger.warning(f"Sentiment: Provider not available for {symbol}")
            return {
                "score": None,  # Unknown, not neutral
                "summary": "Provider unavailable",
                "headlines": [],
                "status": "provider_unavailable"
            }
        
        query_terms = self._get_query_terms(symbol)
        news_articles = self.provider.fetch_news(symbol, hours_back, max_results=10)
        
        if not news_articles:
            logger.info(f"Sentiment: No news found for {symbol} (query terms: {query_terms})")
            return {
                "score": None,  # Unknown
                "summary": f"No news available for {symbol}",
                "headlines": [],
                "status": "no_news"
            }
        
        # Lightweight sentiment: neutral default; simple headline-based hint
        sentiment_result = self._analyze_light(symbol, news_articles)
        self._cache[cache_key] = (sentiment_result, now)
        logger.info(f"Sentiment: Analyzed {len(news_articles)} articles for {symbol}, score={sentiment_result.get('score', None)}")
        return sentiment_result
    
    def _analyze_light(self, symbol: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Lightweight sentiment without Gemini; neutral baseline."""
        headlines = [a.get("title", "") for a in articles[:5] if a.get("title")]
        summary = "Sentiment analysis unavailable" if not headlines else "Neutral sentiment (AI disabled)"
        return {
            "score": 0.0,  # 0.0 = neutral (not unknown)
            "summary": summary,
            "headlines": headlines,
            "confidence": 0.0,
            "status": "neutral_default"
        }
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
