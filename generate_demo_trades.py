"""
Generate demo trades for UI testing.
Inserts sample trade data into the database.
"""

import sqlite3
from datetime import datetime, timedelta
import random

def generate_demo_trades():
    """Generate sample trades for the last 30 days"""
    conn = sqlite3.connect('data/trading_history.db')
    cursor = conn.cursor()
    
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'BTCUSD', 'ETHUSD', 'BNBUSD']
    
    # Generar 20 trades de demo
    now = datetime.now()
    for i in range(20):
        # Tiempo aleatorio en los últimos 30 días
        days_ago = random.randint(0, 29)
        hours_ago = random.randint(0, 23)
        open_time = now - timedelta(days=days_ago, hours=hours_ago)
        
        # Trade abierto hace X horas
        close_time = open_time + timedelta(hours=random.randint(1, 8))
        
        symbol = random.choice(symbols)
        trade_type = random.randint(0, 1)  # 0=BUY, 1=SELL
        volume = round(random.uniform(0.01, 0.5), 2)
        open_price = round(random.uniform(1.0, 100.0), 5)
        close_price = open_price + random.uniform(-0.05, 0.05)
        
        # Calcular profit (simplificado)
        if trade_type == 0:  # BUY
            profit = (close_price - open_price) * 100000 * volume
        else:  # SELL
            profit = (open_price - close_price) * 100000 * volume
        
        profit = round(profit, 2)
        
        ticket = 1000000 + i
        
        try:
            cursor.execute("""
                INSERT INTO trades (
                    ticket, symbol, type, volume, 
                    open_price, open_timestamp, 
                    close_price, close_timestamp,
                    profit, status, commission, swap
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket, symbol, trade_type, volume,
                open_price, open_time.isoformat(),
                close_price, close_time.isoformat(),
                profit, 'closed', 0.5, 0.0
            ))
        except Exception as e:
            print(f"Error inserting trade {i}: {e}")
    
    conn.commit()
    conn.close()
    print("Demo trades generados exitosamente")

if __name__ == "__main__":
    generate_demo_trades()
