"""Prompt templates for Gemini AI decision making"""

from typing import Dict, Any, List, Optional


def build_system_prompt() -> str:
    """Build system prompt for Gemini"""
    return """You are an expert quantitative trading assistant for Forex and Crypto markets. Your role is to analyze market conditions, technical indicators, news sentiment, and risk constraints to make ACTIVE trading decisions.

CRITICAL RULES:
1. You MUST respond ONLY with valid JSON matching the exact schema provided
2. If risk_ok is false, you MUST return action="HOLD" regardless of signals
3. Never suggest positions that exceed risk limits
4. Confidence must be between 0.0 and 1.0
5. BE AGGRESSIVE: If confidence >= 0.30 and signals align, take the trade (BUY/SELL)
6. Always provide clear reasoning in the 'reason' array

Your decisions should be OPPORTUNISTIC and ACTION-ORIENTED. Look for trading opportunities actively. Take calculated risks when technical signals and sentiment align."""


def build_user_prompt(
    symbol: str,
    timeframe: str,
    market_snapshot: Dict[str, Any],
    account_state: Dict[str, Any],
    technical_signal: str,
    indicators: Dict[str, Any],
    news_sentiment: Optional[Dict[str, Any]] = None,
    risk_constraints: Optional[Dict[str, Any]] = None,
    current_positions: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Build user prompt with market context
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe
        market_snapshot: OHLC and price data
        account_state: Account equity, balance, etc.
        technical_signal: Base technical signal (BUY/SELL/HOLD)
        indicators: Technical indicators (EMA, RSI, ATR, etc.)
        news_sentiment: News sentiment data (optional)
        risk_constraints: Risk limits and constraints
        current_positions: Current open positions
    
    Returns:
        Formatted prompt string
    """
    prompt_parts = [
        f"# Trading Decision Request",
        f"",
        f"## Symbol: {symbol} ({timeframe})",
        f"",
        f"## Market Snapshot:",
        f"- Current Price: {market_snapshot.get('current_price', 'N/A')}",
        f"- Spread: {market_snapshot.get('spread_pips', 'N/A')} pips",
        f"- Volatility (ATR): {market_snapshot.get('atr', 'N/A')}",
        f"",
        f"## Technical Indicators:",
        f"- EMA Fast (20): {indicators.get('ema_fast', 'N/A')}",
        f"- EMA Slow (50): {indicators.get('ema_slow', 'N/A')}",
        f"- Trend: {'Bullish' if indicators.get('trend_bullish') else 'Bearish' if indicators.get('trend_bearish') else 'Neutral'}",
        f"- RSI: {indicators.get('rsi', 'N/A'):.2f}",
        f"- ATR: {indicators.get('atr', 'N/A')}",
        f"- Base Technical Signal: {technical_signal}",
        f"",
        f"## Account State:",
        f"- Equity: {account_state.get('equity', 0):.2f}",
        f"- Balance: {account_state.get('balance', 0):.2f}",
        f"- Open Positions: {account_state.get('open_positions_count', 0)}",
        f"- Unrealized PnL: {account_state.get('unrealized_pnl', 0):.2f}",
    ]
    
    if news_sentiment:
        prompt_parts.extend([
            f"",
            f"## News Sentiment:",
            f"- Score: {news_sentiment.get('score', 0):.2f} (range: -1 to +1)",
            f"- Summary: {news_sentiment.get('summary', 'N/A')}",
            f"- Headlines: {', '.join(news_sentiment.get('headlines', [])[:3])}",
        ])
    
    if risk_constraints:
        prompt_parts.extend([
            f"",
            f"## Risk Constraints:",
            f"- Max Risk per Trade: {risk_constraints.get('risk_per_trade_pct', 0):.2f}%",
            f"- Max Daily Loss: {risk_constraints.get('max_daily_loss_pct', 0):.2f}%",
            f"- Max Drawdown: {risk_constraints.get('max_drawdown_pct', 0):.2f}%",
            f"- Max Positions: {risk_constraints.get('max_positions', 0)}",
            f"- Max Spread: {risk_constraints.get('max_spread_pips', 0):.2f} pips",
        ])
    
    if current_positions:
        prompt_parts.extend([
            f"",
            f"## Current Positions:",
        ])
        for pos in current_positions[:5]:  # Limit to 5 positions
            prompt_parts.append(
                f"- {pos.get('symbol', 'N/A')}: {pos.get('type', 'N/A')} "
                f"{pos.get('volume', 0)} lots, PnL: {pos.get('profit', 0):.2f}"
            )
    
    prompt_parts.extend([
        f"",
        f"## Decision Schema:",
        f"Respond with JSON matching this exact structure:",
        f"{{",
        f'  "action": "BUY" | "SELL" | "HOLD" | "CLOSE",',
        f'  "confidence": 0.0-1.0,',
        f'  "symbol": "{symbol}",',
        f'  "timeframe": "{timeframe}",',
        f'  "reason": ["reason1", "reason2", ...],',
        f'  "risk_ok": true | false,',
        f'  "order": {{',
        f'    "type": "MARKET",',
        f'    "volume_lots": 0.01-100.0,',
        f'    "sl_price": number | null,',
        f'    "tp_price": number | null',
        f'  }},',
        f'  "constraints_used": {{',
        f'    "max_risk_per_trade": number | null,',
        f'    "max_positions": number | null,',
        f'    "max_drawdown": number | null',
        f'  }}',
        f"}}",
        f"",
        f"IMPORTANT:",
        f"- If risk_ok is false, return action='HOLD'",
        f"- If confidence >= 0.30 and signals align, TAKE THE TRADE",
        f"- Only return BUY/SELL if all risk checks pass",
        f"- BE AGGRESSIVE: Look for opportunities, not reasons to avoid them",
        f"- Provide specific, actionable reasons",
    ])
    
    return "\n".join(prompt_parts)
