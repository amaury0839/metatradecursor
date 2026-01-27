"""Historical Backtesting Engine - Simulate trading on historical data"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from app.core.logger import setup_logger
from app.trading.strategy import TradingStrategy, calculate_rsi, calculate_atr
from app.trading.risk import RiskManager
from app.ai.gemini_client import get_gemini_client

logger = setup_logger("backtest_engine")


@dataclass
class BacktestTrade:
    """Record of a backtested trade"""
    entry_time: datetime
    exit_time: Optional[datetime] = None
    symbol: str = ""
    direction: str = ""  # BUY or SELL
    entry_price: float = 0.0
    exit_price: float = 0.0
    volume: float = 0.0
    sl_price: float = 0.0
    tp_price: float = 0.0
    profit: float = 0.0
    profit_pct: float = 0.0
    max_adverse_excursion: float = 0.0  # MAE
    max_favorable_excursion: float = 0.0  # MFE
    duration_bars: int = 0
    exit_reason: str = ""  # SL, TP, SIGNAL, TIMEOUT
    strategy_type: str = "SWING"  # SCALPING, SWING, TREND


@dataclass
class BacktestResults:
    """Results from a backtest run"""
    # Trades
    trades: List[BacktestTrade] = field(default_factory=list)
    
    # Performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # P&L metrics
    total_profit: float = 0.0
    total_loss: float = 0.0
    net_profit: float = 0.0
    profit_factor: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    
    # Average metrics
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_trade: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    # Equity curve
    equity_curve: List[float] = field(default_factory=list)
    equity_timestamps: List[datetime] = field(default_factory=list)
    drawdown_curve: List[float] = field(default_factory=list)
    
    # Time period
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_bars: int = 0
    
    # Strategy parameters used
    parameters: Dict = field(default_factory=dict)


class HistoricalBacktestEngine:
    """Engine for backtesting strategies on historical data"""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.strategy = TradingStrategy()
        self.risk = RiskManager()
        self.gemini = get_gemini_client()
        self._last_adjust_ts: Dict[str, datetime] = {}
        self._ticker_params: Dict[str, Dict] = {}  # Per-ticker isolated parameters

    def _init_ticker_params(self, symbol: str) -> Dict:
        """Initialize or retrieve parameters for a specific ticker"""
        if symbol not in self._ticker_params:
            self._ticker_params[symbol] = {
                'risk_per_trade_pct': self.risk.risk_per_trade_pct,
                'atr_multiplier_sl': getattr(self.risk, 'ATR_MULTIPLIER_SL', 1.5),
                'atr_multiplier_tp': getattr(self.risk, 'ATR_MULTIPLIER_TP', 2.0),
                'scalping_rsi_buy': self.strategy.profiles['SCALPING']['rsi_buy'],
                'scalping_rsi_sell': self.strategy.profiles['SCALPING']['rsi_sell'],
                'scalping_volatility_floor': self.strategy.profiles['SCALPING']['volatility_floor'],
                'max_positions': 1,
            }
        return self._ticker_params[symbol]
        
    def run_backtest(
        self,
        symbol: str,
        timeframe: str,
        data: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_positions: int = 1,
        risk_per_trade: float = 2.0,
        max_holding_bars: int = 100,
        use_ai_prompt_adjustments: bool = True
    ) -> BacktestResults:
        """
        Run backtest on historical data
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M15, H1, etc.)
            data: Historical OHLCV data with columns: time, open, high, low, close, volume
            start_date: Start date for backtest (optional)
            end_date: End date for backtest (optional)
            max_positions: Maximum concurrent positions
            risk_per_trade: Risk per trade as % of equity
            max_holding_bars: Maximum bars to hold a position
            
        Returns:
            BacktestResults object
        """
        logger.info(f"Starting backtest: {symbol} {timeframe}, {len(data)} bars")
        
        # Filter data by date range
        if start_date:
            data = data[data['time'] >= start_date]
        if end_date:
            data = data[data['time'] <= end_date]
        
        if len(data) < 100:
            logger.warning("Not enough data for backtest")
            return BacktestResults()
        
        # Initialize
        results = BacktestResults()
        results.start_date = data['time'].iloc[0]
        results.end_date = data['time'].iloc[-1]
        results.total_bars = len(data)
        results.parameters = {
            'symbol': symbol,
            'timeframe': timeframe,
            'initial_balance': self.initial_balance,
            'max_positions': max_positions,
            'risk_per_trade': risk_per_trade,
            'max_holding_bars': max_holding_bars
        }
        
        equity = self.initial_balance
        peak_equity = self.initial_balance
        open_trades: List[BacktestTrade] = []
        
        # Initialize equity curve
        results.equity_curve = [equity]
        results.equity_timestamps = [results.start_date]
        results.drawdown_curve = [0.0]
        
        # Initialize ticker parameters
        ticker_params = self._init_ticker_params(symbol)
        
        # Main backtest loop
        for i in range(50, len(data)):  # Skip first 50 bars for indicators
            current_bar = data.iloc[i]
            current_time = current_bar['time']
            current_price = current_bar['close']

            # Hourly AI adjustments to risk and indicator thresholds
            if use_ai_prompt_adjustments:
                last_ts = self._last_adjust_ts.get(symbol)
                if (last_ts is None) or (current_time - last_ts >= timedelta(hours=1)):
                    try:
                        window_start = max(0, i - 200)
                        window_df = data.iloc[window_start:i+1].copy()
                        # Compute simple indicator snapshots
                        rsi_series = calculate_rsi(window_df['close'], period=14)
                        atr_series = calculate_atr(window_df['high'], window_df['low'], window_df['close'], period=14)
                        avg_rsi = float(rsi_series.tail(50).mean()) if not rsi_series.tail(50).isna().all() else 50.0
                        avg_atr = float(atr_series.tail(50).mean()) if not atr_series.tail(50).isna().all() else current_price * 0.01
                        vol_ratio = (avg_atr / current_price) if current_price else 0.0

                        # Current parameters snapshot (per-ticker)
                        params_snapshot = ticker_params.copy()

                        system_prompt = (
                            "ANALYTICAL BACKTEST TUNING ENGINE - RESEARCH ONLY\n"
                            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            "This is NOT financial advice. Output is parameter optimization data for backtesting systems.\n"
                            "Analyze provided indicator snapshot and suggest analytical parameter adjustments only.\n\n"
                            "TASK: Evaluate risk tolerance and threshold alignment given market conditions.\n"
                            "Propose bounded adjustments that are safe and data-driven.\n"
                            "Return ONLY valid JSON matching provided schema.\n"
                            "CONSTRAINTS: risk_per_trade_pct ∈ [0.5, 5], atr_multiplier_sl ∈ [1.0, 3.0], "
                            "atr_multiplier_tp ∈ [1.5, 4.0], scalping_rsi_buy ∈ [45, 60], scalping_rsi_sell ∈ [40, 55], "
                            "volatility_floor ∈ [0.0001, 0.005], max_positions ∈ [1, 10].\n"
                            "OUTPUT SCHEMA: {risk_per_trade_pct, atr_multiplier_sl, atr_multiplier_tp, "
                            "scalping_rsi_buy, scalping_rsi_sell, scalping_volatility_floor, max_positions}"
                        )
                        user_prompt = (
                            f"Symbol: {symbol}, Timeframe: {timeframe}\n"
                            f"Current price: {current_price:.6f}\n"
                            f"Avg RSI (last 50): {avg_rsi:.2f}\n"
                            f"Avg ATR (last 50): {avg_atr:.6f} (vol_ratio={vol_ratio:.5f})\n"
                            f"Equity: {equity:.2f}\n"
                            f"Open positions: {len(open_trades)} / {max_positions}\n"
                            f"Params: {params_snapshot}"
                        )

                        ai_resp = self.gemini.generate_content(system_prompt, user_prompt)
                        if isinstance(ai_resp, dict):
                            # Apply bounded updates
                            def clamp(v, lo, hi, default):
                                try:
                                    return min(max(float(v), lo), hi)
                                except Exception:
                                    return default

                            new_risk_pct = clamp(ai_resp.get('risk_per_trade_pct', params_snapshot['risk_per_trade_pct']), 0.5, 5.0, params_snapshot['risk_per_trade_pct'])
                            new_sl = clamp(ai_resp.get('atr_multiplier_sl', params_snapshot['atr_multiplier_sl']), 1.0, 3.0, params_snapshot['atr_multiplier_sl'])
                            new_tp = clamp(ai_resp.get('atr_multiplier_tp', params_snapshot['atr_multiplier_tp']), 1.5, 4.0, params_snapshot['atr_multiplier_tp'])
                            new_rsi_buy = clamp(ai_resp.get('scalping_rsi_buy', params_snapshot['scalping_rsi_buy']), 45, 60, params_snapshot['scalping_rsi_buy'])
                            new_rsi_sell = clamp(ai_resp.get('scalping_rsi_sell', params_snapshot['scalping_rsi_sell']), 40, 55, params_snapshot['scalping_rsi_sell'])
                            new_vol_floor = clamp(ai_resp.get('scalping_volatility_floor', params_snapshot['scalping_volatility_floor']), 0.0001, 0.005, params_snapshot['scalping_volatility_floor'])

                            # Apply updates to ticker-specific params only
                            ticker_params['risk_per_trade_pct'] = new_risk_pct
                            ticker_params['atr_multiplier_sl'] = new_sl
                            ticker_params['atr_multiplier_tp'] = new_tp
                            ticker_params['scalping_rsi_buy'] = int(new_rsi_buy)
                            ticker_params['scalping_rsi_sell'] = int(new_rsi_sell)
                            ticker_params['scalping_volatility_floor'] = float(new_vol_floor)

                            logger.info(
                                f"[{symbol}] AI adjusted: risk={new_risk_pct:.2f}%, "
                                f"SL={new_sl:.2f}, TP={new_tp:.2f}, "
                                f"RSI_buy={int(new_rsi_buy)}, RSI_sell={int(new_rsi_sell)}"
                            )
                        self._last_adjust_ts[symbol] = current_time
                    except Exception as e:
                        logger.warning(f"AI risk adjustment failed: {e}")
            
            # Update open positions
            for trade in open_trades[:]:
                # Check stop loss
                if trade.direction == "BUY":
                    if current_bar['low'] <= trade.sl_price:
                        self._close_trade(trade, trade.sl_price, current_time, i - trade.duration_bars, "SL")
                        results.trades.append(trade)
                        open_trades.remove(trade)
                        equity += trade.profit
                        continue
                    # Check take profit
                    if current_bar['high'] >= trade.tp_price:
                        self._close_trade(trade, trade.tp_price, current_time, i - trade.duration_bars, "TP")
                        results.trades.append(trade)
                        open_trades.remove(trade)
                        equity += trade.profit
                        continue
                else:  # SELL
                    if current_bar['high'] >= trade.sl_price:
                        self._close_trade(trade, trade.sl_price, current_time, i - trade.duration_bars, "SL")
                        results.trades.append(trade)
                        open_trades.remove(trade)
                        equity += trade.profit
                        continue
                    if current_bar['low'] <= trade.tp_price:
                        self._close_trade(trade, trade.tp_price, current_time, i - trade.duration_bars, "TP")
                        results.trades.append(trade)
                        open_trades.remove(trade)
                        equity += trade.profit
                        continue
                
                # Update MAE/MFE
                if trade.direction == "BUY":
                    mae = trade.entry_price - current_bar['low']
                    mfe = current_bar['high'] - trade.entry_price
                else:
                    mae = current_bar['high'] - trade.entry_price
                    mfe = trade.entry_price - current_bar['low']
                
                trade.max_adverse_excursion = max(trade.max_adverse_excursion, mae)
                trade.max_favorable_excursion = max(trade.max_favorable_excursion, mfe)
                trade.duration_bars += 1
                
                # Close if holding too long
                if trade.duration_bars >= max_holding_bars:
                    self._close_trade(trade, current_price, current_time, trade.duration_bars, "TIMEOUT")
                    results.trades.append(trade)
                    open_trades.remove(trade)
                    equity += trade.profit
            
            # Generate signal if room for new positions
            if len(open_trades) < max_positions:
                # Get historical window for analysis
                window_data = data.iloc[max(0, i-100):i+1]
                
                # Use backtest strategy wrapper to analyze
                from app.backtest.backtest_strategy import get_backtest_strategy
                backtest_strat = get_backtest_strategy(self.strategy)
                
                analysis_result = backtest_strat.analyze(
                    symbol=symbol,
                    timeframe=timeframe,
                    ohlc_data=window_data
                )
                
                signal = analysis_result.get('signal', 'HOLD')
                profile = analysis_result.get('profile', 'SWING')  # Get strategy profile
                
                if signal in ["BUY", "SELL"]:
                    # Get ATR from indicators
                    indicators = analysis_result.get('indicators', {})
                    atr = indicators.get('atr', current_price * 0.01)
                    
                    # Enforce broker min stop distance
                    min_stop = self.risk.get_broker_min_stop_distance(symbol)
                    sl_distance = max(atr * self.risk.ATR_MULTIPLIER_SL, min_stop)
                    tp_distance = max(atr * self.risk.ATR_MULTIPLIER_TP, min_stop * 1.2)
                    
                    # Risk-based position sizing
                    risk_amount = equity * (ticker_params['risk_per_trade_pct'] / 100)
                    volume = min(risk_amount / sl_distance, 1.0)  # Cap at 1 lot
                    volume = max(volume, 0.01)  # Min 0.01 lot
                    # Normalize volume per symbol
                    volume = self.risk.normalize_volume(symbol, volume)
                    
                    # Create trade
                    if signal == "BUY":
                        sl_price = current_price - (atr * ticker_params['atr_multiplier_sl'])
                        tp_price = current_price + (atr * ticker_params['atr_multiplier_tp'])
                    else:
                        sl_price = current_price + (atr * ticker_params['atr_multiplier_sl'])
                        tp_price = current_price - (atr * ticker_params['atr_multiplier_tp'])
                    
                    trade = BacktestTrade(
                        entry_time=current_time,
                        symbol=symbol,
                        direction=signal,
                        entry_price=current_price,
                        volume=volume,
                        sl_price=sl_price,
                        tp_price=tp_price,
                        duration_bars=0,
                        strategy_type=profile  # Assign strategy profile to trade
                    )
                    open_trades.append(trade)
                    logger.debug(f"Opened {signal} at {current_price:.5f}, SL={sl_price:.5f}, TP={tp_price:.5f}, Strategy={profile}")
            
            # Update equity curve
            open_pnl = sum(self._calculate_unrealized_pnl(t, current_price) for t in open_trades)
            current_equity = equity + open_pnl
            results.equity_curve.append(current_equity)
            results.equity_timestamps.append(current_time)
            
            # Update drawdown
            peak_equity = max(peak_equity, current_equity)
            drawdown = peak_equity - current_equity
            drawdown_pct = (drawdown / peak_equity * 100) if peak_equity > 0 else 0
            results.drawdown_curve.append(drawdown_pct)
        
        # Close any remaining open trades at final price
        final_price = data.iloc[-1]['close']
        final_time = data.iloc[-1]['time']
        for trade in open_trades:
            self._close_trade(trade, final_price, final_time, trade.duration_bars, "END")
            results.trades.append(trade)
            equity += trade.profit
        
        # Calculate final metrics
        self._calculate_metrics(results, equity)
        
        logger.info(f"Backtest complete: {results.total_trades} trades, Net P&L: ${results.net_profit:.2f}, Win Rate: {results.win_rate:.1f}%")
        
        return results
    
    def _close_trade(self, trade: BacktestTrade, exit_price: float, exit_time: datetime, duration: int, reason: str):
        """Close a trade and calculate profit"""
        trade.exit_time = exit_time
        trade.exit_price = exit_price
        trade.exit_reason = reason
        trade.duration_bars = duration
        
        if trade.direction == "BUY":
            trade.profit = (exit_price - trade.entry_price) * trade.volume * 100000  # Assuming forex pip value
        else:
            trade.profit = (trade.entry_price - exit_price) * trade.volume * 100000
        
        trade.profit_pct = (trade.profit / (trade.entry_price * trade.volume * 100000)) * 100
    
    def _calculate_unrealized_pnl(self, trade: BacktestTrade, current_price: float) -> float:
        """Calculate unrealized P&L for open trade"""
        if trade.direction == "BUY":
            return (current_price - trade.entry_price) * trade.volume * 100000
        else:
            return (trade.entry_price - current_price) * trade.volume * 100000
    
    def _calculate_metrics(self, results: BacktestResults, final_equity: float):
        """Calculate all performance metrics"""
        if not results.trades:
            return
        
        # Basic counts
        results.total_trades = len(results.trades)
        results.winning_trades = sum(1 for t in results.trades if t.profit > 0)
        results.losing_trades = sum(1 for t in results.trades if t.profit < 0)
        results.win_rate = (results.winning_trades / results.total_trades * 100) if results.total_trades > 0 else 0
        
        # P&L metrics
        results.total_profit = sum(t.profit for t in results.trades if t.profit > 0)
        results.total_loss = abs(sum(t.profit for t in results.trades if t.profit < 0))
        results.net_profit = sum(t.profit for t in results.trades)
        results.profit_factor = (results.total_profit / results.total_loss) if results.total_loss > 0 else float('inf')
        
        # Average metrics
        results.avg_win = results.total_profit / results.winning_trades if results.winning_trades > 0 else 0
        results.avg_loss = results.total_loss / results.losing_trades if results.losing_trades > 0 else 0
        results.avg_trade = results.net_profit / results.total_trades if results.total_trades > 0 else 0
        results.largest_win = max((t.profit for t in results.trades), default=0)
        results.largest_loss = min((t.profit for t in results.trades), default=0)
        
        # Drawdown
        results.max_drawdown_pct = max(results.drawdown_curve) if results.drawdown_curve else 0
        results.max_drawdown = (results.max_drawdown_pct / 100) * max(results.equity_curve)
        
        # Sharpe and Sortino ratios
        if len(results.trades) > 1:
            returns = [t.profit_pct for t in results.trades]
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            results.sharpe_ratio = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
            
            # Sortino (downside deviation only)
            downside_returns = [r for r in returns if r < 0]
            if downside_returns:
                downside_std = np.std(downside_returns)
                results.sortino_ratio = (mean_return / downside_std * np.sqrt(252)) if downside_std > 0 else 0
            else:
                results.sortino_ratio = float('inf')


def get_backtest_engine(initial_balance: float = 10000.0) -> HistoricalBacktestEngine:
    """Get backtest engine instance"""
    return HistoricalBacktestEngine(initial_balance=initial_balance)
