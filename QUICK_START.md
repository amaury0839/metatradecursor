# Quick Start Guide

## Opción 1: Todo Local (Desarrollo/Testing)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar .env con tus credenciales MT5 y Gemini

# Ejecutar UI completa local
streamlit run app/main.py
```

## Opción 2: Local + Cloud UI (Producción)

### Paso 1: Ejecutar Bot Local

```bash
# En tu máquina local
python run_local_bot.py
```

Esto inicia:
- Trading bot con MT5
- API server en http://localhost:8000

### Paso 2: Configurar Streamlit Cloud

1. **Entry Point**: `app/main_ui.py`
2. **Variables de entorno** (opcional):
   - `TRADING_BOT_API_URL=http://localhost:8000`

### Paso 3: Acceso Remoto (si es necesario)

Si Streamlit Cloud no puede acceder a localhost:

```bash
# Usar ngrok para crear túnel
ngrok http 8000

# Usar la URL de ngrok en Streamlit Cloud
# Ejemplo: https://abc123.ngrok.io
```

## Archivos Clave

- `app/main.py` - UI local completa
- `app/main_ui.py` - UI remota (Streamlit Cloud)
- `app/api/server.py` - API server
- `run_local_bot.py` - Bot local + API

## Verificación

### Local
- Abre http://localhost:8501 (Streamlit)
- Deberías ver la UI completa

### Cloud
- Abre tu app de Streamlit Cloud
- Deberías ver "Connected to Trading Bot" en el sidebar
- Si no, verifica que el bot local esté corriendo
