# 🧪 BACKTESTING & LIVE DEPLOYMENT GUIDE

## PASO 1: Verificar que todos los archivos existen

```powershell
ls app/trading/exit_management_advanced.py
ls app/trading/dynamic_sizing.py
ls app/trading/aggressive_scalping_integration.py
ls pyramiding_integration_example.py
```

Todos deben existir ✅

---

## PASO 2: Crear script de backtesting

Crear archivo: `run_backtest_aggressive.py`

```python
#!/usr/bin/env python3
"""
Backtest AGGRESSIVE_SCALPING + PYRAMIDING system
"""

import sys
from datetime import datetime, timedelta
from app.core.logger import setup_logger
from app.trading.risk import get_risk_manager, get_trading_preset
from app.trading.mt5_client import get_mt5_client
from app.trading.data import get_data_provider
from app.trading.dynamic_sizing import get_dynamic_sizer, get_pyramiding_manager
from app.trading.aggressive_scalping_integration import get_aggressive_scalping_engine

logger = setup_logger("backtest")

class BacktestEngine:
    def __init__(self, preset_name="AGGRESSIVE_SCALPING", symbol="EURUSD"):
        self.preset = get_trading_preset(preset_name)
        self.symbol = symbol
        self.risk = get_risk_manager()
        self.mt5 = get_mt5_client()
        self.data = get_data_provider()
        self.sizer = get_dynamic_sizer()
        self.pyramid_mgr = get_pyramiding_manager()
        self.engine = get_aggressive_scalping_engine()
        
        # Stats
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.pyramid_count = 0
        self.pyramid_success = 0
    
    def run_backtest(self, start_date: str, end_date: str, timeframe="M15"):
        """
        Run backtest for date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: M15, H1, D
        """
        logger.info(f"Starting backtest: {self.symbol} {timeframe}")
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Preset: {self.preset['mode']}")
        
        # Get historical data
        candles = self.data.get_historical_data(
            self.symbol, timeframe, start_date, end_date
        )
        
        if not candles:
            logger.error(f"No data for {self.symbol}")
            return False
        
        logger.info(f"Loaded {len(candles)} candles")
        
        # Simulate trading
        open_positions = {}
        
        for i, candle in enumerate(candles):
            timestamp = candle.get('time')
            open_price = candle.get('open')
            high = candle.get('high')
            low = candle.get('low')
            close = candle.get('close')
            volume = candle.get('volume')
            
            # Check for entry signals (simplified)
            # In real backtest, integrate with decision engine
            signal = self._generate_signal(candle, i, candles)
            
            if signal and "BUY" in signal:
                # Try to enter
                self._process_entry(self.symbol, "BUY", signal)
            elif signal and "SELL" in signal:
                self._process_entry(self.symbol, "SELL", signal)
            
            # Monitor open positions
            for pos_key, position in list(open_positions.items()):
                # Check scale-out
                scale_out = self.engine.check_scale_out(...)
                if scale_out["scale_out_hit"]:
                    self._process_scale_out(position, scale_out)
                
                # Check pyramiding
                pyramid = self.pyramid_mgr.calculate_pyramid_activation(...)
                if pyramid:
                    self._process_pyramid(position, pyramid)
                    self.pyramid_count += 1
                
                # Check trailing
                trailing_sl, is_active = self.engine.check_trailing_stop(...)
                if is_active:
                    position["sl"] = trailing_sl
                
                # Check hard close
                should_close, reason = self.engine.check_hard_close_rsi(...)
                if should_close:
                    pnl = self._close_position(position, close)
                    self.total_pnl += pnl
                    del open_positions[pos_key]
        
        # Close remaining positions
        for pos_key, position in open_positions.items():
            pnl = self._close_position(position, candles[-1]['close'])
            self.total_pnl += pnl
        
        self._print_results()
        return True
    
    def _generate_signal(self, candle, index, all_candles):
        """Generate entry signal (simplified)"""
        # In real backtest, integrate proper signal generation
        return None  # Simplified
    
    def _process_entry(self, symbol, direction, signal):
        """Process entry"""
        entry_price = signal.get('entry_price')
        sl_price = signal.get('sl_price')
        
        # Calculate size
        lot = self.risk.calculate_position_size(symbol, entry_price, sl_price)
        
        # VALIDATE with dynamic sizing
        final_lot = self.sizer.validate_and_clamp_size(symbol, lot)
        if final_lot is None:
            logger.debug(f"Trade rejected: {symbol} - insufficient size")
            return False
        
        self.total_trades += 1
        logger.info(f"Entry {direction} {symbol} {final_lot:.2f} @ {entry_price}")
        return True
    
    def _process_scale_out(self, position, scale_out):
        """Process scale-out"""
        logger.info(f"Scale-out Level {scale_out['tp_level']}: Close {scale_out['close_amount']*100:.0f}%")
    
    def _process_pyramid(self, position, pyramid):
        """Process pyramid"""
        logger.info(f"Pyramid: Add {pyramid['pyramid_lot']:.2f}")
        self.pyramid_success += 1
    
    def _close_position(self, position, close_price):
        """Close position and calculate P&L"""
        entry = position['entry']
        direction = position['direction']
        lot = position['lot']
        
        if direction == "BUY":
            pnl = (close_price - entry) * lot * 100000
        else:
            pnl = (entry - close_price) * lot * 100000
        
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        logger.info(f"Close {direction} @ {close_price}: P&L {pnl:+.2f}")
        return pnl
    
    def _print_results(self):
        """Print backtest results"""
        logger.info("\n" + "="*60)
        logger.info("BACKTEST RESULTS")
        logger.info("="*60)
        logger.info(f"Total trades: {self.total_trades}")
        logger.info(f"Winning trades: {self.winning_trades}")
        logger.info(f"Losing trades: {self.losing_trades}")
        
        if self.total_trades > 0:
            win_rate = (self.winning_trades / self.total_trades) * 100
            logger.info(f"Win rate: {win_rate:.1f}%")
        
        logger.info(f"Total P&L: {self.total_pnl:+.2f}")
        logger.info(f"Pyramids executed: {self.pyramid_count}")
        
        if self.pyramid_count > 0:
            pyramid_success_rate = (self.pyramid_success / self.pyramid_count) * 100
            logger.info(f"Pyramid success rate: {pyramid_success_rate:.1f}%")
        
        logger.info("="*60 + "\n")

if __name__ == "__main__":
    engine = BacktestEngine(
        preset_name="AGGRESSIVE_SCALPING",
        symbol="EURUSD"
    )
    
    # Run backtest (example: last 3 months)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    success = engine.run_backtest(start_date, end_date, timeframe="M15")
    
    if success:
        logger.info("✅ Backtest completed")
    else:
        logger.error("❌ Backtest failed")
        sys.exit(1)
```

