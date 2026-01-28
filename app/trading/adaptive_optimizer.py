"""Adaptive Risk Optimizer - Hourly parameter adjustment using AI and backtest analysis"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from app.core.logger import setup_logger
from app.core.config import get_config
from app.trading.mt5_client import get_mt5_client
from app.trading.portfolio import get_portfolio_manager
from app.core.database import get_database_manager
from app.ai.gemini_client import GeminiClient

logger = setup_logger("adaptive_optimizer")


class AdaptiveRiskOptimizer:
    """Dynamically adjusts risk parameters per ticker based on hourly backtest + AI analysis"""
    
    def __init__(self):
        self.config = get_config()
        self.mt5 = get_mt5_client()
        self.portfolio = get_portfolio_manager()
        self.db = get_database_manager()
        self.gemini = GeminiClient()
        self.params_file = Path(__file__).parent.parent.parent / "data" / "adaptive_params.json"
        self.params_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize adaptive parameters
        self.ticker_params = self._load_params()
        self.last_optimization = {}
        
    def _load_params(self) -> Dict:
        """Load saved adaptive parameters or create defaults"""
        if self.params_file.exists():
            try:
                with open(self.params_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load adaptive params: {e}")
        
        # Return default empty dict
        return {}
    
    def _save_params(self):
        """Save adaptive parameters to disk"""
        try:
            with open(self.params_file, 'w') as f:
                json.dump(self.ticker_params, f, indent=2)
            logger.info(f"✅ Saved adaptive parameters for {len(self.ticker_params)} tickers")
        except Exception as e:
            logger.error(f"Failed to save adaptive params: {e}")
    
    def get_ticker_params(self, symbol: str) -> Dict:
        """Get optimized parameters for a specific ticker"""
        if symbol not in self.ticker_params:
            # Return defaults
            return {
                "max_positions_per_ticker": 2,
                "max_risk_pct": 1.5,
                "max_loss_pct": 4.0,
                "min_win_rate_pct": 45.0,
                "max_daily_loss_pct": 10.0,
                "last_updated": None,
                "win_rate": 0.0,
                "profit_factor": 1.0,
            }
        
        return self.ticker_params[symbol]
    
    def analyze_ticker_performance(self, symbol: str) -> Dict:
        """Analyze performance metrics for a ticker from the last hour"""
        try:
            # Get trades from last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            trades = self.db.query_trades(symbol, since=one_hour_ago)
            
            if not trades:
                return {
                    "symbol": symbol,
                    "trades_count": 0,
                    "win_rate": 0.0,
                    "profit_factor": 1.0,
                    "avg_win": 0.0,
                    "avg_loss": 0.0,
                    "total_pnl": 0.0,
                    "status": "insufficient_data"
                }
            
            # Calculate metrics
            closed_trades = [t for t in trades if t.get('pnl') is not None]
            if not closed_trades:
                return {
                    "symbol": symbol,
                    "trades_count": len(trades),
                    "win_rate": 0.0,
                    "profit_factor": 1.0,
                    "status": "no_closed_trades"
                }
            
            wins = [t for t in closed_trades if t.get('pnl', 0) > 0]
            losses = [t for t in closed_trades if t.get('pnl', 0) < 0]
            
            win_rate = (len(wins) / len(closed_trades)) * 100 if closed_trades else 0
            total_profit = sum(t.get('pnl', 0) for t in wins) if wins else 0
            total_loss = abs(sum(t.get('pnl', 0) for t in losses)) if losses else 0
            profit_factor = total_profit / total_loss if total_loss > 0 else (total_profit / 0.01 if total_profit > 0 else 1.0)
            
            avg_win = total_profit / len(wins) if wins else 0
            avg_loss = total_loss / len(losses) if losses else 0
            
            return {
                "symbol": symbol,
                "trades_count": len(closed_trades),
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "total_pnl": sum(t.get('pnl', 0) for t in closed_trades),
                "wins": len(wins),
                "losses": len(losses),
                "status": "analyzed"
            }
        except Exception as e:
            logger.error(f"Error analyzing {symbol} performance: {e}")
            return {
                "symbol": symbol,
                "status": "error",
                "error": str(e)
            }
    
    def optimize_with_ai(self, symbol: str, performance: Dict) -> Dict:
        """Use AI to recommend parameter adjustments based on performance"""
        try:
            current_params = self.get_ticker_params(symbol)
            
            # Build optimization prompt
            prompt = f"""
Analiza el performance de trading para {symbol} de la última hora y recomienda ajustes de parámetros de riesgo:

**Performance Actual:**
- Win Rate: {performance.get('win_rate', 0):.1f}%
- Profit Factor: {performance.get('profit_factor', 1.0):.2f}
- Trades: {performance.get('trades_count', 0)} (Ganancias: {performance.get('wins', 0)}, Pérdidas: {performance.get('losses', 0)})
- PnL Última Hora: ${performance.get('total_pnl', 0):.2f}
- Avg Win: ${performance.get('avg_win', 0):.2f}
- Avg Loss: ${performance.get('avg_loss', 0):.2f}

