# DIAGRAMA: CÓMO FUNCIONA EL SISTEMA

## 1. BACKTEST (Pruebas offline)
```
BACKTEST ENGINE
    |
    +-- Cargar datos históricos (7 días)
    |
    +-- Ejecutar estrategia en simulación
    |
    +-- Calcular métricas:
    |       - Win Rate (% ganancias)
    |       - Profit Factor (ganancia/pérdida)
    |       - Optimization Score
    |
    +-- Guardar en: data/backtest_results.json
    |
    +-- Entrada: Histórico de MT5
    +-- Salida: Performance report
```

### Ejemplo de output:
```
Backtest EURUSD (7 días):
  Win Rate: 65%
  Profit Factor: 2.15
  Optimization Score: 8.5/10
  Best hours: 08:00-12:00 GMT, 18:00-22:00 GMT
```

---

## 2. IA - ARQUITECTURA CON REGLA DE ORO
```
ENTRADA: Indicadores técnicos (RSI, EMA, ATR)
    |
    v
┌─────────────────────────────────────┐
│ AI GATE - Regla de Oro              │
│ ¿Necesita consulta a IA?            │
└──────┬──────────────────────────────┘
       |
       ├─ SIGNAL = STRONG_BUY/SELL?
       │  └─> NO LLAMA IA (confianza 100%)
       │
       ├─ SIGNAL = BUY/SELL + Confianza >= 75%?
       │  └─> NO LLAMA IA (señal clara)
       │
       ├─ RSI in gray zone (45-55)?
       │  └─> SI LLAMA IA (indeciso)
       │
       ├─ EMAs convergiendo?
       │  └─> SI LLAMA IA (cambio inminente)
       │
       └─ ATR muy bajo?
          └─> SI LLAMA IA (baja volatilidad)
             
    v
┌─────────────────────────────────────┐
│ DECISION ENGINE                     │
│ - Técnico: 70% peso               │
│ - IA (Gemini): 20% peso           │
│ - Sentimiento: 10% peso           │
└──────┬──────────────────────────────┘
       |
       v
SALIDA: 
  - Action: BUY/SELL/HOLD
  - Confidence: 0.0 - 1.0
  - Stop Loss: precio
  - Take Profit: precio
```

### Flujo de ejemplo:
```
EURUSD analizado:
  Indicadores:
    - RSI: 50 (zona gris)
    - EMA12: 1.0920
    - EMA26: 1.0918
    - Señal técnica: BUY (confianza 60%)

  AIGate decision: RSI en zona gris → LLAMAR IA

  Gemini AI análisis:
    - ECB hawkish remarks yesterday
    - Dollar strength moderate
    - Support at 1.0910
    → Recomendación: BUY con precaución

  Decision Engine combina:
    - Técnico 70%: 0.60
    - AI 20%: 0.65
    - Sentiment 10%: 0.55
    → Confianza FINAL: 0.613 (61.3%)

  EJECUCIÓN:
    Action: BUY 0.5 lotes
    Entry: 1.0920
    SL: 1.0890 (- 30 pips)
    TP: 1.0960 (+ 40 pips)
```

---

## 3. REAJUSTES DE RIESGO (Rebalanceos automáticos)

### A. RIESGO DINÁMICO POR TIPO
```
Sistema: Asigna % de riesgo según volatilidad del activo

CRYPTO (Alta volatilidad):
  BTCUSD, ETHUSD, BNBUSD → 3% riesgo por trade

FOREX MAJOR (Media volatilidad):
  EURUSD, GBPUSD, USDJPY → 2% riesgo por trade

FOREX CROSS (Baja-Media):
  AUDNZD, NZDUSD → 2.5% riesgo por trade

Beneficio: Más posiciones en mercados calmados, menos en turbulencias
```

### B. PERFILES DE RIESGO (Cambian automáticamente)
```
Capital: $4,000

CONSERVATIVE (mercado volátil):
  ├─ Risk: 0.25% por trade
  ├─ Max positions: 3
  ├─ Example: Trade 1 = 0.25% * $4,000 = $10 riesgo
  └─ Total max: $30 en riesgo abierto

BALANCED (normal):
  ├─ Risk: 0.5% por trade
  ├─ Max positions: 5
  ├─ Example: Trade 1 = 0.5% * $4,000 = $20 riesgo
  └─ Total max: $100 en riesgo abierto

AGGRESSIVE (mercado tranquilo):
  ├─ Risk: 0.75% por trade
  ├─ Max positions: 7
  ├─ Example: Trade 1 = 0.75% * $4,000 = $30 riesgo
  └─ Total max: $210 en riesgo abierto

Sistema automático:
  - Cambia perfil cada 3+ horas
  - Max 2 cambios por día
  - Basado en volatilidad de mercado
```

### C. GESTIÓN DE POSICIONES ABIERTAS
```
Cada minuto, el bot revisa TODAS las posiciones abiertas:

┌─────────────────────────────────────────┐
│ POSICIÓN ABIERTA: EURUSD                │
│ Entry: 1.0920 | SL: 1.0890 | TP: 1.0960│
└───────────────┬─────────────────────────┘
                |
    ┌───────────┴───────────┐
    |                       |
    v                       v
┌──────────────┐    ┌────────────────┐
│ RSI EXTREME? │    │ TRAILING STOP?  │
│              │    │                │
│ RSI = 42     │    │ Price: 1.0950  │
│ (No < 20)    │    │ Profit: +30p   │
│ Don't close  │    │ ATR: 0.0050    │
└──────────────┘    │ → Move SL UP   │
                    │ From: 1.0890   │
                    │ To: 1.0900     │
                    │ (Lock profit)  │
                    └────────────────┘

Otras reglas:
  - Cierre por timeout (24h default)
  - Cierre por riesgo máximo
  - Cierre por señal opuesta
  - Movimiento de breakeven
```

