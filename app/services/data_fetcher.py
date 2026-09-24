"""
Optimized Data Fetcher - Memory efficient and Fixed
"""

import yfinance as yf
from app.models.candle import Candle


class DataFetcher:
    def __init__(self):
        print("DataFetcher initialized (yfinance - no API key needed)")
    
    def get_intraday_data(self, symbol, timeframe, limit=250):
        """Fetch intraday candle data"""
        try:
            # Convert symbol to yfinance format
            yf_symbol = f"{symbol}=X"
            
            print(f"Fetching {symbol} {timeframe} data from yfinance...")
            df = yf.download(yf_symbol, interval=timeframe, progress=False)
            
            if df.empty:
                raise ValueError(f"No data returned for {symbol}")
            
            # Keep only last 250 candles
            df = df.tail(limit)
            
            candles = []
            for idx, row in df.iterrows():
                try:
                    candle = Candle(
                        symbol=symbol,
                        timestamp=idx.tz_localize(None),
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
            
            if not candles:
                raise ValueError(f"No valid candles parsed for {symbol}")
            
            print(f"Successfully fetched {len(candles)} candles for {symbol}")
            return candles
        
        except Exception as e:
            print(f"Error fetching data: {str(e)}")
            raise ValueError(f"No data returned for {symbol}")
    
    def get_daily_data(self, symbol, limit=250):
        """Fetch daily candle data"""
        return self.get_intraday_data(symbol, "1d", limit=limit)