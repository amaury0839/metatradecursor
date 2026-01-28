#!/usr/bin/env python3
"""Robust system starter - manages bot, UI, and API services"""

import subprocess
import time
import sys
import signal
from pathlib import Path

class SystemManager:
    def __init__(self):
        self.processes = {}
        self.workspace = Path(__file__).parent
        
    def start_bot(self):
        """Start standalone bot runner"""
        print("\n" + "="*80)
        print("🤖 Starting Trading BOT...")
        print("="*80)
        
        try:
            # Use run_bot.py (standalone, NOT Streamlit)
            proc = subprocess.Popen(
                [sys.executable, str(self.workspace / "run_bot.py")],
                cwd=str(self.workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            self.processes['bot'] = proc
            print("✅ BOT started (PID: {})".format(proc.pid))
            time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Failed to start BOT: {e}")
            return False
    
    def start_ui(self):
        """Start Streamlit UI"""
        print("\n" + "="*80)
        print("📊 Starting Streamlit UI...")
        print("="*80)
        
        try:
            proc = subprocess.Popen(
                [
                    sys.executable, "-m", "streamlit", "run",
                    "app/ui_improved.py",
                    "--server.port", "8501",
                    "--logger.level=error"  # Reduce noisy warnings
                ],
                cwd=str(self.workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.processes['ui'] = proc
            print("✅ UI started (PID: {})".format(proc.pid))
            print("📍 Access at: http://localhost:8501")
            time.sleep(3)
            return True
        except Exception as e:
            print(f"❌ Failed to start UI: {e}")
            return False
    
    def start_api(self):
        """Start FastAPI server"""
        print("\n" + "="*80)
        print("🔌 Starting API Server...")
        print("="*80)
        
        try:
            proc = subprocess.Popen(
                [
                    sys.executable, "-m", "uvicorn",
                    "app.api.server:app",
                    "--host", "0.0.0.0",
                    "--port", "8000",
                    "--reload"
                ],
                cwd=str(self.workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.processes['api'] = proc
            print("✅ API Server started (PID: {})".format(proc.pid))
            print("📍 Access at: http://localhost:8000")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"❌ Failed to start API: {e}")
            return False
    
    def check_health(self):
        """Check if all processes are still running"""
        dead_processes = []
        for name, proc in self.processes.items():
            if proc.poll() is not None:  # Process has terminated
                dead_processes.append(name)
        
        if dead_processes:
            print(f"\n⚠️  Dead processes: {', '.join(dead_processes)}")
            return False
        return True
    
    def start_all(self):
        """Start all services"""
        print("\n" + "█"*80)
        print("█" + " "*78 + "█")
        print("█" + "  🚀 TRADING BOT SYSTEM STARTUP".center(78) + "█")
        print("█" + " "*78 + "█")
        print("█"*80)
        
        # Start in order
        if not self.start_bot():
            return False
        
        if not self.start_api():
            return False
        
        if not self.start_ui():
            return False
        
        print("\n" + "="*80)
        print("✅ ALL SERVICES STARTED")
        print("="*80)
        print("\n📊 DASHBOARD: http://localhost:8501")
        print("🤖 BOT: Running (PAPER mode)")
        print("🔌 API: http://localhost:8000")
        print("\n⏸️  Press Ctrl+C to stop all services")
        print("="*80 + "\n")
        
        return True
    
    def stop_all(self):
        """Stop all services gracefully"""
        print("\n⏹️  Stopping all services...")
        for name, proc in self.processes.items():
            if proc.poll() is None:  # Still running
                print(f"  • Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"    Force killing {name}...")
                    proc.kill()
        print("✅ All services stopped")
    
    def run(self):
        """Main loop"""
        if not self.start_all():
            self.stop_all()
            sys.exit(1)
        
        try:
            while True:
                time.sleep(5)
                if not self.check_health():
                    print("⚠️  Some services have crashed. Restarting...")
                    # Could implement auto-restart here
        except KeyboardInterrupt:
            self.stop_all()


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n" + "="*80)
    print("⏹️  Shutdown signal received")
    print("="*80)
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    manager = SystemManager()
    manager.run()
