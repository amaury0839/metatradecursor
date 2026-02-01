# 📟 MONITOREO DEL BOT - Guía de Verificación

## 🔍 Cómo Verificar que TODO Funciona Correctamente

### 1. VERIFICAR QUE BOT ESTÁ TRADANDO

```powershell
# Ver últimos logs
Get-Content bot_continuous.log -Tail 50 | Select-String "signal|CLOSING|GATE"

# Debería ver líneas como:
✅ BTCUSD: SELL signal, confidence=0.75
⚡ ETHUSD | GATE_DECISION: AI_SKIPPED
🔴 CLOSING ADAUSD ticket ... : TIME LIMIT
```

### 2. VERIFICAR POSICIONES REALES

```powershell
# Ver posiciones abiertas en MT5
python check_positions.py

# Debería mostrar:
✅ MT5 connected
💰 CUENTA: 52704771
📊 POSICIONES ABIERTAS: 7-8
  Ticket: XXXXX Symbol: BTCUSD Type: SELL Volume: 0.14
  ...
```

### 3. VERIFICAR TIME_LIMIT ESTÁ ACTIVO

```powershell
# Buscar time_limit closes en logs
Get-Content bot_continuous.log -Tail 200 | Select-String "TIME_LIMIT|TIME LIMIT"

# Si ve esto = está funcionando ✅
⏱️  XRPUSD TIME_LIMIT: 65min > 60min (profit=$1.20)
⏱️  BTCUSD TIME_LIMIT: 70min > 60min (profit=$50.00)
```

Si NO ve time_limit closes en 2+ horas = Reiniciar:
```powershell
Stop-Process -Name python -Force
python run_bot.py
```

### 4. VERIFICAR AI GATE

```powershell
# Ver decisiones de AI gate
Get-Content bot_continuous.log -Tail 100 | Select-String "GATE_DECISION"

# Debería ver MEZCLA de:
⚡ SYMBOL | GATE_DECISION: AI_SKIPPED    (señales fuertes = sin IA)
🧠 SYMBOL | GATE_DECISION: AI_CALLED    (señales débiles = con IA)
```

Si SOLO ves AI_SKIPPED = Probablemente OK (mercado en tendencia fuerte)
Si SOLO ves AI_CALLED = Probablemente OK (mercado incertidumbre)

### 5. VERIFICAR APERTURAS DE TRADES

```powershell
# Ver trades ejecutados
Get-Content bot_continuous.log -Tail 100 | Select-String "✅ Order executed|Order placed|ticket="

# Debería ver nuevos trades cada ~60 segundos:
✅ Order placed successfully: SELL 100.0 lots of DOTUSD at 1.545, ticket=1443657662
✅ DOTUSD: Trade execution logged to database
```

---

## ⚠️ SEÑALES DE ALERTA

### 🔴 BAD SIGN #1: No hay TIME_LIMIT closes
**Síntoma:** Posiciones abiertas >120 minutos sin cerrarse
**Causa Probable:** TIME_LIMIT function falla o bot parado
**Solución:**
```powershell
# Reiniciar bot
Stop-Process -Name python -Force
python run_bot.py
```

### 🔴 BAD SIGN #2: Scheduler stopped
**Síntoma:** Ves en logs "Scheduler stopped"
**Causa:** Bot detuvo el trading loop
**Solución:**
```powershell
# Reiniciar
python run_bot.py
```

### 🔴 BAD SIGN #3: MT5 disconnected
**Síntoma:** Ves "MT5 not connected" o "Login failed"
**Causa:** Conexión perdida a MT5
**Solución:**
```powershell
# Verificar MT5 terminal está abierto
# Reiniciar bot
python run_bot.py
```

### 🟡 YELLOW FLAG #1: AI siempre CALLED
**Síntoma:** Todos los trades dicen "AI_CALLED"
**Posible Razón:** Mercado muy indeciso (normal en consolidación)
**Acción:** Monitorear, es normal

