"""Ejemplo de Integración - AGGRESSIVE_SCALPING en el Bot

Muestra cómo integrar el preset AGGRESSIVE_SCALPING
con el sistema de trading existente.
"""

import logging
from typing import Dict, Optional

# Imports del sistema
from app.trading.aggressive_scalping_integration import (
    get_aggressive_scalping_engine,
    apply_aggressive_scalping_config,
    create_aggressive_scalping_trade_params
)
from app.trading.risk import get_trading_preset
from app.trading.mt5_client import get_mt5_client
from app.core.data import get_data_provider

logger = logging.getLogger(__name__)


class ScalpingTradeManager:
    """Manejador de trades en modo AGGRESSIVE_SCALPING
    
    Integra:
    - Scale-out parcial
    - Trailing stop dinámico
    - Hard closes agresivas
    """
    
    def __init__(self):
        """Inicializar manager"""
        self.preset = get_trading_preset("AGGRESSIVE_SCALPING")
        self.engine = get_aggressive_scalping_engine()
        self.mt5 = get_mt5_client()
        self.data = get_data_provider()
        
        logger.info("✅ AGGRESSIVE_SCALPING Trade Manager initialized")
        logger.info(f"   Mode: {self.preset['mode']}")
        logger.info(f"   Risk: {self.preset['risk_percent']}%")
        logger.info(f"   Max positions: {self.preset['max_concurrent_positions']}")
    
    def execute_trade(
        self,
        symbol: str,
        direction: str,
        confidence: float,
        atr: float
    ) -> Optional[Dict]:
        """Ejecutar trade con configuración AGGRESSIVE_SCALPING
        
        Args:
            symbol: Símbolo (e.g., "EURUSD")
            direction: "BUY" o "SELL"
            confidence: Confianza IA (0-1)
            atr: ATR actual
            
        Returns:
            Dict con info del trade o None si no se abre
        """
        logger.info(f"🚀 Executing {direction} {symbol} (conf={confidence:.2f}, ATR={atr:.5f})")
        
        # 1. Crear parámetros de trade
        trade_params = create_aggressive_scalping_trade_params(
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            atr=atr
        )
        
        logger.info(f"   Lote: {trade_params['lot']:.2f}")
        logger.info(f"   SL: {trade_params['sl_pips']:.5f}")
        logger.info(f"   TP: {trade_params['tp_pips']:.5f}")
        logger.info(f"   AI Mode: {trade_params['ai_mode']}")
        
        # 2. Abrir posición en MT5
        # Aquí irían las llamadas reales a MT5
        # Por ahora es pseudocódigo
        trade_result = {
            "symbol": symbol,
            "direction": direction,
            "lot": trade_params["lot"],
            "entry_price": self.data.get_current_price(symbol),
            "sl": trade_params["sl_pips"],
            "tp": trade_params["tp_pips"],
            "atr_entry": atr,
            "confidence": confidence,
            "preset": self.preset["mode"],
        }
        
        logger.info(f"✅ Trade opened: {trade_result}")
        return trade_result
    
    def monitor_position(
        self,
        position: Dict,
        current_price: float,
        current_atr: float
    ) -> Dict:
        """Monitorear una posición abierta
        
        Args:
            position: Info de posición
            current_price: Precio actual
            current_atr: ATR actual
            
        Returns:
            Dict con acciones a tomar
        """
        symbol = position["symbol"]
        entry_price = position["entry_price"]
        is_buy = position["direction"] == "BUY"
        
        actions = {
            "scale_out": None,
            "trailing_sl": None,
            "hard_close": None,
            "reason": None
        }
        
        # 1. Chequear scale-out (TP parcial)
        scale_out = self.engine.check_scale_out(
            symbol=symbol,
            current_price=current_price,
            entry_price=entry_price,
            entry_atr=position["atr_entry"],
            is_buy=is_buy,
            position_size=position["lot"]
        )
        
        if scale_out["scale_out_hit"]:
            actions["scale_out"] = scale_out
            logger.info(f"📊 {symbol}: {scale_out['description']}")
        
        # 2. Chequear trailing stop
        new_sl, is_active = self.engine.check_trailing_stop(
            symbol=symbol,
            current_price=current_price,
            current_atr=current_atr,
            entry_price=entry_price,
            is_buy=is_buy
        )
        
        if is_active:
            actions["trailing_sl"] = new_sl
            logger.debug(f"📈 {symbol}: Trailing SL = {new_sl:.5f}")
        
        # 3. Chequear hard close RSI
        rsi = self.data.get_rsi(symbol, 14)  # Pseudocódigo
        if rsi is not None:
            should_close, reason = self.engine.check_hard_close_rsi(
                symbol=symbol,
                rsi=rsi,
                is_buy=is_buy
            )
            
            if should_close:
                actions["hard_close"] = True
                actions["reason"] = reason
                logger.warning(f"🛑 {symbol}: {reason}")
        
        return actions
    
    def apply_actions(
        self,
        position: Dict,
        actions: Dict
    ) -> None:
        """Aplicar acciones del monitoreo
        
        Args:
            position: Info de posición
            actions: Acciones a aplicar
        """
        symbol = position["symbol"]
        
        # 1. Scale-out
        if actions["scale_out"]:
            so = actions["scale_out"]
            close_amount = so["close_amount"]
            tp_level = so["tp_level"]
            
            logger.info(f"💰 Closing {close_amount*100:.0f}% at TP{tp_level}")
            # self.mt5.close_partial(symbol, close_amount)
            
            # Si TP2, mover SL a breakeven
            if so["move_sl_to_be"]:
                logger.info(f"🛡️  Moving SL to breakeven")
                # self.mt5.move_sl_to_be(symbol, position["entry_price"])
        
        # 2. Trailing SL
        if actions["trailing_sl"]:
            new_sl = actions["trailing_sl"]
            logger.info(f"📊 Updating SL to trailing: {new_sl:.5f}")
            # self.mt5.update_sl(symbol, new_sl)
        
        # 3. Hard Close
        if actions["hard_close"]:
            reason = actions["reason"]
            logger.warning(f"🛑 Hard closing: {reason}")
            # self.mt5.close_position(symbol)
    
    def get_trading_status(self) -> Dict:
        """Obtener estado de trading actual
        
        Returns:
            Info sobre configuración y posiciones
        """
        return {
            "preset": self.preset["mode"],
            "risk_percent": self.preset["risk_percent"],
            "max_positions": self.preset["max_concurrent_positions"],
            "trading_params": self.engine.get_trading_params(),
            "exit_summary": self.engine.get_exit_summary(),
        }


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

