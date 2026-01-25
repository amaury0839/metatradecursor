"""Stub news provider for testing/development"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.news.provider_base import NewsProvider
from app.core.logger import setup_logger

logger = setup_logger("news_stub")


class StubNewsProvider(NewsProvider):
    """Stub news provider that returns mock data"""
    
    def __init__(self):
        self._mock_news = [
            {
                "title": "Central Bank Policy Update",
                "description": "Market analysts expect continued monetary policy support.",
                "url": "https://example.com/news/1",
                "published_at": datetime.now() - timedelta(hours=2),
                "source": "Mock News",
            },
            {
                "title": "Economic Data Release",
                "description": "Latest economic indicators show mixed signals.",
                "url": "https://example.com/news/2",
                "published_at": datetime.now() - timedelta(hours=5),
                "source": "Mock News",
            },
            {
                "title": "Market Volatility Alert",
                "description": "Traders monitoring key support and resistance levels.",
                "url": "https://example.com/news/3",
                "published_at": datetime.now() - timedelta(hours=8),
                "source": "Mock News",
            },
        ]
    
    def fetch_news(
        self,
        symbol: str,
        hours_back: int = 24,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Return mock news"""
        logger.debug(f"Stub provider: returning mock news for {symbol}")
        return self._mock_news[:max_results]
    
    def is_available(self) -> bool:
        """Stub provider is always available"""
        return True
