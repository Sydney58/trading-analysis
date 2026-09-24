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
    
    # Forex pairs to track
    FOREX_PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
    
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
    MIN_CONFLUENCE = 2
    
    # Risk Management
    DEFAULT_ACCOUNT_SIZE = 10000
    DEFAULT_RISK_PERCENTAGE = 2.0
    
    # ========== TRADING STYLES ==========
    TRADING_STYLES = {
        'scalping': {
            'name': 'Scalping',
            'description': 'Very short-term trades, tight stops, quick exits',
            'timeframes': ['1m', '5m'],
            'tp_multiplier': 1.0,
            'sl_multiplier': 0.5,
            'recommended_account_min': 1000,
        },
        'day_trading': {
            'name': 'Day Trading',
            'description': 'Trades within a single day',
            'timeframes': ['15m', '30m', '1h'],
            'tp_multiplier': 2.0,
            'sl_multiplier': 1.0,
            'recommended_account_min': 5000,
        },
        'swing_trading': {
            'name': 'Swing Trading',
            'description': 'Trades lasting days to weeks',
            'timeframes': ['1h', '4h'],
            'tp_multiplier': 3.0,
            'sl_multiplier': 1.5,
            'recommended_account_min': 10000,
        },
        'position_trading': {
            'name': 'Position Trading',
            'description': 'Long-term trades lasting weeks to months',
            'timeframes': ['4h', '1d', '1w'],
            'tp_multiplier': 4.0,
            'sl_multiplier': 2.0,
            'recommended_account_min': 25000,
        }
    }
    
    # ========== TRADINGVIEW TIMEFRAME MAPPING ==========
    TIMEFRAME_MAPPING = {
    '1m': '1m',      
    '5m': '5m',      
    '15m': '15m',    
    '30m': '30m',    
    '1h': '1h',      
    '4h': '4h',      
    '1d': '1d',      
    '1w': '1wk',     
    '1M': '1mo',     
    }
    
    # Reverse mapping for display
    TIMEFRAME_DISPLAY = {
        '1m': '1m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '60m',
        '4h': '240m',
        '1d': '1d',
        '1wk': '1w',
        '1mo': '1M',
    }


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