### 🟡 YELLOW FLAG #2: AI nunca CALLED
**Síntoma:** Todos los trades dicen "AI_SKIPPED"
**Posible Razón:** Mercado en tendencia clara (normal en trending)
**Acción:** Monitorear, es normal

---

## 📈 MÉTRICAS A MONITOREAR

### P&L Diario
```powershell
# Ver profit/loss del día
Get-Content bot_continuous.log | Select-String "profit:|Balance:|Equity:" | Select-Object -Last 3
```

Esperar:
- Balance = Inicial (~$4,850)
- Equity = Balance + P&L unrealized
- Profit = P&L del día (puede ser + o -)

### Número de Posiciones
```powershell
python check_positions.py | Select-String "POSICIONES|Total"
```

Esperar:
- 6-12 posiciones normalmente
- Max 12 (límite del bot)
- Si >12 = Problema en gestión riesgo

### Deal Count
```powershell
python check_positions.py | Select-String "HISTORIAL|Deal:"
```

Esperar:
- Aumentar constantemente (200+, 300+, 400+ deals)
- Si NO aumenta = Bot no abriendo trades

---

## 🔧 COMANDOS ÚTILES

```powershell
# Ver estado del bot cada 10 segundos
while($true) {
    Clear-Host
    "Bot Status - $(Get-Date)"
    Get-Process | Where-Object {$_.ProcessName -eq "python"} | Select-Object ProcessName,Id
    Get-Content bot_continuous.log -Tail 5
    Start-Sleep 10
}

# Ver posiciones en tiempo real
while($true) {
    Clear-Host
    python check_positions.py
    Start-Sleep 60
}

# Monitorear logs filtrados
Get-Content bot_continuous.log -Wait | Select-String "CLOSING|signal|GATE"
```

---

## 📊 CHECKLIST DIARIO

Cada mañana:

- [ ] Bot proceso está corriendo (`Get-Process python`)
- [ ] Posiciones abiertas entre 6-12 (`python check_positions.py`)
- [ ] P&L es razonable (no -20% losses en 1 hora)
- [ ] Logs muestran TIME_LIMIT closes después de 60 min
- [ ] AI GATE toma decisiones (mix de AI_SKIPPED y AI_CALLED)
- [ ] Nuevos trades se abren cada minuto
- [ ] Ngrok monitor está activo (`Get-Process ngrok`)
- [ ] UI corre en puerto 8501 (`Invoke-WebRequest http://localhost:8501`)

Si todo ✅ → Bot está bien

Si algo ❌ → Reiniciar bot y revisar logs

---

## 🆘 TROUBLESHOOTING RÁPIDO

### Problema: Bot no abre trades
```powershell
# Verificar logs
Get-Content bot_continuous.log -Tail 100 | Select-String "RSI_BLOCK|confidence|signal"

# Si ves muchos RSI_BLOCK = Mercado overbought/oversold
# Esperar o revisar parámetros RSI
```

### Problema: Posiciones no cierran
```powershell
# Verificar TIME_LIMIT
Get-Content bot_continuous.log -Tail 200 | Select-String "TIME_LIMIT|CLOSING"

# Si no ves nada = Reiniciar
Stop-Process -Name python -Force
python run_bot.py
```

### Problema: P&L muy negativo
```powershell
# Revisar tipos de trades
Get-Content bot_continuous.log -Tail 100 | Select-String "SELL|BUY|signal"

# Si solo SELL o solo BUY = Mercado unidireccional
# Bot espera cambio de tendencia
```

---

## 📞 CONTACTO DE EMERGENCIA

Si bot completamente parado:
```powershell
# Nuclear option - Stop everything
Stop-Process -Name python -Force
Stop-Process -Name ngrok -Force

# Restart all
python run_bot.py
python keep_ngrok_alive.py
python -m streamlit run app/main_ui.py
```

