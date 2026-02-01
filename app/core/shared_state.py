"""
Shared state manager for bot status and metrics.
Allows the UI to read bot status without connecting to MT5.
"""

import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.logger import setup_logger

logger = setup_logger("shared_state")


class SharedStateManager:
    """Manages shared state between bot and UI using a JSON file"""
    
    def __init__(self, state_file: str = "data/bot_state.json"):
        self.state_file = Path(state_file)
        self._lock = threading.Lock()
        self._ensure_state_directory()
        
    def _ensure_state_directory(self):
        """Ensure data directory exists"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
    def update_state(self, state_data: Dict[str, Any]) -> bool:
        """Update the shared state"""
        try:
            with self._lock:
                # Add timestamp
                state_data['last_update'] = datetime.now().isoformat()
                
                # Write to file
                with open(self.state_file, 'w') as f:
                    json.dump(state_data, f, indent=2)
                return True
        except Exception as e:
            logger.error(f"Failed to update state: {e}")
            return False
    
    def get_state(self) -> Optional[Dict[str, Any]]:
        """Read the current shared state"""
        try:
            with self._lock:
                if not self.state_file.exists():
                    return None
                    
                with open(self.state_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read state: {e}")
            return None
    
    def update_mt5_status(self, connected: bool, account: int = 0, 
                          balance: float = 0.0, equity: float = 0.0,
                          margin_free: float = 0.0, margin_level: float = 0.0):
        """Update MT5 connection status"""
        state = self.get_state() or {}
        state['mt5'] = {
            'connected': connected,
            'account': account,
            'balance': balance,
            'equity': equity,
            'margin_free': margin_free,
            'margin_level': margin_level,
        }
        return self.update_state(state)
    
    def update_trading_stats(self, open_positions: int = 0, 
                            total_exposure: float = 0.0,
                            daily_trades: int = 0,
                            win_rate: float = 0.0):
        """Update trading statistics"""
        state = self.get_state() or {}
        state['trading'] = {
            'open_positions': open_positions,
            'total_exposure': total_exposure,
            'daily_trades': daily_trades,
            'win_rate': win_rate,
        }
        return self.update_state(state)
    
    def update_bot_status(self, running: bool, mode: str = "SCALPING",
                         last_analysis: Optional[str] = None):
        """Update bot running status"""
        state = self.get_state() or {}
        state['bot'] = {
            'running': running,
            'mode': mode,
            'last_analysis': last_analysis or datetime.now().isoformat(),
        }
        return self.update_state(state)


# Global instance
_shared_state_manager: Optional[SharedStateManager] = None


def get_shared_state_manager() -> SharedStateManager:
    """Get or create the shared state manager singleton"""
    global _shared_state_manager
    if _shared_state_manager is None:
        _shared_state_manager = SharedStateManager()
    return _shared_state_manager
