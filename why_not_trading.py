"""
Script para verificar por qué el bot no está tradeando
"""
import MetaTrader5 as mt5
from datetime import datetime
import time

if not mt5.initialize():
    print("❌ Error inicializando MT5")
    exit()

print("=" * 80)
print("🔍 ANÁLISIS: ¿POR QUÉ EL BOT NO TRADEA?")
print("=" * 80)

# 1. Verificar posiciones actuales
positions = mt5.positions_get()
print(f"\n1️⃣ POSICIONES ACTUALES: {len(positions) if positions else 0}")
if positions:
    for pos in positions:
        print(f"   • {pos.symbol}: {pos.volume} lots, P/L: ${pos.profit:.2f}")

# 2. Verificar cuenta
account = mt5.account_info()
print(f"\n2️⃣ ESTADO DE LA CUENTA:")
print(f"   Balance: ${account.balance:.2f}")
print(f"   Equity: ${account.equity:.2f}")
print(f"   Margen libre: ${account.margin_free:.2f}")
print(f"   Profit: ${account.profit:.2f}")

# 3. Verificar símbolos principales
print(f"\n3️⃣ ESTADO DE SÍMBOLOS:")
symbols_to_check = ["EURUSD", "GBPUSD", "BTCUSD", "ETHUSD", "XRPUSD"]
for symbol in symbols_to_check:
    info = mt5.symbol_info(symbol)
    if info:
        trade_modes = {0: "DISABLED", 1: "LONGONLY", 2: "SHORTONLY", 3: "CLOSEONLY", 4: "FULL"}
        mode = trade_modes.get(info.trade_mode, "UNKNOWN")
        status = "✅" if mode == "FULL" else "❌"
        print(f"   • {symbol}: {mode} {status}")
        
        # Verificar si está abierto el mercado
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            bid_ask_spread = tick.ask - tick.bid
            print(f"     Bid: {tick.bid}, Ask: {tick.ask}, Spread: {bid_ask_spread:.5f}")
    else:
        print(f"   • {symbol}: NO DISPONIBLE ❌")

# 4. Verificar últimas órdenes
print(f"\n4️⃣ ÚLTIMAS ÓRDENES (última hora):")
from_date = datetime.now().replace(hour=datetime.now().hour-1, minute=0, second=0)
to_date = datetime.now()
orders = mt5.history_orders_get(from_date, to_date)

if orders:
    print(f"   Total órdenes: {len(orders)}")
    # Contar por estado
    states = {}
    for order in orders:
        state_names = {
            0: "STARTED", 1: "PLACED", 2: "CANCELED", 
            3: "PARTIAL", 4: "FILLED", 5: "REJECTED",
            6: "EXPIRED", 7: "REQUEST_ADD", 8: "REQUEST_MODIFY", 
            9: "REQUEST_CANCEL"
        }
        state = state_names.get(order.state, f"UNKNOWN({order.state})")
        states[state] = states.get(state, 0) + 1
    
    print(f"   Por estado:")
    for state, count in states.items():
        print(f"     • {state}: {count}")
    
    # Mostrar últimas rechazadas
    rejected = [o for o in orders if o.state == 5]
    if rejected:
        print(f"\n   ⚠️ Órdenes RECHAZADAS ({len(rejected)}):")
        for order in rejected[-5:]:
            dt = datetime.fromtimestamp(order.time_setup)
            print(f"     • {dt.strftime('%H:%M:%S')} - {order.symbol} {order.type} {order.volume_initial}")
else:
    print(f"   ❌ No hay órdenes en la última hora")

# 5. Intentar abrir una orden de prueba (sin ejecutar)
print(f"\n5️⃣ PRUEBA DE CAPACIDAD DE TRADING:")
test_symbol = "EURUSD"
symbol_info = mt5.symbol_info(test_symbol)
if symbol_info:
    if not symbol_info.visible:
        print(f"   ⚠️ {test_symbol} no visible, habilitando...")
        mt5.symbol_select(test_symbol, True)
    
    tick = mt5.symbol_info_tick(test_symbol)
    if tick:
        print(f"   ✅ {test_symbol} disponible para trading")
        print(f"      Precio actual: {tick.bid}")
        print(f"      Volume mínimo: {symbol_info.volume_min}")
        print(f"      Volume step: {symbol_info.volume_step}")
    else:
        print(f"   ❌ No se puede obtener tick de {test_symbol}")
else:
    print(f"   ❌ {test_symbol} no disponible")

# 6. Verificar horario de mercado
print(f"\n6️⃣ HORARIO ACTUAL:")
now = datetime.now()
print(f"   Fecha/Hora: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   Día de semana: {now.strftime('%A')}")
print(f"   Es fin de semana: {'Sí ❌' if now.weekday() >= 5 else 'No ✅'}")

mt5.shutdown()

print("\n" + "=" * 80)
print("✅ DIAGNÓSTICO COMPLETO")
print("=" * 80)
