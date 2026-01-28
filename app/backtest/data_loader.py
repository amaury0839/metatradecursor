"""Data loader for historical backtesting - Downloads data from MT5"""

import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Optional, List
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client

logger = setup_logger("backtest_data")


class HistoricalDataLoader:
    """Load historical data from MT5 for backtesting"""
    
    def __init__(self):
        self.mt5_client = get_mt5_client()
        
        # Timeframe mapping
        self.timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
        }
    
    def load_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Load historical OHLCV data from MT5
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M15, H1, etc.)
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with columns: time, open, high, low, close, tick_volume
        """
        try:
            # Connect to MT5 if not connected
            if not self.mt5_client.is_connected():
                self.mt5_client.connect()
            
            # Get timeframe constant
            tf = self.timeframe_map.get(timeframe, mt5.TIMEFRAME_M15)
            
            logger.info(f"Loading {symbol} {timeframe} data from {start_date} to {end_date}")
            
            # Request data from MT5 (using centralized method with ensure_symbol)
            rates = self.mt5_client.get_rates(symbol, tf, start_time=start_date, count=10000)
            
            if rates is None or len(rates) == 0:
                logger.error(f"No data returned for {symbol} {timeframe}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Rename columns for consistency
            df = df.rename(columns={'tick_volume': 'volume'})
            
            # Select required columns
            df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
            
            logger.info(f"Loaded {len(df)} bars for {symbol} {timeframe}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {e}")
            return None
    
    def load_multiple_symbols(
        self,
        symbols: List[str],
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> dict[str, pd.DataFrame]:
        """
        Load data for multiple symbols
        
        Returns:
            Dictionary mapping symbol -> DataFrame
        """
        data = {}
        
        for symbol in symbols:
            df = self.load_data(symbol, timeframe, start_date, end_date)
            if df is not None:
                data[symbol] = df
        
        return data
    
    def get_available_history(self, symbol: str, timeframe: str) -> Optional[tuple[datetime, datetime]]:
        """
        Get the date range of available historical data
        
        Returns:
            (earliest_date, latest_date) or None
        """
        try:
            if not self.mt5_client.is_connected():
                self.mt5_client.connect()
            
            tf = self.timeframe_map.get(timeframe, mt5.TIMEFRAME_M15)
            
            # Get last 10 bars to find latest date (using centralized method)
            latest_bars = self.mt5_client.get_rates(symbol, tf, count=10)
            if latest_bars is None or len(latest_bars) == 0:
                return None
            
            # Handle both dict and tuple formats
            latest_data = latest_bars[-1]
            if isinstance(latest_data, dict):
                latest_date = datetime.fromtimestamp(latest_data['time'])
            else:
                latest_date = datetime.fromtimestamp(latest_data[0])
            
            # Try to get data from 2 years ago to find earliest available
            test_start = datetime.now() - timedelta(days=730)
            earliest_bars = self.mt5_client.get_rates(symbol, tf, start_time=test_start, count=100)
            
            if earliest_bars is not None and len(earliest_bars) > 0:
                earliest_data = earliest_bars[0]
                if isinstance(earliest_data, dict):
                    earliest_date = datetime.fromtimestamp(earliest_data['time'])
                else:
                    earliest_date = datetime.fromtimestamp(earliest_data[0])
            else:
                # If no data that far back, try 1 year
                test_start = datetime.now() - timedelta(days=365)
                earliest_bars = self.mt5_client.get_rates(symbol, tf, start_time=test_start, count=100)
                if earliest_bars is not None and len(earliest_bars) > 0:
                    earliest_data = earliest_bars[0]
                    if isinstance(earliest_data, dict):
                        earliest_date = datetime.fromtimestamp(earliest_data['time'])
                    else:
                        earliest_date = datetime.fromtimestamp(earliest_data[0])
                else:
                    earliest_date = None
            
            return (earliest_date, latest_date) if earliest_date else None
            
        except Exception as e:
            logger.error(f"Error getting history range: {e}")
            return None
    
    def save_to_csv(self, df: pd.DataFrame, filename: str):
        """Save DataFrame to CSV file"""
        try:
            df.to_csv(filename, index=False)
            logger.info(f"Saved data to {filename}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def load_from_csv(self, filename: str) -> Optional[pd.DataFrame]:
        """Load DataFrame from CSV file"""
        try:
            df = pd.read_csv(filename)
            df['time'] = pd.to_datetime(df['time'])
            logger.info(f"Loaded data from {filename}")
            return df
        except Exception as e:
            logger.error(f"Error loading from CSV: {e}")
            return None


def get_data_loader() -> HistoricalDataLoader:
    """Get data loader singleton"""
    return HistoricalDataLoader()
