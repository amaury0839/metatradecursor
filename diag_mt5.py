#!/usr/bin/env python3
"""
Diagnóstico detallado de conexión a MT5
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import MetaTrader5 as mt5
    print("✅ MetaTrader5 package imported")
except:
    print("❌ MetaTrader5 no instalado")
    sys.exit(1)

print("\n" + "="*70)
print("🔍 DIAGNÓSTICO DE CONEXIÓN MT5")
print("="*70)

# Intenta inicializar
print("\n1️⃣ Inicializando MT5...")
init_result = mt5.initialize()
print(f"   Resultado: {init_result}")

if not init_result:
    error = mt5.last_error()
    print(f"   Error: {error}")
    print("\n❌ MT5 no está respondiendo")
    print("   Asegúrate que:")
    print("   - MT5 está ABIERTO")
    print("   - MT5 está VISIBLE (no minimizado)")
    print("   - Vuelve a Tools → Options → Expert Advisors")
    print("   - Marca: 'Allow algorithmic trading'")
    sys.exit(1)

print("   ✅ Inicialización exitosa")

# Intenta obtener info de la terminal
print("\n2️⃣ Obteniendo información de la terminal...")
terminal_info = mt5.terminal_info()
if terminal_info:
    print(f"   ✅ Terminal conectada")
    print(f"   - Nombre: {terminal_info.name}")
    print(f"   - Ruta: {terminal_info.path}")
else:
    print(f"   ❌ No se obtiene info de terminal")

# Intenta obtener cuentas disponibles
print("\n3️⃣ Buscando cuentas...")
accounts = mt5.accounts_list()
if accounts:
    print(f"   ✅ Se encontraron {len(accounts)} cuenta(s)")
    for acc in accounts[:3]:  # Muestra las primeras 3
        print(f"   - Login: {acc.login}, Server: {acc.server}")
else:
    print(f"   ❌ No hay cuentas disponibles")

# Intenta login sin contraseña (usando sesión guardada)
print("\n4️⃣ Intentando login sin contraseña (sesión guardada)...")
login_result = mt5.login(5045373902, server="metaquotes-Demo")
if login_result:
    print(f"   ✅ Login exitoso")
    account_info = mt5.account_info()
    if account_info:
        print(f"   📊 Cuenta: {account_info.login}")
        print(f"   💰 Balance: {account_info.balance}")
        print(f"   📈 Equity: {account_info.equity}")
else:
    error = mt5.last_error()
    print(f"   ❌ Login falló: {error}")
    
    # Intenta con contraseña
    print("\n5️⃣ Intentando login CON contraseña...")
    login_result = mt5.login(5045373902, "@1GcVmBu", "metaquotes-Demo")
    if login_result:
        print(f"   ✅ Login exitoso (con contraseña)")
        account_info = mt5.account_info()
        if account_info:
            print(f"   📊 Cuenta: {account_info.login}")
            print(f"   💰 Balance: {account_info.balance}")
            print(f"   📈 Equity: {account_info.equity}")
    else:
        error = mt5.last_error()
        print(f"   ❌ Login con contraseña falló: {error}")

mt5.shutdown()
print("\n" + "="*70)
