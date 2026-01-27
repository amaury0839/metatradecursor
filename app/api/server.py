"""FastAPI server for remote UI access to trading bot"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import threading
from app.core.config import get_config
from app.core.state import get_state_manager
from app.core.scheduler import TradingScheduler
from app.trading.mt5_client import get_mt5_client
from app.trading.portfolio import get_portfolio_manager
from app.core.logger import setup_logger
from app.core.analysis_logger import get_analysis_logger
from app.main import main_trading_loop

logger = setup_logger("api_server")

app = FastAPI(title="AI Forex Trading Bot API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-connect to MT5 on startup
@app.on_event("startup")
def startup_event():
    """Auto-connect to MT5 on server startup"""
    logger.info("Starting up API server...")
    logger.info("🤖 Bot en modo HYBRID: Ejecutando con señales técnicas")
    logger.info("   Cuando MT5 se conecte, usará datos en vivo")
    
    # Conectar a MT5 en background (no-blocking)
    def connect_mt5_background():
        try:
            mt5 = get_mt5_client()
            if mt5.connect():
                logger.info("✅ MT5 conectado!")
            else:
                logger.info("⚠️ MT5 no disponible - usando solo señales técnicas")
        except Exception as e:
            logger.info(f"⚠️ MT5 error: {e} - continuando con fallback")
    
    # Start MT5 connection in background thread
    mt5_thread = threading.Thread(target=connect_mt5_background, daemon=True)
    mt5_thread.start()

# Global scheduler instance
_scheduler: Optional[TradingScheduler] = None

# CORS middleware for Streamlit Cloud
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit Cloud URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ConnectionStatus(BaseModel):
    connected: bool
    mode: str
    account_info: Optional[Dict[str, Any]] = None


class TradingStatus(BaseModel):
    scheduler_running: bool
    kill_switch_active: bool
    open_positions: int
    equity: Optional[float] = None
    balance: Optional[float] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "AI Forex Trading Bot API"}


@app.get("/status/connection", response_model=ConnectionStatus)
async def get_connection_status():
    """Get MT5 connection status"""
    mt5 = get_mt5_client()
    config = get_config()
    
    account_info = None
    if mt5.is_connected():
        account_info = mt5.get_account_info()
    
    return ConnectionStatus(
        connected=mt5.is_connected(),
        mode=config.trading.mode,
        account_info=account_info
    )


@app.post("/connection/connect")
async def connect_mt5():
    """Connect to MT5"""
    mt5 = get_mt5_client()
    if mt5.connect():
        return {"success": True, "message": "Connected to MT5"}
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to MT5")


@app.post("/connection/disconnect")
async def disconnect_mt5():
    """Disconnect from MT5"""
    mt5 = get_mt5_client()
    mt5.disconnect()
    return {"success": True, "message": "Disconnected from MT5"}


@app.get("/status/trading", response_model=TradingStatus)
async def get_trading_status():
    """Get trading status"""
    global _scheduler
    state = get_state_manager()
    portfolio = get_portfolio_manager()
    mt5 = get_mt5_client()
    
    account_info = mt5.get_account_info()
    equity = account_info.get('equity') if account_info else None
    balance = account_info.get('balance') if account_info else None
    
    # Check if scheduler is running
    scheduler_running = _scheduler.is_running() if _scheduler else False
    
    return TradingStatus(
        scheduler_running=scheduler_running,
        kill_switch_active=state.is_kill_switch_active(),
        open_positions=portfolio.get_open_positions_count(),
        equity=equity,
        balance=balance
    )


@app.get("/positions")
async def get_positions():
    """Get open positions"""
    portfolio = get_portfolio_manager()
    positions = portfolio.get_open_positions()
    return {"positions": positions}


@app.get("/decisions")
async def get_decisions(limit: int = 100):
    """Get recent decisions"""
    state = get_state_manager()
    decisions = state.get_recent_decisions(limit=limit)
    return {"decisions": decisions}


@app.get("/trades")
async def get_trades(limit: int = 100):
    """Get recent trades"""
    state = get_state_manager()
    trades = state.get_recent_trades(limit=limit)
    return {"trades": trades}


@app.post("/control/kill-switch/activate")
async def activate_kill_switch():
    """Activate kill switch"""
    state = get_state_manager()
    state.activate_kill_switch()
    return {"success": True, "message": "Kill switch activated"}


@app.post("/control/kill-switch/deactivate")
async def deactivate_kill_switch():
    """Deactivate kill switch"""
    state = get_state_manager()
    state.deactivate_kill_switch()
    return {"success": True, "message": "Kill switch deactivated"}


@app.post("/control/scheduler/start")
async def start_scheduler():
    """Start trading scheduler"""
    global _scheduler
    if _scheduler and _scheduler.is_running():
        return {"success": False, "message": "Scheduler already running"}
    
    _scheduler = TradingScheduler(main_trading_loop)
    _scheduler.start()
    return {"success": True, "message": "Scheduler started"}


@app.post("/control/scheduler/stop")
async def stop_scheduler():
    """Stop trading scheduler"""
    global _scheduler
    if not _scheduler or not _scheduler.is_running():
        return {"success": False, "message": "Scheduler not running"}
    
    _scheduler.stop()
    return {"success": True, "message": "Scheduler stopped"}


def start_trading_scheduler():
    """Start trading scheduler (called on server startup)"""
    global _scheduler
    if _scheduler is None:
        try:
            _scheduler = TradingScheduler(main_trading_loop)
            _scheduler.start()
            logger.info("Trading scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            _scheduler = None
            # Don't fail - server can still run without scheduler


@app.get("/symbols")
async def get_symbols():
    """Get available symbols"""
    mt5 = get_mt5_client()
    symbols = mt5.get_symbols()
    return {"symbols": symbols}


@app.get("/logs/analysis")
async def get_analysis_logs(
    symbol: Optional[str] = None,
    analysis_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """Get analysis logs with optional filters"""
    logger = get_analysis_logger()
    logs = logger.get_logs(
        symbol=symbol,
        analysis_type=analysis_type,
        status=status,
        limit=limit
    )
    return {"logs": logs, "total": len(logs)}


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server"""
    logger.info(f"Starting API server on {host}:{port}")
    start_trading_scheduler()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
