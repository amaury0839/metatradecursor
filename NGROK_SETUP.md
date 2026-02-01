# 🌐 A-Bot Ngrok Setup Guide

## Descripción
Ngrok permite exponer tu A-Bot al internet de forma segura sin necesidad de configurar puertos en tu router.

## Requisitos Previos
- A-Bot API ejecutándose en puerto 8002
- A-Bot Dashboard ejecutándose en puerto 8504
- Conexión a internet

## Instalación de Ngrok

### Opción 1: Instalación Automática (Windows PowerShell)
```powershell
.\setup_ngrok.ps1
```

### Opción 2: Instalación Manual
1. Descarga Ngrok desde: https://ngrok.com/download
2. Extrae el archivo en una carpeta
3. Agrega la carpeta a tu PATH (Variables de entorno)

## Configuración de Autenticación

### 1. Obtén tu Token
1. Ve a: https://dashboard.ngrok.com/auth/your-authtoken
2. Si no tienes cuenta, crea una (es gratis)
3. Copia tu token de autenticación

### 2. Configura Ngrok
```bash
ngrok config add-authtoken tu_token_aqui
```

## Inicio de Túneles

### Opción 1: Iniciar Ambos Túneles
```bash
ngrok start --all
```

### Opción 2: Iniciar API Solo
```bash
ngrok http 8002
```

### Opción 3: Iniciar Dashboard Solo
```bash
ngrok http 8504
```

### Opción 4: Usar Script de Inicio (Windows)
```bash
.\launch_ngrok.bat
```

## Qué Verás

Después de ejecutar Ngrok, verás algo como:

```
ngrok                                           (Ctrl+C to quit)

Session Status                online
Account                       tu_email@ejemplo.com
Version                       3.3.0
Region                        us (United States)
Forwarding                    https://abc123def456.ngrok.io -> http://localhost:8002
Forwarding                    https://xyz789uvw456.ngrok.io -> http://localhost:8504

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

## URLs Públicas

Una vez que Ngrok está ejecutándose:

- **A-Bot API**: `https://abc123def456.ngrok.io`
- **A-Bot Dashboard**: `https://xyz789uvw456.ngrok.io`

Estas URLs son públicas y pueden ser compartidas para acceder a tu A-Bot desde cualquier lugar.

## Panel de Inspección

Ngrok proporciona un panel de inspección en:
```
http://localhost:4040
```

Aquí puedes:
- Ver todos los requests en tiempo real
- Inspeccionar headers y body
- Replaying requests
- Ver estadísticas de conexión

## Ejemplo de Uso Completo

### Terminal 1: Ejecutar A-Bot API
```powershell
cd c:\Users\Shadow\Downloads\Metatrade
.\\.venv\Scripts\python.exe -m uvicorn app.api.server:app --host 0.0.0.0 --port 8002
```

### Terminal 2: Ejecutar A-Bot Dashboard
```powershell
cd c:\Users\Shadow\Downloads\Metatrade
.\.venv\Scripts\streamlit.exe run app/main_ui.py --server.port 8504
```

### Terminal 3: Ejecutar Ngrok
```powershell
ngrok start --all
```

Ahora tienes A-Bot expuesto públicamente!

## Trucos y Tips

### 1. URLs Estáticas (Plan Pago)
Con el plan Pro/Enterprise, puedes crear URLs estáticas que nunca cambian.

### 2. Autenticación Básica
Para proteger tus túneles:
```bash
ngrok http 8504 --basic-auth "usuario:contraseña"
```

### 3. Límite de Bandwidth
```bash
ngrok http 8504 --limit-conn 10 --limit-rate 100k
```

### 4. Logs Detallados
```bash
ngrok http 8504 --log stdout --log-format json
```

## Resolución de Problemas

### "Command not found: ngrok"
- Asegúrate de haber agregado Ngrok a tu PATH
- Reinicia PowerShell/CMD
- Verifica: `ngrok --version`

### "Error: Failed to authenticate"
- Verifica tu token: `ngrok config check`
- Reapply token: `ngrok config add-authtoken tu_token`
- Recrea cuenta si es necesario

### "Cannot connect to localhost:8002"
- Verifica que A-Bot API está ejecutándose
- Comprueba el puerto: `netstat -ano | findstr :8002`
- Reinicia el servicio

### Ngrok se desconecta frecuentemente
- Verifica tu conexión a internet
- Aumenta timeout: `ngrok http 8504 --ws-ping-interval=20s`
- Contacta a Ngrok si persiste

## Seguridad

### Recomendaciones
1. ✅ Usa siempre HTTPS (Ngrok lo hace automáticamente)
2. ✅ Protege tu token de autenticación
3. ✅ No compartas URLs públicas en foros públicos
4. ✅ Considera usar autenticación básica
5. ✅ Revisa los logs de acceso regularmente

### Mejores Prácticas
- Regenera tokens regularmente
- Usa firewall para limitar IPs
- Monitorea el panel de inspección
- Limpia sesiones antiguas en dashboard.ngrok.com

## Documentación Oficial
- Docs: https://ngrok.com/docs
- Community: https://ngrok.com/docs/using-ngrok/ngrok-community
- API: https://ngrok.com/docs/api

---

¡A-Bot ahora está expuesto de forma segura al internet! 🚀
