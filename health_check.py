#!/usr/bin/env python3
"""System health check and diagnostics"""

import subprocess
import sys
import time
from pathlib import Path

def check_ports():
    """Check if required ports are available"""
    print("\n" + "="*80)
    print("🔍 Checking Port Availability...")
    print("="*80)
    
    ports = {
        8000: "API Server",
        8501: "Streamlit UI",
    }
    
    for port, service in ports.items():
        try:
            # Try to connect to port
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:
                print(f"  ⚠️  Port {port} ({service}): IN USE")
            else:
                print(f"  ✅ Port {port} ({service}): Available")
        except Exception as e:
            print(f"  ❓ Port {port} ({service}): Check failed ({e})")


def check_dependencies():
    """Check if required packages are installed"""
    print("\n" + "="*80)
    print("📦 Checking Dependencies...")
    print("="*80)
    
    required = [
        'streamlit',
        'requests',
        'uvicorn',
        'fastapi',
        'mt5_connection',  # Check if MT5 is available
    ]
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}: Installed")
        except ImportError:
            print(f"  ❌ {package}: NOT installed - Run: pip install {package}")


def check_files():
    """Check if critical files exist"""
    print("\n" + "="*80)
    print("📁 Checking Critical Files...")
    print("="*80)
    
    workspace = Path(__file__).parent
    critical_files = [
        'run_bot.py',
        'app/ui_improved.py',
        'app/api/server.py',
        'app/main.py',
        'app/core/__init__.py',
        'app/trading/__init__.py',
        'requirements.txt',
    ]
    
    for file_path in critical_files:
        full_path = workspace / file_path
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {file_path}")
    
    return all((workspace / f).exists() for f in critical_files)


def check_processes():
    """Check running Python processes"""
    print("\n" + "="*80)
    print("⚙️  Checking Running Processes...")
    print("="*80)
    
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/V'],
            capture_output=True,
            text=True
        )
        
        if 'python.exe' in result.stdout:
            # Count processes
            lines = [l for l in result.stdout.split('\n') if 'python.exe' in l]
            print(f"  ⚠️  Found {len(lines)} Python process(es) running")
            for line in lines[:5]:  # Show first 5
                print(f"    {line.strip()[:70]}")
        else:
            print("  ✅ No Python processes running (clean state)")
    except Exception as e:
        print(f"  ❓ Could not check processes: {e}")


def show_startup_sequence():
    """Show recommended startup sequence"""
    print("\n" + "="*80)
    print("🚀 RECOMMENDED STARTUP SEQUENCE")
    print("="*80)
    print("""
1️⃣  Stop all existing processes:
    python -m pip install pywin32  # (if needed)
    python -c "import subprocess; subprocess.run(['taskkill', '/F', '/IM', 'python.exe'])"

2️⃣  Start the unified system:
    python start_system.py

3️⃣  Access the dashboard:
    http://localhost:8501

4️⃣  Monitor for stability:
    - Watch for connection errors in UI
    - Check that bot is trading every 30 seconds
    - Verify no ScriptRunContext warnings

If UI disconnects again, check:
    - Are all 3 services still running? (check_processes)
    - Check API server logs for 502 errors
    - Check bot logs for trading errors
    - Verify network connectivity to localhost
    """)


def main():
    print("\n" + "█"*80)
    print("█ SYSTEM HEALTH CHECK".center(80) + "█")
    print("█"*80)
    
    # Run all checks
    check_ports()
    check_files_ok = check_files()
    check_dependencies()
    check_processes()
    show_startup_sequence()
    
    # Summary
    print("\n" + "="*80)
    if check_files_ok:
        print("✅ SYSTEM READY TO START")
        print("\nRun: python start_system.py")
    else:
        print("⚠️  MISSING FILES - System not ready")
        print("\nCreate missing files or clone repository")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
