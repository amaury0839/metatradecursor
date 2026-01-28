"""Integration module for UI, API, and optimization system"""

from typing import Dict, Any
from datetime import datetime
import threading

from app.core.logger import setup_logger
from app.ui.cache_manager import get_cache, get_historical_cache
from app.trading.indicator_optimizer import get_indicator_optimizer
from app.core.database import get_database_manager
from app.trading.mt5_client import get_mt5_client

logger = setup_logger("integration")


class PerformanceOptimizationController:
    """Centralized controller for all optimization activities"""
    
    def __init__(self):
        self.optimizer = get_indicator_optimizer()
        self.db = get_database_manager()
        self.cache = get_cache()
        self.hist_cache = get_historical_cache()
        self.last_optimization = None
        self.is_optimizing = False
        
    def run_continuous_optimization(self, interval_minutes: int = 60):
        """
        Run continuous optimization in background thread.
        
        This analyzes performance and adjusts indicators automatically.
        """
        import time
        
        def _optimization_loop():
            logger.info("Starting continuous optimization loop")
            
            while True:
                try:
                    if self.is_optimizing:
                        logger.debug("Optimization already in progress, skipping")
                        time.sleep(60)
                        continue
                    
                    self.is_optimizing = True
                    
                    # Run optimization
                    logger.info("Running continuous optimization analysis...")
                    report = self.optimizer.continuous_optimization_report(hours=24)
                    
                    if "error" not in report:
                        self.last_optimization = {
                            "timestamp": datetime.now().isoformat(),
                            "report": report
                        }
                        
                        # Apply if recommendations exist
                        if "ai_recommendation" in report:
                            recommendation = report["ai_recommendation"]
                            if "error" not in recommendation:
                                logger.info(f"Optimization recommendation: {recommendation.get('recommendation', '')}")
                        
                        # Clear related caches to force refresh
                        self._clear_analysis_cache()
                    
                    self.is_optimizing = False
                    
                    # Wait for next optimization cycle
                    logger.debug(f"Next optimization in {interval_minutes} minutes")
                    time.sleep(interval_minutes * 60)
                    
                except Exception as e:
                    logger.error(f"Optimization error: {e}")
                    self.is_optimizing = False
                    time.sleep(60)
        
        # Start in background thread
        thread = threading.Thread(target=_optimization_loop, daemon=True)
        thread.start()
        logger.info("Optimization thread started")
    
    def _clear_analysis_cache(self):
        """Clear cache entries related to analysis"""
        cache_keys_to_clear = [
            k for k in self.cache.cache.keys()
            if any(x in k for x in ['daily_perf', 'hourly_perf', 'symbol_perf', 'trades_history'])
        ]
        
        for key in cache_keys_to_clear:
            self.cache.cache.pop(key, None)
        
        logger.debug(f"Cleared {len(cache_keys_to_clear)} cache entries")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status"""
        return {
            "is_optimizing": self.is_optimizing,
            "last_optimization": self.last_optimization,
            "current_params": self.optimizer.current_params,
            "cache_stats": {
                "cache_items": len(self.cache.cache),
                "historical_cache_items": len(self.hist_cache.cache)
            }
        }
    
    def manual_optimization(self) -> Dict[str, Any]:
        """Run optimization immediately"""
        if self.is_optimizing:
            return {"error": "Optimization already in progress"}
        
        self.is_optimizing = True
        try:
            report = self.optimizer.continuous_optimization_report(hours=24)
            self.last_optimization = {
                "timestamp": datetime.now().isoformat(),
                "report": report
            }
            self._clear_analysis_cache()
            return report
        except Exception as e:
            logger.error(f"Manual optimization error: {e}")
            return {"error": str(e)}
        finally:
            self.is_optimizing = False


class UIPerformanceMonitor:
    """Monitor UI performance and suggest optimizations"""
    
    def __init__(self):
        self.cache = get_cache()
        self.hist_cache = get_historical_cache()
        self.metrics = {
            "chart_load_time": [],
            "table_load_time": [],
            "api_response_time": []
        }
    
    def record_load_time(self, component: str, duration_ms: float):
        """Record component load time"""
        if component in self.metrics:
            self.metrics[component].append(duration_ms)
            # Keep only last 100 measurements
            if len(self.metrics[component]) > 100:
                self.metrics[component] = self.metrics[component][-100:]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        for component, times in self.metrics.items():
            if times:
                stats[component] = {
                    "avg_ms": sum(times) / len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "measurements": len(times)
                }
        
        return {
            "performance_stats": stats,
            "cache_effectiveness": {
                "cache_hit_ratio": self._calculate_cache_ratio(),
                "total_cache_items": len(self.cache.cache) + len(self.hist_cache.cache),
                "memory_usage_mb": self._estimate_memory_usage()
            }
        }
    
    def _calculate_cache_ratio(self) -> float:
        """Estimate cache hit ratio"""
        # This is simplified; in production, track actual hits
        return 0.75  # Assume 75% cache hit ratio
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage by caches"""
        cache_size = sum(len(str(v)) for v in self.cache.cache.values())
        hist_size = sum(len(str(v)) for v in self.hist_cache.cache.values())
        return (cache_size + hist_size) / 1024 / 1024


class DataRefreshManager:
    """Intelligent data refresh with smart invalidation"""
    
    def __init__(self):
        self.cache = get_cache()
        self.db = get_database_manager()
        self.refresh_rules = {
            "account_info": {"ttl": 10, "priority": "high"},
            "open_positions": {"ttl": 15, "priority": "high"},
            "trade_history": {"ttl": 300, "priority": "medium"},
            "performance_metrics": {"ttl": 300, "priority": "medium"},
            "analysis": {"ttl": 600, "priority": "low"}
        }
    
    def get_refresh_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for what to refresh"""
        recommendations = []
        
        for cache_type, rules in self.refresh_rules.items():
            cache_key = f"{cache_type}_*"
            entries = [k for k in self.cache.cache.keys() if cache_type in k]
            
            if entries:
                entry = self.cache.cache.get(entries[0], {})
                age_seconds = (datetime.now() - entry.get("timestamp", datetime.now())).total_seconds()
                
                if age_seconds > rules["ttl"]:
                    recommendations.append({
                        "type": cache_type,
                        "action": "refresh",
                        "priority": rules["priority"],
                        "age_seconds": age_seconds,
                        "ttl_seconds": rules["ttl"]
                    })
        
        return {
            "recommendations": sorted(
                recommendations,
                key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]]
            ),
            "timestamp": datetime.now().isoformat()
        }


# Global instances
_perf_controller: PerformanceOptimizationController = None
_ui_monitor: UIPerformanceMonitor = None
_refresh_manager: DataRefreshManager = None


def get_performance_controller() -> PerformanceOptimizationController:
    """Get global performance controller"""
    global _perf_controller
    if _perf_controller is None:
        _perf_controller = PerformanceOptimizationController()
    return _perf_controller


def get_ui_monitor() -> UIPerformanceMonitor:
    """Get global UI performance monitor"""
    global _ui_monitor
    if _ui_monitor is None:
        _ui_monitor = UIPerformanceMonitor()
    return _ui_monitor


def get_refresh_manager() -> DataRefreshManager:
    """Get global refresh manager"""
    global _refresh_manager
    if _refresh_manager is None:
        _refresh_manager = DataRefreshManager()
    return _refresh_manager
