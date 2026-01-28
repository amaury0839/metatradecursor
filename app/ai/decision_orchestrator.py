"""
AI Decision Maker Orchestrator
Integrates dynamic decision engine, backtesting, and indicator optimization
Runs hourly optimization and provides enhanced trading decisions
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from app.core.logger import setup_logger
from app.core.config import get_config
from app.ai.dynamic_decision_engine import (
    get_dynamic_decision_engine,
    DynamicRiskAdjuster,
    TickerPerformanceTracker
)
from app.ai.ticker_indicator_optimizer import get_ticker_indicator_optimizer
from app.backtest.backtest_engine import get_backtest_engine
from app.trading.mt5_client import get_mt5_client
from app.trading.data import get_data_provider

logger = setup_logger("decision_orchestrator")


class DecisionOrchestrator:
    """
    Orchestrates AI decision-making with:
    - Hourly risk adjustment per ticker
    - Indicator optimization
    - Backtesting
    - Performance tracking
    """
    
    def __init__(self):
        self.config = get_config()
        self.decision_engine = get_dynamic_decision_engine()
        self.risk_adjuster = DynamicRiskAdjuster()
        self.performance_tracker = TickerPerformanceTracker()
        self.indicator_optimizer = get_ticker_indicator_optimizer()
        self.backtest_engine = get_backtest_engine()
        self.mt5 = get_mt5_client()
        self.data = get_data_provider()
        
        self.report_file = Path(__file__).parent.parent.parent / "data" / "hourly_optimization_report.json"
        self.report_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.last_optimization_time = {}
        self.optimization_interval_seconds = 3600  # 1 hour
    
    async def hourly_optimization(self) -> Dict[str, Any]:
        """
        Run hourly optimization for all tickers
        - Analyze performance from last hour
        - Adjust risk parameters
        - Optimize indicators
        - Generate reports
        """
        logger.info("🔄 Starting hourly optimization...")
        
        symbols = self.config.trading.default_symbols
        optimization_results = {}
        
        for symbol in symbols:
            try:
                # Check if enough time has passed since last optimization
                last_opt = self.last_optimization_time.get(symbol, datetime.min)
                if (datetime.now() - last_opt).total_seconds() < self.optimization_interval_seconds:
                    continue
                
                # 1. Analyze performance
                performance = self.performance_tracker.calculate_ticker_metrics(symbol, hours=1)
                
                # 2. Adjust risk
                dynamic_risk = self.risk_adjuster.get_dynamic_risk(symbol)
                
                # 3. Optimize indicators
                optimal_indicators = self.indicator_optimizer.get_optimal_indicators(symbol)
                
                optimization_results[symbol] = {
                    "timestamp": datetime.now().isoformat(),
                    "performance": performance,
                    "dynamic_risk": {
                        "base_risk": dynamic_risk["base_risk_pct"],
                        "adjusted_risk": dynamic_risk["adjusted_risk_pct"],
                        "multiplier": dynamic_risk["multiplier"],
                    },
                    "indicators": optimal_indicators.get("indicators", {}),
                    "status": "optimized"
                }
                
                self.last_optimization_time[symbol] = datetime.now()
                
                logger.info(
                    f"✅ Optimized {symbol}: "
                    f"Risk={dynamic_risk['adjusted_risk_pct']:.2f}%, "
                    f"Score={dynamic_risk['multiplier']:.2f}x"
                )
                
            except Exception as e:
                logger.error(f"Error optimizing {symbol}: {e}")
                optimization_results[symbol] = {"error": str(e)}
        
        # Generate report
        report = {
            "optimization_time": datetime.now().isoformat(),
            "symbols_optimized": len([r for r in optimization_results.values() if "error" not in r]),
            "results": optimization_results,
        }
        
        self._save_report(report)
        
        logger.info(f"✅ Hourly optimization complete. Optimized {len(optimization_results)} tickers")
        
        return report
    
    async def run_backtests(self, symbols: Optional[List[str]] = None, days: int = 7) -> Dict:
        """
        Run backtests for symbols to validate strategy
        
        Args:
            symbols: List of symbols (None = all)
            days: Number of days to backtest
        """
        logger.info(f"🔄 Starting backtests for {len(symbols or self.config.trading.default_symbols)} symbols...")
        
        if symbols is None:
            symbols = self.config.trading.default_symbols
        
        results = self.backtest_engine.run_full_backtest(symbols=symbols, days=days)
        
        logger.info(
            f"✅ Backtests complete: "
            f"Avg WR={results['aggregate_statistics']['avg_win_rate']:.1%}, "
            f"Total PnL=${results['aggregate_statistics']['total_combined_pnl']:.2f}"
        )
        
        return results
    
    def make_enhanced_decision(
        self,
        symbol: str,
        timeframe: str,
        technical_signal: str,
        indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make trading decision with full optimization
        
        Args:
            symbol: Symbol to trade
            timeframe: Timeframe
            technical_signal: Technical signal
            indicators: Technical indicators
        
        Returns:
            Dict with decision and metadata
        """
        try:
            # Get decision with dynamic risk adjustment
            decision, prompt_hash, error = self.decision_engine.make_dynamic_decision(
                symbol=symbol,
                timeframe=timeframe,
                technical_signal=technical_signal,
                indicators=indicators
            )
            
            if error:
                logger.warning(f"Decision error for {symbol}: {error}")
            
            # Add metadata
            result = {
                "decision": decision,
                "error": error,
                "metadata": {
                    "prompt_hash": prompt_hash,
                    "timestamp": datetime.now().isoformat(),
                    "symbol": symbol,
                    "timeframe": timeframe,
                }
            }
            
            # If it's a trade, add optimization info
            if decision and decision.action in ["BUY", "SELL"]:
                # Get current ticker parameters
                dynamic_risk = self.risk_adjuster.get_dynamic_risk(symbol)
                indicators_config = self.indicator_optimizer.get_optimal_indicators(symbol)
                
                result["optimization_context"] = {
                    "risk_multiplier": dynamic_risk["multiplier"],
                    "confidence_multiplier": dynamic_risk["confidence_multiplier"],
                    "ticker_indicators": indicators_config.get("indicators", {}),
                    "performance_metrics": dynamic_risk["metrics"],
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error making enhanced decision for {symbol}: {e}")
            return {
                "decision": None,
                "error": str(e),
                "metadata": {
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                }
            }
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status for all tickers"""
        symbols = self.config.trading.default_symbols
        status = {}
        
        for symbol in symbols:
            risk = self.risk_adjuster.get_dynamic_risk(symbol)
            indicators = self.indicator_optimizer.get_optimal_indicators(symbol)
            performance = self.performance_tracker.calculate_ticker_metrics(symbol)
            
            status[symbol] = {
                "risk_multiplier": risk["multiplier"],
                "confidence_multiplier": risk["confidence_multiplier"],
                "win_rate": performance.get("win_rate", 0.0),
                "profit_factor": performance.get("profit_factor", 1.0),
                "trades_last_hour": performance.get("trades", 0),
                "indicator_score": indicators.get("optimization_score", 0.0),
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status_by_ticker": status,
            "last_optimization": self.last_optimization_time,
        }
    
    def _save_report(self, report: Dict):
        """Save optimization report"""
        try:
            # Load existing history
            history = []
            if self.report_file.exists():
                with open(self.report_file, 'r') as f:
                    history = json.load(f)
            
            # Keep only last 24 hours of reports
            cutoff = datetime.now() - timedelta(hours=24)
            history = [
                r for r in history
                if datetime.fromisoformat(r.get("optimization_time", "")) > cutoff
            ]
            
            # Add new report
            history.append(report)
            
            # Save
            with open(self.report_file, 'w') as f:
                json.dump(history, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Could not save optimization report: {e}")


# Global instance
_orchestrator: Optional[DecisionOrchestrator] = None


def get_decision_orchestrator() -> DecisionOrchestrator:
    """Get global decision orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = DecisionOrchestrator()
    return _orchestrator


async def run_hourly_optimization_task():
    """
    Background task that runs hourly optimization
    Should be run in a background thread/async context
    """
    orchestrator = get_decision_orchestrator()
    
    while True:
        try:
            await orchestrator.hourly_optimization()
            # Wait 1 hour
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Error in hourly optimization task: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error
