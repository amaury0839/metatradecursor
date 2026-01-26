# 🚀 Plan de Despliegue - AI Trading Bot

**Status:** ✅ UI Local funcionando (http://localhost:8501)  
**Fecha:** 26 de Enero de 2026  
**Base de Datos:** ✅ SQLite con 416 trades guardados

---

## 📋 Opciones de Despliegue

### **OPCIÓN 1: Despliegue Local (DESARROLLO/TESTING)**
**Tiempo:** 2 minutos | **Costo:** $0 | **Complejidad:** ⭐

```bash
# Terminal 1: Bot principal (trading loop)
python run_local_bot.py

# Terminal 2: Streamlit UI
python -m streamlit run app/ui_improved.py
```

**Características:**
- ✅ BD local SQLite (data/trading_history.db)
- ✅ Logs en tiempo real desde BD
- ✅ Acceso a MT5 local
- ✅ Sin latencia de red
- ✅ Fácil debugging

**Acceso:**
- UI: http://localhost:8501
- BD: data/trading_history.db (SQLite)

**Ventajas:** Desarrollo rápido, testing local, sin costos
**Limitaciones:** Solo accesible localmente, requiere tu PC encendida

---

### **OPCIÓN 2: Despliegue en Docker (PRODUCCIÓN LOCAL)**
**Tiempo:** 15 minutos | **Costo:** $0 | **Complejidad:** ⭐⭐

Infraestructura completa con Docker Compose:

```bash
# Construir y levantar contenedores
docker-compose up -d

# Ver logs
docker-compose logs -f ui
docker-compose logs -f bot
```

**Componentes:**
- 🤖 Bot Trading (Python + MT5)
- 🎯 UI Streamlit (puerto 8501)
- 💾 Base de datos compartida
- 📊 Logging persistente

**Archivos:**
- `Dockerfile.bot` - Imagen del trading bot
- `Dockerfile.ui` - Imagen de Streamlit
- `docker-compose.yml` - Orquestación

**Acceso:**
- UI: http://localhost:8501 (o ip-del-servidor:8501)
- BD: /data/trading_history.db (dentro del contenedor)

**Ventajas:** 
- Escalable
- Reproducible en cualquier máquina
- Fácil de actualizar
- Ambiente consistente

**Limitaciones:** 
- Requiere Docker instalado
- MT5 debe ser accesible desde el contenedor

---

### **OPCIÓN 3: Despliegue en la Nube (PRODUCCIÓN)**
**Tiempo:** 30 minutos | **Costo:** $5-50/mes | **Complejidad:** ⭐⭐⭐

#### **3A: Streamlit Cloud (RECOMENDADO PARA UI)**
```bash
# 1. Fork el repo en GitHub
# 2. Conectar a https://streamlit.io/cloud
# 3. Deploy automático en cada push
```

**Configuración (streamlit/config.toml):**
```toml
[client]
toolbarMode = "viewer"

[server]
headless = true
runOnSave = true
```

**Costo:** Gratis hasta 1GB/mes, $5 para límites más altos

---

#### **3B: AWS EC2 (RECOMENDADO PARA BOT)**
```bash
# 1. Crear instancia EC2 (Ubuntu 22.04)
# 2. SSH en la instancia
# 3. Clonar repo y correr:

cd /opt/metatrade
docker-compose up -d

# Exponer con systemd
sudo systemctl enable trading-bot
```

**Configuración mínima:**
- **Instancia:** t2.micro (gratis el primer año)
- **Storage:** 20GB SSD
- **OS:** Ubuntu 22.04 LTS
- **Security Group:** Abrir puerto 8501 solo para tu IP

**Costo:** Gratis (primer año) → $10-20/mes después

---

#### **3C: Heroku (NO RECOMENDADO - Caro)**
Deprecated en 2022. Usar alternativas.

---

#### **3D: DigitalOcean App Platform (ALTERNATIVA BUENA)**
```bash
# Deploy automático desde GitHub
# Interfaz simple
# Costo: $5-12/mes
```

---

## 🔒 Configuración de Seguridad por Opción

### Local
```python
# .streamlit/config.toml
[client]
toolbarMode = "viewer"
[server]
headless = true
```

### Docker
```dockerfile
# .dockerignore - no incluir:
.git
.gitignore
__pycache__
*.pyc
.env
```

### Cloud
```bash
# Variables de entorno (NO en código)
GEMINI_API_KEY=***
MT5_LOGIN=***
MT5_PASSWORD=***
MT5_SERVER=***
```

---

## 📊 Comparativa de Opciones

| Feature | Local | Docker | Cloud |
|---------|-------|--------|-------|
| **Costo** | $0 | $0 | $5-50/mes |
| **Velocidad Setup** | 2 min | 15 min | 30 min |
| **Escalabilidad** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Uptime 24/7** | ❌ | ✅ | ✅ |
| **Acceso remoto** | ❌ | ✅ | ✅ |
| **MT5 Local** | ✅ | ⚠️ | ❌ |
| **DB Persistente** | ✅ | ✅ | ✅ |
| **Monitoreo** | ❌ | ✅ | ✅ |

---

## 🎯 Mi Recomendación

Para un **trading bot en producción:**

1. **Fase 1 (Ahora):** Local + Docker para testing
   ```bash
   python run_local_bot.py  # En tu PC
   docker-compose up -d     # En Docker
   ```

2. **Fase 2 (Escalado):** AWS EC2 + Streamlit Cloud
   - EC2 para el bot (24/7)
   - Streamlit Cloud para UI (gratis)
   - BD compartida en EC2

3. **Fase 3 (Producción):** Multi-instancia + Load balancing
   - Múltiples bots por par
   - Load balancer
   - DB centralizada (PostgreSQL)

---

## ✅ Checklist de Despliegue

### Pre-Despliegue
- [x] BD funcionando (416 trades)
- [x] Logs desde BD (✅ pages_logs.py actualizado)
- [x] UI sin errores
- [x] Imports validados
- [ ] Variables de entorno configuradas
- [ ] Conexión MT5 verificada en servidor destino
- [ ] Backups de BD

### Durante Despliegue
- [ ] Pull último código
- [ ] Verificar BD
- [ ] Iniciar servicios
- [ ] Monitorear logs por 5 min
- [ ] Verificar que logs se graban

### Post-Despliegue
- [ ] Health check
- [ ] Test trade pequeño
- [ ] Verificar alertas
- [ ] Documentar configuración final

---

## 🆘 Troubleshooting

### "Port 8501 already in use"
```powershell
netstat -ano | findstr 8501
Stop-Process -Id [PID] -Force
```

### BD corrupta o vacía
```bash
python -c "from app.core.database import init_database; init_database()"
```

### MT5 no conecta desde Docker
```dockerfile
# Usar network_mode: host en docker-compose.yml
network_mode: "host"
```

### Streamlit Cloud: ModuleNotFoundError
```bash
# Crear requirements.txt con todas las dependencias
pip freeze > requirements.txt
```

---

## 📞 Soporte

Para cada opción:
- **Local:** Revisar logs con `python run_local_bot.py`
- **Docker:** `docker-compose logs -f`
- **Cloud:** Panel de control del proveedor

---

**¿Cuál opción prefieres? Puedo guiarte paso a paso.**
