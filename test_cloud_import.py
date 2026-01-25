#!/usr/bin/env python
"""Test that all imports work without .env file (cloud mode)"""

import sys
import os

# Simulate cloud environment - remove .env
env_file = ".env"
env_backup = ".env.backup"
if os.path.exists(env_file):
    os.rename(env_file, env_backup)
    print("⚠️  Moved .env to .env.backup to simulate cloud environment")

try:
    # Test imports in order
    print("\n📦 Testing imports for cloud compatibility...\n")
    
    print("1. Importing config...", end=" ")
    from app.core.config import get_config
    print("✅")
    
    print("2. Importing logger...", end=" ")
    from app.core.logger import setup_logger
    print("✅")
    logger = setup_logger("test")
    
    print("3. Importing MT5 client...", end=" ")
    from app.trading.mt5_client import MT5Client
    print("✅")
    
    print("4. Importing Gemini client...", end=" ")
    from app.ai.gemini_client import GeminiClient
    print("✅")
    
    print("5. Importing API client...", end=" ")
    from app.api_client.client import APIClient
    print("✅")
    
    print("6. Testing config values...", end=" ")
    config = get_config()
    print(f"✅ (MT5 Login={config.mt5.login}, Gemini Key={'[SET]' if config.ai.gemini_api_key else '[NOT SET]'})")
    
    print("\n✅ All imports successful! Cloud deployment should work.\n")
    
finally:
    # Restore .env
    if os.path.exists(env_backup):
        if os.path.exists(env_file):
            os.remove(env_file)
        os.rename(env_backup, env_file)
        print("✅ Restored .env file")
