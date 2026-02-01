"""Database manager for storing historical analysis, trades, and AI decisions"""

import sqlite3
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import threading
from app.core.logger import setup_logger

logger = setup_logger("database")


class DatabaseManager:
    """Manages SQLite database for historical data storage"""
    
    def __init__(self, db_path: str = "data/trading_history.db"):
        self.db_path = db_path
        # RLock permite reentrancia cuando save_trade llama a update_trade
        self._lock = threading.RLock()
        self._conn: Optional[sqlite3.Connection] = None
        self._ensure_db_directory()
        self._conn = self._connect()
        self._init_database()

    def _connect(self) -> sqlite3.Connection:
        """Create a SQLite connection with concurrency-friendly settings."""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30,
        )
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=10000;")
        conn.row_factory = sqlite3.Row
        return conn

    def _get_conn(self) -> sqlite3.Connection:
        """Return a shared connection; recreate if closed/broken."""
        try:
            if self._conn is None:
                self._conn = self._connect()
            else:
                # simple health check
                self._conn.execute("SELECT 1")
        except Exception:
            self._conn = self._connect()
        return self._conn
    
    def _ensure_db_directory(self):
        """Ensure data directory exists"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize database schema"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
        
        # Table: analysis_history - Store all technical/sentiment analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,
                
                -- Technical Analysis
                tech_signal VARCHAR(10),
                tech_close REAL,
                tech_rsi REAL,
                tech_ema_fast REAL,
                tech_ema_slow REAL,
                tech_atr REAL,
                tech_trend_bullish BOOLEAN,
                tech_reason TEXT,
                
                -- Sentiment Analysis
                sentiment_score REAL,
                sentiment_summary TEXT,
                sentiment_headlines_count INTEGER,
                
                -- Combined Analysis
                combined_score REAL,
                final_signal VARCHAR(10),
                confidence REAL,
                sources TEXT
            )
        """)
        
        # Create indexes for analysis_history
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_analysis_symbol_timestamp 
                         ON analysis_history(symbol, timestamp)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_analysis_timestamp 
                         ON analysis_history(timestamp)""")
        
        # Table: ai_decisions - Store all AI decisions (enhanced/simple)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,
                
                -- Decision
                action VARCHAR(10) NOT NULL,
                confidence REAL NOT NULL,
                reasoning TEXT,
                
                -- AI Type
                engine_type VARCHAR(20),
                data_sources TEXT,
                web_search_enabled BOOLEAN,
                
                -- Risk Management
                stop_loss REAL,
                take_profit REAL,
                volume_lots REAL,
                risk_ok BOOLEAN,
                
                -- Execution
                executed BOOLEAN DEFAULT 0,
                execution_timestamp DATETIME
            )
        """)
        
        # Create indexes for ai_decisions
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_decisions_symbol_timestamp 
                         ON ai_decisions(symbol, timestamp)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_decisions_executed 
                         ON ai_decisions(executed)""")
        
        # Table: trades - Store all opened/closed trades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket BIGINT UNIQUE,
                symbol VARCHAR(20) NOT NULL,
                
                -- Trade Info
                type VARCHAR(10) NOT NULL,
                volume REAL NOT NULL,
                
                -- Prices
                open_price REAL NOT NULL,
                open_timestamp DATETIME NOT NULL,
                close_price REAL,
                close_timestamp DATETIME,
                
                -- Risk Management
                stop_loss REAL,
                take_profit REAL,
                
                -- P&L
                profit REAL,
                commission REAL,
                swap REAL,
                
                -- Status
                status VARCHAR(20) DEFAULT 'open',
                
                -- Related Decision
                ai_decision_id INTEGER,
                analysis_id INTEGER,
                
                -- Metadata
                comment TEXT
            )
        """)
        
        # Create indexes for trades
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_trades_symbol 
                         ON trades(symbol)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_trades_status 
                         ON trades(status)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_trades_open_timestamp 
                         ON trades(open_timestamp)""")
        
        # Table: performance_metrics - Daily/hourly performance summaries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                period VARCHAR(20) NOT NULL,
                
                -- Trading Stats
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                win_rate REAL,
                
                -- P&L
                gross_profit REAL DEFAULT 0,
                gross_loss REAL DEFAULT 0,
                net_profit REAL DEFAULT 0,
                
                -- Risk Metrics
                max_drawdown REAL,
                sharpe_ratio REAL,
                profit_factor REAL,
                
                -- Account
                starting_balance REAL,
                ending_balance REAL,
                equity_peak REAL
            )
        """)
        
        # Create indexes for performance_metrics
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                         ON performance_metrics(timestamp)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_metrics_period 
                         ON performance_metrics(period)""")
        
        # Table: web_search_cache - Cache web search results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS web_search_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                query_type VARCHAR(50) NOT NULL,
                
                -- Search Results
                snippets TEXT,
                snippet_count INTEGER,
                success BOOLEAN,
                
                -- Cache TTL
                expires_at DATETIME
            )
        """)
        
        # Create indexes for web_search_cache
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_cache_symbol_type 
                         ON web_search_cache(symbol, query_type)""")
        cursor.execute("""CREATE INDEX IF NOT EXISTS idx_cache_expires 
                         ON web_search_cache(expires_at)""")
        
        conn.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    def save_analysis(self, analysis: Dict[str, Any]) -> int:
        """Save analysis to database"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
        
        try:
            tech = analysis.get('technical', {})
            tech_data = tech.get('data', {}) if tech else {}
            sentiment = analysis.get('sentiment', {})
            
            cursor.execute("""
                INSERT INTO analysis_history (
                    timestamp, symbol, timeframe,
                    tech_signal, tech_close, tech_rsi, tech_ema_fast, tech_ema_slow,
                    tech_atr, tech_trend_bullish, tech_reason,
                    sentiment_score, sentiment_summary, sentiment_headlines_count,
                    combined_score, final_signal, confidence, sources
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis.get('timestamp', datetime.now().isoformat()),
                analysis.get('symbol'),
                analysis.get('timeframe', 'M15'),
                tech.get('signal') if tech else None,
                tech_data.get('close'),
                tech_data.get('rsi'),
                tech_data.get('ema_fast'),
                tech_data.get('ema_slow'),
                tech_data.get('atr'),
                tech_data.get('trend_bullish'),
                tech.get('reason') if tech else None,
                sentiment.get('score') if sentiment else None,
                sentiment.get('summary') if sentiment else None,
                len(sentiment.get('headlines', [])) if sentiment else 0,
                analysis.get('combined_score', 0.0),
                analysis.get('signal', 'HOLD'),
                analysis.get('confidence', 0.0),
                json.dumps(analysis.get('available_sources', []))
            ))
            
            analysis_id = cursor.lastrowid
            conn.commit()
            logger.debug(f"Saved analysis for {analysis.get('symbol')} (id={analysis_id})")
            return analysis_id
            
        except Exception as e:
            logger.error(f"Error saving analysis: {e}", exc_info=True)
            conn.rollback()
            return -1
    
    def save_ai_decision(self, symbol: str, timeframe: str, decision: Any, 
                        engine_type: str = 'simple', data_sources: List[str] = None) -> int:
        """Save AI decision to database"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO ai_decisions (
                    timestamp, symbol, timeframe,
                    action, confidence, reasoning,
                    engine_type, data_sources, web_search_enabled,
                    stop_loss, take_profit, volume_lots, risk_ok
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                symbol,
                timeframe,
                decision.action,
                decision.confidence,
                decision.reasoning,
                engine_type,
                json.dumps(data_sources or []),
                engine_type == 'enhanced',
                getattr(decision, 'stop_loss', None),
                getattr(decision, 'take_profit', None),
                getattr(decision, 'volume_lots', None),
                getattr(decision, 'risk_ok', True)
            ))
            
            decision_id = cursor.lastrowid
            conn.commit()
            logger.debug(f"Saved AI decision for {symbol} (id={decision_id})")
            return decision_id
            
        except Exception as e:
            logger.error(f"Error saving AI decision: {e}", exc_info=True)
            conn.rollback()
            return -1
    
    def save_trade(self, trade_info: Dict[str, Any], ai_decision_id: int = None) -> int:
        """Save trade to database"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO trades (
                    ticket, symbol, type, volume,
                    open_price, open_timestamp,
                    close_price, close_timestamp,
                    stop_loss, take_profit,
                    profit, commission, swap,
                    status, ai_decision_id, comment
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_info.get('ticket'),
                trade_info.get('symbol'),
                trade_info.get('type'),
                trade_info.get('volume'),
                trade_info.get('open_price'),
                trade_info.get('open_timestamp', datetime.now().isoformat()),
                trade_info.get('close_price'),
                trade_info.get('close_timestamp'),
                trade_info.get('stop_loss'),
                trade_info.get('take_profit'),
                trade_info.get('profit'),
                trade_info.get('commission'),
                trade_info.get('swap'),
                trade_info.get('status', 'open'),
                ai_decision_id,
                trade_info.get('comment')
            ))
            
            trade_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Saved trade {trade_info.get('ticket')} (id={trade_id})")
            return trade_id
            
        except sqlite3.IntegrityError:
            # Trade already exists, update it
            logger.debug(f"Trade {trade_info.get('ticket')} exists, updating...")
            return self.update_trade(trade_info.get('ticket'), trade_info)
        except Exception as e:
            logger.error(f"Error saving trade: {e}", exc_info=True)
            conn.rollback()
            return -1
    
    def update_trade(self, ticket: int, trade_info: Dict[str, Any]) -> bool:
        """Update existing trade"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    UPDATE trades SET
                        close_price = ?,
                        close_timestamp = ?,
                        profit = ?,
                        commission = ?,
                        swap = ?,
                        status = ?
                    WHERE ticket = ?
                """, (
                    trade_info.get('close_price'),
                    trade_info.get('close_timestamp'),
                    trade_info.get('profit'),
                    trade_info.get('commission'),
                    trade_info.get('swap'),
                    trade_info.get('status', 'closed'),
                    ticket
                ))
                
                conn.commit()
                logger.debug(f"Updated trade {ticket}")
                return True
                
            except Exception as e:
                logger.error(f"Error updating trade: {e}", exc_info=True)
                conn.rollback()
                return False
    
    def get_analysis_history(self, symbol: str = None, days: int = 7) -> List[Dict]:
        """Get analysis history"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
        
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            
            if symbol:
                cursor.execute("""
                    SELECT * FROM analysis_history 
                    WHERE symbol = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (symbol, since))
            else:
                cursor.execute("""
                    SELECT * FROM analysis_history 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (since,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.commit()
    
    def get_ai_decisions(self, symbol: str = None, days: int = 7, 
                        executed_only: bool = False) -> List[Dict]:
        """Get AI decisions"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
        
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            
            query = "SELECT * FROM ai_decisions WHERE timestamp >= ?"
            params = [since]
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if executed_only:
                query += " AND executed = 1"
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.commit()
    
    def get_trades(self, symbol: str = None, status: str = None, days: int = 30) -> List[Dict]:
        """Get trades"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
        
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            
            query = "SELECT * FROM trades WHERE open_timestamp >= ?"
            params = [since]
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY open_timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.commit()

    def get_closed_trades(
        self,
        start_date: datetime,
        end_date: datetime,
        symbol: Optional[str] = None,
    ) -> List[Dict]:
        """Get closed trades within a date range (close_timestamp)."""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()

        try:
            query = """
                SELECT * FROM trades
                WHERE close_timestamp IS NOT NULL
                  AND status = 'closed'
                  AND close_timestamp >= ?
                  AND close_timestamp <= ?
            """
            params = [start_date.isoformat(), end_date.isoformat()]

            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)

            query += " ORDER BY close_timestamp ASC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.commit()
    
    def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get performance summary"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
        
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get trade statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(profit) as net_profit,
                    SUM(CASE WHEN profit > 0 THEN profit ELSE 0 END) as gross_profit,
                    SUM(CASE WHEN profit < 0 THEN ABS(profit) ELSE 0 END) as gross_loss,
                    AVG(profit) as avg_profit
                FROM trades
                WHERE close_timestamp >= ? AND status = 'closed'
            """, (since,))
            
            row = cursor.fetchone()
            
            total_trades = row[0] or 0
            winning_trades = row[1] or 0
            losing_trades = row[2] or 0
            net_profit = row[3] or 0
            gross_profit = row[4] or 0
            gross_loss = row[5] or 0
            avg_profit = row[6] or 0
            
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'net_profit': net_profit,
                'gross_profit': gross_profit,
                'gross_loss': gross_loss,
                'avg_profit': avg_profit,
                'profit_factor': profit_factor
            }
            
        finally:
            conn.commit()
    
    def mark_decision_executed(self, decision_id: int):
        """Mark AI decision as executed"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE ai_decisions 
                SET executed = 1, execution_timestamp = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), decision_id))
            
            conn.commit()
            logger.debug(f"Marked decision {decision_id} as executed")

        except Exception as e:
            logger.error(f"Error marking decision {decision_id} as executed: {e}", exc_info=True)
            conn.rollback()


# Global instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_database() -> DatabaseManager:
    """Backward-compatible alias"""
    return get_database_manager()
