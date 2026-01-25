# Arquitectura: Local vs Streamlit Cloud

## Visión General

El bot ahora está dividido en dos componentes:

1. **Servidor Local (Trading Bot)**: Ejecuta el trading real con MT5
2. **UI Remota (Streamlit Cloud)**: Interfaz web que se conecta al servidor local

## Componentes

### 1. Servidor Local (`run_local_bot.py`)

**Ubicación**: Se ejecuta en tu máquina local

**Responsabilidades**:
- ✅ Conexión a MetaTrader 5
- ✅ Ejecución de trading (PAPER/LIVE)
- ✅ Loop de trading automático
- ✅ API REST para comunicación con UI
- ✅ Gestión de riesgo y ejecución

**Requisitos**:
- Python 3.11+
- MetaTrader 5 instalado
- Todas las dependencias del `requirements.txt`

**Ejecución**:
```bash
python run_local_bot.py
```

Esto inicia:
- El loop de trading en background
- El servidor API en `http://localhost:8000`

### 2. UI Remota (`app/main_ui.py`)

**Ubicación**: Streamlit Cloud

**Responsabilidades**:
- ✅ Visualización de datos
- ✅ Control remoto (kill switch, etc.)
- ✅ Configuración y monitoreo
- ❌ NO ejecuta trading directamente
- ❌ NO requiere MT5

**Requisitos**:
- Python 3.11+
- Solo dependencias de UI (sin MT5)
- Acceso al servidor local (túnel o red)

**Ejecución en Streamlit Cloud**:
- Configurar `app/main_ui.py` como entry point
- Configurar variable de entorno `TRADING_BOT_API_URL` (opcional)

## Configuración

### Servidor Local

1. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

2. **Configurar `.env`**:
```env
MT5_LOGIN=tu_login
MT5_PASSWORD=tu_password
MT5_SERVER=tu_servidor
GEMINI_API_KEY=tu_key
MODE=PAPER
```

3. **Ejecutar**:
```bash
python run_local_bot.py
```

El servidor estará disponible en `http://localhost:8000`

### UI en Streamlit Cloud

1. **Configurar entry point**:
   - En Streamlit Cloud, configurar `app/main_ui.py` como main file

2. **Configurar API URL** (opcional):
   - Variable de entorno: `TRADING_BOT_API_URL`
   - O configurar desde la UI en el sidebar

3. **Para acceso remoto** (si Streamlit Cloud no puede acceder a localhost):
   - Usar un túnel como ngrok:
     ```bash
     ngrok http 8000
     ```
   - Usar la URL de ngrok en Streamlit Cloud

## Flujo de Datos

```
┌─────────────────┐         HTTP/REST         ┌──────────────────┐
│                 │ ◄───────────────────────► │                  │
│  Streamlit UI   │                            │  Local Trading   │
│  (Cloud)        │                            │  Bot (API)       │
│                 │                            │                  │
│  - Visualización│                            │  - MT5 Connection│
│  - Control      │                            │  - Trading Logic │
│  - Config       │                            │  - Risk Mgmt     │
└─────────────────┘                            └──────────────────┘
```

## Ventajas de esta Arquitectura

1. **Seguridad**: El trading real solo corre localmente
2. **Flexibilidad**: UI accesible desde cualquier lugar
3. **Separación**: UI no necesita MT5 ni dependencias pesadas
4. **Escalabilidad**: Múltiples UIs pueden conectarse al mismo bot

## Modos de Operación

### Modo 1: Todo Local
```bash
# Terminal 1: Trading bot + API
python run_local_bot.py

# Terminal 2: UI local
streamlit run app/main_ui.py
```

### Modo 2: Local + Cloud
```bash
# Local: Trading bot + API
python run_local_bot.py

# Streamlit Cloud: UI remota
# Configurar app/main_ui.py como entry point
```

### Modo 3: Túnel para Acceso Remoto
```bash
# Local: Trading bot + API
python run_local_bot.py

# Local: Túnel ngrok
ngrok http 8000

# Streamlit Cloud: UI con URL de ngrok
# Configurar TRADING_BOT_API_URL=https://xxxx.ngrok.io
```

## API Endpoints

El servidor local expone estos endpoints:

- `GET /` - Health check
- `GET /status/connection` - Estado de conexión MT5
- `POST /connection/connect` - Conectar a MT5
- `POST /connection/disconnect` - Desconectar de MT5
- `GET /status/trading` - Estado de trading
- `GET /positions` - Posiciones abiertas
- `GET /decisions` - Decisiones recientes
- `GET /trades` - Trades recientes
- `POST /control/kill-switch/activate` - Activar kill switch
- `POST /control/kill-switch/deactivate` - Desactivar kill switch
- `GET /symbols` - Símbolos disponibles

## Troubleshooting

### UI no se conecta al servidor local

1. Verifica que el servidor local esté corriendo:
   ```bash
   curl http://localhost:8000/
   ```

2. Verifica la URL en la UI (sidebar)

3. Si Streamlit Cloud no puede acceder a localhost, usa un túnel

### Error de CORS

El servidor API ya tiene CORS configurado para permitir todas las conexiones. Si hay problemas, verifica la configuración en `app/api/server.py`.

### El trading no se ejecuta

Verifica que:
1. El servidor local esté corriendo
2. MT5 esté conectado
3. El scheduler esté activo
4. El kill switch no esté activo
