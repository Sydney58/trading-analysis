"""
"""

import yfinance as yf
import pandas as pd
from app.models.candle import Candle


class DataFetcher:
    def __init__(self):
        print("DataFetcher initialized (yfinance - no API key needed)")
    
    def get_intraday_data(self, symbol, timeframe, limit=250):
        """Fetch intraday candle data"""
        try:
            yf_symbol = f"{symbol}=X"
            
            print(f"Fetching {symbol} {timeframe} data from yfinance...")
            df = yf.download(yf_symbol, interval=timeframe, progress=False)
            
            if df.empty:
                raise ValueError(f"No data returned for {symbol}")
            
            # Keep only last 250 candles
            df = df.tail(limit)
            
            candles = []
            
            # Properly iterate through DataFrame
            for timestamp, row in df.iterrows():
                try:
                    # Access values correctly as scalars
                    open_price = float(row['Open']) if pd.notna(row['Open']) else 0
                    high_price = float(row['High']) if pd.notna(row['High']) else 0
                    low_price = float(row['Low']) if pd.notna(row['Low']) else 0
                    close_price = float(row['Close']) if pd.notna(row['Close']) else 0
                    volume = float(row['Volume']) if pd.notna(row['Volume']) else 0
                    
                    # Remove timezone if exists
                    if hasattr(timestamp, 'tz_localize'):
                        timestamp = timestamp.tz_localize(None)
                    
                    candle = Candle(
                        symbol=symbol,
                        timestamp=timestamp,
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=volume,
                        timeframe=timeframe
                    )
                    candles.append(candle)
                except Exception as e:
                    print(f"Warning: Skipping row - {e}")
                    continue
            
            if not candles:
                raise ValueError(f"No valid candles parsed for {symbol}")
            
            print(f"✅ Successfully fetched {len(candles)} candles for {symbol}")
            return candles
        
        except Exception as e:
            print(f"❌ Error fetching data: {str(e)}")
            raise ValueError(f"No data returned for {symbol}")
    
    def get_daily_data(self, symbol, limit=250):
        """Fetch daily candle data"""
        return self.get_intraday_data(symbol, "1d", limit=limit)