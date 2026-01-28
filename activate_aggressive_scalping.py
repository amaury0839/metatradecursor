#!/usr/bin/env python3
"""
🚀 ACTIVACIÓN AGGRESSIVE_SCALPING - VERSIÓN INTEGRADA
Inicia el bot completo con AGGRESSIVE_SCALPING activado
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess
import time

# Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

sys.path.insert(0, str(Path(__file__).parent))

from app.core.logger import setup_logger
from app.trading.aggressive_scalping_integration import get_aggressive_scalping_engine
from app.trading.risk import get_trading_preset

logger = setup_logger("activation_manager")


def print_banner():
    """Print fancy banner"""
    banner = f"""
{BOLD}{CYAN}
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║     🚀 AGGRESSIVE_SCALPING - SISTEMA DE TRADING ACTIVADO 🚀    ║
    ║                                                                  ║
    ║  Trailing Stop Agresivo + Scale-Out Parcial + Hard Closes      ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
{RESET}
"""
    print(banner)


def check_prerequisites():
    """Verify all dependencies"""
    print(f"\n{CYAN}[*] Verificando prerequisitos...{RESET}")
    
    checks = {
        "Config": "app/core/config.py",
        "Logger": "app/core/logger.py",
        "MT5 Client": "app/trading/mt5_client.py",
        "Scalping Engine": "app/trading/exit_management_advanced.py",
        "Integration": "app/trading/aggressive_scalping_integration.py",
        "Main Bot": "app/main.py",
    }
    
    all_ok = True
    for name, path in checks.items():
        if Path(path).exists():
            print(f"  {GREEN}✓{RESET} {name:<20} OK")
        else:
            print(f"  {RED}✗{RESET} {name:<20} MISSING: {path}")
            all_ok = False
    
    return all_ok


def verify_scalping_engine():
    """Verify AGGRESSIVE_SCALPING engine loads correctly"""
    print(f"\n{CYAN}[*] Cargando AGGRESSIVE_SCALPING Engine...{RESET}")
    
    try:
        engine = get_aggressive_scalping_engine()
        preset = get_trading_preset("AGGRESSIVE_SCALPING")
        
        print(f"  {GREEN}✓{RESET} Engine cargado exitosamente")
        print(f"\n{BOLD}Preset AGGRESSIVE_SCALPING:{RESET}")
        print(f"  • Risk per trade:      {GREEN}{preset['risk_percent']}%{RESET}")
        print(f"  • Max positions:       {GREEN}{preset['max_concurrent_positions']}{RESET}")
        print(f"  • SL multiplier:       {GREEN}ATR × {preset['sl_atr_multiple']}{RESET}")
        print(f"  • TP multiplier:       {GREEN}ATR × {preset['tp_atr_multiple']}{RESET}")
        print(f"  • Trailing multiplier: {GREEN}ATR × {preset['trailing_atr_multiple']}{RESET}")
        print(f"  • IA Mode:             {GREEN}{preset['ai_mode']}{RESET}")
        print(f"  • AI blocks trades:    {GREEN}{not preset['ai_blocks_trade']}{RESET}")
        
        print(f"\n{BOLD}TP Levels:{RESET}")
        for tp_level in preset.get('tp_levels', []):
            print(f"  • Level {tp_level['level']}: {tp_level['multiple']}R → "
                  f"Close {tp_level['close_percent']*100:.0f}%"
                  f"{' (SL→BE)' if tp_level.get('move_sl_to_be') else ''}")
        
        return True
    except Exception as e:
        print(f"  {RED}✗{RESET} Error cargando engine: {e}")
        return False


def show_integration_summary():
    """Show what's been integrated"""
    print(f"\n{BOLD}Integraciones Completadas:{RESET}")
    
    integrations = [
        ("Scale-Out Management", "Cierre parcial en 3 niveles de TP"),
        ("Trailing Stop Dinámico", "SL sigue precio basado en ATR"),
        ("Hard Close RSI", "Cierre forzado en RSI > 85 o < 15"),
        ("Position Tracking", "% cerrado y estado en cada TP"),
        ("IA BIAS_ONLY", "IA sugiere pero no bloquea trades"),
        ("Main Bot Loop", "Integración en loop de revisión de posiciones"),
    ]
    
    for feature, description in integrations:
        print(f"  {GREEN}✓{RESET} {feature:<25} {YELLOW}{description}{RESET}")


def show_next_steps():
    """Show what's next"""
    print(f"\n{BOLD}Próximos Pasos:{RESET}")
    
    steps = [
        ("1. Backtesting", "python backtest_aggressive_scalping.py --symbols EURUSD,GBPUSD"),
        ("2. Testing en Demo", "python run_bot.py (asegúrate que está en DEMO mode)"),
        ("3. Monitoreo", "Abre dashboard: http://localhost:8501"),
        ("4. Live (Opcional)", "Cambia config a live mode y activa bot"),
    ]
    
    for step, cmd in steps:
        print(f"  {CYAN}{step:<20}{RESET}")
        print(f"     {YELLOW}{cmd}{RESET}")
        print()


def start_bot():
    """Start the bot"""
    print(f"\n{CYAN}[*] Iniciando Bot...{RESET}")
    
    try:
        # Check if we should start bot or just show commands
        response = input(f"\n¿Iniciar bot ahora? (s/n): ").lower()
        
        if response == 's':
            print(f"\n{YELLOW}Iniciando {BOLD}python run_bot.py{RESET}...\n")
            subprocess.run([sys.executable, "run_bot.py"])
        else:
            print(f"\n{GREEN}Bot no iniciado. Puedes hacerlo manualmente con:{RESET}")
            print(f"  {CYAN}python run_bot.py{RESET}")
            print(f"\nO para backtesting:")
            print(f"  {CYAN}python backtest_aggressive_scalping.py{RESET}")
    
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")


def main():
    """Main activation sequence"""
    
    print_banner()
    
    # 1. Check prerequisites
    if not check_prerequisites():
        print(f"\n{RED}❌ Faltan archivos críticos. Aborting.{RESET}")
        return False
    
    # 2. Verify engine
    if not verify_scalping_engine():
        print(f"\n{RED}❌ Engine no cargó correctamente. Aborting.{RESET}")
        return False
    
    # 3. Show integrations
    show_integration_summary()
    
    # 4. Show next steps
    show_next_steps()
    
    # 5. Offer to start bot
    start_bot()
    
    print(f"\n{BOLD}{GREEN}✅ ACTIVACIÓN COMPLETADA{RESET}")
    print(f"{CYAN}Status: AGGRESSIVE_SCALPING está integrado y listo{RESET}\n")
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Cancelado por usuario{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}Error fatal: {e}{RESET}")
        sys.exit(1)
