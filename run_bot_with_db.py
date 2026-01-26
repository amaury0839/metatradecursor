#!/usr/bin/env python3
"""
Run Trading Bot with Database System Active
Automatically initializes database and starts UI with all features
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def print_banner():
    """Print startup banner"""
    print("\n" + "="*80)
    print(" 🤖 AI Forex Trading Bot with Database System")
    print("="*80)
    print(f" ⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" 📁 Working Directory: {os.getcwd()}")
    print("\n Features Active:")
    print("  ✅ Enhanced AI Decision Engine")
    print("  ✅ Smart Router (Enhanced + Simple fallback)")
    print("  ✅ SQLite Historical Database")
    print("  ✅ Automatic Analysis Saving")
    print("  ✅ Automatic Decision Tracking")
    print("  ✅ Automatic Trade Logging")
    print("  ✅ Analytics Dashboard (📉 Analytics tab)")
    print("  ✅ Historical Data Visualization")
    print("\n Database Components:")
    print("  • analysis_history - All technical & sentiment analysis")
    print("  • ai_decisions - All AI decisions (Enhanced vs Simple)")
    print("  • trades - All open/closed trades with P&L")
    print("  • performance_metrics - Win rate, profit factor, drawdown")
    print("  • web_search_cache - Cached web search results")
    print("\n" + "="*80 + "\n")


def main():
    """Main entry point"""
    try:
        # Print banner
        print_banner()
        
        # Initialize database
        print("🗄️  Initializing database system...")
        from app.core.database import get_database_manager
        db = get_database_manager()
        
        trades_count = len(db.get_trades()) if db.get_trades() else 0
        decisions_count = len(db.get_ai_decisions()) if db.get_ai_decisions() else 0
        analysis_count = len(db.get_analysis_history()) if db.get_analysis_history() else 0
        
        print(f"✅ Database ready:")
        print(f"   • {trades_count} trades")
        print(f"   • {decisions_count} AI decisions")
        print(f"   • {analysis_count} analysis records\n")
        
        # Start Streamlit UI
        print("🚀 Starting Streamlit UI...")
        print("   Open browser: http://localhost:8501")
        print("   Navigate to '📉 Analytics' tab to view historical data")
        print("   Check '📚 History' tab for detailed records\n")
        print("="*80 + "\n")
        
        # Import and run Streamlit
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app/ui_improved.py"],
            cwd=Path(__file__).parent
        )
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Bot stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
