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
        
        # Try multiple ports if 8000 is occupied
        ports = [8000, 8001, 8002, 8003]
        server_started = False
        
        for port in ports:
            try:
                logger.info(f"Attempting to start API server on http://0.0.0.0:{port}")
                uvicorn.run(
                    app,
                    host="0.0.0.0",
                    port=port,
                    log_level="info",
                    access_log=False
                )
                server_started = True
                break
            except OSError as e:
                if "10048" in str(e) or "address already in use" in str(e).lower():
                    logger.warning(f"Port {port} is in use, trying next port...")
                    continue
                else:
                    raise
        
        if not server_started:
            logger.warning("API server could not start on any port, continuing without API server")
            
    except Exception as e:
        logger.warning(f"API server not available: {e}. Bot will continue with trading scheduler only.")


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
        sys.exit(1)
    
    # Start API server in background thread (daemon=True so it doesn't block shutdown)
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    logger.info("API server thread started (daemon mode)")
    
    # Keep main thread alive
    try:
        logger.info("🤖 Trading bot is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        logger.info("Trading bot stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
