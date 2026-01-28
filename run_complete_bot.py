#!/usr/bin/env python3
"""
Run Complete Trading Bot System
Starts BOTH trading loop (background) AND Streamlit UI (foreground)
"""

import threading
import time
import sys
import subprocess
from pathlib import Path
from app.core.logger import setup_logger
from app.core.database import get_database_manager

logger = setup_logger("complete_bot")


def run_trading_loop():
    """Run the trading scheduler in a separate thread"""
    try:
        from app.api.server import start_trading_scheduler
        logger.info("Starting trading scheduler...")
        start_trading_scheduler()
        logger.info("OK Trading scheduler started")
    except Exception as e:
        logger.error(f"FAILED to start trading scheduler: {e}", exc_info=True)


def run_streamlit_ui():
    """Run Streamlit UI in subprocess"""
    try:
        logger.info("Starting Streamlit UI...")
        result = subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app/main.py", "--server.port=8501"],
            cwd=Path(__file__).parent
        )
        logger.info(f"Streamlit exited with code {result.returncode}")
    except Exception as e:
        logger.error(f"FAILED to start Streamlit: {e}", exc_info=True)


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print(" AI COMPLETE TRADING BOT SYSTEM")
    print("="*80)
    print(" Starting:")
    print("  1. Trading Loop (background scheduler)")
    print("  2. Streamlit UI (http://localhost:8501)")
    print("="*80 + "\n")
    
    try:
        # Initialize database
        print("Initializing database...")
        db = get_database_manager()
        trades = len(db.get_trades()) if db.get_trades() else 0
        decisions = len(db.get_ai_decisions()) if db.get_ai_decisions() else 0
        analysis = len(db.get_analysis_history()) if db.get_analysis_history() else 0
        print(f"OK Database ready: {trades} trades, {decisions} decisions, {analysis} analysis records\n")
        
        # Start trading loop in background thread
        trading_thread = threading.Thread(target=run_trading_loop, daemon=False)
        trading_thread.start()
        logger.info("Trading loop thread started")
        
        # Give trading loop time to start
        time.sleep(2)
        
        # Start Streamlit UI in main thread (blocking)
        print("\nStarting Streamlit UI (http://localhost:8501)...\n")
        print("="*80)
        run_streamlit_ui()
        
    except KeyboardInterrupt:
        print("\n\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"FAILED to start bot: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
