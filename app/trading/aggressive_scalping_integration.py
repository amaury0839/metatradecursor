"""Integration with Advanced Exit Management and Aggressive Scalping Preset

Integra:
- Scale-out parcial con múltiples TP
- Trailing stop dinámico
- Hard closes agresivas (RSI 85/15)
- Modo BIAS_ONLY para IA
"""

import logging
from typing import Dict, Optional, Tuple
from app.trading.exit_management_advanced import (
    AdvancedExitManager,
    ScaleOutProfile,
    get_aggressive_scalping_preset,
)
from app.trading.risk import get_trading_preset, get_risk_manager

logger = logging.getLogger(__name__)


class AggressiveScalpingEngine:
    """Engine para scalping agresivo con todas las características
    
    Características:
    - Risk: 0.75% por trade
    - Max 6 posiciones simultáneas
    - Scale-out parcial: 40% @ +0.5R, 30% @ +1R (SL→BE), rest @ trailing
    - Trailing stop dinámico: ATR * 1.0
    - Hard closes agresivas: RSI > 85 / < 15
    - IA en modo BIAS_ONLY (no bloquea)
    """
    
    def __init__(self):
        """Inicializar engine de aggressive scalping"""
        self.preset = get_trading_preset("AGGRESSIVE_SCALPING")
        self.risk_manager = get_risk_manager()
        
        # Inicializar exit manager con escala-out agresivo
        self.exit_manager = AdvancedExitManager(
            scale_out_profile=ScaleOutProfile.SCALPING,
            trailing_enabled=True,
            hard_close_enabled=True
        )
        
        logger.info("🚀 AGGRESSIVE_SCALPING Engine initialized")
        logger.info(f"   Mode: {self.preset['mode']}")
        logger.info(f"   Risk: {self.preset['risk_percent']}% per trade")
        logger.info(f"   Max positions: {self.preset['max_concurrent_positions']}")
        logger.info(f"   RSI hard closes: >{self.preset['rsi_hard_close_overbought']} / <{self.preset['rsi_hard_close_oversold']}")
        logger.info(f"   Trailing stop: ATR * {self.preset['trailing_atr_multiple']}")
        logger.info(f"   IA Mode: {self.preset['ai_mode']} (no bloquea)")
    
    def check_scale_out(
        self,
        symbol: str,
        current_price: float,
        entry_price: float,
        entry_atr: float,
        is_buy: bool,
        position_size: float,
    ) -> Dict:
        """Chequear si hay que cerrar parcialmente por TP
        
        Args:
            symbol: Símbolo
            current_price: Precio actual
            entry_price: Precio de entrada
            entry_atr: ATR en entrada
            is_buy: True si compra
            position_size: Tamaño de posición
            
        Returns:
            Dict con:
            - scale_out_hit: bool (¿hay scale-out?)
            - close_amount: float (% a cerrar)
            - tp_level: int
            - move_sl_to_be: bool
            - description: str
        """
        result = self.exit_manager.process_tp(
            current_price=current_price,
            entry_price=entry_price,
            atr=entry_atr,
            is_buy=is_buy,
            position_size=position_size
        )
        
        if result["tp_hit"]:
            logger.info(f"📊 {symbol}: {result['description']}")
        
        return result
    
    def check_trailing_stop(
        self,
        symbol: str,
        current_price: float,
        current_atr: float,
        entry_price: float,
        is_buy: bool
    ) -> Tuple[Optional[float], bool]:
        """Calcular trailing stop dinámico
        
        Args:
            symbol: Símbolo
            current_price: Precio actual
            current_atr: ATR actual
            entry_price: Precio de entrada
            is_buy: True si compra
            
        Returns:
            (new_sl, is_active)
        """
        new_sl, is_active = self.exit_manager.process_trailing(
            current_price=current_price,
            atr=current_atr,
            entry_price=entry_price,
            is_buy=is_buy
        )
        
        if is_active and new_sl:
            logger.debug(f"📈 {symbol}: Trailing SL = {new_sl:.5f}")
        
        return new_sl, is_active
    
    def check_hard_close_rsi(
        self,
        symbol: str,
        rsi: float,
        is_buy: bool
    ) -> Tuple[bool, str]:
        """Chequear hard close por RSI extremo
        
        Args:
            symbol: Símbolo
            rsi: Valor RSI actual
            is_buy: True si compra
            
        Returns:
            (should_close, reason)
        """
        should_close, reason = self.exit_manager.check_hard_close(rsi, is_buy)
        
        if should_close:
            logger.warning(f"🛑 {symbol}: {reason}")
        
        return should_close, reason
    
    def get_trading_params(self) -> Dict:
        """Obtener parámetros de trading para esta sesión
        
        Returns:
            Dict con todos los parámetros configurados
        """
        return {
            "preset": self.preset["mode"],
            "risk_percent": self.preset["risk_percent"],
            "max_positions": self.preset["max_concurrent_positions"],
            "timeframe": self.preset["timeframe"],
            "trailing_enabled": self.preset["trailing_stop_enabled"],
            "trailing_atr": self.preset["trailing_atr_multiple"],
            "trailing_activation_r": self.preset["trailing_min_profit_r"],
            "rsi_overbought": self.preset["rsi_hard_close_overbought"],
            "rsi_oversold": self.preset["rsi_hard_close_oversold"],
            "sl_atr_multiple": self.preset["sl_atr_multiple"],
            "tp_atr_multiple": self.preset["tp_atr_multiple"],
            "ai_mode": self.preset["ai_mode"],
            "ai_blocks_trade": self.preset["ai_blocks_trade"],
            "tp_levels": self.preset["tp_levels"],
        }
    
    def get_exit_summary(self) -> Dict:
        """Obtener resumen del estado de exits
        
        Returns:
            Info sobre posición actual
        """
        return self.exit_manager.get_summary()
    
    def reset_for_new_position(self):
        """Resetear para nueva posición"""
        self.exit_manager.reset()
        logger.debug("Exit manager reset for new position")


