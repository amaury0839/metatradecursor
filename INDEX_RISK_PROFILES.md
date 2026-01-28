# 📖 INDEX: Risk Profiles Architecture Implementation

## Quick Navigation

### Core Implementation Files
| File | Lines | Purpose |
|------|-------|---------|
| [app/trading/risk_profiles.py](app/trading/risk_profiles.py) | 202 | Profile definitions + manager |
| [app/trading/profile_selector.py](app/trading/profile_selector.py) | 420 | Selection logic + hourly evaluation |
| [app/main.py](app/main.py#L65-L110) | ~45 | Hourly evaluation integration |
| [app/main.py](app/main.py#L867-L905) | ~40 | Trade decision integration |

### Validation & Testing
| File | Tests | Status |
|------|-------|--------|
| [validate_risk_profiles.py](validate_risk_profiles.py) | 6 unit tests | ✅ 6/6 PASSED |
| [validate_full_integration.py](validate_full_integration.py) | 5 integration tests | ✅ 5/5 PASSED |
| [demo_risk_profiles_in_action.py](demo_risk_profiles_in_action.py) | Full demo | ✅ WORKING |

### Documentation
| File | Topic |
|------|-------|
| [RISK_PROFILES_COMPLETE.md](RISK_PROFILES_COMPLETE.md) | Complete technical guide |
| [SESSION_COMPLETE_RISK_PROFILES.md](SESSION_COMPLETE_RISK_PROFILES.md) | Session summary |

---

## 🔍 Code Locations

### RiskProfile Dataclass
```
File: app/trading/risk_profiles.py (lines 14-31)
- name: str
- risk_per_trade: float
- max_positions: int
- atr_sl_mult: float
- min_confidence_score: float
- max_daily_loss: float
- max_drawdown: float
- position_timeout_hours: int
```

### RiskProfileManager Class
```
File: app/trading/risk_profiles.py (lines 36-210)
Key Methods:
- __init__()
- get_current_profile()
- set_profile(name, reason)
- can_change_profile()
- _is_within_daily_limit()
- get_risk_profile_manager() [Singleton]
```

### ProfileSelector Class
```
File: app/trading/profile_selector.py (lines 15-420)
Key Methods:
- __init__()
- get_recent_trades(symbol, hours_back)
- calculate_metrics(trades)
- select_profile(metrics)
- _check_conditions(metrics, conditions, logic)
- evaluate_and_update(hours_back)
- get_profile_selector() [Singleton]

SELECTION_RULES Dictionary:
- CONSERVATIVE: {"conditions": [3 conditions], "logic": "ANY"}
- AGGRESSIVE: {"conditions": [3 conditions], "logic": "ALL"}
- BALANCED: {"conditions": [], "logic": "DEFAULT"}
```

### Main.py Integration Points

#### Hourly Evaluation (lines 65-104)
```python
def evaluate_risk_profile_hourly():
    """Evaluate and update profile once per hour"""
    global _last_profile_evaluation
    
    now = datetime.now()
    if _last_profile_evaluation is not None:
        if (now - _last_profile_evaluation) < timedelta(hours=1):
            return None  # Not yet time
    
    selector = get_profile_selector()
    result = selector.evaluate_and_update(hours_back=12)
    _last_profile_evaluation = now
    return result
```

#### Loop Integration (line 110)
```python
def main_trading_loop():
    try:
        # 🆕 RISK PROFILE HOURLY EVALUATION
        evaluate_risk_profile_hourly()
        # ... rest of trading loop
```

#### Trade Decision Integration (lines 867-890)
```python
# 🆕 RISK PROFILE INTEGRATION
try:
    from app.trading.risk_profiles import get_risk_profile_manager
    profile_mgr = get_risk_profile_manager()
    current_profile = profile_mgr.get_current_profile()
    
    profile_risk_pct = current_profile.risk_per_trade
    effective_risk_pct = min(engine_risk_pct, profile_risk_pct)
    
    max_positions_from_profile = current_profile.max_positions
    
    logger.info(
        f"📊 RISK PROFILE: {current_profile.name} - "
        f"risk={profile_risk_pct:.2f}%, max_pos={max_positions_from_profile}"
    )
except Exception as e:
    logger.debug(f"Profile not available: {e}")
    effective_risk_pct = engine_risk_pct
```

#### Sizing with Profile Risk (line 905)
```python
adaptive_risk_pct = max(
    effective_risk_pct,
    param_injector.get_max_risk_pct_for_symbol(symbol)
)
```

---

## 📊 Profile Parameters

### CONSERVATIVE
- Risk per trade: **0.25%**
- Max positions: **3**
- Stop loss multiplier: **1.8x** ATR
- Min confidence score: **0.70**
- Max daily loss: **5%**
- Max drawdown: **3%**
- Position timeout: **24** hours

**Selection Rule:**
```python
if win_rate < 0.40 or drawdown > 2.0 or profit_factor < 1.1:
    return "CONSERVATIVE"
```

### BALANCED
- Risk per trade: **0.50%**
- Max positions: **5**
- Stop loss multiplier: **1.5x** ATR
- Min confidence score: **0.60**
- Max daily loss: **8%**
- Max drawdown: **5%**
- Position timeout: **18** hours

**Selection Rule:**
```python
if not (any CONSERVATIVE conditions or all AGGRESSIVE conditions):
    return "BALANCED"  # Default
```

### AGGRESSIVE
- Risk per trade: **0.75%**
- Max positions: **7**
- Stop loss multiplier: **1.3x** ATR
- Min confidence score: **0.50**
- Max daily loss: **12%**
- Max drawdown: **8%**
- Position timeout: **12** hours

**Selection Rule:**
```python
if win_rate > 0.55 and profit_factor > 1.4 and drawdown < 1.0:
    return "AGGRESSIVE"
```

---

## 🔄 Stability Rules

### Time Between Changes
```python
MIN_HOURS_BETWEEN_PROFILE_CHANGES = 3  # hours
```
Prevents oscillating between profiles in volatile markets.

### Daily Change Limit
```python
MAX_PROFILE_JUMPS_PER_DAY = 2  # per day
```
Prevents over-reaction and "analysis paralysis".

### Implementation
```
File: app/trading/risk_profiles.py (lines 96-130)
Method: _is_within_daily_limit()
Method: can_change_profile()
```

---

## 📈 Metrics Calculation

### Win Rate
```python
win_rate = winning_trades / total_trades
Range: 0.0 to 1.0
```

### Profit Factor
```python
profit_factor = gross_profit / gross_loss
Range: 0.0+ (1.0 = breakeven)
```

### Max Drawdown (in R)
```python
max_drawdown = peak_equity - lowest_trough_from_peak
Measured in: Risk units (R)
Range: 0.0+ (0 = no drawdown)
```

### Expectancy
```python
expectancy = average_R_per_trade
Formula: sum_of_all_R / trade_count
Range: -inf to +inf (0 = breakeven)
```

**Implementation:**
```
File: app/trading/profile_selector.py
Method: calculate_metrics() (lines 112-185)
```

---

## 🎯 Selection Logic

### Decision Tree
```
START
│
├─ Check CONSERVATIVE conditions (ANY logic):
│  ├─ win_rate < 40%        → TRUE: Return CONSERVATIVE
│  ├─ drawdown > 2R         → TRUE: Return CONSERVATIVE
│  └─ profit_factor < 1.1   → TRUE: Return CONSERVATIVE
│
├─ Check AGGRESSIVE conditions (ALL logic):
│  ├─ win_rate > 55%        AND
│  ├─ profit_factor > 1.4   AND
│  └─ drawdown < 1R         → ALL TRUE: Return AGGRESSIVE
│
└─ Default → Return BALANCED
```

**Implementation:**
```
File: app/trading/profile_selector.py
Method: select_profile() (lines 308-364)
Helper: _check_conditions() (lines 366-405)
```

---

## 🧪 Validation Tests

### Unit Tests (6 tests)
1. **test_profiles_defined** - Verify all 3 profiles exist
2. **test_risk_hierarchy** - Verify correct parameter ordering
3. **test_stability_rules** - Verify 3h cooldown and daily limits
4. **test_metrics_calculation** - Verify metric calculations
5. **test_profile_selection_logic** - Verify selection rules work
6. **test_no_trades_handling** - Verify defaults to BALANCED

**Location:** validate_risk_profiles.py (lines 1-252)

### Integration Tests (5 tests)
1. **test_imports** - All modules load correctly
2. **test_profile_manager** - Manager initialization and access
3. **test_profile_selector** - Selection logic works end-to-end
4. **test_main_integration** - Hourly evaluation works
5. **test_parameter_application** - Asymmetric defense works

**Location:** validate_full_integration.py (lines 1-318)

---

## 🚀 Running Tests

### Unit Tests
```bash
cd c:\Users\Shadow\Downloads\Metatrade
python validate_risk_profiles.py
# Expected: 6/6 PASSED ✅
```

### Integration Tests
```bash
cd c:\Users\Shadow\Downloads\Metatrade
python validate_full_integration.py
# Expected: 5/5 PASSED ✅
```

### Live Demo
```bash
cd c:\Users\Shadow\Downloads\Metatrade
python demo_risk_profiles_in_action.py
# Shows complete architecture in action
```

---

## 🔐 Security & Stability

### Fail-Safe Defaults
```python
if error_in_profile_evaluation:
    use_current_profile()  # Don't change on error
    log_warning()
    continue_trading()
```

### Singleton Pattern
```python
_risk_profile_manager: Optional[RiskProfileManager] = None

def get_risk_profile_manager() -> RiskProfileManager:
    global _risk_profile_manager
    if _risk_profile_manager is None:
        _risk_profile_manager = RiskProfileManager()
    return _risk_profile_manager
```
Ensures single instance across entire bot.

### Throttling
```python
_last_profile_evaluation = None

def evaluate_risk_profile_hourly():
    global _last_profile_evaluation
    if _last_profile_evaluation and (now - _last_profile_evaluation) < 1 hour:
        return None  # Skip evaluation
```
Prevents excessive database queries.

---

## 📊 Status Dashboard (If Implemented)

Expected fields to display:
```
Current Profile:          BALANCED
Risk per Trade:           0.50%
Max Positions:            5
Stop Loss Multiplier:     1.5x ATR

Recent Metrics (last 12h):
  Win Rate:              52.5%
  Profit Factor:         1.38
  Max Drawdown:          1.2R
  Expectancy:            0.25R
  Trades:                20

Stability Status:
  Time since last change: 2h 15m
  Changes today:          1/2
  Can change in:          45 minutes

Selection Reason:         Situación intermedia
Last Changed:             2026-01-28 12:00:00 UTC
Change Reason:            Métricas intermedias
```

---

## 🎓 Learning Resources

### Understanding Risk Profiles
- See: [RISK_PROFILES_COMPLETE.md](RISK_PROFILES_COMPLETE.md) - Full guide
- Demo: [demo_risk_profiles_in_action.py](demo_risk_profiles_in_action.py) - Live example

### Understanding Selection Rules
- See: SELECTION_RULES in [profile_selector.py](app/trading/profile_selector.py)
- Compare: selection logic in select_profile() method

### Understanding Stability
- See: Stability rules in [risk_profiles.py](app/trading/risk_profiles.py)
- Test: test_stability_rules in [validate_risk_profiles.py](validate_risk_profiles.py)

---

## 🔗 Related Components

### Three-Tier Decision System
1. **Engine Selection** → Choose trading style (SCALPING/SWING/CRYPTO)
2. **AI Gate** → Decide when to call AI (gray-zone detection)
3. **Risk Profiles** → Adapt to market conditions (hourly evaluation)

All three layers work together to create intelligent, adaptive, defensive trading.

---

## 📝 Quick Commands

```bash
# Check if profiles are loaded correctly
python -c "from app.trading.risk_profiles import get_risk_profile_manager; print(get_risk_profile_manager().get_current_profile())"

# Run all tests
python validate_risk_profiles.py && python validate_full_integration.py

# See demo
python demo_risk_profiles_in_action.py

# Check integration in main
grep -n "risk_profile" app/main.py

# Find profile references
find . -name "*.py" -type f -exec grep -l "get_risk_profile_manager\|ProfileSelector" {} \;
```

---

## ✅ Checklist for Production

- ✅ Core implementation complete
- ✅ All unit tests pass (6/6)
- ✅ All integration tests pass (5/5)
- ✅ Integrated into main trading loop
- ✅ Documentation complete
- ✅ Demo script working
- ✅ Error handling implemented
- ✅ Logging implemented
- ✅ Stability rules enforced
- ✅ Ready for live trading

---

**This index provides quick access to all Risk Profiles implementation details.**

For complete technical documentation, see: [RISK_PROFILES_COMPLETE.md](RISK_PROFILES_COMPLETE.md)

For session summary, see: [SESSION_COMPLETE_RISK_PROFILES.md](SESSION_COMPLETE_RISK_PROFILES.md)
