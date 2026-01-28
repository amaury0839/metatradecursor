"""
Risk Profiles - Arquitectura robusta y simple
Perfiles pre-backtesteados, no valores sueltos
"""

from typing import Dict, Any
from dataclasses import dataclass
from app.core.logger import setup_logger

logger = setup_logger("risk_profiles")


@dataclass
class RiskProfile:
    """Perfil de riesgo con parámetros pre-backtesteados"""
    
    name: str
    risk_per_trade: float  # % del balance por trade
    max_positions: int  # Máximo de posiciones concurrentes
    atr_sl_mult: float  # Multiplicador ATR para stop loss
    min_confidence_score: float  # Score mínimo para operar
    max_daily_loss: float  # Máx pérdida diaria permitida %
    max_drawdown: float  # Máx drawdown permitido %
    position_timeout_hours: int  # Cerrar posición después de N horas
    
    def __str__(self) -> str:
        return (
            f"{self.name}: "
            f"risk={self.risk_per_trade}%, "
            f"max_pos={self.max_positions}, "
            f"SL={self.atr_sl_mult}x ATR, "
            f"min_score={self.min_confidence_score}"
        )


class RiskProfileManager:
    """
    Gestiona perfiles de riesgo pre-backtesteados
    
    Arquitectura:
    1. Perfiles discretos (no continuos)
    2. Pre-backtesteados offline
    3. Reglas duras para seleccionar
    4. Estabilidad entre cambios
    """
    
    # 🎯 PERFILES PRE-BACKTESTEADOS
    PROFILES = {
        "CONSERVATIVE": RiskProfile(
            name="CONSERVATIVE",
            risk_per_trade=0.25,      # 0.25% por trade (muy conservador)
            max_positions=3,           # Máx 3 posiciones
            atr_sl_mult=1.8,          # Stop loss amplio (menos stops)
            min_confidence_score=0.70, # Exige alta confianza
            max_daily_loss=5.0,       # 5% max loss diario
            max_drawdown=3.0,         # 3% max drawdown
            position_timeout_hours=48 # Cierra después de 48h
        ),
        
        "BALANCED": RiskProfile(
            name="BALANCED",
            risk_per_trade=0.5,       # 0.5% por trade (equilibrado)
            max_positions=5,          # Máx 5 posiciones
            atr_sl_mult=1.5,          # Stop loss medio
            min_confidence_score=0.60, # Confianza media
            max_daily_loss=8.0,       # 8% max loss diario
            max_drawdown=5.0,         # 5% max drawdown
            position_timeout_hours=24 # Cierra después de 24h
        ),
        
        "AGGRESSIVE": RiskProfile(
            name="AGGRESSIVE",
            risk_per_trade=0.75,      # 0.75% por trade (agresivo)
            max_positions=7,          # Máx 7 posiciones
            atr_sl_mult=1.3,          # Stop loss apretado (toma profits rápido)
            min_confidence_score=0.50, # Baja confianza aceptable
            max_daily_loss=12.0,      # 12% max loss diario
            max_drawdown=8.0,         # 8% max drawdown
            position_timeout_hours=12 # Cierra después de 12h
        )
    }
    
    # 🔒 ESTABILIDAD: Regla crítica
    MIN_HOURS_BETWEEN_PROFILE_CHANGES = 3  # Mín 3 horas entre cambios
    MAX_PROFILE_JUMPS_PER_DAY = 2          # Máx 2 cambios por día
    
    def __init__(self):
        self.current_profile = self.PROFILES["BALANCED"]
        self.last_profile_change_time = None
        self.profile_changes_today = 0
        logger.info(f"✅ RiskProfileManager initialized")
        logger.info(f"   Available profiles: {', '.join(self.PROFILES.keys())}")
        logger.info(f"   Starting with: {self.current_profile.name}")
    
    def get_profile(self, name: str) -> RiskProfile:
        """Obtener perfil por nombre"""
        if name not in self.PROFILES:
            logger.warning(f"Profile '{name}' not found, using BALANCED")
            return self.PROFILES["BALANCED"]
        return self.PROFILES[name]
    
    def get_current_profile(self) -> RiskProfile:
        """Obtener perfil actual activo"""
        return self.current_profile
    
    def get_all_profiles(self) -> Dict[str, RiskProfile]:
        """Obtener todos los perfiles disponibles"""
        return self.PROFILES.copy()
    
    def validate_profile_change(self) -> tuple[bool, str]:
        """
        Valida si se puede cambiar el perfil ahora
        
        Reglas de estabilidad:
        - Mín 3 horas entre cambios
        - Máx 2 cambios por día
        
        Returns:
            tuple[bool, str]: (puede_cambiar, razón)
        """
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        # Primer cambio siempre permitido
        if self.last_profile_change_time is None:
            return True, "Primera evaluación"
        
        # Check: 3 horas desde último cambio
        hours_since_change = (now - self.last_profile_change_time).total_seconds() / 3600
        if hours_since_change < self.MIN_HOURS_BETWEEN_PROFILE_CHANGES:
            remaining = self.MIN_HOURS_BETWEEN_PROFILE_CHANGES - hours_since_change
            return False, f"Esperar {remaining:.1f}h más (mín {self.MIN_HOURS_BETWEEN_PROFILE_CHANGES}h entre cambios)"
        
        # Check: 2 cambios por día
        if self.profile_changes_today >= self.MAX_PROFILE_JUMPS_PER_DAY:
            return False, f"Máximo {self.MAX_PROFILE_JUMPS_PER_DAY} cambios por día alcanzado"
        
        return True, "Cambio permitido"
    
    def set_profile(self, profile_name: str, reason: str = "") -> tuple[bool, str]:
        """
        Cambiar perfil actual
        
        Args:
            profile_name: Nombre del perfil (CONSERVATIVE, BALANCED, AGGRESSIVE)
            reason: Razón del cambio (para logs)
        
        Returns:
            tuple[bool, str]: (éxito, mensaje)
        """
        from datetime import datetime
        
        # Validar que exista
        if profile_name not in self.PROFILES:
            return False, f"Perfil '{profile_name}' no existe"
        
        # Si es el mismo, no hacer nada
        new_profile = self.PROFILES[profile_name]
        if new_profile.name == self.current_profile.name:
            return False, f"Ya estamos en {profile_name}"
        
        # Validar estabilidad
        can_change, stability_reason = self.validate_profile_change()
        if not can_change:
            logger.warning(f"🔒 Cambio bloqueado: {stability_reason}")
            return False, stability_reason
        
        # Hacer cambio
        old_profile = self.current_profile.name
        self.current_profile = new_profile
        self.last_profile_change_time = datetime.now()
        self.profile_changes_today += 1
        
        logger.info(
            f"🔄 PROFILE CHANGE: {old_profile} → {profile_name} "
            f"({reason})"
        )
        logger.info(f"   {self.current_profile}")
        
        return True, f"Cambiado a {profile_name}"
    
    def reset_daily_counter(self):
        """Reset contador diario (llamar a las 00:00)"""
        from datetime import datetime
        now = datetime.now()
        if now.hour == 0 and now.minute < 5:  # Entre 00:00 y 00:05
            self.profile_changes_today = 0
            logger.info("📊 Daily profile change counter reset")


# Singleton instance
_profile_manager: 'RiskProfileManager' = None


def get_risk_profile_manager() -> RiskProfileManager:
    """Get singleton risk profile manager"""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = RiskProfileManager()
    return _profile_manager
