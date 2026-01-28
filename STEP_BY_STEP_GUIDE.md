#!/usr/bin/env python3
"""
🎯 PASO A PASO - CÓMO EMPEZAR CON EL SISTEMA OPTIMIZADO
Complete step-by-step guide to get the system running
"""

STEP_BY_STEP = """
╔══════════════════════════════════════════════════════════════════════════╗
║                    🚀 SISTEMA OPTIMIZADO - GUÍA PASO A PASO             ║
╚══════════════════════════════════════════════════════════════════════════╝

OPCIÓN 1: SISTEMA COMPLETO (RECOMENDADO)
═════════════════════════════════════════════════════════════════════════

PASO 1: Abre PowerShell o Terminal
   → Click derecho en el escritorio → Open PowerShell here
   → O navega a: c:\\Users\\Shadow\\Downloads\\Metatrade

PASO 2: Ejecuta el comando
   $ python run_optimized_system.py
   
   ✅ Esto inicia:
      ✓ Bot de trading (LIVE, M15/M5)
      ✓ Servidor API (puerto 8000)
      ✓ Dashboard UI (puerto 8501)
      ✓ Optimización continua (cada 60 min)
      ✓ Monitoreo de performance

PASO 3: Espera a que se inicie (~10 segundos)
   Verás mensajes como:
   - "Trading bot started"
   - "Continuous optimization started"
   - "API Server started"
   - "Streamlit UI started"

PASO 4: Abre el Dashboard
   → Opción A: Click en el link http://localhost:8501
   → Opción B: Copia y pega en tu navegador: http://localhost:8501

PASO 5: ¡Disfrutá!
   ✅ Dashboard principal con equity en tiempo real
   ✅ Análisis técnico en tiempo real
   ✅ Optimizador con recomendaciones IA
   ✅ Historial de operaciones
   ✅ Configuración del bot

LISTO! El sistema está corriendo.

═════════════════════════════════════════════════════════════════════════

OPCIÓN 2: SOLO DASHBOARD
═════════════════════════════════════════════════════════════════════════

Si solo quieres testear el Dashboard (sin bot de fondo):

PASO 1: Abre PowerShell/Terminal en c:\\Users\\Shadow\\Downloads\\Metatrade

PASO 2: Ejecuta
   $ streamlit run app/ui_optimized.py

PASO 3: Se abrirá automáticamente en http://localhost:8501

✅ Podrás ver el dashboard, pero sin datos vivos
   (El bot no estará corriendo en segundo plano)

═════════════════════════════════════════════════════════════════════════

OPCIÓN 3: INTEGRAR EN TU CÓDIGO EXISTENTE
═════════════════════════════════════════════════════════════════════════

Si quieres agregar optimización a tu código:

PASO 1: Lee INTEGRATION_GUIDE_CODE.py (tiene ejemplos)

PASO 2: Agrega 2 líneas a tu main.py:

   from app.integration.performance_controller import get_performance_controller
   
   # En tu función main():
   get_performance_controller().run_continuous_optimization()

PASO 3: Listo! Ahora tienes optimización continua corriendo en background

═════════════════════════════════════════════════════════════════════════

VERIFICACIÓN: ¿ESTÁ TODO FUNCIONANDO?
═════════════════════════════════════════════════════════════════════════

Después de iniciado, verifica esto:

✅ Dashboard abierto
   → Vuelve a http://localhost:8501
   → Deberías ver métricas en tiempo real

✅ API funcionando
   → Abre http://localhost:8000/docs
   → Deberías ver lista de endpoints API

✅ Bot operando
   → En el dashboard, ve a "History"
   → Deberías ver operaciones listadas

✅ Optimizador corriendo
   → En el dashboard, ve a "Optimizer"
   → Haz click en "Analyze"
   → Deberías ver análisis de performance

═════════════════════════════════════════════════════════════════════════

COMANDOS ÚTILES (mientras el sistema corre)
═════════════════════════════════════════════════════════════════════════

En otra terminal PowerShell/Terminal:

# Ver datos históricos
$ curl "http://localhost:8000/api/optimized/trades/history?days=7"

# Ver performance por símbolo
$ curl "http://localhost:8000/api/optimized/performance/symbol?days=30"

# Ver estado del optimizador
$ curl "http://localhost:8000/api/optimized/optimizer/status"

# Limpiar cache
$ curl -X POST "http://localhost:8000/api/optimized/cache/clear"

# Ver estadísticas del cache
$ curl "http://localhost:8000/api/optimized/cache/stats"

═════════════════════════════════════════════════════════════════════════

DASHBOARD - QUEUENES HACER EN CADA PESTAÑA
═════════════════════════════════════════════════════════════════════════

1️⃣ DASHBOARD (Pestaña Principal)
   • Monitorea equity en tiempo real
   • Ve posiciones abiertas
   • Observa win rate
   • Mira curva de equity

2️⃣ ANÁLISIS
   • Selecciona un símbolo de la lista
   • Ve análisis técnico en vivo
   • Revisa sentimiento del mercado
   • Analiza indicadores

3️⃣ OPTIMIZADOR (Nuevo!)
   • Selecciona rango de análisis (1-72 horas)
   • Click en "Analyze & Generate Recommendations"
   • Lee recomendaciones de IA
   • Click en "Apply Recommended Parameters" para aplicar

4️⃣ HISTORIAL
   • Ve todas tus operaciones
   • Filtra por días
   • Ve estadísticas de ganancias
   • Exporta a CSV

5️⃣ CONFIGURACIÓN
   • Ajusta parámetros del bot
   • Limpia cache si necesitas
   • Ve modo del bot (LIVE/DEMO)

═════════════════════════════════════════════════════════════════════════

PRÓXIMOS PASOS (Después de iniciado)
═════════════════════════════════════════════════════════════════════════

DÍA 1-2:
  ✓ Verifica que el bot esté operando normalmente
  ✓ Revisa que el dashboard se carga rápido
  ✓ Prueba los diferentes tabs

SEMANA 1:
  ✓ El optimizador recopila datos (espera 60 min)
  ✓ Ve primeras recomendaciones en tab "Optimizer"
  ✓ Revisa historial de operaciones

SEMANA 2:
  ✓ Optimizador tiene más data
  ✓ Recomendaciones más precisas
  ✓ Parámetros empiezan a ajustarse

SEMANA 3-4:
  ✓ Patrones claros emergiendo
  ✓ Win rate estabilizado
  ✓ Mejores horas y símbolos identificados

═════════════════════════════════════════════════════════════════════════

TROUBLESHOOTING: SI ALGO NO FUNCIONA
═════════════════════════════════════════════════════════════════════════

"El Dashboard no abre"
  → Verifica que corres: python run_optimized_system.py
  → Espera 10 segundos después de iniciar
  → Abre: http://localhost:8501

"El API no responde"
  → El API tarda ~5 segundos en iniciar
  → Abre: http://localhost:8000/docs

"No hay datos en el historial"
  → El bot necesita tiempo para operar
  → Espera 5-10 minutos
  → Refresca: F5 en el dashboard

"El optimizador dice 'Insufficient data'"
  → Necesita al menos 1-2 horas de datos
  → Espera a que el bot opere
  → Intenta en 1 hora

"UI muy lenta"
  → Limpia cache: POST /cache/clear
  → Refresca dashboard: F5
  → Reinicia: Ctrl+C y vuelve a iniciar

═════════════════════════════════════════════════════════════════════════

DOCUMENTACIÓN PARA LEER (En este orden)
═════════════════════════════════════════════════════════════════════════

1. Este archivo (tu estás aquí!)
2. QUICK_START_OPTIMIZED.md (referencia rápida)
3. OPTIMIZATION_REFACTORING_GUIDE.md (detalles técnicos)
4. INTEGRATION_GUIDE_CODE.py (ejemplos de código)

═════════════════════════════════════════════════════════════════════════

PREGUNTAS FRECUENTES
═════════════════════════════════════════════════════════════════════════

P: ¿Cuánto tiempo tarda en iniciarse?
R: ~10 segundos para tener todo corriendo

P: ¿Puedo cambiar el intervalo de optimización?
R: Sí, en run_optimized_system.py, línea con interval_minutes=60

P: ¿El bot deja de operar mientras se optimiza?
R: No, optimización corre en background sin interrupciones

P: ¿Cómo aumento/disminuyo velocidad de UI?
R: Cambia TTL en app/ui_optimized.py (@streamlit_cache(ttl=X))

P: ¿Puedo exportar datos?
R: Sí, en pestaña "History" hay botón "Export to CSV"

P: ¿Dónde están los logs?
R: En carpeta logs/ del proyecto

═════════════════════════════════════════════════════════════════════════

¡LISTO PARA EMPEZAR!
═════════════════════════════════════════════════════════════════════════

1. Abre PowerShell en: c:\\Users\\Shadow\\Downloads\\Metatrade
2. Ejecuta: python run_optimized_system.py
3. Abre: http://localhost:8501
4. ¡Disfrutá tu sistema optimizado! 🚀

═════════════════════════════════════════════════════════════════════════
"""

