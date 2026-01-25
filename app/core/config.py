"""Configuration management using Pydantic Settings"""

from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class MT5Config(BaseSettings):
    """MetaTrader 5 connection configuration"""
    
    login: int = Field(..., alias="MT5_LOGIN")
    password: str = Field(..., alias="MT5_PASSWORD")
    server: str = Field(..., alias="MT5_SERVER")
    path: Optional[str] = Field(None, alias="MT5_PATH")
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class TradingConfig(BaseSettings):
    """Trading configuration"""
    
    mode: str = Field("PAPER", alias="MODE")
    timezone: str = Field("America/New_York", alias="TIMEZONE")
    polling_interval_seconds: int = Field(30, alias="POLLING_INTERVAL_SECONDS")
    
    # Default symbols
    default_symbols: List[str] = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
    default_timeframe: str = "M15"
    
    # Risk defaults
    default_risk_per_trade: float = Field(0.5, alias="DEFAULT_RISK_PER_TRADE")
    default_max_daily_loss: float = Field(2.0, alias="DEFAULT_MAX_DAILY_LOSS")
    default_max_drawdown: float = Field(8.0, alias="DEFAULT_MAX_DRAWDOWN")
    default_max_positions: int = Field(2, alias="DEFAULT_MAX_POSITIONS")
    
    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ["PAPER", "LIVE"]:
            raise ValueError("MODE must be 'PAPER' or 'LIVE'")
        return v_upper
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class AIConfig(BaseSettings):
    """AI/Gemini configuration"""
    
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    min_confidence_threshold: float = 0.62
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
