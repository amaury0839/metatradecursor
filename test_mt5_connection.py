#!/usr/bin/env python3
"""
Intenta conectar a MT5 cuando esté disponible
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.trading.mt5_client import get_mt5_client
from app.core.logger import setup_logger

logger = setup_logger("mt5_connect_test")

print("\n" + "="*70)
print("🔍 VERIFICANDO CONEXIÓN A METATRADER 5")
print("="*70)

mt5 = get_mt5_client()

logger.info("\n📋 Configuración esperada:")
logger.info(f"   Cuenta: {mt5.config.mt5.login}")
logger.info(f"   Server: {mt5.config.mt5.server}")
logger.info(f"   Path: {mt5.config.mt5.path}")

logger.info("\n⏳ Intentando conectar a MT5...")
logger.info("   (MT5 debe estar ABIERTO y AUTENTICADO)")

# Intenta conectar
success = mt5.connect()

if success:
    logger.info("\n✅ ¡CONEXIÓN EXITOSA!")
    account = mt5.get_account_info()
    if account:
        logger.info(f"\n📊 Datos de la cuenta:")
        logger.info(f"   Login: {account.get('login')}")
        logger.info(f"   Server: {account.get('server')}")
        logger.info(f"   Balance: ${account.get('balance'):.2f}")
        logger.info(f"   Equity: ${account.get('equity'):.2f}")
else:
    logger.error("\n❌ No se pudo conectar a MT5")
    logger.error("\n📝 Solución:")
    logger.error("   1. Abre MetaTrader 5 (si no está abierto)")
    logger.error("   2. Ve a: Tools → Options")
    logger.error("   3. En la pestaña 'Expert Advisors', habilita:")
    logger.error("      ✓ Allow automated trading")
    logger.error("      ✓ Allow DLL imports")
    logger.error("      ✓ Allow imports")
    logger.error("   4. Haz clic en 'OK'")
    logger.error("   5. REINICIA MT5 completamente")
    logger.error("   6. El bot se conectará automáticamente al reiniciar")

print("="*70 + "\n")
