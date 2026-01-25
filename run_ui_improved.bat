@echo off
REM Run improved Streamlit UI
echo Starting AI Trading Bot - Modern UI...
cd /d %~dp0
.venv\Scripts\python.exe -m streamlit run app/ui_improved.py
pause
