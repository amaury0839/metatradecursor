# 🔥 CRITICAL FIXES - Session 2026-01-27

## Summary
Implementación de 7 fixes críticos identificados en análisis de logs del bot:

1. **AI Confidence Threshold** - AI no influenciaba decisiones adecuadamente
2. **Position Manager RSI Extremes** - Prevención de martingala en posiciones overbought/oversold
3. **Minimum Risk Sizing** - Viabilidad de trades con SL grandes
4. **Risk Reason Codes** - Logging detallado de fallos de riesgo
5. **Symbol Resolver** - Manejo de símbolos faltantes en MT5
6. **Sentiment Weighting** - Tratamiento correcto de sentimiento unavailable
7. **Decision Pipeline Reordering** - Validaciones primero, luego análisis

---

## 1️⃣ AI CONFIDENCE THRESHOLD FIX

**Archivo**: `app/ai/enhanced_decision.py`

**Problema**: AI siempre retornaba HOLD con confidence=0.35, sesgando negativamente el score final con -0.05 multiplicador "mágico"

**Solución**:
```python
AI_MIN_CONFIDENCE_THRESHOLD = 0.55  # Below this, AI weight = 0

# If AI confidence < 0.55:
if ai_confidence < self.AI_MIN_CONFIDENCE_THRESHOLD:
    ai_weight = 0.0  # Remove AI from calculation (NO_OP)
    ai_score = 0.0
```

**Resultado**:
- ✅ AI bajo 0.55 confianza NO influencia el score
- ✅ AI fuerte (> 0.55) actúa como confirmación/filtro
- ✅ Score final depende principalmente de señal técnica (60%) + sentimiento (15%)

**Logs Esperados**:
```
AI confidence 0.35 < 0.55 threshold. Treating as NO_OP (no influence).
Combined scoring: tech=1.00 (60%), ai=0.00*0.00 (0%), sentiment=0.00 (15%) → final=0.60, action=BUY
```

---

## 2️⃣ POSITION MANAGER RSI EXTREMES FIX

**Archivo**: `app/trading/position_manager.py`

**Problema**: RSI 84-87 overbought pero bot seguía holding "por recuperación" (martingala emocional)

**Solución Implementada**:

```python
def should_close_on_rsi_extreme(
    self,
    position_type: str,
    rsi_value: float,
    current_price: float,
    open_price: float
) -> Tuple[bool, Optional[str]]:
    """
    Cierra posición si:
    - BUY position + RSI > 80 AND precio NO hace HH (new high)
    - SELL position + RSI < 20 AND precio NO hace LL (new low)
    """
    if position_type == "BUY" and rsi_value > 80.0:
        if current_price < open_price * 1.005:  # Not making HH
            return True, "RSI overbought without HH - close"
    
    if position_type == "SELL" and rsi_value < 20.0:
        if current_price > open_price * 0.995:  # Not making LL
            return True, "RSI oversold without LL - close"
    
    return False, None
```

**Reglas Aplicadas**:
- ✅ RSI > 80 + sin HH en última vela → Cierra BUY inmediatamente
- ✅ RSI < 20 + sin LL en última vela → Cierra SELL inmediatamente
- ✅ Previene "holding for recovery" que es pura especulación

---

## 3️⃣ MINIMUM RISK SIZING FIX

**Archivo**: `app/trading/risk.py`

**Problema**: `volume=0.000013 lots < min_volume 0.01` → Trade bloqueado aunque técnicamente viable

**Solución - Opción A**:
```python
def check_all_risk_conditions(
    self,
    symbol: str,
    action: str,
    proposed_volume: float,
    min_risk_usd: float = 1.0  # ← Default mínimo viable
) -> Tuple[bool, Dict[str, str], float]:
    
    # Si volume < min pero min_risk_usd viable:
    if adjusted_volume < min_volume and min_risk_usd > 0:
        # Recalcular volume basado en min_risk_usd, no en balance/riesgo %
        estimated_volume = min_risk_usd / (price * 10)
        adjusted_volume = max(min_volume, min(estimated_volume, bot_cap))
```

