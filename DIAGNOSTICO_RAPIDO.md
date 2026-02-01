# DIAGNOSTICO RAPIDO - Cómo verificar que todo funciona

## Pregunta 1: "¿Funciona el Backtest?"

### Opción A: Ver resultado (Rápido - 2 minutos)
```
Navegar a: c:\Users\Shadow\Downloads\Metatrade\data\backtest_results.json

Buscar: 
  - "optimization_score"
  - "win_rate"
  - "profit_factor"

Si ve estos campos → ✅ BACKTEST FUNCIONA
Si no ve nada → ❌ BACKTEST NO HA CORRIDO
```

### Opción B: Ejecutar test (Verificación - 5 minutos)
```
En PowerShell:
  
cd C:\Users\Shadow\Downloads\Metatrade
.venv\Scripts\Activate.ps1
python -c "
from app.backtest.backtest_engine import BacktestEngine
engine = BacktestEngine()
result = engine.backtest_symbol('EURUSD', days=3)
print('✓ Backtest completado:', result.get('metrics', {}).get('win_rate', 'N/A'))
"

Resultado esperado:
  ✓ Backtest completado: 0.65  (o algún porcentaje)
```

---

## Pregunta 2: "¿Funciona la IA?"

### Verificación: Revisar logs (Rápido - 3 minutos)
```
Ver últimas líneas:
  Get-Content -Path "c:\Users\Shadow\Downloads\Metatrade\logs\trading_bot.log" -Tail 50

Buscar patrones:
  • "AI SKIP" = IA no necesaria (60% esperado)
  • "AI NEEDED" = IA llamada (40% esperado)
  • "GATE_DECISION" = Gate working

Si ve ambos → ✅ IA FUNCIONA
Si solo ve SKIP → ⚠️ Revisar si hay trades en ventana gris
```

### Verificación: Test rápido (5 minutos)
```
python -c "
from app.ai.ai_gate import AIGate

gate = AIGate()
print('AIGate inicializado')

# Test 1: Strong signal
result, reason = gate.needs_ai('STRONG_BUY', {'rsi': 30})
print(f'Test STRONG_BUY: needs_ia={result} (esperado: False)')

# Test 2: Gray zone
result, reason = gate.needs_ai('BUY', {'rsi': 50, 'ema_fast': 100, 'ema_slow': 100})
print(f'Test gray zone: needs_ia={result} (esperado: True)')
"

Resultado esperado:
  AIGate inicializado
  Test STRONG_BUY: needs_ia=False (esperado: False) ✓
  Test gray zone: needs_ia=True (esperado: True) ✓
```

---

## Pregunta 3: "¿Funcionan los reajustes de riesgo?"

### Verificación A: Ver posiciones abiertas (1 minuto)
```
Ir a UI: http://localhost:8501

Buscar tabla: "Open Positions"

Ver columnas:
  - Symbol
  - Direction (BUY/SELL)
  - Entry Price
  - Stop Loss (debe ser menor para BUY, mayor para SELL)
  - Take Profit (debe ser mayor para BUY, menor para SELL)

Si todos tienen SL y TP → ✅ REAJUSTES FUNCIONAN
Si faltan SL/TP → ❌ REVISAR EXECUTION
```

### Verificación B: Check Risk Manager (3 minutos)
```
python -c "
from app.trading.risk import RiskManager

risk = RiskManager()
print(f'Max positions: {risk.max_positions} (debe ser 50)')
print(f'Max daily loss: {risk.max_daily_loss_pct}% (debe ser 10%)')
print(f'Max exposure: {risk.max_total_exposure_pct}% (debe ser 15%)')

# Test: ¿Cuánto riesgo para cada símbolo?
print(f'EURUSD risk: {risk.get_risk_pct_for_symbol(\"EURUSD\")}% (debe ser ~2%)')
print(f'BTCUSD risk: {risk.get_risk_pct_for_symbol(\"BTCUSD\")}% (debe ser ~3%)')
"

Resultado esperado:
  Max positions: 50
  Max daily loss: 10.0%
  Max exposure: 15.0%
  EURUSD risk: 0.02%
  BTCUSD risk: 0.03%
  
Si ve todos estos valores → ✅ RISK MANAGER OK
```

### Verificación C: Check Risk Profiles (2 minutos)
```
python -c "
from app.trading.risk_profiles import RiskProfileManager

profiles = RiskProfileManager()
print(f'Current: {profiles.current_profile.name}')
print(f'Available: {list(profiles.PROFILES.keys())}')

for name, profile in profiles.PROFILES.items():
    print(f'{name}: risk={profile.risk_per_trade}%, max_pos={profile.max_positions}')
"

Resultado esperado:
  Current: BALANCED
  Available: ['CONSERVATIVE', 'BALANCED', 'AGGRESSIVE']
  CONSERVATIVE: risk=0.25%, max_pos=3
  BALANCED: risk=0.5%, max_pos=5
  AGGRESSIVE: risk=0.75%, max_pos=7
  
Si ve estos perfiles → ✅ PROFILES OK
```

### Verificación D: Check Position Manager (2 minutos)
```
python -c "
from app.trading.position_manager import PositionManager

pos = PositionManager()

# Test RSI close
should_close, reason = pos.should_close_on_rsi_extreme('BTCUSD', 'BUY', 85, 45000, 44000)
print(f'RSI > 80 close: {should_close} (esperado: True)')

# Test trailing stop  
trailing = pos.calculate_trailing_stop('EURUSD', 'BUY', 1.0950, 1.0900, 1.0880, 0.0050)
print(f'Trailing stop updated: {trailing is not None} (esperado: True)')
"

Resultado esperado:
  RSI > 80 close: True
  Trailing stop updated: True
  
Si ve True en ambos → ✅ POSITION MANAGER OK
```

