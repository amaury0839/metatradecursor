HARD CLOSE RULES - IMPLEMENTATION COMPLETE
===============================================================================

PRIORIDAD 1: ELIMINAR "HOLDING FOR RECOVERY" ✅
===============================================================================

Reemplazado por 3 REGLAS DURAS sin excepciones:

REGLA A - RSI EXTREMO SIN EXCEPCIONES
--------------------------------------
Función: position_manager.should_close_on_rsi_extreme()

BUY + RSI > 80.0 → CERRAR INMEDIATAMENTE
SELL + RSI < 20.0 → CERRAR INMEDIATAMENTE

❌ NO hay excepciones por "making HH/LL"
❌ NO hay "holding for recovery"
✅ Cierre duro sin importar P&L

Ejemplo en logs: "🔴 HARD CLOSE: RSI 82.3 > 80 (overbought) - BUY position closed immediately"


REGLA B - TIEMPO MÁXIMO EN TRADE (TTL)
---------------------------------------
Función: position_manager.should_close_on_candle_ttl()

Parámetros:
- Timeframe: M15 (15 minutos por vela)
- Max candles: 6 velas sin movimiento favorable
- Duración máxima: ~90 minutos (6 × 15 min)

Lógica:
1. Si pasan 6 velas Y la posición NO está ganando → CERRAR
2. Ganancia mínima: 0.05% a favor para mantener
3. CIERRE SIN EXCEPCIONES

Ejemplo:
- Abre BUY a las 14:00
- 14:15 (vela 1): sin movimiento
- 14:30 (vela 2): sin movimiento
- ...
- 15:30 (vela 6): sin movimiento → 🔴 CLOSE

Mensaje en logs: "🔴 HARD CLOSE: 6 candles (M15) without profit - close now"


REGLA C - INVALIDACIÓN TÉCNICA (EMA CROSS)
-------------------------------------------
Función: position_manager.should_close_on_ema_invalidation()

BUY POSITION:
- Debe cumplirse: EMA_fast > EMA_slow
- Si EMA_fast cruza DEBAJO de EMA_slow → CERRAR INMEDIATAMENTE
- Significa: Tendencia alcista se rompió

SELL POSITION:
- Debe cumplirse: EMA_fast < EMA_slow  
- Si EMA_fast cruza ARRIBA de EMA_slow → CERRAR INMEDIATAMENTE
- Significa: Tendencia bajista se rompió

Mensaje en logs: "🔴 HARD CLOSE: EMA_fast (1.0950) < EMA_slow (1.0960) - BUY invalidated"


PRIORIDAD 3: RANKING DE POSICIONES PARA CIERRE ✅
===============================================================================

Función: position_manager.rank_positions_for_closing()

Antes de buscar NUEVOS trades → Cierra las PEORES posiciones primero

Criterios de Ranking (composite score):
1. P&L (60% weight) - Pérdidas peores primero
2. Tiempo abierto (25% weight) - Posiciones viejas primero
3. Distancia a SL (15% weight) - Cerca del stop primero

Fórmula:
score = (pnl × 0.60) - (minutes_held × 0.25) + (distance_to_sl × 0.15)

Menor score = Posición peor = Cierra primero

Flujo:
1. Portfolio está al 80%+ de max_positions
2. System ejecuta rank_positions_for_closing()
3. Identifica las 2 peores posiciones
4. Las cierra ANTES de buscar nuevos trades
5. Libera slots para nuevas oportunidades

Ejemplo en logs:
```
⚠️  Approaching max positions (38/50)
🎯 Attempting to close 2 worst positions first...
   Closing worst #1: EURUSD (P&L=$-12.50)
   Closing worst #2: GBPUSD (P&L=$-8.75)
```


CAMBIOS EN CÓDIGO
===============================================================================

1. app/trading/position_manager.py
   ✅ Modified: should_close_on_rsi_extreme() - Sin excepciones ahora
   ✅ Added: should_close_on_candle_ttl() - REGLA B
   ✅ Added: should_close_on_ema_invalidation() - REGLA C
   ✅ Added: rank_positions_for_closing() - PRIORIDAD 3

2. app/main.py - main_trading_loop()
   ✅ Lines 195-255: Reemplacé lógica de RSI
   ✅ Agregué check de TTL
   ✅ Agregué check de EMA invalidation
   ✅ Eliminé: "holding for recovery" completamente
   ✅ Lines 327-351: Agregué ranking de posiciones antes de nuevos trades


EJECUCIÓN DEL FLUJO
===============================================================================

STEP 1: POSICIONES ABIERTAS
  └─ Para cada posición abierta:
     ├─ Check REGLA A (RSI extremo) → CIERRE DURO
     ├─ Check REGLA B (TTL) → CIERRE DURO
     ├─ Check REGLA C (EMA invalidation) → CIERRE DURO
     ├─ Check tiempo máximo (4 horas)
     └─ Check pérdida > 2% capital

STEP 2: RANKING Y CIERRE DE PEORES
  └─ Si portfolio cerca max posiciones:
     ├─ rank_positions_for_closing()
     ├─ Identifica peores 1-2
     └─ Cierra antes de nuevos trades

STEP 3: BUSCAR NUEVOS TRADES
  └─ Solo si hay slots disponibles
     ├─ Check adaptive parameters
     ├─ Análisis técnico
     ├─ Análisis de sentimiento
     └─ Decisión de entrada


IMPACTO ESPERADO
===============================================================================

ANTES (con "holding for recovery"):
- Mantener posiciones perdedoras esperando recuperación
- Bloquear slots con posiciones "stuck"
- Acumular pérdidas por falta de disciplina
- Emociones interfieren en decisiones

DESPUÉS (con HARD CLOSE RULES):
✅ RSI extremo = automático close → Evita reversals
✅ TTL expirado = automático close → No "stuck" positions
✅ EMA cruzada = automático close → Respeta invalidación técnica
✅ Ranking = cierra peores primero → Maximiza capital disponible
✅ Disciplina mecánica → Sin excepciones emocionales


TESTING
===============================================================================

Ejecutar bot:
  python run_bot.py

Verificar en logs:
  grep "HARD CLOSE" logs/bot_run.log
  grep "rank_positions_for_closing" logs/bot_run.log
  grep -v "holding for recovery" logs/bot_run.log  # Should be empty

Monitor en vivo:
  - Ver "🔴 HARD CLOSE" messages
  - Ver "🎯 Position ranking" messages
  - Verificar que NO hay "holding for recovery"


PARÁMETROS AJUSTABLES
===============================================================================

Para cambiar comportamiento, editar en position_manager.py:

1. REGLA A (RSI extremo):
   - BUY threshold: cambiar "rsi_value > 80.0" a otro valor
   - SELL threshold: cambiar "rsi_value < 20.0" a otro valor

2. REGLA B (TTL):
   - max_candles_without_profit: cambiar "6" a otro valor (5, 7, 8)
   - min_profit_threshold: cambiar "0.0005" (0.05%) a otro %

3. REGLA C (EMA):
   - Umbral: actualmente basado en cruce exacto
   - Puede añadirse buffer si se desea (ej: 0.5 pips)

4. RANKING:
   - Weights: 60%, 25%, 15% pueden ajustarse
   - max_close_before_entry: cambiar "2" a más/menos posiciones


===============================================================================
IMPLEMENTACIÓN COMPLETADA - HARD CLOSE RULES ACTIVAS
===============================================================================
