# Script PowerShell para reiniciar ngrok rápidamente

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "🔄 REINICIANDO NGROK" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan

# Detener ngrok si está corriendo
Write-Host "`n🛑 Deteniendo ngrok existente..." -ForegroundColor Yellow
$ngrokProcess = Get-Process -Name ngrok -ErrorAction SilentlyContinue
if ($ngrokProcess) {
    Stop-Process -Name ngrok -Force
    Write-Host "✅ Ngrok detenido (PID: $($ngrokProcess.Id))" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "⚠️  Ngrok no estaba corriendo" -ForegroundColor Gray
}

# Iniciar ngrok
Write-Host "`n🚀 Iniciando ngrok en puerto 8501..." -ForegroundColor Yellow
Start-Process -FilePath "ngrok" -ArgumentList "http", "8501" -WindowStyle Hidden
Start-Sleep -Seconds 5

# Verificar que inició
$ngrokProcess = Get-Process -Name ngrok -ErrorAction SilentlyContinue
if ($ngrokProcess) {
    Write-Host "✅ Ngrok iniciado (PID: $($ngrokProcess.Id))" -ForegroundColor Green
    
    # Obtener URL pública
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction SilentlyContinue
        $publicUrl = $response.tunnels[0].public_url
        Write-Host "`n🌐 URL PÚBLICA:" -ForegroundColor Cyan
        Write-Host "   $publicUrl" -ForegroundColor White -BackgroundColor DarkGreen
        Write-Host "`n✅ Ngrok está activo y listo!" -ForegroundColor Green
    } catch {
        Write-Host "`n⚠️  Ngrok iniciado pero URL no disponible aún. Espera 10 segundos." -ForegroundColor Yellow
    }
} else {
    Write-Host "`n❌ Error: Ngrok no se pudo iniciar" -ForegroundColor Red
    Write-Host "   Verifica que ngrok esté instalado: ngrok version" -ForegroundColor Gray
}

Write-Host "`n" -NoNewline
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
