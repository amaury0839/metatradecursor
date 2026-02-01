@echo off
REM A-Bot Ngrok Tunnel Launcher
REM ============================================================================

echo.
echo ========================================
echo  A-BOT NGROK TUNNEL LAUNCHER
echo ========================================
echo.

REM Check if ngrok is available
where ngrok >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Ngrok no está instalado o no está en PATH
    echo.
    echo Para instalar ngrok:
    echo 1. Descarga desde: https://ngrok.com/download
    echo 2. Extrae el archivo
    echo 3. Agrega ngrok.exe a tu PATH
    echo.
    pause
    exit /b 1
)

echo [OK] Ngrok encontrado
echo.

REM Check if authentication token is set
ngrok config check >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Ngrok no está autenticado
    echo.
    echo Para configurar el token:
    echo 1. Ve a: https://dashboard.ngrok.com/auth/your-authtoken
    echo 2. Copia tu token
    echo 3. Ejecuta: ngrok config add-authtoken TU_TOKEN_AQUI
    echo.
    pause
    exit /b 1
)

echo [OK] Ngrok autenticado
echo.

echo ========================================
echo  INICIANDO TÚNELES
echo ========================================
echo.

REM Launch ngrok with both tunnels
echo [INFO] Iniciando túneles para A-Bot...
echo   - API Bot: localhost:8002
echo   - Dashboard: localhost:8504
echo.

REM Check if both services are running
timeout /t 2 >nul

echo [INFO] Abriendo ngrok con ambos túneles...
echo.

REM Start ngrok
ngrok start --all

REM If ngrok config file doesn't exist, start with manual tunnels
if %errorlevel% neq 0 (
    echo.
    echo [INFO] Usando túneles individuales...
    echo [INFO] Nota: Necesitas ejecutar esto en múltiples ventanas
    echo.
    echo Para la API:
    echo   ngrok http 8002
    echo.
    echo Para el Dashboard:
    echo   ngrok http 8504
    echo.
    pause
)
