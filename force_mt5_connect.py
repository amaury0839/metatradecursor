#!/usr/bin/env python3
"""
Force MT5 connection - bypasses checks and attempts all connection methods
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.logger import setup_logger
from app.trading.mt5_client import get_mt5_client

logger = setup_logger("force_connect")

def force_connect():
    """Intenta conectar a MT5 de forma más agresiva"""
    logger.info("=" * 60)
    logger.info("🔧 Forzando conexión a MT5...")
    logger.info("=" * 60)
    
    mt5 = get_mt5_client()
    
    # Método 1: Conectar normalmente
    logger.info("\n1️⃣ Intento 1: Conexión estándar...")
    if mt5.connect():
        logger.info("✅ ¡ÉXITO! MT5 conectado")
        account = mt5.get_account_info()
        if account:
            logger.info(f"📊 Cuenta: {account.get('login')}")
            logger.info(f"💰 Balance: {account.get('balance')}")
            logger.info(f"📈 Equity: {account.get('equity')}")
        return True
    
    logger.warning("❌ Falló conexión estándar")
    
    # Método 2: Forzar desconexión y reconectar
    logger.info("\n2️⃣ Intento 2: Forzar reset...")
    try:
        import MetaTrader5 as mt5_lib
        mt5_lib.shutdown()
        import time
        time.sleep(2)
        if mt5.connect():
            logger.info("✅ ¡ÉXITO! MT5 conectado después de reset")
            account = mt5.get_account_info()
            if account:
                logger.info(f"📊 Cuenta: {account.get('login')}")
            return True
    except Exception as e:
        logger.warning(f"❌ Reset falló: {e}")
    
    # Método 3: Info de error
    logger.error("\n❌ No se pudo conectar a MT5")
    logger.error("\n📝 PRÓXIMOS PASOS MANUALES:")
    logger.error("=" * 60)
    logger.error("1. Abre MetaTrader 5")
    logger.error("2. Ve a Tools → Options")
    logger.error("3. En la pestaña 'Expert Advisors', habilita:")
    logger.error("   ✓ Allow automated trading")
    logger.error("   ✓ Allow DLL imports")
    logger.error("   ✓ Allow imports")
    logger.error("4. Haz clic en OK")
    logger.error("5. REINICIA MT5 completamente")
    logger.error("6. Luego ejecuta de nuevo este script")
    logger.error("=" * 60)
    
    return False

if __name__ == "__main__":
    success = force_connect()
    sys.exit(0 if success else 1)
