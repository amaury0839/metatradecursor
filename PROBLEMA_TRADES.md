# PROBLEMA IDENTIFICADO: TRADES NO SE REGISTRAN

## Estado Actual

**Problem**: Los 84 pares se están analizando, pero:
1. Las órdenes se RECHAZAN por mercados CERRADOS (CLOSED)
2. Las órdenes que SÍ se ejecutan NO se registran en la base de datos

---

## Root Causes Identificadas

### Causa 1: Mercados Cerrados (ICMarkets Demo)

En los logs vemos este patrón:
```
"Cannot trade AUDNZD: AUDNZD: CLOSED" 
"Cannot trade AUDSGD: AUDSGD: CLOSED"
"Cannot trade CADCHF: CADCHF: CLOSED"
```

**Razón**: Es sábado/domingo (2026-02-01 es domingo)

ICMarkets cierra:
- Viernes 22:00 GMT
- Reabre domingo 22:00 GMT (en 8 horas aproximadamente)

**Solución**: Esperar a que abran los mercados (domingo 22:00 GMT / lunes)

---

### Causa 2: Pares No Disponibles en Demo

Varios pares están marcados como "CLOSED" permanentemente:
```
AUDNZD, AUDSGD, CADCHF - No disponibles en tu cuenta demo
```

**Solución**: Remover estos pares del .env

---

### Causa 3: Volumen Mínimo No Cumplido

Algunos pares calculan volumen MENOR que el mínimo del broker:

```
CADJPY: calculated_volume: 0.007811 < broker_min: 0.010000 → SKIP
CHFJPY: calculated_volume: 0.005443 < broker_min: 0.010000 → SKIP
```

**Solución**: Aumentar capital o reducir número de pares

---

### Causa 4: Database Logging Issue (CRÍTICO)

El `save_trade()` se llama con estructura incorrecta:

```python
# LO QUE ENVIA (INCORRECTO):
db.save_trade({
    "action": decision.action,      ← Campo incorrecto
    "sl_price": sl_price,           ← Campo incorrecto
    "tp_price": tp_price,           ← Campo incorrecto
})

# LO QUE ESPERA save_trade() (CORRECTO):
{
    "type": "BUY/SELL",        ← Campo correcto
    "stop_loss": price,        ← Campo correcto
    "take_profit": price,      ← Campo correcto
    "open_timestamp": datetime,  ← FALTA
}
```

**Impacto**: Trades se rechazan silenciosamente en el INSERT, por eso retorna 0 en get_trades()

---

## Solución: Fix Database Logging

Necesito corregir cómo se guardan los trades. El problema está en `trading_loop.py` línea 380:
