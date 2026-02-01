"""
Modern Streamlit dashboard for the trading bot.
Focused on a cleaner UI, de-duplicated logic, and a statement view.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any
import sqlite3

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.core.config import get_config
from app.core.database import get_database_manager
from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client
from app.ui.ui_components import section_header, stat_card, metric_grid, empty_state

logger = setup_logger("ui_modern")


def apply_ui_theme() -> None:
    """Inject a modern, intentional visual style."""
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=DM+Sans:wght@400;500;700&display=swap');

:root {
    --ink: #121316;
    --subtle: #6a6f78;
    --accent: #2fbf8f;
    --accent-2: #f7b267;
    --panel: #ffffff;
    --panel-2: #f7f5ef;
    --border: #e7e2d8;
    --shadow: rgba(20, 20, 20, 0.08);
}

html, body, [class*="st-"] {
    font-family: "DM Sans", system-ui, -apple-system, sans-serif;
    color: var(--ink);
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1200px 600px at 10% -10%, #f8efe2 0%, transparent 60%),
        radial-gradient(900px 500px at 90% 10%, #eaf7f1 0%, transparent 55%),
        linear-gradient(180deg, #f7f5ef 0%, #f2f1ec 100%);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8f6f1 100%);
    border-right: 1px solid var(--border);
}

h1, h2, h3, h4, h5, h6 {
    font-family: "Space Grotesk", system-ui, -apple-system, sans-serif;
    letter-spacing: -0.02em;
}

.hero {
    background: linear-gradient(135deg, #1f2933 0%, #0b0d0f 100%);
    color: #ffffff;
    border-radius: 18px;
    padding: 28px 32px;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.25);
    position: relative;
    overflow: hidden;
}

.hero:after {
    content: "";
    position: absolute;
    top: -60px;
    right: -60px;
    width: 220px;
    height: 220px;
    background: radial-gradient(circle, rgba(47,191,143,0.35), transparent 65%);
}

.hero-title {
    font-size: 2.2rem;
    margin: 0;
}

.hero-subtitle {
    color: #c8d0da;
    margin-top: 6px;
    font-size: 0.95rem;
}

.chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,0.12);
    color: #ffffff;
    font-size: 0.85rem;
    margin-right: 6px;
}

.stat-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 10px 20px var(--shadow);
    animation: fadeUp 0.7s ease both;
}

.stat-value {
    font-size: 1.5rem;
    font-weight: 700;
}

.stat-label {
    color: var(--subtle);
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.soft-panel {
    background: var(--panel-2);
    border: 1px dashed var(--border);
    border-radius: 12px;
    padding: 16px;
}

.section-title {
    font-size: 1.1rem;
    margin-bottom: 6px;
}

.table-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 8px;
    box-shadow: 0 10px 20px var(--shadow);
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _get_db():
    if "db" not in st.session_state:
        st.session_state.db = get_database_manager()
    return st.session_state.db


def _get_config():
    if "config" not in st.session_state:
        st.session_state.config = get_config()
    return st.session_state.config


def get_mt5_status() -> Dict[str, Any]:
    """Check MT5 connection status from shared state."""
    try:
        from app.core.shared_state import get_shared_state_manager
        shared_state = get_shared_state_manager()
        state_data = shared_state.get_state()
        
        if state_data and 'mt5' in state_data:
            mt5_data = state_data['mt5']
            return {
                "connected": mt5_data.get('connected', False),
                "account": mt5_data.get('account', 0),
                "balance": mt5_data.get('balance', 0.0),
                "equity": mt5_data.get('equity', 0.0),
                "margin_free": mt5_data.get('margin_free', 0.0),
                "margin_level": mt5_data.get('margin_level', 0.0),
                "last_update": state_data.get('last_update', ''),
            }
    except Exception as exc:
        logger.error("Failed to read shared state: %s", exc)

    return {"connected": False}


def get_trading_stats(days: int = 30) -> Dict[str, Any]:
    """Get trading statistics from the history database."""
    try:
        db = _get_db()
        return db.get_performance_summary(days=days)
    except Exception as exc:
        logger.error("Failed to get trading stats: %s", exc)
        return {}


def render_header() -> None:
    """Render the hero header with status chips."""
    mt5_status = get_mt5_status()
    status_text = "Connected" if mt5_status.get("connected") else "Offline"
    account_text = (
        f"Account {mt5_status.get('account')}"
        if mt5_status.get("connected")
        else "No account"
    )

    st.markdown(
        f"""
