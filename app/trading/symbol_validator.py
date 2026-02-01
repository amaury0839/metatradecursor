"""
Symbol Validator
Automatically validates and filters available trading symbols
"""
import MetaTrader5 as mt5
from typing import List, Dict
from app.core.logger import setup_logger

logger = setup_logger("symbol_validator")


class SymbolValidator:
    """Validates trading symbols against MT5"""
    
    def __init__(self):
        self.valid_symbols = []
        self.invalid_symbols = []
        self.symbol_details = {}
    
    def validate_symbols(self, candidates: List[str], skip_list: List[str] = None) -> List[str]:
        """
        Validate candidate symbols against MT5
        
        Args:
            candidates: List of symbol names to test
            skip_list: Symbols to explicitly skip
        
        Returns:
            List of valid, tradeable symbols
        """
        skip_list = skip_list or []
        
        if not mt5.initialize():
            logger.error("❌ Failed to initialize MT5 for symbol validation")
            # Return candidates as fallback
            return [s for s in candidates if s not in skip_list]
        
        logger.info(f"🔍 Validating {len(candidates)} candidate symbols...")
        
        for symbol in candidates:
            if symbol in skip_list:
                logger.debug(f"⏭️  {symbol} (skipped)")
                self.invalid_symbols.append(symbol)
                continue
            
            try:
                info = mt5.symbol_info(symbol)
                
                if info is None:
                    logger.debug(f"❌ {symbol} (not found)")
                    self.invalid_symbols.append(symbol)
                elif info.trade_mode == mt5.SYMBOL_TRADE_MODE_DISABLED:
                    logger.debug(f"❌ {symbol} (disabled)")
                    self.invalid_symbols.append(symbol)
                else:
                    logger.info(f"✅ {symbol}")
                    self.valid_symbols.append(symbol)
                    self.symbol_details[symbol] = {
                        'bid': info.bid,
                        'ask': info.ask,
                        'digits': info.digits,
                        'volume_min': info.volume_min,
                        'volume_max': info.volume_max,
                    }
            except Exception as e:
                logger.warning(f"⚠️  {symbol} (error: {e})")
                self.invalid_symbols.append(symbol)
        
        mt5.shutdown()
        
        logger.info(f"\n✅ Validation complete: {len(self.valid_symbols)} valid symbols")
        if self.invalid_symbols:
            logger.warning(f"❌ {len(self.invalid_symbols)} invalid symbols (will be skipped)")
        
        return self.valid_symbols
    
    def get_valid_symbols(self) -> List[str]:
        """Get list of validated symbols"""
        return self.valid_symbols
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """Get details for a validated symbol"""
        return self.symbol_details.get(symbol, {})


# Global instance
_validator = None


def get_symbol_validator() -> SymbolValidator:
    """Get or create global symbol validator instance"""
    global _validator
    if _validator is None:
        _validator = SymbolValidator()
    return _validator
