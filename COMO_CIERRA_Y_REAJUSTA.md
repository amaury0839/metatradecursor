# 🤖 ¿CÓMO CIERRA POSICIONES Y SE REAJUSTA CON IA?

## Resumen Ejecutivo

El bot ejecuta **2 ciclos cada 60 segundos**:

1. **REVISIÓN DE POSICIONES ABIERTAS** (lines 80-210 en trading_loop.py)
   - Evalúa cada posición con 6 reglas de cierre
   - Si alguna regla se cumple → **CIERRA**
   
2. **BÚSQUEDA DE NUEVAS OPORTUNIDADES** (lines 260-400 en trading_loop.py)
   - Analiza 40 símbolos buscando señales
   - Consulta IA si la señal es débil
   - Abre nuevas posiciones si pasa todas las validaciones

---

## 🔴 CIERRE DE POSICIONES - 6 REGLAS EVALUADAS EN ORDEN

### Localización: `app/trading/position_manager.py` líneas 580-700 en método `review_position_full()`

```
═══════════════════════════════════════════════════════════════════
CICLO DE REVISIÓN (cada 60 segundos por cada posición abierta)
═══════════════════════════════════════════════════════════════════

Posición ABIERTA: EURUSD BUY 1.0 lot
├─ Entry: 1.1800 hace 15 min
├─ Actual: 1.1785 (P&L = -$150)
├─ SL: 1.1750
└─ TP: 1.1900

EVALUACIÓN (en orden):
┌──────────────────────────────────────────────────────────────────┐
│ REGLA 1: PROFIT TARGET                                           │
│ ─────────────────────────────────────────────────────────────    │
│ ¿Llegó a TP (1.1900)?                          ❌ NO (actual=1.1785)  │
│ → Continúa evaluando                                              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ REGLA 2: PROFIT RETRACE PROTECTION                               │
│ ─────────────────────────────────────────────────────────────    │
│ ¿Estuvo en ganancia antes?                     ❌ NO (siempre -$150) │
│ → Continúa evaluando                                              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ REGLA 3: RSI EXTREME (Sin esperanza)                             │
│ ─────────────────────────────────────────────────────────────    │
│ Posición BUY, ¿RSI > 80?                       ❌ NO (RSI = 42)   │
│ → Continúa evaluando                                              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ ⭐ REGLA 4: OPPOSITE SIGNAL (CAMBIO DE SEÑAL)                   │
│ ─────────────────────────────────────────────────────────────    │
│ Posición es BUY                                                  │
│ Nueva análisis dice: SELL con confianza 0.78                     │
│ ¿Confianza >= 0.70?                            ✅ SÍ (0.78 > 0.70) │
│                                                                   │
│ 🔴 CIERRE INMEDIATO SIN IMPORTAR P&L                             │
│    Razón: "Opposite signal: SELL (confidence=0.78)"              │
│    Log: 🔵 EURUSD T123456: CLOSING - Opposite signal...          │
│                                                                   │
│ → SALTA a ejecución de cierre (no evalúa reglas 5,6)             │
└──────────────────────────────────────────────────────────────────┘

SI HUBIESE PASADO REGLA 4:

┌──────────────────────────────────────────────────────────────────┐
│ REGLA 5: TIME LIMIT (máx 60 minutos)                             │
│ ─────────────────────────────────────────────────────────────    │
│ Posición abierta hace: 15 min                                     │
│ ¿> 60 min?                                     ❌ NO              │
│ → Continúa evaluando                                              │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ REGLA 6: TRAILING STOP (solo si en ganancia)                     │
│ ─────────────────────────────────────────────────────────────    │
│ P&L = -$150 (en pérdida)                                          │
│ ¿En ganancia?                                  ❌ NO              │
│ → NO actualiza SL                                                 │
│ → MANTIENE posición                                               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 LAS 6 REGLAS EN DETALLE

### ✅ REGLA 1: PROFIT TARGET - Cierre en 1.5R

**Cuándo se cierra:**
- Posición llega a Take Profit (TP)
- También se considera cierre parcial en 1.0R (50% de volumen)

**Código:**
```python
if current_price >= tp_price:  # Para BUY
    logger.info("💰 EURUSD: PROFIT TARGET - Closing full position")
    return {'should_close': True, 'reason': 'Profit target reached'}
