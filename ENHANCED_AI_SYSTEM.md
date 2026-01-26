# Enhanced AI Trading Decision System

## 🚀 Nuevo Sistema Mejorado

El sistema de decisión de trading ahora tiene **dos motores de IA**:

### 1. **Enhanced Decision Engine** (Nuevo) - `app/ai/enhanced_decision_engine.py`
Motor avanzado con capacidades de búsqueda web y análisis multi-fuente:

#### Fuentes de Datos:
- **Technical Indicators (30%)**: RSI, EMAs, tendencias, momentum
- **News Sentiment (20%)**: Análisis de noticias del mercado
- **Web Intelligence (30%)**: Búsqueda en tiempo real de:
  - Información general del mercado
  - Últimas noticias y eventos
  - Análisis técnico de fuentes web
  - Pronósticos y predicciones
- **AI Synthesis (20%)**: Integración experta con Gemini 2.0

#### Características:
✅ Web scraping con DuckDuckGo (sin API keys necesarias)
✅ Análisis multi-fuente con ponderación inteligente
✅ Decisiones más informadas basadas en datos en tiempo real
✅ Threshold agresivo: confidence >= 0.40 para ejecutar
✅ Contexto de portfolio para decisiones inteligentes

### 2. **Simple Decision Engine** (Fallback) - `app/ai/decision_engine.py`
Motor simple que solo usa datos técnicos y sentiment:

#### Características:
✅ Análisis rápido sin dependencias externas
✅ Usa solo datos locales (técnicos + sentiment)
✅ Sin búsquedas web
✅ Backup confiable cuando falla el enhanced

---

## 🎯 Smart Decision Router

El sistema usa **smart routing** automático:

```python
from app.ai.smart_decision_router import make_smart_decision

# Intenta enhanced primero, fallback a simple
decision = make_smart_decision(
    symbol="EURUSD",
    timeframe="M15",
    technical_data=tech_data,
    sentiment_data=sent_data,
    use_enhanced=True  # True = enhanced, False = solo simple
)
```

### Flujo de Decisión:
```
1. Intenta Enhanced Decision Engine
   ├─ ✓ Si funciona → Retorna decisión
   └─ ✗ Si falla → Fallback a Simple
   
2. Simple Decision Engine (Fallback)
   ├─ ✓ Si funciona → Retorna decisión
   └─ ✗ Si falla → Retorna None
```

---

## 🔧 Configuración

### Variables de Entorno (.env)
```bash
# AI Configuration
GEMINI_API_KEY=your_gemini_key_here

# Trading Symbols
DEFAULT_SYMBOLS=EURUSD,USDJPY,BTCUSD,ETHUSD,...

# News API (opcional)
NEWS_API_KEY=your_news_api_key
```

### Config.py
```python
class AIConfig:
    min_confidence_threshold: float = 0.30  # Threshold mínimo
    enhanced_confidence_threshold: float = 0.40  # Para enhanced
    max_retries: int = 3
    timeout_seconds: int = 30
```

---

## 📊 Estructura del Sistema

```
app/ai/
├── enhanced_decision_engine.py   # Motor avanzado con web search
├── decision_engine.py             # Motor simple (fallback)
├── smart_decision_router.py       # Router inteligente
├── gemini_client.py               # Cliente Gemini API
├── schemas.py                     # TradingDecision schema
└── prompt_templates.py            # Prompts para AI

app/trading/
└── integrated_analysis.py         # Integra todo (UPDATED)
```

---

## 🎮 Uso en el Trading Loop

El sistema está integrado automáticamente en `app/main.py`:

```python
# En analyze_symbol()
analysis = integrated_analyzer.analyze_symbol(
    symbol=symbol,
    timeframe=timeframe,
    use_enhanced_ai=True  # ← Activa enhanced
)

# El análisis incluye:
# - analysis['technical']: Indicadores técnicos
# - analysis['sentiment']: News sentiment
# - analysis['ai_decision']: Decisión AI (si available)
# - analysis['signal']: BUY/SELL/HOLD final
# - analysis['confidence']: Nivel de confianza
```

---

## 📈 Ponderación de Decisiones

### Cuando AI Decision está disponible:
```
Priority 1: AI Decision (si confidence >= 0.40)
Priority 2: Technical Signal + Sentiment
Priority 3: Combined Score
```

