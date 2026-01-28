# 📋 QUICK REFERENCE: What to Expect in Logs

## ✅ SUCCESS LOGS (Good signs)

### Position Limits Enforced
```
INFO: Cannot open new trade on EURCAD: Currency already has open position. Skipping EURCAD
```
✓ Currency conflict filter working

```
INFO: Max open trades (3) already reached. Currently: 3
```
✓ Max position limit enforced

### HOLD Signal Respected
```
INFO: Technical signal is HOLD → forcing HOLD (signal masters)
```
✓ HOLD overriding other signals

```
INFO: Technical signal BUY but confidence too low (0.55 < 0.7), forcing HOLD
```
✓ Confidence threshold enforced (min 0.70)

### Real Confidence Calculation
```
INFO: Confidence breakdown: tech=0.75, ai=0.50, sentiment=0.60 → weighted=0.63
```
✓ Weighted confidence is being calculated (not hardcoded 0.60)

### Risk Sizing
```
INFO: Risk $1.70 (0.5% of $340) for EURUSD BUY
```
✓ Per-trade risk limited to 0.5%

```
INFO: Daily loss cap: $6.80 (2% of balance)
```
✓ Daily loss limit is 2%

---

## ⚠️ WARNING LOGS (Watch for these)

```
WARNING: Technical analysis failed for EURUSD
```
→ Check data provider connection

```
WARNING: AI layer unavailable/blocked; forcing HOLD
```
→ Gemini API unavailable, trading stopped (correct behavior)

```
WARNING: RSI oversold (15), signal forced to HOLD
```
✓ RSI filter working (overbought/oversold protection)

---

## ❌ ERROR LOGS (Should NOT see these)

### RED FLAG #1: Hardcoded Confidence
```
comment: 'AI Bot - Confidence: 0.60'
```
❌ **Confidence hardcoded - fix not applied!**  
→ Check `_build_technical_decision()` in decision_engine.py

### RED FLAG #2: HOLD Not Respected
```
INFO: Using AI decision: BUY (confidence=0.35)
```
❌ **BUY opened despite low confidence - threshold broken!**  
→ Check min_confidence_threshold >= 0.70 in config.py

### RED FLAG #3: Currency Conflict Ignored
```
INFO: Opened EURCAD while EURUSD already open
```
❌ **Currency conflict not detected - filter broken!**  
→ Verify `has_currency_conflict()` in risk.py

### RED FLAG #4: Max Positions Exceeded
```
INFO: Opened trade #25 (max is 3)
```
❌ **Position limit not enforced - check main.py line 306!**

---

## 📊 EXAMPLE: Good Trading Session (M5 Scalping)

```
[14:05:00] Starting trading loop...
[14:05:15] Analyzing EURUSD...
[14:05:15]   [ANALYSIS] Mode: SCALPING, RSI: 52.4, EMA_fast > EMA_slow (bullish)
[14:05:15]   Signal: BUY
[14:05:20]   Confidence breakdown: tech=0.75, ai=0.00, sentiment=0.00 → weighted=0.30
[14:05:20]   Technical signal BUY but confidence too low (0.30 < 0.7), forcing HOLD
[14:05:20]   ✓ HOLD (confidence=0.30)

[14:06:00] Analyzing EURUSD... (retry)
[14:06:00]   [ANALYSIS] Mode: SCALPING, RSI: 68.2, EMA_fast > EMA_slow (bullish)
[14:06:00]   Signal: BUY
[14:06:05]   Confidence breakdown: tech=0.75, ai=0.65, sentiment=0.60 → weighted=0.70
[14:06:05]   ✓ Using technical signal: BUY (weighted_conf=0.70)
[14:06:10]   Risk $1.70 (0.5% of $340)
[14:06:10]   Can open new trade? Max 3, currently 1 → YES
[14:06:10]   Currency conflict? No open EUR positions → NO
[14:06:10]   ✓ All checks passed, placing BUY order...

[14:06:15] BUY 0.05 lots EURUSD @ 1.0950, SL=1.0925, TP=1.0975
[14:06:20] Order succeeded, ticket=12345

[14:08:00] Analyzing USDJPY...
[14:08:05]   Signal: HOLD
[14:08:05]   ✓ Signal is HOLD → forcing HOLD (signal masters)

[14:20:00] EURUSD closed at +$2.50 profit (0.73%)
[14:20:10] Position closed, P&L logged
```

