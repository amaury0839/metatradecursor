"""
Enhanced Hourly Optimizer - Integrates DecisionOrchestrator with existing scheduler
Provides per-ticker dynamic risk adjustment, indicator optimization, and backtesting
"""

import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import json
from app.core.logger import setup_logger
from app.core.config import get_config
from app.ai.decision_orchestrator import get_decision_orchestrator
from app.core.database import get_database_manager

logger = setup_logger("enhanced_optimizer")


class EnhancedHourlyOptimizer:
    """
    Integrates DecisionOrchestrator for hourly optimization
    Replaces the standard adaptive_optimizer with enhanced features:
    - Per-ticker dynamic risk adjustment (0.6-1.2x multipliers)
    - Individual indicator optimization per ticker
    - Backtesting and performance analysis
    - Rolling 24-hour report history
    """
    
    def __init__(self):
        self.orchestrator = get_decision_orchestrator()
        self.config = get_config()
        self.db = get_database_manager()
        self.running = False
        self.last_optimization = None
        self.optimization_results = {}
        
    def hourly_optimization_cycle(self) -> Dict[str, Any]:
        """
        Execute hourly optimization for all trading pairs
        
        Returns:
            Dict with optimization results for all symbols
        """
        try:
            logger.info("="*80)
            logger.info("🚀 STARTING ENHANCED HOURLY OPTIMIZATION")
            logger.info("="*80)
            
            start_time = datetime.now()
            
            # Run the orchestrator's hourly optimization
            # This is async-friendly and handles all tickers
            results = self._run_optimization_sync()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.info("="*80)
            logger.info(f"✅ OPTIMIZATION COMPLETE - {len(results)} tickers processed in {elapsed:.1f}s")
            logger.info("="*80)
            
            self.last_optimization = datetime.now()
            self.optimization_results = results
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in hourly optimization cycle: {e}", exc_info=True)
            return {"error": str(e)}
    
    def _run_optimization_sync(self) -> Dict[str, Any]:
        """
        Run optimization synchronously (bridges async to sync)
        """
        try:
            # Use asyncio to run the async hourly_optimization
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.orchestrator.hourly_optimization())
                return result if result else {}
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"⚠️  Async optimization failed, using sync fallback: {e}")
            return self._run_optimization_fallback()
    
    def _run_optimization_fallback(self) -> Dict[str, Any]:
        """
        Fallback: Run optimization without async
        Directly call get_optimization_status which is synchronous
        """
        try:
            status = self.orchestrator.get_optimization_status()
            
            # Convert status to results format
            results = {}
            for symbol, info in status.get("status_by_ticker", {}).items():
                results[symbol] = {
                    "timestamp": datetime.now().isoformat(),
                    "risk_multiplier": info.get("risk_multiplier", 1.0),
                    "confidence_multiplier": info.get("confidence_multiplier", 1.0),
                    "win_rate": info.get("win_rate", 0.0),
                    "profit_factor": info.get("profit_factor", 1.0),
                    "trades_last_hour": info.get("trades_last_hour", 0),
                    "status": "optimized" if info.get("risk_multiplier") > 0 else "pending"
                }
            
            logger.info(f"✅ Fallback optimization processed {len(results)} tickers")
            return results
            
        except Exception as e:
            logger.error(f"❌ Fallback optimization also failed: {e}")
            return {}
    
    def run_full_backtest(self, symbols: Optional[list] = None, days: int = 7) -> Dict[str, Any]:
        """
        Run comprehensive backtest on trading strategy
        
        Args:
            symbols: List of symbols to backtest (None = all)
            days: Number of days to backtest
        
        Returns:
            Backtest results with metrics
        """
        try:
            logger.info(f"🔄 Running {days}-day backtest...")
            
            results = self.orchestrator.run_backtests(symbols=symbols, days=days)
            
            logger.info(f"✅ Backtest complete")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Backtest failed: {e}")
            return {"error": str(e)}
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status for all tickers"""
        return self.orchestrator.get_optimization_status()
    
    def get_ticker_performance(self, symbol: str, hours: int = 1) -> Dict[str, Any]:
        """Get detailed performance metrics for a specific ticker"""
        try:
            return self.orchestrator.performance_tracker.calculate_ticker_metrics(symbol, hours=hours)
        except Exception as e:
            logger.warning(f"Could not get performance for {symbol}: {e}")
            return {}
    
    def get_dynamic_risk(self, symbol: str) -> Dict[str, Any]:
        """Get dynamic risk adjustment for a specific ticker"""
        try:
            return self.orchestrator.risk_adjuster.get_dynamic_risk(symbol)
        except Exception as e:
            logger.warning(f"Could not get dynamic risk for {symbol}: {e}")
            return {}
    
    def get_optimal_indicators(self, symbol: str) -> Dict[str, Any]:
        """Get optimal indicator configuration for a specific ticker"""
        try:
            return self.orchestrator.indicator_optimizer.get_optimal_indicators(symbol)
        except Exception as e:
            logger.warning(f"Could not get optimal indicators for {symbol}: {e}")
            return {}


# Global instance
_enhanced_optimizer: Optional[EnhancedHourlyOptimizer] = None


def get_enhanced_optimizer() -> EnhancedHourlyOptimizer:
    """Get global enhanced optimizer instance"""
    global _enhanced_optimizer
    if _enhanced_optimizer is None:
        _enhanced_optimizer = EnhancedHourlyOptimizer()
    return _enhanced_optimizer