```

---

### ✅ REGLA 2: PROFIT RETRACE PROTECTION - Protege ganancias

**Cuándo se cierra:**
- Posición estuvo en ganancia (e.g., +$500)
- Ahora retrocedió 35% de esa ganancia (baja a +$325)
- Se cierra parcial (50% del volumen) para proteger profits

**Código:**
```python
if max_profit > 0:
    retrace_threshold = max_profit * 0.35
    current_drawdown = max_profit - current_profit
    
    if current_drawdown >= retrace_threshold:
        logger.info("🟡 EURUSD: PROFIT RETRACE - Closing 50%")
        return {'should_close': True, 'close_percent': 0.5}
```

---

### ✅ REGLA 3: RSI EXTREME - Mercado en extremo

**Cuándo se cierra:**
- Posición BUY pero RSI > 80 (sobrecomprado) ✅ Cierra
- Posición SELL pero RSI < 20 (sobrevendido) ✅ Cierra

**Por qué:** Si está en extremo, mejor salir que esperar reversión

**Código:**
```python
if position_type == "BUY" and rsi >= 80 and current_profit > 0:
    logger.info("📈 EURUSD: RSI_EXTREME (>80) - Closing to lock profit")
    return {'should_close': True, 'reason': 'RSI extreme (overbought)'}
```

---

### ⭐ REGLA 4: OPPOSITE SIGNAL - CAMBIO DE TENDENCIA (TU PREGUNTA!)

**Cuándo se cierra:**
- Posición es **BUY** pero nueva análisis dice **SELL** con confianza ≥ 0.70
- Posición es **SELL** pero nueva análisis dice **BUY** con confianza ≥ 0.70

**IMPORTANTE:** Se cierra **SIN IMPORTAR SI ESTÁ EN GANANCIA O PÉRDIDA**

**Razón:** No pelear contra la tendencia. Si el mercado cambió, mejor salir.

**Código en `position_manager.py` líneas 182-213:**
```python
def should_close_on_opposite_signal(
    self,
    position_type: str,           # "BUY" o "SELL"
    current_signal: str,          # Nueva señal: "BUY", "SELL", "HOLD"
    confidence: float,            # 0.78
    min_confidence_to_reverse: float = 0.7  # Umbral
) -> Tuple[bool, Optional[str]]:
    """
    BUY position + SELL signal with high confidence → CLOSE
    SELL position + BUY signal with high confidence → CLOSE
    """
    
    # Caso 1: Estamos en BUY pero ahora dice SELL
    if position_type == "BUY" and current_signal == "SELL":
        if confidence >= min_confidence_to_reverse:
            return True, f"Opposite signal: SELL (confidence={confidence:.2f})"
    
    # Caso 2: Estamos en SELL pero ahora dice BUY
    if position_type == "SELL" and current_signal == "BUY":
        if confidence >= min_confidence_to_reverse:
            return True, f"Opposite signal: BUY (confidence={confidence:.2f})"
    
    return False, None
```

**Ejemplo en logs:**
```
✅ EURUSD T1000001: Previous signal = BUY (pos abierto hace 10 min)
🔄 New analysis: SELL signal, confidence = 0.78
🔵 EURUSD T1000001: CLOSING - Opposite signal: SELL (confidence=0.78)
✅ Closed 1.0 lot at 1.1785 (P&L = -$150)
```

---

### ✅ REGLA 5: TIME LIMIT - Máximo tiempo sin ganancia

**Cuándo se cierra:**
- Posición abierta más de 60 minutos (4 velas M15)
- Sin importar P&L

**Código:**
```python
def should_close_on_time_limit(
    self,
    position,
    max_hold_minutes: int = 60
) -> Tuple[bool, Optional[str]]:
    
    time_open = datetime.fromisoformat(position['time'])
    time_elapsed = (datetime.now() - time_open).total_seconds() / 60
    
    if time_elapsed > max_hold_minutes:
        return True, f"Time limit exceeded ({time_elapsed:.0f}min > {max_hold_minutes}min)"
