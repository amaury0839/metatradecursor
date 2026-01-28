# 🚀 AGGRESSIVE_SCALPING - Guía Completa

## Overview

Sistema de scalping agresivo optimizado para M15 con:
- **Scale-out parcial** en 3 niveles de TP
- **Trailing stop dinámico** basado en ATR
- **Hard closes agresivas** (RSI > 85 / < 15)
- **IA en modo BIAS_ONLY** (no bloquea trades)
- **Risk dinámico**: 0.75% por trade

---

## Parámetros Principales

### Risk Management
```
Risk per trade:         0.75%       (Escalado según equity)
Max concurrent pos:     6           (Límite de 50 es máximo)
Dynamic lot:            Enabled     (Auto-ajusta según equity)
```

### Stop Loss & Take Profit
```
SL:  ATR * 1.2          (1.2 ATR base)
TP:  ATR * 2.0          (Target inicial)
Trailing: ATR * 1.0     (Activa después +1R)
```

### Hard Closes (RSI)
```
Overbought: RSI > 85    (Aggressive, default es 80)
Oversold:   RSI < 15    (Aggressive, default es 20)
Reason: Cierres de emergencia en movimientos extremos
```

### IA Configuration
```
Mode:                   BIAS_ONLY
Blocks trades:          FALSE       (La IA NO bloquea)
Confidence threshold:   0.35        (Bajo, permite trades)
Role:                   Sesgo directional
```

---

## Scale-Out Parcial Explicado

### Estructura de 3 TPs

```
ENTRADA @ 1.0000
       ↓
       ├─ TP1: +0.5R @ 1.0050
       │  └─ Cierra 40% de posición
       │  └─ Bloquea 0.2R de ganancia
       │
       ├─ TP2: +1.0R @ 1.0100
       │  └─ Cierra 30% de posición (ahora 30% abierto)
       │  └─ Mueve SL a Breakeven (1.0000)
       │  └─ Riesgo = 0 (worst case)
       │
       └─ TP3: +1.5R + Trailing
          └─ Cierra 30% restante (pero con trailing)
          └─ Trailing activa en +1R
          └─ SL = High - ATR * 1.0 (dinámico)
```

### Ejemplo Real (EURUSD)

```
Entry:     1.0850
ATR:       0.0050

SL:        1.0850 - (0.0050 * 1.2) = 1.0794
TP:        1.0850 + (0.0050 * 2.0) = 1.0950

Posición:  1.0 lotes

--- Trade en progreso ---

Price: 1.0875 (+25 pips, +0.5R)
→ TP1 HIT: Cierra 0.4 lotes
→ Quedan 0.6 lotes en trade
→ P&L parcial: +$50 (asumiendo bid/ask)

Price: 1.0900 (+50 pips, +1.0R)
→ TP2 HIT: Cierra 0.18 lotes (30% de 0.6)
→ Quedan 0.42 lotes en trade
→ SL movido a 1.0850 (breakeven)
→ P&L: +$100, sin riesgo en trade abierto

Price: 1.0925 (trailing activo, +1.5R)
→ Trailing SL: 1.0925 - (0.0050 * 1.0) = 1.0875
→ Si precio cae a 1.0875 → Cierra automático 0.42 lotes
→ P&L final: +$150+ (dependiendo del cierre)

RESULTADO: 
- Tomamos ganancias en cada nivel TP
- Al nivel 2, convertimos a "free trade" (SL en BE)
- Al nivel 3, dejamos correr con trailing
```

---

## Trailing Stop Dinámico

### Cómo Funciona

```
Activación:
- Se activa automáticamente después de +1R de ganancia
- No es estático, se recalcula cada barra
- Distancia = ATR * 1.0 (1 ATR actual)

Ajuste Dinámico:
- Si precio sube (en BUY): SL sube automático
- Si precio baja: SL se mantiene (nunca baja)
- Efecto: "Atrapa" el máximo del movimiento

Ventaja:
- Protege ganancias sin capar upside
- Se adapta a volatilidad (ATR cambia)
- Ideal para scalping (rápidas ganancias)
```

