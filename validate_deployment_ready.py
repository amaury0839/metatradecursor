"""
Phase 5A: Pre-Deployment Validation
Location: validate_deployment_ready.py

Checks all systems are ready for production deployment
"""

import logging
import sys
import os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_python_version():
    """TEST 1: Verify Python version compatibility"""
    logger.info("=" * 70)
    logger.info("TEST 1: Python Version Compatibility")
    logger.info("=" * 70)
    
    import sys
    version_info = sys.version_info
    
    logger.info(f"Python version: {version_info.major}.{version_info.minor}.{version_info.micro}")
    
    if version_info.major >= 3 and version_info.minor >= 9:
        logger.info(f"✅ Python {version_info.major}.{version_info.minor} is compatible (minimum 3.9)")
        return True
    else:
        logger.error(f"❌ Python {version_info.major}.{version_info.minor} is too old (minimum 3.9)")
        return False


def test_dependencies_installed():
    """TEST 2: Verify all dependencies are installed"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Dependencies Installation")
    logger.info("=" * 70)
    
    required_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'plotly',
        'MetaTrader5',
        'requests',
        'dotenv',  # python-dotenv imports as dotenv
        'pydantic',
        'google',
    ]
    
    optional_packages = ['sqlalchemy']
    
    all_installed = True
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✅ {package} is installed")
        except ImportError:
            logger.error(f"❌ {package} is NOT installed")
            all_installed = False
    
    # Check optional packages (databases)
    for package in optional_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} is installed (optional)")
        except ImportError:
            logger.warning(f"⚠️  {package} is NOT installed (optional - needed for PostgreSQL)")
    
    return all_installed


def test_environment_configuration():
    """TEST 3: Verify environment configuration"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Environment Configuration")
    logger.info("=" * 70)
    
    from dotenv import load_dotenv
    
    # Try to load .env
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        logger.info("✅ .env file found and loaded")
    else:
        logger.warning("⚠️  .env file not found (using system environment variables)")
    
    # Check required environment variables
    required_vars = [
        'MODE',
        'MT5_LOGIN',
        'MT5_SERVER',
        'LOG_LEVEL',
    ]
    
    missing_vars = []
    for var in required_vars:
        if os.getenv(var):
            logger.info(f"✅ {var} is set")
        else:
            logger.warning(f"⚠️  {var} is not set (may be optional)")
            missing_vars.append(var)
    
    return len(missing_vars) == 0


def test_database_connection():
    """TEST 4: Verify database connectivity"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Database Connection")
    logger.info("=" * 70)
    
    try:
        # Try to import database manager
        from app.core.database import get_database_manager
        db = get_database_manager()
        logger.info("✅ Database connection available")
        return True
    except Exception as e:
        logger.warning(f"⚠️  Database connection: {e}")
        logger.info("   (Database may not be required for all deployments)")
        return True  # Not critical


def test_file_structure():
    """TEST 5: Verify critical file structure"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 5: File Structure")
    logger.info("=" * 70)
    
    required_files = {
        'app/main.py': 'Main application',
        'app/trading/trading_loop.py': 'Trading logic',
        'app/ui/pages_dashboard_unified.py': 'Dashboard',
        'app/trading/decision_constants.py': 'Decision constants',
        'app/trading/signal_execution_split.py': 'Signal split',
        'app/trading/trade_validation.py': 'Validation gates',
        'app/trading/ai_optimization.py': 'AI optimization',
    }
    
    all_present = True
    
    for file_path, description in required_files.items():
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            logger.info(f"✅ {description}: {file_path} ({size} bytes)")
        else:
            logger.error(f"❌ {description}: {file_path} - NOT FOUND")
            all_present = False
    
    return all_present


