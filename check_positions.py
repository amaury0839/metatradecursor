import MetaTrader5 as mt5
from datetime import datetime

if not mt5.initialize():
    print("❌ MT5 initialize() failed")
    mt5.shutdown()
    exit()

print(f"✅ MT5 connected\n")

# Get account info
account_info = mt5.account_info()
if account_info:
    print(f"💰 CUENTA: {account_info.login}")
    print(f"   Balance: ${account_info.balance:.2f}")
    print(f"   Equity: ${account_info.equity:.2f}")
    print(f"   Margen: ${account_info.margin:.2f}")
    print(f"   Free Margin: ${account_info.margin_free:.2f}")
    print(f"   Profit: ${account_info.profit:.2f}")
    print()

# Get open positions
positions = mt5.positions_get()
if positions:
    print(f"📊 POSICIONES ABIERTAS: {len(positions)}\n")
    print("=" * 100)
    for pos in positions:
        print(f"Ticket: {pos.ticket}")
        print(f"  Symbol: {pos.symbol}")
        print(f"  Type: {'BUY' if pos.type == 0 else 'SELL'}")
        print(f"  Volume: {pos.volume:.2f}")
        print(f"  Entry: {pos.price_open}")
        print(f"  Current: {pos.price_current}")
        print(f"  SL: {pos.sl}")
        print(f"  TP: {pos.tp}")
        print(f"  Profit: ${pos.profit:.2f}")
        print(f"  Time: {datetime.fromtimestamp(pos.time)}")
        print("-" * 100)
else:
    print("📊 No hay posiciones abiertas")

print()

# Get today's deals (history)
from_date = datetime(2026, 1, 31)
to_date = datetime.now()
deals = mt5.history_deals_get(from_date, to_date)

if deals:
    print(f"\n📈 HISTORIAL DE HOY: {len(deals)} deals")
    print("=" * 100)
    for deal in deals[:20]:  # Show last 20
        print(f"Deal: {deal.ticket}")
        print(f"  Order: {deal.order}")
        print(f"  Symbol: {deal.symbol}")
        print(f"  Type: {deal.type}")
        print(f"  Volume: {deal.volume}")
        print(f"  Price: {deal.price}")
        print(f"  Profit: ${deal.profit:.2f}")
        print(f"  Time: {datetime.fromtimestamp(deal.time)}")
        print("-" * 100)
else:
    print("\n📈 No hay deals en el historial de hoy")

mt5.shutdown()
