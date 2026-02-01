# A-Bot Quick Ngrok Setup - One-Shot Installation & Launch
# Ejecuta: powershell -ExecutionPolicy Bypass -File quick_ngrok.ps1

param(
    [string]$authtoken = ""
)

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           🚀 A-Bot Ngrok Quick Setup & Launch 🚀              ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Verificar si Ngrok está instalado
Write-Host "[1/4] 🔍 Verificando instalación de Ngrok..." -ForegroundColor Yellow

$ngrokPath = $(try { Get-Command ngrok -ErrorAction Stop | Select-Object -ExpandProperty Source } catch { $null })

if ($null -eq $ngrokPath) {
    Write-Host "      ⚠️  Ngrok no encontrado. Instalando..." -ForegroundColor Yellow
    
    # Descargar Ngrok
    $ngrokUrl = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    $ngrokZip = "$env:TEMP\ngrok.zip"
    $ngrokExtract = "$env:TEMP\ngrok"
    
    Write-Host "      📥 Descargando Ngrok desde: $ngrokUrl" -ForegroundColor Cyan
    
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $ngrokUrl -OutFile $ngrokZip -UseBasicParsing -ErrorAction Stop
        Write-Host "      ✅ Descarga completada" -ForegroundColor Green
    } catch {
        Write-Host "      ❌ Error descargando Ngrok: $_" -ForegroundColor Red
        exit 1
    }
    
    # Extraer archivo
    Write-Host "      📦 Extrayendo archivo..." -ForegroundColor Cyan
    
    try {
        if (Test-Path $ngrokExtract) { Remove-Item $ngrokExtract -Recurse -Force }
        Expand-Archive -Path $ngrokZip -DestinationPath $ngrokExtract -ErrorAction Stop
        Write-Host "      ✅ Extracción completada" -ForegroundColor Green
    } catch {
        Write-Host "      ❌ Error extrayendo: $_" -ForegroundColor Red
        exit 1
    }
    
    # Mover a Program Files
    $ngrokProgram = "C:\Program Files\ngrok"
    
    Write-Host "      📂 Moviendo a Program Files..." -ForegroundColor Cyan
    
    try {
        if (Test-Path $ngrokProgram) { Remove-Item $ngrokProgram -Recurse -Force }
        New-Item -ItemType Directory -Path $ngrokProgram -Force | Out-Null
        Copy-Item "$ngrokExtract\ngrok.exe" -Destination $ngrokProgram -Force
        Write-Host "      ✅ Instalación completada en: $ngrokProgram" -ForegroundColor Green
    } catch {
        Write-Host "      ⚠️  No se pudo instalar en Program Files, usando $env:TEMP" -ForegroundColor Yellow
        $ngrokProgram = $ngrokExtract
    }
    
    # Agregar a PATH
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if (-not $currentPath.Contains($ngrokProgram)) {
        [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$ngrokProgram", "User")
        $env:PATH += ";$ngrokProgram"
        Write-Host "      ✅ Ngrok agregado al PATH" -ForegroundColor Green
    }
    
    # Limpiar
    Remove-Item $ngrokZip -Force -ErrorAction SilentlyContinue
    
} else {
    Write-Host "      ✅ Ngrok ya está instalado en: $ngrokPath" -ForegroundColor Green
}

Write-Host ""

