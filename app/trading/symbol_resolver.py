"""Symbol Resolver - maps symbol names and handles missing symbols in MT5"""

from typing import Optional, Dict, List
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client

logger = setup_logger("symbol_resolver")


class SymbolResolver:
    """
    Resolves symbol names and finds alternatives when unavailable.
    
    Brokers may have symbols with different naming conventions:
    - DOGEUSD vs DOGUSD vs DOGEUSD.a
    - AVAXUSD vs AVAXUSD.a vs AVAX
    - etc.
    """
    
    # Symbol mapping cache (symbol → actual_symbol_in_mt5)
    SYMBOL_CACHE = {}
    
    # Known alternative names for each base symbol
    KNOWN_ALTERNATIVES = {
        "DOGEUSD": ["DOGUSD", "DOGEUSD.a", "DOGE/USD"],
        "AVAXUSD": ["AVAXUSD.a", "AVAX", "AVAX/USD"],
        "SHIB": ["SHIBUSD", "SHIBUSD.a", "SHIB/USD"],
        "LINK": ["LINKUSD", "LINKUSD.a", "LINK/USD"],
        "UNI": ["UNIUSD", "UNIUSD.a", "UNI/USD"],
        "MATIC": ["MATICUSD", "MATICUSD.a", "MATIC/USD"],
    }
    
    def __init__(self):
        self.mt5 = get_mt5_client()
    
    def resolve_symbol(self, symbol: str) -> Optional[str]:
        """
        Resolve symbol name to actual MT5 symbol.
        
        Tries in order:
        1. Direct symbol (cached if successful)
        2. Known alternatives
        3. Pattern matching (* wildcards)
        4. Return None if not found
        
        Args:
            symbol: Requested symbol name
        
        Returns:
            Actual MT5 symbol name or None if not available
        """
        # Check cache first
        if symbol in self.SYMBOL_CACHE:
            cached = self.SYMBOL_CACHE[symbol]
            if cached is None:
                return None  # Known to be missing
            logger.debug(f"Symbol cache hit: {symbol} → {cached}")
            return cached
        
        # Try direct symbol
        if self._symbol_exists(symbol):
            self.SYMBOL_CACHE[symbol] = symbol
            logger.info(f"✅ Resolved {symbol} (direct match)")
            return symbol
        
        # Try known alternatives
        alternatives = self.KNOWN_ALTERNATIVES.get(symbol, [])
        for alt in alternatives:
            if self._symbol_exists(alt):
                self.SYMBOL_CACHE[symbol] = alt
                logger.info(f"✅ Resolved {symbol} → {alt} (alternative)")
                return alt
        
        # Try pattern matching
        base = symbol.rstrip("0123456789.")  # Remove numbers and dots
        matched = self._find_symbol_by_pattern(base)
        if matched:
            self.SYMBOL_CACHE[symbol] = matched
            logger.info(f"✅ Resolved {symbol} → {matched} (pattern match)")
            return matched
        
        # Not found
        self.SYMBOL_CACHE[symbol] = None
        logger.warning(f"❌ Symbol {symbol} not found in MT5 (checked {len(alternatives)} alternatives)")
        return None
    
    def _symbol_exists(self, symbol: str) -> bool:
        """Check if symbol exists in MT5"""
        try:
            info = self.mt5.get_symbol_info(symbol)
            return info is not None
        except:
            return False
    
    def _find_symbol_by_pattern(self, base_pattern: str) -> Optional[str]:
        """
        Find symbol by pattern matching.
        
        Example: base_pattern="DOGE" matches "DOGEUSD", "DOGUSD", etc.
        
        Args:
            base_pattern: Base symbol pattern
        
        Returns:
            Matching symbol or None
        """
        try:
            # Get all available symbols (this might be expensive)
            all_symbols = self.mt5.get_all_symbols()
            if not all_symbols:
                return None
            
            # Find symbols that contain the pattern
            matches = [s for s in all_symbols if base_pattern.upper() in s.upper()]
            
            # Prefer exact-ish matches (same length or close)
            if matches:
                # Sort by length and prefer ones ending with USD
                matches.sort(
                    key=lambda x: (
                        abs(len(x) - len(base_pattern)),  # Length similarity
                        0 if x.endswith("USD") else 1,     # USD suffix preference
                        x  # Alphabetical fallback
                    )
                )
                logger.debug(f"Pattern {base_pattern} matches: {matches[:3]}")
                return matches[0]
            
            return None
        except Exception as e:
            logger.warning(f"Error finding symbol by pattern {base_pattern}: {e}")
            return None
    
    def get_all_symbols(self) -> List[str]:
        """Get all available symbols from MT5"""
        try:
            return self.mt5.get_all_symbols() or []
        except:
            return []
    
    def validate_symbol_list(self, symbols: List[str]) -> Dict[str, Optional[str]]:
        """
        Validate a list of symbols and resolve unavailable ones.
        
        Args:
            symbols: List of requested symbols
        
        Returns:
            Dict mapping original symbol → resolved symbol (None if unavailable)
        """
        results = {}
        for symbol in symbols:
            resolved = self.resolve_symbol(symbol)
            results[symbol] = resolved
            
            if resolved is None:
                logger.warning(f"⚠️ {symbol} unavailable - will skip in trading")
            else:
                logger.info(f"✅ {symbol} → {resolved}")
        
        return results
    
    def suggest_alternative(self, symbol: str) -> Optional[str]:
        """
        Suggest an alternative symbol if the requested one is unavailable.
        
        Args:
            symbol: Unavailable symbol
        
        Returns:
            Suggested alternative symbol or None
        """
        # Check known alternatives first
        if symbol in self.KNOWN_ALTERNATIVES:
            for alt in self.KNOWN_ALTERNATIVES[symbol]:
                if self._symbol_exists(alt):
                    logger.info(f"Suggesting {alt} as alternative to {symbol}")
                    return alt
        
        # Try to find similar symbols
        base = symbol.rstrip("0123456789.")
        for known_base, alts in self.KNOWN_ALTERNATIVES.items():
            if base.upper() in known_base.upper():
                for alt in alts:
                    if self._symbol_exists(alt):
                        logger.info(f"Suggesting {alt} as alternative to {symbol}")
                        return alt
        
        return None


# Global instance
_resolver: Optional[SymbolResolver] = None


def get_symbol_resolver() -> SymbolResolver:
    """Get global symbol resolver instance"""
    global _resolver
    if _resolver is None:
        _resolver = SymbolResolver()
    return _resolver
