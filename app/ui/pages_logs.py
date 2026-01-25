"""Logs and audit page - Works for both local and remote modes"""

import streamlit as st
import json

# Try to import local modules
try:
    from app.core.state import get_state_manager
    LOCAL_MODE = True
except ImportError:
    LOCAL_MODE = False


def render_logs():
    """Render logs page - auto-detects local or remote mode"""
    if LOCAL_MODE:
        render_logs_local()
    else:
        if "api_client" in st.session_state:
            render_logs_remote(st.session_state.api_client)
        else:
            st.error("API client not available.")


def render_logs_local():
    """Render logs page - Local mode"""
    state = get_state_manager()
    
    st.subheader("📋 Logs & Audit Trail")
    
    # Tabs
    tab1, tab2 = st.tabs(["Decisions Audit", "Trade History"])
    
    with tab1:
        st.markdown("### Decision Audit Trail")
        
        limit = st.number_input("Number of records", min_value=10, max_value=1000, 
                               value=100, step=10)
        
        if st.button("Refresh"):
            st.rerun()
        
        decisions = state.get_recent_decisions(limit=limit)
        
        if decisions:
            decision_data = []
            for dec in decisions:
                reason_text = ""
                if dec.get('reason'):
                    try:
                        reason_list = json.loads(dec.get('reason', '[]'))
                        reason_text = "; ".join(reason_list) if isinstance(reason_list, list) else str(dec.get('reason', ''))
                    except:
                        reason_text = str(dec.get('reason', ''))
                
                decision_data.append({
                    "Timestamp": dec.get('timestamp', '')[:19] if dec.get('timestamp') else '',
                    "Symbol": dec.get('symbol', ''),
                    "Timeframe": dec.get('timeframe', ''),
                    "Signal": dec.get('signal', ''),
                    "Action": dec.get('action', ''),
                    "Confidence": f"{dec.get('confidence', 0):.2f}",
                    "Volume": f"{dec.get('volume_lots', 0):.2f}" if dec.get('volume_lots') else "N/A",
                    "SL": f"{dec.get('sl_price', 0):.5f}" if dec.get('sl_price') else "N/A",
                    "TP": f"{dec.get('tp_price', 0):.5f}" if dec.get('tp_price') else "N/A",
                    "Risk OK": "✅" if dec.get('risk_checks_passed') else "❌",
                    "Executed": "✅" if dec.get('execution_success') else "❌",
                    "Reason": reason_text[:100] + "..." if len(reason_text) > 100 else reason_text,
                })
            
            st.dataframe(decision_data, use_container_width=True, height=400)
        else:
            st.info("No decisions recorded yet")
    
    with tab2:
        st.markdown("### Trade History")
        
        limit = st.number_input("Number of trades", min_value=10, max_value=1000, 
                               value=100, step=10, key="trades_limit")
        
        if st.button("Refresh Trades"):
            st.rerun()
        
        trades = state.get_recent_trades(limit=limit)
        
        if trades:
            trade_data = []
            for trade in trades:
                trade_data.append({
                    "Timestamp": trade.get('timestamp', '')[:19] if trade.get('timestamp') else '',
                    "Symbol": trade.get('symbol', ''),
                    "Action": trade.get('action', ''),
                    "Volume": f"{trade.get('volume_lots', 0):.2f}",
                    "Entry": f"{trade.get('entry_price', 0):.5f}",
                    "Exit": f"{trade.get('exit_price', 0):.5f}" if trade.get('exit_price') else "N/A",
                    "PnL": f"${trade.get('pnl', 0):.2f}" if trade.get('pnl') else "N/A",
                })
            
            st.dataframe(trade_data, use_container_width=True, height=400)
        else:
            st.info("No trades recorded yet")


def render_logs_remote(api_client):
    """Render logs page - Remote mode"""
    import asyncio
    
    st.subheader("📋 Logs & Audit Trail")
    
    tab1, tab2 = st.tabs(["Decisions Audit", "Trade History"])
    
    with tab1:
        st.markdown("### Decision Audit Trail")
        
        limit = st.number_input("Number of records", min_value=10, max_value=1000, 
                               value=100, step=10)
        
        if st.button("Refresh"):
            st.rerun()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        decisions = loop.run_until_complete(api_client.get_decisions(limit=limit))
        loop.close()
        
        if decisions:
            decision_data = []
            for dec in decisions:
                reason_text = ""
                if dec.get('reason'):
                    try:
                        reason_list = json.loads(dec.get('reason', '[]'))
                        reason_text = "; ".join(reason_list) if isinstance(reason_list, list) else str(dec.get('reason', ''))
                    except:
                        reason_text = str(dec.get('reason', ''))
                
                decision_data.append({
                    "Timestamp": dec.get('timestamp', '')[:19] if dec.get('timestamp') else '',
                    "Symbol": dec.get('symbol', ''),
                    "Signal": dec.get('signal', ''),
                    "Action": dec.get('action', ''),
                    "Confidence": f"{dec.get('confidence', 0):.2f}",
                    "Risk OK": "✅" if dec.get('risk_checks_passed') else "❌",
                    "Executed": "✅" if dec.get('execution_success') else "❌",
                })
            
            st.dataframe(decision_data, use_container_width=True, height=400)
        else:
            st.info("No decisions recorded yet")
    
    with tab2:
        st.markdown("### Trade History")
        
        limit = st.number_input("Number of trades", min_value=10, max_value=1000, 
                               value=100, step=10, key="trades_limit")
        
        if st.button("Refresh Trades"):
            st.rerun()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        trades = loop.run_until_complete(api_client.get_trades(limit=limit))
        loop.close()
        
        if trades:
            trade_data = []
            for trade in trades:
                trade_data.append({
                    "Timestamp": trade.get('timestamp', '')[:19] if trade.get('timestamp') else '',
                    "Symbol": trade.get('symbol', ''),
                    "Action": trade.get('action', ''),
                    "Volume": f"{trade.get('volume_lots', 0):.2f}",
                    "Entry": f"{trade.get('entry_price', 0):.5f}",
                    "Exit": f"{trade.get('exit_price', 0):.5f}" if trade.get('exit_price') else "N/A",
                    "PnL": f"${trade.get('pnl', 0):.2f}" if trade.get('pnl') else "N/A",
                })
            
            st.dataframe(trade_data, use_container_width=True, height=400)
        else:
            st.info("No trades recorded yet")
