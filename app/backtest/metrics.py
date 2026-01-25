"""Backtest metrics calculation"""

from typing import List, Dict, Any
import pandas as pd
import numpy as np


def calculate_metrics(trades: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate backtest metrics
    
    Args:
        trades: List of trade dicts with keys: entry_price, exit_price, volume, pnl
    
    Returns:
        Dict with metrics
    """
    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
        }
    
    # Basic stats
    total_trades = len(trades)
    pnls = [t.get("pnl", 0.0) for t in trades]
    winning_trades = [p for p in pnls if p > 0]
    losing_trades = [p for p in pnls if p < 0]
    
    win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0.0
    total_pnl = sum(pnls)
    avg_win = np.mean(winning_trades) if winning_trades else 0.0
    avg_loss = abs(np.mean(losing_trades)) if losing_trades else 0.0
    
    # Profit factor
    gross_profit = sum(winning_trades) if winning_trades else 0.0
    gross_loss = abs(sum(losing_trades)) if losing_trades else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
    
    # Drawdown calculation
    equity_curve = []
    running_equity = 10000.0  # Starting equity
    peak_equity = running_equity
    max_drawdown = 0.0
    
    for pnl in pnls:
        running_equity += pnl
        equity_curve.append(running_equity)
        if running_equity > peak_equity:
            peak_equity = running_equity
        drawdown = (peak_equity - running_equity) / peak_equity * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # Sharpe ratio (simplified)
    if len(pnls) > 1:
        returns = np.array(pnls) / 10000.0  # Normalize
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0.0
    else:
        sharpe_ratio = 0.0
    
    return {
        "total_trades": total_trades,
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe_ratio,
    }