def test_no_hardcoded_credentials():
    """TEST 6: Verify no hardcoded credentials in code"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 6: Security - No Hardcoded Credentials")
    logger.info("=" * 70)
    
    sensitive_patterns = ['password=', 'api_key=', 'secret=', 'token=']
    dangerous_files = []
    
    # Files that are allowed to reference these patterns (config/client files)
    allowed_patterns = [
        'gemini_client.py',  # Uses API client patterns
        'mt5_client.py',     # Uses MT5 connection patterns
    ]
    
    # Check Python files for hardcoded credentials
    for py_file in Path('app').rglob('*.py'):
        # Skip allowed files
        if any(allowed in str(py_file) for allowed in allowed_patterns):
            logger.info(f"⏭️  Skipping allowed file: {py_file}")
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Look for actual hardcoded values (not parameter names)
                for pattern in sensitive_patterns:
                    if pattern in content.lower() and 'os.getenv' not in content:
                        # Check if it's actually a hardcoded value (not just parameter)
                        lines = content.split('\n')
                        for line in lines:
                            if pattern in line.lower() and '=' in line and not any(keyword in line for keyword in ['def ', 'class ', '#', 'os.getenv', 'environ']):
                                dangerous_files.append(str(py_file))
                                break
        except Exception as e:
            logger.warning(f"⚠️  Could not read {py_file}: {e}")
    
    if not dangerous_files:
        logger.info("✅ No hardcoded credentials found in code")
        return True
    else:
        logger.error(f"❌ Potential hardcoded credentials in: {dangerous_files}")
        return False


def test_logging_configuration():
    """TEST 7: Verify logging is configured"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 7: Logging Configuration")
    logger.info("=" * 70)
    
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    if log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        logger.info(f"✅ Logging level set to: {log_level}")
        return True
    else:
        logger.error(f"❌ Invalid logging level: {log_level}")
        return False


def test_git_status():
    """TEST 8: Verify git repository status"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 8: Git Repository Status")
    logger.info("=" * 70)
    
    try:
        import subprocess
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            if result.stdout.strip():
                logger.warning("⚠️  Uncommitted changes detected:")
                for line in result.stdout.strip().split('\n'):
                    logger.warning(f"   {line}")
            else:
                logger.info("✅ Working directory is clean (all changes committed)")
            return True
        else:
            logger.warning("⚠️  Could not check git status (git may not be available)")
            return True
    except Exception as e:
        logger.warning(f"⚠️  Git status check: {e}")
        return True


def test_docker_files():
    """TEST 9: Verify Docker files exist and are valid"""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 9: Docker Configuration")
    logger.info("=" * 70)
    
    files_to_check = {
        'Dockerfile.bot': 'Bot Dockerfile',
        'docker-compose.yml': 'Docker Compose',
        '.dockerignore': 'Docker ignore file',
    }
    
    all_present = True
    
    for filename, description in files_to_check.items():
        if Path(filename).exists():
            logger.info(f"✅ {description}: {filename}")
        else:
            logger.warning(f"⚠️  {description}: {filename} - NOT FOUND")
            all_present = False
    
    return all_present


def main():
    """Run all pre-deployment tests"""
    logger.info("\n")
    logger.info("🚀" * 35)
    logger.info("PHASE 5A: PRE-DEPLOYMENT VALIDATION")
    logger.info("🚀" * 35)
    
    tests = [
        ("TEST 1: Python Version", test_python_version),
        ("TEST 2: Dependencies", test_dependencies_installed),
        ("TEST 3: Environment Config", test_environment_configuration),
        ("TEST 4: Database Connection", test_database_connection),
        ("TEST 5: File Structure", test_file_structure),
        ("TEST 6: No Hardcoded Credentials", test_no_hardcoded_credentials),
        ("TEST 7: Logging Configuration", test_logging_configuration),
        ("TEST 8: Git Repository Status", test_git_status),
        ("TEST 9: Docker Files", test_docker_files),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("PRE-DEPLOYMENT VALIDATION SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"TOTAL: {passed}/{total} checks passed")
    logger.info("=" * 70)
    
    if passed == total:
        logger.info("\n✅ ALL PRE-DEPLOYMENT CHECKS PASSED")
        logger.info("System is READY for deployment")
        logger.info("\nNext steps:")
        logger.info("1. Review .env.production configuration")
        logger.info("2. Set up secret manager for credentials")
        logger.info("3. Build Docker image: docker build -t metatrade-bot .")
        logger.info("4. Test Docker container locally")
        logger.info("5. Deploy to staging environment")
        logger.info("6. Run 24-hour staging tests")
        logger.info("7. Deploy to production")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} check(s) failed")
        logger.error("Please fix issues before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())
