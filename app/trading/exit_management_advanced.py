"""Advanced Exit Management - Scale-out Parcial + Trailing Stop Agresivo

Sistema de exits profesional con:
- Scale-out parcial en múltiples TP
- Trailing stop dinámico basado en ATR
- Take profits escalonados
- Movimiento de SL a breakeven
- Hard closes agresivas (RSI 85/15)
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class ScaleOutProfile(Enum):
    """Perfiles de scale-out"""
    CONSERVATIVE = "conservative"      # 20% / 50% / rest
    STANDARD = "standard"              # 30% / 50% / rest
    AGGRESSIVE = "aggressive"          # 30% / 40% / rest (menor risk)
    SCALPING = "scalping"              # 40% / 30% / rest (máx. ganancias)


@dataclass
class TakeProfitLevel:
    """Define un nivel de take profit"""
    level: int                          # TP1, TP2, TP3
    price_multiple: float               # Múltiplo de R (0.5R = 0.5)
    close_percent: float                # % de posición a cerrar
    move_sl_to_be: bool                 # Mover SL a breakeven
    description: str                    # Descripción (TP1: +0.5R → 30%)


@dataclass
class TrailingStopConfig:
    """Configuración de trailing stop"""
    enabled: bool                       # Activado/desactivado
    atr_multiple: float                 # Múltiplo de ATR (1.0 = ATR base)
    min_profit_r: float                 # Profit mínimo en R para activar
    atr_lookback: int                   # Períodos para calcular ATR
    update_frequency: str               # "tick" o "candle"


@dataclass
class HardCloseConfig:
    """Configuración de cierres duros agresivos"""
    rsi_overbought: float              # RSI > X (85 agresivo)
    rsi_oversold: float                # RSI < X (15 agresivo)
    enabled: bool                       # Activado
    reason: str                         # Razón del cierre


class ScaleOutManager:
    """Gestor de scale-out parcial"""
    
    def __init__(self, profile: ScaleOutProfile = ScaleOutProfile.AGGRESSIVE):
        """Inicializar manager de scale-out
        
        Args:
            profile: Perfil de scale-out
        """
        self.profile = profile
        self.tp_levels = self._get_tp_levels(profile)
    
    def _get_tp_levels(self, profile: ScaleOutProfile) -> List[TakeProfitLevel]:
        """Obtener niveles de TP según perfil"""
        
        if profile == ScaleOutProfile.CONSERVATIVE:
            return [
                TakeProfitLevel(1, 0.5, 0.20, False, "TP1: +0.5R → 20%"),
                TakeProfitLevel(2, 1.0, 0.50, True, "TP2: +1.0R → 50% (SL→BE)"),
                TakeProfitLevel(3, 2.0, 1.00, False, "TP3: +2.0R → 100%"),
            ]
        
        elif profile == ScaleOutProfile.STANDARD:
            return [
                TakeProfitLevel(1, 0.5, 0.30, False, "TP1: +0.5R → 30%"),
                TakeProfitLevel(2, 1.0, 0.50, True, "TP2: +1.0R → 50% (SL→BE)"),
                TakeProfitLevel(3, 2.0, 1.00, False, "TP3: +2.0R → trailing"),
            ]
        
        elif profile == ScaleOutProfile.AGGRESSIVE:
            return [
                TakeProfitLevel(1, 0.5, 0.30, False, "TP1: +0.5R → 30%"),
                TakeProfitLevel(2, 1.0, 0.40, True, "TP2: +1.0R → 40% (SL→BE)"),
                TakeProfitLevel(3, 2.0, 1.00, False, "TP3: +2.0R → trailing"),
            ]
        
        elif profile == ScaleOutProfile.SCALPING:
            return [
                TakeProfitLevel(1, 0.5, 0.40, False, "TP1: +0.5R → 40%"),
                TakeProfitLevel(2, 1.0, 0.30, True, "TP2: +1.0R → 30% (SL→BE)"),
                TakeProfitLevel(3, 1.5, 1.00, False, "TP3: +1.5R → trailing"),
            ]
        
        return []
    
    def get_tp_levels(self) -> List[TakeProfitLevel]:
        """Obtener niveles de TP actuales"""
        return self.tp_levels
    
    def get_next_tp(self, closed_percent: float) -> Optional[TakeProfitLevel]:
        """Obtener siguiente TP para cerrar parcialmente
        
        Args:
            closed_percent: % ya cerrado (0.0 - 1.0)
            
        Returns:
            Siguiente nivel de TP o None si todo cerrado
        """
        for tp in self.tp_levels:
            if closed_percent < sum(t.close_percent for t in self.tp_levels[:tp.level]):
                return tp
        return None


class TrailingStopManager:
    """Gestor de trailing stop dinámico"""
    
    def __init__(self, config: TrailingStopConfig):
        """Inicializar manager de trailing stop
        
        Args:
            config: Configuración de trailing stop
        """
        self.config = config
        self.highest_price = None
        self.trail_distance = None
        self.activated = False
        self.activation_profit = 0
    
    def update(self, current_price: float, atr: float, entry_price: float, 
               is_buy: bool) -> Tuple[Optional[float], bool]:
        """Actualizar trailing stop
        
        Args:
            current_price: Precio actual
            atr: ATR actual
            entry_price: Precio de entrada
            is_buy: True si es compra
            
        Returns:
            (sl_price, is_trailing_active)
        """
        if not self.config.enabled:
            return None, False
        
        # Calcular profit actual en R
        if is_buy:
            profit_r = (current_price - entry_price) / atr if atr > 0 else 0
        else:
            profit_r = (entry_price - current_price) / atr if atr > 0 else 0
        
        # Activar trailing si profit mínimo alcanzado
        if profit_r >= self.config.min_profit_r and not self.activated:
            self.activated = True
            self.activation_profit = profit_r
            logger.info(f"🎯 Trailing stop activado: +{profit_r:.2f}R")
        
        if not self.activated:
            return None, False
        
        # Calcular distancia de trail
        trail_distance = atr * self.config.atr_multiple
        
        # Actualizar highest/lowest según dirección
        if is_buy:
            if self.highest_price is None or current_price > self.highest_price:
                self.highest_price = current_price
            
            # SL = highest_price - trail_distance
            sl_price = self.highest_price - trail_distance
            
        else:
            if self.highest_price is None or current_price < self.highest_price:
                self.highest_price = current_price
            
            # SL = lowest_price + trail_distance
            sl_price = self.highest_price + trail_distance
        
        self.trail_distance = trail_distance
        
        return sl_price, True
    
    def reset(self):
        """Resetear el trailing stop"""
        self.highest_price = None
        self.trail_distance = None
        self.activated = False
        self.activation_profit = 0


class HardCloseManager:
    """Gestor de cierres duros agresivos"""
    
    def __init__(self, config: HardCloseConfig):
        """Inicializar manager de hard close
        
        Args:
            config: Configuración de hard close
        """
        self.config = config
        self.triggered_reasons: List[str] = []
    
    def check_rsi_hardclose(self, rsi: float, is_buy: bool) -> Tuple[bool, str]:
        """Chequear si hay hard close por RSI
        
        Args:
            rsi: Valor de RSI actual
            is_buy: True si es posición compra
            
        Returns:
            (should_close, reason)
        """
        if not self.config.enabled:
            return False, ""
        
        # BUY: Cerrar si RSI overbought
        if is_buy and rsi > self.config.rsi_overbought:
            reason = f"HARD CLOSE: RSI {rsi:.1f} > {self.config.rsi_overbought} (overbought)"
            self.triggered_reasons.append(reason)
            logger.warning(f"🛑 {reason}")
            return True, reason
        
        # SELL: Cerrar si RSI oversold
        if not is_buy and rsi < self.config.rsi_oversold:
            reason = f"HARD CLOSE: RSI {rsi:.1f} < {self.config.rsi_oversold} (oversold)"
            self.triggered_reasons.append(reason)
            logger.warning(f"🛑 {reason}")
            return True, reason
        
        return False, ""
    
    def get_triggered_reasons(self) -> List[str]:
        """Obtener razones de triggers"""
        return self.triggered_reasons
    
    def reset(self):
        """Resetear triggers"""
        self.triggered_reasons = []


class AdvancedExitManager:
    """Manager principal de exits avanzados
    
    Combina:
    - Scale-out parcial en múltiples TP
    - Trailing stop dinámico
    - Hard closes agresivos (RSI)
    - Movimiento de SL a breakeven
    """
    
    def __init__(
        self,
        scale_out_profile: ScaleOutProfile = ScaleOutProfile.AGGRESSIVE,
        trailing_enabled: bool = True,
        hard_close_enabled: bool = True
    ):
        """Inicializar manager de exits avanzado
        
        Args:
            scale_out_profile: Perfil de scale-out
            trailing_enabled: Activar trailing stop
            hard_close_enabled: Activar hard closes
        """
        self.scale_out = ScaleOutManager(scale_out_profile)
        
        # Configurar trailing stop
        trailing_config = TrailingStopConfig(
            enabled=trailing_enabled,
            atr_multiple=1.0,
            min_profit_r=1.0,  # Activar después de +1R
            atr_lookback=14,
            update_frequency="candle"
        )
        self.trailing = TrailingStopManager(trailing_config)
        
        # Configurar hard closes (RSI agresivo)
        hard_close_config = HardCloseConfig(
            rsi_overbought=85,  # Más agresivo que 80
            rsi_oversold=15,    # Más agresivo que 20
            enabled=hard_close_enabled,
            reason="RSI extremo"
        )
        self.hard_close = HardCloseManager(hard_close_config)
        
        self.closed_percent = 0.0
        self.breakeven_active = False
    
    def process_tp(
        self,
        current_price: float,
        entry_price: float,
        atr: float,
        is_buy: bool,
        position_size: float
    ) -> Dict:
        """Procesar take profit con scale-out
        
        Args:
            current_price: Precio actual
            entry_price: Precio de entrada
            atr: ATR actual
            is_buy: True si compra
            position_size: Tamaño total de posición
            
        Returns:
            Dict con:
            - tp_hit: bool (¿TP alcanzado?)
            - close_amount: float (cantidad a cerrar)
            - tp_level: int (número de TP)
            - move_sl_to_be: bool (¿mover SL a BE?)
            - description: str
        """
        result = {
            "tp_hit": False,
            "close_amount": 0,
            "tp_level": 0,
            "move_sl_to_be": False,
            "description": ""
        }
        
        # Calcular profit en R
        if atr == 0:
            return result
        
        if is_buy:
            profit_r = (current_price - entry_price) / atr
            direction_ok = current_price > entry_price
        else:
            profit_r = (entry_price - current_price) / atr
            direction_ok = current_price < entry_price
        
        if not direction_ok:
            return result
        
        # Chequear cada nivel de TP
        for tp in self.scale_out.get_tp_levels():
            if profit_r >= tp.price_multiple and self.closed_percent < 1.0:
                
                # Calcular cantidad a cerrar
                remaining = 1.0 - self.closed_percent
                to_close = min(tp.close_percent, remaining)
                
                if to_close > 0.001:  # Mínimo 0.1%
                    self.closed_percent += to_close
                    
                    result["tp_hit"] = True
                    result["close_amount"] = to_close
                    result["tp_level"] = tp.level
                    result["move_sl_to_be"] = tp.move_sl_to_be
                    result["description"] = tp.description
                    
                    if tp.move_sl_to_be:
                        self.breakeven_active = True
                    
                    logger.info(f"✅ {tp.description}: cerrar {to_close*100:.1f}%")
                    break
        
        return result
    
    def process_trailing(
        self,
        current_price: float,
        atr: float,
        entry_price: float,
        is_buy: bool
    ) -> Tuple[Optional[float], bool]:
        """Procesar trailing stop
        
        Args:
            current_price: Precio actual
            atr: ATR actual
            entry_price: Precio de entrada
            is_buy: True si compra
            
        Returns:
            (new_sl, is_active)
        """
        return self.trailing.update(current_price, atr, entry_price, is_buy)
    
    def check_hard_close(self, rsi: float, is_buy: bool) -> Tuple[bool, str]:
        """Chequear hard close por RSI
        
        Args:
            rsi: RSI actual
            is_buy: True si compra
            
        Returns:
            (should_close, reason)
        """
        return self.hard_close.check_rsi_hardclose(rsi, is_buy)
    
    def get_summary(self) -> Dict:
        """Obtener resumen del estado de exits
        
        Returns:
            Diccionario con estado actual
        """
        return {
            "closed_percent": self.closed_percent,
            "remaining": 1.0 - self.closed_percent,
            "breakeven_active": self.breakeven_active,
            "trailing_active": self.trailing.activated,
            "trailing_distance": self.trailing.trail_distance,
            "tp_levels": [
                {
                    "level": tp.level,
                    "multiple": tp.price_multiple,
                    "close_percent": tp.close_percent,
                    "description": tp.description
                }
                for tp in self.scale_out.get_tp_levels()
            ]
        }
    
    def reset(self):
        """Resetear para nueva posición"""
        self.closed_percent = 0.0
        self.breakeven_active = False
        self.trailing.reset()
        self.hard_close.reset()


# ============================================================================
# PRESETS DE CONFIGURACIÓN
# ============================================================================

def get_aggressive_scalping_preset() -> Dict:
    """Preset AGGRESSIVE_SCALPING - Optimizado para M15
    
    - Risk: 0.75% por trade
    - Max trades: 6
    - Lote dinámico
    - IA: bias only (no bloquea)
    - RSI hard close: >85 / <15
    - SL: ATR * 1.2
    - TP: ATR * 2.0
    - Trailing: ATR * 1.0
    """
    return {
        "mode": "AGGRESSIVE_SCALPING",
        "timeframe": "M15",
        
        # Risk Management
        "risk_percent": 0.75,
        "max_concurrent_positions": 6,
        "dynamic_lot": True,
        
        # Exit Management
        "scale_out_profile": "SCALPING",
        "trailing_stop_enabled": True,
        "trailing_atr_multiple": 1.0,
        "trailing_min_profit_r": 1.0,
        
        # Hard Closes (Agresivo)
        "rsi_hard_close_overbought": 85,
        "rsi_hard_close_oversold": 15,
        
        # Stop Loss & Take Profit
        "sl_atr_multiple": 1.2,
        "tp_atr_multiple": 2.0,
        
        # IA Configuration
        "ai_mode": "BIAS_ONLY",
        "ai_blocks_trade": False,  # IA no bloquea, solo sesga
        "confidence_threshold": 0.35,
        
        # Hard Close Rules (existentes)
        "hard_close_rules": {
            "rsi_overbought": True,
            "time_to_live": True,
            "ema_crossover": True,
            "trend_reversal": True
        },
        
        # Descripción
        "description": "Aggressive scalping con scale-out parcial y trailing stop dinámico"
    }


def get_standard_preset() -> Dict:
    """Preset STANDARD - Swing trading
    
    Más conservador, para H1+
    """
    return {
        "mode": "STANDARD",
        "timeframe": "H1",
        
        "risk_percent": 1.0,
        "max_concurrent_positions": 3,
        "dynamic_lot": True,
        
        "scale_out_profile": "STANDARD",
        "trailing_stop_enabled": True,
        "trailing_atr_multiple": 1.5,
        "trailing_min_profit_r": 1.5,
        
        "rsi_hard_close_overbought": 80,
        "rsi_hard_close_oversold": 20,
        
        "sl_atr_multiple": 1.5,
        "tp_atr_multiple": 3.0,
        
        "ai_mode": "FULL",
        "ai_blocks_trade": False,
        "confidence_threshold": 0.40,
        
        "description": "Standard swing trading con scale-out conservador"
    }


def get_conservative_preset() -> Dict:
    """Preset CONSERVATIVE - Máxima seguridad
    
    Para traders risk-averse
    """
    return {
        "mode": "CONSERVATIVE",
        "timeframe": "D",
        
        "risk_percent": 0.5,
        "max_concurrent_positions": 2,
        "dynamic_lot": True,
        
        "scale_out_profile": "CONSERVATIVE",
        "trailing_stop_enabled": True,
        "trailing_atr_multiple": 2.0,
        "trailing_min_profit_r": 2.0,
        
        "rsi_hard_close_overbought": 80,
        "rsi_hard_close_oversold": 20,
        
        "sl_atr_multiple": 2.0,
        "tp_atr_multiple": 4.0,
        
        "ai_mode": "FULL",
        "ai_blocks_trade": True,
        "confidence_threshold": 0.50,
        
        "description": "Conservative daily trading con máxima protección"
    }
