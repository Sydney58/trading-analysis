from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Candle:
    """Represents a forex price candle/bar"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    timeframe: str  # e.g., "1min", "5min", "15min", "60min"
    
    def __repr__(self):
        return f"Candle({self.symbol} {self.timeframe} {self.timestamp}: O={self.open} H={self.high} L={self.low} C={self.close})"


@dataclass
class TechnicalIndicators:
    """Technical analysis indicators for a candle"""
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    ema_short: Optional[float] = None
    ema_long: Optional[float] = None
    sma_short: Optional[float] = None
    sma_long: Optional[float] = None
    atr: Optional[float] = None
    
    def __repr__(self):
        return f"TechnicalIndicators(RSI={self.rsi}, MACD={self.macd}, EMA_S={self.ema_short}, SMA_S={self.sma_short})"


@dataclass
class Signal:
    """Trading signal generated from analysis"""
    symbol: str
    timeframe: str
    timestamp: datetime
    signal_type: str  # "LONG", "SHORT", "WAIT"
    confidence: float  # 0.0 to 1.0
    indicators: TechnicalIndicators
    reasons: list[str]  # Why this signal was generated
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    
    def __repr__(self):
        return f"Signal({self.symbol} {self.timeframe} {self.signal_type} @ {self.timestamp})"