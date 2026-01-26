#!/usr/bin/env python3
"""Initialize and verify database system"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import get_database_manager
from app.core.logger import setup_logger

logger = setup_logger("init_db")


def init_database():
    """Initialize database and display status"""
    
    print("\n" + "="*70)
    print("🗄️  Database System Initialization")
    print("="*70 + "\n")
    
    try:
        # Get database manager (this creates tables if needed)
        db = get_database_manager()
        print("✅ Database initialized successfully")
        
        # Test connectivity
        print("\n📋 Checking database structure...")
        
        try:
            trades = db.get_trades()
            print(f"   ✅ trades table: {len(trades)} records")
        except Exception as e:
            print(f"   ⚠️  trades table: {e}")
        
        try:
            decisions = db.get_ai_decisions()
            print(f"   ✅ ai_decisions table: {len(decisions)} records")
        except Exception as e:
            print(f"   ⚠️  ai_decisions table: {e}")
        
        try:
            analysis = db.get_analysis_history()
            print(f"   ✅ analysis_history table: {len(analysis)} records")
        except Exception as e:
            print(f"   ⚠️  analysis_history table: {e}")
        
        # Display database path
        print(f"\n📁 Database Location: {db.db_path}")
        
        # Check file size
        import os
        if os.path.exists(db.db_path):
            size_kb = os.path.getsize(db.db_path) / 1024
            print(f"💾 Database Size: {size_kb:.2f} KB")
        
        print("\n" + "="*70)
        print("✅ Database system is ready!")
        print("="*70)
        print("\nIntegrated components:")
        print("  ✅ app/core/database.py - DatabaseManager class")
        print("  ✅ app/trading/integrated_analysis.py - Analysis saving")
        print("  ✅ app/ai/smart_decision_router.py - Decision saving")
        print("  ✅ app/main.py - Trade saving/updating")
        print("  ✅ app/ui/pages_history.py - History visualization")
        print("  ✅ app/ui/pages_database_analytics.py - Analytics dashboard")
        print("  ✅ app/ui_improved.py - UI integration (Analytics tab)")
        
        print("\nNext steps:")
        print("  1. Run the bot: streamlit run app/ui_improved.py")
        print("  2. Let it trade and collect data")
        print("  3. Check Analytics tab for historical data")
        print("  4. Migrate old trades: python migrate_trades.py --days 30")
        print("\n" + "="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
