"""NewsAPI provider for real news"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.news.provider_base import NewsProvider
from app.core.config import get_config
from app.core.logger import setup_logger

logger = setup_logger("news_newsapi")


class NewsAPIProvider(NewsProvider):
    """NewsAPI.org provider"""
    
    def __init__(self):
        self.config = get_config()
        self.api_key = self.config.news.news_api_key
        self.base_url = "https://newsapi.org/v2"
        self._available = self.api_key is not None and len(self.api_key) > 0
    
    def fetch_news(
        self,
        symbol: str,
        hours_back: int = 24,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Fetch news from NewsAPI"""
        if not self.is_available():
            logger.warning("NewsAPI not available (missing API key)")
            return []
        
        try:
            # Extract currencies from symbol
            base_currency, quote_currency = self.extract_currency_from_symbol(symbol)
            if not base_currency or not quote_currency:
                logger.warning(f"Cannot extract currencies from {symbol}")
                return []
            
            # Build query (search for both currencies)
            query = f"{base_currency} {quote_currency} forex"
            
            # Calculate time range
            to_time = datetime.now()
            from_time = to_time - timedelta(hours=hours_back)
            
            # Make API request
            url = f"{self.base_url}/everything"
            params = {
                "q": query,
                "apiKey": self.api_key,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": max_results,
                "from": from_time.isoformat(),
                "to": to_time.isoformat(),
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            # Parse articles
            articles = data.get("articles", [])
            news_list = []
            
            for article in articles[:max_results]:
                try:
                    published_str = article.get("publishedAt", "")
                    published_at = datetime.fromisoformat(
                        published_str.replace("Z", "+00:00")
                    ) if published_str else datetime.now()
                    
                    news_list.append({
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "url": article.get("url", ""),
                        "published_at": published_at,
                        "source": article.get("source", {}).get("name", "Unknown"),
                    })
                except Exception as e:
                    logger.warning(f"Error parsing article: {e}")
                    continue
            
            logger.info(f"Fetched {len(news_list)} news articles for {symbol}")
            return news_list
            
        except Exception as e:
            logger.error(f"Error fetching news from NewsAPI: {e}", exc_info=True)
            return []
    
    def is_available(self) -> bool:
        """Check if NewsAPI is available"""
        return self._available