```

**Log ejemplo:**
```
⏱️  GBPUSD T1000002: CLOSING - Time limit exceeded (65min > 60min)
```

---

### ✅ REGLA 6: TRAILING STOP - Protege con ATR

**Cuándo se ejecuta:**
- Si posición está **EN GANANCIA**
- Actualiza Stop Loss dinámicamente usando ATR

**Por qué:** A medida que precio sube, sube el SL automáticamente

**Código:**
```python
if current_profit > 0 and atr > 0:  # Solo si en ganancia
    new_sl = current_price - (atr * 1.0)  # SL = precio actual - 1*ATR
    
    if new_sl > current_sl:  # Solo actualiza si sube
        logger.info(f"📈 {symbol} trailing SL: {current_sl:.5f} → {new_sl:.5f}")
        return {'update_sl': new_sl}
```

**Log ejemplo:**
```
📈 EURUSD trailing SL: 1.1765 → 1.1780
```

---

## 🧠 REAJUSTE CON IA - PUERTA DE IA (AI GATE)

### Localización: `app/trading/trading_loop.py` líneas 260-310

```
═══════════════════════════════════════════════════════════════════
BÚSQUEDA DE NUEVAS OPORTUNIDADES (cada 60 segundos)
═══════════════════════════════════════════════════════════════════

Para cada símbolo (40 símbolos analizados):

PASO 1: Análisis técnico SIN IA (rápido)
  ├─ RSI, EMA, ATR
  ├─ Genera señal: BUY, SELL, HOLD
  └─ Confianza técnica: 0.75 si BUY/SELL, 0.0 si HOLD

PASO 2: PUERTA DE IA (AI GATE) - DECISIÓN AUTOMÁTICA
  │
  ├─→ ¿Señal técnica es FUERTE?
  │   (e.g., RSI extremo + EMA alineada + tendencia clara)
  │
  │   ✅ SÍ (FUERTE)
  │   └─→ SALTAR IA (PATH B: AI_SKIPPED)
  │       └─→ Usar análisis técnico directamente
  │       └─→ Log: ⚡ EURUSD | GATE_DECISION: AI_SKIPPED
  │
  │   ❌ NO (DÉBIL/AMBIGUA)
  │   └─→ CONSULTAR IA (PATH A: AI_CALLED)
  │       └─→ Reanalizar con AI enabled
  │       └─→ IA añade: sentimiento, noticias, ML
  │       └─→ Log: 🧠 EURUSD | GATE_DECISION: AI_CALLED
  │
  └─→ Ambos paths generan decisión final


PASO 3: VALIDACIÓN DE EJECUCIÓN
  └─→ ¿Confianza >= umbral (0.65)?
      └─→ ¿Cuenta tiene capital suficiente?
          └─→ ¿Portfolio no está lleno (< 40 posiciones)?
              └─→ ✅ ABRIR NUEVA POSICIÓN
```

---

## 📋 EJEMPLO COMPLETO: CICLO DE 60 SEGUNDOS

```
═══════════════════════════════════════════════════════════════════
CICLO #1234 - Timestamp: 2026-01-31 18:05:00
═══════════════════════════════════════════════════════════════════

🔴 FASE 1: REVISIÓN DE POSICIONES ABIERTAS
───────────────────────────────────────────────────────────────────

Posición 1: EURUSD BUY 1.0 lot (abierto hace 45 min)
  ├─ Entry: 1.1800, Actual: 1.1785 (P&L = -$150)
  ├─ Evaluando: REGLA 1, 2, 3... → REGLA 4
  ├─ Nueva señal: SELL (conf=0.78)
  └─ ✅ CIERRE DETECTADO
     └─ Log: 🔵 EURUSD T1000001: CLOSING - Opposite signal: SELL (conf=0.78)
     └─ Ejecuta: close_position(ticket=1000001)
     └─ Resultado: Posición cerrada a 1.1785

