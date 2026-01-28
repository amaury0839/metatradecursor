# 🧪 ADAPTIVE OPTIMIZATION - TEST & VALIDATION PLAN

## Overview
This document provides step-by-step instructions to validate that the adaptive optimization system is working correctly.

**Estimated Time**: 2 hours (to see first optimization cycle)

---

## PHASE 1: Pre-Deployment Validation (5 min)

### Step 1.1: Run System Validation Script
```bash
python validate_adaptive_system.py
```

**Expected Output**:
```
✅ ALL CHECKS PASSED
System is ready for deployment!
```

**If Failed**: Check the error messages and ensure all files exist.

---

### Step 1.2: Verify File Structure
```bash
ls -la app/trading/adaptive_optimizer.py
ls -la app/trading/optimization_scheduler.py
ls -la app/trading/parameter_injector.py
cat data/adaptive_params.json    # May not exist yet - that's OK
```

**Expected**:
- ✅ Three modules exist
- ✅ `data/` directory exists (JSON file may be created later)

---

### Step 1.3: Check Log Directory
```bash
mkdir -p logs
ls -la logs/
```

**Expected**:
- ✅ `logs/` directory ready for storing output

---

## PHASE 2: Bot Startup (5 min)

### Step 2.1: Start the Bot
```bash
python run_bot.py
```

**Expected Initial Output** (within first 30 seconds):
```
✅ Optimization scheduler started (will optimize every hour)
🎯 Trading symbols (optimized, no market check): [EURUSD, GBPUSD, BTCUSD, ...]
✅ MT5 connected - using live account data
```

**If NOT Seen**:
- Check for errors in bot output
- Verify MT5 connection
- Check Gemini API key configuration

### Step 2.2: Let Bot Run for 5 Minutes
Watch the logs for normal trading activity:
```
✅ DECISION OK: EURUSD BUY - proceeding to stop validation
📊 SIZING: EURUSD volume=0.0200 (adaptive_risk=1.50%)
✅ Order executed: ticket=1234567
```

**Expected**: 
- ✅ Trading happens normally
- ✅ No errors related to parameter_injector or optimizer
- ✅ Adaptive risk percentages appear in sizing logs

---

## PHASE 3: Adaptive Parameter Validation (15 min)

### Step 3.1: Check Initial Parameter File
After bot has run for 5 minutes:
```bash
cat data/adaptive_params.json
```

**Note**: File may be empty or not exist yet. That's normal - it gets created/updated at optimization time.

### Step 3.2: Watch for Adaptive Symbol Checks
In bot logs, look for lines like:
```
⏭️  SKIPPED GBPUSD (adaptive): Win rate below threshold
✅ Trading allowed: EURUSD (performance check passed)
```

**Expected**:
- ✅ Adaptive checks appear in logs
- ✅ Some symbols may be skipped initially (normal)
- ✅ No errors in parameter_injector calls

### Step 3.3: Verify Sizing with Adaptive Parameters
Look for sizing logs:
```
📊 SIZING: EURUSD volume=0.0200 (adaptive_risk=1.50%)
📊 SIZING: BTCUSD volume=0.0150 (adaptive_risk=1.80%)
```

**Expected**:
- ✅ Adaptive risk percentages shown
- ✅ Risk values in range 0.5% - 3.0%
- ✅ Different symbols may have different risk %
- ✅ No errors in calculation

---

## PHASE 4: Hourly Optimization Cycle (Variable - up to 2 hours)

### Step 4.1: Wait for Top of Hour
The optimization cycle runs at top of every hour (00 minutes).

**To speed up testing**: If you can't wait, you can manually trigger it:
```python
python -c "
from app.trading.adaptive_optimizer import AdaptiveRiskOptimizer
opt = AdaptiveRiskOptimizer()
results = opt.hourly_optimization_cycle()
print(f'Optimization complete: {results}')
"
```

### Step 4.2: Monitor Optimization Logs
At the top of the hour, you should see:
```
🔄 HOURLY ADAPTIVE OPTIMIZATION CYCLE STARTED
├─ Analyzing EURUSD: 12 trades in last hour
│  ├─ Win Rate: 58.3%
│  ├─ Profit Factor: 1.45x
│  ├─ Avg Win: $15.50
│  └─ Avg Loss: -$10.75
├─ AI Optimization for EURUSD: increase
│  ├─ Win Rate 58.3% >= 55% threshold → recommend increase
│  ├─ Current: max_risk=1.5%, max_pos=2
│  ├─ Recommended: max_risk=1.8%, max_pos=3
│  └─ Applied with safety bounds
├─ Saved updated parameters
...
✅ OPTIMIZATION CYCLE COMPLETE: 20 tickers analyzed
```

