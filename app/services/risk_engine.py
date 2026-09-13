"""
Risk Engine
Calculates proper entry, stop loss, take profit, and position sizing
Makes trading signals actually tradeable!
"""

from typing import List, Optional
from app.models import Candle, Signal
from app.config import Config

class RiskEngine:
    """
    Manages risk for each trading signal
    
    Calculates:
    - Entry price (where to buy/sell)
    - Stop loss (where to exit if wrong)
    - Take profit (where to exit if right)
    - Risk:Reward ratio (is the trade worth it?)
    - Position size (how much to risk)
    
    Key principle: NEVER risk more than you're willing to lose!
    """
    
    def __init__(self, account_balance: float = 10000):
        """
        Initialize Risk Engine
        
        Args:
            account_balance: Your trading account size (default: $10,000)
        """
        self.account_balance = account_balance
        self.risk_per_trade = 0.02  # Risk 2% per trade (conservative)
        print(f"RiskEngine initialized (Account: ${account_balance:,.2f})")
    
    def calculate_risk(self, signal: Signal, candles: List[Candle], atr: float) -> Signal:
        """
        Calculate risk management levels for a signal
        
        Args:
            signal: Signal object from SignalEngine
            candles: List of Candle objects (for price history)
            atr: Average True Range (volatility measure)
        
        Returns:
            Updated Signal with entry, stop_loss, take_profit, risk_reward_ratio
        
        Example:
            >>> signal = engine.generate_signal(candles, indicators, "EURUSD", "60min")
            >>> signal = risk_engine.calculate_risk(signal, candles, indicators.atr)
            >>> print(signal.entry_price)
            >>> print(signal.stop_loss)
            >>> print(signal.take_profit)
        """
        
        if not candles or not signal:
            raise ValueError("Need signal and candles")
        
        print(f"Calculating risk for {signal.signal_type} signal...")
        
        latest_candle = candles[-1]
        
        # Get recent price history (last 20 candles for support/resistance)
        recent_candles = candles[-20:] if len(candles) >= 20 else candles
        
        # Calculate entry, stop loss, and take profit based on signal type
        if signal.signal_type == "LONG":
            entry, stop_loss, take_profit = self._calculate_long_levels(
                latest_candle, recent_candles, atr
            )
        elif signal.signal_type == "SHORT":
            entry, stop_loss, take_profit = self._calculate_short_levels(
                latest_candle, recent_candles, atr
            )
        else:  # WAIT signal
            return signal
        
        # Calculate risk and reward
        if signal.signal_type == "LONG":
            risk = entry - stop_loss  # How much below entry we'll exit
            reward = take_profit - entry  # How much above entry we profit
        else:  # SHORT
            risk = stop_loss - entry  # How much above entry we'll exit
            reward = entry - take_profit  # How much below entry we profit
        
        # Calculate risk:reward ratio
        if risk > 0:
            risk_reward_ratio = reward / risk
        else:
            risk_reward_ratio = 0
        
        # Update signal with risk management levels
        signal.entry_price = entry
        signal.stop_loss = stop_loss
        signal.take_profit = take_profit
        signal.risk_reward_ratio = risk_reward_ratio
        
        return signal
    
    def _calculate_long_levels(self, latest_candle: Candle, recent_candles: List[Candle], atr: float):
        """
        Calculate entry, stop, and take profit for LONG trades
        
        Logic:
        - Entry: Current price (or slightly below for better fill)
        - Stop Loss: Below recent low or 2x ATR below entry (whichever is lower)
        - Take Profit: Entry + 2x Risk (good risk:reward)
        """
        
        # Entry: Current price
        entry = latest_candle.close
        
        # Stop Loss: Find lowest low in recent candles
        recent_lows = [c.low for c in recent_candles]
        recent_low = min(recent_lows)
        
        # Stop loss: recent low - ATR buffer (add some room)
        stop_loss = recent_low - (atr * 0.5)
        
        # Make sure stop loss isn't too close to entry (at least 1 ATR below)
        min_stop = entry - (atr * 1.0)
        if stop_loss > min_stop:
            stop_loss = min_stop
        
        # Take profit: Risk x 2 (for 1:2 risk:reward)
        risk = entry - stop_loss
        take_profit = entry + (risk * 2.0)
        
        return entry, stop_loss, take_profit
    
    def _calculate_short_levels(self, latest_candle: Candle, recent_candles: List[Candle], atr: float):
        """
        Calculate entry, stop, and take profit for SHORT trades
        
        Logic:
        - Entry: Current price (or slightly above for better fill)
        - Stop Loss: Above recent high or 2x ATR above entry (whichever is higher)
        - Take Profit: Entry - 2x Risk (good risk:reward)
        """
        
        # Entry: Current price
        entry = latest_candle.close
        
        # Stop Loss: Find highest high in recent candles
        recent_highs = [c.high for c in recent_candles]
        recent_high = max(recent_highs)
        
        # Stop loss: recent high + ATR buffer
        stop_loss = recent_high + (atr * 0.5)
        
        # Make sure stop loss isn't too close to entry (at least 1 ATR above)
        max_stop = entry + (atr * 1.0)
        if stop_loss < max_stop:
            stop_loss = max_stop
        
        # Take profit: Risk x 2 (for 1:2 risk:reward)
        risk = stop_loss - entry
        take_profit = entry - (risk * 2.0)
        
        return entry, stop_loss, take_profit
    
    def get_position_size(self, signal: Signal, account_size: Optional[float] = None) -> float:
        """
        Calculate position size based on risk
        
        Position Size = (Account Risk / Price Risk) * Pip Value
        
        Conservative approach: Risk only 2% of account per trade
        
        Args:
            signal: Signal with entry and stop loss levels
            account_size: Account size (uses default if not provided)
        
        Returns:
            Position size in lots (for forex)
        
        Example:
            >>> position_size = risk_engine.get_position_size(signal)
            >>> print(f"Trade {position_size} micro lots")
        """
        
        if not signal.entry_price or not signal.stop_loss:
            return 0
        
        if account_size is None:
            account_size = self.account_balance
        
        # Amount we're willing to risk on this trade
        account_risk = account_size * self.risk_per_trade
        
        # Price difference (how many pips)
        if signal.signal_type == "LONG":
            price_risk = signal.entry_price - signal.stop_loss
        else:  # SHORT
            price_risk = signal.stop_loss - signal.entry_price
        
        if price_risk <= 0:
            return 0
        
        # Standard forex lot: 100,000 units
        # Micro lot: 1,000 units
        # Mini lot: 10,000 units
        
        # For simplicity: calculate in micro lots (1,000 units)
        # 1 pip on EURUSD micro lot = $0.10
        pips = price_risk * 10000  # Convert price difference to pips
        dollar_risk_per_micro_lot = pips * 0.1  # $0.10 per pip per micro lot
        
        if dollar_risk_per_micro_lot <= 0:
            return 0
        
        position_size_micro_lots = account_risk / dollar_risk_per_micro_lot
        
        return position_size_micro_lots
    
    def validate_trade(self, signal: Signal) -> bool:
        """
        Check if a trade is worth taking
        
        Filters:
        - Confidence must be >= 50%
        - Risk:Reward must be >= 1:1 (at least break-even potential)
        - Stop loss must be different from entry
        
        Args:
            signal: Signal with all risk parameters
        
        Returns:
            True if trade is valid, False otherwise
        """
        
        if not signal:
            return False
        
        # Must have confidence
        if signal.confidence < 0.50:
            print(f"REJECTED: Confidence too low ({signal.confidence * 100:.0f}%)")
            return False
        
        # Must have risk:reward
        if not signal.risk_reward_ratio or signal.risk_reward_ratio < 1.0:
            print(f"REJECTED: Risk:Reward ratio too low ({signal.risk_reward_ratio})")
            return False
        
        # Must have proper stop loss
        if signal.entry_price == signal.stop_loss:
            print("REJECTED: Stop loss equals entry (no risk management)")
            return False
        
        return True


# Create global instance
risk_engine = RiskEngine()