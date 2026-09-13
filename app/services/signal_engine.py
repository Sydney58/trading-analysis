"""
Signal Engine
Generates trading signals (BUY/SELL/WAIT) based on technical indicator confluence
"""

from typing import List, Tuple
from datetime import datetime
from app.models import Candle, TechnicalIndicators, Signal
from app.config import Config

class SignalEngine:
    """
    Generates trading signals by analyzing technical indicators
    
    Logic:
    - Analyzes multiple indicators (RSI, MACD, EMAs, SMAs)
    - Looks for CONFLUENCE (multiple indicators agreeing)
    - Calculates confidence score (0-100%)
    - Only generates signals when confidence is high
    - Explains WHY each signal was generated
    """
    
    def __init__(self):
        print("SignalEngine initialized")
    
    def generate_signal(
        self, 
        candles: List[Candle], 
        indicators: TechnicalIndicators,
        symbol: str,
        timeframe: str
    ) -> Signal:
        """
        Generate a trading signal based on technical indicators
        
        Args:
            candles: List of Candle objects (for context, latest is used)
            indicators: TechnicalIndicators object with calculated values
            symbol: Forex pair (e.g., "EURUSD")
            timeframe: Timeframe (e.g., "60min")
        
        Returns:
            Signal object with type, confidence, and reasons
        
        Example:
            >>> signal = engine.generate_signal(candles, indicators, "EURUSD", "60min")
            >>> print(signal.signal_type)  # "LONG", "SHORT", or "WAIT"
            >>> print(signal.confidence)   # 0.85 (85%)
            >>> print(signal.reasons)      # ["RSI oversold", "MACD bullish"]
        """
        
        if not candles:
            raise ValueError("Need at least one candle")
        
        latest_candle = candles[-1]
        
        print(f"Analyzing {symbol} {timeframe}...")
        
        # Analyze each indicator
        rsi_signal, rsi_reason = self._analyze_rsi(indicators.rsi)
        macd_signal, macd_reason = self._analyze_macd(indicators.macd, indicators.macd_signal)
        ema_signal, ema_reason = self._analyze_ema(latest_candle.close, indicators.ema_short, indicators.ema_long)
        sma_signal, sma_reason = self._analyze_sma(latest_candle.close, indicators.sma_short, indicators.sma_long)
        
        # Collect all signals and reasons
        all_signals = []
        all_reasons = []
        
        if rsi_signal != "WAIT":
            all_signals.append(rsi_signal)
            all_reasons.append(rsi_reason)
        
        if macd_signal != "WAIT":
            all_signals.append(macd_signal)
            all_reasons.append(macd_reason)
        
        if ema_signal != "WAIT":
            all_signals.append(ema_signal)
            all_reasons.append(ema_reason)
        
        if sma_signal != "WAIT":
            all_signals.append(sma_signal)
            all_reasons.append(sma_reason)
        
        # Calculate final signal and confidence
        final_signal, confidence = self._calculate_confluence(all_signals)
        
        # Create Signal object
        signal = Signal(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=datetime.now(),
            signal_type=final_signal,
            confidence=confidence,
            indicators=indicators,
            reasons=all_reasons,
            entry_price=latest_candle.close,
            stop_loss=None,  # Will be calculated by Risk Engine
            take_profit=None,  # Will be calculated by Risk Engine
            risk_reward_ratio=None  # Will be calculated by Risk Engine
        )
        
        return signal
    
    def _analyze_rsi(self, rsi: float) -> Tuple[str, str]:
        """
        Analyze RSI indicator
        
        RSI > 70 = Overbought (SELL signal)
        RSI < 30 = Oversold (BUY signal)
        30-70 = Neutral (WAIT)
        """
        
        if rsi is None:
            return "WAIT", ""
        
        if rsi > Config.RSI_OVERBOUGHT:  # > 70
            return "SHORT", f"RSI overbought ({rsi:.2f})"
        elif rsi < Config.RSI_OVERSOLD:  # < 30
            return "LONG", f"RSI oversold ({rsi:.2f})"
        else:
            return "WAIT", ""
    
    def _analyze_macd(self, macd: float, macd_signal: float) -> Tuple[str, str]:
        """
        Analyze MACD indicator
        
        MACD > Signal = Bullish (BUY signal)
        MACD < Signal = Bearish (SELL signal)
        MACD = Signal = Neutral (WAIT)
        """
        
        if macd is None or macd_signal is None:
            return "WAIT", ""
        
        diff = macd - macd_signal
        
        if diff > 0.00001:  # Small threshold for floating point
            return "LONG", f"MACD bullish (MACD > Signal)"
        elif diff < -0.00001:
            return "SHORT", f"MACD bearish (MACD < Signal)"
        else:
            return "WAIT", ""
    
    def _analyze_ema(self, price: float, ema_short: float, ema_long: float) -> Tuple[str, str]:
        """
        Analyze EMA trend
        
        Price > EMA9 > EMA21 = Strong uptrend (BUY)
        Price < EMA9 < EMA21 = Strong downtrend (SELL)
        Otherwise = WAIT
        """
        
        if price is None or ema_short is None or ema_long is None:
            return "WAIT", ""
        
        # Check if price is above both EMAs (uptrend)
        if price > ema_short and ema_short > ema_long:
            return "LONG", f"Price above EMA9 > EMA21 (uptrend)"
        
        # Check if price is below both EMAs (downtrend)
        elif price < ema_short and ema_short < ema_long:
            return "SHORT", f"Price below EMA9 < EMA21 (downtrend)"
        
        # Price above short-term EMA (bullish)
        elif price > ema_short:
            return "LONG", f"Price above EMA9 (bullish short-term)"
        
        # Price below short-term EMA (bearish)
        elif price < ema_short:
            return "SHORT", f"Price below EMA9 (bearish short-term)"
        
        else:
            return "WAIT", ""
    
    def _analyze_sma(self, price: float, sma_short: float, sma_long: float) -> Tuple[str, str]:
        """
        Analyze SMA long-term trend
        
        Price > SMA200 = Long-term uptrend (BUY bias)
        Price < SMA200 = Long-term downtrend (SELL bias)
        """
        
        if price is None or sma_long is None:
            return "WAIT", ""
        
        # Price above 200 SMA (strong uptrend)
        if price > sma_long:
            return "LONG", f"Price above SMA200 (long-term uptrend)"
        
        # Price below 200 SMA (strong downtrend)
        elif price < sma_long:
            return "SHORT", f"Price below SMA200 (long-term downtrend)"
        
        else:
            return "WAIT", ""
    
    def _calculate_confluence(self, signals: List[str]) -> Tuple[str, float]:
        """
        Calculate final signal based on confluence
        
        Confluence = How many indicators agree
        
        More indicators agreeing = Higher confidence
        
        Logic:
        - 3+ indicators say LONG = Strong BUY (90% confidence)
        - 2 indicators say LONG = Buy (70% confidence)
        - 1 indicator says LONG = Weak Buy (50% confidence)
        - Mixed signals = WAIT (0% confidence)
        """
        
        if not signals:
            return "WAIT", 0.0
        
        # Count LONG and SHORT signals
        long_count = signals.count("LONG")
        short_count = signals.count("SHORT")
        
        # Minimum confluence = 2 indicators agreeing (Config.MIN_CONFLUENCE)
        min_confluence = Config.MIN_CONFLUENCE
        
        # Strong LONG signal
        if long_count >= 3:
            confidence = 0.90  # 90% confidence
            return "LONG", confidence
        elif long_count >= min_confluence:
            confidence = 0.70  # 70% confidence
            return "LONG", confidence
        elif long_count == 1:
            confidence = 0.50  # 50% confidence
            return "LONG", confidence
        
        # Strong SHORT signal
        elif short_count >= 3:
            confidence = 0.90  # 90% confidence
            return "SHORT", confidence
        elif short_count >= min_confluence:
            confidence = 0.70  # 70% confidence
            return "SHORT", confidence
        elif short_count == 1:
            confidence = 0.50  # 50% confidence
            return "SHORT", confidence
        
        # Mixed or no signals
        else:
            return "WAIT", 0.0


# Create global instance
engine = SignalEngine()