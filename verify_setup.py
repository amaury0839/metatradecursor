"""Script to verify setup and dependencies"""

import sys
from pathlib import Path


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"❌ Python 3.11+ required. Current: {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    required = [
        "streamlit",
        "pandas",
        "numpy",
        "pydantic",
        "MetaTrader5",
        "google.generativeai",
        "httpx",
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace(".", "_") if "." in package else package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing.append(package)
    
    return len(missing) == 0


def check_env_file():
    """Check if .env file exists"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  .env file not found. Copy .env.example to .env and configure it.")
        else:
            print("❌ .env.example not found")
        return False
    
    print("✅ .env file exists")
    return True


def check_directories():
    """Check if required directories exist"""
    dirs = ["app", "data", "tests", "logs"]
    all_exist = True
    
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {dir_name}/ directory exists")
        else:
            print(f"⚠️  {dir_name}/ directory missing (will be created automatically)")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    return True


def main():
    """Run all checks"""
    print("=" * 50)
    print("AI Forex Trading Bot - Setup Verification")
    print("=" * 50)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        (".env File", check_env_file),
        ("Directories", check_directories),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        result = check_func()
        results.append((name, result))
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("=" * 50)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n✅ All checks passed! You're ready to run the bot.")
        print("\nTo start:")
        print("  streamlit run app/main.py")
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        print("\nTo install dependencies:")
        print("  pip install -r requirements.txt")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
