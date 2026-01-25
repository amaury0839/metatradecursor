# Guía de Despliegue - Local vs Cloud

## Arquitectura Dividida

El bot ahora tiene dos modos de operación:

### 1. Modo Local Completo (`app/main.py`)
- Ejecuta trading real con MT5
- Incluye UI completa
- Requiere MT5 instalado

### 2. Modo UI Remota (`app/main_ui.py`)
- Solo UI, sin trading
- Se conecta a servidor local vía API
- Para Streamlit Cloud

## Despliegue en Streamlit Cloud

### Paso 1: Configurar Entry Point

En Streamlit Cloud, configura:
- **Main file**: `app/main_ui.py` (NO `app/main.py`)

### Paso 2: Variables de Entorno

Configura en Streamlit Cloud Secrets:
```
TRADING_BOT_API_URL=http://localhost:8000
```

O déjalo vacío y configura desde la UI.

### Paso 3: Ejecutar Servidor Local

En tu máquina local:
```bash
python run_local_bot.py
```

Esto inicia:
- Trading bot con MT5
- API server en puerto 8000

### Paso 4: Acceso Remoto (Opcional)

Si Streamlit Cloud no puede acceder a `localhost:8000`, usa un túnel:

```bash
# Instalar ngrok
# https://ngrok.com/

# Crear túnel
ngrok http 8000

# Usar la URL de ngrok en Streamlit Cloud
# Ejemplo: https://abc123.ngrok.io
```

## Archivos Clave

- `app/main.py` - UI local completa (con trading)
- `app/main_ui.py` - UI remota (solo visualización)
- `app/api/server.py` - API server para comunicación
- `app/api_client/client.py` - Cliente API para UI remota
- `run_local_bot.py` - Script para ejecutar bot local + API

## Flujo Recomendado

1. **Desarrollo/Testing Local**:
   ```bash
   streamlit run app/main.py
   ```

2. **Producción Local + Cloud UI**:
   ```bash
   # Terminal 1: Bot local
   python run_local_bot.py
   
   # Streamlit Cloud: UI remota
   # Configurar app/main_ui.py como entry point
   ```

## Notas Importantes

- La UI remota NO requiere MetaTrader5
- El trading solo se ejecuta en el servidor local
- La API debe ser accesible desde Streamlit Cloud (usar túnel si es necesario)
- El servidor local debe estar corriendo para que la UI funcione
