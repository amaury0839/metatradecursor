#!/usr/bin/env python3
"""
Test script to validate TIME_LIMIT closing logic

Verifica que posiciones antiguas sean cerradas después de 60 minutos
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.trading.position_manager import get_position_manager
from app.trading.mt5_client import get_mt5_client
from app.core.logger import setup_logger

logger = setup_logger("test_time_limit")


def test_time_limit():
    """Test if TIME_LIMIT rule works correctly"""
    
    logger.info("=" * 80)
    logger.info("🧪 TEST: TIME_LIMIT Closing Rule")
    logger.info("=" * 80)
    
    # Initialize
    position_mgr = get_position_manager()
    mt5 = get_mt5_client()
    
    # Get real positions
    if not mt5.is_connected():
        if not mt5.connect():
            logger.error("❌ Cannot connect to MT5")
            return
    
    positions = mt5.get_positions()
    if not positions:
        logger.warning("⚠️  No open positions found")
        return
    
    logger.info(f"\n📊 Found {len(positions)} open positions")
    logger.info("-" * 80)
    
    for i, pos in enumerate(positions):
        symbol = pos.get('symbol', 'N/A')
        ticket = pos.get('ticket', 0)
        pos_type = pos.get('type', 0)
        profit = pos.get('profit', 0)
        time_open = pos.get('time_open', None)
        
        pos_type_str = 'BUY' if pos_type == 0 else 'SELL'
        
        logger.info(f"\n[Position {i+1}] {symbol} {pos_type_str} Ticket={ticket}")
        logger.info(f"  P&L: ${profit:.2f}")
        
        # MT5 uses 'time' not 'time_open'
        time_opened = pos.get('time', None)
        logger.info(f"  time (opened): {time_opened} (type: {type(time_opened).__name__ if time_opened else 'None'})")
        
        # Test TIME_LIMIT
        try:
            should_close, reason = position_mgr.should_close_on_time_limit(
                pos, max_hold_minutes=60
            )
            
            if should_close:
                logger.warning(f"  ⏱️  SHOULD CLOSE: {reason}")
            else:
                # Calculate hold time for info
                time_val = pos.get('time', None)
                if isinstance(time_val, (int, float)):
                    from datetime import datetime
                    open_dt = datetime.fromtimestamp(time_val)  # Use local timezone
                    hold_mins = (datetime.now() - open_dt).total_seconds() / 60
                    logger.info(f"  ✅ Holding ({hold_mins:.0f} min < 60 min limit)")
                else:
                    logger.warning(f"  ⚠️  Unexpected time format: {type(time_val)}")
                    
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ Test complete")
    logger.info("=" * 80)


if __name__ == "__main__":
    test_time_limit()
