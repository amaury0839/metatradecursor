"""Optimized API endpoints for historical data and performance metrics"""

from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd

from app.core.database import get_database_manager
from app.ui.cache_manager import get_cache, get_historical_cache
from app.trading.indicator_optimizer import get_indicator_optimizer
from app.core.config import get_config

router = APIRouter(prefix="/api/optimized", tags=["optimized"])

# ============================================================================
# HISTORICAL DATA ENDPOINTS
# ============================================================================

@router.get("/trades/history")
async def get_trades_history(
    days: int = Query(7, ge=1, le=90),
    symbol: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
) -> Dict[str, Any]:
    """
    Get historical trades with efficient caching.
    
    Query Parameters:
    - days: Number of days to retrieve (1-90)
    - symbol: Optional symbol filter
    - skip: Pagination skip
    - limit: Pagination limit
    
    Returns trades with metadata including win rate, P&L statistics
    """
    # Check cache first
    cache_key = f"trades_history_{days}_{symbol}_{skip}_{limit}"
    cached = get_historical_cache().get(cache_key, max_age_seconds=300)
    if cached is not None:
        return cached
    
    db = get_database_manager()
    cutoff = datetime.now() - timedelta(days=days)
    
    trades = db.get_trades(
        since=cutoff,
        symbol=symbol,
        offset=skip,
        limit=limit
    )
    
    if not trades:
        return {"trades": [], "total": 0, "win_rate": 0}
    
    # Calculate statistics
    df = pd.DataFrame(trades)
    total = len(trades)
    wins = sum(1 for t in trades if t.get("profit", 0) > 0)
    
    response = {
        "trades": trades,
        "total": total,
        "win_rate": wins / total if total > 0 else 0,
        "total_pnl": sum(t.get("profit", 0) for t in trades),
        "avg_trade": sum(t.get("profit", 0) for t in trades) / total if total > 0 else 0,
        "cached": False
    }
    
    # Cache result
    get_historical_cache().set(cache_key, response, ttl=300)
    
    return response


