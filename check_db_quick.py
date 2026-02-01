import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/trading_history.db')
cursor = conn.cursor()

# Ver tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("📊 TABLES:", [t[0] for t in cursor.fetchall()])

# Ver últimas trades
try:
    cursor.execute("""
        SELECT symbol, action, volume, entry_price, timestamp 
        FROM trades 
        ORDER BY timestamp DESC 
        LIMIT 15
    """)
    print("\n🔥 ÚLTIMAS 15 TRADES:")
    print("-" * 80)
    for row in cursor.fetchall():
        symbol, action, volume, price, ts = row
        print(f"{symbol:10} | {action:4} | {volume:8.2f} lots | ${price:10.5f} | {ts}")
except Exception as e:
    print(f"Error: {e}")
    # Intentar con otra estructura
    cursor.execute("PRAGMA table_info(trades)")
    cols = [c[1] for c in cursor.fetchall()]
    print(f"Columnas disponibles: {cols}")

# Contar total de trades
cursor.execute("SELECT COUNT(*) FROM trades")
total = cursor.fetchone()[0]
print(f"\n📈 Total de trades registrados: {total}")

# Ver resumen por símbolo
cursor.execute("""
    SELECT symbol, COUNT(*) as count, SUM(volume) as total_vol
    FROM trades
    GROUP BY symbol
    ORDER BY count DESC
    LIMIT 10
""")
print("\n📊 TOP 10 SÍMBOLOS MÁS TRADED:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"{row[0]:10} | {row[1]:3} trades | {row[2]:8.2f} lots")

conn.close()
