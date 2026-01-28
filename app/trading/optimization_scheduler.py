"""Hourly optimization scheduler - runs adaptive risk optimization every hour"""

import threading
import time
from datetime import datetime, timedelta
from app.core.logger import setup_logger
from app.trading.enhanced_optimizer import get_enhanced_optimizer

logger = setup_logger("optimization_scheduler")


class OptimizationScheduler:
    """Scheduler for hourly adaptive risk parameter optimization"""
    
    def __init__(self):
        self.optimizer = get_enhanced_optimizer()  # Use enhanced optimizer
        self.running = False
        self.thread = None
        self.last_run = None
        self.next_run = None
    
    def start(self):
        """Start the optimization scheduler"""
        if self.running:
            logger.warning("Optimization scheduler already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("✅ Optimization scheduler started (hourly)")
    
    def stop(self):
        """Stop the optimization scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("✅ Optimization scheduler stopped")
    
    def _run_loop(self):
        """Main scheduling loop"""
        logger.info("Optimization scheduler loop started")
        
        while self.running:
            try:
                # Calculate next run time (top of hour)
                now = datetime.now()
                next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                wait_seconds = (next_run - now).total_seconds()
                
                self.next_run = next_run
                
                if wait_seconds > 0:
                    logger.info(f"⏱️  Next optimization in {wait_seconds/60:.1f} minutes ({next_run.strftime('%H:%M:%S')})")
                    time.sleep(min(wait_seconds, 60))  # Check every minute
                else:
                    # Execute optimization
                    self._execute_optimization()
            
            except Exception as e:
                logger.error(f"Error in optimization scheduler: {e}", exc_info=True)
                time.sleep(60)
    
    def _execute_optimization(self):
        """Execute the hourly optimization"""
        try:
            self.last_run = datetime.now()
            logger.info(f"🔄 EXECUTING HOURLY OPTIMIZATION at {self.last_run.strftime('%H:%M:%S')}")
            
            # Run optimization cycle
            results = self.optimizer.hourly_optimization_cycle()
            
            logger.info(f"✅ Optimization complete at {datetime.now().strftime('%H:%M:%S')} - {len(results)} tickers processed")
        
        except Exception as e:
            logger.error(f"Error executing optimization: {e}", exc_info=True)


# Global scheduler instance
_scheduler: OptimizationScheduler = None


def get_optimization_scheduler() -> OptimizationScheduler:
    """Get global optimization scheduler"""
    global _scheduler
    if _scheduler is None:
        _scheduler = OptimizationScheduler()
    return _scheduler


def start_optimization_scheduler():
    """Start the global optimization scheduler"""
    scheduler = get_optimization_scheduler()
    scheduler.start()
    return scheduler
