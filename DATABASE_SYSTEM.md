# Sistema de Base de Datos Histórica - Actualización Completada

## 📋 Resumen de Cambios

Se ha implementado un sistema completo de base de datos SQLite para:
- ✅ Guardar todos los análisis históricos (técnico, sentimiento, combinado)
- ✅ Guardar todas las decisiones AI (Enhanced vs Simple)
- ✅ Guardar todos los trades abiertos y cerrados con P&L
- ✅ Calcular métricas de performance (win rate, profit factor, equity curve)
- ✅ Dashboard analytics con visualizaciones Plotly
- ✅ Migración automática de datos históricos desde MT5

---

## 🗄️ Esquema de Base de Datos

### Tabla: analysis_history
Registra cada análisis técnico realizado:
- **Campos:** symbol, timeframe, rsi, macd, bollinger_position, technical_signal, sentiment_score, combined_score, timestamp

### Tabla: ai_decisions
Registra cada decisión tomada por los motores IA:
- **Campos:** symbol, timeframe, action, confidence, reasoning, engine_type, data_sources, status, timestamp

### Tabla: trades
Registra el ciclo de vida completo de cada trade:
- **Campos:** ticket, symbol, trade_type, volume, open_price, close_price, stop_loss, take_profit, profit, commission, swap, status, open_timestamp, close_timestamp

### Tabla: performance_metrics
Resumen calculado de performance:
- **Campos:** period_start, period_end, total_trades, winning_trades, losing_trades, win_rate, profit_factor, total_pnl, max_drawdown

### Tabla: web_search_cache
Cache de búsquedas web para optimización:
- **Campos:** query, results, timestamp, engine

---

## 🔧 Integración en el Bot

### 1. **app/core/database.py** (NUEVO)
Clase `DatabaseManager` con métodos:
```python
db = get_database_manager()

# Guardar análisis
db.save_analysis(analysis_result)

# Guardar decisión AI
db.save_ai_decision(symbol, timeframe, decision, engine_type, data_sources)

# Guardar trade
db.save_trade(trade_info)

# Actualizar trade cerrado
db.update_trade(ticket, close_info)

# Obtener datos históricos
trades = db.get_trades()
decisions = db.get_ai_decisions()
analysis = db.get_analysis_history()
```

### 2. **app/trading/integrated_analysis.py** (MODIFICADO)
- ✅ Agregado: `from app.core.database import get_database_manager`
- ✅ En `__init__`: `self.db = get_database_manager()`
- ✅ En `analyze_symbol()`: Llama a `db.save_analysis()` después de cada análisis

**Línea de integración:**
```python
analysis_id = self.db.save_analysis(result)
```

### 3. **app/ai/smart_decision_router.py** (MODIFICADO)
- ✅ Agregado: `from app.core.database import get_database_manager`
- ✅ En `make_smart_decision()`: Guarda decisiones Enhanced y Simple
- ✅ Incluye: engine_type, confidence, reasoning, data_sources

**Líneas de integración:**
```python
# Enhanced AI
db.save_ai_decision(symbol, timeframe, decision, engine_type='enhanced', 
                    data_sources=['technical', 'sentiment', 'web', 'ai'])

# Simple AI
db.save_ai_decision(symbol, timeframe, decision, engine_type='simple',
                    data_sources=['technical', 'sentiment'])
```

### 4. **app/main.py** (MODIFICADO)
- ✅ Agregado: `from app.core.database import get_database_manager`
- ✅ Agregado: Importes de `datetime` y `MetaTrader5`
- ✅ En `place_market_order()`: Llama a `db.save_trade()` después de orden exitosa
- ✅ En `close_position()`: Llama a `db.update_trade()` después de cerrar

**Líneas de integración:**
```python
# Después de place_market_order exitosa (~línea 370)
db = get_database_manager()
db.save_trade({
    'ticket': ticket,
    'symbol': symbol,
    'trade_type': decision.action,
    'volume': volume,
    'open_price': entry_price,
    'stop_loss': sl_price,
    'take_profit': tp_price,
    'status': 'open'
})

# Después de close_position exitosa (~línea 180)
db.update_trade(pos_ticket, {
    'close_price': current_price,
    'close_timestamp': datetime.now().isoformat(),
    'profit': pos_profit,
    'status': 'closed'
})
```

### 5. **app/ui/pages_history.py** (EXISTENTE)
3 páginas para visualizar historial:
- `render_analysis_history_page()` - Gráficos RSI, confianza, señales
- `render_ai_decisions_page()` - Comparación de motores, distribución acciones
- `render_trade_history_page()` - Equity curve, distribución ganancias, tabla trades

### 6. **app/ui/pages_database_analytics.py** (NUEVO)
Dashboard completo con 5 tabs:
- **Performance** - Equity curve, distribution, win rate, P&L
- **Trade Analysis** - Filtros por símbolo/tipo, performance por símbolo, tabla detallada
- **AI Decisions** - Engine comparison, action distribution, confidence analysis
- **Analysis History** - Technical indicators trends, estadísticas, registros
- **System Stats** - Database health, conteos, resumen por símbolo

### 7. **app/ui_improved.py** (MODIFICADO)
- ✅ Agregada 6ª tab: "📉 Analytics"
- ✅ Importa y renderiza: `render_database_analytics()`
- ✅ Mantiene tabs existentes: Dashboard, Analysis, History, Configuration, Logs

