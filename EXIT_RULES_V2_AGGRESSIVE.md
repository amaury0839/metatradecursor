# 🎯 REGLAS DE SALIDA MEJORADAS - VERSION 2

## ⚠️ CAMBIOS CRÍTICOS

Tu sistema anterior fue diseñado como "trend follower" → ahora es **scalping puro**.

### Antes ❌
- Esperaba a que la señal se invirtiera para cerrar
- Posiciones "forever hold" sin límite de tiempo
- Sin límite de pérdida

### Ahora ✅
- **Cierre independiente de la señal técnica**
- Gestión estricta de tiempo
- Stop loss automático

---

## 📋 NUEVAS REGLAS DE SALIDA

### 1️⃣ **PROFIT TARGET (R-Multiple)** ⭐ MÁXIMA PRIORIDAD

```
R = abs(entry - SL)

🚨 Si profit <= -1.0R → CIERRE TOTAL (stop loss)
💵 Si profit >= 1.0R → CIERRE PARCIAL 50%
💰 Si profit >= 1.5R → CIERRE TOTAL (¡ganancia!)
```

**Cambios respecto a v1:**
- ✅ Agregado stop loss automático (-1.0R)
- ✅ Bajados targets: 1.0R en lugar de 0.8R
- ✅ Full close en 1.5R en lugar de 1.2R
- ✅ Protege contra pérdidas de drawdown

---

### 2️⃣ **PROFIT RETRACE (Protección de Scalp)**

```
Si max_profit_visto = $100
Y profit_actual = $60
Y retroceso = 40% > threshold (35%)
→ CIERRE INMEDIATO
```

Previene que ganancias se evaporen.

---

### 3️⃣ **TIME LIMIT (⏱️ CRÍTICO PARA SCALPING)**

```
Si posición abierta > 60 minutos
→ CIERRE POR TIEMPO (aunque la señal siga válida)

El mercado ya no te está dando lo que querías.
```

**Cambios respecto a v1:**
- ✅ Bajado de 240 min a 60 min (4 velas M15)
- ✅ Ahora es más agresivo

---

### 4️⃣ **RSI EXTREME (Hard Close)**

```
BUY + RSI > 80 → CIERRE INMEDIATO (sobrecaliente)
SELL + RSI < 20 → CIERRE INMEDIATO (sobrevendido)
```

Sin excepciones, sin "esperar recovery".

---

### 5️⃣ **OPPOSITE SIGNAL**

```
Si señal técnica se invierte CON confidence >= 0.7
→ CIERRE
```

Cuando el análisis técnico cambió, no luchas contra la tendencia.

---

### 6️⃣ **TRAILING STOP (ATR)**

```
Si profit > 0:
  - BUY: SL = price - (1.0 × ATR)
  - SELL: SL = price + (1.0 × ATR)
  
Solo bloquea ganancias (nunca empeora SL)
```

---

## 🔧 CORRECCIONES TÉCNICAS

### Error 1: Volumen inválido en cierre parcial
**Problema:** Intentaba cerrar 0.795 lots pero el broker requiere mínimo específico.

**Solución:** 
```python
min_volume = symbol_info.volume_min
volume = round(volume / min_volume) * min_volume  # Redondear a múltiplo válido
```

### Error 2: Posiciones sin SL/TP
**Problema:** Algunas posiciones no tenían SL definido (SL=0), causaba crash en cálculo de R.

**Solución:**
```python
if entry_price == 0 or sl_price == 0:
    return False, None, None  # Skip si falta SL
```

### Error 3: IA deshabilitada
**Problema:** Weight de IA bajó a 0% porque confidence < 0.55.

**Situación actual:**
- Technical: 100% (confidence siempre > 0.55)
- AI: 0% (confidence usually < 0.55)
- Sentiment: 0%

Esto está **por diseño en BIAS_ONLY mode**, pero significa que el sistema es 100% técnico.

---

## ✅ ORDEN DE PRIORIDAD DE CIERRE

```
1. Profit target / Stop loss (-1R)       ← Si alcanza limit
2. Profit retrace (35%)                   ← Si pierde ganancia
3. RSI extreme (>80/<20)                  ← Si entra pánico
4. Opposite signal (confidence 0.7)       ← Si técnico cambia
5. Time limit (60 minutos)                ← Si lleva mucho tiempo
6. Trailing stop                          ← Si baja desde peak
```

Cada regla es **INDEPENDIENTE** de la señal técnica.

---

## 🚀 COMPORTAMIENTO ESPERADO

### Antes
```
Found 26 open positions
Position X: ... holding
Position Y: ... holding
Position Z: ... holding
...
(muchas en rojo, esperando forever)
```

### Ahora
```
Found 26 open positions
Position AUDNZD: Closing (partial 50%) - PROFIT TARGET 0.81R
Position CADCHF: Closing (full) - Opposite signal
Position LTCUSD: Closing (full) - TIME LIMIT 67 min
Position XRPUSD: Closing (full) - PROFIT TARGET 1.51R
...
(activo, cerrando ganancias y limitando pérdidas)
```

---

## 📊 PARÁMETROS RECOMENDADOS

Para **AGGRESSIVE_SCALPING**:
- Profit target partial: **1.0R**
- Profit target full: **1.5R**
- Stop loss: **-1.0R**
- Time limit: **60 minutos**
- Profit retrace threshold: **35%**
- Trailing ATR multiple: **1.0**

---

## 🧪 PRÓXIMO TEST

Reinicia el bot y observa:

```
✅ ¿Se cierran posiciones por profit target?
✅ ¿Se cierran por tiempo después de 60 min?
✅ ¿Se respetan volúmenes mínimos en cierre parcial?
✅ ¿Se ejecuta cierre parcial en 1.0R y total en 1.5R?
✅ ¿Se registran los cierres en logs?
```

---

**Estado**: 🔴 **LISTO PARA TESTING**
