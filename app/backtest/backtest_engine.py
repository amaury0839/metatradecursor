"""
Advanced Backtesting Engine
Tests trading strategies with individual ticker parameters
Provides detailed performance analysis
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import json
from app.core.logger import setup_logger
from app.core.database import get_database_manager
from app.ai.ticker_indicator_optimizer import get_ticker_indicator_optimizer

logger = setup_logger("backtest_engine")


class BacktestEngine:
    """Advanced backtesting with ticker-specific optimization"""
    
    def __init__(self):
        self.db = get_database_manager()
        self.indicator_optimizer = get_ticker_indicator_optimizer()
        self.results_file = Path(__file__).parent.parent.parent / "data" / "backtest_results.json"
        self.results_file.parent.mkdir(parents=True, exist_ok=True)
        
    def backtest_symbol(
        self,
        symbol: str,
        days: int = 7,
        use_optimized_indicators: bool = True
    ) -> Dict[str, Any]:
        """
        Backtest a symbol using historical data and trades
        
        Args:
            symbol: Ticker symbol
            days: Number of days to backtest
            use_optimized_indicators: Use optimized indicators vs defaults
        
        Returns:
            Dict with backtest results
        """
        try:
            logger.info(f"🔄 Starting backtest for {symbol} ({days} days)...")
            
            # Get historical data
            since_time = datetime.now() - timedelta(days=days)
            trades = self.db.get_trades(symbol=symbol, days=days)
            
            if not trades:
                logger.warning(f"No trade data for {symbol}")
                return {"symbol": symbol, "status": "no_data"}
            
            # Get optimized indicators if requested
            if use_optimized_indicators:
                indicator_config = self.indicator_optimizer.get_optimal_indicators(symbol)
                indicators = indicator_config.get("indicators", {})
            else:
                indicators = {}
            
            # Calculate metrics
            metrics = self._calculate_metrics(trades)
            
            # Analyze by timeframe
            timeframe_analysis = self._analyze_by_timeframe(trades)
            
            # Analyze by hour of day
            hourly_analysis = self._analyze_by_hour(trades)
            
            result = {
                "symbol": symbol,
                "period_days": days,
                "backtest_date": datetime.now().isoformat(),
                "indicators_used": indicators,
                "metrics": metrics,
                "timeframe_analysis": timeframe_analysis,
                "hourly_analysis": hourly_analysis,
                "optimization_score": self._calculate_optimization_score(metrics),
            }
            
            # Save results
            self._save_results(symbol, result)
            
            logger.info(
                f"✅ Backtest complete for {symbol}: "
                f"WR={metrics['win_rate']:.1%}, "
                f"PF={metrics['profit_factor']:.2f}, "
                f"Score={result['optimization_score']:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Backtest error for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}
    
    def _calculate_metrics(self, trades: list) -> Dict[str, float]:
        """Calculate performance metrics from trades"""
        if not trades:
            return self._empty_metrics()
        
        # Classify trades
        wins = [t for t in trades if t.get('pnl', 0) > 0]
        losses = [t for t in trades if t.get('pnl', 0) < 0]
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        
        # Calculate metrics
        total_trades = len(trades)
        closed_trades = wins + losses
        win_count = len(wins)
        loss_count = len(losses)
        
        if not closed_trades:
            return self._empty_metrics()
        
        win_rate = win_count / len(closed_trades) if closed_trades else 0
        total_wins = sum(t.get('pnl', 0) for t in wins)
        total_losses = sum(abs(t.get('pnl', 0)) for t in losses)
        profit_factor = total_wins / total_losses if total_losses > 0 else (1.0 if total_wins > 0 else 1.0)
        
        # Risk-reward ratio
        avg_win = total_wins / win_count if win_count > 0 else 0
        avg_loss = total_losses / loss_count if loss_count > 0 else 0
        rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Sharpe Ratio (simplified)
        pnls = [t.get('pnl', 0) for t in closed_trades]
        mean_pnl = sum(pnls) / len(pnls)
        variance = sum((p - mean_pnl)**2 for p in pnls) / len(pnls)
        sharpe = mean_pnl / (variance**0.5) if variance > 0 else 0
        
        # Max consecutive wins/losses
        max_consec_wins = self._max_consecutive(trades, True)
        max_consec_losses = self._max_consecutive(trades, False)
        
        # Expectancy (average profit per trade)
        expectancy = total_pnl / total_trades if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "closed_trades": len(closed_trades),
            "open_trades": total_trades - len(closed_trades),
            "wins": win_count,
            "losses": loss_count,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "total_pnl": total_pnl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "risk_reward_ratio": rr_ratio,
            "sharpe_ratio": sharpe,
            "expectancy": expectancy,
            "max_consecutive_wins": max_consec_wins,
            "max_consecutive_losses": max_consec_losses,
        }
    
    def _empty_metrics(self) -> Dict[str, float]:
        """Return empty metrics dict"""
        return {
            "total_trades": 0,
            "closed_trades": 0,
            "open_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "profit_factor": 1.0,
            "total_pnl": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "risk_reward_ratio": 0.0,
            "sharpe_ratio": 0.0,
            "expectancy": 0.0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
        }
    
    def _max_consecutive(self, trades: list, winning: bool) -> int:
        """Calculate max consecutive wins or losses"""
        max_consec = 0
        current_consec = 0
        
        for trade in trades:
            pnl = trade.get('pnl', 0)
            is_win = pnl > 0
            
            if is_win == winning:
                current_consec += 1
                max_consec = max(max_consec, current_consec)
            else:
                current_consec = 0
        
        return max_consec
    
    def _analyze_by_timeframe(self, trades: list) -> Dict[str, Dict]:
        """Analyze performance by timeframe"""
        result = {}
        
        # Group by timeframe
        for trade in trades:
            tf = trade.get('timeframe', 'unknown')
            if tf not in result:
                result[tf] = []
            result[tf].append(trade)
        
        # Calculate metrics for each
        for tf, tf_trades in result.items():
            result[tf] = self._calculate_metrics(tf_trades)
        
        return result
    
    def _analyze_by_hour(self, trades: list) -> Dict[str, Dict]:
        """Analyze performance by hour of day"""
        result = {}
        
        for hour in range(24):
            result[f"hour_{hour:02d}"] = []
        
        # Group by hour
        for trade in trades:
            try:
                entry_time = datetime.fromisoformat(trade.get('entry_time', ''))
                hour = entry_time.hour
                result[f"hour_{hour:02d}"].append(trade)
            except:
                pass
        
        # Calculate metrics for each hour
        for hour_key, hour_trades in result.items():
            if hour_trades:
                result[hour_key] = self._calculate_metrics(hour_trades)
            else:
                result[hour_key] = self._empty_metrics()
        
        return result
    
    def _calculate_optimization_score(self, metrics: Dict) -> float:
        """
        Calculate composite optimization score
        Score = (profit_factor * 0.3) + (win_rate * 0.3) + (sharpe_ratio * 0.2) + (expectancy * 0.2)
        """
        pf = min(metrics.get('profit_factor', 1.0), 3.0) / 3.0  # Cap at 3.0
        wr = metrics.get('win_rate', 0.5)
        sharpe = min(abs(metrics.get('sharpe_ratio', 0.0)), 2.0) / 2.0  # Cap at 2.0
        expectancy = metrics.get('expectancy', 0.0)
        
        # Normalize expectancy (assume max expectancy is 100)
        exp_score = min(abs(expectancy), 100) / 100 if expectancy != 0 else 0.5
        
        score = (pf * 0.3) + (wr * 0.3) + (sharpe * 0.2) + (exp_score * 0.2)
        return min(score, 1.0)  # Cap at 1.0
    
    def _save_results(self, symbol: str, results: Dict):
        """Save backtest results to file"""
        try:
            # Load existing results
            all_results = {}
            if self.results_file.exists():
                with open(self.results_file, 'r') as f:
                    all_results = json.load(f)
            
            # Update with new result
            all_results[symbol] = results
            
            # Save
            with open(self.results_file, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save backtest results: {e}")
    
    def run_full_backtest(
        self,
        symbols: Optional[List[str]] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Run backtest for multiple symbols
        
        Args:
            symbols: List of symbols (None = all from config)
            days: Number of days to backtest
        
        Returns:
            Dict with results for all symbols
        """
        from app.core.config import get_config
        
        if symbols is None:
            symbols = get_config().trading.default_symbols
        
        logger.info(f"🔄 Running full backtest for {len(symbols)} symbols ({days} days)...")
        
        all_results = {}
        for symbol in symbols:
            try:
                result = self.backtest_symbol(symbol, days=days)
                all_results[symbol] = result
            except Exception as e:
                logger.error(f"Backtest failed for {symbol}: {e}")
                all_results[symbol] = {"error": str(e)}
        
        # Calculate aggregate statistics
        aggregate = self._calculate_aggregate_stats(all_results)
        
        logger.info(
            f"✅ Full backtest complete: "
            f"Avg WR={aggregate['avg_win_rate']:.1%}, "
            f"Avg PF={aggregate['avg_profit_factor']:.2f}"
        )
        
        return {
            "backtest_date": datetime.now().isoformat(),
            "symbols_tested": len(all_results),
            "period_days": days,
            "results_by_symbol": all_results,
            "aggregate_statistics": aggregate,
        }
    
    def _calculate_aggregate_stats(self, results: Dict) -> Dict:
        """Calculate aggregate statistics across all symbols"""
        valid_results = [r for r in results.values() if "metrics" in r]
        
        if not valid_results:
            return {"status": "no_valid_results"}
        
        avg_wr = sum(r["metrics"]["win_rate"] for r in valid_results) / len(valid_results)
        avg_pf = sum(r["metrics"]["profit_factor"] for r in valid_results) / len(valid_results)
        avg_sharpe = sum(r["metrics"]["sharpe_ratio"] for r in valid_results) / len(valid_results)
        total_pnl = sum(r["metrics"]["total_pnl"] for r in valid_results)
        
        return {
            "symbols_with_data": len(valid_results),
            "avg_win_rate": avg_wr,
            "avg_profit_factor": avg_pf,
            "avg_sharpe_ratio": avg_sharpe,
            "total_combined_pnl": total_pnl,
        }


# Global instance
_backtest_engine: Optional[BacktestEngine] = None


def get_backtest_engine() -> BacktestEngine:
    """Get global backtest engine instance"""
    global _backtest_engine
    if _backtest_engine is None:
        _backtest_engine = BacktestEngine()
    return _backtest_engine