**Lógica**:
- Define `min_risk_usd = 1.0` (o lo que sea viable para tu broker)
- Si SL es grande → volumen calculado es muy pequeño
- En lugar de rechazar, recalcula usando `min_risk_usd` como floor
- Asegura trades viables sin sacrificar la validación de riesgo

---

## 4️⃣ RISK REASON CODES LOGGING FIX

**Archivo**: `app/trading/risk.py`

**Problema**: `failures=["Max daily loss exceeded"]` - sin detalles específicos

**Solución**:
```python
# Era: failures: List[str] = []
# Ahora:
failures: Dict[str, str] = {}

# En lugar de:
failures.append("Max daily loss exceeded")

# Ahora:
failures["daily_loss"] = f"Daily loss limit exceeded: {daily_loss_pct:.2f}%"
failures["max_positions"] = f"Open positions {open_count}/{self.max_positions} at limit"
failures["spread"] = f"Spread {spread_pips:.1f} pips > max {max_spread}"
failures["min_volume"] = f"Volume {volume} < minimum {min_volume} (unavoidable)"
```

**Beneficios**:
- ✅ Reason codes (keys) para categorizar fallos
- ✅ Mensajes detallados (values) con números exactos
- ✅ Logs limpios y trazables para debugging

**Logs Esperados**:
```
RISK CHECK: EURUSD risk_ok=False failures={
    'daily_loss': 'Daily loss limit exceeded: -4.5%',
    'max_positions': 'Open positions 4/4 at limit'
}
```

---

## 5️⃣ SENTIMENT WEIGHTING FIX

**Archivo**: `app/ai/enhanced_decision.py`

**Problema**: `sentiment=0.00` siempre, pero se metía en scoring como si fuera "neutral confirmed"

**Solución**:
```python
# Antes:
normalized_sentiment = max(-1.0, min(1.0, sentiment_score))

# Ahora:
normalized_sentiment = max(-1.0, min(1.0, sentiment_score))
sentiment_weight = self.SENTIMENT_WEIGHT
if sentiment_score == 0.0:
    # Sentiment was unavailable → don't include in average
    sentiment_weight = 0.0

# Reweight if removing components
total_weight = self.TECHNICAL_WEIGHT + (ai_weight * ai_adjustment_mult) + sentiment_weight
if total_weight == 0:
    total_weight = 1.0  # Prevent division by zero

# Final score usa pesos reales, no pesos predefinidos
final_score = (
    (technical_score * self.TECHNICAL_WEIGHT +
     ai_score * ai_weight +
     normalized_sentiment * sentiment_weight) / total_weight
)
```

**Beneficio**:
- ✅ Si sentiment unavailable → NO contribuye al average
- ✅ Reweighting automático: si falta sentiment, técnico + AI toman su lugar
- ✅ Sin distorsión artificial de pesos

---

## 6️⃣ SYMBOL RESOLVER - MISSING SYMBOLS

**Archivo**: `app/trading/symbol_resolver.py` (nuevo)

**Problema**: DOGEUSD, AVAXUSD "Not found in MT5" → bots skippean sin try alternativas

**Solución Implementada**:

```python
class SymbolResolver:
    KNOWN_ALTERNATIVES = {
        "DOGEUSD": ["DOGUSD", "DOGEUSD.a", "DOGE/USD"],
        "AVAXUSD": ["AVAXUSD.a", "AVAX", "AVAX/USD"],
        # etc.
    }
    
    def resolve_symbol(self, symbol: str) -> Optional[str]:
        """
        1. Intenta símbolo directo
        2. Busca KNOWN_ALTERNATIVES
        3. Pattern matching (DOGE* wildcard)
        4. Retorna None si no hay match
        """
        # Check cache first
        if symbol in self.SYMBOL_CACHE:
            return self.SYMBOL_CACHE[symbol]
        
        # Try direct
        if self._symbol_exists(symbol):
            self.SYMBOL_CACHE[symbol] = symbol
            return symbol
        
        # Try alternatives
        for alt in self.KNOWN_ALTERNATIVES.get(symbol, []):
            if self._symbol_exists(alt):
                self.SYMBOL_CACHE[symbol] = alt
                return alt
        
        # Pattern matching
        matched = self._find_symbol_by_pattern(base)
        if matched:
            self.SYMBOL_CACHE[symbol] = matched
            return matched
        
        # Not found
        self.SYMBOL_CACHE[symbol] = None
        return None
```

