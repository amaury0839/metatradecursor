# ❌ El Bot No Hace Trades - Solución

## Problema Encontrado

Tu `.env` tenía `TRADING_MODE=DEMO` pero el código espera `MODE=LIVE` o `MODE=PAPER`.

## ✅ Solución Aplicada

```
ANTES: TRADING_MODE=DEMO        ❌ Inválido
AHORA: MODE=LIVE               ✅ Correcto
```

## 🎯 Para que el Bot Haga Trades

Necesita **TODO ESTO**:

### 1. **Modo de Trading Activado**
```env
MODE=LIVE           # ← Haz trading REAL (con dinero)
# O
MODE=PAPER          # ← Haz trading SIMULADO (sin riesgo)
```

### 2. **Kill Switch Desactivado**
El bot tiene un "kill switch" para emergencias:
- Si está **ACTIVO** → Bot pausa trades
- Si está **INACTIVO** → Bot hace trades

**Status actual:**
```python
from app.core.state import get_state_manager
state = get_state_manager()

# Ver estado
print(state.is_kill_switch_active())  # True = pausa, False = funciona

# Si está activo, desactivar:
state.deactivate_kill_switch()
```

### 3. **MT5 Conectado** (para datos en vivo)
```python
from app.trading.mt5_client import get_mt5_client
mt5 = get_mt5_client()

# Ver estado
print(mt5.is_connected())  # True = conectado, False = desconectado

# Si no está conectado:
mt5.connect()
```

**Importante:** Si MT5 no está disponible, el bot usa **señales técnicas** sin datos en vivo.

### 4. **Estrategia Generando Señales**
El bot necesita ver una **señal de compra/venta**:

```python
from app.trading.strategy import get_strategy
from app.core.config import get_config

config = get_config()
strategy = get_strategy()

# Ver si hay señales
symbol = config.trading.default_symbols[0]  # Por ej: EURUSD
signal, indicators, error = strategy.get_signal(symbol, "M15")

print(f"Signal: {signal}")  # BUY, SELL, o HOLD
```

**Las señales se basan en:**
- EMA Fast vs EMA Slow (tendencia)
- RSI (sobreventa/sobrecompra)
- ATR (volatilidad)

### 5. **Risk Management Permitiendo Trades**
El bot verifica riesgos antes de cada orden:

```python
from app.trading.risk import get_risk_manager

risk = get_risk_manager()
symbol = "EURUSD"

# Verificar si puede hacer un BUY
risk_ok, failures = risk.check_all_risk_conditions(
    symbol, "BUY", volume=0.01
)

if risk_ok:
    print("✅ Risk OK - Puede hacer trade")
else:
    print(f"❌ Risk check failed: {failures}")
```

**Razones comunes de rechazo:**
- Muy muchas posiciones abiertas
- Pérdida diaria muy grande
- Drawdown máximo excedido
- Tamaño de orden muy grande

### 6. **Gemini API Disponible** (OPCIONAL para AI)
Si quieres decisiones con IA:

```env
GEMINI_API_KEY=tu-clave-aqui
```

Sin esto, el bot usa **solo análisis técnico** (funciona igual).

## 📊 Checklist de Diagnóstico

Corre este script para verificar TODO:

```bash
python diagnose_trading.py
```

Verifica:
- ✅ Modo de trading (LIVE/PAPER)
- ✅ Kill switch (activo/inactivo)
- ✅ MT5 conectado
- ✅ Señales técnicas generadas
- ✅ Risk management OK
- ✅ Decision engine activo
- ✅ Execution manager listo

## 🚀 Pasos para Empezar a Hacer Trades

### Paso 1: Verificar Configuración
```bash
python diagnose_trading.py
```

### Paso 2: Si hay problemas, corregir
```env
MODE=LIVE                    # ← Activar modo trading
POLLING_INTERVAL_SECONDS=30  # ← Verificar cada 30 segundos
```

### Paso 3: Asegurar Kill Switch INACTIVO
```python
from app.core.state import get_state_manager
state = get_state_manager()
state.deactivate_kill_switch()  # Necesario si estaba paused
```

### Paso 4: Conectar MT5
```bash
# 1. Abrir MetaTrader 5
# 2. En otra terminal:
python
>>> from app.trading.mt5_client import get_mt5_client
>>> mt5 = get_mt5_client()
>>> mt5.connect()  # Debería retornar True
```