### Fuentes de AI Decision:
```
Enhanced Engine:
- Technical: 30%
- Sentiment: 20%
- Web Search: 30%
- AI Synthesis: 20%

Simple Engine:
- Technical: 60%
- Sentiment: 40%
```

---

## 🔍 Web Search Details

### Queries Automáticas:
1. **General**: `{symbol} forex crypto trading analysis today`
2. **News**: `{symbol} latest news market impact trading`
3. **Technical**: `{symbol} technical analysis support resistance`
4. **Forecast**: `{symbol} price prediction forecast today`

### Search Provider:
- **DuckDuckGo HTML** (no API key necesaria)
- Timeout: 10 segundos
- Limit: 5 resultados por query
- Snippet max: 500 caracteres

---

## ⚙️ Mantenimiento del Volumen

El sistema también corrige problemas de volumen:

### Problema Anterior:
```python
# Forzaba volumen mínimo aunque el capital fuera insuficiente
lots = max(min_volume, calculated_lots)  # ❌ MALO
```

### Solución Nueva:
```python
# Rechaza trades si volumen < mínimo del broker
if calculated_lots < min_volume:
    return 0.0  # ✓ CORRECTO
```

**Resultado**: No más trades con volumen excesivo en crypto (100 lotes ADAUSD)

---

## 📋 Logs y Debugging

### Enhanced Engine Logs:
```
INFO:enhanced_ai - Aggregated 6 data sources for BTCUSD
INFO:enhanced_ai - Enhanced AI Decision: BUY BTCUSD (confidence=0.75, sources=6)
```

### Router Logs:
```
INFO:ai_router - Attempting ENHANCED decision for EURUSD
INFO:ai_router - ✓ Enhanced decision succeeded: BUY with confidence 0.65
```

### Fallback Logs:
```
WARNING:ai_router - Enhanced decision failed: timeout, falling back to simple
INFO:ai_router - Using SIMPLE decision engine for EURUSD
INFO:ai_router - ✓ Simple decision succeeded: BUY with confidence 0.55
```

---

## 🎯 Thresholds y Aggressiveness

### Current Settings:
```python
# Integrated Analysis
MIN_CONFIDENCE_FOR_ACTION = 0.30  # Base threshold

# Enhanced AI
ENHANCED_CONFIDENCE = 0.40  # Para ejecutar con enhanced

# Simple AI
SIMPLE_CONFIDENCE = 0.30  # Para ejecutar con simple
```

### Ejemplo de Decisión:
```json
{
  "action": "BUY",
  "confidence": 0.75,
  "reasoning": "Strong bullish confluence: Technical RSI oversold + positive sentiment + web search shows bullish forecasts",
  "stop_loss": 1.0850,
  "take_profit": 1.1050,
  "volume_lots": 0.50
}
```

---

## 🚦 Testing

Para probar el enhanced engine:

```python
from app.ai.enhanced_decision_engine import get_enhanced_decision_engine

engine = get_enhanced_decision_engine()

# Test web search
web_info = engine.search_web_info("EURUSD", "general")
print(web_info)

# Test decision
decision = engine.make_enhanced_decision(
    symbol="EURUSD",
    timeframe="M15",
    technical_data=tech_data,
    sentiment_data=sent_data
)
print(decision)
```

---

## 📝 Notas Importantes

1. **Web Search**: Puede tardar 10-30 segundos por análisis (3-4 queries)
2. **Fallback**: Simple engine es rápido (<5 segundos)
3. **Cache**: News sentiment tiene cache de 1 hora
4. **Rate Limiting**: DuckDuckGo puede limitar si haces demasiadas búsquedas
5. **Internet**: Enhanced requiere conexión estable

---

## 🔮 Próximas Mejoras

- [ ] Caché de web search results (15-30 min)
- [ ] Más search providers (Google, Bing, etc.)
- [ ] Sentiment analysis de web snippets
- [ ] Machine learning para mejorar ponderación
- [ ] Backtesting de enhanced vs simple
- [ ] Dashboard comparativo en UI

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa logs en `logs/`
2. Verifica conexión a internet
3. Comprueba que beautifulsoup4 está instalado
4. Usa `use_enhanced_ai=False` para deshabilitar enhanced

---

**Sistema creado**: 2024
**Última actualización**: Hoy 🚀