print(STEP_BY_STEP)

# Also create a desktop shortcut guide
SHORTCUT_GUIDE = """
Opcionalmente, puedes crear un shortcut en el escritorio:

OPCIÓN A: Crear .bat file (Windows)
──────────────────────────────────

1. Click derecho en escritorio → New → Text Document
2. Copia esto:
   @echo off
   cd /d "c:\\Users\\Shadow\\Downloads\\Metatrade"
   python run_optimized_system.py
   pause

3. Save Como: start_bot.bat (importante: .bat)
4. Click derecho en el archivo → Send to → Desktop (create shortcut)
5. Ahora puedes hacer doble-click para iniciar!

OPCIÓN B: Crear .ps1 file (PowerShell)
──────────────────────────────────────

1. Click derecho en escritorio → New → Text Document
2. Copia esto:
   Set-Location "c:\\Users\\Shadow\\Downloads\\Metatrade"
   python run_optimized_system.py

3. Save Como: start_bot.ps1
4. Click derecho → Properties → Security → Unblock
5. Ahora puedes ejecutar con PowerShell

OPCIÓN C: Crear Shortcut directo
────────────────────────────────

1. Click derecho en escritorio → New → Shortcut
2. En "location": 
   C:\\Windows\\System32\\cmd.exe /c cd /d "c:\\Users\\Shadow\\Downloads\\Metatrade" && python run_optimized_system.py
3. Name: "Trading Bot"
4. Finish
5. Click derecho en shortcut → Properties → Advanced → Run as administrator
6. ¡Listo! Doble-click para iniciar

"""

if __name__ == "__main__":
    print("\n" + "="*80)
    print("Para crear shortcuts opcionales, lee arriba ⬆️")
    print("="*80)
