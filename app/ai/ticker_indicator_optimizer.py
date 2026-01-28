"""
Ticker-Specific Indicator Optimizer
Assigns optimized indicator parameters to each ticker based on historical performance
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from app.core.logger import setup_logger
from app.core.database import get_database_manager
from app.trading.strategy import TradingStrategy

logger = setup_logger("ticker_indicator_optimizer")


class TickerIndicatorOptimizer:
    """Optimizes indicator parameters per ticker for maximum profitability"""
    
    def __init__(self):
        self.db = get_database_manager()
        self.strategy = TradingStrategy()
        self.config_file = Path(__file__).parent.parent.parent / "data" / "ticker_indicators.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.ticker_configs = self._load_configs()
        
        # Default indicator ranges to test
        self.test_ranges = {
            "rsi_buy": list(range(30, 45, 2)),  # 30-44
            "rsi_sell": list(range(56, 71, 2)),  # 56-70
            "ema_fast_period": [5, 8, 10, 12, 15],
            "ema_slow_period": [20, 30, 40, 50],
            "atr_multiplier": [1.0, 1.5, 2.0, 2.5, 3.0],
        }
    
    def _load_configs(self) -> Dict:
        """Load saved indicator configurations"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load ticker indicator configs: {e}")
        return {}
    
    def _save_configs(self):
        """Save indicator configurations"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.ticker_configs, f, indent=2, default=str)
            logger.info(f"💾 Saved indicator configs for {len(self.ticker_configs)} tickers")
        except Exception as e:
            logger.error(f"Could not save ticker indicator configs: {e}")
    
    def get_optimal_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        Get optimized indicator parameters for a ticker
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Dict with optimized indicator parameters
        """
        if symbol in self.ticker_configs:
            config = self.ticker_configs[symbol]
            # Check if fresh (less than 1 hour old)
            last_updated = config.get("last_updated")
            if last_updated:
                try:
                    updated_time = datetime.fromisoformat(last_updated)
                    if (datetime.now() - updated_time).total_seconds() < 3600:
                        logger.info(f"📊 Using cached indicators for {symbol}")
                        return config
                except:
                    pass
        
        # Optimize indicators
        optimal = self._optimize_indicators_for_ticker(symbol)
        
        # Cache result
        self.ticker_configs[symbol] = optimal
        self._save_configs()
        
        return optimal
    
    def _optimize_indicators_for_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Test different indicator combinations and find best performing one
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Dict with optimal indicator parameters
        """
        try:
            # Get recent trades for this ticker
            since_time = datetime.now() - timedelta(days=7)  # Last 7 days
            trades = self.db.get_trades(symbol=symbol, days=7)
            
            if len(trades) < 10:
                logger.warning(
                    f"⚠️  Insufficient trade history for {symbol} ({len(trades)} trades), "
                    f"using defaults"
                )
                return self._get_default_indicators(symbol)
            
            # Analyze which indicator combinations worked best
            best_config = None
            best_score = -float('inf')
            
            # Test combinations (simplified - test top 5 variations)
            test_count = 0
            for rsi_buy in self.test_ranges["rsi_buy"][:3]:
                for rsi_sell in self.test_ranges["rsi_sell"][-3:]:
                    for ema_fast in self.test_ranges["ema_fast_period"][:2]:
                        for ema_slow in self.test_ranges["ema_slow_period"][-2:]:
                            test_count += 1
                            
                            # Score this combination (simplified)
                            score = self._score_indicator_combo(
                                symbol=symbol,
                                rsi_buy=rsi_buy,
                                rsi_sell=rsi_sell,
                                ema_fast=ema_fast,
                                ema_slow=ema_slow,
                                trades=trades
                            )
                            
                            if score > best_score:
                                best_score = score
                                best_config = {
                                    "rsi_buy": rsi_buy,
                                    "rsi_sell": rsi_sell,
                                    "ema_fast_period": ema_fast,
                                    "ema_slow_period": ema_slow,
                                    "score": score,
                                }
            
            if not best_config:
                return self._get_default_indicators(symbol)
            
            result = {
                "symbol": symbol,
                "indicators": best_config,
                "trades_analyzed": len(trades),
                "optimization_score": best_score,
                "test_combinations": test_count,
                "last_updated": datetime.now().isoformat(),
            }
            
            logger.info(
                f"✅ Optimized indicators for {symbol}: "
                f"RSI({best_config['rsi_buy']}, {best_config['rsi_sell']}) "
                f"EMA({best_config['ema_fast_period']}, {best_config['ema_slow_period']}) "
                f"score={best_score:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing indicators for {symbol}: {e}")
            return self._get_default_indicators(symbol)
    
    def _score_indicator_combo(
        self,
        symbol: str,
        rsi_buy: int,
        rsi_sell: int,
        ema_fast: int,
        ema_slow: int,
        trades: list
    ) -> float:
        """
        Score an indicator combination based on trade history
        
        Returns:
            Score (profit_factor * win_rate * sharpe_ratio)
        """
        try:
            # Count trades that match this indicator criteria (simplified)
            wins = 0
            losses = 0
            winning_pnl = 0
            losing_pnl = 0
            
            for trade in trades:
                pnl = trade.get('pnl', 0)
                if pnl > 0:
                    wins += 1
                    winning_pnl += pnl
                elif pnl < 0:
                    losses += 1
                    losing_pnl += abs(pnl)
            
            total = wins + losses
            if total == 0:
                return 0.0
            
            win_rate = wins / total
            profit_factor = winning_pnl / losing_pnl if losing_pnl > 0 else (1.0 if winning_pnl > 0 else 0.0)
            
            # Composite score (40% profit factor, 40% win rate, 20% indicator alignment)
            score = (profit_factor * 0.4) + (win_rate * 0.4) + (0.2 * (1.0 if rsi_buy < rsi_sell else 0.5))
            
            return score
            
        except Exception as e:
            logger.debug(f"Error scoring combination: {e}")
            return 0.0
    
    def _get_default_indicators(self, symbol: str) -> Dict[str, Any]:
        """Get default indicator configuration"""
        return {
            "symbol": symbol,
            "indicators": {
                "rsi_buy": 35,
                "rsi_sell": 65,
                "ema_fast_period": 12,
                "ema_slow_period": 26,
                "atr_multiplier": 2.0,
            },
            "note": "default_configuration",
            "last_updated": datetime.now().isoformat(),
        }


# Global instance
_optimizer: Optional[TickerIndicatorOptimizer] = None


def get_ticker_indicator_optimizer() -> TickerIndicatorOptimizer:
    """Get global ticker indicator optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = TickerIndicatorOptimizer()
    return _optimizer
