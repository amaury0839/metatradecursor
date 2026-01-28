"""
Integration helpers for including optimized components in existing main.py
"""

# ============================================================================
# ADD THIS TO THE TOP OF YOUR EXISTING main.py
# ============================================================================

"""
# Import optimization components
from app.integration.performance_controller import (
    get_performance_controller,
    get_ui_monitor,
    get_refresh_manager
)
from app.trading.indicator_optimizer import get_indicator_optimizer
from app.ui.cache_manager import get_cache, get_historical_cache
"""

# ============================================================================
# ADD THIS TO YOUR MAIN STARTUP (after config loading)
# ============================================================================

"""
def setup_optimization_system():
    '''Initialize optimization system before trading loop'''
    logger.info("Setting up optimization system...")
    
    # Initialize caches
    cache = get_cache()
    hist_cache = get_historical_cache()
    logger.info(f"Cache system initialized")
    
    # Start continuous optimization
    controller = get_performance_controller()
    controller.run_continuous_optimization(interval_minutes=60)
    logger.info("Continuous optimization started (every 60 minutes)")
    
    # Initialize UI monitor
    monitor = get_ui_monitor()
    logger.info("UI performance monitor initialized")
    
    # Initialize refresh manager
    manager = get_refresh_manager()
    logger.info("Data refresh manager initialized")
    
    return controller, monitor, manager
"""

# ============================================================================
# ADD THIS IN YOUR MAIN TRADING LOOP
# ============================================================================

"""
def main_trading_loop():
    '''Main trading loop with optimization integration'''
    
    # Setup optimization (one time)
    controller, monitor, manager = setup_optimization_system()
    
    # Your existing trading loop
    while True:
        try:
            # ... your existing trading logic ...
            
            # OPTIONAL: Monitor UI performance
            # import time
            # start = time.time()
            # ... do work ...
            # monitor.record_load_time("trading_cycle", (time.time() - start) * 1000)
            
            # OPTIONAL: Check if refresh needed
            # recommendations = manager.get_refresh_recommendations()
            # if recommendations['recommendations']:
            #     logger.info(f"Refresh recommended: {recommendations}")
            #     cache.clear()
            
            time.sleep(30)  # Main loop interval
            
        except Exception as e:
            logger.error(f"Trading loop error: {e}")
            time.sleep(5)
"""

# ============================================================================
# EXAMPLE: FULL INTEGRATION SNIPPET
# ============================================================================

INTEGRATION_EXAMPLE = """
# At the top of app/main.py, add these imports:

from app.integration.performance_controller import get_performance_controller
from app.ui.cache_manager import get_cache

# In your main_trading_loop() function, add at the beginning:

def main_trading_loop():
    # ... existing setup code ...
    
    # Initialize optimization
    logger.info("Initializing optimization system...")
    controller = get_performance_controller()
    controller.run_continuous_optimization(interval_minutes=60)
    
    # Main loop
    while True:
        try:
            # ... your existing trading logic (unchanged) ...
            
            # Periodically check optimization status (optional)
            if iteration % 120 == 0:  # Every 120 iterations (60 minutes)
                status = controller.get_optimization_status()
                logger.info(f"Optimization status: {status}")
            
            time.sleep(30)  # or your existing interval
            iteration += 1
            
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(5)
"""

# ============================================================================
# API INTEGRATION FOR FastAPI main app
# ============================================================================

API_INTEGRATION_EXAMPLE = """
# In your FastAPI app (app/api/main.py or wherever you initialize FastAPI):

from fastapi import FastAPI
from app.api.optimized_endpoints import router as optimized_router

app = FastAPI(title="Trading Bot API")

# Include optimized endpoints
app.include_router(optimized_router)

# Your existing routes...
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
"""

# ============================================================================
# STREAMLIT UI INTEGRATION
# ============================================================================

UI_INTEGRATION_EXAMPLE = """
# Option A: Run optimized UI directly
streamlit run app/ui_optimized.py

# Option B: Keep your existing UI and add imports from cache_manager
# In your existing UI pages, add at the top:

from app.ui.cache_manager import streamlit_cache, get_cache

# Then decorate any function that fetches data:

@streamlit_cache(ttl=10)
def load_my_data():
    # Your data loading code
    return data

# Option C: Import both old and new UI components
# In your main page, use tabs to switch:

tab1, tab2 = st.tabs(["Old Dashboard", "Optimized Dashboard"])
with tab1:
    # Run your old dashboard
    old_dashboard()
with tab2:
    # Run optimized dashboard
    from app.ui_optimized import render_dashboard
    render_dashboard()
"""

# ============================================================================
# MINIMAL INTEGRATION (Easiest)
# ============================================================================

MINIMAL_INTEGRATION = """
# Add just 2 lines to your main.py to enable optimization:

# At top of file:
from app.integration.performance_controller import get_performance_controller

# In your main() or startup:
def main():
    # ... existing code ...
    
    # Add this one line to enable continuous optimization:
    get_performance_controller().run_continuous_optimization()
    
    # Rest of your code...
"""

# ============================================================================
# FULL INTEGRATION CLASS (For production)
# ============================================================================