Posición 2: GBPUSD SELL 0.5 lot (abierto hace 65 min)
  ├─ Entry: 1.2650, Actual: 1.2645 (P&L = +$25)
  ├─ Evaluando: REGLA 1, 2, 3, 4... → REGLA 5
  ├─ Tiempo abierto: 65 min > 60 min
  └─ ✅ CIERRE POR TIEMPO LIMIT
     └─ Log: ⏱️  GBPUSD T1000002: CLOSING - Time limit exceeded
     └─ Ejecuta: close_position(ticket=1000002)
     └─ Resultado: Posición cerrada a 1.2645

Posición 3: AUDUSD BUY 0.2 lot (abierto hace 20 min)
  ├─ Entry: 0.6650, Actual: 0.6668 (P&L = +$36)
  ├─ Evaluando: REGLA 1, 2, 3, 4, 5
  ├─ Todas las reglas: NO
  ├─ REGLA 6 (Trailing Stop)
  │  ├─ En ganancia: ✅ SÍ
  │  ├─ ATR = 0.0012
  │  ├─ SL antiguo: 0.6632
  │  ├─ SL nuevo: 0.6656 (0.6668 - 0.0012)
  │  └─ ✅ ACTUALIZAR SL
  └─ Log: 📈 AUDUSD trailing SL: 0.6632 → 0.6656

═══════════════════════════════════════════════════════════════════
Resultado: Cerradas 2 posiciones, actualizado 1 SL
═══════════════════════════════════════════════════════════════════

🟢 FASE 2: BÚSQUEDA DE NUEVAS OPORTUNIDADES
───────────────────────────────────────────────────────────────────

Portfolio status:
  ├─ Posiciones antes: 8
  ├─ Cierres esta ciclo: 2
  ├─ Posiciones ahora: 6
  ├─ Capacidad máx: 40
  ├─ % Utilización: 15% (slot disponible: ✅ SÍ)
  └─ Proceder a buscar nuevas oportunidades

Analizando símbolo #1: EURUSD
  ├─ Análisis técnico (SIN IA):
  │  ├─ RSI: 58 (neutro)
  │  ├─ EMA: distancia 0.0003 (normal)
  │  ├─ ATR: 0.0006
  │  └─ Señal: SELL (confianza técnica: 0.75)
  │
  ├─ PUERTA DE IA - Decisión:
  │  ├─ ¿Señal fuerte? 
  │  │  └─ RSI neutral + EMA normal = NO es fuerte
  │  │
  │  └─→ CONSULTAR IA (AI_CALLED)
  │     ├─ Log: 🧠 EURUSD | GATE_DECISION: AI_CALLED (RSI neutral)
  │     ├─ Análisis IA:
  │     │  ├─ Sentimiento: 0.62 (levemente bullish)
  │     │  ├─ Noticias: -0.1 (sin impacto)
  │     │  ├─ Modelo ML: BUY (conf=0.55)
  │     │  └─ Resultado: Cambiar a BUY
  │     │
  │     └─ Decision final: BUY (de IA)
  │
  ├─ Validación:
  │  ├─ Confianza >= 0.65? ✅ SÍ (0.75)
  │  ├─ Capital disponible? ✅ SÍ ($50,000)
  │  ├─ Portfolio no lleno? ✅ SÍ (6/40)
  │  └─ SL/TP calcs:
  │     ├─ Entry: 1.1785
  │     ├─ SL: 1.1765 (0.0020 = 20 pips)
  │     ├─ TP: 1.1870 (85 pips, 4.25R)
  │     └─ Volumen: 0.5 lot
  │
  └─ ✅ EJECUTAR ORDEN
     ├─ Log: ✅ EURUSD: BUY signal, confidence=0.75
     ├─ Ejecuta: buy(symbol="EURUSD", volume=0.5, entry=1.1785, sl=1.1765, tp=1.1870)
     └─ Resultado: Orden abierta - Ticket #1000010

