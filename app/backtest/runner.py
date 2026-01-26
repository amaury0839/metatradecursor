"""Backtest runner for historical data"""

import pandas as pd
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.trading.strategy import TradingStrategy
from app.backtest.metrics import calculate_metrics
from app.core.logger import setup_logger
from app.ai.onnx_model import load_onnx_classifier, OnnxClassifier

logger = setup_logger("backtest")


class BacktestRunner:
    """Runs backtest on historical OHLC data"""
    
    def __init__(self, onnx_model_path: Optional[str] = None):
        self.strategy = TradingStrategy()
        self.onnx: Optional[OnnxClassifier] = load_onnx_classifier(onnx_model_path) if onnx_model_path else None

    def _onnx_signal(self, row) -> Optional[str]:
        if not self.onnx:
            return None
        try:
            features = [
                float(row.get("close", 0.0)),
                float(row.get("ema_fast", 0.0)),
                float(row.get("ema_slow", 0.0)),
                float(row.get("rsi", 0.0)),
                float(row.get("atr", 0.0)),
            ]
            signal, _scores = self.onnx.predict(features)
            return signal
        except Exception:
            return None
    
    def run_backtest(
        self,
        data_file: str,
        symbol: str,
        initial_equity: float = 10000.0
    ) -> Dict[str, Any]:
        """
        Run backtest on CSV file
        
        Args:
            data_file: Path to CSV file with OHLC data
            symbol: Symbol name
            initial_equity: Starting equity
        
        Returns:
            Dict with backtest results
        """
        # Load data
        try:
            df = pd.read_csv(data_file)
            
            # Ensure required columns
            required_cols = ["time", "open", "high", "low", "close"]
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"CSV must have columns: {required_cols}")
            
            # Convert time to datetime
            df["time"] = pd.to_datetime(df["time"])
            df.set_index("time", inplace=True)
            
            # Add volume if missing
            if "volume" not in df.columns:
                df["volume"] = 1000
            
            logger.info(f"Loaded {len(df)} candles from {data_file}")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return {"error": str(e)}
        
        # Calculate indicators (will pick swing profile by default here)
        df = self.strategy.calculate_indicators(df)
        
        # Simple backtest logic
        trades: List[Dict[str, Any]] = []
        position = None
        equity = initial_equity
        
        for i in range(50, len(df)):  # Start after enough data for indicators
            row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # Get signal (base from strategy + optional ONNX override)
            signal = "HOLD"
            if row["trend_bullish"] and prev_row["rsi"] < 50 and row["rsi"] >= 50:
                signal = "BUY"
            elif row["trend_bearish"] and prev_row["rsi"] > 50 and row["rsi"] <= 50:
                signal = "SELL"

            onnx_signal = self._onnx_signal(row)
            if onnx_signal:
                signal = onnx_signal
            
            # Simple execution logic
            if signal == "BUY" and position is None:
                # Open long position
                atr = row["atr"]
                entry_price = row["close"]
                sl_price = entry_price - (atr * 1.5)
                tp_price = entry_price + (atr * 2.5)
                volume = 0.1  # Fixed volume for simplicity
                
                position = {
                    "type": "BUY",
                    "entry_price": entry_price,
                    "sl_price": sl_price,
                    "tp_price": tp_price,
                    "volume": volume,
                    "entry_index": i,
                }
                
            elif signal == "SELL" and position is None:
                # Open short position
                atr = row["atr"]
                entry_price = row["close"]
                sl_price = entry_price + (atr * 1.5)
                tp_price = entry_price - (atr * 2.5)
                volume = 0.1
                
                position = {
                    "type": "SELL",
                    "entry_price": entry_price,
                    "sl_price": sl_price,
                    "tp_price": tp_price,
                    "volume": volume,
                    "entry_index": i,
                }
            
            # Check exit conditions
            if position:
                exit_price = None
                exit_reason = None
                
                if position["type"] == "BUY":
                    if row["low"] <= position["sl_price"]:
                        exit_price = position["sl_price"]
                        exit_reason = "SL"
                    elif row["high"] >= position["tp_price"]:
                        exit_price = position["tp_price"]
                        exit_reason = "TP"
                else:  # SELL
                    if row["high"] >= position["sl_price"]:
                        exit_price = position["sl_price"]
                        exit_reason = "SL"
                    elif row["low"] <= position["tp_price"]:
                        exit_price = position["tp_price"]
                        exit_reason = "TP"
                
                if exit_price:
                    # Calculate PnL
                    if position["type"] == "BUY":
                        pnl = (exit_price - position["entry_price"]) * position["volume"] * 100000
                    else:
                        pnl = (position["entry_price"] - exit_price) * position["volume"] * 100000
                    
                    trades.append({
                        "entry_price": position["entry_price"],
                        "exit_price": exit_price,
                        "volume": position["volume"],
                        "pnl": pnl,
                        "exit_reason": exit_reason,
                    })
                    
                    equity += pnl
                    position = None
        
        # Calculate metrics
        metrics = calculate_metrics(trades)
        metrics["initial_equity"] = initial_equity
        metrics["final_equity"] = equity
        metrics["total_return_pct"] = ((equity - initial_equity) / initial_equity) * 100
        
        logger.info(f"Backtest completed: {metrics['total_trades']} trades, "
                   f"Win rate: {metrics['win_rate']:.2f}%, "
                   f"Total PnL: {metrics['total_pnl']:.2f}")
        
        return {
            "metrics": metrics,
            "trades": trades,
        }


def main():
    """CLI entry point for backtest"""
    parser = argparse.ArgumentParser(description="Run backtest on historical data")
    parser.add_argument("--data", required=True, help="Path to CSV file")
    parser.add_argument("--symbol", default="EURUSD", help="Symbol name")
    parser.add_argument("--equity", type=float, default=10000.0, help="Initial equity")
    parser.add_argument("--onnx_model", help="Path to ONNX model for signal override", default=None)
    
    args = parser.parse_args()
    
    runner = BacktestRunner(args.onnx_model)
    results = runner.run_backtest(args.data, args.symbol, args.equity)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return
    
    metrics = results["metrics"]
    print("\n=== Backtest Results ===")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Winning Trades: {metrics['winning_trades']}")
    print(f"Losing Trades: {metrics['losing_trades']}")
    print(f"Win Rate: {metrics['win_rate']:.2f}%")
    print(f"Total PnL: {metrics['total_pnl']:.2f}")
    print(f"Average Win: {metrics['avg_win']:.2f}")
    print(f"Average Loss: {metrics['avg_loss']:.2f}")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Initial Equity: {metrics['initial_equity']:.2f}")
    print(f"Final Equity: {metrics['final_equity']:.2f}")
    print(f"Total Return: {metrics['total_return_pct']:.2f}%")


if __name__ == "__main__":
    main()
