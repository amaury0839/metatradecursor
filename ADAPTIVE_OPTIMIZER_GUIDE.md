# Adaptive Risk Optimizer - Hourly Parameter Tuning

## Overview
Sistema de optimización automática que **cada hora** ajusta los parámetros de riesgo por ticker basado en:
- ✅ Backtest de performance (últimas 60 minutos)
- ✅ Análisis con IA (Gemini)
- ✅ Ajustes inteligentes por símbolo

## Cómo Funciona

### 1. Ciclo Horario Automático
```
TOP OF HOUR → Análisis performance último 1h → IA recomienda ajustes → Aplica parámetros → Guarda
```

### 2. Métricas Analizadas por Ticker
- **Win Rate %**: % de trades ganadores en la última hora
- **Profit Factor**: Ganancias totales / Pérdidas totales
- **Avg Win/Loss**: Ganancia/pérdida promedio
- **Total PnL**: Resultado neto de la hora

### 3. Reglas de Ajuste Automático por IA

| Condición | Acción |
|-----------|--------|
| Win Rate < 40% | ⬇️ REDUCIR riesgo y posiciones (conservador) |
| Win Rate > 55% | ⬆️ AUMENTAR riesgo y posiciones (agresivo) |
| Profit Factor < 1.0 | ⬇️ Reducir volumen 10% (con pérdidas) |
| Profit Factor > 2.0 | ⬆️ Aumentar volumen 10% (máx 2% risk) |
| Sin trades | ➡️ Mantener parámetros |

### 4. Parámetros Ajustables por Ticker

```python
{
    "symbol": "EURUSD",
    "max_risk_pct": 1.5,              # % máximo de balance a riesgo
    "max_positions_per_ticker": 2,    # Posiciones máximas del símbolo
    "min_win_rate_pct": 45.0,         # Win rate mínimo requerido
    "max_daily_loss_pct": 10.0,       # Máximo loss diario
    "last_updated": "2026-01-28T02:00:00",
    "win_rate": 52.3,                 # Performance actual
    "profit_factor": 1.45              # PF actual
}
```

## Archivos Creados

### 1. `app/trading/adaptive_optimizer.py`
- **Clase**: `AdaptiveRiskOptimizer`
- **Métodos**:
  - `analyze_ticker_performance(symbol)` - Analiza últimas 60 min
  - `optimize_with_ai(symbol, performance)` - Usa Gemini para recomendar
  - `apply_optimization(symbol, recommendation)` - Aplica cambios
  - `hourly_optimization_cycle()` - Ejecuta ciclo completo

- **Almacenamiento**: `data/adaptive_params.json`

### 2. `app/trading/optimization_scheduler.py`
- **Clase**: `OptimizationScheduler`
- **Función**: Ejecuta optimización automáticamente cada hora
- **Thread**: Independiente del trading loop

### 3. `app/trading/parameter_injector.py`
- **Clase**: `ParameterInjector`
- **Métodos**:
  - `get_max_risk_pct_for_symbol(symbol)` - Riesgo adaptativo
  - `get_max_positions_for_symbol(symbol)` - Posiciones adaptativas
  - `should_trade_symbol(symbol)` - Permite/bloquea trading

## Integración en Trading

### Cómo acceder a parámetros adaptativos:

```python
from app.trading.parameter_injector import get_parameter_injector

injector = get_parameter_injector()

# Durante el trading loop
symbol = "EURUSD"
risk_pct = injector.get_max_risk_pct_for_symbol(symbol)
max_pos = injector.get_max_positions_for_symbol(symbol)
can_trade, reason = injector.should_trade_symbol(symbol)
```

## Flujo de Datos

```
Trading Cycle (every 30s)
    ↓
    → Ejecuta trades con parámetros adaptativos
    → Guarda resultados en DB
    ↓
Optimization Scheduler (every 60 min, TOP OF HOUR)
    ↓
    → get_adaptive_optimizer()
    → analyze_ticker_performance() [lee últimas 60 min de trades]
    → optimize_with_ai() [pide recomendación a Gemini]
    → apply_optimization() [aplica cambios]
    → save_params() [persiste adaptive_params.json]
    ↓
Próximo ciclo de trading usa parámetros nuevos
```

## Monitoreo

### Logs esperados:

```
🔄 HOURLY ADAPTIVE OPTIMIZATION CYCLE STARTED
✅ AI Optimization for EURUSD: increase - Win Rate 58% > 55% threshold
🔧 Updated EURUSD: Risk 1.5% → 1.8%, Positions 2 → 3
✅ OPTIMIZATION CYCLE COMPLETE: 16 tickers optimized
   EURUSD: WR=58.0% PF=1.45x → increase
   GBPUSD: WR=42.0% PF=0.95x → decrease
   BTCUSD: WR=50.0% PF=1.20x → maintain
```

## Limitaciones de Seguridad

- Max Risk: Capped a 0.5% - 3.0% (nunca > 3%)
- Max Positions: Capped a 1 - 5 (nunca > 5)
- Min Win Rate: Capped a 30% - 70%
- Cambios máximos: ±20% por ajuste
- Histórico mínimo: Requiere al menos 1 trade en última hora

## Configuración Manual (opcional)

Si necesitas override de parámetros, edita `data/adaptive_params.json`:

```json
{
    "EURUSD": {
        "max_risk_pct": 2.0,
        "max_positions_per_ticker": 3,
        "min_win_rate_pct": 50.0,
        "last_updated": "2026-01-28T01:00:00"
    }
}
```

## Próximos Pasos Automáticos

1. ✅ Créate archivos de optimización
2. ✅ Integrado en run_bot.py
3. ⏳ Espera a próxima hora para primer ciclo
4. 📊 Monitorea logs para ajustes aplicados
5. 🔄 Parámetros se actualizan cada hora automáticamente

## Troubleshooting

**Problema**: "No optimization results"
**Solución**: Requiere trades en última hora. Espera más ciclos de trading.

**Problema**: Parámetros no cambian
**Solución**: Win rate muy cercano a threshold. Necesita divergencia > 10%.

**Problema**: Errors en AI
**Solución**: Verifica conexión a Gemini API. Check logs para detalles.