**What to Check**:
- ✅ Cycle starts at top of hour
- ✅ Each symbol is analyzed
- ✅ Performance metrics calculated
- ✅ AI recommendations shown
- ✅ Parameters applied
- ✅ No errors or exceptions

### Step 4.3: Verify Parameter Update
After optimization, check the file:
```bash
cat data/adaptive_params.json
```

**Expected Format**:
```json
{
    "EURUSD": {
        "max_risk_pct": 1.8,
        "max_positions_per_ticker": 3,
        "min_win_rate_pct": 40.0,
        "last_updated": "2026-01-28T14:00:00"
    },
    "GBPUSD": {
        "max_risk_pct": 1.0,
        "max_positions_per_ticker": 1,
        "min_win_rate_pct": 45.0,
        "last_updated": "2026-01-28T14:00:00"
    },
    ...
}
```

**What to Check**:
- ✅ JSON is valid format
- ✅ All configured symbols present
- ✅ Parameters in valid ranges (0.5%-3% risk, 1-5 positions)
- ✅ Timestamps updated to current time
- ✅ File is readable and complete

---

## PHASE 5: Post-Optimization Trading (15 min)

### Step 5.1: Verify Trading Uses New Parameters
After optimization, watch trading logs for:
```
📊 SIZING: EURUSD volume=0.0240 (adaptive_risk=1.80%)
✅ Trading allowed: BTCUSD (min_wr_pct=35% < actual 60%)
⏭️  SKIPPED GBPUSD (adaptive): Win rate 30% below threshold 45%
```

**Expected**:
- ✅ Risk percentages match newly optimized values
- ✅ Position limits reflect new recommendations
- ✅ Symbol blocking uses updated thresholds

### Step 5.2: Monitor for Continued Optimization
The system should optimize again at the next hour:
```
Next optimization in 45 minutes...
Next optimization in 30 minutes...
Next optimization in 15 minutes...
🔄 HOURLY ADAPTIVE OPTIMIZATION CYCLE STARTED
```

**Expected**:
- ✅ Each hour brings new optimization
- ✅ Parameters evolve based on trading performance
- ✅ System is self-healing and adaptive

---

## PHASE 6: Extended Validation (24+ hours)

### Step 6.1: Multi-Hour Parameter Evolution
Run for 24+ hours and track:
```bash
# View parameter history
tail -f data/adaptive_params.json

# Count optimizations
grep "OPTIMIZATION CYCLE COMPLETE" run.log | wc -l

# Analyze parameter changes
grep "AI Optimization for" run.log | head -20
grep "Updated.*Risk.*→" run.log | head -20
```

**Expected**:
- ✅ 24+ optimization cycles (one per hour)
- ✅ Parameters changing based on performance
- ✅ Different risk % for different symbols
- ✅ Positive-WR symbols getting higher risk
- ✅ Negative-WR symbols getting lower risk

### Step 6.2: Compare Performance Before/After
```bash
# Extract win rates before optimization
grep "Analyzing EURUSD: .* trades" run.log | head -1

# Extract win rates after N hours
grep "Analyzing EURUSD: .* trades" run.log | tail -1

# Should show improvement or at least consistent performance
```

**Expected**:
- ✅ Win rates stable or improving
- ✅ Parameter adjustments respond to performance
- ✅ Aggressive symbols remain aggressive
- ✅ Struggling symbols become conservative

### Step 6.3: Verify Persistence
Stop and restart the bot:
```bash
# Stop current bot (Ctrl+C or kill process)
# Check that data is preserved
cat data/adaptive_params.json

# Restart bot
python run_bot.py

# Verify it uses saved parameters
grep "Loading adaptive parameters" run.log
```

**Expected**:
- ✅ Parameters persisted across restart
- ✅ Next optimization builds on previous data
- ✅ No parameter resets on restart

---

## TROUBLESHOOTING CHECKLIST

### Problem: "Optimization scheduler started" not in logs
**Solutions**:
- [ ] Check run_bot.py includes optimization scheduler import
- [ ] Verify optimization_scheduler.py exists
- [ ] Check for import errors in bot output

### Problem: No optimization logs at top of hour
**Solutions**:
- [ ] Wait until next hour boundary (bot must be running)
- [ ] Check that bot has been running > 60 minutes
- [ ] Verify at least 1 trade per symbol in last hour
- [ ] Check logs for "HOURLY ADAPTIVE OPTIMIZATION CYCLE"

