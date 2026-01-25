#!/usr/bin/env python3
"""
Script para limpiar conexiones previas de MT5 y hacer reset completo
"""
import subprocess
import time
import sys

print("="*70)
print("🔧 LIMPIEZA FORZADA DE MT5")
print("="*70)

# Paso 1: Cerrar todos los procesos de MT5
print("\n1️⃣ Cerrando MetaTrader5...")
subprocess.run("taskkill /F /IM terminal64.exe", shell=True, capture_output=True)
subprocess.run("taskkill /F /IM terminal.exe", shell=True, capture_output=True)
time.sleep(3)
print("   ✅ MT5 cerrado")

# Paso 2: Cerrar procesos Python
print("\n2️⃣ Cerrando procesos Python...")
subprocess.run("taskkill /F /IM python.exe", shell=True, capture_output=True)
time.sleep(2)
print("   ✅ Python limpio")

# Paso 3: Mensaje
print("\n3️⃣ Abriendo MT5 de nuevo...")
print("   - Espera a que se cargue completamente")
print("   - Verifica que inicies sesión automáticamente")
print("   - NO minimices MT5")

# Abre MT5
try:
    subprocess.Popen("C:\\Program Files\\MetaTrader 5\\terminal64.exe")
    print("   ✅ MT5 iniciado")
    print("\n   Esperando 15 segundos para que MT5 se cargue...")
    
    for i in range(15, 0, -1):
        print(f"   {i}...", end=" ", flush=True)
        time.sleep(1)
    print("\n   ✅ Listo\n")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

print("="*70)
print("\n📝 PRÓXIMOS PASOS:")
print("1. Verifica que MT5 esté abierto y logueado")
print("2. Ejecuta: .\.\.venv\Scripts\python.exe diag_mt5.py")
print("3. O ejecuta directamente el bot: .\.venv\Scripts\python.exe run_local_bot.py")
print("="*70 + "\n")