---

## 📊 Dashboard Analytics

### Acceso
1. Abre la UI: `streamlit run app/ui_improved.py`
2. Navega a la tab **"📉 Analytics"**
3. Explora los 5 sub-tabs:

### Funcionalidades

**Performance Tab:**
- Métricas clave (Total trades, Closed, P&L, Win Rate)
- Equity curve mostrando P&L acumulado
- Profit distribution (histograma)
- Win vs Loss comparison

**Trade Analysis Tab:**
- Filtros por Status, Symbol, Type
- Performance por símbolo
- Tabla detallada de trades con sorteo

**AI Decisions Tab:**
- Distribución de motores (Enhanced vs Simple)
- Distribución de acciones (BUY, SELL, HOLD)
- Confidence analysis por motor
- Últimas 20 decisiones

**Analysis History Tab:**
- Technical indicators trends (RSI over time)
- Estadísticas (RSI promedio, MACD, Bollinger)
- Últimos 50 registros de análisis

**System Stats Tab:**
- Conteo total (trades, decisiones, análisis)
- Tamaño de base de datos
- Health check
- Resumen por símbolo

---

## 🚀 Migración de Datos Históricos

Para importar trades históricos desde MT5:

```bash
# Últimos 30 días (default)
python migrate_trades.py

# Últimos 60 días
python migrate_trades.py --days 60

# Símbolos específicos
python migrate_trades.py --days 30 --symbols EURUSD,GBPUSD,XRPUSD
```

**¿Qué hace?**
1. Conecta a MT5
2. Obtiene todos los deals del período
3. Agrupa deals por ticket (IN=open, OUT=close)
4. Calcula profit, commission, swap
5. Guarda en base de datos

---

## 📈 Uso en Backtesting & Reajuste

### Exportar datos para análisis
```python
from app.core.database import get_database_manager

db = get_database_manager()

# Obtener trades cerrados
trades = db.get_trades()
closed_trades = [t for t in trades if t['status'] == 'closed']

# Calcular métricas
performance = db.get_performance_summary()

# Exportar a CSV para análisis
import pandas as pd
df = pd.DataFrame(closed_trades)
df.to_csv('trades_export.csv', index=False)
```

### Analizar decisiones AI
```python
# Ver cuál motor (Enhanced vs Simple) es más rentable
decisions = db.get_ai_decisions()
enhanced_decisions = [d for d in decisions if d['engine_type'] == 'enhanced']
simple_decisions = [d for d in decisions if d['engine_type'] == 'simple']
```

---

## 🔍 Verificación de Integración

Cada componente guarda datos automáticamente:

1. **✅ Análisis** - Se guardan después de `integrated_analysis.py:analyze_symbol()`
2. **✅ Decisiones AI** - Se guardan después de `smart_decision_router.py:make_smart_decision()`
3. **✅ Trades** - Se guardan después de `main.py:place_market_order()` y se actualizan en `close_position()`

Para verificar:
```python
# Revisar datos en database.py
from app.core.database import get_database_manager
db = get_database_manager()

print("Total trades:", len(db.get_trades()))
print("Total decisions:", len(db.get_ai_decisions()))
print("Total analysis:", len(db.get_analysis_history()))
```

---

## 📝 Logs de la Integración

### app/main.py
```
✅ Added import: from app.core.database import get_database_manager
✅ Added imports: from datetime import datetime, import MetaTrader5 as mt5
✅ Added db.save_trade() after place_market_order success
✅ Added db.update_trade() after close_position success
```

### app/trading/integrated_analysis.py
```
✅ Added import: from app.core.database import get_database_manager
✅ Added db instance in __init__
✅ Added db.save_analysis() in analyze_symbol return
```

### app/ai/smart_decision_router.py
```
✅ Added import: from app.core.database import get_database_manager
✅ Added db instance in make_smart_decision
✅ Added db.save_ai_decision() for enhanced engine
✅ Added db.save_ai_decision() for simple engine
```

### app/ui_improved.py
```
✅ Added 6th tab: "📉 Analytics"
✅ Added render_database_analytics() call with error handling
✅ Maintains existing 5 tabs for backward compatibility
```

---

## 🎯 Próximos Pasos Opcionales

1. **Backtesting Engine**: Usar datos históricos para optimizar parámetros
2. **Performance Reporting**: Generar reportes semanales/mensuales
3. **Model Retraining**: Usar datos históricos para reentrenar Enhanced AI
4. **Alertas**: Notificar cuando win rate cae bajo umbral
5. **Exportación**: Generar reportes Excel/PDF de performance

---

## ✅ Estado de Implementación

| Componente | Estado | Línea |
|-----------|--------|-------|
| database.py | ✅ Completado | core/ |
| integrated_analysis.py | ✅ Integrado | trading/ |
| smart_decision_router.py | ✅ Integrado | ai/ |
| main.py | ✅ Integrado | root |
| pages_history.py | ✅ Completado | ui/ |
| pages_database_analytics.py | ✅ Completado | ui/ |
| ui_improved.py | ✅ Integrado | app/ |
| migrate_trades.py | ✅ Completado | root |

**Base de datos lista para:**
- ✅ Análisis histórico
- ✅ Backtesting
- ✅ Performance reporting
- ✅ AI retraining
- ✅ Trade lifecycle tracking
