# Sistema de Base de Datos - Guía de Uso 🗄️

## ¿Qué se ha implementado?

Un sistema completo de **persistencia histórica** que automáticamente:
- ✅ Guarda **todos los análisis** (técnico + sentimiento)
- ✅ Registra **todas las decisiones AI** (Enhanced vs Simple)
- ✅ Almacena **todos los trades** (abiertos y cerrados)
- ✅ Calcula **métricas de performance** (win rate, profit factor, etc.)
- ✅ Proporciona **dashboard de analytics** con visualizaciones

---

## 🚀 Inicio Rápido

### Opción 1: Iniciar Bot con Sistema Activo (RECOMENDADO)
```bash
python run_bot_with_db.py
```

Esto:
1. Inicializa la base de datos
2. Muestra estadísticas actuales
3. Abre Streamlit UI con Sistema Activo
4. Todas las características listas para usar

### Opción 2: Iniciar UI Directamente
```bash
streamlit run app/ui_improved.py
```

---

## 📊 Acceder a los Datos Históricos

### En la UI de Streamlit

**Ubicación:** Tab principal **"📉 Analytics"**

Contiene 5 sub-tabs:

#### 1️⃣ **Performance**
- Equity curve (P&L acumulado)
- Distribución de ganancias/pérdidas
- Win rate, total trades, P&L
- Profit distribution histogram

#### 2️⃣ **Trade Analysis**
- Filtros por Status, Symbol, Type
- Performance por símbolo
- Tabla detallada de todos los trades
- Métricas por símbolo

#### 3️⃣ **AI Decisions**
- Enhanced vs Simple engine comparison
- Action distribution (BUY, SELL, HOLD)
- Confidence analysis
- Últimas 20 decisiones

#### 4️⃣ **Analysis History**
- RSI trends over time
- Indicadores técnicos (MACD, Bollinger)
- Estadísticas de análisis
- Últimos 50 registros

#### 5️⃣ **System Stats**
- Conteo de registros (trades, decisiones, análisis)
- Database health check
- Tamaño de la BD
- Resumen por símbolo

---

## 🔍 Verificación de Integración

### Verificar que está guardando datos:

```python
from app.core.database import get_database_manager

db = get_database_manager()

# Verificar trades
trades = db.get_trades()
print(f"Total trades: {len(trades)}")

# Verificar decisiones AI
decisions = db.get_ai_decisions()
print(f"Total AI decisions: {len(decisions)}")

# Verificar análisis
analysis = db.get_analysis_history()
print(f"Total analysis: {len(analysis)}")
```

### Ubicación de la base de datos:
```
data/trading_history.db
```

### Ver contenido directo (SQLite):
```bash
sqlite3 data/trading_history.db
sqlite> SELECT COUNT(*) FROM trades;
sqlite> SELECT COUNT(*) FROM ai_decisions;
sqlite> SELECT COUNT(*) FROM analysis_history;
```

---

## 📤 Migrar Datos Históricos de MT5

Para importar trades anteriores a la BD:

```bash
# Últimos 30 días (default)
python migrate_trades.py

# Últimos 60 días
python migrate_trades.py --days 60

# Símbolos específicos
python migrate_trades.py --days 30 --symbols EURUSD,GBPUSD,XRPUSD
```

**Esto:**
- Conecta a MT5
- Obtiene deal history
- Agrupa por ticket (IN=open, OUT=close)
- Calcula P&L, commission, swap
- Guarda todo en BD

---

## 📊 Usar Datos para Backtesting

### Exportar a CSV
```python
from app.core.database import get_database_manager
import pandas as pd

db = get_database_manager()
trades = db.get_trades()

# Convertir a DataFrame
df = pd.DataFrame(trades)

# Filtrar trades cerrados
df_closed = df[df['status'] == 'closed']

# Exportar
df_closed.to_csv('trades_for_backtest.csv', index=False)
```

### Calcular métricas
```python
performance = db.get_performance_summary()
print(f"Win Rate: {performance['win_rate']:.1f}%")
print(f"Profit Factor: {performance['profit_factor']:.2f}")
print(f"Total P&L: ${performance['total_pnl']:.2f}")
```

### Analizar por engine
```python
decisions = db.get_ai_decisions()

enhanced = [d for d in decisions if d['engine_type'] == 'enhanced']
simple = [d for d in decisions if d['engine_type'] == 'simple']

print(f"Enhanced decisions: {len(enhanced)}")
print(f"Simple decisions: {len(simple)}")
```

---

## 🔄 Flujo de Datos

### Durante operación normal:

```
1. Bot ejecuta análisis técnico
   ↓ app/trading/integrated_analysis.py
   ↓ db.save_analysis()
   ↓ analysis_history table ✅

2. Smart router toma decisión
   ↓ app/ai/smart_decision_router.py
   ↓ db.save_ai_decision()
   ↓ ai_decisions table ✅

3. Si hay señal, ejecutar trade
   ↓ app/main.py place_market_order()
   ↓ db.save_trade()
   ↓ trades table (status='open') ✅

4. Si condición de cierre se cumple
   ↓ app/main.py close_position()
   ↓ db.update_trade()
   ↓ trades table (status='closed', profit updated) ✅

5. User accede a analytics
   ↓ app/ui/pages_database_analytics.py
   ↓ db.get_trades(), get_ai_decisions(), get_analysis_history()
   ↓ Plotly charts & tables ✅
```

---

## 📁 Archivos Modificados/Creados

