"""Run local trading bot with API server"""

import threading
import uvicorn
from app.api.server import app, start_trading_scheduler
from app.core.logger import setup_logger

logger = setup_logger("local_bot")


def main():
    """Main entry point"""
    logger.info("Starting AI Forex Trading Bot - Local Mode with API Server")
    
    # Start trading scheduler (runs in background)
    start_trading_scheduler()
    
    # Start API server (blocking)
    try:
        logger.info("API server starting on http://0.0.0.0:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        logger.info("Trading bot stopped")


if __name__ == "__main__":
    main()
