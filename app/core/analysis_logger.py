"""Analysis logging system for real-time UI display"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque
import threading
import json

@dataclass
class AnalysisLog:
    """Single analysis log entry"""
    timestamp: str
    symbol: str
    timeframe: str
    analysis_type: str  # 'TECHNICAL', 'AI', 'EXECUTION', 'RISK'
    status: str  # 'SUCCESS', 'WARNING', 'ERROR'
    message: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class AnalysisLogger:
    """Manages analysis logs for display in UI"""
    
    def __init__(self, max_entries: int = 500):
        self.max_entries = max_entries
        self.logs: deque = deque(maxlen=max_entries)
        self.lock = threading.Lock()
    
    def log_analysis(
        self,
        symbol: str,
        timeframe: str,
        analysis_type: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an analysis event
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Timeframe (e.g., 'M15')
            analysis_type: Type of analysis ('TECHNICAL', 'AI', 'EXECUTION', 'RISK')
            status: Status ('SUCCESS', 'WARNING', 'ERROR')
            message: Human-readable message
            details: Optional dictionary with additional details
        """
        log_entry = AnalysisLog(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol=symbol,
            timeframe=timeframe,
            analysis_type=analysis_type,
            status=status,
            message=message,
            details=details or {}
        )
        
        with self.lock:
            self.logs.append(log_entry)
    
    def log_technical_analysis(
        self,
        symbol: str,
        timeframe: str,
        signal: str,
        rsi: Optional[float] = None,
        ema_signal: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log technical analysis result
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            signal: Trading signal (BUY, SELL, HOLD)
            rsi: RSI value
            ema_signal: EMA signal description
            details: Additional details
        """
        message_parts = [f"Signal: {signal}"]
        if rsi is not None:
            message_parts.append(f"RSI: {rsi:.2f}")
        if ema_signal:
            message_parts.append(f"EMA: {ema_signal}")
        
        details_dict = details or {}
        if rsi is not None:
            details_dict['rsi'] = rsi
        if ema_signal:
            details_dict['ema_signal'] = ema_signal
        
        self.log_analysis(
            symbol=symbol,
            timeframe=timeframe,
            analysis_type="TECHNICAL",
            status="SUCCESS",
            message=" | ".join(message_parts),
            details=details_dict
        )
    
    def log_ai_analysis(
        self,
        symbol: str,
        timeframe: str,
        decision: str,
        confidence: Optional[float] = None,
        reasoning: Optional[str] = None,
        status: str = "SUCCESS"
    ) -> None:
        """Log AI analysis result"""
        message_parts = [f"Decision: {decision}"]
        if confidence is not None:
            message_parts.append(f"Confidence: {confidence:.2%}")
        if reasoning:
            message_parts.append(f"Reasoning: {reasoning}")
        
        details_dict = {}
        if confidence is not None:
            details_dict['confidence'] = confidence
        if reasoning:
            details_dict['reasoning'] = reasoning
        
        self.log_analysis(
            symbol=symbol,
            timeframe=timeframe,
            analysis_type="AI",
            status=status,
            message=" | ".join(message_parts),
            details=details_dict
        )
    
    def log_execution(
        self,
        symbol: str,
        action: str,
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log trade execution"""
        message = f"Execution: {action}"
        self.log_analysis(
            symbol=symbol,
            timeframe="",
            analysis_type="EXECUTION",
            status=status,
            message=message,
            details=details
        )
    
    def log_risk_check(
        self,
        symbol: str,
        check_name: str,
        passed: bool,
        reason: Optional[str] = None
    ) -> None:
        """Log risk check result"""
        status = "SUCCESS" if passed else "WARNING"
        message = f"Risk Check: {check_name} - {'PASSED' if passed else 'BLOCKED'}"
        if reason:
            message += f" ({reason})"
        
        self.log_analysis(
            symbol=symbol,
            timeframe="",
            analysis_type="RISK",
            status=status,
            message=message,
            details={"passed": passed, "reason": reason}
        )
    
    def get_logs(
        self,
        symbol: Optional[str] = None,
        analysis_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get filtered logs
        
        Args:
            symbol: Filter by symbol
            analysis_type: Filter by analysis type
            status: Filter by status
            limit: Maximum number of logs to return
        
        Returns:
            List of log entries as dictionaries
        """
        with self.lock:
            logs = list(self.logs)
        
        # Apply filters
        if symbol:
            logs = [l for l in logs if l.symbol == symbol]
        if analysis_type:
            logs = [l for l in logs if l.analysis_type == analysis_type]
        if status:
            logs = [l for l in logs if l.status == status]
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        if limit:
            logs = logs[:limit]
        
        return [log.to_dict() for log in logs]
    
    def get_recent_logs(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get most recent logs"""
        return self.get_logs(limit=count)
    
    def get_symbol_summary(self, symbol: str) -> Dict[str, Any]:
        """Get summary of analyses for a symbol"""
        logs = self.get_logs(symbol=symbol)
        
        if not logs:
            return {"symbol": symbol, "count": 0}
        
        summary = {
            "symbol": symbol,
            "count": len(logs),
            "latest": logs[0],  # Newest is first after sorting
            "by_type": {},
            "by_status": {}
        }
        
        for log in logs:
            # Count by type
            atype = log["analysis_type"]
            summary["by_type"][atype] = summary["by_type"].get(atype, 0) + 1
            
            # Count by status
            astatus = log["status"]
            summary["by_status"][astatus] = summary["by_status"].get(astatus, 0) + 1
        
        return summary
    
    def clear_logs(self) -> None:
        """Clear all logs"""
        with self.lock:
            self.logs.clear()


# Global singleton instance
_analysis_logger: Optional[AnalysisLogger] = None


def get_analysis_logger() -> AnalysisLogger:
    """Get or create global analysis logger instance"""
    global _analysis_logger
    if _analysis_logger is None:
        _analysis_logger = AnalysisLogger()
    return _analysis_logger
