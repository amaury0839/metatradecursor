# 🎯 PASOS PARA CONECTAR EL BOT A MT5

## Situación Actual ✅
- ✅ MetaTrader5 package instalado correctamente
- ✅ Bot corriendo y escuchando en puerto 8000
- ❌ MT5 no responde a conexión IPC (necesita configuración)

---

## 📋 PASOS A SEGUIR (5 minutos)

### PASO 1: Abre MetaTrader 5
- Asegúrate que MT5 esté **completamente abierto**
- Verifica que ya estés **logueado** en tu cuenta (5045373902)

### PASO 2: Ve a Tools → Options
```
En la ventana principal de MT5:
  ├─ Menú "Tools" (superior)
  └─ Selecciona "Options"
```

### PASO 3: Abre pestaña "Expert Advisors"
```
En la ventana de Options que se abre:
  └─ Busca la pestaña "Expert Advisors" (debería ser la cuarta o quinta)
```

### PASO 4: Habilita las opciones requeridas
Dentro de la pestaña "Expert Advisors", MARCA estas casillas:

**CRÍTICO (OBLIGATORIO):**
- ☑️ **"Allow automated trading"** ← ESTA ES LA MÁS IMPORTANTE
  
**RECOMENDADO (OPCIONAL):**
- ☑️ "Allow DLL imports"
- ☑️ "Allow imports"

### PASO 5: Aplica cambios
- Haz clic en el botón **"OK"** para guardar

### PASO 6: REINICIA MT5
- **CIERRA** completamente MT5
- Espera 5 segundos
- **ABRE** MT5 de nuevo
- Verifica que inicies sesión automáticamente

### PASO 7: El bot se conectará automáticamente
Una vez MT5 esté reabierto, el bot se conectará automáticamente en el siguiente ciclo.

---

## ✅ RESULTADO ESPERADO

Cuando funcione, verás en los logs del bot:

```
✅ MT5 conectado exitosamente
📊 Cuenta: 5045373902
💰 Balance: 10000.00 USD
📈 Equity: 10000.00 USD
```

---

## ⚠️ TROUBLESHOOTING

Si aún no conecta después de habilitar "Allow automated trading":

1. **Verifica que está habilitado:** 
   - Vuelve a Tools → Options → Expert Advisors
   - Confirma que "Allow automated trading" está ☑️ (con checkmark)

2. **Reinicia MT5:**
   - Cierra completamente MT5
   - Abre de nuevo
   - Espera a que se cargue completamente

3. **Verifica que MT5 está abierto:**
   - MT5 NO puede estar minimizado
   - Debe estar visible en pantalla

4. **Executa el test:**
   - `.\.venv\Scripts\python.exe test_mt5_connection.py`
   - Verá el estado de la conexión

---

**Cuando lo hagas, el bot comenzará a ejecutar operaciones en tiempo real con señales técnicas y fallback a Gemini cuando esté disponible.**