### Ejemplo Trailing (continuación)

```
Price: 1.0925 (Trailing activado)
Trailing SL: 1.0925 - 0.005 = 1.0920  

Price: 1.0935 → Trailing SL: 1.0930  (SL sube)
Price: 1.0940 → Trailing SL: 1.0935  (SL sube)
Price: 1.0937 → Trailing SL: 1.0935  (SL no baja, queda igual)
Price: 1.0933 → CIERRE AUTOMÁTICO en 1.0935

Resultado: Cazamos el máximo (1.0940) - 0.005 = 1.0935 pips
           Mejor que cerrar en TP3 (1.0900 + 2.0 ATR = 1.0950)
```

---

## Hard Closes - RSI Extremo

### Cuándo Activa

```
COMPRA (Long):
- Si RSI > 85 → Cierre INMEDIATO
- Razón: Overbought extremo (movimiento demasiado lejos)
- Protege contra reversiones violentas

VENTA (Short):
- Si RSI < 15 → Cierre INMEDIATO
- Razón: Oversold extremo
- Protege contra rebotes bruscos
```

### Lógica

```
RSI > 85 no significa "no compres", significa:
- El movimiento alcista fue extremo
- El pullback será probablemente brusco
- Es mejor cerrar parciales y dejar trailing
- En lugar de mantener todo abierto

Ejemplo:
Price está muy arriba, todos están comprando
RSI = 88 (extremo)
→ Cierra posición por hard close RSI
→ Evita el pullback violento que suele venir
→ "Seguro contra reversal"
```

---

## IA Mode: BIAS_ONLY

### Qué Significa

```
BIAS_ONLY:
- IA genera SESGO direccional
- NO bloquea trades
- Simplemente orienta: +0.3 BUY / -0.2 SELL

NO BLOQUEA:
- Si la regla dice COMPRA
- Y IA tiene -0.5 sesgo VENTA
- IGUALMENTE se abre la compra
- IA es "opinión", no "veto"

Ventaja para Scalping:
- Permitimos trades rápidos sin aprobación IA
- IA añade sesgo pero no ralentiza
- M15 necesita reacción rápida
```

### Ejemplo Integración

```
Señal técnica: RSI cruzó 50 (momentum)
IA sesgo: +0.2 (ligeramente bullish)
Confianza: 0.45 (sobre threshold 0.35)

RESULTADO: TRADE EJECUTADO
Razón: Sesgo + técnica = alineados

---

Señal técnica: EMA cruzó (venta)
IA sesgo: +0.3 (bullish)
Confianza: 0.55

RESULTADO: TRADE EJECUTADO (VENTA)
Razón: IA es apenas opinión, técnica es acción
```

---

## Cómo Usar en Código

### 1. Activar Preset

```python
from app.trading.risk import get_trading_preset

# Cargar preset
preset = get_trading_preset("AGGRESSIVE_SCALPING")

# Aplicar a decisión
decision.risk_percent = preset["risk_percent"]
decision.max_positions = preset["max_concurrent_positions"]
```

### 2. Scale-Out

```python
from app.trading.aggressive_scalping_integration import get_aggressive_scalping_engine

engine = get_aggressive_scalping_engine()

# Chequear si hay TP hit
result = engine.check_scale_out(
    symbol="EURUSD",
    current_price=1.0875,
    entry_price=1.0850,
    entry_atr=0.0050,
    is_buy=True,
    position_size=1.0
)

if result["scale_out_hit"]:
    close_amount = result["close_amount"]  # 0.4 = 40%
    tp_level = result["tp_level"]         # 1 (TP1)
    print(f"Scale-out TP{tp_level}: cierra {close_amount*100:.0f}%")
    
    if result["move_sl_to_be"]:
        print("Mueve SL a breakeven")
```

### 3. Trailing Stop

```python
# Calcular nuevo SL con trailing
new_sl, is_active = engine.check_trailing_stop(
    symbol="EURUSD",
    current_price=1.0925,
    current_atr=0.0048,
    entry_price=1.0850,
    is_buy=True
)

if is_active and new_sl:
    print(f"Trailing SL: {new_sl:.5f}")
    # Usar nuevo_sl como SL en MT5
```

