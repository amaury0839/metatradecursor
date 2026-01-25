"""Client for connecting to local trading bot API"""

import httpx
from typing import Optional, Dict, Any, List
from app.core.logger import setup_logger

logger = setup_logger("api_client")


class TradingBotAPIClient:
    """Client for connecting to local trading bot API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get MT5 connection status"""
        try:
            response = await self.client.get(f"{self.base_url}/status/connection")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {"connected": False, "mode": "UNKNOWN", "account_info": None}
    
    async def connect_mt5(self) -> bool:
        """Connect to MT5"""
        try:
            response = await self.client.post(f"{self.base_url}/connection/connect")
            response.raise_for_status()
            return response.json().get("success", False)
        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}")
            return False
    
    async def disconnect_mt5(self) -> bool:
        """Disconnect from MT5"""
        try:
            response = await self.client.post(f"{self.base_url}/connection/disconnect")
            response.raise_for_status()
            return response.json().get("success", False)
        except Exception as e:
            logger.error(f"Error disconnecting from MT5: {e}")
            return False
    
    async def get_trading_status(self) -> Dict[str, Any]:
        """Get trading status"""
        try:
            response = await self.client.get(f"{self.base_url}/status/trading")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting trading status: {e}")
            return {
                "scheduler_running": False,
                "kill_switch_active": False,
                "open_positions": 0,
                "equity": None,
                "balance": None
            }
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get open positions"""
        try:
            response = await self.client.get(f"{self.base_url}/positions")
            response.raise_for_status()
            return response.json().get("positions", [])
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []
    
    async def get_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent decisions"""
        try:
            response = await self.client.get(f"{self.base_url}/decisions", params={"limit": limit})
            response.raise_for_status()
            return response.json().get("decisions", [])
        except Exception as e:
            logger.error(f"Error getting decisions: {e}")
            return []
    
    async def get_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades"""
        try:
            response = await self.client.get(f"{self.base_url}/trades", params={"limit": limit})
            response.raise_for_status()
            return response.json().get("trades", [])
        except Exception as e:
            logger.error(f"Error getting trades: {e}")
            return []
    
    async def activate_kill_switch(self) -> bool:
        """Activate kill switch"""
        try:
            response = await self.client.post(f"{self.base_url}/control/kill-switch/activate")
            response.raise_for_status()
            return response.json().get("success", False)
        except Exception as e:
            logger.error(f"Error activating kill switch: {e}")
            return False
    
    async def deactivate_kill_switch(self) -> bool:
        """Deactivate kill switch"""
        try:
            response = await self.client.post(f"{self.base_url}/control/kill-switch/deactivate")
            response.raise_for_status()
            return response.json().get("success", False)
        except Exception as e:
            logger.error(f"Error deactivating kill switch: {e}")
            return False
    
    async def get_symbols(self) -> List[str]:
        """Get available symbols"""
        try:
            response = await self.client.get(f"{self.base_url}/symbols")
            response.raise_for_status()
            return response.json().get("symbols", [])
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
            return []
    
    async def is_available(self) -> bool:
        """Check if API server is available"""
        try:
            response = await self.client.get(f"{self.base_url}/")
            response.raise_for_status()
            return True
        except Exception:
            return False


# Global API client instance
_api_client: Optional[TradingBotAPIClient] = None


def get_api_client(base_url: Optional[str] = None) -> TradingBotAPIClient:
    """Get global API client instance"""
    global _api_client
    if _api_client is None:
        url = base_url or "http://localhost:8000"
        _api_client = TradingBotAPIClient(url)
    return _api_client