<div class="hero">
  <div class="hero-title">MetaTrade Control Room</div>
  <div class="hero-subtitle">AI trading operations, risk, and performance in one view.</div>
  <div style="margin-top: 16px;">
    <span class="chip">MT5: {status_text}</span>
    <span class="chip">{account_text}</span>
    <span class="chip">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    """Sidebar with quick status and controls."""
    with st.sidebar:
        st.markdown("## Control Panel")
        st.caption("Realtime status and quick controls")
        mt5_status = get_mt5_status()
        status = "Connected" if mt5_status.get("connected") else "Offline"
        st.write(f"MT5: {status}")
        if mt5_status.get("connected"):
            st.write(f"Account: {mt5_status.get('account')}")
        st.divider()
        st.slider("Refresh rate (seconds)", 1, 30, 5, 1)
        st.button("Start bot")
        st.button("Stop bot")


def render_quick_stats() -> None:
    """Render quick statistics cards."""
    mt5_status = get_mt5_status()

    col1, col2, col3, col4 = st.columns(4)
    if mt5_status.get("connected"):
        balance = mt5_status.get("balance", 0.0)
        equity = mt5_status.get("equity", 0.0)
        margin_free = mt5_status.get("margin_free", 0.0)
        margin_used = max(balance - margin_free, 0.0)
        usage = (margin_used / balance * 100) if balance else 0.0

        with col1:
            stat_card("Balance", f"${balance:,.2f}", "Account balance")
        with col2:
            stat_card("Equity", f"${equity:,.2f}", "Balance plus open PnL")
        with col3:
            stat_card("Free Margin", f"${margin_free:,.2f}", "Available margin")
        with col4:
            stat_card("Margin Used", f"{usage:.1f}%", "Utilization")
    else:
        with col1:
            stat_card("MT5 Status", "Offline", "Connect MT5 to load metrics")
        with col2:
            stat_card("Balance", "N/A", "No account data")
        with col3:
            stat_card("Equity", "N/A", "No account data")
        with col4:
            stat_card("Margin Used", "N/A", "No account data")


def _plot_equity_curve(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["close_timestamp"],
            y=df["cumulative_pnl"],
            mode="lines+markers",
            line=dict(color="#2fbf8f", width=3),
            marker=dict(size=6),
            fill="tozeroy",
            fillcolor="rgba(47,191,143,0.2)",
        )
    )
    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis_title="Close time",
        yaxis_title="Cumulative net PnL",
        template="plotly_white",
    )
    return fig


def render_dashboard_tab() -> None:
    """Main dashboard view."""
    section_header("Live overview")
    render_quick_stats()

    section_header("Performance snapshot", "Closed trades over the last 30 days")
    stats = get_trading_stats(days=30)
    metric_grid(
        [
            {"label": "Trades (30d)", "value": str(stats.get("total_trades", 0)), "note": "Closed trades"},
            {"label": "Win Rate", "value": f"{stats.get('win_rate', 0.0):.1f}%", "note": "Closed trades"},
            {"label": "Net PnL", "value": f"${stats.get('net_profit', 0.0):,.2f}", "note": "Last 30 days"},
            {"label": "Profit Factor", "value": f"{stats.get('profit_factor', 0.0):.2f}", "note": "Gross profit/loss"},
        ],
        columns=4,
    )

    section_header("PnL curve", "Closed trades only")
    db = _get_db()
    end = datetime.now()
    start = end - timedelta(days=30)
    trades = db.get_closed_trades(start, end)
    df = pd.DataFrame(trades)
    if df.empty:
        empty_state("No closed trades", "No closed trades found in the last 30 days.")
    else:
        df["close_timestamp"] = pd.to_datetime(df["close_timestamp"])
        df["net_pnl"] = (
            df["profit"].fillna(0)
            - df["commission"].fillna(0)
            - df["swap"].fillna(0)
        )
        df = df.sort_values("close_timestamp")
        df["cumulative_pnl"] = df["net_pnl"].cumsum()
        st.plotly_chart(_plot_equity_curve(df), use_container_width=True)


