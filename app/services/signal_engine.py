"""
Signal Engine
Generates trading signals (LONG/SHORT/WAIT) based on technical indicator confluence
"""

from typing import List, Tuple
from datetime import datetime
from app.models import Candle, TechnicalIndicators, Signal
from app.config import Config

# Confidence lost for each indicator that disagrees with the chosen direction
OPPOSING_PENALTY = 0.20


class SignalEngine:
    """
    Generates trading signals by analyzing technical indicators

    Logic:
    - Analyzes multiple indicators (RSI, MACD, EMAs, SMAs)
    - Looks for CONFLUENCE (multiple indicators agreeing)
    - Disagreeing indicators reduce confidence
    - Ties (equal LONG and SHORT votes) produce WAIT
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
            symbol: Instrument (e.g., "EURUSD", "XAUUSD")
            timeframe: Timeframe (e.g., "1h")

        Returns:
            Signal object with type, confidence, and reasons
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
        RSI > 70 = Overbought (SHORT)
        RSI < 30 = Oversold (LONG)
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
        MACD > Signal = Bullish (LONG)
        MACD < Signal = Bearish (SHORT)
        MACD = Signal = Neutral (WAIT)
        """

        if macd is None or macd_signal is None:
            return "WAIT", ""

        diff = macd - macd_signal

        if diff > 0.00001:  # Small threshold for floating point
            return "LONG", "MACD bullish (MACD > Signal)"
        elif diff < -0.00001:
            return "SHORT", "MACD bearish (MACD < Signal)"
        else:
            return "WAIT", ""

    def _analyze_ema(self, price: float, ema_short: float, ema_long: float) -> Tuple[str, str]:
        """
        Price > EMA9 > EMA21 = Strong uptrend (LONG)
        Price < EMA9 < EMA21 = Strong downtrend (SHORT)
        Otherwise, the price's side of EMA9 decides
        """

        if price is None or ema_short is None or ema_long is None:
            return "WAIT", ""

        if price > ema_short and ema_short > ema_long:
            return "LONG", "Price above EMA9 > EMA21 (uptrend)"

        elif price < ema_short and ema_short < ema_long:
            return "SHORT", "Price below EMA9 < EMA21 (downtrend)"

        elif price > ema_short:
            return "LONG", "Price above EMA9 (bullish short-term)"

        elif price < ema_short:
            return "SHORT", "Price below EMA9 (bearish short-term)"

        else:
            return "WAIT", ""

    def _analyze_sma(self, price: float, sma_short: float, sma_long: float) -> Tuple[str, str]:
        """
        Price > SMA200 = Long-term uptrend (LONG)
        Price < SMA200 = Long-term downtrend (SHORT)
        """

        if price is None or sma_long is None:
            return "WAIT", ""

        if price > sma_long:
            return "LONG", "Price above SMA200 (long-term uptrend)"

        elif price < sma_long:
            return "SHORT", "Price below SMA200 (long-term downtrend)"

        else:
            return "WAIT", ""

    def _calculate_confluence(self, signals: List[str]) -> Tuple[str, float]:
        """
        Combine indicator votes into one direction and a confidence value.

        Base confidence from the majority side's agreement:
        - 3+ agree = 0.90
        - MIN_CONFLUENCE agree (default 2) = 0.70
        - 1 agrees = 0.50

        Each indicator voting the other way subtracts OPPOSING_PENALTY.
        A tie between LONG and SHORT (including no votes) is WAIT.

        NOTE: these base values are placeholders. Replace them with
        win rates measured in the backtest (calibration step).
        """

        if not signals:
            return "WAIT", 0.0

        long_count = signals.count("LONG")
        short_count = signals.count("SHORT")

        # Tie = indicators cancel out, so no trade
        if long_count == short_count:
            return "WAIT", 0.0

        direction = "LONG" if long_count > short_count else "SHORT"
        agree = max(long_count, short_count)
        oppose = min(long_count, short_count)

        if agree >= 3:
            base = 0.90
        elif agree >= Config.MIN_CONFLUENCE:
            base = 0.70
        else:
            base = 0.50

        confidence = max(0.0, base - OPPOSING_PENALTY * oppose)
        return direction, round(confidence, 2)


# Create global instance
engine = SignalEngine()