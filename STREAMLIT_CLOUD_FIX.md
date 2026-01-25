# Fix para Streamlit Cloud - MetaTrader5 Opcional

## Problema
Streamlit Cloud muestra error: `ModuleNotFoundError: No module named 'MetaTrader5'` en la línea 3 de `mt5_client.py`

## Solución Aplicada
El archivo `app/trading/mt5_client.py` ahora tiene el import de MetaTrader5 envuelto en `try/except` para que sea opcional.

## Verificación Local
El archivo local está correcto. Verifica que en tu repositorio local, `app/trading/mt5_client.py` tenga:

```python
# Líneas 10-23 aproximadamente
MT5_AVAILABLE = False
try:
    import MetaTrader5 as mt5  # type: ignore
    MT5_AVAILABLE = True
except (ImportError, ModuleNotFoundError, OSError):
    MT5_AVAILABLE = False
    class MockMT5:
        pass
    mt5 = MockMT5()  # type: ignore
```

**NO debe tener** `import MetaTrader5 as mt5` directamente en la línea 3.

## Pasos para Actualizar Streamlit Cloud

1. **Verifica que el archivo local esté correcto:**
```bash
# En Windows PowerShell
Get-Content app\trading\mt5_client.py | Select-Object -First 25
```

Deberías ver el `try/except` alrededor de la línea 13-23.

2. **Haz commit y push:**
```bash
git add app/trading/mt5_client.py
git commit -m "Fix: Make MetaTrader5 optional for Streamlit Cloud"
git push origin main
```

3. **Verifica en GitHub:**
   - Ve a tu repositorio en GitHub
   - Abre `app/trading/mt5_client.py`
   - Verifica que las líneas 13-23 tengan el `try/except`
   - **NO debe haber** `import MetaTrader5 as mt5` en la línea 3

4. **Reinicia Streamlit Cloud:**
   - Ve al dashboard de Streamlit Cloud
   - Haz clic en "Reboot app" o "Restart"
   - Espera a que se recargue

## Si el Error Persiste

Si después del push y reinicio sigue el error:

1. **Verifica que el commit se haya subido:**
   - Revisa el historial de commits en GitHub
   - Asegúrate de que el último commit incluya los cambios

2. **Fuerza una recarga:**
   - Haz un pequeño cambio (agrega un comentario)
   - Haz commit y push nuevamente
   - Esto fuerza a Streamlit Cloud a recargar

3. **Verifica la rama:**
   - Asegúrate de que Streamlit Cloud esté apuntando a la rama correcta (main/master)
   - Verifica en la configuración de Streamlit Cloud

## Archivos que Deben Tener try/except

- ✅ `app/trading/mt5_client.py` (líneas 13-23)
- ✅ `app/trading/data.py` (líneas 10-24)
- ✅ `app/trading/execution.py` (líneas 12-26)

Todos estos archivos deben tener el import de MetaTrader5 envuelto en `try/except`.