### Paso 5: Iniciar el Bot
```bash
python run_local_bot.py
```

### Paso 6: Monitorear Trades
- **Opción A:** Dashboard UI (http://localhost:8501)
- **Opción B:** API endpoint (http://localhost:8000/status/trading)
- **Opción C:** Logs (logs/trading_bot.log)

## 📈 Modos de Operación

### LIVE Mode (Real Trading)
```env
MODE=LIVE
```
- ✅ Hace trades REALES
- ✅ Usa dinero de tu cuenta
- ⚠️ Riesgo real de pérdida
- 🔒 Requiere verificar todo 2 veces

### PAPER Mode (Simulated Trading)
```env
MODE=PAPER
```
- ✅ Simula trades sin enviar a MT5
- ✅ Sin riesgo real
- ✅ Bueno para testing
- ❌ No es trading real

## 🔍 Debugging: ¿Por qué NO hace trades?

| Síntoma | Causa | Solución |
|---------|-------|----------|
| Bot corre pero sin trades | Kill switch activo | `state.deactivate_kill_switch()` |
| Error `MODE must be 'PAPER' or 'LIVE'` | Mal formato en .env | Cambiar `TRADING_MODE=DEMO` → `MODE=LIVE` |
| "MT5 not connected" en logs | MT5 no está corriendo | Abrir MetaTrader 5 |
| "No signal generated" | Mercado sin setup | Esperar setup técnico o cambiar símbolo |
| "Risk check failed" | Demasiado riesgo | Reducir `DEFAULT_RISK_PER_TRADE` |
| "Too many positions" | Posiciones abiertas | Cerrar alguna o subir `DEFAULT_MAX_POSITIONS` |
| Gemini error | No hay API key | Agregar `GEMINI_API_KEY` o dejar vacío |

## 📄 Archivos Importantes

- **[.env](.env)** ← Configuración (MODE, MT5, Gemini)
- **[app/main.py](app/main.py)** ← Loop principal de trading
- **[app/trading/strategy.py](app/trading/strategy.py)** ← Señales técnicas
- **[app/trading/execution.py](app/trading/execution.py)** ← Ejecutar órdenes
- **[app/trading/risk.py](app/trading/risk.py)** ← Validar riesgos
- **[app/core/state.py](app/core/state.py)** ← Estado y kill switch

## 💡 Tips Avanzados

### Monitoreo en Tiempo Real
```python
from app.core.state import get_state_manager
from app.trading.portfolio import get_portfolio_manager

state = get_state_manager()
portfolio = get_portfolio_manager()

print(f"Equity: ${state.current_equity}")
print(f"Positions: {portfolio.get_open_positions()}")
print(f"Last decision: {state.get_last_decision()}")
```

### Ajustar Riesgos
```env
DEFAULT_RISK_PER_TRADE=0.5        # 0.5% por trade
DEFAULT_MAX_DAILY_LOSS=2.0        # 2% máximo/día
DEFAULT_MAX_DRAWDOWN=8.0          # 8% máximo drawdown
DEFAULT_MAX_POSITIONS=2           # 2 posiciones simultáneas
```

### Ver Decisiones Guardadas
```python
from app.core.state import get_state_manager
state = get_state_manager()

# Todas las decisiones
decisions = state.get_decision_history(limit=10)
for d in decisions:
    print(f"{d.symbol}: {d.action} (confidence: {d.confidence})")
```

## ❓ FAQ

**P: ¿Qué pasa si dejo el bot corriendo?**
R: Verifica cada 30 segundos (configurable). Si hay señal + riesgo OK → Hace trade.

**P: ¿Cuál es mejor, LIVE o PAPER?**
R: PAPER para testing/validation. LIVE para trading real. Ambos funcionan igual.

**P: ¿Necesito Gemini API Key?**
R: NO. El bot funciona con análisis técnico puro. Gemini solo mejora decisiones.

**P: ¿Por qué a veces no hace trades?**
R: Probablemente risk check rechazó la orden. Corre `diagnose_trading.py` para ver.

**P: ¿Cuánto tarda en hacer un trade?**
R: Máximo 30 segundos (el polling interval). Puede ser más rápido si hay signal.

---

**Status:** ✅ Bot listo para hacer trades después de cambiar TRADING_MODE → MODE

**Próximo paso:** Corre `diagnose_trading.py` para verificar que todo está bien.
