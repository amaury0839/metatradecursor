"""Scheduling and orchestration for trading loop"""

import time
from datetime import datetime
from typing import Callable, Optional
from threading import Thread, Event
from app.core.config import get_config
from app.core.logger import setup_logger
from app.core.state import get_state_manager

logger = setup_logger("scheduler")


class TradingScheduler:
    """Manages the main trading loop"""
    
    def __init__(self, trading_callback: Callable):
        """
        Initialize scheduler
        
        Args:
            trading_callback: Function to call on each cycle (should handle all trading logic)
        """
        self.config = get_config()
        self.state = get_state_manager()
        self.trading_callback = trading_callback
        self._running = False
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        self.interval_seconds = self.config.trading.polling_interval_seconds
    
    def start(self):
        """Start the scheduler"""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self._running = True
        self._stop_event.clear()
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"Scheduler started with interval {self.interval_seconds}s")
    
    def stop(self):
        """Stop the scheduler"""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("Scheduler stopped")
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._running
    
    def _run_loop(self):
        """Main scheduling loop"""
        logger.info("Trading loop started")
        
        while self._running and not self._stop_event.is_set():
            try:
                # Check kill switch
                if self.state.is_kill_switch_active():
                    logger.debug("Kill switch active, skipping cycle")
                    time.sleep(self.interval_seconds)
                    continue
                
                # Execute trading callback
                start_time = time.time()
                self.trading_callback()
                elapsed = time.time() - start_time
                
                logger.debug(f"Trading cycle completed in {elapsed:.2f}s")
                
                # Sleep for remaining interval
                sleep_time = max(0, self.interval_seconds - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error("Error in trading loop", exc_info=e)
                # Continue running even on error
                time.sleep(self.interval_seconds)
        
        logger.info("Trading loop ended")
    
    def set_interval(self, seconds: int):
        """Update polling interval"""
        self.interval_seconds = max(1, seconds)
        logger.info(f"Polling interval updated to {self.interval_seconds}s")
