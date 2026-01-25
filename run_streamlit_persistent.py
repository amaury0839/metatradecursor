"""Wrapper para mantener Streamlit corriendo continuamente"""

import subprocess
import time
import sys
import os

def run_streamlit():
    """Run Streamlit and keep it alive"""
    while True:
        try:
            print("🚀 Starting Streamlit UI...")
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                "app/ui_simple.py",
                "--client.toolbarMode=viewer",
                "--server.headless=true",
                "--logger.level=warning"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Read output
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
                    if "You can now view your Streamlit app" in line:
                        print("✅ Streamlit is ready!")
            
            # If process ends, restart it
            returncode = process.wait()
            print(f"⚠️ Streamlit stopped with code {returncode}, restarting in 5 seconds...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_streamlit()
