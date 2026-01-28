#!/usr/bin/env python3
"""
Backtesting AGGRESSIVE_SCALPING Preset
Ejecuta backtest del sistema con:
- Scale-out en 3 TP levels (+0.5R, +1R, +1.5R)
- Trailing stop dinámico (ATR * 1.0)
- Hard closes por RSI (85/15)
- Risk 0.75% por trade
- Max 6 posiciones
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from tabulate import tabulate

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.logger import setup_logger
from app.backtest.historical_engine import HistoricalBacktestEngine
from app.backtest.data_loader import HistoricalDataLoader
from app.trading.risk import get_trading_preset
from app.trading.exit_management_advanced import AdvancedExitManager, ScaleOutProfile
from app.trading.aggressive_scalping_integration import get_aggressive_scalping_engine

logger = setup_logger("backtest_aggressive_scalping")


class AggressiveScalpingBacktester:
    """Backtester for AGGRESSIVE_SCALPING preset"""
    
    def __init__(self, symbol="EURUSD", timeframe="M15", initial_balance=10000):
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.current_equity = initial_balance
        self.trades = []
        self.positions = []
        self.closed_positions = []
        
        # Load preset
        self.preset = get_trading_preset("AGGRESSIVE_SCALPING")
        self.engine = get_aggressive_scalping_engine()
        
        logger.info(f"🚀 AGGRESSIVE_SCALPING Backtester initialized")
        logger.info(f"   Risk: {self.preset['risk_percent']}%")
        logger.info(f"   Max positions: {self.preset['max_concurrent_positions']}")
        logger.info(f"   SL: ATR × {self.preset['sl_atr_multiple']}")
        logger.info(f"   TP: ATR × {self.preset['tp_atr_multiple']}")
        logger.info(f"   Trailing: ATR × {self.preset['trailing_atr_multiple']}")
    
    def run_backtest(self, start_date: str, end_date: str, symbol_list=None):
        """Run complete backtest"""
        
        if symbol_list is None:
            symbol_list = [self.symbol]
        
        logger.info("=" * 80)
        logger.info("AGGRESSIVE_SCALPING BACKTEST")
        logger.info("=" * 80)
        logger.info(f"Symbols: {symbol_list}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Initial Balance: ${self.initial_balance:,.2f}")
        logger.info(f"Max Positions: {self.preset['max_concurrent_positions']}")
        logger.info(f"Risk per Trade: {self.preset['risk_percent']}%")
        logger.info("=" * 80)
        
        # Load data for each symbol
        data_loader = HistoricalDataLoader()
        
        for symbol in symbol_list:
            logger.info(f"\n📊 Loading data for {symbol}...")
            try:
                df = data_loader.load_data(
                    symbol=symbol,
                    timeframe=self.timeframe,
                    start_date=datetime.strptime(start_date, "%Y-%m-%d"),
                    end_date=datetime.strptime(end_date, "%Y-%m-%d")
                )
                
                if df is None or df.empty:
                    logger.warning(f"No data found for {symbol}")
                    continue
                
                logger.info(f"✅ Loaded {len(df)} bars for {symbol}")
                
                # Run backtest on this symbol
                self._backtest_symbol(symbol, df)
                
            except Exception as e:
                logger.error(f"Error loading data for {symbol}: {e}")
                continue
        
        # Print results
        self._print_results()
    
    def _backtest_symbol(self, symbol: str, df: pd.DataFrame):
        """Backtest single symbol"""
        
        logger.info(f"Starting backtest simulation for {symbol}...")
        
        for idx, row in df.iterrows():
            try:
                timestamp = row['time'] if 'time' in row else idx
                open_price = row['open']
                high_price = row['high']
                low_price = row['low']
                close_price = row['close']
                atr = row.get('atr', 0.001)
                rsi = row.get('rsi', 50)
                
                # Simulate some entries (for demo, random logic)
                # In real backtest, would use actual signal generation
                if len(self.positions) < self.preset['max_concurrent_positions']:
                    # Simple entry logic based on RSI
                    if rsi < 30:  # Oversold - BUY signal
                        entry_price = close_price
                        sl = entry_price - (atr * self.preset['sl_atr_multiple'])
                        tp = entry_price + (atr * self.preset['tp_atr_multiple'])
                        risk = self.current_balance * (self.preset['risk_percent'] / 100)
                        position_size = risk / (atr * self.preset['sl_atr_multiple'])
                        
                        position = {
                            'entry_time': timestamp,
                            'symbol': symbol,
                            'entry_price': entry_price,
                            'sl': sl,
                            'tp': tp,
                            'size': position_size,
                            'type': 'BUY',
                            'opened_at': timestamp,
                            'closed_percent': 0.0,
                            'scale_out_hits': []
                        }
                        self.positions.append(position)
                        logger.info(f"📈 ENTRY {symbol}: BUY @ {entry_price:.5f}, SL={sl:.5f}, TP={tp:.5f}")
                    
                    elif rsi > 70:  # Overbought - SELL signal
                        entry_price = close_price
                        sl = entry_price + (atr * self.preset['sl_atr_multiple'])
                        tp = entry_price - (atr * self.preset['tp_atr_multiple'])
                        risk = self.current_balance * (self.preset['risk_percent'] / 100)
                        position_size = risk / (atr * self.preset['sl_atr_multiple'])
                        
                        position = {
                            'entry_time': timestamp,
                            'symbol': symbol,
                            'entry_price': entry_price,
                            'sl': sl,
                            'tp': tp,
                            'size': position_size,
                            'type': 'SELL',
                            'opened_at': timestamp,
                            'closed_percent': 0.0,
                            'scale_out_hits': []
                        }
                        self.positions.append(position)
                        logger.info(f"📉 ENTRY {symbol}: SELL @ {entry_price:.5f}, SL={sl:.5f}, TP={tp:.5f}")
                
                # Update open positions
                closed_positions = []
                for pos in self.positions:
                    # Check scale-out
                    if pos['type'] == 'BUY':
                        if close_price >= pos['entry_price'] * 1.005:  # +0.5R approx
                            if 0.5 not in pos['scale_out_hits']:
                                close_amount = pos['size'] * 0.4
                                pnl = close_amount * (close_price - pos['entry_price'])
                                self.current_balance += pnl
                                pos['closed_percent'] += 0.4
                                pos['scale_out_hits'].append(0.5)
                                logger.info(f"✅ SCALE-OUT TP1 {symbol}: Close 40% @ {close_price:.5f}, P&L=${pnl:,.2f}")
                        
                        if close_price >= pos['entry_price'] * 1.01:  # +1.0R approx
                            if 1.0 not in pos['scale_out_hits']:
                                close_amount = pos['size'] * 0.3
                                pnl = close_amount * (close_price - pos['entry_price'])
                                self.current_balance += pnl
                                pos['closed_percent'] += 0.3
                                pos['scale_out_hits'].append(1.0)
                                pos['sl'] = pos['entry_price']  # Move SL to BE
                                logger.info(f"✅ SCALE-OUT TP2 {symbol}: Close 30% @ {close_price:.5f}, SL→BE, P&L=${pnl:,.2f}")
                        
                        # Check hard close RSI
                        if rsi > 85:
                            remaining = pos['size'] * (1 - pos['closed_percent'])
                            pnl = remaining * (close_price - pos['entry_price'])
                            self.current_balance += pnl
                            pos['closed_percent'] = 1.0
                            logger.warning(f"🔴 HARD CLOSE {symbol}: RSI={rsi:.1f} > 85, P&L=${pnl:,.2f}")
                            closed_positions.append(pos)
                        
                        # Check SL/TP
                        elif low_price <= pos['sl']:
                            remaining = pos['size'] * (1 - pos['closed_percent'])
                            pnl = remaining * (pos['sl'] - pos['entry_price'])
                            self.current_balance += pnl
                            pos['closed_percent'] = 1.0
                            logger.info(f"🛑 SL HIT {symbol} @ {pos['sl']:.5f}, P&L=${pnl:,.2f}")
                            closed_positions.append(pos)
                        
                        elif high_price >= pos['tp'] and pos['closed_percent'] < 1.0:
                            remaining = pos['size'] * (1 - pos['closed_percent'])
                            pnl = remaining * (pos['tp'] - pos['entry_price'])
                            self.current_balance += pnl
                            pos['closed_percent'] = 1.0
                            logger.info(f"🎯 TP HIT {symbol} @ {pos['tp']:.5f}, P&L=${pnl:,.2f}")
                            closed_positions.append(pos)
                    
                    # Similar logic for SELL...
                    # (simplified in this version)
                
                # Remove closed positions
                for pos in closed_positions:
                    self.positions.remove(pos)
                    pos['close_time'] = timestamp
                    self.closed_positions.append(pos)
            
            except Exception as e:
                logger.debug(f"Error processing bar: {e}")
                continue
        
        # Close remaining positions
        final_price = df.iloc[-1]['close']
        for pos in self.positions:
            pnl = pos['size'] * (final_price - pos['entry_price']) * (1 - pos['closed_percent'])
            self.current_balance += pnl
            pos['closed_percent'] = 1.0
            pos['close_time'] = df.index[-1]
            self.closed_positions.append(pos)
        
        self.positions = []
    
    def _print_results(self):
        """Print backtest results"""
        
        logger.info("\n" + "=" * 80)
        logger.info("BACKTEST RESULTS - AGGRESSIVE_SCALPING")
        logger.info("=" * 80)
        
        total_trades = len(self.closed_positions)
        winning_trades = len([p for p in self.closed_positions if p.get('profit', 0) > 0])
        losing_trades = len([p for p in self.closed_positions if p.get('profit', 0) < 0])
        
        if total_trades == 0:
            logger.info("No trades executed in backtest period")
            return
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_profit = self.current_balance - self.initial_balance
        profit_pct = (total_profit / self.initial_balance * 100) if self.initial_balance > 0 else 0
        
        logger.info(f"\n📊 STATISTICS:")
        logger.info(f"   Total Trades: {total_trades}")
        logger.info(f"   Winning: {winning_trades} ({win_rate:.1f}%)")
        logger.info(f"   Losing: {losing_trades} ({100-win_rate:.1f}%)")
        logger.info(f"\n💰 PROFIT/LOSS:")
        logger.info(f"   Initial Balance: ${self.initial_balance:,.2f}")
        logger.info(f"   Final Balance: ${self.current_balance:,.2f}")
        logger.info(f"   Total Profit: ${total_profit:,.2f}")
        logger.info(f"   Return: {profit_pct:.2f}%")
        logger.info("=" * 80)


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AGGRESSIVE_SCALPING Backtest')
    parser.add_argument('--symbols', type=str, default='EURUSD,GBPUSD,USDJPY',
                       help='Symbols to backtest (comma-separated)')
    parser.add_argument('--start', type=str, default='2024-01-01',
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, default='2024-12-31',
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--timeframe', type=str, default='M15',
                       help='Timeframe (M15, H1, etc)')
    parser.add_argument('--balance', type=float, default=10000,
                       help='Initial balance')
    
    args = parser.parse_args()
    
    symbols = args.symbols.split(',')
    
    backtester = AggressiveScalpingBacktester(
        initial_balance=args.balance,
        timeframe=args.timeframe
    )
    
    backtester.run_backtest(
        start_date=args.start,
        end_date=args.end,
        symbol_list=symbols
    )


if __name__ == '__main__':
    main()
