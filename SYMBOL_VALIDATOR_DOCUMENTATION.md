# 🔍 Symbol Validator - Detección Dinámica de Símbolos

## ¿Cómo Funciona?

El bot ahora valida **automáticamente** todos los símbolos contra MT5 al iniciarse.

### Flujo de Validación

```
1. Bot Inicia
   └─→ Lee config.trading.default_symbols (88 candidatos)
   
2. Crea SymbolValidator
   └─→ Intenta conectar a MT5
   
3. Para CADA símbolo candidato:
   ├─→ ¿Existe en MT5?
   ├─→ ¿trade_mode != DISABLED?
   └─→ SÍ = Válido ✅ | NO = Inválido ❌
   
4. Resultado Final
   └─→ 54 válidos / 7 inválidos
       Config actualizada con 54 símbolos válidos
   
5. Bot comienza a operar
   └─→ Solamente los 54 símbolos validados
```

---

## 📊 Código Implementado

### File: `app/trading/symbol_validator.py`

```python
class SymbolValidator:
    def validate_symbols(self, candidates: List[str]) -> List[str]:
        """
        Valida cada símbolo contra MT5
        Retorna lista de símbolos válidos
        """
        for symbol in candidates:
            info = mt5.symbol_info(symbol)
            if info and info.trade_mode != DISABLED:
                self.valid_symbols.append(symbol)
                logger.info(f"✅ {symbol}")
            else:
                self.invalid_symbols.append(symbol)
                logger.debug(f"❌ {symbol}")
```

### File: `run_bot.py` (init code)

```python
# En main():
config = get_config()

# Validar símbolos
validator = get_symbol_validator()
valid_symbols = validator.validate_symbols(
    candidates=config.trading.default_symbols,
    skip_list=config.trading.symbols_to_skip
)

# Actualizar config con símbolos validados
config.trading.default_symbols = valid_symbols
```

---

## 🎯 Logs de Validación

Cuando el bot inicia, ves esto:

```json
{
  "event": "Config loaded: 61 symbols",
  "level": "info"
}
{
  "event": "🔍 Validating 61 candidate symbols...",
  "level": "info"
}
{
  "event": "✅ EURUSD",
  "level": "info"
}
{
  "event": "✅ US500",
  "level": "info"
}
{
  "event": "✅ BTCUSD",
  "level": "info"
}
...
{
  "event": "✅ Validation complete: 54 valid symbols",
  "level": "info"
}
{
  "event": "❌ 7 invalid symbols (will be skipped)",
  "level": "warning"
}
{
  "event": "📊 Using 54 validated symbols",
  "level": "info"
}
```

---

## 🔧 Ventajas del Sistema

### 1. **Automático**
- No necesitas verificar qué símbolos están disponibles
- El bot lo hace automáticamente

### 2. **Robusto**
- Si un símbolo está cerrado → Se salta automáticamente
- Si MT5 no responde → Usa símbolos previos en caché
- No hay errores de trading en símbolos inválidos

### 3. **Adaptable**
- Cambias de broker? Automáticamente detecta nuevos símbolos
- Aggrega símbolos a tu cuenta? El bot los detecta en la siguiente ejecución
- Mercados regionales? Se ajusta automáticamente

### 4. **Auditable**
- Logs completos de qué fue validado
- Fácil de debuggear si hay problemas

---

## 🎨 Configuración Personalizada

### Excluir símbolos específicos:

```python
# app/core/config.py
symbols_to_skip = [
    "NAS100",    # No disponible en demo
    "GOLD",      # Requiere suscripción
    "ES",        # Futuros no en demo
]
```

### O vía variables de entorno:

```bash
# .env file
SYMBOLS_TO_SKIP=NAS100,GER40,GOLD,ES,CL
```

---

## 📈 Escalabilidad Futura

Cuando tengas acceso a más símbolos:

```python
# Agregar nuevos candidatos a config
default_symbols = [
    # Existentes
    "EURUSD", "BTCUSD", ...
    # NUEVOS - Se validarán automáticamente
    "AAPL", "MSFT", "AMZN",  # Stocks
    "GOLD", "SILVER",          # Commodities
    "ES", "NQ", "YM",          # Futures
]

# El bot automáticamente:
# 1. Detectará cuáles están disponibles
# 2. Filtrará los que no están
# 3. Operará solo los válidos
```

---

## 🚨 Error Handling

Si algo falla:

```python
except Exception as e:
    logger.warning(f"⚠️  {symbol} (error: {e})")
    invalid_symbols.append(symbol)  # Tratado como inválido
    continue  # Continúa con el siguiente
```

---

## 📊 Estadísticas de Validación

El validador también guarda:

```python
symbol_details = {
    "EURUSD": {
        "bid": 1.0845,
        "ask": 1.0846,
        "digits": 5,
        "volume_min": 0.01,
        "volume_max": 100,
    },
    ...
}
```

Útil para:
- Cálculo de spreads
- Validación de tamaño de posición
- Debugging de símbolos problemáticos

---

## ⚙️ Integración con Otros Módulos

### Risk Manager
```python
# Usa símbolos validados para cálculo de exposición
risk = portfolio.calculate_exposure(
    valid_symbols  # Solo los validados
)
```

### Trading Loop
```python
# Solo analiza/tradea símbolos válidos
for symbol in config.trading.default_symbols:  # Ya filtrado
    signal, indicators = strategy.get_signal(symbol)
    ...
```

### Strategy Engine
```python
# Skips inválidos automáticamente
if symbol not in validator.get_valid_symbols():
    continue  # Salta símbolos inválidos
```

---

## 🎯 Conclusión

El sistema de validación de símbolos hace que el bot sea:

1. ✅ **Más robusto** - Maneja símbolos faltantes/cerrados
2. ✅ **Más flexible** - Se adapta a cambios de broker/región
3. ✅ **Más escalable** - Fácil agregar 100 más símbolos
4. ✅ **Más confiable** - Menos errores de MT5
5. ✅ **Más mantenible** - Logs claros de qué pasó

**Resultado**: Un bot que "just works" con cualquier set de símbolos.
