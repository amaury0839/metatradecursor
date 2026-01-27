"""Test version of Analysis Logs tab - simplified"""

import streamlit as st
import pandas as pd

st.title("Test: Analysis Logs")

st.info("Test endpoint: http://localhost:8000/logs/analysis?limit=5")

try:
    import requests
    response = requests.get("http://localhost:8000/logs/analysis?limit=5", timeout=3)
    if response.status_code == 200:
        data = response.json()
        st.success(f"✅ Got {data['total']} logs")
        
        if data['logs']:
            # Show first log as JSON
            st.json(data['logs'][0])
            
            # Show table
            logs_df = pd.DataFrame([{
                'timestamp': l.get('timestamp'),
                'symbol': l.get('symbol'),
                'type': l.get('analysis_type'),
                'status': l.get('status'),
                'message': str(l.get('message'))[:60]
            } for l in data['logs'][:10]])
            
            st.dataframe(logs_df, use_container_width=True)
except Exception as e:
    st.error(f"Error: {e}")
