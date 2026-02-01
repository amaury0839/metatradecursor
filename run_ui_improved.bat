@echo off
REM Run unified Streamlit UI
echo Starting AI Trading Bot - UI...
cd /d %~dp0
.venv\Scripts\python.exe -m streamlit run app/main.py
pause
