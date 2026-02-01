#!/usr/bin/env python3
"""
Diagnóstico rápido de por qué no está tradueando
"""

import sys
sys.path.insert(0, '/home/Downloads/Metatrade')

from app.trading.market_status import MarketStatus
from app.trading.mt5_client import get_mt5_client
from app.core.logger import setup_logger
from datetime import datetime

logger = setup_logger("diagnose")

print("\n" + "="*80)
print("🔍 DIAGNÓSTICO: ¿Por qué no está tradueando?")
print("="*80 + "\n")

# 1. Verificar conexión MT5
print("1️⃣  VERIFICANDO CONEXIÓN MT5...")
mt5 = get_mt5_client()
if not mt5.is_connected():
    print("   ❌ MT5 NO CONECTADO")
    sys.exit(1)
print("   ✅ MT5 Conectado\n")

# 2. Verificar estado del mercado
print("2️⃣  VERIFICANDO ESTADO DEL MERCADO...")
market_status = MarketStatus()

crypto_symbols = ["BTCUSD", "ETHUSD", "BNBUSD"]
forex_symbols = ["EURUSD", "GBPUSD", "USDJPY"]

print("\n   📊 CRYPTO SYMBOLS (deberían estar SIEMPRE abiertos):")
for symbol in crypto_symbols:
    is_open = market_status.is_symbol_open(symbol)
    status_text = market_status.get_market_status_text(symbol)
    print(f"      {symbol:10} → {'✅ ABIERTO' if is_open else '❌ CERRADO'} ({status_text})")

print("\n   💱 FOREX SYMBOLS:")
for symbol in forex_symbols:
    is_open = market_status.is_symbol_open(symbol)
    status_text = market_status.get_market_status_text(symbol)
    print(f"      {symbol:10} → {'✅ ABIERTO' if is_open else '❌ CERRADO'} ({status_text})")

# 3. Verificar hora actual
print("\n3️⃣  HORA ACTUAL:")
now = datetime.utcnow()
print(f"   UTC Time: {now.strftime('%A %Y-%m-%d %H:%M:%S')}")
print(f"   Weekday: {now.weekday()} (0=Mon, 6=Sun)")

# 4. Verificar horario Forex
print("\n4️⃣  HORARIO FOREX (UTC):")
print(f"   Actual hour: {now.hour}")
is_forex_open = market_status._is_market_open_by_time()
print(f"   ¿Forex abierto por hora? {'✅ SÍ' if is_forex_open else '❌ NO'}")

# 5. Verificar trading mode en MT5
print("\n5️⃣  VERIFICANDO TRADE_MODE EN MT5:")
for symbol in crypto_symbols + forex_symbols:
    try:
        symbol_info = mt5.get_symbol_info(symbol)
        if symbol_info:
            trade_mode = symbol_info.get('trade_mode', -1)
            trade_mode_text = {2: "QUOTES", 4: "FULL"}.get(trade_mode, f"UNKNOWN({trade_mode})")
            print(f"      {symbol:10} → trade_mode={trade_mode_text}")
        else:
            print(f"      {symbol:10} → ❌ Símbolo no encontrado en MT5")
    except Exception as e:
        print(f"      {symbol:10} → ❌ Error: {e}")

print("\n" + "="*80)
print("📋 RESUMEN:")
print("="*80)

all_crypto_open = all(market_status.is_symbol_open(s) for s in crypto_symbols)
print(f"\n✓ ¿Todos los CRYPTO símbolos están abiertos? {'✅ SÍ' if all_crypto_open else '❌ NO'}")

if not all_crypto_open:
    print("\n🔴 PROBLEMA ENCONTRADO: Crypto symbols no están abiertos")
    print("   Esto es INCORRECTO - crypto debería estar SIEMPRE abierto 24/7")
    print("\n   SOLUCIÓN: Revisar market_status.py y verificar CRYPTO_24_7 list")
else:
    print("\n✅ Crypto está correctamente abierto 24/7")

print("\n" + "="*80 + "\n")
