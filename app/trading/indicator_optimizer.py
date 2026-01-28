"""Continuous indicator adjustment system using AI"""

import numpy as np
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import json
from app.core.logger import setup_logger
from app.ai.gemini_client import get_gemini_client
from app.core.database import get_database_manager
from app.trading.strategy import TradingStrategy
from app.core.config import get_config

logger = setup_logger("indicator_optimizer")

# Global optimizer instance
_optimizer_instance: Optional['IndicatorOptimizer'] = None


class IndicatorOptimizer:
    """AI-driven continuous optimization of trading indicators"""
    
    def __init__(self):
        self.gemini = get_gemini_client()
        self.db = get_database_manager()
        self.strategy = TradingStrategy()
        self.optimization_history = []
        self.current_params = {}
        
    def analyze_performance(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze recent trading performance by strategy"""
        try:
            # Get trades from last N hours
            cutoff = datetime.now() - timedelta(hours=hours)
            trades = self.db.get_trades(since=cutoff)
            
            if not trades:
                return {"trades_count": 0, "analysis": "Insufficient data"}
            
            # Group by strategy
            by_strategy = {}
            for trade in trades:
                strat = trade.get("strategy_type", "unknown")
                if strat not in by_strategy:
                    by_strategy[strat] = []
                by_strategy[strat].append(trade)
            
            # Calculate metrics per strategy
            metrics = {}
            for strat, strat_trades in by_strategy.items():
                wins = sum(1 for t in strat_trades if t.get("profit", 0) > 0)
                losses = len(strat_trades) - wins
                total_profit = sum(t.get("profit", 0) for t in strat_trades)
                
                metrics[strat] = {
                    "trades": len(strat_trades),
                    "win_rate": wins / len(strat_trades) if strat_trades else 0,
                    "total_profit": total_profit,
                    "avg_profit": total_profit / len(strat_trades) if strat_trades else 0,
                }
            
            return {
                "analysis_period": f"Last {hours}h",
                "total_trades": len(trades),
                "by_strategy": metrics,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {"error": str(e)}
    
    def get_optimization_recommendation(self, performance: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to recommend parameter adjustments"""
        try:
            if performance.get("error") or performance.get("trades_count", 0) == 0:
                return {"recommendation": "Insufficient data for optimization"}
            
            # Build prompt for AI
            prompt = f"""
            Analyze this trading performance and recommend indicator parameter adjustments:
            
            Performance Summary:
            {json.dumps(performance, indent=2)}
            
            Current Indicator Parameters:
            - SCALPING EMA: fast=5, slow=20, RSI=48
            - SWING EMA: fast=20, slow=50, RSI=55
            - TREND EMA: fast=50, slow=200, RSI varies
            
            Based on win rates and profit, suggest:
            1. Which parameters to adjust (EMA periods, RSI thresholds)
            2. Direction of adjustment (increase/decrease)
            3. Estimated impact (conservative estimate)
            4. Which strategy needs most adjustment
            
            Format as JSON with keys: parameter, current_value, recommended_value, reason
            """
            
            response = self.gemini.generate_content(
                system_prompt="You are a quantitative trading analyst specializing in indicator optimization.",
                user_prompt=prompt,
                use_cache=False
            )
            
            if not response:
                return {"error": "AI unavailable"}
            
            return {
                "recommendation": response,
                "timestamp": datetime.now().isoformat(),
                "confidence": 0.7
            }
        except Exception as e:
            logger.error(f"Optimization recommendation failed: {e}")
            return {"error": str(e)}
    
    def apply_optimization(self, adjustments: Dict[str, Any]) -> Tuple[bool, str]:
        """Apply recommended adjustments to strategy parameters"""
        try:
            if not isinstance(adjustments, dict):
                return False, "Invalid adjustments format"
            
            # Validate adjustments
            for param, value in adjustments.items():
                if not isinstance(param, str) or not isinstance(value, (int, float)):
                    continue
                
                # Apply with safety limits
                if "ema" in param.lower():
                    value = max(2, min(500, int(value)))  # Between 2 and 500 periods
                elif "rsi" in param.lower():
                    value = max(20, min(80, int(value)))  # Between 20 and 80
                
                self.current_params[param] = value
                logger.info(f"Updated {param} to {value}")
            
            # Save to database for persistence
            self.db.save_optimization(
                params=self.current_params,
                timestamp=datetime.now()
            )
            
            return True, "Optimization applied successfully"
        except Exception as e:
            logger.error(f"Failed to apply optimization: {e}")
            return False, str(e)
    
    def get_adaptive_rsi_threshold(self, symbol: str, volatility: float) -> Tuple[int, int]:
        """Calculate adaptive RSI thresholds based on volatility"""
        base_buy = 48
        base_sell = 52
        
        # Adjust based on volatility
        if volatility > 0.02:  # High volatility
            return base_buy - 5, base_sell + 5  # Easier entries
        elif volatility < 0.005:  # Low volatility
            return base_buy + 3, base_sell - 3  # Stricter entries
        else:
            return base_buy, base_sell
    
    def get_adaptive_ema_periods(self, timeframe: str, win_rate: float) -> Tuple[int, int]:
        """Calculate adaptive EMA periods based on performance"""
        base_fast, base_slow = 5, 20
        
        # Adjust based on recent win rate
        if win_rate > 0.60:  # Strong performance
            return int(base_fast * 0.9), int(base_slow * 0.9)  # Faster response
        elif win_rate < 0.45:  # Weak performance
            return int(base_fast * 1.1), int(base_slow * 1.1)  # Slower, more stable
        else:
            return base_fast, base_slow
    
    def continuous_optimization_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        try:
            # Get performance metrics
            performance = self.analyze_performance(hours)
            
            # Get AI recommendation
            recommendation = self.get_optimization_recommendation(performance)
            
            # Calculate adaptive parameters
            perf_by_strat = performance.get("by_strategy", {})
            scalp_wr = perf_by_strat.get("SCALPING", {}).get("win_rate", 0.5)
            
            adaptive_rsi_buy, adaptive_rsi_sell = self.get_adaptive_rsi_threshold("EURUSD", 0.01)
            adaptive_ema_fast, adaptive_ema_slow = self.get_adaptive_ema_periods("M5", scalp_wr)
            
            return {
                "report_timestamp": datetime.now().isoformat(),
                "analysis_period_hours": hours,
                "performance_summary": performance,
                "ai_recommendation": recommendation,
                "adaptive_parameters": {
                    "rsi_buy": adaptive_rsi_buy,
                    "rsi_sell": adaptive_rsi_sell,
                    "ema_fast": adaptive_ema_fast,
                    "ema_slow": adaptive_ema_slow,
                },
                "optimization_status": "ready_for_application"
            }
        except Exception as e:
            logger.error(f"Optimization report failed: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}


# Global optimizer instance
_optimizer = None

def get_indicator_optimizer() -> IndicatorOptimizer:
    """Get global optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = IndicatorOptimizer()
    return _optimizer