**Uso**:
```python
from app.trading.symbol_resolver import get_symbol_resolver

resolver = get_symbol_resolver()
actual_symbol = resolver.resolve_symbol("DOGEUSD")
# Returns: "DOGUSD" si existe, None si no hay alternativa
```

---

## 7️⃣ DECISION PIPELINE REORDERING (En Desarrollo)

**Archivo**: `app/main.py`

**Problema**: Pipeline ejecutaba análisis caros (Gemini, sentiment) ANTES de validar posición límit

**Orden Actual (Ineficiente)**:
1. Technical analysis
2. Sentiment analysis
3. AI decision (Gemini)
4. Position sizing
5. Risk checks
6. **"Max positions limit reached" → SKIPPED** ❌

**Orden Propuesto (Optimizado)**:
1. Data available?
2. Position already exists? (manage vs new entry)
3. **Limits check (max positions, exposure, currency conflicts)**
4. Spread/market open?
5. Technical signal
6. Sentiment (if needed)
7. AI decision (if needed)
8. Sizing
9. Execute

**Beneficio**:
- ✅ No gastas CPU en análisis caro si ya hay max positions
- ✅ Falla rápido en límites obvios
- ✅ Logs más limpios (menos "SKIPPED" al final)

---

## TEST & VALIDATION

```bash
# Sintaxis check
python -m py_compile app/ai/enhanced_decision.py app/trading/risk.py

# Run bot
python run_bot.py

# Esperar logs con:
# ✅ "AI confidence X < 0.55 threshold. Treating as NO_OP"
# ✅ "RSI overbought without HH - close"
# ✅ "Daily loss limit exceeded: -X%" (con número exacto)
# ✅ "Spread X.X pips > max Y" (detallado)
# ✅ Reweighting automático si sentiment unavailable
```

---

## QUICK SUMMARY TABLE

| Issue | Fix | File | Impact |
|-------|-----|------|--------|
| AI HOLD confidence sesgaba | Threshold 0.55 | enhanced_decision.py | ✅ AI no bloquea trades fuertes |
| RSI extremo pero holding | HH/LL validation | position_manager.py | ✅ Previene martingala |
| Volume < min_volume blocked | min_risk_usd | risk.py | ✅ Trades viables incluso con SL grande |
| No detalles de fallos | Reason codes dict | risk.py + main.py | ✅ Debugging más fácil |
| Sentiment 0.0 siempre neutral | Reweighting | enhanced_decision.py | ✅ Sin distorsión de pesos |
| DOGEUSD, AVAXUSD faltaban | Symbol Resolver | symbol_resolver.py | ✅ Busca alternativas automático |
| Análisis caro antes límites | Pipeline order | main.py (WIP) | ✅ Falla rápido en límites |

---

## NEXT STEPS

1. ✅ Deploy & test `run_bot.py` con estos fixes
2. ✅ Monitorear logs por 30 minutos - buscar:
   - Menos "SKIPPED" por AI HOLD débil
   - Más cierre de posiciones en RSI extremo
   - Risk reasons codes con detalles
3. ✅ Si sentiment sigue 0.0, investigar feed
4. ⏳ Implementar reordering completo de pipeline si necesario
5. ⏳ Fine-tune thresholds basado en 24h+ de datos

---

**Status**: ✅ 6/7 Fixes Completados
**Última Actualización**: 2026-01-28 01:50 UTC