@router.get("/performance/daily")
async def get_daily_performance(
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get daily performance summary.
    
    Returns daily P&L, win rate, and trade count
    """
    cache_key = f"daily_perf_{days}"
    cached = get_cache().get(cache_key)
    if cached:
        return cached
    
    db = get_database_manager()
    cutoff = datetime.now() - timedelta(days=days)
    trades = db.get_trades(since=cutoff)
    
    if not trades:
        return {"daily": [], "total_pnl": 0, "avg_daily_pnl": 0}
    
    df = pd.DataFrame(trades)
    df['date'] = pd.to_datetime(df['open_timestamp']).dt.date
    
    daily_stats = []
    for date, group in df.groupby('date'):
        trades_count = len(group)
        wins = sum(1 for _, t in group.iterrows() if t['profit'] > 0)
        pnl = group['profit'].sum()
        
        daily_stats.append({
            "date": str(date),
            "trades": trades_count,
            "wins": wins,
            "win_rate": wins / trades_count if trades_count > 0 else 0,
            "pnl": pnl
        })
    
    response = {
        "daily": sorted(daily_stats, key=lambda x: x['date']),
        "total_pnl": df['profit'].sum(),
        "avg_daily_pnl": df.groupby('date')['profit'].sum().mean(),
        "best_day": max(daily_stats, key=lambda x: x['pnl']) if daily_stats else None,
        "worst_day": min(daily_stats, key=lambda x: x['pnl']) if daily_stats else None
    }
    
    get_cache().set(cache_key, response, ttl=3600)
    return response


@router.get("/performance/symbol")
async def get_symbol_performance(
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get performance statistics by symbol.
    
    Returns win rate, P&L, and trade count per symbol
    """
    cache_key = f"symbol_perf_{days}"
    cached = get_cache().get(cache_key)
    if cached:
        return cached
    
    db = get_database_manager()
    cutoff = datetime.now() - timedelta(days=days)
    trades = db.get_trades(since=cutoff)
    
    if not trades:
        return {"by_symbol": {}}
    
    df = pd.DataFrame(trades)
    
    by_symbol = {}
    for symbol, group in df.groupby('symbol'):
        trades_count = len(group)
        wins = sum(1 for _, t in group.iterrows() if t['profit'] > 0)
        pnl = group['profit'].sum()
        
        by_symbol[symbol] = {
            "trades": trades_count,
            "wins": wins,
            "losses": trades_count - wins,
            "win_rate": wins / trades_count if trades_count > 0 else 0,
            "pnl": pnl,
            "avg_trade": pnl / trades_count if trades_count > 0 else 0
        }
    
    response = {
        "by_symbol": by_symbol,
        "best_symbol": max(by_symbol.items(), key=lambda x: x[1]['win_rate']) if by_symbol else None,
        "worst_symbol": min(by_symbol.items(), key=lambda x: x[1]['win_rate']) if by_symbol else None
    }
    
    get_cache().set(cache_key, response, ttl=3600)
    return response


@router.get("/performance/hourly")
async def get_hourly_performance(
    days: int = Query(7, ge=1, le=30)
) -> Dict[str, Any]:
    """
    Get hourly performance analysis.
    
    Returns win rate and trade count by hour of day
    """
    cache_key = f"hourly_perf_{days}"
    cached = get_cache().get(cache_key)
    if cached:
        return cached
    
    db = get_database_manager()
    cutoff = datetime.now() - timedelta(days=days)
    trades = db.get_trades(since=cutoff)
    
    if not trades:
        return {"by_hour": {}}
    
    df = pd.DataFrame(trades)
    df['hour'] = pd.to_datetime(df['open_timestamp']).dt.hour
    
    by_hour = {}
    for hour, group in df.groupby('hour'):
        trades_count = len(group)
        wins = sum(1 for _, t in group.iterrows() if t['profit'] > 0)
        pnl = group['profit'].sum()
        
        by_hour[str(hour)] = {
            "trades": trades_count,
            "wins": wins,
            "win_rate": wins / trades_count if trades_count > 0 else 0,
            "pnl": pnl,
            "avg_trade": pnl / trades_count if trades_count > 0 else 0
        }
    
    response = {
        "by_hour": by_hour,
        "best_hour": max(by_hour.items(), key=lambda x: x[1]['win_rate']) if by_hour else None,
    }
    
    get_cache().set(cache_key, response, ttl=3600)
    return response


# ============================================================================
# OPTIMIZATION ENDPOINTS
# ============================================================================

@router.get("/optimizer/status")
async def get_optimizer_status() -> Dict[str, Any]:
    """Get current optimizer status and parameters"""
    optimizer = get_indicator_optimizer()
    
    return {
        "status": "active",
        "current_params": optimizer.current_params,
        "last_update": datetime.now().isoformat(),
        "optimization_mode": "continuous"
    }


@router.post("/optimizer/analyze")
async def analyze_performance(
    hours: int = Query(24, ge=1, le=168)
) -> Dict[str, Any]:
    """
    Run AI-driven performance analysis and get optimization recommendations.
    
    Query Parameters:
    - hours: Analysis window in hours (1-168)
    
    Returns performance metrics and AI recommendations
    """
    optimizer = get_indicator_optimizer()
    
    report = optimizer.continuous_optimization_report(hours=hours)
    
    return report


@router.post("/optimizer/apply")
async def apply_optimization(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply optimization parameters to trading indicators.
    
    Parameters: Dictionary of parameter names to values
    
    Returns success/failure status and message
    """
    optimizer = get_indicator_optimizer()
    
    success, message = optimizer.apply_optimization(params)
    
    return {
        "success": success,
        "message": message,
        "applied_params": params if success else {},
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@router.get("/analysis/winning-trades")
async def get_winning_trades(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=100)
) -> Dict[str, Any]:
    """
    Get best performing trades.
    
    Returns top N winning trades sorted by profit
    """
    cache_key = f"winning_{days}_{limit}"
    cached = get_cache().get(cache_key)
    if cached:
        return cached
    
    db = get_database_manager()
    cutoff = datetime.now() - timedelta(days=days)
    trades = db.get_trades(since=cutoff)
    
    if not trades:
        return {"trades": [], "total": 0}
    
    df = pd.DataFrame(trades)
    winning = df[df['profit'] > 0].nlargest(limit, 'profit')
    
    response = {
        "trades": winning.to_dict('records'),
        "total": len(df[df['profit'] > 0]),
        "avg_winning_trade": winning['profit'].mean(),
        "total_winning_pnl": winning['profit'].sum()
    }
    
    get_cache().set(cache_key, response, ttl=3600)
    return response


@router.get("/analysis/losing-trades")
async def get_losing_trades(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=100)
) -> Dict[str, Any]:
    """
    Get worst performing trades.
    
    Returns bottom N losing trades sorted by loss
    """
    cache_key = f"losing_{days}_{limit}"
    cached = get_cache().get(cache_key)
    if cached:
        return cached
    
    db = get_database_manager()
    cutoff = datetime.now() - timedelta(days=days)
    trades = db.get_trades(since=cutoff)
    
    if not trades:
        return {"trades": [], "total": 0}
    
    df = pd.DataFrame(trades)
    losing = df[df['profit'] <= 0].nsmallest(limit, 'profit')
    
    response = {
        "trades": losing.to_dict('records'),
        "total": len(df[df['profit'] <= 0]),
        "avg_losing_trade": losing['profit'].mean(),
        "total_losing_pnl": losing['profit'].sum()
    }
    
    get_cache().set(cache_key, response, ttl=3600)
    return response


@router.get("/analysis/correlation")
async def get_symbol_correlation(
    days: int = Query(30, ge=1, le=365)
) -> Dict[str, Any]:
    """
    Analyze correlation between symbols based on trade performance.
    
    Returns correlation matrix and insights
    """
    cache_key = f"correlation_{days}"
    cached = get_cache().get(cache_key)
    if cached:
        return cached
    
    db = get_database_manager()
    cutoff = datetime.now() - timedelta(days=days)
    trades = db.get_trades(since=cutoff)
    
    if not trades:
        return {"correlation": {}}
    
    df = pd.DataFrame(trades)
    df['date'] = pd.to_datetime(df['open_timestamp']).dt.date
    
    # Pivot trades by date and symbol
    pivot = df.pivot_table(
        values='profit',
        index='date',
        columns='symbol',
        aggfunc='sum'
    )
    
    # Calculate correlation
    correlation = pivot.corr().round(3)
    
    response = {
        "correlation": correlation.to_dict(),
        "summary": "Analyze which symbols move together"
    }
    
    get_cache().set(cache_key, response, ttl=3600)
    return response


# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

@router.post("/cache/clear")
async def clear_cache() -> Dict[str, str]:
    """Clear all caches"""
    get_cache().clear()
    get_historical_cache().clear()
    return {"status": "cleared", "message": "All caches cleared successfully"}


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    cache = get_cache()
    hist_cache = get_historical_cache()
    
    return {
        "cache_items": len(cache.cache),
        "historical_cache_items": len(hist_cache.cache),
        "cache_memory_usage_mb": sum(len(str(v)) for v in cache.cache.values()) / 1024 / 1024,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("This module is meant to be imported into a FastAPI app")
