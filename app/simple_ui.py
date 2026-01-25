"""Simple Streamlit UI"""
import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(
    page_title="AI Forex Bot", 
    page_icon="📈",
    layout="wide"
)

st.title("🤖 AI Forex Trading Bot")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Status")
    try:
        response = requests.get("http://localhost:8000/status/trading", timeout=2)
        if response.status_code == 200:
            data = response.json()
            st.metric("Scheduler", "🟢 Running" if data.get("scheduler_running") else "🔴 Stopped")
            st.metric("Kill Switch", "🔴 Active" if data.get("kill_switch_active") else "🟢 Inactive")
            st.metric("Open Positions", data.get("open_positions", 0))
            st.metric("Equity", f"${data.get('equity', 0):,.2f}")
        else:
            st.error("Cannot connect to API")
    except Exception as e:
        st.error(f"Connection error: {str(e)}")

with col2:
    st.subheader("📡 Trading Status")
    if st.button("🎯 Start Scheduler"):
        try:
            requests.post("http://localhost:8000/control/scheduler/start")
            st.success("Scheduler started!")
            st.rerun()
        except:
            st.error("Failed to start")
    
    if st.button("⏹️ Stop Scheduler"):
        try:
            requests.post("http://localhost:8000/control/scheduler/stop")
            st.success("Scheduler stopped!")
            st.rerun()
        except:
            st.error("Failed to stop")

st.divider()

# Symbols info
st.subheader("💱 Trading Symbols")
try:
    response = requests.get("http://localhost:8000/symbols", timeout=2)
    if response.status_code == 200:
        symbols = response.json()
        cols = st.columns(len(symbols.get("symbols", [])))
        for i, symbol in enumerate(symbols.get("symbols", [])):
            with cols[i]:
                st.markdown(f"**{symbol}**")
except:
    st.info("Symbols data unavailable")

st.divider()

# Recent decisions
st.subheader("📋 Recent Decisions")
try:
    response = requests.get("http://localhost:8000/decisions", timeout=2)
    if response.status_code == 200:
        decisions = response.json()
        if decisions.get("decisions"):
            for decision in decisions["decisions"][-5:]:
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"**{decision.get('symbol')}**")
                    col2.write(f"Action: {decision.get('action')}")
                    col3.write(f"Confidence: {decision.get('confidence', 0):.2%}")
        else:
            st.info("No decisions yet")
except:
    st.info("Decisions data unavailable")

st.divider()

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
st.caption("🔗 Bot API: http://localhost:8000")
