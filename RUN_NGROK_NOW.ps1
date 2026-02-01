# 🚀 A-Bot Ngrok - Ultra Quick Start
# Ejecuta esto en PowerShell para instalar y ejecutar Ngrok inmediatamente

# Permitir ejecución de scripts
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

Write-Host @"
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║                    🚀 A-Bot Ngrok Ultra Quick Start 🚀                   ║
║                                                                          ║
║                    Exponiendo A-Bot al Internet...                       ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Función para descargar Ngrok
function Install-Ngrok {
    Write-Host "`n[PASO 1] Descargando e instalando Ngrok..." -ForegroundColor Yellow
    
    try {
        # URL de descarga
        $url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
        $output = "$env:TEMP\ngrok.zip"
        
        # Descargar
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Write-Host "  ↓ Descargando desde: $url" -ForegroundColor Gray
        
        $progressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing
        
        # Extraer
        $extractPath = "$env:TEMP\ngrok_extract"
        if (Test-Path $extractPath) { Remove-Item $extractPath -Recurse -Force }
        
        Write-Host "  📦 Extrayendo archivo..." -ForegroundColor Gray
        Expand-Archive -Path $output -DestinationPath $extractPath -Force
        
        # Mover a Program Files
        $installPath = "C:\Program Files\ngrok"
        if (Test-Path $installPath) { Remove-Item $installPath -Recurse -Force }
        New-Item -ItemType Directory -Path $installPath -Force | Out-Null
        Copy-Item "$extractPath\ngrok.exe" -Destination $installPath -Force
        
        # Agregar a PATH
        $pathVar = [Environment]::GetEnvironmentVariable("PATH", "User")
        if ($pathVar -notlike "*ngrok*") {
            [Environment]::SetEnvironmentVariable("PATH", "$pathVar;$installPath", "User")
            $env:PATH += ";$installPath"
        }
        
        # Limpiar
        Remove-Item $output -Force
        Remove-Item $extractPath -Recurse -Force
        
        Write-Host "  ✅ Ngrok instalado correctamente" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Host "  ❌ Error en instalación: $_" -ForegroundColor Red
        return $false
    }
}

# Función para configurar token
function Configure-NgrokToken {
    param([string]$token)
    
    Write-Host "`n[PASO 2] Configurando autenticación de Ngrok..." -ForegroundColor Yellow
    
    if ([string]::IsNullOrWhiteSpace($token)) {
        Write-Host "  ℹ️  No se proporcionó token. Solicitando..." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  📋 INSTRUCCIONES:" -ForegroundColor Yellow
        Write-Host "     1. Abre: https://dashboard.ngrok.com/auth/your-authtoken" -ForegroundColor Gray
        Write-Host "     2. Crea una cuenta gratis (o inicia sesión)" -ForegroundColor Gray
        Write-Host "     3. Copia el token que ves en la pantalla" -ForegroundColor Gray
        Write-Host ""
        
        $token = Read-Host "  🔑 Pega tu Ngrok auth token aquí"
    }
    
    if ([string]::IsNullOrWhiteSpace($token)) {
        Write-Host "  ⚠️  Token vacío. Continuando sin autenticación..." -ForegroundColor Yellow
        return $false
    }
    
    try {
        ngrok config add-authtoken $token 2>&1 | Out-Null
        Write-Host "  ✅ Token configurado correctamente" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  ⚠️  Error configurando token (continuando igualmente): $_" -ForegroundColor Yellow
        return $false
    }
}

# Función para verificar puertos
function Test-LocalServices {
    Write-Host "`n[PASO 3] Verificando servicios locales..." -ForegroundColor Yellow
    
    $allGood = $true
    
    try {
        $apiTest = (New-Object System.Net.Sockets.TcpClient).ConnectAsync("127.0.0.1", 8002).Wait(1000)
        if ($apiTest) {
            Write-Host "  ✅ A-Bot API activo en puerto 8002" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  A-Bot API NO encontrado en puerto 8002" -ForegroundColor Yellow
            $allGood = $false
        }
    } catch {
        Write-Host "  ⚠️  A-Bot API NO encontrado en puerto 8002" -ForegroundColor Yellow
        $allGood = $false
    }
    
    try {
        $uiTest = (New-Object System.Net.Sockets.TcpClient).ConnectAsync("127.0.0.1", 8504).Wait(1000)
        if ($uiTest) {
            Write-Host "  ✅ A-Bot Dashboard activo en puerto 8504" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  A-Bot Dashboard NO encontrado en puerto 8504" -ForegroundColor Yellow
            $allGood = $false
        }
    } catch {
        Write-Host "  ⚠️  A-Bot Dashboard NO encontrado en puerto 8504" -ForegroundColor Yellow
        $allGood = $false
    }
    
    if (-not $allGood) {
        Write-Host ""
        Write-Host "  ⚠️  ADVERTENCIA: Algunos servicios no están activos" -ForegroundColor Red
        Write-Host "     Abre otras terminales y ejecuta:" -ForegroundColor Yellow
        Write-Host "     - Terminal 2: python -m uvicorn app.api.server:app --host 0.0.0.0 --port 8002" -ForegroundColor Gray
        Write-Host "     - Terminal 3: streamlit run app/main_ui.py --server.port 8504" -ForegroundColor Gray
    }
    
    return $allGood
}

# Función para iniciar Ngrok
function Start-Ngrok {
    Write-Host "`n[PASO 4] Iniciando túneles Ngrok..." -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                      🌐 NGROK EN EJECUCIÓN 🌐                 ║" -ForegroundColor Cyan
    Write-Host "╠════════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
    Write-Host "║                                                                ║" -ForegroundColor Cyan
    Write-Host "║  📊 Panel de inspección:  http://localhost:4040              ║" -ForegroundColor Cyan
    Write-Host "║  🌐 API pública:          https://xxxx-xxxx.ngrok.io         ║" -ForegroundColor Cyan
    Write-Host "║  📱 Dashboard público:    https://yyyy-yyyy.ngrok.io         ║" -ForegroundColor Cyan
    Write-Host "║                                                                ║" -ForegroundColor Cyan
    Write-Host "║  ⏸️  Presiona CTRL+C para detener                            ║" -ForegroundColor Cyan
    Write-Host "║                                                                ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        ngrok start --config="$env:USERPROFILE\.ngrok2\ngrok.yml" --all 2>&1
    } catch {
        Write-Host "❌ Error iniciando Ngrok: $_" -ForegroundColor Red
        exit 1
    }
}

# MAIN EXECUTION
try {
    # Paso 1: Instalar Ngrok si es necesario
    $ngrokExists = $null -ne (Get-Command ngrok -ErrorAction SilentlyContinue)
    if (-not $ngrokExists) {
        if (-not (Install-Ngrok)) {
            Write-Host "`n❌ Falló la instalación de Ngrok" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "`n[PASO 1] Ngrok ya está instalado ✅" -ForegroundColor Green
    }
    
    # Paso 2: Configurar token
    $token = $args[0]
    Configure-NgrokToken -token $token | Out-Null
    
    # Paso 3: Verificar servicios locales
    Test-LocalServices | Out-Null
    
    # Paso 4: Iniciar Ngrok
    Start-Ngrok
    
} catch {
    Write-Host "`n❌ Error inesperado: $_" -ForegroundColor Red
    exit 1
}