def example_scalping_session():
    """Ejemplo de una sesión completa de scalping
    
    Muestra:
    - Apertura de trade
    - Monitoreo en vivo
    - Scale-outs
    - Trailing stop
    """
    
    logger.info("\n" + "="*70)
    logger.info("AGGRESSIVE_SCALPING - EJEMPLO DE SESIÓN")
    logger.info("="*70)
    
    manager = ScalpingTradeManager()
    
    # 1. ABRIR TRADE
    logger.info("\n1️⃣ ABRIENDO TRADE")
    logger.info("-" * 70)
    
    position = manager.execute_trade(
        symbol="EURUSD",
        direction="BUY",
        confidence=0.55,
        atr=0.0050
    )
    
    # Simular progresión de precio
    simulation_data = [
        {"price": 1.0850, "atr": 0.0050, "rsi": 45, "desc": "Entry"},
        {"price": 1.0865, "atr": 0.0049, "rsi": 55, "desc": "+15 pips (+0.3R)"},
        {"price": 1.0875, "atr": 0.0048, "rsi": 62, "desc": "+25 pips (+0.5R) ← TP1"},
        {"price": 1.0900, "atr": 0.0047, "rsi": 72, "desc": "+50 pips (+1.0R) ← TP2"},
        {"price": 1.0925, "atr": 0.0046, "rsi": 78, "desc": "+75 pips (+1.5R) ← Trailing"},
        {"price": 1.0935, "atr": 0.0045, "rsi": 82, "desc": "+85 pips (máximo)"},
        {"price": 1.0920, "atr": 0.0046, "rsi": 88, "desc": "+70 pips (pullback) ← Hard close?"},
    ]
    
    for i, data in enumerate(simulation_data, 1):
        logger.info(f"\n{i}️⃣  MONITOR {data['desc']}")
        logger.info("-" * 70)
        
        actions = manager.monitor_position(
            position=position,
            current_price=data["price"],
            current_atr=data["atr"]
        )
        
        if any([actions["scale_out"], actions["trailing_sl"], actions["hard_close"]]):
            manager.apply_actions(position, actions)
            
            if actions["hard_close"]:
                logger.info(f"\n❌ TRADE CERRADO: {actions['reason']}")
                break
    
    logger.info("\n" + "="*70)
    logger.info("FIN DE SESIÓN")
    logger.info("="*70)
    
    status = manager.get_trading_status()
    logger.info(f"\nEstado final:")
    logger.info(f"  Preset: {status['preset']}")
    logger.info(f"  Risk: {status['risk_percent']}%")
    logger.info(f"  Max pos: {status['max_positions']}")


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Correr ejemplo
    example_scalping_session()