---

## Pregunta 4: "¿Se está ejecutando el bot?"

### Verificación A: Ver procesos (1 minuto)
```
PowerShell:
  Get-Process | Select-Object ProcessName | findstr python

Buscar: python.exe (debe aparecer)

Si ve python.exe → ✅ BOT CORRIENDO
Si no ve nada → ❌ BOT NO INICIADO
```

### Verificación B: Ver logs en vivo (2 minutos)
```
PowerShell:
  
Get-Content -Path "logs\trading_bot.log" -Tail 100 -Follow

Buscar:
  - {"event": "EURUSD", "level": "info"
  - Order placed successfully
  - Trading loop complete

Si ve eventos nuevos cada 60 segundos → ✅ BOT ACTIVO
Si logs están estáticos → ❌ BOT DETENIDO
```

### Verificación C: Ver posiciones en MT5
```
MetaTrader 5 → View → Positions

Debe ver:
  - BTCUSD, ETHUSD, EURUSD, etc. (varios símbolos)
  - Columna "Time" con timestamp reciente
  - Columna "Profit" con valores negativos o positivos

Si ve varias posiciones → ✅ BOT EJECUTANDO
Si ve 0 posiciones → ❌ REVISAR BOT STATUS
```

---

## Pregunta 5: "¿Qué tan seguro es el riesgo?"

### Métrica 1: Total Exposure
```
UI dashboard → Exposure gauge

Buscar: "X.XX% / 15.0%"

Interpretación:
  < 5%   = ✅ MUY SEGURO
  5-10%  = ✅ SEGURO
  10-15% = ⚠️ ALERTA AMARILLA
  > 15%  = ❌ ALERTA ROJA

Ejemplo: "0.24% / 15%" = ✅ Muy seguro
```

### Métrica 2: Verificar Daily Loss
```
python -c "
from app.core.database import get_database_manager

db = get_database_manager()
trades = db.get_trades(days=1)  # Trades del último día

pnl = sum(t.get('pnl', 0) for t in trades if isinstance(t, dict))
print(f'Daily P&L: ${pnl:.2f}')

# Si capital es $4,000
daily_loss_pct = (abs(pnl) / 4000) * 100
print(f'Daily loss %: {daily_loss_pct:.2f}%')
print(f'Límite: 10.0%')
print(f'Status: {'✓ SAFE' if daily_loss_pct < 10 else '✗ ALERT'}')
"
```

### Métrica 3: Position Count
```
UI dashboard → Posiciones abiertas

Buscar: "N posiciones"

Interpretación:
  < 10   = ✅ SEGURO
  10-30  = ✅ NORMAL
  30-50  = ⚠️ ALERTA
  > 50   = ❌ ERROR (max es 50)

Actual: 9 posiciones = ✅ SEGURO
```

---

## Checklist de Diagnostico Rápido

### Para confirmar TODO funciona (5 minutos):

```bash
# 1. Verificar Backtest
[ ] ¿Existe data/backtest_results.json?
[ ] ¿Tiene campos: optimization_score, win_rate?

# 2. Verificar IA
[ ] ¿Logs muestran "AI SKIP" y "AI NEEDED"?
[ ] ¿Ratio ~60:40 (skip:needed)?

# 3. Verificar Risk
[ ] ¿Max positions = 50?
[ ] ¿Max daily loss = 10%?
[ ] ¿3 Profiles disponibles?

# 4. Verificar Ejecución
[ ] ¿Bot corriendo (python.exe en procesos)?
[ ] ¿Logs escribiendo cada 60 segundos?
[ ] ¿Posiciones abiertas en MT5?

# 5. Verificar Seguridad
[ ] ¿Exposure < 15%?
[ ] ¿Daily loss < 10%?
[ ] ¿Posiciones < 50?

Todos SI → ✅ SISTEMA 100% OPERATIVO
Alguno NO → ⚠️ REVISAR SECCIÓN CORRESPONDIENTE
```

---

## Troubleshooting Rápido

### "¿Por qué no veo trades nuevos?"
```
1. Verificar si bot está corriendo:
   Get-Process | findstr python
   
2. Verificar si hay spreads altos:
   Logs → buscar "spread"
   
3. Verificar si es fin de semana:
   Forex cierra viernes 22:00 GMT a domingo 22:00 GMT
   
4. Verificar limites de riesgo:
   Daily loss alcanzado? (max 10%)
   Exposure alcanzado? (max 15%)
   Posiciones alcanzado? (max 50)
```

### "¿Por qué IA está desactivada?"
```
Normal si:
• Señales técnicas son muy claras (STRONG_BUY/SELL)
• RSI está en extremos (< 35 o > 65)
• Trend es muy claro

No es normal si:
• 100% AI SKIP → Revisar AIGate lógica
• 0% AI NEEDED → Sin trades en zona gris
```

### "¿Por qué trading loop se detuvo?"
```
1. Error en MT5:
   Verificar connection: MT5 abierto?
   Verificar credentials en .env
   
2. Error en base de datos:
   Revisar data/trading_history.db
   Revisar permisos de escritura
   
3. Error en Gemini:
   Verificar API key en .env
   Verificar límite de requests
```

---

**Última actualización**: 2026-02-01
**Para preguntas**: Revisar VALIDATION_REPORT.md o SYSTEM_FLOW_DIAGRAM.md