def render_positions_tab() -> None:
    """Open positions view - reads from database."""
    section_header("Open positions")
    
    try:
        db = _get_db()
        
        # Get open positions from database
        # For now, we'll show a placeholder since we're reading from shared state
        from app.core.shared_state import get_shared_state_manager
        shared_state = get_shared_state_manager()
        state_data = shared_state.get_state()
        
        if not state_data or 'trading' not in state_data:
            st.info("No position data available yet. Bot is initializing...")
            return
        
        trading_data = state_data.get('trading', {})
        open_positions = trading_data.get('open_positions', 0)
        total_exposure = trading_data.get('total_exposure', 0.0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Open Positions", open_positions)
        with col2:
            st.metric("Total Exposure", f"{total_exposure:.2f}%")
        with col3:
            st.metric("Status", "Active" if open_positions > 0 else "No Positions")
        
        # Try to get recent trades from database
        try:
            conn = sqlite3.connect('data/trading_history.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT symbol, type, volume, open_price, open_timestamp, close_price, profit
                FROM trades
                WHERE close_timestamp IS NULL
                ORDER BY open_timestamp DESC
                LIMIT 20
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                position_data = []
                for row in rows:
                    position_data.append({
                        "Symbol": row[0],
                        "Side": "BUY" if row[1] == 0 else "SELL",
                        "Volume": row[2],
                        "Entry": f"{row[3]:.5f}",
                        "Current": f"{row[5]:.5f}" if row[5] else "N/A",
                        "PnL": f"${row[6]:.2f}" if row[6] else "N/A",
                    })
                
                df = pd.DataFrame(position_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No open positions in database.")
        except Exception as e:
            st.warning(f"Could not load position details from database: {e}")
            
    except Exception as exc:
        st.error(f"Error loading positions: {exc}")


def render_analysis_tab() -> None:
    """Analysis and insights view."""
    section_header("Market analysis")
    empty_state(
        "Connect analysis pipeline",
        "Wire this to analysis_history and ai_decisions for live insights.",
    )

    col1, col2 = st.columns(2)
    with col1:
        section_header("Signal mix (sample)")
        st.write("- BUY: 62%")
        st.write("- SELL: 28%")
        st.write("- HOLD: 10%")
    with col2:
        section_header("AI confidence (sample)")
        st.write("- Average confidence: 0.71")
        st.write("- Guardrail threshold: 0.55")


def render_settings_tab() -> None:
    """Settings and configuration."""
    section_header("Configuration")
    config = _get_config()

    tab1, tab2, tab3 = st.tabs(["Trading", "Risk", "System"])
    with tab1:
        st.markdown("#### Trading")
        col1, col2 = st.columns(2)
        with col1:
            st.selectbox(
                "Trading mode",
                ["PAPER", "LIVE"],
                index=0 if config.trading.mode == "PAPER" else 1,
            )
        with col2:
            st.number_input(
                "Max concurrent positions",
                min_value=1,
                max_value=200,
                value=min(config.trading.default_max_positions, 200),
            )

    with tab2:
        st.markdown("#### Risk limits")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.slider("Risk per trade (%)", 0.1, 5.0, 1.0, 0.1)
        with col2:
            st.slider("Daily loss limit (%)", 1.0, 10.0, 3.0, 0.5)
        with col3:
            st.slider("Max drawdown (%)", 5.0, 30.0, 10.0, 1.0)

    with tab3:
        st.markdown("#### System status")
        st.write(f"Mode: {config.trading.mode}")
        st.write("Streamlit: active")


def render_logs_tab() -> None:
    """Activity and logs view."""
    section_header("Activity feed")
    db = _get_db()
    trades = db.get_trades(days=7)
    if not trades:
        empty_state("No recent trades", "No trades recorded in the last 7 days.")
        return

    df = pd.DataFrame(trades)
    df["open_timestamp"] = pd.to_datetime(df["open_timestamp"])
    df = df.sort_values("open_timestamp", ascending=False).head(20)
    st.dataframe(
        df[["open_timestamp", "symbol", "type", "volume", "open_price", "status"]],
        use_container_width=True,
        hide_index=True,
    )


def _statement_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    net = df["net_pnl"].sum()
    wins = df[df["net_pnl"] > 0]
    losses = df[df["net_pnl"] < 0]
    win_rate = (len(wins) / len(df) * 100) if len(df) else 0.0
    gross_profit = wins["net_pnl"].sum() if not wins.empty else 0.0
    gross_loss = abs(losses["net_pnl"].sum()) if not losses.empty else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
    avg_win = wins["net_pnl"].mean() if not wins.empty else 0.0
    avg_loss = losses["net_pnl"].mean() if not losses.empty else 0.0
    best_trade = df["net_pnl"].max() if not df.empty else 0.0
    worst_trade = df["net_pnl"].min() if not df.empty else 0.0
    return {
        "net": net,
        "total_trades": len(df),
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "best_trade": best_trade,
        "worst_trade": worst_trade,
    }


def render_statement_tab() -> None:
    """Account statement based on historical closed trades."""
    section_header("Account statement", "Historical closed trades")

    col1, col2, col3 = st.columns(3)
    with col1:
        range_key = st.selectbox("Range", ["7d", "30d", "90d", "365d", "Custom"])
    with col2:
        symbol_filter = st.text_input("Symbol filter (optional)").strip().upper()
    with col3:
        include_commission = st.toggle("Net after commission", value=True)

    end_date = datetime.now()
    if range_key == "Custom":
        date_range = st.date_input(
            "Start and end",
            value=(end_date.date() - timedelta(days=30), end_date.date()),
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date = datetime.combine(date_range[0], datetime.min.time())
            end_date = datetime.combine(date_range[1], datetime.max.time())
        else:
            start_date = end_date - timedelta(days=30)
    else:
        days = int(range_key.replace("d", ""))
        start_date = end_date - timedelta(days=days)

    db = _get_db()
    trades = db.get_closed_trades(start_date, end_date, symbol_filter or None)
    df = pd.DataFrame(trades)
    if df.empty:
        empty_state(
            "No closed trades",
            "No closed trades in the selected range. Ensure data/trading_history.db is populated.",
        )
        return

    df["open_timestamp"] = pd.to_datetime(df["open_timestamp"])
    df["close_timestamp"] = pd.to_datetime(df["close_timestamp"])
    df["gross_pnl"] = df["profit"].fillna(0)
    df["commission"] = df["commission"].fillna(0)
    df["swap"] = df["swap"].fillna(0)
    if include_commission:
        df["net_pnl"] = df["gross_pnl"] - df["commission"] - df["swap"]
    else:
        df["net_pnl"] = df["gross_pnl"]

    df = df.sort_values("close_timestamp")
    df["cumulative_pnl"] = df["net_pnl"].cumsum()
    df["close_date"] = df["close_timestamp"].dt.date

    metrics = _statement_metrics(df)
    metric_grid(
        [
            {"label": "Net PnL", "value": f"${metrics['net']:,.2f}", "note": "Selected range"},
            {"label": "Trades", "value": str(metrics["total_trades"]), "note": "Closed trades"},
            {"label": "Win Rate", "value": f"{metrics['win_rate']:.1f}%", "note": "Closed trades"},
            {"label": "Profit Factor", "value": f"{metrics['profit_factor']:.2f}", "note": "Gross profit/loss"},
            {"label": "Avg Win", "value": f"${metrics['avg_win']:,.2f}", "note": "Positive trades"},
            {"label": "Avg Loss", "value": f"${metrics['avg_loss']:,.2f}", "note": "Negative trades"},
            {"label": "Best Trade", "value": f"${metrics['best_trade']:,.2f}", "note": "Largest net trade"},
            {"label": "Worst Trade", "value": f"${metrics['worst_trade']:,.2f}", "note": "Smallest net trade"},
        ],
        columns=4,
    )

    section_header("Equity curve")
    st.plotly_chart(_plot_equity_curve(df), use_container_width=True)

    section_header("Daily summary")
    daily = (
        df.groupby("close_date")
        .agg(
            trades=("id", "count"),
            gross=("gross_pnl", "sum"),
            net=("net_pnl", "sum"),
        )
        .reset_index()
    )
    st.dataframe(daily, use_container_width=True, hide_index=True)

    section_header("Statement details")
    statement = df[
        [
            "close_timestamp",
            "ticket",
            "symbol",
            "type",
            "volume",
            "open_price",
            "close_price",
            "gross_pnl",
            "commission",
            "swap",
            "net_pnl",
        ]
    ].rename(
        columns={
            "close_timestamp": "close_time",
            "open_price": "entry",
            "close_price": "exit",
            "gross_pnl": "gross",
            "net_pnl": "net",
        }
    )
    st.dataframe(statement, use_container_width=True, hide_index=True)

    csv = statement.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download statement (CSV)",
        data=csv,
        file_name="account_statement.csv",
        mime="text/csv",
    )
