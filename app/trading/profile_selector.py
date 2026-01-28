"""
Profile Selector - Reglas duras, no ML
Selecciona perfil basado en métricas backtested
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from app.core.logger import setup_logger
from app.trading.risk_profiles import get_risk_profile_manager

logger = setup_logger("profile_selector")


class ProfileSelector:
    """
    Selecciona perfil de riesgo basado en métricas reales
    
    Arquitectura:
    1. Colecta trades recientes (últimas N horas)
    2. Calcula 4 métricas duras
    3. Aplica reglas simples para seleccionar
    4. Respeta límites de estabilidad
    """
    
    # Ventanas de backtest por tipo
    BACKTEST_WINDOWS = {
        "SCALPING": 6,   # Últimas 6 horas
        "SWING": 48,     # Últimas 48 horas
        "CRYPTO": 24,    # Últimas 24 horas
        "DEFAULT": 12    # Últimas 12 horas (default)
    }
    
    # 🎯 REGLAS DURAS para seleccionar perfil
    # Simples, sin ML, pre-backtested
    SELECTION_RULES = {
        # CONSERVATIVE: Riesgo alto o drawdown alto
        "CONSERVATIVE": {
            "conditions": [
                {"metric": "win_rate", "op": "<", "value": 0.40},  # WR < 40%
                {"metric": "drawdown", "op": ">", "value": 2.0},   # DD > 2R
                {"metric": "profit_factor", "op": "<", "value": 1.1},  # PF < 1.1
            ],
            "logic": "ANY"  # Cualquiera de estas es suficiente
        },
        
        # AGGRESSIVE: Buen performance
        "AGGRESSIVE": {
            "conditions": [
                {"metric": "win_rate", "op": ">", "value": 0.55},  # WR > 55%
                {"metric": "profit_factor", "op": ">", "value": 1.4},  # PF > 1.4
                {"metric": "drawdown", "op": "<", "value": 1.0},   # DD < 1R
            ],
            "logic": "ALL"  # Todas estas deben cumplirse
        },
        
        # BALANCED: Por defecto, situación intermedia
        "BALANCED": {
            "conditions": [],
            "logic": "DEFAULT"  # Fallback si no cumplen otras reglas
        }
    }
    
    def __init__(self):
        self.profile_manager = get_risk_profile_manager()
        self.last_evaluation_time = None
        self.evaluation_interval_hours = 1  # Evaluar cada hora
        logger.info("✅ ProfileSelector initialized")
        logger.info("   Metrics: win_rate, profit_factor, drawdown, expectancy")
    
    def get_recent_trades(
        self,
        symbol: Optional[str] = None,
        hours_back: int = 12
    ) -> list:
        """
        Colecta trades recientes de la BD
        
        Args:
            symbol: Símbolo específico (None = todos)
            hours_back: Cuántas horas atrás mirar
        
        Returns:
            List de trades
        """
        from app.core.database import get_database_manager
        
        try:
            db = get_database_manager()
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            # Query trades desde cutoff_time
            trades = db.get_trades(
                since_timestamp=cutoff_time.isoformat(),
                symbol=symbol,
                status="closed"  # Solo trades cerrados
            )
            
            logger.info(f"📊 Collected {len(trades)} trades from last {hours_back}h")
            return trades or []
        
        except Exception as e:
            logger.error(f"Error collecting trades: {e}")
            return []
    
    def calculate_metrics(self, trades: list) -> Dict[str, float]:
        """
        Calcula 4 métricas duras
        
        1. Win rate = wins / total
        2. Profit factor = gross_profit / gross_loss
        3. Max drawdown = peak_to_trough (en R)
        4. Expectancy = avg R per trade
        
        Args:
            trades: Lista de trades cerrados
        
        Returns:
            Dict con métricas
        """
        
        if not trades:
            logger.warning("⚠️  No trades to calculate metrics")
            return {
                "win_rate": 0.5,
                "profit_factor": 1.0,
                "drawdown": 1.0,
                "expectancy": 0.0,
                "trade_count": 0
            }
        
        # Extraer datos
        profits = []
        losses = []
        r_values = []
        
        for trade in trades:
            try:
                pnl = float(trade.get("profit", 0))
                
                # Risk en $ (diferencia entre entry y SL)
                entry = float(trade.get("entry_price", 0))
                sl = float(trade.get("stop_loss", 0))
                risk_usd = abs(entry - sl) if entry and sl else 1.0
                
                if risk_usd == 0:
                    risk_usd = 1.0
                
                r_value = pnl / risk_usd  # R realizado
                r_values.append(r_value)
                
                if pnl > 0:
                    profits.append(pnl)
                else:
                    losses.append(abs(pnl))
            
            except Exception as e:
                logger.debug(f"Error processing trade: {e}")
                continue
        
        # 1️⃣ WIN RATE
        wins = len([p for p in profits if p > 0])
        total = len(trades)
        win_rate = wins / total if total > 0 else 0.5
        
        # 2️⃣ PROFIT FACTOR
        total_profit = sum(profits) if profits else 0.001
        total_loss = sum(losses) if losses else 0.001
        profit_factor = total_profit / total_loss if total_loss > 0 else 1.0
        
        # 3️⃣ MAX DRAWDOWN (en R)
        cumulative = 0
        peak = 0
        max_dd = 0
        for r in r_values:
            cumulative += r
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        
        # 4️⃣ EXPECTANCY (R promedio)
        expectancy = sum(r_values) / len(r_values) if r_values else 0.0
        
        metrics = {
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "drawdown": max_dd,  # En R
            "expectancy": expectancy,
            "trade_count": total,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(
            f"📊 Metrics: WR={win_rate:.1%}, PF={profit_factor:.2f}, "
            f"DD={max_dd:.2f}R, E={expectancy:.2f}R, n={total}"
        )
        
        return metrics
    
    def select_profile(self, metrics: Dict[str, float]) -> Tuple[str, str]:
        """
        Selecciona perfil basado en reglas duras
        
        Args:
            metrics: Diccionario con métricas (win_rate, profit_factor, etc.)
        
        Returns:
            Tuple[str, str]: (nombre_perfil, razón)
        """
        
        # Extrae métricas (para test, pueden no tener trade_count)
        win_rate = metrics.get("win_rate", 0.5)
        profit_factor = metrics.get("profit_factor", 1.0)
        drawdown = metrics.get("drawdown", 1.0)
        trade_count = metrics.get("trade_count", 0)
        
        # Sin trades suficientes → BALANCED (neutral)
        # Detectar cuando son default metrics (vacío): WR=50%, PF=1.0, DD=1.0
        is_default_metrics = (
            trade_count == 0 and
            abs(win_rate - 0.5) < 0.01 and  # ~50%
            abs(profit_factor - 1.0) < 0.01 and  # ~1.0
            abs(drawdown - 1.0) < 0.01  # ~1.0R
        )
        
        if is_default_metrics:
            logger.info("✅ BALANCED: Insufficient data (no trades yet)")
            return "BALANCED", "Sin trades suficientes"
        
        logger.info(
            f"🔍 Evaluating profile selection..."
            f" WR={win_rate:.1%}, PF={profit_factor:.2f}, DD={drawdown:.2f}R"
        )
        
        # Aplicar reglas
        # 1️⃣ Check CONSERVATIVE (riesgo alto)
        conservative_rules = self.SELECTION_RULES["CONSERVATIVE"]["conditions"]
        if self._check_conditions(metrics, conservative_rules, "ANY"):
            reason = "Riesgo detectado: WR baja o DD alta"
            logger.info(f"✅ CONSERVATIVE: {reason}")
            return "CONSERVATIVE", reason
        
        # 2️⃣ Check AGGRESSIVE (good performance)
        aggressive_rules = self.SELECTION_RULES["AGGRESSIVE"]["conditions"]
        if self._check_conditions(metrics, aggressive_rules, "ALL"):
            reason = "Buen performance: WR alta y PF fuerte"
            logger.info(f"✅ AGGRESSIVE: {reason}")
            return "AGGRESSIVE", reason
        
        # 3️⃣ Por defecto BALANCED
        reason = "Situación intermedia o insuficientes trades"
        logger.info(f"✅ BALANCED: {reason}")
        return "BALANCED", reason
    
    def _check_conditions(
        self,
        metrics: Dict[str, float],
        conditions: list,
        logic: str
    ) -> bool:
        """
        Evalúa un conjunto de condiciones
        
        Args:
            metrics: Diccionario de métricas
            conditions: Lista de condiciones
            logic: "ANY" o "ALL"
        
        Returns:
            bool: True si cumple la lógica
        """
        
        if not conditions:
            return False
        
        results = []
        for condition in conditions:
            metric_name = condition.get("metric")
            operator = condition.get("op")
            threshold = condition.get("value")
            
            metric_value = metrics.get(metric_name, 0)
            
            if operator == "<":
                result = metric_value < threshold
            elif operator == ">":
                result = metric_value > threshold
            elif operator == "<=":
                result = metric_value <= threshold
            elif operator == ">=":
                result = metric_value >= threshold
            else:
                result = False
            
            results.append(result)
            logger.debug(f"  {metric_name} {operator} {threshold} → {result}")
        
        if logic == "ANY":
            return any(results)
        elif logic == "ALL":
            return all(results)
        else:
            return False
    
    def evaluate_and_update(self, hours_back: int = 12) -> Dict[str, Any]:
        """
        Pipeline completo: collect → calculate → select → update
        
        Args:
            hours_back: Ventana de análisis en horas
        
        Returns:
            Dict con resultado de la evaluación
        """
        
        logger.info("=" * 60)
        logger.info("🔄 PROFILE EVALUATION CYCLE")
        logger.info("=" * 60)
        
        # 1️⃣ Colecta trades recientes
        trades = self.get_recent_trades(hours_back=hours_back)
        
        # 2️⃣ Calcula métricas
        metrics = self.calculate_metrics(trades)
        
        # 3️⃣ Selecciona perfil
        selected_profile, reason = self.select_profile(metrics)
        
        # 4️⃣ Intenta cambiar (respeta estabilidad)
        success, change_message = self.profile_manager.set_profile(
            selected_profile,
            reason=reason
        )
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "trades_analyzed": len(trades),
            "metrics": metrics,
            "selected_profile": selected_profile,
            "selection_reason": reason,
            "profile_changed": success,
            "change_message": change_message,
            "current_profile": self.profile_manager.get_current_profile().name
        }
        
        logger.info("=" * 60)
        logger.info(f"📊 SUMMARY:")
        logger.info(f"   Trades analyzed: {len(trades)}")
        logger.info(f"   Selected: {selected_profile} ({reason})")
        logger.info(f"   Changed: {success} ({change_message})")
        logger.info(f"   Active: {self.profile_manager.get_current_profile().name}")
        logger.info("=" * 60)
        
        return result


# Singleton instance
_profile_selector: Optional[ProfileSelector] = None


def get_profile_selector() -> ProfileSelector:
    """Get singleton profile selector"""
    global _profile_selector
    if _profile_selector is None:
        _profile_selector = ProfileSelector()
    return _profile_selector
