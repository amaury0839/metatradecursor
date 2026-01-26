# Script para reiniciar el bot con Enhanced AI
# Ejecutar: .\restart_bot.ps1

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  REINICIANDO BOT CON ENHANCED AI" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Detener procesos existentes
Write-Host "[1/3] Deteniendo procesos anteriores..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*Metatrade*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Iniciar bot
Write-Host "[2/3] Iniciando bot con Enhanced AI..." -ForegroundColor Yellow
Write-Host "  - Enhanced AI: ACTIVO" -ForegroundColor Green
Write-Host "  - Web Search: ACTIVO" -ForegroundColor Green
Write-Host "  - Fallback: ACTIVO" -ForegroundColor Green
Write-Host ""

$botPath = "C:\Users\Shadow\Downloads\Metatrade"
$pythonExe = "$botPath\.venv\Scripts\python.exe"

# Iniciar bot en nueva ventana
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$botPath'; & '$pythonExe' run_local_bot.py" -WindowStyle Normal

Write-Host "[3/3] Esperando 5 segundos antes de iniciar UI..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Iniciar Streamlit UI
Write-Host "Iniciando Streamlit UI..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$botPath'; & '$pythonExe' -m streamlit run app/ui_improved.py --server.port 8501" -WindowStyle Normal

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  BOT INICIADO CORRECTAMENTE" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard UI: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "Revisa los logs para ver:" -ForegroundColor Yellow
Write-Host "  - 'Attempting ENHANCED decision'" -ForegroundColor White
Write-Host "  - 'Aggregated X data sources'" -ForegroundColor White
Write-Host "  - 'Enhanced decision succeeded'" -ForegroundColor White
Write-Host ""
Write-Host "Si quieres ngrok, ejecuta:" -ForegroundColor Yellow
Write-Host "  C:\Users\Shadow\Downloads\ngrok\ngrok.exe http 8501" -ForegroundColor White
Write-Host ""
