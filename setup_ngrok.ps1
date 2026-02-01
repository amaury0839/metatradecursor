# A-Bot Ngrok Setup Script
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  A-BOT NGROK CONFIGURATION" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if ngrok is installed
Write-Host "🔍 Verificando si Ngrok está instalado..." -ForegroundColor Yellow
$ngrokExists = Get-Command ngrok -ErrorAction SilentlyContinue

if (-not $ngrokExists) {
    Write-Host "❌ Ngrok no está instalado" -ForegroundColor Red
    Write-Host ""
    Write-Host "📥 Descargando e instalando Ngrok..." -ForegroundColor Yellow
    
    # Download ngrok
    $ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    $ngrokZip = "$PSScriptRoot\ngrok.zip"
    $ngrokDir = "$PSScriptRoot\ngrok"
    
    # Create ngrok directory if it doesn't exist
    if (-not (Test-Path $ngrokDir)) {
        New-Item -ItemType Directory -Path $ngrokDir -Force | Out-Null
    }
    
    Write-Host "⬇️  Descargando desde: $ngrokUrl" -ForegroundColor Cyan
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $ngrokUrl -OutFile $ngrokZip -UseBasicParsing
        Write-Host "✅ Descarga completada" -ForegroundColor Green
        
        # Extract
        Write-Host "📦 Extrayendo archivos..." -ForegroundColor Cyan
        Expand-Archive -Path $ngrokZip -DestinationPath $ngrokDir -Force
        Write-Host "✅ Archivos extraídos" -ForegroundColor Green
        
        # Add to PATH
        $ngrokPath = "$ngrokDir\ngrok.exe"
        if (Test-Path $ngrokPath) {
            $env:PATH += ";$ngrokDir"
            Write-Host "✅ Ngrok agregado a PATH" -ForegroundColor Green
        }
        
        Remove-Item $ngrokZip -Force
    } catch {
        Write-Host "❌ Error al descargar Ngrok: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ Ngrok ya está instalado" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACIÓN DE NGROK" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get authentication token
$authFile = "$PSScriptRoot\.ngrok-config\auth.txt"
if (Test-Path $authFile) {
    $token = Get-Content $authFile -Raw
    Write-Host "✅ Token de autenticación encontrado" -ForegroundColor Green
} else {
    Write-Host "⚠️  Token de autenticación no configurado" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📝 Para configurar el token:" -ForegroundColor Cyan
    Write-Host "1. Ve a https://dashboard.ngrok.com/auth/your-authtoken" -ForegroundColor White
    Write-Host "2. Copia tu token de autenticación" -ForegroundColor White
    Write-Host "3. Ejecuta: ngrok config add-authtoken TU_TOKEN_AQUI" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INICIO DE TÚNELES NGROK" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create ngrok config file
$configDir = "$PSScriptRoot\.ngrok"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

$configFile = "$configDir\ngrok.yml"

$config = @"
version: "2"
tunnels:
  a-bot-api:
    proto: http
    addr: localhost:8002
    inspect: false
  a-bot-dashboard:
    proto: http
    addr: localhost:8504
    inspect: false
"@

Set-Content -Path $configFile -Value $config
Write-Host "✅ Archivo de configuración creado: $configFile" -ForegroundColor Green

Write-Host ""
Write-Host "📋 Configuración de Túneles:" -ForegroundColor Cyan
Write-Host "  • A-Bot API: localhost:8002 → ngrok" -ForegroundColor White
Write-Host "  • A-Bot Dashboard: localhost:8504 → ngrok" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INICIAR NGROK" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🚀 Para iniciar los túneles, ejecuta:" -ForegroundColor Yellow
Write-Host ""
Write-Host "ngrok start --config=""$configFile"" --all" -ForegroundColor Cyan
Write-Host ""

Write-Host "O para iniciar túneles individuales:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Opción 1: API solamente" -ForegroundColor White
Write-Host "ngrok http 8002" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opción 2: Dashboard solamente" -ForegroundColor White
Write-Host "ngrok http 8504" -ForegroundColor Cyan
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INFORMACIÓN IMPORTANTE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Después de iniciar ngrok, verás:" -ForegroundColor Green
Write-Host "   • URL pública para acceder a A-Bot" -ForegroundColor White
Write-Host "   • Estadísticas de conexión" -ForegroundColor White
Write-Host "   • Panel de inspección en http://localhost:4040" -ForegroundColor White
Write-Host ""

Write-Host "💡 Recuerda:" -ForegroundColor Cyan
Write-Host "   • El bot API debe estar ejecutándose (puerto 8002)" -ForegroundColor White
Write-Host "   • El dashboard debe estar ejecutándose (puerto 8504)" -ForegroundColor White
Write-Host "   • Los túneles se cerrarán si cierras la ventana de Ngrok" -ForegroundColor White
Write-Host ""
