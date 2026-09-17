"""
Optimized Data Fetcher - Memory efficient
Fetches only 250 candles (enough for all indicators, much less memory)
"""

import yfinance as yf
from app.models.candle import Candle


class DataFetcher:
    """Fetches forex data from yfinance with memory optimization"""
    
    def __init__(self):
        print("DataFetcher initialized (yfinance - no API key needed)")
    
    def get_intraday_data(self, symbol, timeframe, limit=250):
        """
        Fetch intraday candle data
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            timeframe: Timeframe (e.g., "60m", "15m")
            limit: Number of candles to fetch (default: 250 to save memory)
        
        Returns:
            List of Candle objects
        """
        try:
            # Convert symbol to yfinance format
            yf_symbol = f"{symbol}=X"
            
            # Fetch data - REDUCED TO 250 CANDLES (was 714)
            print(f"Fetching {symbol} {timeframe} data from yfinance...")
            df = yf.download(yf_symbol, interval=timeframe, progress=False, period="max")
            
            # Keep only last 250 candles (most recent data)
            df = df.tail(limit)
            
            if df.empty:
                raise ValueError(f"No data returned for {symbol}")
            
            # Convert to Candle objects
            candles = []
            for idx, row in df.iterrows():
                try:
                    candle = Candle(
                        symbol=symbol,
                        timestamp=idx.tz_localize(None),  # Remove timezone
                        open=float(row['Open']),
                        high=float(row['High']),
                        low=float(row['Low']),
                        close=float(row['Close']),
                        volume=float(row['Volume']) if 'Volume' in row else 0,
                        timeframe=timeframe
                    )
                    candles.append(candle)
                except (KeyError, TypeError, ValueError) as e:
                    print(f"Warning: Could not parse row: {e}")
                    continue
            
            print(f"Successfully fetched {len(candles)} candles for {symbol}")
            return candles
        
        except Exception as e:
            print(f"Error fetching data: {str(e)}")
            raise ValueError(f"No data returned for {symbol}")
    
    def get_daily_data(self, symbol, limit=250):
        """
        Fetch daily candle data
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            limit: Number of candles to fetch (default: 250)
        
        Returns:
            List of Candle objects
        """
        return self.get_intraday_data(symbol, "1d", limit=limit)