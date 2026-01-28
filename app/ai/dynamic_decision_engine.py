"""
Dynamic Decision Engine - Enhanced AI decision making with hourly risk adjustment per ticker
Features:
- Hourly risk reajustment based on ticker performance
- Individual indicator profiles per ticker
- Backtesting integration
- Adaptive confidence thresholds
"""

import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
from app.ai.decision_engine import DecisionEngine
from app.ai.schemas import TradingDecision
from app.core.logger import setup_logger
from app.core.config import get_config
from app.core.database import get_database_manager
from app.trading.mt5_client import get_mt5_client
from app.trading.risk import get_risk_manager
from app.trading.portfolio import get_portfolio_manager

logger = setup_logger("dynamic_decision_engine")


class TickerPerformanceTracker:
    """Tracks individual ticker performance for dynamic parameter adjustment"""
    
    def __init__(self):
        self.db = get_database_manager()
        self.cache_file = Path(__file__).parent.parent.parent / "data" / "ticker_performance.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.performance_data = self._load_cache()
        
    def _load_cache(self) -> Dict:
        """Load cached performance data"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load performance cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save performance data to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.performance_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save performance cache: {e}")
    
    def calculate_ticker_metrics(self, symbol: str, hours: int = 1) -> Dict:
        """
        Calculate performance metrics for a ticker over last N hours
        
        Args:
            symbol: Ticker symbol
            hours: Number of hours to analyze
        
        Returns:
            Dict with performance metrics
        """
        try:
            # Get trades from last N hours
            since_time = datetime.now() - timedelta(hours=hours)
            trades = self.db.get_trades(symbol=symbol, days=hours/24)
            
            if not trades:
                return {
                    "symbol": symbol,
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "win_rate": 0.5,
                    "profit_factor": 1.0,
                    "total_pnl": 0.0,
                    "avg_win": 0.0,
                    "avg_loss": 0.0,
                    "sharpe_ratio": 0.0,
                }
            
            # Analyze closed trades
            winning_trades = []
            losing_trades = []
            
            for trade in trades:
                pnl = trade.get('pnl', 0)
                if pnl > 0:
                    winning_trades.append(pnl)
                elif pnl < 0:
                    losing_trades.append(abs(pnl))
            
            total_trades = len(winning_trades) + len(losing_trades)
            if total_trades == 0:
                return {
                    "symbol": symbol,
                    "trades": len(trades),
                    "win_rate": 0.5,
                    "profit_factor": 1.0,
                    "status": "no_closed_trades"
                }
            
            win_rate = len(winning_trades) / total_trades
            total_wins = sum(winning_trades) if winning_trades else 0
            total_losses = sum(losing_trades) if losing_trades else 0
            
            profit_factor = total_wins / total_losses if total_losses > 0 else (1.0 if total_wins > 0 else 1.0)
            avg_win = total_wins / len(winning_trades) if winning_trades else 0.0
            avg_loss = total_losses / len(losing_trades) if losing_trades else 0.0
            
            # Sharpe Ratio (simplified)
            if winning_trades and losing_trades:
                returns = winning_trades + [-x for x in losing_trades]
                mean_return = sum(returns) / len(returns)
                variance = sum((x - mean_return)**2 for x in returns) / len(returns)
                sharpe = mean_return / (variance**0.5) if variance > 0 else 0
            else:
                sharpe = 0.0
            
            metrics = {
                "symbol": symbol,
                "trades": total_trades,
                "wins": len(winning_trades),
                "losses": len(losing_trades),
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "total_pnl": total_wins - total_losses,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "sharpe_ratio": sharpe,
                "last_updated": datetime.now().isoformat(),
            }
            
            # Cache result
            self.performance_data[symbol] = metrics
            self._save_cache()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}


class DynamicRiskAdjuster:
    """Adjusts risk parameters per ticker based on hourly performance"""
    
    def __init__(self):
        self.config = get_config()
        self.risk = get_risk_manager()
        self.tracker = TickerPerformanceTracker()
        self.params_file = Path(__file__).parent.parent.parent / "data" / "dynamic_risk_params.json"
        self.params_file.parent.mkdir(parents=True, exist_ok=True)
        self.ticker_params = self._load_params()
        self.last_adjustment = {}
        
    def _load_params(self) -> Dict:
        """Load saved dynamic risk parameters"""
        try:
            if self.params_file.exists():
                with open(self.params_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load dynamic risk params: {e}")
        return {}
    
    def _save_params(self):
        """Save dynamic risk parameters"""
        try:
            with open(self.params_file, 'w') as f:
                json.dump(self.ticker_params, f, indent=2, default=str)
            logger.info(f"💾 Saved dynamic risk params for {len(self.ticker_params)} tickers")
        except Exception as e:
            logger.error(f"Could not save dynamic risk params: {e}")
    
    def get_dynamic_risk(self, symbol: str) -> Dict:
        """
        Calculate dynamic risk parameters for a ticker
        
        Args:
            symbol: Ticker symbol
        
        Returns:
            Dict with adjusted risk parameters
        """
        # 🔥 GET BASE RISK FROM RISK_CONFIG (2%, 2.5%, OR 3% based on asset type)
        base_risk = self.risk.get_risk_pct_for_symbol(symbol) * 100
        base_max_daily_loss = self.config.trading.default_max_daily_loss
        base_max_positions = self.config.trading.default_max_positions
        
        # Get performance metrics (last hour)
        metrics = self.tracker.calculate_ticker_metrics(symbol, hours=1)
        
        # Adjust based on win rate
        win_rate = metrics.get("win_rate", 0.5)
        profit_factor = metrics.get("profit_factor", 1.0)
        trades_count = metrics.get("trades", 0)
        
        # Dynamic risk multiplier based on performance
        if trades_count < 3:
            # Not enough data, use conservative multiplier
            multiplier = 0.8
            confidence_multiplier = 0.7
        elif win_rate >= 0.65 and profit_factor >= 1.5:
            # Excellent performance - increase risk slightly
            multiplier = 1.2
            confidence_multiplier = 1.2
        elif win_rate >= 0.55 and profit_factor >= 1.2:
            # Good performance - maintain or slight increase
            multiplier = 1.05
            confidence_multiplier = 1.1
        elif win_rate < 0.45 or profit_factor < 0.8:
            # Poor performance - reduce risk
            multiplier = 0.6
            confidence_multiplier = 0.6
        else:
            # Average performance - maintain base
            multiplier = 1.0
            confidence_multiplier = 1.0
        
        adjusted_params = {
            "symbol": symbol,
            "base_risk_pct": base_risk,
            "adjusted_risk_pct": base_risk * multiplier,
            "base_max_daily_loss_pct": base_max_daily_loss,
            "adjusted_max_daily_loss_pct": base_max_daily_loss * multiplier,
            "confidence_multiplier": confidence_multiplier,
            "multiplier": multiplier,
            "metrics": metrics,
            "last_adjusted": datetime.now().isoformat(),
        }
        
        # Cache
        self.ticker_params[symbol] = adjusted_params
        self._save_params()
        
        logger.info(
            f"🎯 Dynamic risk for {symbol}: "
            f"risk={adjusted_params['adjusted_risk_pct']:.2f}% "
            f"(multiplier={multiplier:.2f}x), "
            f"wr={win_rate:.1%}, pf={profit_factor:.2f}"
        )
        
        return adjusted_params


class DynamicDecisionEngine(DecisionEngine):
    """Enhanced decision engine with hourly risk adjustment per ticker"""
    
    def __init__(self):
        super().__init__()
        self.risk_adjuster = DynamicRiskAdjuster()
        self.portfolio = get_portfolio_manager()
        
    def make_dynamic_decision(
        self,
        symbol: str,
        timeframe: str,
        technical_signal: str,
        indicators: Dict[str, Any]
    ) -> Tuple[Optional[TradingDecision], Optional[str], Optional[str]]:
        """
        Make trading decision with dynamic risk adjustment
        
        Args:
            symbol: Symbol to analyze
            timeframe: Timeframe
            technical_signal: Technical signal (BUY/SELL/HOLD)
            indicators: Technical indicators
        
        Returns:
            Tuple of (decision, prompt_hash, error_message)
        """
        # Get base decision from parent
        decision, prompt_hash, error = self.make_decision(
            symbol=symbol,
            timeframe=timeframe,
            technical_signal=technical_signal,
            indicators=indicators
        )
        
        if decision is None or decision.action == "HOLD":
            return decision, prompt_hash, error
        
        # Adjust for dynamic risk
        dynamic_risk = self.risk_adjuster.get_dynamic_risk(symbol)
        multiplier = dynamic_risk["multiplier"]
        confidence_mult = dynamic_risk["confidence_multiplier"]
        
        # Adjust order size based on ticker performance
        if decision.order:
            original_volume = decision.order.volume_lots
            adjusted_volume = original_volume * multiplier
            
            # Cap by risk
            max_volume = self.risk.hard_max_volume_lots
            adjusted_volume = min(adjusted_volume, max_volume)
            
            decision.order.volume_lots = adjusted_volume
            
            logger.info(
                f"📊 Adjusted {symbol} position size: "
                f"{original_volume:.4f} → {adjusted_volume:.4f} lots "
                f"(multiplier: {multiplier:.2f}x)"
            )
        
        # Adjust confidence threshold
        decision.confidence *= confidence_mult
        decision.confidence = min(1.0, decision.confidence)
        
        return decision, prompt_hash, error


# Global instance
_dynamic_engine: Optional[DynamicDecisionEngine] = None


def get_dynamic_decision_engine() -> DynamicDecisionEngine:
    """Get global dynamic decision engine instance"""
    global _dynamic_engine
    if _dynamic_engine is None:
        _dynamic_engine = DynamicDecisionEngine()
    return _dynamic_engine
