# AI Forex Trading Bot

Bot de trading algorítmico para Forex con interfaz Streamlit, ejecución en MetaTrader 5, y decisiones asistidas por Gemini API + análisis de sentimiento de noticias.

## ⚠️ DISCLAIMER DE RIESGO

**Este software es solo para fines educativos y de investigación. El trading de divisas conlleva un riesgo significativo de pérdida de capital. No se proporciona ningún consejo financiero. Use bajo su propio riesgo. El autor no se hace responsable de pérdidas financieras.**

## Arquitectura

El bot está dividido en dos componentes:

1. **Servidor Local**: Ejecuta trading real con MT5 (requiere MT5 instalado)
2. **UI Remota**: Interfaz web para Streamlit Cloud (solo visualización)

Ver [README_LOCAL_VS_CLOUD.md](README_LOCAL_VS_CLOUD.md) para detalles completos.

## Características

- ✅ Conexión a MetaTrader 5 (modo PAPER por defecto, LIVE con confirmación)
- ✅ Interfaz Streamlit (local o remota)
- ✅ Estrategia híbrida: señales técnicas + decisiones asistidas por Gemini
- ✅ Análisis de sentimiento de noticias
- ✅ Gestión de riesgo profesional
- ✅ Auditoría completa de decisiones
- ✅ Backtesting básico
- ✅ API REST para acceso remoto

## Instalación Rápida

### Opción 1: Todo Local

```bash
pip install -r requirements.txt
streamlit run app/main.py
```

### Opción 2: Local + Cloud UI

**Local (Bot + API)**:
```bash
pip install -r requirements.txt
python run_local_bot.py
```

**Streamlit Cloud (UI)**:
- Entry point: `app/main_ui.py`
- Requirements: `requirements_cloud.txt` (sin MT5)

Ver [QUICK_START.md](QUICK_START.md) para guía completa.

## Requisitos

### Servidor Local
- Python 3.11+
- MetaTrader 5 instalado
- API Key de Google Gemini
- (Opcional) API Key de NewsAPI

### UI Remota (Streamlit Cloud)
- Python 3.11+
- API Key de Google Gemini (para algunas funciones)
- Acceso al servidor local (túnel si es necesario)

## Configuración

1. **Copiar `.env.example` a `.env`**
2. **Configurar variables**:
   - `GEMINI_API_KEY` (requerido)
   - `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` (solo local)
   - `MODE=PAPER` (default)

## Uso

### Modo Local Completo

```bash
streamlit run app/main.py
```

### Modo Local + Cloud

1. **Iniciar bot local**:
```bash
python run_local_bot.py
```

2. **Configurar Streamlit Cloud**:
   - Entry point: `app/main_ui.py`
   - Variable opcional: `TRADING_BOT_API_URL`

3. **Acceso remoto** (si es necesario):
```bash
ngrok http 8000
# Usar URL de ngrok en Streamlit Cloud
```

## Documentación

- [README_LOCAL_VS_CLOUD.md](README_LOCAL_VS_CLOUD.md) - Arquitectura detallada
- [QUICK_START.md](QUICK_START.md) - Guía rápida
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Guía de despliegue
- [README_DEMO.md](README_DEMO.md) - Modo demo

## Estructura

```
app/
├── main.py              # UI local completa
├── main_ui.py           # UI remota (Streamlit Cloud)
├── api/                 # API server
├── api_client/          # Cliente API
├── ui/                  # Páginas UI (auto-detectan modo)
├── trading/             # Lógica de trading
├── ai/                  # Gemini y decisiones
└── ...
```

## Licencia

Este proyecto es de código abierto para fines educativos.
