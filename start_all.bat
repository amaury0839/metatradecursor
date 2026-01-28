@echo off
REM Comprehensive Trading System Startup
echo.
echo ================================================================================
echo  ^>^>^> TRADING SYSTEM STARTUP (All Services)
echo ================================================================================
echo.

REM Kill any existing Python processes
echo Cleaning up old processes...
taskkill /F /IM python.exe 2>nul >nul
timeout /t 2 /nobreak >nul

REM Start BOT (standalone, no Streamlit)
echo.
echo [1/3] Starting Trading BOT...
start "Trading BOT" /MIN python run_bot.py
timeout /t 3 /nobreak >nul

REM Start API Server
echo [2/3] Starting API Server...
start "API Server" /MIN python -m uvicorn app.api.server:app --host 0.0.0.0 --port 8000
timeout /t 3 /nobreak >nul

REM Start Streamlit UI
echo [3/3] Starting Streamlit UI...
start "Streamlit UI" /MIN python -m streamlit run app/ui_improved.py --server.port 8501 --logger.level=error
timeout /t 3 /nobreak >nul

REM Success message
echo.
echo ================================================================================
echo    ✅ ALL SERVICES STARTED
echo ================================================================================
echo.
echo  📊 Dashboard:  http://localhost:8501
echo  🤖 Bot:        Running (PAPER mode, 30s interval)
echo  🔌 API:        http://localhost:8000
echo.
echo  Windows opened in minimized mode. Use Task Manager to view/close.
echo.
pause
