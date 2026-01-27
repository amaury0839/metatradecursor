"""Backtest visualizer - Generate charts and reports"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List
from app.backtest.historical_engine import BacktestResults
from app.core.logger import setup_logger

logger = setup_logger("backtest_viz")


class BacktestVisualizer:
    """Generate visualizations for backtest results"""
    
    @staticmethod
    def plot_equity_curve(results: BacktestResults) -> go.Figure:
        """Plot equity curve with drawdown"""
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=('Equity Curve', 'Drawdown %')
        )
        
        # Equity curve
        fig.add_trace(
            go.Scatter(
                x=results.equity_timestamps,
                y=results.equity_curve,
                mode='lines',
                name='Equity',
                line=dict(color='#2ecc71', width=2)
            ),
            row=1, col=1
        )
        
        # Add initial balance line
        fig.add_hline(
            y=results.parameters.get('initial_balance', 10000),
            line_dash="dash",
            line_color="gray",
            row=1, col=1
        )
        
        # Drawdown
        fig.add_trace(
            go.Scatter(
                x=results.equity_timestamps,
                y=[-dd for dd in results.drawdown_curve],
                mode='lines',
                name='Drawdown',
                line=dict(color='#e74c3c', width=1),
                fill='tozeroy'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title="Equity Curve and Drawdown",
            height=600,
            hovermode='x unified',
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Equity ($)", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
        
        return fig
    
    @staticmethod
    def plot_trade_distribution(results: BacktestResults) -> go.Figure:
        """Plot profit/loss distribution of trades"""
        profits = [t.profit for t in results.trades]
        
        fig = go.Figure()
        
        # Histogram
        fig.add_trace(go.Histogram(
            x=profits,
            nbinsx=30,
            marker_color=['#2ecc71' if p > 0 else '#e74c3c' for p in profits],
            name='Trade P&L'
        ))
        
        fig.update_layout(
            title="Trade P&L Distribution",
            xaxis_title="Profit/Loss ($)",
            yaxis_title="Number of Trades",
            height=400,
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def plot_monthly_returns(results: BacktestResults) -> go.Figure:
        """Plot monthly returns heatmap"""
        if not results.trades:
            return go.Figure()
        
        # Create DataFrame from trades
        trades_df = pd.DataFrame([{
            'date': t.exit_time,
            'profit': t.profit
        } for t in results.trades if t.exit_time])
        
        trades_df['year'] = trades_df['date'].dt.year
        trades_df['month'] = trades_df['date'].dt.month
        
        # Aggregate by month
        monthly = trades_df.groupby(['year', 'month'])['profit'].sum().reset_index()
        
        # Pivot for heatmap
        pivot = monthly.pivot(index='year', columns='month', values='profit')
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=[f'M{m}' for m in pivot.columns],
            y=pivot.index,
            colorscale='RdYlGn',
            text=pivot.values,
            texttemplate='$%{text:.0f}',
            colorbar=dict(title="P&L ($)")
        ))
        
        fig.update_layout(
            title="Monthly Returns Heatmap",
            xaxis_title="Month",
            yaxis_title="Year",
            height=400
        )
        
        return fig
    
    @staticmethod
    def plot_mae_mfe(results: BacktestResults) -> go.Figure:
        """Plot MAE/MFE scatter"""
        winning_trades = [t for t in results.trades if t.profit > 0]
        losing_trades = [t for t in results.trades if t.profit <= 0]
        
        fig = go.Figure()
        
        # Winning trades
        if winning_trades:
            fig.add_trace(go.Scatter(
                x=[t.max_adverse_excursion for t in winning_trades],
                y=[t.max_favorable_excursion for t in winning_trades],
                mode='markers',
                name='Winning Trades',
                marker=dict(color='#2ecc71', size=8, opacity=0.6)
            ))
        
        # Losing trades
        if losing_trades:
            fig.add_trace(go.Scatter(
                x=[t.max_adverse_excursion for t in losing_trades],
                y=[t.max_favorable_excursion for t in losing_trades],
                mode='markers',
                name='Losing Trades',
                marker=dict(color='#e74c3c', size=8, opacity=0.6)
            ))
        
        fig.update_layout(
            title="MAE vs MFE Analysis",
            xaxis_title="Max Adverse Excursion",
            yaxis_title="Max Favorable Excursion",
            height=500,
            hovermode='closest'
        )
        
        return fig
    
    @staticmethod
    def generate_report(results: BacktestResults) -> str:
        """Generate text report of backtest results"""
        report = f"""
========================================
BACKTEST RESULTS REPORT
========================================

Period: {results.start_date.strftime('%Y-%m-%d')} to {results.end_date.strftime('%Y-%m-%d')}
Symbol: {results.parameters.get('symbol', 'N/A')}
Timeframe: {results.parameters.get('timeframe', 'N/A')}
Total Bars: {results.total_bars:,}

----------------------------------------
PERFORMANCE SUMMARY
----------------------------------------
Initial Balance:    ${results.parameters.get('initial_balance', 0):,.2f}
Final Equity:       ${results.equity_curve[-1]:,.2f}
Net Profit:         ${results.net_profit:+,.2f}
Return:             {(results.net_profit / results.parameters.get('initial_balance', 1) * 100):+.2f}%

----------------------------------------
TRADE STATISTICS
----------------------------------------
Total Trades:       {results.total_trades}
Winning Trades:     {results.winning_trades} ({results.win_rate:.1f}%)
Losing Trades:      {results.losing_trades}

Gross Profit:       ${results.total_profit:,.2f}
Gross Loss:         ${results.total_loss:,.2f}
Profit Factor:      {results.profit_factor:.2f}

Average Win:        ${results.avg_win:,.2f}
Average Loss:       ${results.avg_loss:,.2f}
Average Trade:      ${results.avg_trade:,.2f}

Largest Win:        ${results.largest_win:,.2f}
Largest Loss:       ${results.largest_loss:,.2f}

----------------------------------------
RISK METRICS
----------------------------------------
Max Drawdown:       ${results.max_drawdown:,.2f} ({results.max_drawdown_pct:.2f}%)
Sharpe Ratio:       {results.sharpe_ratio:.2f}
Sortino Ratio:      {results.sortino_ratio:.2f}

----------------------------------------
TRADE BREAKDOWN BY EXIT REASON
----------------------------------------
"""
        
        # Count by exit reason
        exit_reasons = {}
        for trade in results.trades:
            reason = trade.exit_reason
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        for reason, count in sorted(exit_reasons.items(), key=lambda x: x[1], reverse=True):
            pct = (count / results.total_trades * 100) if results.total_trades > 0 else 0
            report += f"{reason:12s}: {count:4d} ({pct:5.1f}%)\n"
        
        report += "\n========================================\n"
        
        return report


def get_visualizer() -> BacktestVisualizer:
    """Get visualizer singleton"""
    return BacktestVisualizer()
