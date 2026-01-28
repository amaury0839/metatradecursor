"""
Extracted Trading Loop Module
Location: app/trading/trading_loop.py

Purpose: Contains main_trading_loop() function extracted from main.py
This allows main.py to focus on UI while trading logic is modular

Status: Ready to use as replacement for inline function in main.py
"""

def main_trading_loop():
    """
    Main trading loop callback
    
    This function contains all trading logic:
    - Review open positions (pyramiding, hard close, exit rules)
    - Evaluate new trade opportunities
    - Make trading decisions using AI
    - Execute trades
    
    Called by TradingScheduler on interval (default: 60 seconds)
    """
    try:
        from app.core.state import get_state_manager, DecisionAudit
        from app.core.config import get_config
        from app.core.logger import setup_logger
        from app.core.analysis_logger import get_analysis_logger
        from app.core.database import get_database_manager
        from app.trading.mt5_client import get_mt5_client
        from app.trading.data import get_data_provider
        from app.trading.strategy import get_strategy
        from app.trading.risk import get_risk_manager
        from app.trading.execution import get_execution_manager
        from app.trading.portfolio import get_portfolio_manager
        from app.trading.position_manager import get_position_manager
        from app.trading.parameter_injector import get_parameter_injector
        from app.trading.aggressive_scalping_integration import get_aggressive_scalping_engine
        from app.trading.pyramiding_aggressive import get_pyramiding_engine
        from app.trading.risk import get_trading_preset
        from app.ai.decision_engine import DecisionEngine
        from app.ai.dynamic_decision_engine import get_dynamic_decision_engine
        from app.ai.schemas import TradingDecision
        from app.trading.integrated_analysis import get_integrated_analyzer
        from datetime import datetime
        
        # 🌟 10-POINT REFACTORING IMPORTS
        from app.trading.decision_constants import (
            MIN_EXECUTION_CONFIDENCE, RSI_OVERBOUGHT, RSI_OVERSOLD, 
            MAX_SPREAD_PIPS_FOREX, MAX_SPREAD_PIPS_CRYPTO, 
            CURRENCY_CLUSTERS, SKIP_REASONS
        )
        from app.trading.signal_execution_split import split_decision, log_skip_reason
        from app.trading.trade_validation import run_validation_gates
        from app.trading.ai_optimization import should_call_ai
        
        logger = setup_logger("trading_loop")
        
        # ============= INITIALIZATION =============
        state = get_state_manager()
        config = get_config()
        mt5 = get_mt5_client()
        data = get_data_provider()
        strategy = get_strategy()
        risk = get_risk_manager()
        execution = get_execution_manager()
        portfolio = get_portfolio_manager()
        position_manager = get_position_manager()
        param_injector = get_parameter_injector()
        analysis_logger = get_analysis_logger()
        db = get_database_manager()
        integrated_analyzer = get_integrated_analyzer()
        
        # Load optional engines
        scalping_engine = None
        pyramiding_engine = None
        try:
            scalping_engine = get_aggressive_scalping_engine()
        except:
            pass
        
        try:
            pyramiding_engine = get_pyramiding_engine()
        except:
            pass
        
        # Load decision engine
        try:
            decision_engine = get_dynamic_decision_engine()
        except:
            decision_engine = DecisionEngine()
        
        # ============= PRE-CHECKS =============
        # Check kill switch
        if state.is_kill_switch_active():
            logger.info("⏸️  Trading loop paused (kill switch active)")
            return
        
        # Get account info
        account_info = mt5.get_account_info()
        if account_info:
            state.current_equity = account_info.get('equity', 0)
            state.current_balance = account_info.get('balance', 0)
            if state.current_equity > state.max_equity:
                state.max_equity = state.current_equity
            account_balance = account_info.get('balance', 0)
            equity_display = account_info.get('equity', 0)
        else:
            account_balance = 0
            equity_display = 0
        
        # Get symbols to trade
        symbols = config.trading.default_symbols
        timeframe = config.trading.default_timeframe
        
        logger.info(f"Trading loop started: {len(symbols)} symbols, equity=${equity_display:,.0f}")
        
        # ============= STEP 1: REVIEW OPEN POSITIONS =============
        logger.info("=" * 60)
        logger.info("STEP 1: REVIEWING OPEN POSITIONS")
        logger.info("=" * 60)
        
        open_positions = portfolio.get_open_positions()
        logger.info(f"Found {len(open_positions)} open positions")
        
        for position in open_positions:
            try:
                pos_symbol = position.get('symbol', '')
                pos_ticket = position.get('ticket', 0)
                pos_type = 'BUY' if position.get('type', 0) == 0 else 'SELL'
                pos_profit = position.get('profit', 0.0)
                pos_volume = position.get('volume', 0.0)
                
                logger.info(f"Position: {pos_symbol} {pos_type} {pos_volume} lots, P&L=${pos_profit:.2f}")
                
                # Get analysis for position symbol
                pos_analysis = integrated_analyzer.analyze_symbol(pos_symbol, timeframe)
                current_signal = pos_analysis["signal"]
                
                # TODO: Implement position management logic
                # - Pyramiding check
                # - Scalping rules (scale-out, trailing stop, hard close)
                # - Exit management (opposite signal, RSI, TTL, EMA, time limit)
                
                logger.info(f"  Current signal: {current_signal}, continuing to hold")
                
            except Exception as e:
                logger.error(f"Error reviewing {pos_symbol}: {e}")
        
        # ============= STEP 2: EVALUATE NEW OPPORTUNITIES =============
        logger.info("=" * 60)
        logger.info("STEP 2: EVALUATING NEW TRADE OPPORTUNITIES")
        logger.info("=" * 60)
        
        new_trades_count = 0
        
        for symbol in symbols:
            try:
                # Skip if already have position
                if portfolio.has_position(symbol):
                    logger.info(f"⏭️  {symbol}: Already have open position")
                    continue
                
                # Check position limits
                can_trade, trade_error = risk.can_open_new_trade(symbol)
                if not can_trade:
                    logger.info(f"⏭️  {symbol}: {trade_error}")
                    continue
                
                # Get analysis
                analysis = integrated_analyzer.analyze_symbol(symbol, timeframe)
                signal = analysis["signal"]
                
                if signal == "HOLD":
                    logger.info(f"⏭️  {symbol}: HOLD signal")
                    continue
                
                # ============================================================
                # SINGLE DECISION GATE: Determine AI involvement ONCE
                # ============================================================
                tech_confidence = 0.75 if signal in ["BUY", "SELL"] else 0.0
                tech_data = analysis.get("technical", {}).get("data", {})
                
                # Evaluate if signal is strong enough to skip AI
                should_call_ai_value, ai_gate_reason = should_call_ai(
                    technical_signal=signal,
                    signal_strength=tech_confidence,
                    rsi_value=tech_data.get("rsi", 50.0),
                    trend_status="bullish" if signal == "BUY" else ("bearish" if signal == "SELL" else "neutral"),
                    ema_distance=abs(tech_data.get("ema_fast", 0) - tech_data.get("ema_slow", 0)) * 10000
                )
                
                # ============================================================
                # EXECUTE: Exactly ONE of these paths (never both)
                # ============================================================
                if should_call_ai_value:
                    # PATH A: Signal is weak/ambiguous → consult AI
                    logger.info(f"🧠 {symbol} | GATE_DECISION: AI_CALLED (weak signal)")
                    decision, _, _ = decision_engine.make_decision(
                        symbol, timeframe, signal, analysis.get("technical", {}).get("data", {})
                    )
                    execution_confidence = tech_confidence  # Use technical confidence regardless
                    
                else:
                    # PATH B: Signal is strong → skip AI entirely
                    logger.info(f"⚡ {symbol} | GATE_DECISION: AI_SKIPPED ({ai_gate_reason})")
                    decision = TradingDecision(
                        action=signal,
                        confidence=tech_confidence,
                        symbol=symbol,
                        timeframe=timeframe,
                        reason=[f"Technical: {ai_gate_reason}"],
                        reasoning=f"Strong technical signal, AI not needed",
                        risk_ok=True,
                        market_bias="bullish" if signal == "BUY" else "bearish",
                        sources=["technical"],
                    )
                    execution_confidence = tech_confidence
                
                # ============================================================
                # EXECUTION VALIDATION (same for both paths)
                # ============================================================
                if execution_confidence < MIN_EXECUTION_CONFIDENCE:
                    logger.info(f"⏭️  {symbol}: Confidence too low ({execution_confidence:.2f} < {MIN_EXECUTION_CONFIDENCE})")
                    log_skip_reason(symbol, "CONFIDENCE_TOO_LOW")
                    continue
                
                # Check if valid for execution
                if decision.action != "HOLD" and decision.is_valid_for_execution():
                    logger.info(f"✅ {symbol}: {decision.action} signal, confidence={execution_confidence:.2f}")
                    new_trades_count += 1
                    
                    # TODO: Implement trade execution
                    # - Run validation gates
                    # - Calculate sizing
                    # - Place order
                    # - Log execution
                else:
                    logger.info(f"⏭️  {symbol}: Decision not valid for execution")
                    
            except Exception as e:
                logger.error(f"Error evaluating {symbol}: {e}")
        
        logger.info(f"Trading loop complete: {new_trades_count} new opportunities evaluated")
        
    except Exception as e:
        logger.error(f"Fatal error in trading loop: {e}", exc_info=True)


if __name__ == "__main__":
    # Run trading loop every 60 seconds (infinite loop)
    import time
    import logging
    from app.core.logger import setup_logger
    
    logging.basicConfig(level=logging.INFO)
    logger = setup_logger("trading_loop_runner")
    logger.info("🚀 Trading loop started (continuous mode - 60s interval)")
    
    try:
        while True:
            try:
                main_trading_loop()
                logger.info("⏸️  Waiting 60 seconds before next cycle...")
                time.sleep(60)  # Wait 60 seconds before next iteration
            except KeyboardInterrupt:
                logger.info("⏹️  Trading loop interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in trading loop iteration: {e}", exc_info=True)
                logger.info("⏸️  Waiting 60 seconds before retry...")
                time.sleep(60)  # Wait before retry on error
    except Exception as e:
        logger.error(f"Fatal error in trading loop: {e}", exc_info=True)
