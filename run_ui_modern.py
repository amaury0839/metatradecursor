#!/usr/bin/env python
"""
Modern UI Launcher - Start the modernized Streamlit dashboard
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Launch the modern UI"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║      📈 AI TRADING BOT - MODERN UI v2.0                      ║
    ║      Professional Dashboard with Advanced Features            ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print("🚀 Starting modern UI server...")
    print("📱 Features:")
    print("   ✅ Professional dark/light theme")
    print("   ✅ Integrated trading dashboard")
    print("   ✅ Real-time position monitoring")
    print("   ✅ Dynamic risk management display")
    print("   ✅ Hard close rules visualization")
    print("   ✅ Advanced analytics")
    print("   ✅ Responsive design")
    print()
    
    # Get the modern UI file
    ui_file = Path(__file__).parent / "app" / "main_ui_modern.py"
    
    if not ui_file.exists():
        print("❌ Error: Modern UI file not found!")
        print(f"   Looking for: {ui_file}")
        sys.exit(1)
    
    print(f"📂 UI File: {ui_file}")
    print()
    
    # Launch Streamlit
    try:
        print("⏳ Launching Streamlit server...")
        print("   🌐 Dashboard will open at: http://localhost:8501")
        print()
        print("   Press Ctrl+C to stop the server")
        print()
        
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(ui_file), 
             "--logger.level=info", "--client.showErrorDetails=true"],
            cwd=Path(__file__).parent
        )
    
    except KeyboardInterrupt:
        print("\n\n✅ UI server stopped")
        sys.exit(0)
    
    except Exception as e:
        print(f"❌ Error launching UI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