**Parámetros Actuales:**
- Max Risk %: {current_params.get('max_risk_pct', 1.5)}%
- Max Positions: {current_params.get('max_positions_per_ticker', 2)}
- Min Win Rate: {current_params.get('min_win_rate_pct', 45)}%

**Reglas de Ajuste:**
1. Si Win Rate < 40%: AUMENTAR conservadurismo (reducir riesgo, reducir posiciones)
2. Si Win Rate > 55%: AUMENTAR agresividad (aumentar riesgo, aumentar posiciones)
3. Si Profit Factor < 1.0: Reducir volumen 10%
4. Si Profit Factor > 2.0: Aumentar volumen 10% (máx 2% risk)
5. Mantener balance: no cambiar más de ±20% por ajuste

Devuelve SOLO JSON sin explicación:
{{
    "recommendation": "increase|decrease|maintain",
    "max_risk_pct": <number>,
    "max_positions": <number>,
    "min_win_rate_pct": <number>,
    "reasoning": "<brief reason>"
}}
"""
            
            # Get AI recommendation
            response = self.gemini.chat(prompt, model="gemini-2.5-flash-lite", temperature=0.3)
            
            # Parse response
            try:
                # Extract JSON from response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    recommendation = json.loads(json_str)
                    
                    logger.info(f"✅ AI Optimization for {symbol}: {recommendation.get('recommendation')} - {recommendation.get('reasoning')}")
                    return recommendation
                else:
                    logger.warning(f"Could not parse AI response for {symbol}: {response[:100]}")
                    return {"recommendation": "maintain"}
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error for {symbol}: {e}")
                return {"recommendation": "maintain"}
        
        except Exception as e:
            logger.error(f"Error optimizing {symbol} with AI: {e}")
            return {"recommendation": "maintain"}
    
    def apply_optimization(self, symbol: str, recommendation: Dict):
        """Apply AI recommendations to update parameters"""
        try:
            current = self.get_ticker_params(symbol)
            
            # Extract recommended values (with safety bounds)
            new_params = {
                **current,
                "max_risk_pct": min(max(recommendation.get('max_risk_pct', current['max_risk_pct']), 0.5), 3.0),
                "max_positions_per_ticker": max(min(recommendation.get('max_positions', current['max_positions_per_ticker']), 5), 1),
                "min_win_rate_pct": min(max(recommendation.get('min_win_rate_pct', current['min_win_rate_pct']), 30), 70),
                "last_updated": datetime.now().isoformat(),
            }
            
            # Store in memory
            self.ticker_params[symbol] = new_params
            
            # Log changes
            if new_params != current:
                logger.info(f"🔧 Updated {symbol}: Risk {current['max_risk_pct']}% → {new_params['max_risk_pct']}%, "
                           f"Positions {current['max_positions_per_ticker']} → {new_params['max_positions_per_ticker']}")
            
            self.last_optimization[symbol] = {
                "timestamp": datetime.now().isoformat(),
                "recommendation": recommendation,
                "new_params": new_params
            }
        
        except Exception as e:
            logger.error(f"Error applying optimization for {symbol}: {e}")
    
    def hourly_optimization_cycle(self):
        """Execute hourly optimization for all trading symbols"""
        logger.info("="*80)
        logger.info("🔄 HOURLY ADAPTIVE OPTIMIZATION CYCLE STARTED")
        logger.info("="*80)
        
        symbols = self.config.trading.default_symbols
        optimization_results = []
        
        for symbol in symbols:
            try:
                # Analyze performance
                performance = self.analyze_ticker_performance(symbol)
                
                if performance.get('status') != "analyzed":
                    logger.debug(f"⏭️  {symbol}: {performance.get('status')}")
                    continue
                
                # Get AI recommendation
                recommendation = self.optimize_with_ai(symbol, performance)
                
                # Apply optimization
                self.apply_optimization(symbol, recommendation)
                
                optimization_results.append({
                    "symbol": symbol,
                    "performance": performance,
                    "recommendation": recommendation
                })
            
            except Exception as e:
                logger.error(f"Error in optimization cycle for {symbol}: {e}")
        
        # Save optimized parameters
        self._save_params()
        
        # Log summary
        logger.info(f"✅ OPTIMIZATION CYCLE COMPLETE: {len(optimization_results)} tickers optimized")
        for result in optimization_results:
            sym = result['symbol']
            perf = result['performance']
            rec = result['recommendation']
            logger.info(f"   {sym}: WR={perf.get('win_rate', 0):.0f}% PF={perf.get('profit_factor', 1.0):.1f}x → {rec.get('recommendation', 'maintain')}")
        
        return optimization_results


# Global instance
_optimizer: Optional[AdaptiveRiskOptimizer] = None


def get_adaptive_optimizer() -> AdaptiveRiskOptimizer:
    """Get global optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = AdaptiveRiskOptimizer()
    return _optimizer