### Creados (NUEVOS):
- ✅ `app/core/database.py` - DatabaseManager class
- ✅ `app/ui/pages_database_analytics.py` - Analytics dashboard (5 tabs)
- ✅ `init_database.py` - Script de inicialización
- ✅ `run_bot_with_db.py` - Script para iniciar bot con BD
- ✅ `DATABASE_SYSTEM.md` - Documentación técnica
- ✅ `DATABASE_USAGE.md` - Este archivo

### Modificados:
- ✅ `app/trading/integrated_analysis.py` - Agregado save_analysis()
- ✅ `app/ai/smart_decision_router.py` - Agregado save_ai_decision()
- ✅ `app/main.py` - Agregado save_trade() y update_trade()
- ✅ `app/ui_improved.py` - Agregada tab "📉 Analytics"

### Existentes (sin cambios):
- ✓ `app/ui/pages_history.py` - Ya tenía visualización
- ✓ `migrate_trades.py` - Ya existía

---

## 🎯 Casos de Uso

### 1️⃣ Monitoreo en Tiempo Real
```
→ Abre Analytics tab
→ Ve equidad curve actualizarse en vivo
→ Monitorea win rate, P&L
```

### 2️⃣ Análisis Diario
```
→ Bot corre durante el día
→ Al final, abre Analytics
→ Analiza performance por símbolo
→ Exporta reportes
```

### 3️⃣ Optimización de Parámetros
```
→ Descarga datos históricos a CSV
→ Corre backtesting con diferentes parámetros
→ Compara resultados
→ Ajusta el bot
```

### 4️⃣ Reentrenamiento de AI
```
→ Obtiene últimos N trades
→ Calcula features (RSI, MACD, sentimiento, etc.)
→ Etiqueta con resultado (win/loss)
→ Retrain Enhanced AI model
```

### 5️⃣ Reportes de Performance
```
→ Exports trades to Excel
→ Generate charts (equity curve, distribution)
→ Calculate metrics (Sharpe ratio, Sortino, etc.)
→ Send to stakeholders
```

---

## ⚙️ Configuración (Opcional)

### Cambiar ubicación de BD
```python
# En app/core/database.py, line 17:
db_path: str = "data/trading_history.db"  # Cambiar aquí
```

### Cambiar retención de datos
```python
# En app/core/database.py, método get_analysis_history:
# Agregar WHERE timestamp > DATE('now', '-90 days')
```

### Purgar datos antiguos
```python
db.delete_old_data(days=90)  # Mantener últimos 90 días
```

---

## 🐛 Troubleshooting

### Q: Base de datos no se inicializa
```bash
# Solución:
python init_database.py
```

### Q: No aparecen datos en Analytics tab
```bash
# Verificar:
1. ¿Bot está corriendo y generando trades?
2. ¿Ha pasado al menos 1 análisis/trade?
3. Esperar a que se complete primer ciclo (30s default)
```

### Q: Analytics tab muestra error
```
# Verificar logs:
tail -f logs/streamlit_*.log

# Reiniciar:
python init_database.py
streamlit run app/ui_improved.py
```

### Q: Database file muy grande
```bash
# Limpiar datos antiguos:
python -c "from app.core.database import get_database_manager; get_database_manager().delete_old_data(days=90)"
```

---

## 📈 Métricas Disponibles

### Por Trade:
- `ticket` - ID único
- `symbol` - Pair traded
- `open_price`, `close_price` - Entry/exit
- `profit` - P&L en dinero
- `commission`, `swap` - Costos
- `status` - open/closed
- `open_timestamp`, `close_timestamp` - Timestamps

### Por AI Decision:
- `symbol`, `timeframe` - Contexto
- `action` - BUY/SELL/HOLD
- `confidence` - 0-100%
- `engine_type` - enhanced/simple
- `data_sources` - Qué inputs usó
- `reasoning` - Por qué decidió

### Por Analysis:
- `rsi`, `macd`, `bollinger_position` - Indicadores
- `technical_signal` - UP/DOWN/NEUTRAL
- `sentiment_score` - -1.0 a +1.0
- `combined_score` - Overall

### Performance:
- `win_rate` - % de trades ganadores
- `profit_factor` - Ganancias/Pérdidas
- `total_pnl` - P&L acumulado
- `max_drawdown` - Pérdida máxima

---

## ✅ Checklist de Funcionalidad

- ✅ Base de datos inicializada
- ✅ Análisis guardados automáticamente
- ✅ Decisiones AI registradas
- ✅ Trades logueados (abiertos y cerrados)
- ✅ Analytics tab visible en UI
- ✅ Gráficos y tablas funcionando
- ✅ Filtros disponibles
- ✅ Métricas calculadas
- ✅ Migration script disponible
- ✅ Exportación a CSV posible

---

## 🚀 Próximos Pasos Recomendados

1. **Correr el bot** con `python run_bot_with_db.py`
2. **Dejar que recopile datos** durante 1-2 semanas
3. **Migrar datos históricos** con `python migrate_trades.py --days 90`
4. **Analizar en Analytics tab** para ver patterns
5. **Exportar para backtesting** y optimizar parámetros
6. **Retrain AI** con nuevos datos históricos

---

## 📞 Soporte

Para dudas sobre:
- **Esquema BD**: Ver `DATABASE_SYSTEM.md`
- **Integración código**: Ver archivos .py comentados
- **Visualización**: Ver `pages_database_analytics.py`
- **Datos**: Usar `init_database.py` para diagnosticar

---

**¡Sistema de Base de Datos Completamente Implementado! 🎉**

*Última actualización: 2024*
*Versión: 1.0 - Production Ready*
