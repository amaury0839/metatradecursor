# Notas de Despliegue - Streamlit Cloud

## Problema Resuelto: MetaTrader5 Opcional

El bot ahora funciona **sin MetaTrader5 instalado** en modo demo. Los cambios principales:

### Archivos Modificados

1. **`app/trading/mt5_client.py`**
   - Import de MetaTrader5 envuelto en `try/except`
   - Crea mock de MT5 si no está disponible
   - Funciona en modo demo automáticamente

2. **`app/trading/data.py`**
   - Import de MetaTrader5 envuelto en `try/except`
   - Genera datos simulados en modo demo

3. **`app/trading/execution.py`**
   - Import de MetaTrader5 envuelto en `try/except`
   - Simula órdenes en modo demo

4. **`requirements.txt`**
   - MetaTrader5 comentado (opcional)
   - No causa error si no está instalado

### Para Desplegar en Streamlit Cloud

1. **Asegúrate de que todos los cambios estén commiteados:**
```bash
git status
git add .
git commit -m "Make MetaTrader5 optional for demo mode"
```

2. **Push al repositorio:**
```bash
git push origin main
```

3. **Streamlit Cloud debería:**
   - Detectar automáticamente el push
   - Reinstalar dependencias (sin MetaTrader5)
   - Ejecutar el bot en modo demo

### Verificación

Después del push, el bot debería:
- ✅ Cargar sin errores de importación
- ✅ Mostrar "Demo Mode" en la UI
- ✅ Generar datos de mercado simulados
- ✅ Funcionar completamente sin MT5

### Variables de Entorno Necesarias

Mínimo requerido en Streamlit Cloud Secrets:
- `GEMINI_API_KEY` (requerido)

Opcionales:
- `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` (solo si tienes MT5)
- `NEWS_API_KEY` (opcional, para noticias reales)

### Troubleshooting

Si después del push sigue apareciendo el error:
1. Verifica que el commit se haya hecho correctamente
2. Revisa los logs de Streamlit Cloud
3. Intenta reiniciar la app desde el dashboard
4. Verifica que el archivo en GitHub tenga el try/except
