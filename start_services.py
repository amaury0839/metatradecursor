#!/usr/bin/env python3
"""
Start all required services: API, UI, and Bot
Run this script to bring the system online
"""
import subprocess
import sys
import time
import os

# Add workspace to path
sys.path.insert(0, r'c:\Users\Shadow\Downloads\Metatrade')

from app.core.logger import setup_logger

logger = setup_logger("service_manager")

print("\n" + "=" * 80)
print("METATRADE A-BOT SERVICE MANAGER")
print("=" * 80)

services = [
    {
        "name": "API Server",
        "port": 8002,
        "cmd": [sys.executable, "app/api/server.py"],
        "startup_delay": 3,
        "description": "FastAPI backend (core data & trading control)"
    },
    {
        "name": "Streamlit UI",
        "port": 8504,
        "cmd": [sys.executable, "-m", "streamlit", "run", "app/main_ui.py", "--server.port", "8504"],
        "startup_delay": 5,
        "description": "Web dashboard for monitoring"
    },
    {
        "name": "Trading Bot",
        "port": None,
        "cmd": [sys.executable, "run_bot.py"],
        "startup_delay": 2,
        "description": "Continuous trading loop"
    },
]

processes = []

def start_service(service):
    """Start a service and return the process"""
    print(f"\n[STARTING] {service['name']} ({service['description']})")
    print(f"  Command: {' '.join(service['cmd'])}")
    
    try:
        cwd = r'c:\Users\Shadow\Downloads\Metatrade'
        process = subprocess.Popen(
            service['cmd'],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        time.sleep(service['startup_delay'])
        
        if process.poll() is None:  # Process still running
            if service['port']:
                print(f"  ✅ RUNNING on port {service['port']}")
            else:
                print(f"  ✅ RUNNING")
            return process
        else:
            print(f"  ❌ FAILED to start (process exited)")
            return None
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return None

def main():
    """Start all services"""
    print("\n" + "-" * 80)
    print("STARTING SERVICES...")
    print("-" * 80)
    
    for service in services:
        process = start_service(service)
        if process:
            processes.append({"name": service["name"], "process": process})
    
    print("\n" + "=" * 80)
    print("SERVICE STATUS:")
    print("=" * 80)
    
    for item in processes:
        status = "RUNNING" if item["process"].poll() is None else "STOPPED"
        print(f"  {item['name']}: {status}")
    
    print("\n" + "=" * 80)
    print("ACCESS POINTS:")
    print("=" * 80)
    print("  API Server: http://localhost:8002")
    print("  Streamlit UI: http://localhost:8504")
    print("  Trading Bot: Running in continuous mode (60-second cycles)")
    print("\n" + "=" * 80)
    print("PRESS CTRL+C TO STOP ALL SERVICES")
    print("=" * 80 + "\n")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[SHUTTING DOWN] Terminating all services...")
        for item in processes:
            try:
                item["process"].terminate()
                print(f"  {item['name']}: stopped")
            except:
                pass
        print("[SHUTDOWN] Complete")
        sys.exit(0)

if __name__ == "__main__":
    main()
