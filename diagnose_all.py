"""
Diagnóstico completo del sistema de trading
"""
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import sqlite3
import os

print("=" * 80)
print("🔍 DIAGNÓSTICO COMPLETO DEL SISTEMA")
print("=" * 80)

# 1. Verificar MT5
print("\n1️⃣ CONEXIÓN MT5")
print("-" * 80)
if not mt5.initialize():
    print("❌ MT5 NO INICIALIZADO")
    print(f"   Error: {mt5.last_error()}")
else:
    print("✅ MT5 conectado")
    account = mt5.account_info()
    if account:
        print(f"   Cuenta: {account.login}")
        print(f"   Balance: ${account.balance:.2f}")
        print(f"   Equity: ${account.equity:.2f}")
        print(f"   Profit: ${account.profit:.2f}")
        print(f"   Margen libre: ${account.margin_free:.2f}")
    
    # Verificar posiciones
    positions = mt5.positions_get()
    print(f"   Posiciones abiertas: {len(positions) if positions else 0}")
    
    # Verificar símbolos
    symbols = ["EURUSD", "BTCUSD", "ETHUSD"]
    print(f"\n   Verificando símbolos disponibles:")
    for symbol in symbols:
        info = mt5.symbol_info(symbol)
        if info:
            trade_mode_map = {0: "DISABLED", 1: "LONGONLY", 2: "SHORTONLY", 3: "CLOSEONLY", 4: "FULL"}
            trade_mode = trade_mode_map.get(info.trade_mode, "UNKNOWN")
            print(f"   • {symbol}: {trade_mode} {'✅' if trade_mode == 'FULL' else '❌'}")
        else:
            print(f"   • {symbol}: NO DISPONIBLE ❌")

# 2. Verificar Database
print("\n2️⃣ BASE DE DATOS")
print("-" * 80)
db_path = "data/trading_history.db"
if os.path.exists(db_path):
    print(f"✅ Database existe: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar trades
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        print(f"   Total trades: {trade_count}")
        
        # Últimos trades
        cursor.execute("""
            SELECT symbol, type, volume, open_price, open_timestamp, status 
            FROM trades 
            ORDER BY id DESC 
            LIMIT 5
        """)
        recent_trades = cursor.fetchall()
        if recent_trades:
            print(f"\n   Últimos 5 trades:")
            for trade in recent_trades:
                symbol, ttype, vol, price, ts, status = trade
                print(f"   • {symbol} {ttype} {vol} @ {price} - {status}")
        
        # Verificar analysis_history
        cursor.execute("SELECT COUNT(*) FROM analysis_history WHERE timestamp > datetime('now', '-1 hour')")
        recent_analysis = cursor.fetchone()[0]
        print(f"\n   Análisis última hora: {recent_analysis}")
        
        # Verificar ai_decisions
        cursor.execute("SELECT COUNT(*) FROM ai_decisions WHERE timestamp > datetime('now', '-1 hour')")
        recent_decisions = cursor.fetchone()[0]
        print(f"   Decisiones IA última hora: {recent_decisions}")
        
        conn.close()
    except Exception as e:
        print(f"   ⚠️ Error leyendo DB: {e}")
else:
    print(f"❌ Database no existe: {db_path}")

# 3. Verificar archivos de configuración
print("\n3️⃣ CONFIGURACIÓN")
print("-" * 80)
if os.path.exists(".env"):
    print("✅ Archivo .env existe")
    with open(".env", "r") as f:
        lines = f.readlines()
        for key in ["MODE", "MT5_LOGIN", "GEMINI_API_KEY", "DEFAULT_RISK_PER_TRADE", "MAX_POSITIONS"]:
            for line in lines:
                if line.startswith(key):
                    value = line.strip().split("=", 1)[1] if "=" in line else ""
                    if "API" in key or "PASSWORD" in key:
                        value = value[:10] + "..." if len(value) > 10 else value
                    print(f"   {key}: {value}")
else:
    print("❌ Archivo .env no existe")

# 4. Verificar deals de hoy en MT5
print("\n4️⃣ ACTIVIDAD DE TRADING HOY")
print("-" * 80)
if mt5.initialize():
    from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    to_date = datetime.now()
    
    deals = mt5.history_deals_get(from_date, to_date)
    orders = mt5.history_orders_get(from_date, to_date)
    
    print(f"   Deals ejecutados hoy: {len(deals) if deals else 0}")
    print(f"   Órdenes hoy: {len(orders) if orders else 0}")
    
    if deals and len(deals) > 0:
        # Últimos 5 deals
        print(f"\n   Últimos 5 deals:")
        for deal in list(deals)[-5:]:
            dt = datetime.fromtimestamp(deal.time)
            deal_type = "BUY" if deal.type == 0 else "SELL" if deal.type == 1 else "OTHER"
            print(f"   • {dt.strftime('%H:%M:%S')} - {deal.symbol} {deal_type} {deal.volume} @ {deal.price} (P/L: ${deal.profit:.2f})")
    
    # Verificar órdenes rechazadas
    if orders:
        rejected = [o for o in orders if o.state == 6]  # STATE_REJECTED
        if rejected:
            print(f"\n   ⚠️ Órdenes rechazadas: {len(rejected)}")
            for order in rejected[-3:]:
                dt = datetime.fromtimestamp(order.time_setup)
                print(f"   • {dt.strftime('%H:%M:%S')} - {order.symbol} RECHAZADA")
    
    mt5.shutdown()

# 5. Verificar si el bot está ejecutando el loop
print("\n5️⃣ ESTADO DEL BOT")
print("-" * 80)
log_files = ["bot_continuous.log", "bot_latest.log", "trading.log"]
for log_file in log_files:
    if os.path.exists(log_file):
        print(f"✅ Log encontrado: {log_file}")
        # Leer última línea
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    print(f"   Última línea: {last_line[:100]}...")
        except Exception as e:
            print(f"   ⚠️ Error leyendo: {e}")
    else:
        print(f"⚠️ Log no existe: {log_file}")

print("\n" + "=" * 80)
print("✅ DIAGNÓSTICO COMPLETO")
print("=" * 80)