# Instancia global
_aggressive_scalping_engine: Optional[AggressiveScalpingEngine] = None


def get_aggressive_scalping_engine() -> AggressiveScalpingEngine:
    """Obtener instancia global del engine
    
    Returns:
        AggressiveScalpingEngine
    """
    global _aggressive_scalping_engine
    if _aggressive_scalping_engine is None:
        _aggressive_scalping_engine = AggressiveScalpingEngine()
    return _aggressive_scalping_engine


# ============================================================================
# INTEGRATION WITH DECISION ENGINE
# ============================================================================

def apply_aggressive_scalping_config(decision_engine) -> None:
    """Aplicar configuración AGGRESSIVE_SCALPING a un decision engine
    
    Args:
        decision_engine: Instancia de decision engine
    """
    preset = get_trading_preset("AGGRESSIVE_SCALPING")
    
    # Aplicar configuración
    decision_engine.confidence_threshold = preset["confidence_threshold"]
    decision_engine.hard_close_rsi_overbought = preset["rsi_hard_close_overbought"]
    decision_engine.hard_close_rsi_oversold = preset["rsi_hard_close_oversold"]
    
    # Modo IA: BIAS_ONLY (no bloquea)
    decision_engine.ai_blocks_trades = preset["ai_blocks_trade"]
    
    logger.info(f"✅ AGGRESSIVE_SCALPING applied to decision engine")
    logger.info(f"   AI Mode: {preset['ai_mode']} (blocks={preset['ai_blocks_trade']})")
    logger.info(f"   Confidence threshold: {preset['confidence_threshold']}")
    logger.info(f"   RSI Hard Closes: >{preset['rsi_hard_close_overbought']} / <{preset['rsi_hard_close_oversold']}")


def create_aggressive_scalping_trade_params(
    symbol: str,
    direction: str,
    confidence: float,
    atr: float
) -> Dict:
    """Crear parámetros de trade con configuración AGGRESSIVE_SCALPING
    
    Args:
        symbol: Símbolo a tradear
        direction: "BUY" o "SELL"
        confidence: Confianza de IA (0-1)
        atr: ATR actual
        
    Returns:
        Dict con parámetros de trade
    """
    preset = get_trading_preset("AGGRESSIVE_SCALPING")
    risk_manager = get_risk_manager()
    
    # Risk y lote
    risk_percent = preset["risk_percent"]
    sl_pips = atr * preset["sl_atr_multiple"]
    tp_pips = atr * preset["tp_atr_multiple"]
    
    # Calcular lote
    lot = risk_manager.calculate_lot_size(symbol, risk_percent, sl_pips)
    
    return {
        "symbol": symbol,
        "direction": direction,
        "lot": lot,
        "confidence": confidence,
        "sl_pips": sl_pips,
        "tp_pips": tp_pips,
        "atr": atr,
        "risk_percent": risk_percent,
        "preset": preset["mode"],
        "ai_mode": preset["ai_mode"],
        "scale_out_enabled": True,
        "trailing_stop_enabled": preset["trailing_stop_enabled"],
        "hard_close_rsi": (
            preset["rsi_hard_close_overbought"]
            if direction == "BUY"
            else preset["rsi_hard_close_oversold"]
        ),
    }
