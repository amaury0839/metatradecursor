"""Order execution and management"""

from typing import Optional, Dict, Tuple
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import get_config
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client
from app.trading.risk import get_risk_manager
from app.trading.market_status import get_market_status
from app.trading.data import get_data_provider

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


# ✅ HELPER FUNCTIONS (pragmatic validation)

def sym_info(symbol: str):
    """Get symbol_info as object plus dict for safe access"""
    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError(f"Symbol info not found: {symbol}")
    return info, info._asdict()


def get_bid_ask(symbol: str) -> Tuple[float, float]:
    """Get live BID/ASK for symbol"""
    t = mt5.symbol_info_tick(symbol)
    if t is None:
        return None, None
    return t.bid, t.ask


def min_stop_distance(symbol: str) -> float:
    """Calculate minimum stop distance = max(stops_level, freeze_level) * 1.2 buffer"""
    try:
        _, d = sym_info(symbol)
    except RuntimeError:
        return 0.0001
    
    point = d.get("point", 0.0001)
    stops = (d.get("trade_stops_level", 0) or 0) * point
    freeze = (d.get("trade_freeze_level", 0) or 0) * point
    
    # Buffer defensivo (spread + latencia)
    return max(stops, freeze) * 1.2


def validate_stops_live(symbol: str, side: str, sl: float, tp: float) -> Tuple[bool, Optional[str]]:
    """
    Valida SL/TP CONTRA BID/ASK en vivo
    
    Args:
        symbol: Symbol name
        side: "BUY" o "SELL"
        sl: Stop loss price
        tp: Take profit price
    
    Returns:
        Tuple (valid, error_message)
    """
    bid, ask = get_bid_ask(symbol)
    if bid is None or ask is None:
        return False, "Cannot get BID/ASK"
    
    m = min_stop_distance(symbol)
    
    if side == "BUY":
        # BUY: SL debe estar debajo de BID, TP arriba de ASK
        if sl >= bid - m:
            return False, f"SL too close to BID ({sl:.5f} >= {bid-m:.5f})"
        if tp <= ask + m:
            return False, f"TP too close to ASK ({tp:.5f} <= {ask+m:.5f})"
    else:
        # SELL: SL debe estar arriba de ASK, TP debajo de BID
        if sl <= ask + m:
            return False, f"SL too close to ASK ({sl:.5f} <= {ask+m:.5f})"
        if tp >= bid - m:
            return False, f"TP too close to BID ({tp:.5f} >= {bid-m:.5f})"
    
    return True, None


def norm(symbol: str, price: float) -> float:
    """Normalizar precio a DIGITS exactos del símbolo"""
    try:
        _, d = sym_info(symbol)
    except RuntimeError:
        return price
    digits = d.get("digits", 5)
    return round(price, digits)


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
            return True, {
                "order": 12345,
                "retcode": mt5.TRADE_RETCODE_DONE,
                "volume": volume,
                "price": self._get_simulated_price(symbol, order_type),
                "comment": comment,
                "request_id": 0,
            }, None
        
        if not self.mt5.is_connected():
            return False, None, "MT5 not connected"
        
        if not MT5_AVAILABLE:
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
            
            if not self.market_status.is_forex_market_open(symbol):
                status_text = self.market_status.get_market_status_text(symbol)
                logger.warning(f"Cannot trade {symbol}: {status_text}")
                return False, None, f"{status_text} - Order rejected"
            
            # ✅ 1️⃣ Obtener BID/ASK en vivo
            bid, ask = get_bid_ask(symbol)
            if bid is None:
                return False, None, f"Cannot get BID/ASK for {symbol}"
            
            if order_type.upper() == "BUY":
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                price = ask
            elif order_type.upper() == "SELL":
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                price = bid
            else:
                return False, None, f"Invalid order type: {order_type}"
            
            # ✅ 2️⃣ Normalizar TODO a DIGITS
            price = norm(symbol, price)
            if sl_price:
                sl_price = norm(symbol, sl_price)
            if tp_price:
                tp_price = norm(symbol, tp_price)
            
            # ✅ 1️⃣ Validar SL/TP CONTRA BID/ASK en vivo
            if sl_price and tp_price:
                valid, error = validate_stops_live(symbol, order_type.upper(), sl_price, tp_price)
                if not valid:
                    logger.warning(f"⚠️ {symbol}: {error}")
                    return False, None, f"Stop validation failed: {error}"
            
            # Normalize volume
            try:
                volume = self.risk.normalize_volume(symbol, volume)
            except Exception:
                pass
            
            # ✅ 3️⃣ Preparar request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type_mt5,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            if sl_price:
                request["sl"] = sl_price
            if tp_price:
                request["tp"] = tp_price
            
            # ✅ 3️⃣ order_check() + LOGGING OBLIGATORIO
            logger.info(f"\n🔍 order_check() {symbol}:")
            logger.info(f"  Type: {order_type.upper()}, Volume: {volume}")
            logger.info(f"  Price: {price}, SL: {sl_price}, TP: {tp_price}")
            logger.info(f"  REQUEST: {request}")
            
            check = mt5.order_check(request)
            
            logger.info(f"🔍 order_check() RESPONSE:")
            if check:
                logger.info(f"  Retcode: {check.retcode}, Comment: {check.comment}")
                logger.info(f"  Balance: {check.balance}, Profit: {check.profit}")
            else:
                logger.error(f"  ❌ order_check() returned None")
            
            # Si order_check falla → error claro
            if check is None or check.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = check.comment if check else "order_check returned None"
                logger.error(f"❌ Order validation failed: {error_msg}")
                return False, None, f"Order check failed: {error_msg}"
            
            # ✅ order_check OK → enviar
            logger.info(f"✅ order_check passed. Sending order...")
            result = mt5.order_send(request)
            
            if result is None:
                error = mt5.last_error()
                logger.error(f"❌ order_send() failed: {error}")
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
            # accept dict or SymbolInfo
            if not isinstance(symbol_info, dict):
                try:
                    symbol_info = symbol_info._asdict()
                except Exception:
                    symbol_info = {}
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
            
            # Update trade record in database with profit
            try:
                from app.core.database import get_database
                db = get_database()
                
                # Get the closed position from history with profit
                from datetime import datetime, timedelta
                now = datetime.now()
                # Look back 7 days to find the closing deal
                seven_days_ago = now - timedelta(days=7)
                
                deals = mt5.history_deals_get(seven_days_ago, now)
                if deals:
                    # Find the closing deal for this position (most recent exit)
                    matching_deals = [d for d in deals if d.position_id == ticket and d.entry == 1]
                    if matching_deals:
                        # Get the most recent closing deal
                        deal = matching_deals[-1]
                        trade_info = {
                            'close_price': deal.price,
                            'close_timestamp': datetime.fromtimestamp(deal.time).isoformat(),
                            'profit': deal.profit,
                            'commission': deal.commission,
                            'swap': deal.swap,
                            'status': 'closed'
                        }
                        db.update_trade(ticket, trade_info)
                        logger.info(f"✅ Trade {ticket} updated: profit=${deal.profit:.2f}, commission=${deal.commission:.2f}")
            except Exception as e:
                logger.warning(f"Could not update trade profit from MT5: {e}. Trade closed but profit not logged.")
                # This is not critical - trade is still closed
            
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
