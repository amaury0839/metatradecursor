#!/usr/bin/env python3
"""Inspect MT5 position object structure"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.trading.mt5_client import get_mt5_client
from app.core.logger import setup_logger

logger = setup_logger("inspect_mt5")

mt5 = get_mt5_client()
if mt5.connect():
    positions = mt5.get_positions()
    if positions:
        pos = positions[0]
        
        print("\n" + "="*80)
        print("MT5 POSITION DICT STRUCTURE")
        print("="*80)
        print(f"\nType: {type(pos)}")
        print(f"\nKeys in dict: {list(pos.keys())}")
        print(f"\nPosition data:")
        for key, value in pos.items():
            print(f"  {key}: {value} (type: {type(value).__name__})")
        
        print("\n" + "="*80)