FULL_INTEGRATION_CLASS = """
from app.integration.performance_controller import (
    get_performance_controller,
    get_ui_monitor,
    get_refresh_manager
)
from app.trading.indicator_optimizer import get_indicator_optimizer

class OptimizedTradingSystem:
    '''Wrapper for complete optimized trading system'''
    
    def __init__(self):
        self.perf_controller = get_performance_controller()
        self.ui_monitor = get_ui_monitor()
        self.refresh_manager = get_refresh_manager()
        self.optimizer = get_indicator_optimizer()
    
    def start(self):
        '''Start all optimization systems'''
        logger.info("Starting optimized trading system...")
        self.perf_controller.run_continuous_optimization(interval_minutes=60)
        logger.info("✅ Optimization system started")
    
    def get_status(self):
        '''Get system status'''
        return {
            "optimization": self.perf_controller.get_optimization_status(),
            "ui_performance": self.ui_monitor.get_performance_stats(),
            "refresh_recommendations": self.refresh_manager.get_refresh_recommendations()
        }
    
    def run_optimization_now(self):
        '''Run optimization immediately'''
        return self.perf_controller.manual_optimization()

# Usage:
system = OptimizedTradingSystem()
system.start()
status = system.get_status()
"""

# ============================================================================
# CONFIGURATION OPTIONS
# ============================================================================

CONFIGURATION_GUIDE = """
# Configure optimization timing:
controller.run_continuous_optimization(interval_minutes=60)  # Default
controller.run_continuous_optimization(interval_minutes=30)  # More frequent
controller.run_continuous_optimization(interval_minutes=120) # Less frequent

# Configure cache TTL (in ui_optimized.py):
@streamlit_cache(ttl=10)   # 10 seconds
@streamlit_cache(ttl=5)    # 5 seconds (faster, more API calls)
@streamlit_cache(ttl=30)   # 30 seconds (slower refresh, fewer API calls)

# Configure refresh rules (in performance_controller.py):
self.refresh_rules = {
    "account_info": {"ttl": 10, "priority": "high"},
    "open_positions": {"ttl": 15, "priority": "high"},
    "trade_history": {"ttl": 300, "priority": "medium"},
    "performance_metrics": {"ttl": 300, "priority": "medium"},
    "analysis": {"ttl": 600, "priority": "low"}
}
"""

# ============================================================================
# TROUBLESHOOTING INTEGRATION
# ============================================================================

TROUBLESHOOTING = """
# If optimization not running:
status = get_performance_controller().get_optimization_status()
print(status)

# If API endpoints not available:
# Make sure app/api/main.py includes:
from app.api.optimized_endpoints import router as optimized_router
app.include_router(optimized_router)

# If UI is still slow:
# Check cache is working:
from app.ui.cache_manager import get_cache
cache = get_cache()
print(f"Cache items: {len(cache.cache)}")

# If memory usage high:
# Clear cache:
get_cache().clear()
get_historical_cache().clear()

# If DB queries slow:
# Check if indices exist:
db = get_database_manager()
db.create_indices()

# Monitor optimization:
controller = get_performance_controller()
status = controller.get_optimization_status()
print(f"Last optimization: {status['last_optimization']}")
"""

# ============================================================================
# QUICK START SCRIPT
# ============================================================================

QUICK_START_SCRIPT = """
#!/usr/bin/env python3
'''Quick integration test'''

import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from app.integration.performance_controller import get_performance_controller
from app.ui.cache_manager import get_cache
from app.trading.indicator_optimizer import get_indicator_optimizer
from app.core.logger import setup_logger

logger = setup_logger("integration_test")

def test_integration():
    '''Test all optimization components'''
    
    logger.info("Testing integration components...")
    
    # Test 1: Cache system
    logger.info("✓ Testing cache system...")
    cache = get_cache()
    cache.set("test", {"value": 123})
    assert cache.get("test") == {"value": 123}
    cache.clear()
    
    # Test 2: Optimization controller
    logger.info("✓ Testing optimization controller...")
    controller = get_performance_controller()
    status = controller.get_optimization_status()
    assert "is_optimizing" in status
    
    # Test 3: Indicator optimizer
    logger.info("✓ Testing indicator optimizer...")
    optimizer = get_indicator_optimizer()
    analysis = optimizer.analyze_performance(hours=24)
    assert "error" in analysis or "total_trades" in analysis
    
    logger.info("✅ All integration tests passed!")
    return True

if __name__ == "__main__":
    test_integration()
"""

# ============================================================================
# SUMMARY
# ============================================================================

print("""
╔═════════════════════════════════════════════════════════════════════════╗
║            OPTIMIZATION INTEGRATION GUIDE                              ║
╚═════════════════════════════════════════════════════════════════════════╝

Quick Integration Options:

1. MINIMAL (1 line):
   get_performance_controller().run_continuous_optimization()

2. STANDARD (5-10 lines):
   - Import components
   - Initialize in main()
   - Start optimization loop

3. FULL (Production):
   - Complete OptimizedTradingSystem class
   - Status monitoring
   - Performance tracking
   - Logging integration

See examples above for your use case.
""")