# Obtener token si no fue proporcionado
if ([string]::IsNullOrWhiteSpace($authtoken)) {
    Write-Host "[2/4] 🔐 Autenticación de Ngrok" -ForegroundColor Yellow
    
    # Verificar si ya existe token guardado
    $ngrokConfigPath = "$env:USERPROFILE\.ngrok2\ngrok.yml"
    
    if (Test-Path $ngrokConfigPath) {
        Write-Host "      ✅ Archivo de configuración de Ngrok encontrado" -ForegroundColor Green
        Write-Host ""
        Write-Host "      📋 Contenido actual:" -ForegroundColor Cyan
        Get-Content $ngrokConfigPath | ForEach-Object { Write-Host "         $_" -ForegroundColor Gray }
        Write-Host ""
        Write-Host "      ❓ ¿Usar token existente? (S/n): " -ForegroundColor Yellow -NoNewline
        
        $response = Read-Host
        if ($response -ne "n") {
            Write-Host "      ✅ Usando token existente" -ForegroundColor Green
        } else {
            $authtoken = Read-Host "      🔑 Ingresa tu Ngrok auth token (obtén uno en https://dashboard.ngrok.com)"
        }
    } else {
        Write-Host "      ❌ No se encontró token de Ngrok guardado" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "      📖 Instrucciones:" -ForegroundColor Cyan
        Write-Host "         1. Ve a: https://dashboard.ngrok.com/auth/your-authtoken" -ForegroundColor Gray
        Write-Host "         2. Crea una cuenta (es gratis)" -ForegroundColor Gray
        Write-Host "         3. Copia tu token de autenticación" -ForegroundColor Gray
        Write-Host ""
        
        $authtoken = Read-Host "      🔑 Ingresa tu Ngrok auth token"
        
        if ([string]::IsNullOrWhiteSpace($authtoken)) {
            Write-Host "      ❌ Token no proporcionado. Abortando..." -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "[2/4] 🔐 Usando token proporcionado" -ForegroundColor Yellow
}

# Configurar token si fue proporcionado
if (-not [string]::IsNullOrWhiteSpace($authtoken)) {
    Write-Host "      🔧 Configurando token..." -ForegroundColor Cyan
    
    try {
        ngrok config add-authtoken $authtoken 2>&1 | Out-Null
        Write-Host "      ✅ Token configurado exitosamente" -ForegroundColor Green
    } catch {
        Write-Host "      ⚠️  Error configurando token (pero continuaremos): $_" -ForegroundColor Yellow
    }
}

Write-Host ""

# Verificar puertos locales
Write-Host "[3/4] 🔌 Verificando servicios locales..." -ForegroundColor Yellow

$apiRunning = $false
$uiRunning = $false

try {
    $testAPI = Test-NetConnection -ComputerName localhost -Port 8002 -InformationLevel Quiet -ErrorAction SilentlyContinue
    if ($testAPI) {
        Write-Host "      ✅ A-Bot API ejecutándose en puerto 8002" -ForegroundColor Green
        $apiRunning = $true
    } else {
        Write-Host "      ⚠️  A-Bot API NO está ejecutándose en puerto 8002" -ForegroundColor Yellow
    }
} catch { }

try {
    $testUI = Test-NetConnection -ComputerName localhost -Port 8504 -InformationLevel Quiet -ErrorAction SilentlyContinue
    if ($testUI) {
        Write-Host "      ✅ A-Bot Dashboard ejecutándose en puerto 8504" -ForegroundColor Green
        $uiRunning = $true
    } else {
        Write-Host "      ⚠️  A-Bot Dashboard NO está ejecutándose en puerto 8504" -ForegroundColor Yellow
    }
} catch { }

Write-Host ""

if (-not $apiRunning -and -not $uiRunning) {
    Write-Host "      ⚠️  ADVERTENCIA: Ningún servicio está ejecutándose localmente" -ForegroundColor Red
    Write-Host "      📝 Asegúrate de ejecutar primero:" -ForegroundColor Yellow
    Write-Host "         - Terminal 1: A-Bot API en puerto 8002" -ForegroundColor Gray
    Write-Host "         - Terminal 2: A-Bot Dashboard en puerto 8504" -ForegroundColor Gray
}

Write-Host ""

# Iniciar Ngrok
Write-Host "[4/4] 🚀 Iniciando túneles Ngrok..." -ForegroundColor Yellow
Write-Host ""

# Crear configuración si no existe
$ngrokConfigDir = "$env:USERPROFILE\.ngrok2"
if (-not (Test-Path $ngrokConfigDir)) {
    New-Item -ItemType Directory -Path $ngrokConfigDir -Force | Out-Null
}

# Crear config file para iniciar múltiples túneles
$configFile = "$env:TEMP\ngrok_abot_config.yml"
@"
version: "3"
authtoken: `${NGROK_AUTHTOKEN}
web_addr: 127.0.0.1:4040
tunnels:
  a-bot-api:
    addr: 8002
    proto: http
  a-bot-dashboard:
    addr: 8504
    proto: http
"@ | Set-Content $configFile

Write-Host "      📊 Panel de Inspección Ngrok: http://localhost:4040" -ForegroundColor Cyan
Write-Host ""
Write-Host "      🌐 A-Bot será expuesto con estas URLs públicas:" -ForegroundColor Cyan
Write-Host "         - API: https://tu-ngrok-id.ngrok.io" -ForegroundColor Gray
Write-Host "         - Dashboard: https://tu-otro-ngrok-id.ngrok.io" -ForegroundColor Gray
Write-Host ""
Write-Host "      ⚠️  Las URLs cambian cada vez que reinicia Ngrok (sin plan pago)" -ForegroundColor Yellow
Write-Host ""

# Iniciar Ngrok
Write-Host "      ⏳ Iniciando Ngrok (Ctrl+C para detener)..." -ForegroundColor Cyan
Write-Host ""

try {
    ngrok start --all
} catch {
    Write-Host "      ❌ Error iniciando Ngrok: $_" -ForegroundColor Red
    exit 1
}
