"""Runtime state management and persistence"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import threading
from app.core.config import get_config
from app.core.logger import setup_logger

logger = setup_logger("state")


@dataclass
class DecisionAudit:
    """Audit record for a trading decision"""
    timestamp: str
    symbol: str
    timeframe: str
    signal: str  # BUY, SELL, HOLD, CLOSE
    confidence: float
    action: str  # Actual action taken
    volume_lots: Optional[float] = None
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None
    reason: List[str] = None
    prompt_hash: Optional[str] = None
    gemini_response: Optional[Dict[str, Any]] = None
    risk_checks_passed: bool = False
    execution_success: bool = False
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.reason is None:
            self.reason = []


@dataclass
class TradeRecord:
    """Record of an executed trade"""
    trade_id: Optional[int] = None
    timestamp: str = ""
    symbol: str = ""
    action: str = ""  # BUY, SELL, CLOSE
    volume_lots: float = 0.0
    entry_price: float = 0.0
    sl_price: Optional[float] = None
    tp_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    commission: Optional[float] = None
    swap: Optional[float] = None
    decision_id: Optional[int] = None  # Link to DecisionAudit


class StateManager:
    """Manages runtime state and persistence"""
    
    def __init__(self, db_path: str = "data/trading_bot.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()
        
        # Runtime state
        self.kill_switch_active = False
        self.last_decision_time: Dict[str, datetime] = {}  # symbol -> last decision time
        self.daily_pnl: float = 0.0
        self.daily_trade_count: int = 0
        self.current_equity: float = 0.0
        self.current_balance: float = 0.0
        self.max_equity: float = 0.0  # For drawdown calculation
    
    def _init_db(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Decisions audit table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decisions_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL,
                    action TEXT NOT NULL,
                    volume_lots REAL,
                    sl_price REAL,
                    tp_price REAL,
                    reason TEXT,
                    prompt_hash TEXT,
                    gemini_response TEXT,
                    risk_checks_passed INTEGER,
                    execution_success INTEGER,
                    error_message TEXT
                )
            """)
            
            # Trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    volume_lots REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    sl_price REAL,
                    tp_price REAL,
                    exit_price REAL,
                    pnl REAL,
                    commission REAL,
                    swap REAL,
                    decision_id INTEGER,
                    FOREIGN KEY (decision_id) REFERENCES decisions_audit(id)
                )
            """)
            
            # Config snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    config_json TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    def save_decision(self, decision: DecisionAudit) -> int:
        """Save a decision audit record and return its ID"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO decisions_audit (
                        timestamp, symbol, timeframe, signal, confidence,
                        action, volume_lots, sl_price, tp_price, reason,
                        prompt_hash, gemini_response, risk_checks_passed,
                        execution_success, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    decision.timestamp,
                    decision.symbol,
                    decision.timeframe,
                    decision.signal,
                    decision.confidence,
                    decision.action,
                    decision.volume_lots,
                    decision.sl_price,
                    decision.tp_price,
                    json.dumps(decision.reason),
                    decision.prompt_hash,
                    json.dumps(decision.gemini_response) if decision.gemini_response else None,
                    1 if decision.risk_checks_passed else 0,
                    1 if decision.execution_success else 0,
                    decision.error_message
                ))
                decision_id = cursor.lastrowid
                conn.commit()
                return decision_id
    
    def save_trade(self, trade: TradeRecord) -> int:
        """Save a trade record and return its ID"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trades (
                        timestamp, symbol, action, volume_lots, entry_price,
                        sl_price, tp_price, exit_price, pnl, commission,
                        swap, decision_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade.timestamp,
                    trade.symbol,
                    trade.action,
                    trade.volume_lots,
                    trade.entry_price,
                    trade.sl_price,
                    trade.tp_price,
                    trade.exit_price,
                    trade.pnl,
                    trade.commission,
                    trade.swap,
                    trade.decision_id
                ))
                trade_id = cursor.lastrowid
                conn.commit()
                return trade_id
    
    def get_recent_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent decision audit records"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM decisions_audit
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trade records"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM trades
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def activate_kill_switch(self):
        """Activate kill switch"""
        self.kill_switch_active = True
        logger.warning("Kill switch activated - all trading operations stopped")
    
    def deactivate_kill_switch(self):
        """Deactivate kill switch"""
        self.kill_switch_active = False
        logger.info("Kill switch deactivated")
    
    def is_kill_switch_active(self) -> bool:
        """Check if kill switch is active"""
        return self.kill_switch_active
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at start of new trading day)"""
        self.daily_pnl = 0.0
        self.daily_trade_count = 0
        logger.info("Daily statistics reset")


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get global state manager instance"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager
