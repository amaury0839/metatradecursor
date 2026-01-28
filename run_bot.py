#!/usr/bin/env python3
"""Standalone bot runner - DOES NOT use Streamlit - ROBUST VERSION"""

import sys
from pathlib import Path
import time
import signal
import os
import logging
import threading

# Suppress Streamlit warnings about ScriptRunContext
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime').setLevel(logging.ERROR)

# Set Streamlit to bare mode (prevents ScriptRunContext errors)
os.environ['STREAMLIT_LOGGER_LEVEL'] = 'error'

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_config
from app.core.logger import setup_logger
from app.core.scheduler import TradingScheduler
from app.core.database import get_database_manager
from app.trading.mt5_client import get_mt5_client
from app.main import main_trading_loop

logger = setup_logger("bot_runner")

# Global scheduler for signal handling
scheduler = None
_should_exit = False


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global scheduler, _should_exit
    logger.warning(f"⚠️ Signal {sig} received - graceful shutdown initiated")
    _should_exit = True
    if scheduler and scheduler.is_running():
        scheduler.stop()
        logger.info("✅ Scheduler stopped")
    time.sleep(1)
    sys.exit(0)


def main():
    """Main bot runner with robust error handling"""
    global scheduler, _should_exit
    
    logger.info("="*80)
    logger.info("🤖 TRADING BOT STARTED (Standalone Mode - ROBUST)")
    logger.info("="*80)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Load config
        config = get_config()
        logger.info(f"✅ Config loaded: {len(config.trading.default_symbols)} symbols")
        
        # Initialize and connect MT5
        mt5 = get_mt5_client()
        logger.info("✅ MT5 client initialized")
        if mt5.connect():
            logger.info("✅ MT5 connected and authenticated")
            account_info = mt5.get_account_info()
            if account_info:
                logger.info(f"   Account: {account_info.get('login')}, Balance: ${account_info.get('balance', 0):.2f}")
        else:
            logger.warning("⚠️ MT5 connection failed; bot will continue with technical-only fallback mode")
        
        # Initialize database
        db = get_database_manager()
        logger.info("✅ Database initialized")
        
        # Start optimization scheduler (hourly adaptive risk parameters)
        from app.trading.optimization_scheduler import start_optimization_scheduler
        opt_scheduler = start_optimization_scheduler()
        logger.info("✅ Optimization scheduler started (will optimize every hour)")
        
        # Start trading scheduler with high robustness
        logger.info("🎯 Starting trading scheduler...")
        scheduler = TradingScheduler(main_trading_loop)
        scheduler.start()
        
        if scheduler.is_running():
            logger.info(f"✅ Trading scheduler started successfully ({scheduler.interval_seconds}s interval)")
        else:
            logger.error("❌ Scheduler failed to start")
            sys.exit(1)
        
        # Keep running indefinitely with robust error handling
        logger.info("📍 Bot is running. Press Ctrl+C to stop.")
        cycle_count = 0
        
        while not _should_exit:
            try:
                cycle_count += 1
                
                # Check scheduler health
                if not scheduler.is_running():
                    logger.error("⚠️ Scheduler stopped unexpectedly! Restarting...")
                    scheduler = TradingScheduler(main_trading_loop)
                    scheduler.start()
                    logger.info("✅ Scheduler restarted")
                
                # Log health every 60 seconds
                if cycle_count % 12 == 0:  # 5s * 12 = 60s
                    logger.info(f"💓 Bot health check: scheduler_running={scheduler.is_running()}, cycles={cycle_count}")
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(5)
                continue
    
    except KeyboardInterrupt:
        logger.warning("⚠️ KeyboardInterrupt - initiating graceful shutdown")
        _should_exit = True
        if scheduler and scheduler.is_running():
            scheduler.stop()
        logger.info("✅ Bot stopped gracefully")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}", exc_info=True)
        if scheduler and scheduler.is_running():
            scheduler.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