**Key indicators:**
- ✓ Confidence calculated (not 0.60)
- ✓ HOLD enforced
- ✓ Risk per trade: $1.70
- ✓ Positions tracked (1/3 max)
- ✓ No currency conflicts

---

## 🧪 TEST: Manual Verification

### 1. Check Risk Config
```bash
grep "risk_per_trade_pct\|max_positions\|max_trades_per" app/trading/risk.py
```
**Expected output:**
```
self.risk_per_trade_pct = 0.5           # ✓
self.max_positions = 3                  # ✓
self.max_trades_per_currency = 1        # ✓
```

### 2. Check Signal Logic
```bash
grep -A 3 "If technical says HOLD" app/trading/integrated_analysis.py
```
**Expected output:**
```
if tech_signal == "HOLD":
    logger.info(f"Signal is HOLD → forcing HOLD")
    return "HOLD", 0.05
```

### 3. Check Confidence Calculation
```bash
grep -A 5 "_calculate_weighted_confidence" app/ai/decision_engine.py
```
**Expected output:**
```python
confidence = (
    0.4 * technical_score +
    0.4 * ai_score +
    0.2 * sentiment_score
)
```

### 4. Check Currency Filter
```bash
grep -A 2 "has_currency_conflict" app/main.py
```
**Expected output:**
```
can_trade, trade_error = risk.can_open_new_trade(symbol)
if not can_trade:
```

---

## 🚨 IMMEDIATE ACTION IF YOU SEE

| Log Message | Action |
|-------------|--------|
| `Confidence: 0.60` (hardcoded) | STOP - reload code, restart bot |
| `Opening trade #4` | STOP - max positions broken |
| `Opened EURUSD+EURCAD together` | STOP - currency filter broken |
| `BUY trade opened despite HOLD signal` | STOP - signal logic broken |
| `Daily loss: $27+` | STOP - check risk caps |

---

## 🎯 NORMAL DAILY PATTERN (Expected)

```
START OF DAY:
- 0 open positions
- Ready to trade (EURUSD, USDJPY, GBPUSD)

DURING TRADING (M5 scalping, typical):
- 1-3 positions open (max 3)
- Each trade size: 0.05 lots (max)
- Risk per trade: $1.70 (0.5%)
- Hold time: 5-30 minutes

END OF DAY:
- All positions closed
- Daily P&L logged: -2% to +3% (healthy range)
- No positions held overnight

RED FLAG:
- 4+ positions at once → BUG
- 1 position in EURUSD + 1 in EURCAD → BUG
- Trade sizes > 0.05 lots → BUG
- Daily loss > $6.80 → BUG
- Positions held > 4 hours → ADJUST timeframe
```

---

## 📞 DEBUGGING: If Something's Wrong

### Step 1: Check Config
```bash
python -c "from app.core.config import get_config; c = get_config(); print(f'Risk: {c.trading.default_risk_per_trade}%, Max positions: {c.trading.default_max_positions}, Symbols: {c.trading.default_symbols}')"
```

### Step 2: Check Risk Manager
```bash
python -c "from app.trading.risk import get_risk_manager; r = get_risk_manager(); print(f'Max positions: {r.max_positions}, Risk per trade: {r.risk_per_trade_pct}%, Currency limit: {r.max_trades_per_currency}')"
```

### Step 3: Check Decision Engine
```bash
python -c "from app.ai.decision_engine import DecisionEngine; d = DecisionEngine(); conf = d._calculate_weighted_confidence(0.75, 0.50, 0.60); print(f'Confidence (0.75, 0.50, 0.60): {conf}')"
```

Expected: `Confidence: 0.63` (not `0.60`)

### Step 4: Watch Live Logs
```bash
tail -f logs/trading_bot.log | grep -E "Signal|Confidence|Max open|Currency conflict"
```

---

**Remember:** These changes are **CRITICAL** for account survival. Monitor logs closely for the first 24 hours.
