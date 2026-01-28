"""Streamlit main entry point - Local version (full trading bot)"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import MetaTrader5 as mt5

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_config, reload_config
from app.core.state import get_state_manager
from app.core.scheduler import TradingScheduler
from app.core.logger import setup_logger
from app.core.analysis_logger import get_analysis_logger
from app.core.database import get_database_manager
from app.trading.mt5_client import get_mt5_client
from app.trading.integrated_analysis import get_integrated_analyzer
from app.trading.market_status import get_market_status
from app.ui.pages_dashboard_unified import render_dashboard
from app.ui.pages_config import render_config
from app.ui.pages_strategy import render_strategy
from app.ui.pages_risk import render_risk
from app.ui.pages_news import render_news
from app.ui.pages_logs import render_logs
from app.ui.pages_analysis import render_analysis_logs
# 🚀 AGGRESSIVE_SCALPING IMPORTS
from app.trading.aggressive_scalping_integration import (
    get_aggressive_scalping_engine,
    apply_aggressive_scalping_config
)
from app.trading.risk import get_trading_preset

# 🔺 PYRAMIDING IMPORTS (Aggressive pyramiding + dynamic min volume)
from app.trading.pyramiding_aggressive import (
    get_pyramiding_engine,
    PyramidingIntegration,
)

# Configure page
st.set_page_config(
    page_title="AI Forex Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

logger = setup_logger("streamlit_main")


# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.scheduler = None
    st.session_state.mt5_connected = False
    # Auto-connect in demo mode
    try:
        import app.trading.mt5_client as mt5_module
        if not getattr(mt5_module, 'MT5_AVAILABLE', True):
            mt5_client = get_mt5_client()
            mt5_client.connect()
    except Exception:
        pass


# 🆕 Tracking para evaluaciones horarias de perfiles
_last_profile_evaluation = None


def evaluate_risk_profile_hourly():
    """
    Evalúa y actualiza perfil de riesgo cada hora
    Se ejecuta al inicio de main_trading_loop si ha pasado 1 hora
    
    Returns:
        Dict con resultado de la evaluación (o None si no se ejecutó)
    """
    global _last_profile_evaluation
    from datetime import datetime, timedelta
    from app.trading.profile_selector import get_profile_selector
    
    now = datetime.now()
    
    # Checkear si han pasado 1 hora desde la última evaluación
    if _last_profile_evaluation is not None:
        if (now - _last_profile_evaluation) < timedelta(hours=1):
            return None  # No evaluamos aún
    
    # Ejecutar evaluación
    logger.info("=" * 60)
    logger.info("🔄 HOURLY RISK PROFILE EVALUATION")
    logger.info("=" * 60)
    
    try:
        selector = get_profile_selector()
        result = selector.evaluate_and_update(hours_back=12)
        _last_profile_evaluation = now
        logger.info(f"✅ Profile evaluation complete: {result['current_profile']}")
        return result
    except Exception as e:
        logger.error(f"❌ Profile evaluation failed: {e}")
        return None


def main_trading_loop():
    """Main trading loop callback"""
    try:
        from app.core.state import get_state_manager, DecisionAudit
        from app.trading.mt5_client import get_mt5_client
        from app.trading.data import get_data_provider
        from app.trading.strategy import get_strategy
        from app.trading.risk import get_risk_manager
        from app.trading.execution import get_execution_manager
        from app.trading.portfolio import get_portfolio_manager
        from app.trading.position_manager import get_position_manager
        from app.trading.parameter_injector import get_parameter_injector
        from app.ai.decision_engine import DecisionEngine
        from app.ai.dynamic_decision_engine import get_dynamic_decision_engine
        from app.ai.schemas import TradingDecision, OrderDetails
        from datetime import datetime
        
        # 🌟 10-POINT REFACTORING IMPORTS
        from app.trading.decision_constants import MIN_EXECUTION_CONFIDENCE, RSI_OVERBOUGHT, RSI_OVERSOLD, MAX_SPREAD_PIPS_FOREX, MAX_SPREAD_PIPS_CRYPTO, CURRENCY_CLUSTERS, SKIP_REASONS
        from app.trading.signal_execution_split import split_decision, log_skip_reason, SignalAnalysis, ExecutionDecision
        from app.trading.trade_validation import TradeValidationGates, run_validation_gates
        from app.trading.ai_optimization import should_call_ai
        
        # 🆕 RISK PROFILE HOURLY EVALUATION
        evaluate_risk_profile_hourly()
        
        state = get_state_manager()
        mt5 = get_mt5_client()
        data = get_data_provider()
        strategy = get_strategy()
        risk = get_risk_manager()
        execution = get_execution_manager()
        portfolio = get_portfolio_manager()
        position_manager = get_position_manager()
        param_injector = get_parameter_injector()  # 🆕 Adaptive parameter injector
        
        # 🚀 AGGRESSIVE_SCALPING ENGINE INITIALIZATION
        try:
            scalping_engine = get_aggressive_scalping_engine()
            scalping_preset = get_trading_preset("AGGRESSIVE_SCALPING")
            logger.info(f"✅ AGGRESSIVE_SCALPING Engine loaded - Risk: {scalping_preset['risk_percent']}% Max: {scalping_preset['max_concurrent_positions']} positions")
        except Exception as e:
            logger.error(f"❌ Failed to load AGGRESSIVE_SCALPING engine: {e}")
            scalping_engine = None
        
        # � PYRAMIDING ENGINE INITIALIZATION (Aggressive pyramiding + dynamic min volume)
        try:
            pyramiding_engine = get_pyramiding_engine()
            logger.info(f"✅ PYRAMIDING Engine loaded - Dynamic min volume: $5k→0.05 lots, $10k→0.10 lots")
        except Exception as e:
            logger.error(f"❌ Failed to load PYRAMIDING engine: {e}")
            pyramiding_engine = None
        
        # �🚀 ENHANCED: Use dynamic decision engine with per-ticker risk adjustment
        try:
            decision_engine = get_dynamic_decision_engine()
            logger.info("✅ Using Enhanced Decision Engine with per-ticker dynamic risk adjustment")
        except Exception as e:
            logger.warning(f"⚠️  Could not load enhanced decision engine: {e}, using standard engine")
            decision_engine = DecisionEngine()
        
        config = get_config()
        analysis_logger = get_analysis_logger()
        db = get_database_manager()  # Add database manager for saving analyses
        
        # 🔴 CRITICAL DEBUG: Log trading mode at every cycle start
        logger.info(f"🔴 TRADING MODE CHECK: is_paper_mode={config.is_paper_mode()} trading_mode={config.trading.mode} MT5_connected={mt5.is_connected()}")
        
        # Check kill switch
        if state.is_kill_switch_active():
            return
        
        # Check connection - warn if not connected but continue with technical fallback
        if not mt5.is_connected():
            logger.warning("⚠️ MT5 not connected - using technical signals only")
            # Continue with technical signal processing instead of returning
        else:
            logger.info("✅ MT5 connected - using live account data")
        
        # Update account info
        account_info = mt5.get_account_info()
        if account_info:
            state.current_equity = account_info.get('equity', 0)
            state.current_balance = account_info.get('balance', 0)
            if state.current_equity > state.max_equity:
                state.max_equity = state.current_equity
        
        # Get symbols to trade (from config only - optimized)
        symbols = config.trading.default_symbols
        timeframe = config.trading.default_timeframe
        
        # 🥇 SOLUTION 1: Filter out problematic FOREX pairs for small accounts
        # These pairs have very high volume_min and won't execute on small balance
        FOREX_DISABLED_FOR_SMALL_BALANCE = [
            "EURJPY",    # High volume_min (10+), wide spread
            "GBPJPY",    # High volume_min (10+), wide spread  
            "EURGBP",    # High volume_min, low liquidity for small accounts
            "USDJPY",    # JPY crosses often have high volume_min
            "AUDNZD",    # Cross pairs often too illiquid for small accounts
            "EURNZD",    # Cross pairs
            "GBPNZD",    # Cross pairs
        ]
        
        # Get account equity to decide filtering
        equity = account_info.get('equity', 0) if account_info else 0
        symbols_filtered = []
        for symbol in symbols:
            if equity < 10000 and symbol in FOREX_DISABLED_FOR_SMALL_BALANCE:
                logger.info(f"⏭️  {symbol} disabled for small account (equity=${equity:.2f})")
            else:
                symbols_filtered.append(symbol)
        
        symbols = symbols_filtered
        logger.info(f"🎯 Trading symbols after filtering: {symbols} (account equity=${equity:.2f})")
        
        # OPTIMIZATION: Skip dynamic market status check to save 500ms+ per cycle
        # Use only configured symbols (much faster)
        logger.info(f"Trading symbols (optimized, no market check): {symbols}")
        
        # Get integrated analyzer (includes technical + sentiment)
        integrated_analyzer = get_integrated_analyzer()
        
        # Get account info for balance-based calculations
        account_info = mt5.get_account_info()
        account_balance = account_info.get('balance', 0) if account_info else 0
        
        # === STEP 1: REVIEW OPEN POSITIONS ===
        open_positions = portfolio.get_open_positions()
        for position in open_positions:
            try:
                pos_symbol = position.get('symbol', '')
                pos_ticket = position.get('ticket', 0)
                pos_type = 'BUY' if position.get('type', 0) == 0 else 'SELL'
                pos_profit = position.get('profit', 0.0)
                pos_volume = position.get('volume', 0.0)
                pos_price = position.get('price_open', 0.0)
                pos_sl = position.get('price_stop', 0.0)
                
                logger.info(f"Reviewing open position: {pos_symbol} {pos_type} {pos_volume} lots, ticket={pos_ticket}, P&L=${pos_profit:.2f}")
                
                # Get current analysis for position symbol
                pos_analysis = integrated_analyzer.analyze_symbol(pos_symbol, timeframe)
                current_signal = pos_analysis["signal"]
                
                # 🔺 CHECK PYRAMIDING TRIGGER: At +0.5R, add 50% more
                if pyramiding_engine:
                    try:
                        tick = data.get_current_tick(pos_symbol)
                        current_price = tick.get('bid' if pos_type == 'SELL' else 'ask', pos_price) if tick else pos_price
                        
                        should_pyramid, pyramid_details = pyramiding_engine.check_pyramid_and_execute(
                            symbol=pos_symbol,
                            current_price=current_price,
                            account_balance=account_balance,
                        )
                        
                        if should_pyramid and pyramid_details:
                            logger.info(f"🔺 PYRAMID TRIGGER: {pyramid_details['message']}")
                            pyramid_lot = pyramid_details['pyramid_lot']
                            pyramid_entry = pyramid_details['pyramid_entry']
                            new_combined_sl = pyramid_details['new_combined_sl']
                            
                            # Execute pyramid: add new position
                            success, pyramid_error = execution.place_market_order(
                                symbol=pos_symbol,
                                order_type=pos_type,
                                volume=pyramid_lot,
                                sl_price=new_combined_sl,
                                tp_price=0,  # Use existing TP
                                comment=f"Pyramid at +0.5R - Additional {pyramid_lot:.2f} lots @ {pyramid_entry:.5f}",
                                atr=0.001,
                            )
                            
                            if success:
                                logger.info(f"✅ PYRAMID EXECUTED: Added {pyramid_lot:.2f} lots to {pos_symbol}")
                                # Update SL on original position to combined SL
                                if pos_sl != new_combined_sl:
                                    mt5.modify_position_sl(pos_ticket, new_combined_sl)
                                    logger.info(f"🔐 Updated original position SL to breakeven: {new_combined_sl:.5f}")
                            else:
                                logger.warning(f"⚠️ PYRAMID EXECUTION FAILED: {pyramid_error}")
                    
                    except Exception as e:
                        logger.debug(f"Pyramiding check error: {e}")

                confidence = pos_analysis.get("confidence", 0.5)
                
                # Save analysis to database for logs UI
                try:
                    db.save_analysis(pos_analysis)
                except Exception as e:
                    logger.warning(f"Failed to save position analysis to DB: {e}")
                
                # � AGGRESSIVE_SCALPING: Check scale-out, trailing stop, hard close
                if scalping_engine:
                    try:
                        # Get ATR for calculations
                        atr = pos_analysis.get("technical", {}).get("data", {}).get("atr", 0.001)
                        is_buy = pos_type == 'BUY'
                        current_tick = data.get_current_tick(pos_symbol)
                        current_price = current_tick.get('bid', pos_price) if current_tick else pos_price
                        
                        # 1️⃣ CHECK SCALE-OUT (TP levels)
                        scale_out_result = scalping_engine.check_scale_out(
                            symbol=pos_symbol,
                            current_price=current_price,
                            entry_price=pos_price,
                            atr=atr,
                            is_buy=is_buy,
                            current_lot=pos_volume
                        )
                        if scale_out_result.get("scale_out_hit"):
                            close_amount = scale_out_result["close_amount"]
                            close_percent = scale_out_result["close_percent"]
                            tp_level = scale_out_result["tp_level"]
                            close_lot = pos_volume * close_percent
                            
                            logger.info(f"🎯 SCALE-OUT TP{tp_level}: Closing {close_percent*100:.0f}% ({close_lot:.2f} lots) @ {current_price:.5f}")
                            
                            # Partial close in MT5
                            success, error = execution.close_position_partial(pos_ticket, close_lot)
                            if success:
                                logger.info(f"✅ Partial close executed: {close_lot:.2f} lots")
                                if scale_out_result.get("move_sl_to_be"):
                                    logger.info(f"🔐 Moving SL to breakeven: {pos_price:.5f}")
                                    mt5.modify_position_sl(pos_ticket, pos_price)
                            else:
                                logger.error(f"❌ Partial close failed: {error}")
                        
                        # 2️⃣ CHECK TRAILING STOP
                        trailing_sl, is_trailing_active = scalping_engine.check_trailing_stop(
                            symbol=pos_symbol,
                            current_price=current_price,
                            atr=atr,
                            entry_price=pos_price,
                            is_buy=is_buy
                        )
                        if is_trailing_active and trailing_sl > 0:
                            current_sl = position.get('price_stop', 0)
                            if is_buy and trailing_sl > current_sl:
                                logger.info(f"🔄 Trailing SL updated: {current_sl:.5f} → {trailing_sl:.5f}")
                                mt5.modify_position_sl(pos_ticket, trailing_sl)
                            elif not is_buy and trailing_sl < current_sl:
                                logger.info(f"🔄 Trailing SL updated: {current_sl:.5f} → {trailing_sl:.5f}")
                                mt5.modify_position_sl(pos_ticket, trailing_sl)
                        
                        # 3️⃣ CHECK HARD CLOSE (RSI extremes)
                        rsi = pos_analysis.get("technical", {}).get("data", {}).get("rsi", 50)
                        should_hard_close, hard_close_reason = scalping_engine.check_hard_close_rsi(
                            symbol=pos_symbol,
                            rsi=rsi,
                            is_buy=is_buy
                        )
                        if should_hard_close:
                            logger.warning(f"🔴 HARD CLOSE TRIGGERED: {hard_close_reason} (RSI={rsi:.1f})")
                            success, error = execution.close_position(pos_ticket)
                            if success:
                                logger.info(f"✅ Position closed by hard close rule: {pos_profit:.2f}")
                            else:
                                logger.error(f"❌ Hard close failed: {error}")
                            continue  # Skip rest of checks
                    
                    except Exception as e:
                        logger.debug(f"AGGRESSIVE_SCALPING check error: {e}")
                
                # �🔧 Exit Management: Check for RSI extremes, opposite signal, breakeven, trailing stop
                should_close = False
                close_reason = []
                
                # 1. Check opposite signal (BUY position + SELL signal → close)
                should_close_opposite, opposite_reason = position_manager.should_close_on_opposite_signal(
                    position_type=pos_type,
                    current_signal=current_signal,
                    confidence=confidence,
                    min_confidence_to_reverse=0.70
                )
                if should_close_opposite:
                    should_close = True
                    close_reason.append(opposite_reason)
                
                # 2. Check RSI extremes (exit management for scalping - don't hold through reversal)
                try:
                    if pos_analysis.get("technical") and pos_analysis["technical"].get("data"):
                        tech_data = pos_analysis["technical"]["data"]
                        rsi = tech_data.get("rsi", 50)
                        
                        # Get current price and EMA values for exit checks
                        tick = data.get_current_tick(pos_symbol)
                        current_price = tick.get('bid', 0) if tick else 0
                        position_open_price = position.get('price_open', 0)
                        
                        # ⚔️ REGLA A - RSI EXTREMO SIN EXCEPCIONES
                        should_close_rsi, rsi_reason = position_manager.should_close_on_rsi_extreme(
                            symbol=pos_symbol,
                            position_type=pos_type,
                            rsi_value=rsi,
                            current_price=current_price,
                            open_price=position_open_price
                        )
                        if should_close_rsi:
                            should_close = True
                            close_reason.append(rsi_reason)
                            logger.warning(f"🔴 {rsi_reason}")
                        
                        # ⚔️ REGLA B - TTL (MAX CANDLES WITHOUT PROFIT)
                        try:
                            should_close_ttl, ttl_reason = position_manager.should_close_on_candle_ttl(
                                position=position,
                                current_price=current_price,
                                entry_price=position_open_price,
                                position_type=pos_type,
                                timeframe="M15",
                                max_candles_without_profit=6
                            )
                            if should_close_ttl:
                                should_close = True
                                close_reason.append(ttl_reason)
                                logger.warning(f"🔴 {ttl_reason}")
                        except Exception as e:
                            logger.debug(f"Error checking TTL for {pos_symbol}: {e}")
                        
                        # ⚔️ REGLA C - EMA INVALIDATION
                        try:
                            ema_fast = analysis.get("technical", {}).get("data", {}).get("ema_fast", 0)
                            ema_slow = analysis.get("technical", {}).get("data", {}).get("ema_slow", 0)
                            should_close_ema, ema_reason = position_manager.should_close_on_ema_invalidation(
                                position_type=pos_type,
                                ema_fast=ema_fast,
                                ema_slow=ema_slow,
                                current_price=current_price
                            )
                            if should_close_ema:
                                should_close = True
                                close_reason.append(ema_reason)
                                logger.warning(f"🔴 {ema_reason}")
                        except Exception as e:
                            logger.debug(f"Error checking EMA invalidation for {pos_symbol}: {e}")
                        
                except Exception as e:
                    logger.warning(f"Error checking hard close rules for {pos_symbol}: {e}")
                
                # 3. Check time limit (don't hold scalp trades overnight)
                try:
                    should_close_time, time_reason = position_manager.should_close_on_time_limit(
                        position=position,
                        max_hold_minutes=240  # 4 hours for scalping
                    )
                    if should_close_time:
                        should_close = True
                        close_reason.append(time_reason)
                except Exception as e:
                    logger.warning(f"Error checking time limit for {pos_symbol}: {e}")
                
                # Cerrar si pérdida > 2% del capital
                if account_info and pos_profit < 0:
                    equity = account_info.get('equity', 1000)
                    loss_pct = abs(pos_profit / equity * 100)
                    if loss_pct > 2.0:
                        should_close = True
                        close_reason.append(f"Stop loss por pérdida: {loss_pct:.2f}% del capital")
                
                # Tomar ganancias si profit > 3% del capital
                if account_info and pos_profit > 0:
                    equity = account_info.get('equity', 1000)
                    profit_pct = pos_profit / equity * 100
                    if profit_pct > 3.0:
                        should_close = True
                        close_reason.append(f"Toma de ganancias: {profit_pct:.2f}% del capital")
                
                if should_close:
                    logger.info(f"Cerrando posición {pos_ticket}: {', '.join(close_reason)}")
                    analysis_logger.log_execution(
                        symbol=pos_symbol,
                        action=f"CLOSE {pos_type} {pos_volume} lots (ticket {pos_ticket})",
                        status="INFO",
                        details={"reason": close_reason, "profit": pos_profit}
                    )
                    success, error = execution.close_position(pos_ticket)
                    if success:
                        logger.info(f"✅ Posición {pos_ticket} cerrada exitosamente")
                        analysis_logger.log_execution(
                            symbol=pos_symbol,
                            action=f"Position closed: P&L=${pos_profit:.2f}",
                            status="SUCCESS",
                            details={"profit": pos_profit}
                        )
                        
                        # Update trade in database
                        try:
                            db = get_database_manager()
                            tick = mt5.symbol_info_tick(pos_symbol) or {}
                            bid = tick.get('bid') if isinstance(tick, dict) else getattr(tick, 'bid', None)
                            ask = tick.get('ask') if isinstance(tick, dict) else getattr(tick, 'ask', None)
                            close_price = ask if pos_type == 0 else bid
                            db.update_trade(pos_ticket, {
                                'close_price': close_price,
                                'close_timestamp': datetime.now().isoformat(),
                                'profit': pos_profit,
                                'status': 'closed'
                            })
                        except Exception as db_error:
                            logger.error(f"Error updating trade in database: {db_error}")
                    else:
                        logger.error(f"❌ Error cerrando posición {pos_ticket}: {error}")
                        analysis_logger.log_execution(
                            symbol=pos_symbol,
                            action=f"Failed to close position {pos_ticket}",
                            status="ERROR",
                            details={"error": error}
                        )
                else:
                    logger.info(f"Manteniendo posición {pos_ticket}: señal={current_signal}, P&L=${pos_profit:.2f}")
                    
            except Exception as e:
                logger.error(f"Error revisando posición: {e}", exc_info=True)
        
        # === STEP 2: EVALUATE NEW TRADE OPPORTUNITIES ===
        # 🎯 PRIORIDAD 3 - RANKING DE POSICIONES PARA CIERRE
        # Antes de buscar NUEVOS trades, cierra las PEORES posiciones
        try:
            open_positions = portfolio.get_open_positions()
            if open_positions and len(open_positions) > 0:
                ranked_worst = position_manager.rank_positions_for_closing(open_positions)
                
                # Intenta cerrar las 1-2 peores posiciones primero
                max_close_before_entry = min(2, len(ranked_worst) // 3)  # Close 1-2 worst if many open
                if len(open_positions) >= config.trading.default_max_positions * 0.8:
                    logger.warning(f"⚠️  Approaching max positions ({len(open_positions)}/{config.trading.default_max_positions})")
                    logger.info(f"🎯 Attempting to close {max_close_before_entry} worst positions first...")
                    
                    for i, worst_pos in enumerate(ranked_worst[:max_close_before_entry]):
                        try:
                            worst_symbol = worst_pos.get('symbol', '?')
                            worst_pnl = worst_pos.get('pnl', 0)
                            logger.info(f"   Closing worst #{i+1}: {worst_symbol} (P&L=${worst_pnl:.2f})")
                            # Execution happens in position review above, just log here
                        except:
                            pass
        except Exception as e:
            logger.debug(f"Error in position ranking: {e}")
        
        # Process each symbol
        for symbol in symbols:
            try:
                # Check if we already have a position
                if portfolio.has_position(symbol):
                    # Ya revisada arriba, skip para nuevos trades
                    continue
                
                # 🆕 CHECK ADAPTIVE PARAMETERS: Skip if symbol performance is too poor
                # This uses hourly-optimized parameters from adaptive_optimizer
                can_trade_symbol, param_reason = param_injector.should_trade_symbol(symbol)
                if not can_trade_symbol:
                    logger.info(f"⏭️  SKIPPED {symbol} (adaptive): {param_reason}")
                    continue  # Skip based on adaptive performance metrics
                
                # 🔧 FIX #1: EARLY POSITION LIMIT CHECK (before expensive analysis)
                # Fail fast if we're at max positions - no point analyzing further
                # ADAPTIVE: Use per-symbol max positions instead of global
                adaptive_max_positions = param_injector.get_max_positions_for_symbol(symbol)
                can_trade, trade_error = risk.can_open_new_trade(symbol)
                if not can_trade:
                    logger.info(f"⏭️  SKIPPED {symbol}: position limit check failed: {trade_error} (adaptive_max={adaptive_max_positions})")
                    continue  # Skip symbol entirely, don't waste CPU on analysis
                
                # 🔧 FIX #2: EXPOSURE CHECK (before expensive analysis)
                # Check if we already have too much exposure to this currency pair
                account_info = mt5.get_account_info()
                if account_info:
                    # Check if adding this would exceed currency pair exposure limits
                    base_currency = symbol[:3]  # EUR from EURUSD
                    existing_exposure = portfolio.get_exposure_by_currency(base_currency)
                    if existing_exposure and existing_exposure >= risk.max_trades_per_currency:
                        logger.info(f"⏭️  SKIPPED {symbol}: currency exposure limit reached for {base_currency}")
                        continue
                
                # 🔧 NOW: Do the expensive analysis (only if early checks passed)
                # === INTEGRATED ANALYSIS (Technical + Sentiment + Cache) ===
                analysis = integrated_analyzer.analyze_symbol(symbol, timeframe)
                
                # Save analysis to database for logs UI
                try:
                    db.save_analysis(analysis)
                except Exception as e:
                    logger.warning(f"Failed to save analysis to DB: {e}")
                
                # Log all available sources
                for source in analysis["available_sources"]:
                    if source == "TECHNICAL" and analysis["technical"]:
                        tech = analysis["technical"]
                        analysis_logger.log_technical_analysis(
                            symbol=symbol,
                            timeframe=timeframe,
                            signal=tech["signal"],
                            rsi=tech["data"].get("rsi") if tech["data"] else None,
                            ema_signal=tech["data"].get("ema_trend") if tech["data"] else None,
                            details=tech["data"] if tech["data"] else {}
                        )
                    elif source == "SENTIMENT" and analysis["sentiment"]:
                        sent = analysis["sentiment"]
                        analysis_logger.log_analysis(
                            symbol=symbol,
                            timeframe=timeframe,
                            analysis_type="SENTIMENT",
                            status="SUCCESS",
                            message=f"News Score: {sent.get('score', 0):.2f}",
                            details=sent
                        )
                
                # Use combined signal
                signal = analysis["signal"]
                if signal == "HOLD":
                    continue
                
                # 🌟 STEP 0: EARLY SPREAD CHECK (GATE 1 - before AI, scoring, sizing)
                tick = data.get_current_tick(symbol)
                if not tick:
                    logger.info(f"⏭️  SKIPPED {symbol}: no tick data for spread check")
                    log_skip_reason(symbol, "NO_TICK_DATA")
                    continue
                
                spread_pips = (tick.get('ask', 0) - tick.get('bid', 0)) * 10000 if symbol.endswith('USD') else (tick.get('ask', 0) - tick.get('bid', 0)) * 100
                is_forex = symbol.endswith('USD') or symbol.endswith('JPY') or symbol.endswith('GBP') or symbol.endswith('CHF') or symbol.endswith('CAD')
                max_spread = MAX_SPREAD_PIPS_FOREX if is_forex else MAX_SPREAD_PIPS_CRYPTO
                
                spread_ok = spread_pips <= max_spread
                if not spread_ok:
                    logger.info(f"⏭️  SKIPPED {symbol}: spread too high ({spread_pips:.1f} > {max_spread})")
                    log_skip_reason(symbol, "SPREAD_TOO_HIGH")
                    continue
                
                # Use combined signal
                signal = analysis["signal"]
                if signal == "HOLD":
                    continue
                
                # 🌟 STEP 1: Decide if should call AI (new optimization)
                should_call_ai_value, ai_optimization_reason = should_call_ai(
                    signal_direction=signal,
                    signal_strength=analysis.get("technical", {}).get("confidence", 0.0),
                    indicators=analysis["technical"]["data"] if analysis["technical"] else {}
                )
                
                needs_ai = should_call_ai_value
                ai_reason = ai_optimization_reason
                
                # Si NO necesita IA → crear decisión técnica pura (sin latencia)
                if not needs_ai:
                    logger.info(f"🚫 AI SKIP for {symbol}: {ai_reason}")
                    
                    tech_confidence = analysis.get("technical", {}).get("confidence", 0.0)
                    
                    # 🌟 STEP 2: Split signal direction from execution confidence
                    signal_analysis, execution_decision = split_decision(
                        signal_direction=signal,
                        signal_strength=tech_confidence,
                        technical_score=tech_confidence,
                        ai_score=0.0,  # Will update if we call AI
                        sentiment_score=analysis.get("sentiment", {}).get("score", 0.5) if analysis.get("sentiment") else 0.5
                    )
                    
                    # Check execution decision BEFORE creating TradingDecision
                    if not execution_decision.should_execute:
                        logger.info(f"⏭️  SKIPPED {symbol}: execution confidence too low ({execution_decision.execution_confidence:.2f} < {MIN_EXECUTION_CONFIDENCE})")
                        log_skip_reason(symbol, "CONFIDENCE_TOO_LOW")
                        continue
                    
                    # Crear decisión basada solo en señal técnica
                    decision = TradingDecision(
                        action=signal,
                        confidence=execution_decision.execution_confidence,
                        symbol=symbol,
                        timeframe=timeframe,
                        reason=[f"Technical-only: {ai_reason}"],
                        reasoning=f"AI not needed. {ai_reason}. Using strong technical signal.",
                        risk_ok=True,
                        market_bias="bullish" if signal == "BUY" else "bearish",
                        sources=analysis.get("available_sources", ["technical"]),
                    )
                    prompt_hash = None
                    decision_error = None
                    
                    # Log decisión técnica
                    analysis_logger.log_ai_analysis(
                        symbol=symbol,
                        timeframe=timeframe,
                        decision=signal,
                        confidence=execution_decision.execution_confidence,
                        reasoning=f"Tech-only (AI skipped): {ai_reason}"
                    )
                else:
                    # Zona gris detectada → consultar IA
                    logger.info(f"✅ AI CONSULT for {symbol}: {ai_reason}")
                    
                    # Get AI decision with integrated data (enhanced with dynamic risk adjustment)
                    from app.ai.dynamic_decision_engine import DynamicDecisionEngine
                    if isinstance(decision_engine, DynamicDecisionEngine):
                        # Use enhanced decision with per-ticker dynamic risk
                        decision, prompt_hash, decision_error = decision_engine.make_dynamic_decision(
                            symbol, timeframe, signal, tech_data
                        )
                    else:
                        # Fall back to standard decision
                        decision, prompt_hash, decision_error = decision_engine.make_decision(
                            symbol, timeframe, signal, tech_data
                        )
                
                # 🔁 FALLBACK INTELIGENTE: Solo aplica si se consultó IA y falló
                if needs_ai and (decision_error or not decision):
                    # Evaluar si la señal técnica es lo suficientemente fuerte para ejecutar sin IA
                    technical_score = analysis.get("technical", {}).get("confidence", 0.0)
                    
                    # Si tech_score >= 0.65, ejecutar el trade basado en señal técnica pura
                    if signal in ["BUY", "SELL"] and technical_score >= 0.65:
                        logger.warning(
                            f"AI failed for {symbol}, but technical score={technical_score:.2f} >= 0.65. "
                            f"Executing {signal} trade with TECH-ONLY decision."
                        )
                        analysis_logger.log_ai_analysis(
                            symbol=symbol,
                            timeframe=timeframe,
                            decision=signal,
                            confidence=technical_score,
                            status="WARNING",
                            reasoning=(
                                f"AI unavailable/failed, executing TECH-ONLY trade. "
                                f"Tech score={technical_score:.2f}. "
                                f"Sources: {', '.join(analysis['available_sources'])}"
                            ),
                        )
                        
                        # Crear decisión desde señal técnica (riesgo más conservador)
                        decision = TradingDecision(
                            action=signal,
                            confidence=technical_score * 0.95,  # Reducir ligeramente confianza sin IA
                            symbol=symbol,
                            timeframe=timeframe,
                            reason=[f"Technical-only execution. AI unavailable. Tech score={technical_score:.2f}"],
                            reasoning=f"AI failed; executing based on technical signal strength. Score={technical_score:.2f}",
                            risk_ok=True,
                            market_bias="neutral" if signal == "HOLD" else ("bullish" if signal == "BUY" else "bearish"),
                            sources=analysis.get("available_sources", ["technical"]),
                        )
                        prompt_hash = None
                    else:
                        # Técnica débil o sin señal → HOLD conservador
                        analysis_logger.log_ai_analysis(
                            symbol=symbol,
                            timeframe=timeframe,
                            decision="HOLD",
                            status="WARNING",
                            reasoning=(
                                f"IA unavailable/blocked, sin confirmación técnica fuerte. "
                                f"Tech score={technical_score:.2f} < 0.65. "
                                f"Sources: {', '.join(analysis['available_sources'])}"
                            ),
                        )
                        logger.warning(
                            f"AI unavailable for {symbol}, technical score={technical_score:.2f} < 0.65. "
                            f"Forcing conservative HOLD."
                        )

                        decision = TradingDecision(
                            action="HOLD",
                            confidence=0.0,
                            symbol=symbol,
                            timeframe=timeframe,
                            reason=["AI layer unavailable or blocked"],
                            reasoning="AI failed and technical score too weak; holding to avoid weak signals.",
                            risk_ok=False,
                            market_bias="neutral",
                            sources=["technical", "sentiment"],
                        )
                        prompt_hash = None
                else:
                    # IA consultada exitosamente - Log AI decision
                    if needs_ai:
                        confidence = decision.confidence if hasattr(decision, 'confidence') else None
                        reasoning = getattr(decision, 'reasoning', None) or '. '.join(getattr(decision, 'reason', []))
                        analysis_logger.log_ai_analysis(
                            symbol=symbol,
                            timeframe=timeframe,
                            decision=decision.action,
                            confidence=confidence,
                            reasoning=f"Análisis integrado ({', '.join(analysis['available_sources'])}): {reasoning}"
                        )
                
                # 🥇 SCALPING RULE: Technical signal is primary, AI is confirmatory
                # If we have a valid technical signal (BUY/SELL), always execute
                # Don't let AI block a valid technical trade
                if signal in ["BUY", "SELL"]:
                    # Recalculate execution decision with any AI score
                    tech_confidence = analysis.get("technical", {}).get("confidence", 0.0)
                    ai_score = getattr(decision, 'confidence', tech_confidence) if needs_ai else 0.0
                    
                    signal_analysis, execution_decision = split_decision(
                        signal_direction=signal,
                        signal_strength=tech_confidence,
                        technical_score=tech_confidence,
                        ai_score=ai_score,
                        sentiment_score=analysis.get("sentiment", {}).get("score", 0.5) if analysis.get("sentiment") else 0.5
                    )
                    
                    # Check confidence gate again with AI input
                    if not execution_decision.should_execute:
                        logger.info(f"⏭️  SKIPPED {symbol}: execution confidence too low after AI ({execution_decision.execution_confidence:.2f} < {MIN_EXECUTION_CONFIDENCE})")
                        log_skip_reason(symbol, "CONFIDENCE_TOO_LOW")
                        continue
                    
                    # Override AI decision if it conflicts with technical signal
                    if decision.action != signal:
                        logger.info(
                            f"🥇 SCALPING OVERRIDE: {symbol} "
                            f"technical={signal} "
                            f"vs AI={decision.action}. Using technical signal."
                        )
                        decision.action = signal
                        decision.confidence = execution_decision.execution_confidence
                    else:
                        # AI confirms technical → use AI confidence (already computed)
                        decision.confidence = execution_decision.execution_confidence
                        logger.info(f"🥇 AI CONFIRMS: {symbol} {decision.action} (confidence={execution_decision.execution_confidence:.2f})")

                
                # Check if decision is actionable
                if decision.action == "HOLD" or not decision.is_valid_for_execution():
                    logger.info(f"🔴 SKIPPED: {symbol} action={decision.action} valid_for_execution={decision.is_valid_for_execution()}")
                    continue
                
                logger.info(f"✅ DECISION OK: {symbol} {decision.action} - proceeding to validation gates")
                
                # 🌟 STEP 3: Run comprehensive validation gates (7 sequential gates)
                if decision.action in ["BUY", "SELL"]:
                    tick = data.get_current_tick(symbol)
                    if not tick:
                        logger.info(f"⏭️  SKIPPED {symbol}: no tick data for stop validation")
                        log_skip_reason(symbol, "NO_TICK_DATA")
                        continue

                    entry_price = tick.get('ask', 0) if decision.action == "BUY" else tick.get('bid', 0)
                    
                    # Get ATR from technical analysis data
                    atr_value = 0
                    if analysis["technical"] and analysis["technical"]["data"]:
                        atr_value = analysis["technical"]["data"].get("atr", 0)
                    
                    # Get broker info for validation
                    symbol_info = mt5.get_symbol_info(symbol)
                    broker_min_lot = symbol_info.get('volume_min', 0.01) if symbol_info else 0.01
                    broker_max_lot = symbol_info.get('volume_max', 100.0) if symbol_info else 100.0
                    tick_size = symbol_info.get('point', 0.0001) if symbol_info else 0.0001
                    
                    stop_distance = risk.get_default_stop_distance(entry_price, atr_value)
                    sl_price = decision.order.sl_price if decision.order and decision.order.sl_price else (
                        entry_price - stop_distance if decision.action == "BUY" else entry_price + stop_distance
                    )
                    tp_price = decision.order.tp_price if decision.order and decision.order.tp_price else (
                        entry_price + (stop_distance * 2) if decision.action == "BUY" else entry_price - (stop_distance * 2)
                    )
                    
                    # Get RSI for RSI gate
                    rsi_value = analysis["technical"]["data"].get("rsi", 50) if analysis["technical"] and analysis["technical"]["data"] else 50
                    
                    # Run all 7 validation gates
                    gates_ok, skip_reason, validated_volume = run_validation_gates(
                        symbol=symbol,
                        direction=decision.action,
                        entry_price=entry_price,
                        sl_price=sl_price,
                        tp_price=tp_price,
                        signal_strength=analysis.get("technical", {}).get("confidence", 0.0),
                        execution_confidence=decision.confidence,
                        rsi_value=rsi_value,
                        spread_pips=spread_pips,
                        computed_lot=0.01,  # Will be recalculated after gates pass
                        broker_min_lot=broker_min_lot,
                        broker_max_lot=broker_max_lot,
                        tick_size=tick_size,
                        portfolio=portfolio,
                        mt5_client=mt5,
                        account_balance=account_balance
                    )
                    
                    if not gates_ok:
                        logger.info(f"⏭️  SKIPPED {symbol}: validation gate failed - {skip_reason}")
                        log_skip_reason(symbol, skip_reason)
                        continue
                    
                    logger.info(f"✅ GATES OK: {symbol} entry={entry_price:.5f} SL={sl_price:.5f} TP={tp_price:.5f}")
                    
                    # � SELECT TRADING ENGINE (Scalping / Swing / Crypto)
                    from app.trading.trading_engines import get_engine_selector
                    engine_selector = get_engine_selector()
                    selected_engine = engine_selector.select_engine(symbol, timeframe)
                    
                    logger.info(f"🎯 SELECTED ENGINE: {selected_engine.name} for {symbol} ({timeframe})")
                    
                    # Engine validates trade (spread, volume limits)
                    engine_ok, engine_failures = selected_engine.validate_trade(symbol, decision.action, 0.01)
                    if not engine_ok:
                        logger.warning(f"🚫 {selected_engine.name} REJECTED: {symbol} - {engine_failures}")
                        continue
                    
                    # Use engine-specific parameters for stops
                    sl_multiplier = selected_engine.get_stop_loss_multiplier()
                    tp_multiplier = selected_engine.get_take_profit_multiplier()
                    engine_risk_pct = selected_engine.get_risk_percent()
                    
                    # 🆕 RISK PROFILE INTEGRATION
                    # Aplica parámetros del perfil actual de riesgo
                    try:
                        from app.trading.risk_profiles import get_risk_profile_manager
                        profile_mgr = get_risk_profile_manager()
                        current_profile = profile_mgr.get_current_profile()
                        
                        # El perfil puede ajustar los parámetros del engine
                        # Usa el MENOR de engine_risk y profile_risk (defensa asimétrica)
                        profile_risk_pct = current_profile.risk_per_trade
                        effective_risk_pct = min(engine_risk_pct, profile_risk_pct)
                        
                        # El perfil define max posiciones (hard limit)
                        max_positions_from_profile = current_profile.max_positions
                        
                        logger.info(
                            f"📊 RISK PROFILE: {current_profile.name} - "
                            f"risk={profile_risk_pct:.2f}%, max_pos={max_positions_from_profile}, "
                            f"SL={current_profile.atr_sl_mult:.1f}x ATR"
                        )
                    except Exception as e:
                        logger.debug(f"Risk profile not available: {e}, using engine defaults")
                        effective_risk_pct = engine_risk_pct
                        max_positions_from_profile = None
                    
                    # Recalculate stops with engine multipliers
                    stop_distance = atr_value * sl_multiplier if atr_value > 0 else risk.get_default_stop_distance(entry_price, atr_value)
                    sl_price = entry_price - stop_distance if decision.action == "BUY" else entry_price + stop_distance
                    tp_price = entry_price + (atr_value * tp_multiplier) if decision.action == "BUY" else entry_price - (atr_value * tp_multiplier)
                    
                    logger.info(f"🎯 ENGINE STOPS: SL={sl_multiplier}x ATR, TP={tp_multiplier}x ATR → SL={sl_price:.5f}, TP={tp_price:.5f}")
                    
                    # 🔧 FIX #4: SIZING (after all validation)
                    # Use effective risk percentage (min of engine and profile)
                    volume = decision.order.volume_lots if decision.order else 0.01
                    adaptive_risk_pct = max(effective_risk_pct, param_injector.get_max_risk_pct_for_symbol(symbol))
                    
                    # Temporarily override risk manager's max_trade_risk_pct for this trade
                    original_risk_pct = risk.max_trade_risk_pct
                    risk.max_trade_risk_pct = adaptive_risk_pct
                    volume = risk.cap_volume_by_risk(symbol, entry_price, sl_price, volume)
                    risk.max_trade_risk_pct = original_risk_pct  # Restore original
                    
                    # 🚫 ENGINE VOLUME CHECK: Skip if volume too low (NO CLAMP for scalping)
                    if selected_engine.should_skip_low_volume(symbol, volume):
                        logger.warning(f"🚫 {selected_engine.name} SKIP: {symbol} volume {volume:.4f} below threshold")
                        continue
                    
                    logger.info(f"📊 SIZING: {symbol} volume={volume:.4f} (engine_risk={engine_risk_pct:.2f}%, adaptive_risk={adaptive_risk_pct:.2f}%)")

                    # 🔧 FIX #5: RISK CHECKS (final pre-execution validation)
                    risk_ok, failures, volume = risk.check_all_risk_conditions(
                        symbol, decision.action, volume
                    )
                    
                    logger.info(f"🔴 RISK CHECK: {symbol} risk_ok={risk_ok} failures={failures} volume={volume}")
                    
                    # 🔧 FIX: failures is now Dict[str, str] with reason codes
                    failure_reasons = list(failures.values()) if isinstance(failures, dict) else failures
                    
                    # 🥇 SCALPING FIX: Only block if risk checks fail AND volume is below minimum
                    # Strong technical signal can override minor risk warnings if volume is viable
                    symbol_info = mt5.get_symbol_info(symbol)
                    min_volume = symbol_info.get('volume_min', 0.01) if symbol_info else 0.01
                    
                    # Check if this trade qualifies for scalping override
                    scalp_override = False
                    if not risk_ok:
                        # Check if volume is at least viable (>= min_volume)
                        if volume >= min_volume and signal in ["BUY", "SELL"] and analysis.get("technical", {}).get("confidence", 0) >= 0.65:
                            logger.warning(
                                f"🥇 SCALPING OVERRIDE: {symbol} minor risk warnings overridden by strong technical signal "
                                f"(failures: {list(failures.keys())}, but volume={volume} >= min={min_volume} and tech_conf=0.65+)"
                            )
                            # Allow execution anyway for scalping
                            scalp_override = True
                        else:
                            logger.info(f"🔴 SKIPPED: {symbol} risk checks failed: {failure_reasons}")
                            # Log risk check failures
                            for reason_code, reason_msg in failures.items():
                                analysis_logger.log_risk_check(
                                    symbol=symbol,
                                    check_name=reason_code,
                                    passed=False,
                                    reason=reason_msg
                                )
                            # Save decision audit
                            from app.core.state import DecisionAudit
                            audit = DecisionAudit(
                                timestamp=datetime.now().isoformat(),
                                symbol=symbol,
                                timeframe=timeframe,
                                signal=signal,
                                confidence=decision.confidence,
                                action="HOLD",
                                reason=decision.reason + [f"Risk check failed: {', '.join(failures)}"],
                                prompt_hash=prompt_hash,
                                gemini_response=decision.model_dump(),
                                risk_checks_passed=False,
                            )
                            state.save_decision(audit)
                            continue
                    
                    # If scalp_override is True, risk_ok is True, or both → proceed to execution
                    if not (scalp_override or risk_ok):
                        logger.info(f"🔴 SKIPPED: {symbol} risk checks failed and no scalp override")
                        continue
                    
                    # Log successful risk checks (or scalp override)
                    if scalp_override:
                        analysis_logger.log_risk_check(
                            symbol=symbol,
                            check_name="Scalping Override",
                            passed=True,
                            reason="Risk checks overridden by strong technical signal for scalping"
                        )
                    else:
                        analysis_logger.log_risk_check(
                            symbol=symbol,
                            check_name="All Risk Checks",
                            passed=True,
                            reason="Todas las comprobaciones de riesgo pasaron"
                        )
                    
                    # Ensure final volume passed to execution is capped post-risk
                    volume = risk.cap_volume_by_risk(symbol, entry_price, sl_price, volume)

                    # 🔴 CRITICAL DEBUG: Log before placing order
                    logger.info(
                        f"🔴 ABOUT TO EXECUTE ORDER:\n"
                        f"  Symbol: {symbol}\n"
                        f"  Action: {decision.action}\n"
                        f"  Volume: {volume} lots\n"
                        f"  Entry Price: {entry_price}\n"
                        f"  SL: {sl_price}\n"
                        f"  TP: {tp_price}\n"
                        f"  Confidence: {decision.confidence:.2f}\n"
                        f"  is_paper_mode: {config.is_paper_mode()}\n"
                    )

                    success, order_result, exec_error = execution.place_market_order(
                        symbol=symbol,
                        order_type=decision.action,
                        volume=volume,
                        sl_price=sl_price,
                        tp_price=tp_price,
                        comment=f"AI Bot - Confidence: {decision.confidence:.2f}",
                        atr=atr_value,
                    )
                    
                    # 🔴 CRITICAL DEBUG: Log execution result
                    logger.info(f"🔴 ORDER RESULT: success={success}, error={exec_error}, order_result={order_result}")
                    
                    # Log execution result
                    if success:
                        analysis_logger.log_execution(
                            symbol=symbol,
                            action=f"{decision.action} {volume} lots a {entry_price}",
                            status="SUCCESS",
                            details={
                                "volume": volume,
                                "entry_price": entry_price,
                                "sl_price": sl_price,
                                "tp_price": tp_price,
                                "order_result": str(order_result)
                            }
                        )
                        
                        # Save trade to database
                        try:
                            db = get_database_manager()
                            if order_result and isinstance(order_result, dict):
                                ticket = order_result.get('order', 0)
                                if ticket:
                                    db.save_trade({
                                        'ticket': ticket,
                                        'symbol': symbol,
                                        'trade_type': decision.action,
                                        'volume': volume,
                                        'open_price': entry_price,
                                        'stop_loss': sl_price,
                                        'take_profit': tp_price,
                                        'status': 'open',
                                        'comment': f"Confidence: {decision.confidence:.2f}"
                                    })
                        except Exception as db_error:
                            logger.error(f"Error saving trade to database: {db_error}")
                    else:
                        # Incluir detalles del error en el mensaje principal
                        error_msg = f"Execution: {decision.action} {volume} lots - ERROR: {exec_error}"
                        if order_result and 'retcode' in order_result:
                            error_msg += f" (retcode: {order_result['retcode']})"
                        
                        analysis_logger.log_execution(
                            symbol=symbol,
                            action=error_msg,
                            status="ERROR",
                            details={
                                "error": exec_error,
                                "order_result": str(order_result)
                            }
                        )
                    
                    # Save decision audit
                    audit = DecisionAudit(
                        timestamp=datetime.now().isoformat(),
                        symbol=symbol,
                        timeframe=timeframe,
                        signal=signal,
                        confidence=decision.confidence,
                        action=decision.action,
                        volume_lots=volume,
                        sl_price=sl_price,
                        tp_price=tp_price,
                        reason=decision.reason,
                        prompt_hash=prompt_hash,
                        gemini_response=decision.model_dump(),
                        risk_checks_passed=True,
                        execution_success=success,
                        error_message=exec_error,
                    )
                    state.save_decision(audit)
                    
                    if success:
                        logger.info(f"Order executed: {decision.action} {volume} lots of {symbol}")
                    else:
                        logger.error(f"Order execution failed: {exec_error}")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}", exc_info=True)
                continue
                
    except Exception as e:
        logger.error(f"Error in trading loop: {e}", exc_info=True)


def sidebar():
    """Render sidebar"""
    st.sidebar.title("🤖 AI Forex Trading Bot")
    
    # Connection status
    mt5 = get_mt5_client()
    config = get_config()
    state = get_state_manager()
    
    # Check if MT5 is available (import after mt5_client is loaded)
    try:
        # Import after the module is loaded to avoid circular issues
        import app.trading.mt5_client as mt5_module
        MT5_AVAILABLE = getattr(mt5_module, 'MT5_AVAILABLE', False)
    except (ImportError, AttributeError):
        MT5_AVAILABLE = False
    
    if mt5.is_connected():
        if MT5_AVAILABLE:
            st.sidebar.success("✅ MT5 Connected")
        else:
            st.sidebar.info("🔄 Demo Mode (MT5 not available)")
        account_info = mt5.get_account_info()
        if account_info:
            st.sidebar.metric("Equity", f"${account_info.get('equity', 0):,.2f}")
    else:
        if MT5_AVAILABLE:
            st.sidebar.error("❌ MT5 Disconnected")
            if st.sidebar.button("Connect to MT5"):
                with st.spinner("Connecting..."):
                    if mt5.connect():
                        st.rerun()
        else:
            st.sidebar.info("🔄 Demo Mode - Auto-connected")
    
    st.sidebar.divider()
    
    # Mode
    mode = config.trading.mode
    st.sidebar.markdown(f"**Mode:** {mode}")
    
    if mode == "LIVE":
        st.sidebar.warning("⚠️ LIVE MODE ACTIVE")
    
    st.sidebar.divider()
    
    # Kill switch
    st.sidebar.subheader("🛑 Kill Switch")
    if state.is_kill_switch_active():
        st.sidebar.error("**ACTIVE** - All trading stopped")
        if st.sidebar.button("Deactivate Kill Switch"):
            state.deactivate_kill_switch()
            st.rerun()
    else:
        st.sidebar.success("Inactive")
        if st.sidebar.button("Activate Kill Switch", type="primary"):
            state.activate_kill_switch()
            st.rerun()
    
    st.sidebar.divider()
    
    # Scheduler status
    scheduler = st.session_state.get("scheduler")
    if scheduler and scheduler.is_running():
        st.sidebar.success("🟢 Trading Loop Running")
        if st.sidebar.button("Stop Loop"):
            scheduler.stop()
            st.session_state.scheduler = None
            st.rerun()
    else:
        st.sidebar.info("⚪ Trading Loop Stopped")
        if st.sidebar.button("Start Loop"):
            scheduler = TradingScheduler(main_trading_loop)
            scheduler.start()
            st.session_state.scheduler = scheduler
            st.rerun()
    
    st.sidebar.divider()
    
    # Selected symbols
    st.sidebar.subheader("📊 Symbols")
    symbols = config.trading.default_symbols
    for symbol in symbols:
        st.sidebar.text(symbol)


def main():
    """Main Streamlit app"""
    sidebar()
    
    # Import the new integrated analysis page
    from app.ui.pages_integrated_analysis import render_integrated_analysis
    
    # Page selection
    page = st.selectbox(
        "Navigation",
        ["Dashboard", "Análisis Integrado", "Análisis en Tiempo Real", "Configuration", "Strategy", "Risk Management", "News", "Logs/Audit"],
        key="page_select"
    )
    
    st.title(f"📈 {page}")
    
    # Render selected page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Análisis Integrado":
        render_integrated_analysis()
    elif page == "Análisis en Tiempo Real":
        render_analysis_logs()
    elif page == "Configuration":
        render_config()
    elif page == "Strategy":
        render_strategy()
    elif page == "Risk Management":
        render_risk()
    elif page == "News":
        render_news()
    elif page == "Logs/Audit":
        render_logs()


if __name__ == "__main__":
    main()