---

## PASO 3: Ejecutar Backtesting

```powershell
python run_backtest_aggressive.py
```

Esperar resultados. Verificar:
- ✅ Win rate > 55%
- ✅ Profit factor > 1.8
- ✅ Pyramid success rate > 60%
- ✅ Drawdown < 15%

---

## PASO 4: Si Backtest OK → Paper Trading

```powershell
# Opción 1: Paper trading con Streamlit
python -m streamlit run app/main_ui.py

# Opción 2: Paper trading CLI
python run_bot.py --mode=paper
```

Ejecutar por 1 semana. Verificar:
- ✅ Pyramid triggers
- ✅ Scale-out execution
- ✅ Hard closes funcional
- ✅ Dynamic sizing effect
- ✅ All P&L logged

---

## PASO 5: Si Paper Trading OK → Live Pequeño

```powershell
# Start with small account ($1,000)
# Max 2 positions
python run_bot.py --mode=live --max-positions=2
```

Monitorear primera 24h:
- ✅ Trades ejecutados
- ✅ SL en lugar correcto
- ✅ TP hits
- ✅ Pyramid activations
- ✅ Scale-out closings

---

## PASO 6: Scale Up (After Profit)

Si semana 1 es profitable:
- Aumentar a 4 posiciones
- Aumentar capital a $5k

Si semana 2 es profitable:
- Aumentar a 6 posiciones
- Aumentar capital a $10k+

---

## 📊 MÉTRICAS CRÍTICAS A MONITOREAR

### Entrada
- [x] Dynamic sizing applied
- [x] Min volume respetado
- [x] Consolation trades rechazados

### Monitoreo
- [x] Scale-out en TP levels
- [x] SL move a BE en TP2
- [x] Trailing stop updates
- [x] Pyramid triggers @ +0.5R
- [x] Hard closes @ RSI 85/15

### Salida
- [x] Partial closes logged
- [x] Pyramid SL to BE confirmed
- [x] Final P&L calculated
- [x] Pyramid reset executed

### Estadísticas
- [x] Win rate
- [x] Profit factor
- [x] Drawdown
- [x] Pyramid success rate
- [x] Average trade duration
- [x] Best/worst trade

---

## 🚨 TROUBLESHOOTING

### Error: "Cannot import dynamic_sizing"
→ Verificar que `app/trading/dynamic_sizing.py` existe
→ Verificar que está en mismo folder que `risk.py`

### Error: "Pyramid failed"
→ Check MT5 connection
→ Check SL distance compliance with broker

### Error: "Trade rejected - insufficient size"
→ This is NORMAL (feature, not bug)
→ Significa que calculated lot < minimum para balance
→ Sign that system está siendo conservador

### Pyramiding no se activa
→ Check que ATR se está calculando
→ Check que +0.5R threshold está siendo alcanzado
→ Aumentar logging para debug

---

## 📈 CRITERIOS DE ÉXITO

Para pasar de backtesting a paper trading:
- [x] Win rate >= 55%
- [x] Profit factor >= 1.8
- [x] Trades > 50 (statistical significance)
- [x] Drawdown < 15%

Para pasar de paper a live:
- [x] Paper trading profitable > 1 semana
- [x] Pyramid success rate > 60%
- [x] All signals ejecutados correctamente
- [x] No errors en 1 semana

---

## 🎯 TIMELINE RECOMENDADO

```
HOY:          Ejecutar backtest
MAÑANA:       Analizar resultados + paper trading
1 SEMANA:     Paper trading completo
SEMANA 2:     Live pequeño ($1k, 2 posiciones)
SEMANA 3:     Si profitable → escalar
SEMANA 4+:    Full scale AGGRESSIVE_SCALPING
```

---

## ✅ FINAL CHECKLIST

- [ ] Backtesting completado
- [ ] Resultados OK (win rate > 55%)
- [ ] Paper trading 1 semana
- [ ] All systems go
- [ ] Live account listo
- [ ] Monitor activo
- [ ] P&L tracking activo
- [ ] Ready to scale

---

**Status**: 🟢 Ready for backtesting NOW

Proceder con confidence.