### Problem: "No module named parameter_injector"
**Solutions**:
- [ ] Verify parameter_injector.py exists in app/trading/
- [ ] Check main.py has correct import statement
- [ ] Verify Python path includes workspace root
- [ ] Run validate_adaptive_system.py to diagnose

### Problem: Parameters not updating in JSON file
**Solutions**:
- [ ] Check data/ directory is writable
- [ ] Verify optimization cycle completed (see logs)
- [ ] Check for errors in AI/Gemini API calls
- [ ] Ensure database has trade history

### Problem: Trading blocked unexpectedly
**Solutions**:
- [ ] Check adaptive_params.json for current thresholds
- [ ] Verify symbol's actual win rate
- [ ] Look for "SKIPPED...adaptive" messages in logs
- [ ] Check can_trade_symbol() logic in injector

### Problem: Extreme parameter values (>3% risk, >5 positions)
**Solutions**:
- [ ] This shouldn't happen - safety bounds enforce limits
- [ ] If it does, delete data/adaptive_params.json
- [ ] Bot will regenerate with valid defaults
- [ ] Check apply_optimization() in optimizer for bounds

---

## VALIDATION CHECKLIST

Mark these off as you progress:

### Pre-Deployment
- [ ] validate_adaptive_system.py passes all checks
- [ ] All three modules exist and are importable
- [ ] No import errors in Python

### Bot Startup
- [ ] "Optimization scheduler started" appears in logs
- [ ] MT5 connection successful
- [ ] Trading begins normally
- [ ] No errors related to parameter_injector

### Adaptive Parameters
- [ ] "adaptive_risk=X.XX%" appears in sizing logs
- [ ] Symbol checks show adaptive validation
- [ ] Different symbols have different risk %
- [ ] Risk values in range 0.5%-3.0%

### Optimization Cycle
- [ ] Cycle starts at top of hour
- [ ] All symbols analyzed
- [ ] Performance metrics calculated
- [ ] AI recommendations received
- [ ] Parameters saved to JSON file
- [ ] No errors or exceptions

### Post-Optimization
- [ ] New parameters used in next trades
- [ ] Risk sizing reflects new values
- [ ] Symbol blocking updated per new thresholds
- [ ] Trading continues without issues

### Extended Operation
- [ ] 24+ hours of continuous operation
- [ ] Multiple optimization cycles (1 per hour)
- [ ] Parameters evolving per performance
- [ ] System handling edge cases gracefully

---

## Success Criteria

✅ **System is working correctly if**:
1. Optimization scheduler starts automatically with bot
2. Adaptive parameters appear in trading loop logs
3. Hourly optimization cycle completes without errors
4. Parameters saved to data/adaptive_params.json
5. New parameters used in subsequent trades
6. Different symbols get different risk values
7. System runs 24+ hours without crashes
8. Parameters persist across bot restart

❌ **System needs investigation if**:
1. No optimization logs appear
2. Parameters always stay at defaults
3. Errors in optimizer or scheduler code
4. Trading doesn't respect new parameters
5. All symbols get same risk regardless of performance

---

## Performance Expectations

### CPU Usage
- Optimization cycle: 2-5 seconds per 20 symbols
- Normal impact: < 1% additional CPU during optimization
- Trading loop: No noticeable slowdown

### Memory Usage
- Adaptive modules: ~10 MB additional memory
- Parameter file: < 1 KB (minimal)
- No memory leaks expected

### Latency
- Trading decisions: No additional latency
- Parameter lookup: < 1 ms (in-memory cache)
- Optimization: Runs async, doesn't block trades

---

## Next Steps After Validation

1. **Monitor 24 Hours**: Let system optimize across full daily cycle
2. **Review Parameter Evolution**: Check how parameters adapt to market
3. **Analyze Trading Results**: Correlate optimization with performance
4. **Fine-tune Bounds**: Adjust safety limits if needed (optional)
5. **Deploy to Production**: System is production-ready

---

**Ready to Validate?**

```bash
python validate_adaptive_system.py
# Then
python run_bot.py
# Then
# Monitor logs for 2+ hours to see full optimization cycle
```

**Expected timeline**:
- 0 min: Bot starts
- 5 min: Trading begins with adaptive parameters
- 60 min: First optimization cycle runs
- 120 min: Second optimization cycle (can see parameter evolution)
- 24h+: Full system validation complete

**Questions?** Check the detailed documentation in:
- `ADAPTIVE_OPTIMIZER_GUIDE.md` - How it works
- `ADAPTIVE_INTEGRATION_COMPLETE.md` - Integration details  
- `ADAPTIVE_OPTIMIZATION_FINAL.md` - Complete reference
