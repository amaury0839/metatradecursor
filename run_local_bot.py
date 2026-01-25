"""Run local trading bot with API server"""

import threading
import time
import sys
from app.core.logger import setup_logger

logger = setup_logger("local_bot")


def run_api_server():
    """Run the API server in a separate thread"""
    try:
        import uvicorn
        from app.api.server import app
        
        logger.info("Starting API server on http://0.0.0.0:8000")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=False
        )
    except Exception as e:
        logger.error(f"API server error: {e}", exc_info=True)


def main():
    """Main entry point"""
    logger.info("Starting AI Forex Trading Bot - Local Mode with API Server")
    
    # Import after logging is configured
    from app.api.server import start_trading_scheduler
    
    # Start trading scheduler
    try:
        start_trading_scheduler()
        logger.info("✅ Trading scheduler started")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    
    # Start API server in background thread
    api_thread = threading.Thread(target=run_api_server, daemon=False)
    api_thread.start()
    logger.info("API server thread started")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        logger.info("Trading bot stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
