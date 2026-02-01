"""
Analyze Amelia Bot Trading Logs - Extract Key Events
"""

import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

log_file = Path("logs/trading_bot.log")

# Read and filter key events
events = []
trading_loops = []
positions_data = []

with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        
        # Extract timestamp and message
        try:
            parts = line.split(" - ")
            if len(parts) >= 3:
                timestamp = parts[0]
                level = parts[1]
                message = " - ".join(parts[2:])
                
                # Collect key trading events
                if any(x in message for x in ["Trading loop", "STEP", "Found", "CLOSING", "Opposite", "Position:"]):
                    events.append((timestamp, message[:150]))
        except:
            pass

# Print last 50 key events
print("\n" + "="*80)
print("🤖 AMELIA BOT - RECENT TRADING ACTIVITY")
print("="*80 + "\n")

if events:
    print(f"Found {len(events)} key events\n")
    print("LAST 50 KEY EVENTS:")
    print("-" * 80)
    for ts, msg in events[-50:]:
        print(f"{ts} | {msg}")
else:
    print("No key trading events found in logs")

# Count statistics
print("\n" + "="*80)
print("STATISTICS")
print("="*80)

# Get line count
total_lines = sum(1 for _ in open(log_file, 'r', encoding='utf-8', errors='ignore'))
print(f"Total log lines: {total_lines:,}")

# Check for errors/warnings
with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()
    error_count = content.count("ERROR")
    warning_count = content.count("WARNING")
    info_count = content.count("INFO")

print(f"ERROR count: {error_count}")
print(f"WARNING count: {warning_count}")
print(f"INFO count: {info_count}")

print("\n✅ Log analysis complete")