Analizando símbolo #2: GBPUSD
  ├─ Análisis técnico:
  │  ├─ RSI: 32 (cercano a sobrevendido)
  │  ├─ EMA: distancia 0.0008 (separadas)
  │  ├─ ATR: 0.0008
  │  └─ Señal: BUY (confianza técnica: 0.75)
  │
  ├─ PUERTA DE IA - Decisión:
  │  ├─ ¿Señal fuerte?
  │  │  └─ RSI bajo + EMA separadas + ATR alto = SÍ es fuerte
  │  │
  │  └─→ SALTAR IA (AI_SKIPPED)
  │     └─ Log: ⚡ GBPUSD | GATE_DECISION: AI_SKIPPED (Strong technical)
  │
  ├─ Validación:
  │  ├─ Confianza >= 0.65? ✅ SÍ (0.75)
  │  ├─ Capital disponible? ✅ SÍ ($49,500)
  │  ├─ Portfolio no lleno? ✅ SÍ (7/40)
  │  └─ SL/TP calcs: SL=1.2635, TP=1.2750
  │
  └─ ✅ EJECUTAR ORDEN
     ├─ Log: ✅ GBPUSD: BUY signal, confidence=0.75
     └─ Resultado: Orden abierta - Ticket #1000011

[... continúa con 38 símbolos restantes ...]

═══════════════════════════════════════════════════════════════════
Resultado final: Abiertas 2 nuevas posiciones
═══════════════════════════════════════════════════════════════════

🎯 ESTADO DEL BOT
───────────────────────────────────────────────────────────────────
Ciclo inicio:  8 posiciones
Cierres:      -2 (señal opuesta + tiempo limit)
Aperturas:    +2 (EURUSD + GBPUSD)
Ciclo fin:     8 posiciones

Logs generados:
  📊 4 decisiones de IA (EURUSD consultó, GBPUSD saltó)
  🔵 2 cierres ejecutados
  ✅ 2 aperturas ejecutadas
  📈 1 actualización de trailing stop

⏰ Próximo ciclo: +60 segundos (18:06:00)

```

---

## 📌 RESUMEN: CÓMO FUNCIONA

### **1. Cierre por Señal Opuesta** (Tu pregunta principal)
- Cada ciclo (60 seg), evalúa cada posición abierta
- Calcula nueva señal técnica (RSI, EMA, ATR)
- Si señal cambió a opuesta + confianza ≥ 0.70 → **CIERRA**
- Se cierra sin importar ganancia o pérdida

### **2. Reajuste con IA**
- Si signal técnica es débil → **Consulta IA**
  - IA añade: sentimiento, noticias web, modelos ML
  - Resultado puede cambiar la decisión
- Si señal técnica es fuerte → **Salta IA** (más rápido)
  - Usa análisis técnico directo
  - Ahorra tiempo de computación

### **3. Ciclo Continuo**
```
Cada 60 segundos:
├─→ Revisar posiciones abiertas (6 reglas de cierre)
├─→ Buscar nuevas oportunidades (40 símbolos)
│   ├─→ Análisis técnico SIN IA
│   ├─→ PUERTA DE IA (decide si consultar IA)
│   └─→ Ejecutar si pasa validaciones
└─→ Repeat
```

---

## 🎯 LOGS QUE VAS A VER

```
🔵 EURUSD T1000001: CLOSING - Opposite signal: SELL (confidence=0.78)
⏱️  GBPUSD T1000002: CLOSING - Time limit exceeded (65min > 60min)
🧠 AUDCAD | GATE_DECISION: AI_CALLED (RSI neutral)
⚡ NZDUSD | GATE_DECISION: AI_SKIPPED (Strong technical)
✅ EURUSD: BUY signal, confidence=0.75
📈 AUDUSD trailing SL: 0.6632 → 0.6656
```

---

## ✅ VERIFICACIÓN

Ambas funciones están **100% implementadas y activas**:
- ✅ `position_manager.py:review_position_full()` - Revisa posiciones
- ✅ `position_manager.py:should_close_on_opposite_signal()` - Cierra por señal opuesta
- ✅ `trading_loop.py:should_call_ai()` - Puerta de IA
- ✅ `trading_loop.py:main_trading_loop()` - Ciclo principal

Los logs que ves confirman que todo está funcionando en tiempo real.