### D. VALIDACIÓN DE RIESGO (Risk Gates)
```
Antes de ejecutar CUALQUIER trade:

1. ¿Alcanzado max daily loss (10%)?
   └─> NO → Continuar
   └─> SI → STOP TODO

2. ¿Total exposición < 15%?
   └─> SI → Continuar
   └─> NO → REDUCIR tamaño

3. ¿Menos de 50 posiciones abiertas?
   └─> SI → Continuar
   └─> NO → NO ABRIR MÁS

4. ¿Spread dentro de límites?
   ├─ Forex: < 10 pips?
   ├─ Crypto: < 300 pips?
   └─> SI para ambos → Continuar

5. ¿Profit factor > 1.0?
   └─> SI → Aumentar riesgo (agresivo)
   └─> NO → Disminuir riesgo (conservador)
```

---

## 4. CICLO COMPLETO: 60 SEGUNDOS

```
Timestamp: 13:23:14

SEGUNDO 0-5: Revisar posiciones abiertas (9)
  ├─ BTCUSD: +$45 → Trailing SL
  ├─ ETHUSD: -$12 → Monitor
  ├─ EURUSD: +$8 → RSI check
  └─ ... (6 más)

SEGUNDO 5-15: Analizar 84 símbolos
  ├─ Indicadores técnicos (RSI, EMA, ATR)
  ├─ Detectar señales (BUY/SELL)
  └─ Aplicar AIGate

SEGUNDO 15-30: Decisiones para señales grises
  ├─ 3 símbolos necesitan IA
  ├─ Llamar Gemini (10 segundos)
  ├─ Combinar análisis
  └─ Calcular confianza

SEGUNDO 30-45: Ejecutar operaciones
  ├─ Position sizing (volumen óptimo)
  ├─ Validar riesgos (6 checks)
  ├─ Orden_check() (validación MT5)
  └─ order_send() (enviar a broker)

SEGUNDO 45-60: Logging y rebalanceo
  ├─ Guardar decisiones en BD
  ├─ Actualizar estadísticas
  ├─ Evaluar cambio de perfil
  └─ Preparar próximo ciclo

RESULTADO:
  ✅ 9 posiciones monitoreadas
  ✅ 8 nuevas oportunidades evaluadas
  ✅ 1 nueva orden ejecutada
  ✅ Exposición: 0.24% / 15%
  ✅ Siguiente ciclo: +60s
```

---

## 5. TABLA COMPARATIVA: RISK PROFILES

```
┌───────────────┬──────────────┬──────────────┬──────────────┐
│ Parámetro     │ CONSERVATIVE │ BALANCED     │ AGGRESSIVE   │
├───────────────┼──────────────┼──────────────┼──────────────┤
│ Risk/trade    │ 0.25%        │ 0.50%        │ 0.75%        │
│ Max positions │ 3            │ 5            │ 7            │
│ Min confid.   │ 70%          │ 60%          │ 50%          │
│ Max daily loss│ 5%           │ 8%           │ 12%          │
│ Max drawdown  │ 3%           │ 5%           │ 8%           │
│ Position hold │ 48 horas     │ 24 horas     │ 12 horas     │
├───────────────┼──────────────┼──────────────┼──────────────┤
│ Usar cuando   │ Crisis       │ Normal       │ Bull trend   │
│               │ Volatilidad  │ Volatilidad  │ Volatilidad  │
│               │ muy alta     │ media        │ baja         │
├───────────────┼──────────────┼──────────────┼──────────────┤
│ Capital/day   │ ~$10         │ ~$20         │ ~$30         │
│ (risk 0.5%)   │ (max)        │ (typical)    │ (max)        │
└───────────────┴──────────────┴──────────────┴──────────────┘

Con capital = $4,000
```

---

## 6. MATRIZ DE DECISIÓN

```
RSI         EMA Trend   Tech Signal   →  AI Gate Decision
─────────────────────────────────────────────────────────
> 70        Diverge     SELL          →  NO IA (confianza 100%)
< 30        Converge    BUY           →  NO IA (confianza 100%)
45-55       Weak        HOLD/WEAK     →  SI IA (zona gris)
35-45       Bull        BUY           →  NO IA (confianza 80%)
55-65       Bear        SELL          →  NO IA (confianza 80%)
50          Convergir   BUY           →  SI IA (decisión ambigua)

Ventaja: 
  - Menos llamadas a Gemini (60% menos)
  - Respuestas más rápidas
  - Decisiones más claras
  - Menor costo API
```

---

## 7. RESUMEN: CÓMO ESTÁ BALANCEADO

```
        AUTOMATIZACIÓN vs INTELIGENCIA
        
Automatizado (Sin IA):      Inteligente (Con IA):
├─ 60% de decisiones      ├─ 40% de decisiones
├─ Basado en técnico      ├─ Análisis fundamental
├─ Rápido (< 1ms)         ├─ Contextual (mercado)
├─ Predecible             ├─ Adaptativo
└─ Bajo costo             └─ Alto valor
        
Resultado: Sistema híbrido eficiente
```

---

**Conclusión**: Todos los componentes están diseñados para trabajar juntos,
automatizando lo obvio (señales técnicas fuertes) e inteligentificando lo ambiguo
(decisiones grises). Los reajustes de riesgo ocurren automáticamente cada minuto.
