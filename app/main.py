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
from app.ui.pages_dashboard import render_dashboard
from app.ui.pages_config import render_config
from app.ui.pages_strategy import render_strategy
from app.ui.pages_risk import render_risk
from app.ui.pages_news import render_news
from app.ui.pages_logs import render_logs
from app.ui.pages_analysis import render_analysis_logs

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
        from app.ai.decision_engine import DecisionEngine
        from app.ai.schemas import TradingDecision, OrderDetails
        from datetime import datetime
        
        state = get_state_manager()
        mt5 = get_mt5_client()
        data = get_data_provider()
        strategy = get_strategy()
        risk = get_risk_manager()
        execution = get_execution_manager()
        portfolio = get_portfolio_manager()
        decision_engine = DecisionEngine()
        config = get_config()
        analysis_logger = get_analysis_logger()
        db = get_database_manager()  # Add database manager for saving analyses
        
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
        
        # Get symbols to trade (from config or UI state)
        symbols = config.trading.default_symbols
        timeframe = config.trading.default_timeframe
        
        # Get market status detector (for forex/crypto 24/7 handling)
        market_status = get_market_status()
        
        # Filter only open markets if we have symbol data
        tradeable_symbols = market_status.get_tradeable_symbols()
        if tradeable_symbols:
            symbols = [s for s in symbols if s in tradeable_symbols]
            if symbols:
                logger.info(f"Trading symbols (market open): {symbols}")
        
        # Get integrated analyzer (includes technical + sentiment)
        integrated_analyzer = get_integrated_analyzer()
        
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
                
                logger.info(f"Reviewing open position: {pos_symbol} {pos_type} {pos_volume} lots, ticket={pos_ticket}, P&L=${pos_profit:.2f}")
                
                # Get current analysis for position symbol
                pos_analysis = integrated_analyzer.analyze_symbol(pos_symbol, timeframe)
                current_signal = pos_analysis["signal"]
                
                # Save analysis to database for logs UI
                try:
                    db.save_analysis(pos_analysis)
                except Exception as e:
                    logger.warning(f"Failed to save position analysis to DB: {e}")
                
                # Decisión de cierre basada en señal contraria o baja confianza
                should_close = False
                close_reason = []
                
                if pos_type == 'BUY' and current_signal == 'SELL':
                    should_close = True
                    close_reason.append(f"Señal contraria detectada: posición BUY pero señal actual es SELL")
                elif pos_type == 'SELL' and current_signal == 'BUY':
                    should_close = True
                    close_reason.append(f"Señal contraria detectada: posición SELL pero señal actual es BUY")
                
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
                            db.update_trade(pos_ticket, {
                                'close_price': mt5.symbol_info_tick(pos_symbol).ask if pos_type == 0 else mt5.symbol_info_tick(pos_symbol).bid,
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
        # Process each symbol
        for symbol in symbols:
            try:
                # Check if we already have a position
                if portfolio.has_position(symbol):
                    # Ya revisada arriba, skip para nuevos trades
                    continue
                
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
                
                # Get AI decision with integrated data
                decision, prompt_hash, decision_error = decision_engine.make_decision(
                    symbol, timeframe, signal, analysis["technical"]["data"] if analysis["technical"] else {}
                )
                
                # Si la IA falla, bloquea nuevas entradas y devuelve HOLD neutral
                if decision_error or not decision:
                    analysis_logger.log_ai_analysis(
                        symbol=symbol,
                        timeframe=timeframe,
                        decision="HOLD",
                        status="WARNING",
                        reasoning=(
                            "IA no disponible/bloqueada, se fuerza HOLD. "
                            f"Sources: {', '.join(analysis['available_sources'])}"
                        ),
                    )
                    logger.warning(f"AI unavailable for {symbol}, forcing HOLD and skipping trade")

                    decision = TradingDecision(
                        action="HOLD",
                        confidence=0.0,
                        symbol=symbol,
                        timeframe=timeframe,
                        reason=["AI layer unavailable or blocked"],
                        reasoning="AI failed; holding to avoid trading sin confirmación.",
                        risk_ok=False,
                        market_bias="neutral",
                        sources=["technical", "sentiment"],
                    )
                    prompt_hash = None
                else:
                    # Log AI decision
                    confidence = decision.confidence if hasattr(decision, 'confidence') else None
                    reasoning = getattr(decision, 'reasoning', None) or '. '.join(getattr(decision, 'reason', []))
                    analysis_logger.log_ai_analysis(
                        symbol=symbol,
                        timeframe=timeframe,
                        decision=decision.action,
                        confidence=confidence,
                        reasoning=f"Análisis integrado ({', '.join(analysis['available_sources'])}): {reasoning}"
                    )
                
                # Check if decision is actionable (y respeta riesgo AI)
                if decision.action == "HOLD" or not decision.is_valid_for_execution():
                    continue
                
                # Run risk checks
                if decision.action in ["BUY", "SELL"]:
                    volume = decision.order.volume_lots if decision.order else 0.01

                    tick = data.get_current_tick(symbol)
                    if not tick:
                        continue

                    entry_price = tick.get('ask', 0) if decision.action == "BUY" else tick.get('bid', 0)
                    
                    # Get ATR from technical analysis data
                    atr_value = 0
                    if analysis["technical"] and analysis["technical"]["data"]:
                        atr_value = analysis["technical"]["data"].get("atr", 0)
                    
                    stop_distance = risk.get_default_stop_distance(entry_price, atr_value)
                    sl_price = decision.order.sl_price if decision.order and decision.order.sl_price else (
                        entry_price - stop_distance if decision.action == "BUY" else entry_price + stop_distance
                    )
                    tp_price = decision.order.tp_price if decision.order and decision.order.tp_price else (
                        entry_price + (stop_distance * 2) if decision.action == "BUY" else entry_price - (stop_distance * 2)
                    )
                    volume = risk.cap_volume_by_risk(symbol, entry_price, sl_price, volume)

                    risk_ok, failures = risk.check_all_risk_conditions(
                        symbol, decision.action, volume
                    )
                    
                    if not risk_ok:
                        logger.info(f"Risk checks failed for {symbol}: {failures}")
                        # Log risk check failures
                        for failure in failures:
                            analysis_logger.log_risk_check(
                                symbol=symbol,
                                check_name=failure,
                                passed=False,
                                reason="Condiciones de riesgo no cumplidas"
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
                    
                    # Log successful risk checks
                    analysis_logger.log_risk_check(
                        symbol=symbol,
                        check_name="All Risk Checks",
                        passed=True,
                        reason="Todas las comprobaciones de riesgo pasaron"
                    )
                    
                    success, order_result, exec_error = execution.place_market_order(
                        symbol=symbol,
                        order_type=decision.action,
                        volume=volume,
                        sl_price=sl_price,
                        tp_price=tp_price,
                        comment=f"AI Bot - Confidence: {decision.confidence:.2f}"
                    )
                    
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
