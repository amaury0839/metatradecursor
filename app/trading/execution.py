"""Order execution and management"""

from typing import Optional, Dict, Tuple
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import get_config
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client
from app.trading.risk import get_risk_manager
from app.trading.market_status import get_market_status

# Try to import MetaTrader5 - optional dependency
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    # Define constants for demo mode
    class MockMT5:
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1
        TRADE_ACTION_DEAL = 1
        TRADE_ACTION_SLTP = 2
        ORDER_TIME_GTC = 0
        ORDER_FILLING_IOC = 1
        TRADE_RETCODE_DONE = 10009
        POSITION_TYPE_BUY = 0
        POSITION_TYPE_SELL = 1
    mt5 = MockMT5()  # type: ignore

logger = setup_logger("execution")


class ExecutionManager:
    """Manages order execution"""
    
    def __init__(self):
        self.config = get_config()
        self.mt5 = get_mt5_client()
        self.risk = get_risk_manager()
        self.market_status = get_market_status()
    
    def place_market_order(
        self,
        symbol: str,
        order_type: str,  # "BUY" or "SELL"
        volume: float,
        sl_price: Optional[float] = None,
        tp_price: Optional[float] = None,
        comment: str = "AI Trading Bot"
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Place a market order
        
        Args:
            symbol: Symbol name
            order_type: "BUY" or "SELL"
            volume: Volume in lots
            sl_price: Stop loss price (optional)
            tp_price: Take profit price (optional)
            comment: Order comment
        
        Returns:
            Tuple of (success, order_result_dict, error_message)
        """
        # Check if in PAPER mode
        if self.config.is_paper_mode():
            logger.info(
                f"[PAPER] Would place {order_type} order: {symbol}, "
                f"volume={volume}, sl={sl_price}, tp={tp_price}"
            )
            # Simulate order
            return True, {
                "order": 12345,
                "retcode": 10009,  # TRADE_RETCODE_DONE
                "volume": volume,
                "price": self._get_simulated_price(symbol, order_type),
                "comment": comment,
                "request_id": 0,
            }, None
        
        # LIVE mode - execute real order
        if not self.mt5.is_connected():
            return False, None, "MT5 not connected"
        
        if not MT5_AVAILABLE:
            # Demo mode - simulate order
            tick = self.mt5.get_tick(symbol)
            price = tick.get('ask', 0) if order_type.upper() == "BUY" else tick.get('bid', 0) if tick else 0
            return True, {
                "order": 12345,
                "retcode": mt5.TRADE_RETCODE_DONE,
                "volume": volume,
                "price": price,
                "comment": comment,
                "request_id": 0,
            }, None
        
        try:
            symbol_info = self.mt5.get_symbol_info(symbol)
            if not symbol_info:
                return False, None, f"Cannot get symbol info for {symbol}"
            
            # Check if market is open for trading
            if not self.market_status.is_forex_market_open(symbol):
                status_text = self.market_status.get_market_status_text(symbol)
                logger.warning(f"Cannot trade {symbol}: {status_text}")
                return False, None, f"{status_text} - Order rejected by market status"
            
            # Prepare order request
            if order_type.upper() == "BUY":
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask
            elif order_type.upper() == "SELL":
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid
            else:
                return False, None, f"Invalid order type: {order_type}"

            # Enforce broker minimum stop distances to avoid retcode 10016
            sl_price, tp_price = self._enforce_min_stop_distance(
                symbol=symbol,
                order_type=order_type,
                entry_price=price,
                sl_price=sl_price,
                tp_price=tp_price,
                symbol_info=symbol_info,
            )
            
            # Normalize volume to broker constraints before sending
            try:
                volume = self.risk.normalize_volume(symbol, volume)
            except Exception:
                pass

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type_mt5,
                "price": price,
                "deviation": 20,  # Slippage in points
                "magic": 234000,  # Magic number for bot identification
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Add SL/TP if provided
            if sl_price:
                request["sl"] = sl_price
            if tp_price:
                request["tp"] = tp_price
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                error = mt5.last_error()
                return False, None, f"Order send failed: {error}"
            
            result_dict = result._asdict()
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = f"Order rejected by MT5: retcode={result.retcode}, comment='{result.comment}'"
                if hasattr(result, 'volume'):
                    error_msg += f", requested_volume={volume}, actual_volume={result.volume}"
                logger.error(error_msg)

                # If broker says mercado cerrado, bloqueamos temporalmente el símbolo para no insistir
                if result.retcode == 10018 or "market closed" in str(result.comment).lower():
                    self.market_status.block_symbol(symbol, minutes=60)
                return False, result_dict, error_msg
            
            logger.info(
                f"Order placed successfully: {order_type} {volume} lots of {symbol} "
                f"at {result.price}, ticket={result.order}"
            )
            
            return True, result_dict, None
            
        except Exception as e:
            logger.error(f"Error placing order: {e}", exc_info=True)
            return False, None, str(e)

    def _enforce_min_stop_distance(
        self,
        symbol: str,
        order_type: str,
        entry_price: float,
        sl_price: Optional[float],
        tp_price: Optional[float],
        symbol_info: Dict
    ) -> Tuple[Optional[float], Optional[float]]:
        """Adjust SL/TP to satisfy broker stop level constraints and avoid retcode 10016."""
        try:
            point = symbol_info.get('point', 0.0001)
            min_points = symbol_info.get('trade_stops_level', symbol_info.get('stops_level', 0)) or 0
            min_dist = min_points * point
            if min_dist <= 0:
                return sl_price, tp_price

            is_buy = order_type.upper() == "BUY"

            if sl_price:
                dist = (entry_price - sl_price) if is_buy else (sl_price - entry_price)
                if dist < min_dist:
                    sl_price = entry_price - min_dist if is_buy else entry_price + min_dist
                    logger.info(f"Adjusted SL for {symbol} to respect min stop distance ({min_dist})")

            if tp_price:
                dist = (tp_price - entry_price) if is_buy else (entry_price - tp_price)
                if dist < min_dist:
                    tp_price = entry_price + min_dist if is_buy else entry_price - min_dist
                    logger.info(f"Adjusted TP for {symbol} to respect min stop distance ({min_dist})")

            return sl_price, tp_price
        except Exception as e:
            logger.warning(f"Failed enforcing stop distance for {symbol}: {e}")
            return sl_price, tp_price
    
    def close_position(self, ticket: int, volume: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """
        Close a position
        
        Args:
            ticket: Position ticket
            volume: Volume to close (None = close all)
        
        Returns:
            Tuple of (success, error_message)
        """
        if self.config.is_paper_mode() or not MT5_AVAILABLE:
            logger.info(f"[PAPER/DEMO] Would close position ticket={ticket}, volume={volume}")
            return True, None
        
        if not self.mt5.is_connected():
            return False, "MT5 not connected"
        
        try:
            # Get position
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return False, f"Position {ticket} not found"
            
            position = positions[0]
            symbol = position.symbol
            pos_type = position.type
            pos_volume = position.volume
            
            # Determine close volume
            close_volume = volume if volume else pos_volume
            if close_volume > pos_volume:
                close_volume = pos_volume
            
            # Determine close type (opposite of position type)
            if pos_type == mt5.POSITION_TYPE_BUY:
                close_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid
            else:
                close_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": close_volume,
                "type": close_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "AI Bot Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result is None:
                error = mt5.last_error()
                return False, f"Close order failed: {error}"
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return False, f"Close rejected: {result.retcode} - {result.comment}"
            
            logger.info(f"Position {ticket} closed successfully")
            return True, None
            
        except Exception as e:
            logger.error(f"Error closing position: {e}", exc_info=True)
            return False, str(e)
    
    def modify_position(
        self,
        ticket: int,
        sl_price: Optional[float] = None,
        tp_price: Optional[float] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Modify position SL/TP
        
        Args:
            ticket: Position ticket
            sl_price: New stop loss price
            tp_price: New take profit price
        
        Returns:
            Tuple of (success, error_message)
        """
        if self.config.is_paper_mode() or not MT5_AVAILABLE:
            logger.info(
                f"[PAPER/DEMO] Would modify position ticket={ticket}, "
                f"sl={sl_price}, tp={tp_price}"
            )
            return True, None
        
        if not self.mt5.is_connected():
            return False, "MT5 not connected"
        
        try:
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                return False, f"Position {ticket} not found"
            
            position = positions[0]
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
            }
            
            if sl_price:
                request["sl"] = sl_price
            if tp_price:
                request["tp"] = tp_price
            
            result = mt5.order_send(request)
            
            if result is None:
                error = mt5.last_error()
                return False, f"Modify order failed: {error}"
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return False, f"Modify rejected: {result.retcode} - {result.comment}"
            
            logger.info(f"Position {ticket} modified successfully")
            return True, None
            
        except Exception as e:
            logger.error(f"Error modifying position: {e}", exc_info=True)
            return False, str(e)
    
    def _get_simulated_price(self, symbol: str, order_type: str) -> float:
        """Get simulated price for PAPER mode"""
        tick = self.mt5.get_tick(symbol)
        if tick:
            if order_type.upper() == "BUY":
                return tick.get('ask', 0.0)
            else:
                return tick.get('bid', 0.0)
        return 0.0


# Global execution manager instance
_execution_manager: Optional[ExecutionManager] = None


def get_execution_manager() -> ExecutionManager:
    """Get global execution manager instance"""
    global _execution_manager
    if _execution_manager is None:
        _execution_manager = ExecutionManager()
    return _execution_manager
