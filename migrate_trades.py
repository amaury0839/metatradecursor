"""Migrate existing trades from MT5 to database"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_database_manager
from app.trading.mt5_client import get_mt5_client
from app.core.logger import setup_logger

logger = setup_logger("migrate")


def migrate_historical_trades(days: int = 30):
    """Migrate historical trades from MT5 to database"""
    
    logger.info(f"Starting migration of last {days} days of trades...")
    
    db = get_database_manager()
    mt5 = get_mt5_client()
    
    # Connect to MT5
    if not mt5.connect():
        logger.error("Failed to connect to MT5")
        return False
    
    # Get historical deals
    from_date = datetime.now() - timedelta(days=days)
    deals = mt5.get_history_deals(from_date)
    
    if not deals:
        logger.warning("No historical deals found")
        return False
    
    logger.info(f"Found {len(deals)} historical deals")
    
    # Group deals by position ticket
    positions = {}
    
    for deal in deals:
        ticket = deal.get('position_id', deal.get('ticket'))
        if ticket not in positions:
            positions[ticket] = []
        positions[ticket].append(deal)
    
    logger.info(f"Grouped into {len(positions)} positions")
    
    # Process each position
    migrated = 0
    skipped = 0
    errors = 0
    
    for ticket, position_deals in positions.items():
        try:
            # Sort by time
            position_deals.sort(key=lambda x: x.get('time', 0))
            
            # Find entry and exit deals
            entry_deal = None
            exit_deal = None
            
            for deal in position_deals:
                entry_type = deal.get('entry', 0)
                if entry_type == 0:  # IN
                    entry_deal = deal
                elif entry_type == 1:  # OUT
                    exit_deal = deal
            
            if not entry_deal:
                skipped += 1
                continue
            
            # Build trade info
            trade_info = {
                'ticket': ticket,
                'symbol': entry_deal.get('symbol', 'UNKNOWN'),
                'type': 'BUY' if entry_deal.get('type', 0) == 0 else 'SELL',
                'volume': entry_deal.get('volume', 0.0),
                'open_price': entry_deal.get('price', 0.0),
                'open_timestamp': datetime.fromtimestamp(entry_deal.get('time', 0)).isoformat(),
                'comment': entry_deal.get('comment', '')
            }
            
            # If position is closed
            if exit_deal:
                trade_info.update({
                    'close_price': exit_deal.get('price', 0.0),
                    'close_timestamp': datetime.fromtimestamp(exit_deal.get('time', 0)).isoformat(),
                    'profit': exit_deal.get('profit', 0.0),
                    'commission': entry_deal.get('commission', 0.0) + exit_deal.get('commission', 0.0),
                    'swap': exit_deal.get('swap', 0.0),
                    'status': 'closed'
                })
            else:
                trade_info['status'] = 'open'
            
            # Save to database
            trade_id = db.save_trade(trade_info)
            
            if trade_id > 0:
                migrated += 1
                logger.debug(f"Migrated trade {ticket}")
            else:
                errors += 1
                logger.warning(f"Failed to migrate trade {ticket}")
                
        except Exception as e:
            errors += 1
            logger.error(f"Error processing position {ticket}: {e}")
    
    logger.info(f"Migration complete: {migrated} migrated, {skipped} skipped, {errors} errors")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate MT5 trades to database")
    parser.add_argument("--days", type=int, default=30, help="Number of days to migrate")
    
    args = parser.parse_args()
    
    print(f"🔄 Migrating last {args.days} days of trades...")
    
    success = migrate_historical_trades(days=args.days)
    
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
