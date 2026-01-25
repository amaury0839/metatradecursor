# Modo Demo/Streamlit Cloud

Este bot puede ejecutarse en **modo demo** sin necesidad de tener MetaTrader 5 instalado. Esto es útil para:

- Desarrollo y pruebas
- Demostraciones
- Ejecución en Streamlit Cloud
- Entornos donde MT5 no está disponible

## Características del Modo Demo

- ✅ Funciona sin MetaTrader 5 instalado
- ✅ Simula conexión a MT5
- ✅ Genera datos de mercado simulados
- ✅ Todas las funciones de UI disponibles
- ✅ Estrategia y análisis AI funcionan normalmente
- ⚠️ Las órdenes se simulan (no se ejecutan realmente)

## Instalación para Demo

```bash
# Instalar dependencias (sin MetaTrader5)
pip install -r requirements.txt

# MetaTrader5 se omite automáticamente si no está disponible
```

## Uso

El bot detecta automáticamente si MetaTrader5 está disponible:

- **Con MT5**: Se conecta normalmente y ejecuta órdenes reales (en modo LIVE) o simuladas (en modo PAPER)
- **Sin MT5**: Ejecuta en modo demo con datos simulados

```bash
streamlit run app/main.py
```

## Notas

- En modo demo, todas las órdenes se simulan
- Los datos de mercado son generados aleatoriamente
- La funcionalidad de análisis AI y estrategia funciona normalmente
- Para trading real, necesitas instalar MetaTrader 5 y el paquete Python correspondiente
