"""
Technical Analysis Service
Calculates trading indicators from price data
"""

import pandas as pd
import numpy as np
from typing import List
from app.models import Candle, TechnicalIndicators
from app.config import Config

class TechnicalAnalysis:
    """
    Calculates technical indicators from candle data
    Uses the `ta` library for accurate calculations
    """
    
    def __init__(self):
        print("TechnicalAnalysis initialized")
    
    def analyze(self, candles: List[Candle]) -> TechnicalIndicators:
        """
        Calculate all technical indicators for the latest candle
        
        Args:
            candles: List of Candle objects (at least 200 for moving averages)
        
        Returns:
            TechnicalIndicators object with all calculated values
        
        Example:
            >>> candles = fetcher.get_intraday_data("EURUSD", "60min")
            >>> indicators = analyzer.analyze(candles)
            >>> print(indicators.rsi, indicators.macd)
        """
        
        if not candles or len(candles) < 20:
            raise ValueError("Need at least 20 candles for analysis")
        
        try:
            # Convert candles to DataFrame for easier calculation
            df = self._candles_to_dataframe(candles)
            
            print(f"Analyzing {len(candles)} candles...")
            
            # Calculate all indicators
            rsi = self._calculate_rsi(df)
            macd, macd_signal, macd_histogram = self._calculate_macd(df)
            ema_short = self._calculate_ema(df, Config.EMA_SHORT)
            ema_long = self._calculate_ema(df, Config.EMA_LONG)
            sma_short = self._calculate_sma(df, Config.SMA_SHORT)
            sma_long = self._calculate_sma(df, Config.SMA_LONG)
            atr = self._calculate_atr(df)
            
            # Get the latest values (most recent candle)
            indicators = TechnicalIndicators(
                rsi=rsi[-1] if len(rsi) > 0 else None,
                macd=macd[-1] if len(macd) > 0 else None,
                macd_signal=macd_signal[-1] if len(macd_signal) > 0 else None,
                macd_histogram=macd_histogram[-1] if len(macd_histogram) > 0 else None,
                ema_short=ema_short[-1] if len(ema_short) > 0 else None,
                ema_long=ema_long[-1] if len(ema_long) > 0 else None,
                sma_short=sma_short[-1] if len(sma_short) > 0 else None,
                sma_long=sma_long[-1] if len(sma_long) > 0 else None,
                atr=atr[-1] if len(atr) > 0 else None
            )
            
            return indicators
            
        except Exception as e:
            print(f"Error analyzing candles: {e}")
            raise
    
    def _candles_to_dataframe(self, candles: List[Candle]) -> pd.DataFrame:
        """
        Convert Candle objects to pandas DataFrame
        
        This makes calculations easier using pandas built-in functions
        """
        data = {
            'open': [c.open for c in candles],
            'high': [c.high for c in candles],
            'low': [c.low for c in candles],
            'close': [c.close for c in candles],
            'volume': [c.volume for c in candles],
        }
        
        df = pd.DataFrame(data)
        return df
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = None) -> list:
        """
        Calculate Relative Strength Index (RSI)
        
        RSI measures momentum on a scale of 0-100
        - RSI > 70 = Overbought (potential sell)
        - RSI < 30 = Oversold (potential buy)
        
        Formula:
        1. Calculate price changes
        2. Average gains / Average losses
        3. RSI = 100 - (100 / (1 + RS))
        """
        
        if period is None:
            period = Config.RSI_PERIOD
        
        close = df['close']
        
        # Calculate price changes
        deltas = close.diff()
        
        # Separate gains and losses
        gains = deltas.copy()
        losses = deltas.copy()
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Calculate average gains and losses
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()
        
        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))
            rsi[np.isinf(rsi)] = 0  # Handle infinity values
        
        return rsi.fillna(0).tolist()
    
    def _calculate_macd(self, df: pd.DataFrame):
        """
        Calculate MACD (Moving Average Convergence Divergence)
        
        MACD tracks trend changes using exponential moving averages
        
        Components:
        - MACD line = 12-period EMA - 26-period EMA
        - Signal line = 9-period EMA of MACD line
        - Histogram = MACD - Signal
        
        Trading signals:
        - MACD crosses above signal = Bullish
        - MACD crosses below signal = Bearish
        """
        
        close = df['close']
        
        # Calculate EMAs
        ema_12 = close.ewm(span=Config.MACD_FAST, adjust=False).mean()
        ema_26 = close.ewm(span=Config.MACD_SLOW, adjust=False).mean()
        
        # MACD line
        macd_line = ema_12 - ema_26
        
        # Signal line (9-period EMA of MACD)
        signal_line = macd_line.ewm(span=Config.MACD_SIGNAL, adjust=False).mean()
        
        # Histogram
        histogram = macd_line - signal_line
        
        return (
            macd_line.fillna(0).tolist(),
            signal_line.fillna(0).tolist(),
            histogram.fillna(0).tolist()
        )
    
    def _calculate_ema(self, df: pd.DataFrame, period: int) -> list:
        """
        Calculate Exponential Moving Average (EMA)
        
        EMA gives more weight to recent prices
        Used for trend identification
        
        - EMA 9 = Short-term trend
        - EMA 21 = Medium-term trend
        
        Price above EMA = Uptrend
        Price below EMA = Downtrend
        """
        
        close = df['close']
        ema = close.ewm(span=period, adjust=False).mean()
        
        return ema.fillna(0).tolist()
    
    def _calculate_sma(self, df: pd.DataFrame, period: int) -> list:
        """
        Calculate Simple Moving Average (SMA)
        
        SMA is the average of prices over a period
        Used for identifying long-term trends
        
        - SMA 50 = Medium-term support/resistance
        - SMA 200 = Long-term trend (golden cross indicator)
        
        Price above SMA 200 = Long-term uptrend
        Price below SMA 200 = Long-term downtrend
        """
        
        close = df['close']
        sma = close.rolling(window=period).mean()
        
        return sma.fillna(0).tolist()
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = None) -> list:
        """
        Calculate Average True Range (ATR)
        
        ATR measures volatility - how much price swings
        Used for position sizing and setting stop losses
        
        Formula:
        True Range = max(high - low, abs(high - prev_close), abs(low - prev_close))
        ATR = Average of True Range over period
        """
        
        if period is None:
            period = Config.ATR_PERIOD
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR as average of True Range
        atr = tr.rolling(window=period).mean()
        
        return atr.fillna(0).tolist()


# Create global instance
analyzer = TechnicalAnalysis()