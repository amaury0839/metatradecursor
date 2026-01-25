"""Base class for news providers"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class NewsProvider(ABC):
    """Base class for news providers"""
    
    @abstractmethod
    def fetch_news(
        self,
        symbol: str,
        hours_back: int = 24,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch news articles for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            hours_back: How many hours back to search
            max_results: Maximum number of results
        
        Returns:
            List of news articles with keys: title, description, url, published_at, source
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass
    
    def extract_currency_from_symbol(self, symbol: str) -> tuple:
        """
        Extract base and quote currencies from symbol
        
        Args:
            symbol: Symbol like 'EURUSD'
        
        Returns:
            Tuple of (base_currency, quote_currency)
        """
        if len(symbol) == 6:
            return symbol[:3], symbol[3:]
        return None, None
