"""Simple test UI to verify Streamlit works"""

import streamlit as st

st.title("✅ Test UI - Streamlit Working")

st.write("This is a minimal test to verify Streamlit is working correctly.")

if st.button("Click me"):
    st.success("Button clicked! Streamlit is working.")

st.metric("Test Metric", "100", "+10")
