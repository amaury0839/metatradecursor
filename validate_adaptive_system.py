#!/usr/bin/env python3
"""Validate adaptive optimization system setup"""

import sys
from pathlib import Path

# Add workspace to path
workspace_root = Path(__file__).parent
sys.path.insert(0, str(workspace_root))

def check_file_exists(path: str) -> bool:
    """Check if file exists"""
    full_path = workspace_root / path
    exists = full_path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {path}")
    return exists

def try_import(module_path: str, module_name: str) -> bool:
    """Try to import module"""
    try:
        # Dynamic import
        parts = module_name.split('.')
        mod = __import__(module_name)
        for part in parts[1:]:
            mod = getattr(mod, part)
        print(f"✅ Import: {module_name}")
        return True
    except Exception as e:
        print(f"❌ Import: {module_name} - {e}")
        return False

def main():
    print("=" * 60)
    print("ADAPTIVE OPTIMIZATION SYSTEM VALIDATION")
    print("=" * 60)
    
    print("\n📋 CHECKING FILES:")
    print("-" * 60)
    
    files_ok = all([
        check_file_exists("app/trading/adaptive_optimizer.py"),
        check_file_exists("app/trading/optimization_scheduler.py"),
        check_file_exists("app/trading/parameter_injector.py"),
        check_file_exists("app/main.py"),
        check_file_exists("run_bot.py"),
    ])
    
    print("\n🔗 CHECKING IMPORTS:")
    print("-" * 60)
    
    imports_ok = all([
        try_import("app.trading", "app.trading.adaptive_optimizer"),
        try_import("app.trading", "app.trading.optimization_scheduler"),
        try_import("app.trading", "app.trading.parameter_injector"),
    ])
    
    print("\n🔍 CHECKING INTEGRATION:")
    print("-" * 60)
    
    # Check main.py has parameter_injector import
    try:
        with open(workspace_root / "app/main.py", "r", encoding="utf-8", errors="ignore") as f:
            main_content = f.read()
        
        checks = [
            ("parameter_injector import" in main_content, "parameter_injector imported in main.py"),
            ("param_injector = get_parameter_injector()" in main_content, "param_injector instantiated"),
            ("param_injector.should_trade_symbol" in main_content, "should_trade_symbol called"),
            ("param_injector.get_max_risk_pct_for_symbol" in main_content, "get_max_risk_pct_for_symbol called"),
        ]
        
        for check, desc in checks:
            status = "✅" if check else "❌"
            print(f"{status} {desc}")
        
        integration_ok = all(c[0] for c in checks)
    except Exception as e:
        print(f"❌ Error checking main.py: {e}")
        integration_ok = False
    
    # Check run_bot.py has scheduler
    try:
        with open(workspace_root / "run_bot.py", "r", encoding="utf-8", errors="ignore") as f:
            run_content = f.read()
        
        scheduler_ok = "start_optimization_scheduler" in run_content
        status = "✅" if scheduler_ok else "❌"
        print(f"{status} Scheduler imported in run_bot.py")
    except Exception as e:
        print(f"❌ Error checking run_bot.py: {e}")
        scheduler_ok = False
    
    print("\n📊 SUMMARY:")
    print("-" * 60)
    
    all_ok = files_ok and imports_ok and integration_ok and scheduler_ok
    if all_ok:
        print("✅ ALL CHECKS PASSED")
        print("\nSystem is ready for deployment!")
        print("\nNext steps:")
        print("1. python run_bot.py")
        print("2. Monitor logs for optimization scheduler initialization")
        print("3. Wait for top of next hour to see optimization cycle")
        print("4. Check data/adaptive_params.json for updated parameters")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease review the failures above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
