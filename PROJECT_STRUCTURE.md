# Estructura del Proyecto

```
ai_forex_bot/
├── app/
│   ├── __init__.py
│   ├── main.py                      # Entry point Streamlit
│   │
│   ├── ui/                          # Interfaz Streamlit
│   │   ├── __init__.py
│   │   ├── pages_dashboard.py      # Dashboard principal
│   │   ├── pages_config.py          # Configuración
│   │   ├── pages_strategy.py        # Estrategia
│   │   ├── pages_risk.py             # Gestión de riesgo
│   │   ├── pages_news.py             # Noticias y sentimiento
│   │   └── pages_logs.py             # Logs y auditoría
│   │
│   ├── core/                        # Módulos core
│   │   ├── __init__.py
│   │   ├── config.py                 # Configuración (Pydantic)
│   │   ├── state.py                  # Estado y persistencia
│   │   ├── logger.py                 # Logging estructurado
│   │   └── scheduler.py              # Scheduler de trading loop
│   │
│   ├── trading/                     # Módulos de trading
│   │   ├── __init__.py
│   │   ├── mt5_client.py            # Cliente MetaTrader 5
│   │   ├── data.py                  # Fetching de datos OHLC
│   │   ├── execution.py            # Ejecución de órdenes
│   │   ├── risk.py                  # Gestión de riesgo
│   │   ├── portfolio.py            # Gestión de portfolio
│   │   └── strategy.py              # Estrategia técnica
│   │
│   ├── ai/                          # Módulos AI
│   │   ├── __init__.py
│   │   ├── gemini_client.py        # Cliente Gemini API
│   │   ├── decision_engine.py      # Motor de decisiones
│   │   ├── schemas.py              # Schemas Pydantic
│   │   └── prompt_templates.py    # Templates de prompts
│   │
│   ├── news/                        # Módulos de noticias
│   │   ├── __init__.py
│   │   ├── provider_base.py        # Clase base provider
│   │   ├── provider_stub.py        # Provider stub (mock)
│   │   ├── provider_newsapi.py    # Provider NewsAPI
│   │   └── sentiment.py            # Análisis de sentimiento
│   │
│   └── backtest/                    # Backtesting
│       ├── __init__.py
│       ├── runner.py               # Runner de backtest
│       └── metrics.py              # Cálculo de métricas
│
├── data/                            # Datos
│   └── sample_ohlc.csv             # Datos de muestra
│
├── tests/                           # Tests
│   ├── __init__.py
│   ├── test_risk.py                # Tests de riesgo
│   ├── test_decision_schema.py     # Tests de schemas
│   └── test_strategy_signals.py    # Tests de estrategia
│
├── logs/                            # Logs (generado automáticamente)
│
├── .env.example                     # Ejemplo de configuración
├── .gitignore
├── requirements.txt                 # Dependencias Python
├── pytest.ini                      # Configuración pytest
├── verify_setup.py                 # Script de verificación
├── run_streamlit.bat               # Script Windows
├── run_streamlit.sh                # Script Linux/Mac
├── README.md                        # Documentación principal
└── PROJECT_STRUCTURE.md            # Este archivo
```

## Flujo de Ejecución

1. **Inicialización**: `app/main.py` carga configuración y conecta a MT5
2. **Scheduler**: `app/core/scheduler.py` ejecuta el loop de trading cada X segundos
3. **Trading Loop** (`main_trading_loop` en `app/main.py`):
   - Obtiene datos OHLC para cada símbolo
   - Calcula señales técnicas (`app/trading/strategy.py`)
   - Obtiene sentimiento de noticias (`app/news/sentiment.py`)
   - Solicita decisión a Gemini (`app/ai/decision_engine.py`)
   - Valida riesgo (`app/trading/risk.py`)
   - Ejecuta orden si es válida (`app/trading/execution.py`)
   - Guarda auditoría (`app/core/state.py`)

## Componentes Principales

### Core
- **config.py**: Gestión de configuración con Pydantic Settings
- **state.py**: Estado runtime y persistencia SQLite
- **logger.py**: Logging estructurado con structlog
- **scheduler.py**: Loop de trading con threading

### Trading
- **mt5_client.py**: Wrapper para MetaTrader5 API
- **data.py**: Fetching y caching de datos OHLC
- **execution.py**: Ejecución de órdenes (PAPER/LIVE)
- **risk.py**: Validaciones de riesgo y position sizing
- **portfolio.py**: Tracking de posiciones abiertas
- **strategy.py**: Indicadores técnicos (EMA, RSI, ATR)

### AI
- **gemini_client.py**: Cliente para Google Gemini API
- **decision_engine.py**: Combina señales técnicas + AI + noticias
- **schemas.py**: Validación estricta de decisiones con Pydantic
- **prompt_templates.py**: Construcción de prompts para Gemini

### News
- **provider_base.py**: Interface para proveedores de noticias
- **provider_stub.py**: Provider mock para desarrollo
- **provider_newsapi.py**: Integración con NewsAPI.org
- **sentiment.py**: Análisis de sentimiento usando Gemini

### UI
- **pages_dashboard.py**: Métricas, posiciones, decisiones recientes
- **pages_config.py**: Configuración de MT5, AI, noticias
- **pages_strategy.py**: Configuración de estrategia técnica
- **pages_risk.py**: Parámetros de riesgo
- **pages_news.py**: Visualización de noticias y sentimiento
- **pages_logs.py**: Auditoría de decisiones y trades
