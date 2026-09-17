"""
Risk Management Engine - Calculates Entry, Stop Loss, Take Profit, and Position Size
Now supports multiple trading styles and custom account sizes
"""

from app.models.candle import Signal
from app.config import Config


class RiskEngine:
    """
    Manages trading risk with dynamic calculations based on:
    - Trading style (Scalping, Day, Swing, Position)
    - Account size
    - Risk percentage
    - ATR (volatility)
    """
    
    def __init__(self, account_size=None, risk_percentage=None):
        """
        Initialize risk engine
        
        Args:
            account_size: Trading account size in USD (default: 10000)
            risk_percentage: Risk per trade as percentage (default: 2.0)
        """
        self.account_size = account_size or Config.DEFAULT_ACCOUNT_SIZE
        self.risk_percentage = risk_percentage or Config.DEFAULT_RISK_PERCENTAGE
        self.trading_styles = Config.TRADING_STYLES
        
        print(f"RiskEngine initialized (Account: ${self.account_size:.2f}, Risk: {self.risk_percentage}%)")
    
    def calculate_risk(self, signal, candles, atr, trading_style='day_trading'):
        """
        Calculate entry, stop loss, take profit, and position size
        
        Args:
            signal: Signal object with signal_type
            candles: List of Candle objects
            atr: Average True Range value
            trading_style: One of ['scalping', 'day_trading', 'swing_trading', 'position_trading']
        
        Returns:
            Updated Signal object with risk parameters
        """
        
        if not candles:
            return signal
        
        # Get trading style configuration
        style_config = self.trading_styles.get(trading_style, self.trading_styles['day_trading'])
        
        # Current price (entry)
        entry_price = candles[-1].close
        
        # Calculate stop loss and take profit based on trading style
        risk_amount = self.account_size * (self.risk_percentage / 100)
        
        if signal.signal_type == "LONG":
            # LONG: Stop below entry, TP above entry
            stop_loss = entry_price - (atr * style_config['sl_multiplier'])
            risk_pips = (entry_price - stop_loss) * 10000
            
            # Calculate take profit based on trading style multiplier
            take_profit = entry_price + (atr * style_config['tp_multiplier'])
            profit_pips = (take_profit - entry_price) * 10000
            
        elif signal.signal_type == "SHORT":
            # SHORT: Stop above entry, TP below entry
            stop_loss = entry_price + (atr * style_config['sl_multiplier'])
            risk_pips = (stop_loss - entry_price) * 10000
            
            # Calculate take profit based on trading style multiplier
            take_profit = entry_price - (atr * style_config['tp_multiplier'])
            profit_pips = (entry_price - take_profit) * 10000
            
        else:  # WAIT
            return signal
        
        # Calculate position size in micro lots
        # Formula: (Account × Risk%) / (Stop Loss Pips × Pip Value)
        # 1 pip = $0.10 for 1 micro lot
        pip_value_per_micro_lot = 0.10  # USD per pip per micro lot
        
        if risk_pips > 0:
            position_size_micro_lots = risk_amount / (risk_pips * pip_value_per_micro_lot)
        else:
            position_size_micro_lots = 0
        
        # Calculate risk:reward ratio
        if risk_pips > 0:
            risk_reward_ratio = profit_pips / risk_pips
        else:
            risk_reward_ratio = 0
        
        # Update signal with calculated values
        signal.entry_price = entry_price
        signal.stop_loss = stop_loss
        signal.take_profit = take_profit
        signal.risk_pips = risk_pips
        signal.profit_pips = profit_pips
        signal.risk_reward_ratio = risk_reward_ratio
        signal.position_size_micro_lots = position_size_micro_lots
        signal.trading_style = trading_style
        signal.account_size = self.account_size
        signal.risk_percentage = self.risk_percentage
        
        return signal
    
    def validate_trade(self, signal):
        """
        Validate if trade meets minimum quality criteria
        
        Args:
            signal: Signal object
        
        Returns:
            True if trade is valid, False otherwise
        """
        
        # Check confidence
        if signal.confidence < 0.50:
            return False
        
        # Check risk:reward ratio (minimum 1:1)
        if signal.risk_reward_ratio < 1.0:
            return False
        
        # Check stop loss is not equal to entry
        if signal.stop_loss == signal.entry_price:
            return False
        
        # Check take profit is not equal to entry
        if signal.take_profit == signal.entry_price:
            return False
        
        return True
    
    def get_position_size(self, signal):
        """
        Get position size from signal
        
        Args:
            signal: Signal object
        
        Returns:
            Position size in micro lots
        """
        return signal.position_size_micro_lots if hasattr(signal, 'position_size_micro_lots') else 0
    
    def get_trading_style_info(self, trading_style):
        """
        Get information about a trading style
        
        Args:
            trading_style: Style key
        
        Returns:
            Dictionary with style information
        """
        style = self.trading_styles.get(trading_style)
        if style:
            return {
                'name': style['name'],
                'description': style['description'],
                'timeframes': style['timeframes'],
                'tp_multiplier': style['tp_multiplier'],
                'sl_multiplier': style['sl_multiplier'],
                'recommended_account_min': style['recommended_account_min'],
            }
        return None
    
    def get_all_trading_styles(self):
        """
        Get all available trading styles
        
        Returns:
            List of trading styles
        """
        return [
            {
                'key': key,
                'name': style['name'],
                'description': style['description'],
                'recommended_account_min': style['recommended_account_min'],
            }
            for key, style in self.trading_styles.items()
        ]