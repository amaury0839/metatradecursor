#!/usr/bin/env python3
"""
Capture the first trading cycle from bot to verify crypto execution
"""
import sys
import os
import subprocess
import time
import json
from pathlib import Path

# Start the bot in background
print("[INFO] Starting bot...")
process = subprocess.Popen(
    [sys.executable, r"c:\Users\Shadow\Downloads\Metatrade\run_bot.py"],
    cwd=r"c:\Users\Shadow\Downloads\Metatrade",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

print("[INFO] Waiting for trading cycle to complete (8 seconds)...\n")
time.sleep(8)

# Terminate bot
process.terminate()
try:
    process.wait(timeout=2)
except subprocess.TimeoutExpired:
    process.kill()
    process.wait()

print("\n" + "=" * 80)
print("BOT CYCLE OUTPUT:")
print("=" * 80)

# Read and display output
stdout, _ = process.communicate()
lines = stdout.split('\n')

# Filter and display relevant lines
crypto_symbols = ["BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "XRPUSD", "ADAUSD", "DOTUSD", "LTCUSD", "DOGEUSD"]

crypto_activity = []
for line in lines:
    if any(crypto in line for crypto in crypto_symbols):
        if any(keyword in line for keyword in ["GATE_DECISION", "signal", "Market Open", "place_market_order", "SELL", "BUY"]):
            crypto_activity.append(line)

if crypto_activity:
    print("\n[CRYPTO TRADING ACTIVITY DETECTED]:\n")
    for line in crypto_activity[:30]:  # Show first 30 relevant lines
        if "{" not in line:  # Skip JSON logs
            print(f"  {line}")
else:
    print("\n[NO CRYPTO ACTIVITY DETECTED] - Showing first 30 lines:\n")
    count = 0
    for line in lines:
        if line.strip() and "{" not in line:
            print(f"  {line}")
            count += 1
            if count >= 30:
                break

print("\n" + "=" * 80)
