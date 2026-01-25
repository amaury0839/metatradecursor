# Sistema de Logging de Análisis en Tiempo Real

## Descripción

Se ha agregado un nuevo sistema de logging que registra todos los análisis que realiza el bot de trading, permitiendo visualizar en tiempo real:

- **Análisis Técnicos**: Señales de indicadores técnicos (RSI, EMA, etc.)
- **Análisis de IA**: Decisiones del motor de inteligencia artificial (Gemini)
- **Ejecución de Órdenes**: Resultados de la ejecución de trades
- **Comprobaciones de Riesgo**: Validación de condiciones de riesgo

## Nuevas Características

### 1. **AnalysisLogger** (`app/core/analysis_logger.py`)

Un sistema robusto para registrar análisis con:
- Thread-safe: Puede usarse desde múltiples threads
- Búsqueda y filtrado: Filtrar por símbolo, tipo de análisis, estado
- Límite configurable: Máximo de entradas en memoria (por defecto 500)
- Acceso a datos: Obtener logs globales o por símbolo

#### Métodos principales:

```python
# Registrar análisis técnico
analysis_logger.log_technical_analysis(
    symbol="EURUSD",
    timeframe="M15",
    signal="BUY",
    rsi=35.2,
    ema_signal="Alcista"
)

# Registrar decisión de IA
analysis_logger.log_ai_analysis(
    symbol="EURUSD",
    timeframe="M15",
    decision="BUY",
    confidence=0.85,
    reasoning="Tendencia alcista confirmada"
)

# Registrar ejecución
analysis_logger.log_execution(
    symbol="EURUSD",
    action="BUY 0.1 lots",
    status="SUCCESS"
)

# Registrar comprobación de riesgo
analysis_logger.log_risk_check(
    symbol="EURUSD",
    check_name="Daily Loss Limit",
    passed=True
)

# Obtener logs recientes
logs = analysis_logger.get_recent_logs(count=50)

# Obtener logs filtrados
logs = analysis_logger.get_logs(
    symbol="EURUSD",
    analysis_type="TECHNICAL",
    status="SUCCESS"
)

# Resumen de símbolo
summary = analysis_logger.get_symbol_summary("EURUSD")
```

### 2. **Nueva Página "Análisis en Tiempo Real"** (`app/ui/pages_analysis.py`)

Una interfaz completa para visualizar análisis con 4 vistas:

#### **Vista Tabla**
- Tabla con todas las columnas de análisis
- Filtros por estado (SUCCESS, WARNING, ERROR)
- Colores para cada estado

#### **Vista Timeline**
- Representación cronológica de análisis
- Iconos por tipo de análisis
- Expandible para ver detalles

#### **Vista Por Símbolo**
- Resumen rápido de análisis por símbolo
- Desglose por tipo
- Detalles expandibles para cada análisis

#### **Vista Por Tipo**
- Agrupación por tipo de análisis (TECHNICAL, AI, EXECUTION, RISK)
- Estadísticas por tipo
- Detalles de cada análisis

### 3. **Integración en el Bot Principal** (`app/main.py`)

El trading loop ahora registra automáticamente:

- **Análisis Técnico**: Cuando se calcula RSI, EMA y se genera una señal
- **Decisión de IA**: La decisión del motor Gemini con confianza
- **Errores**: Cuando hay problemas en análisis o decisiones
- **Comprobaciones de Riesgo**: Si pasan o fallan las validaciones
- **Ejecución**: Resultado de la colocación de órdenes

## Cómo Acceder

1. Abre la UI de Streamlit: `http://localhost:8501`
2. En el menú de navegación, selecciona **"Análisis en Tiempo Real"**
3. Usa los filtros para ver los análisis que te interesan

## Ejemplo de Uso

```python
from app.core.analysis_logger import get_analysis_logger

# Obtener la instancia global
logger = get_analysis_logger()

# Registrar un análisis
logger.log_technical_analysis(
    symbol="GBPUSD",
    timeframe="M15",
    signal="SELL",
    rsi=72.5,
    ema_signal="Bajista",
    details={"atr": 0.0045, "ema_cross": "DOWN"}
)

# Ver últimos análisis
logs = logger.get_recent_logs(count=20)
for log in logs:
    print(f"{log['timestamp']} - {log['symbol']}: {log['message']}")
```

## Tipos de Análisis

### TECHNICAL (📊)
Análisis de indicadores técnicos:
- Señal: BUY, SELL, HOLD
- RSI: Valor del Índice de Fuerza Relativa
- EMA: Señal de cruce de medias móviles

### AI (🤖)
Decisiones del motor de IA (Gemini):
- Decisión: BUY, SELL, HOLD
- Confianza: Porcentaje de confianza (0-100%)
- Razonamiento: Explicación de la decisión

### EXECUTION (💹)
Resultados de ejecución de órdenes:
- Acción: Tipo y tamaño de orden
- Precios: Entrada, SL, TP
- Estado: SUCCESS o ERROR

### RISK (⚠️)
Comprobaciones de riesgo:
- Nombre: Tipo de comprobación
- Resultado: PASSED o BLOCKED
- Razón: Por qué pasó o falló

## Estados

- **SUCCESS** (✅): Operación exitosa
- **WARNING** (⚠️): Operación bloqueada pero normal
- **ERROR** (❌): Error en la operación

## Información Almacenada

Cada análisis registra:
- **Timestamp**: Hora exacta
- **Symbol**: Par de divisas
- **Timeframe**: Marco de tiempo (M15, H1, etc.)
- **Analysis Type**: Tipo de análisis
- **Status**: Estado del análisis
- **Message**: Mensaje legible
- **Details**: Diccionario con detalles adicionales

## Performance

- Máximo de 500 entradas en memoria (configurable)
- Thread-safe para uso concurrente
- Búsqueda O(n) en memoria
- Overhead mínimo al registrar

## Próximas Mejoras

- Persistencia en base de datos SQLite
- Exportación a CSV/Excel
- Gráficos de análisis en tiempo
- Webhooks para notificaciones
- API REST para acceder a logs