### 4. Hard Close RSI

```python
# Chequear hard close por RSI
should_close, reason = engine.check_hard_close_rsi(
    symbol="EURUSD",
    rsi=86.5,
    is_buy=True
)

if should_close:
    print(f"HARD CLOSE: {reason}")
    # Cerrar posición inmediatamente
```

---

## Parámetros Por Timeframe

### M15 (Scalping)
```
Perfecto para:          AGGRESSIVE_SCALPING
Risk:                   0.75% (agresivo)
Max positions:          6
Scale-out:              Sí (rápidas ganancias)
Trailing:               Sí (corto-plazo)
Recomendado:            ✅ Este preset
```

### H1 (Swing)
```
Perfecto para:          STANDARD
Risk:                   1.0%
Max positions:          3
Scale-out:              Sí (conservador)
Trailing:               Sí (ATR * 1.5)
Use: get_trading_preset("STANDARD")
```

### D (Position)
```
Perfecto para:          CONSERVATIVE
Risk:                   0.5%
Max positions:          2
Scale-out:              Sí (muy conservador)
Trailing:               Sí (ATR * 2.0)
Use: get_trading_preset("CONSERVATIVE")
```

---

## Monitoreo En Vivo

### Parámetros a Seguir

```
✓ Posición abierta:     % ganancia vs TP
✓ Profit realizados:    Total parcial + TP hits
✓ SL actual:            Mover a BE cuando TP2 hit
✓ Trailing SL:          Debe subir con precio
✓ RSI:                  Vigilar > 85 o < 15
✓ ATR:                  Cambios en volatilidad
```

### Ejemplo Dashboard

```
═══════════════════════════════════════════════════════════════
AGGRESSIVE_SCALPING - EURUSD (M15)
═══════════════════════════════════════════════════════════════

Entry:          1.0850      SL: 1.0794      TP: 1.0950
Current:        1.0922      Profit: +72 pips (+1.44R)

Scale-Out Status:
  TP1 (+0.5R):  ✅ CLOSED 40%        P&L: +$50
  TP2 (+1.0R):  ✅ CLOSED 30%        SL→BE: 1.0850
  TP3 (+1.5R):  ⏳ WAITING            SL: 1.0912 (trailing)

Risk Status:
  RSI:          72 (no extremo)       
  ATR:          48 pips (volatilidad normal)
  Remaining:    30% posición abierta

Trailing Info:
  Activated:    ✅ Yes (+1.44R > 1.0R)
  Highest:      1.0922
  Trail Dist:   48 pips (1 ATR)
  Current SL:   1.0874 (auto-updated)
═══════════════════════════════════════════════════════════════
```

---

## Resumen Rápido

| Feature | Valor | Beneficio |
|---------|-------|-----------|
| Risk | 0.75% | Agresivo pero controlado |
| Scale-Out | 3 TP | Bloquea ganancias en cada nivel |
| TP1 | +0.5R @ 40% | Ganancia "segura" rápida |
| TP2 | +1.0R @ 30% | SL→BE, "free trade" |
| TP3 | +1.5R + Trailing | "Dejamos correr" dinámicamente |
| Trailing | ATR * 1.0 | Adapta a volatilidad |
| Hard Close RSI | >85 / <15 | Protege de extremos |
| IA Mode | BIAS_ONLY | No bloquea, solo sesga |

---

## ✅ Checklist para Usar

- [ ] Cargar preset AGGRESSIVE_SCALPING
- [ ] Configurar risk_percent = 0.75
- [ ] Max positions = 6
- [ ] Activar trailing stop
- [ ] Activar hard closes RSI (85/15)
- [ ] IA en modo BIAS_ONLY (no bloquea)
- [ ] Monitorear TPs en cada nivel
- [ ] Vigilar RSI para hard closes
- [ ] Dejar trailing activo después +1R
- [ ] Resetear engine entre trades

---

**Status**: ✅ Listo para producción  
**Timeframe**: M15 (recomendado)  
**Modo**: Scalping agresivo  
**Versión**: 1.0
