"""Configuration management using Pydantic Settings"""

from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class MT5Config(BaseSettings):
    """MetaTrader 5 connection configuration - OPTIONAL for cloud deployment"""
    
    login: Optional[int] = Field(None, alias="MT5_LOGIN")
    password: Optional[str] = Field(None, alias="MT5_PASSWORD")
    server: Optional[str] = Field(None, alias="MT5_SERVER")
    path: Optional[str] = Field(None, alias="MT5_PATH")
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class TradingConfig(BaseSettings):
    """Trading configuration"""
    
    mode: str = Field("LIVE", alias="MODE")
    timezone: str = Field("America/New_York", alias="TIMEZONE")
    polling_interval_seconds: int = Field(60, alias="POLLING_INTERVAL_SECONDS")  # Increased from 30s to 60s for stability
    
    # 🔧 EXPANDED: ALL 48 Forex + Crypto Pairs Available in MT5
    default_symbols: List[str] = [
        # === MAJOR FOREX PAIRS (7) ===
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD",
        
        # === CROSS PAIRS (32) ===
        "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDSGD", "CADCHF", "CADJPY",
        "CHFJPY", "CHFSGD", "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY",
        "EURNOK", "EURNZD", "EURPLN", "EURSEK", "EURSGD", "GBPAUD", "GBPCAD",
        "GBPCHF", "GBPJPY", "GBPSGD", "NZDCAD", "NZDCHF", "NZDJPY", "USDHKD",
        "USDMXN", "USDSGD", "USDTRY", "USDZAR",
        
        # === CRYPTO (9) ===
        "BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "XRPUSD", "ADAUSD", 
        "DOTUSD", "LTCUSD", "UNIUSD",
    ]
    
    default_timeframe: str = "M15"  # M15 scalping (balanced for 200 trades)
    
    # 🔧 ADAPTIVE SIZING: Risk adjusted to balance (see RiskManager.calculate_position_size_by_balance)
    default_risk_per_trade: float = Field(1.5, alias="DEFAULT_RISK_PER_TRADE")  # 1.5% per trade (MORE AGGRESSIVE)
    default_max_daily_loss: float = Field(10.0, alias="DEFAULT_MAX_DAILY_LOSS")  # 10% max daily loss (more aggressive)
    default_max_drawdown: float = Field(10.0, alias="DEFAULT_MAX_DRAWDOWN")  # 10% max drawdown
    default_max_positions: int = Field(200, alias="DEFAULT_MAX_POSITIONS")  # MAX 200 open trades
    
    # 🔧 Crypto-specific: ENABLED with adaptive sizing
    crypto_symbols: List[str] = [
        "BTCUSD", "ETHUSD", "BNBUSD", "SOLUSD", "XRPUSD", "ADAUSD", "DOTUSD", "LTCUSD", "DOGEUSD",
        "AVAXUSD", "POLKAUSD", "UNIUSD", "LINKUSD", "LUNAUSD", "MATICUSD",
        "ATOMUSD", "VETUSD", "FILUSD", "ARBUSD", "OPUSD", "GMXUSD",
    ]
    enable_crypto_trading: bool = Field(True, alias="ENABLE_CRYPTO_TRADING")
    
    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ["PAPER", "LIVE"]:
            raise ValueError("MODE must be 'PAPER' or 'LIVE'")
        return v_upper
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class AIConfig(BaseSettings):
    """AI/Gemini configuration - OPTIONAL for cloud deployment"""
    
    gemini_api_key: Optional[str] = Field(None, alias="GEMINI_API_KEY")
    gemini_model: str = Field("gemini-2.5-flash-lite", alias="GEMINI_MODEL")
    min_confidence_threshold: float = 0.25  # Optimized: lower threshold for more execution
    max_retries: int = 3
    timeout_seconds: int = 30
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class NewsConfig(BaseSettings):
    """News provider configuration"""
    
    news_api_key: Optional[str] = Field(None, alias="NEWS_API_KEY")
    cache_minutes: int = Field(15, alias="NEWS_CACHE_MINUTES")
    provider: str = "stub"  # stub, newsapi
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class LoggingConfig(BaseSettings):
    """Logging configuration"""
    
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_file: str = Field("logs/trading_bot.log", alias="LOG_FILE")
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class AppConfig:
    """Main application configuration aggregator"""
    
    def __init__(self):
        self.mt5 = MT5Config()
        self.trading = TradingConfig()
        self.ai = AIConfig()
        self.news = NewsConfig()
        self.logging = LoggingConfig()
        
        # Ensure logs directory exists
        log_dir = os.path.dirname(self.logging.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    def is_live_mode(self) -> bool:
        """Check if running in LIVE mode"""
        return self.trading.mode == "LIVE"
    
    def is_paper_mode(self) -> bool:
        """Check if running in PAPER mode"""
        return self.trading.mode == "PAPER"


# Global config instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """Reload configuration from environment"""
    global _config
    _config = AppConfig()
    return _config
