import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    
    # Alpha Vantage API
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
    
    # Forex pairs to track (using Alpha Vantage format: EURUSD, GBPUSD, etc.)
    FOREX_PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
    
    # Candle timeframes (Alpha Vantage intraday: 1min, 5min, 15min, 30min, 60min)
    TIMEFRAMES = {
        "1min": "1min",
        "5min": "5min",
        "15min": "15min",
        "60min": "60min",
        "daily": "daily"
    }
    
    # Technical Analysis Settings
    RSI_PERIOD = 14
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    EMA_SHORT = 9
    EMA_LONG = 21
    
    SMA_SHORT = 50
    SMA_LONG = 200
    
    ATR_PERIOD = 14
    
    # Signal Settings
    MIN_CONFLUENCE = 2  # Minimum signals needed for LONG/SHORT


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True


# Select config based on environment
config = DevelopmentConfig()