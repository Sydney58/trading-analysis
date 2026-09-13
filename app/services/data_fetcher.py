import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import List
from app.models import Candle

class DataFetcher:
    """
    Fetches forex price data using yfinance
    Works without API keys and no rate limits!
    """
    
    def __init__(self):
        print("DataFetcher initialized (yfinance - no API key needed)")
    
    def get_intraday_data(self, symbol: str, timeframe: str = "60min") -> List[Candle]:
        """
        Fetch intraday forex data using yfinance
        
        Args:
            symbol: Forex pair (e.g., "EURUSD")
            timeframe: Time interval (60min, 15min, etc)
        
        Returns:
            List of Candle objects
        """
        
        try:
            # Convert timeframe format
            yf_timeframe = timeframe.replace("min", "m")
            
            # Convert symbol to yfinance format
            yf_symbol = f"{symbol}=X"
            
            print(f"Fetching {symbol} {timeframe} data from yfinance...")
            
            # Download data
            data = yf.download(
                yf_symbol,
                period="30d",
                interval=yf_timeframe,
                progress=False
            )
            
            if data.empty:
                raise ValueError(f"No data returned for {symbol}")
            
            candles = self._parse_dataframe(data, symbol, timeframe)
            
            print(f"Successfully fetched {len(candles)} candles for {symbol}")
            return candles
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            raise
    
    def _parse_dataframe(self, df, symbol: str, timeframe: str) -> List[Candle]:
        """
        Convert yfinance DataFrame to Candle objects
        Handles MultiIndex columns from yfinance
        """
        candles = []
        
        try:
            # Get the ticker symbol in the format yfinance uses
            yf_symbol = f"{symbol}=X"
            
            # yfinance returns MultiIndex columns like ('Close', 'EURUSD=X')
            # We access them as tuples
            
            # Iterate through rows
            for idx in range(len(df)):
                try:
                    # Extract values using tuple column access
                    open_price = float(df.iloc[idx][('Open', yf_symbol)])
                    high_price = float(df.iloc[idx][('High', yf_symbol)])
                    low_price = float(df.iloc[idx][('Low', yf_symbol)])
                    close_price = float(df.iloc[idx][('Close', yf_symbol)])
                    volume = int(df.iloc[idx][('Volume', yf_symbol)]) if ('Volume', yf_symbol) in df.columns else 0
                    
                    # Get timestamp from index
                    timestamp = df.index[idx]
                    
                    # Convert pandas Timestamp to datetime
                    if hasattr(timestamp, 'to_pydatetime'):
                        dt = timestamp.to_pydatetime()
                    else:
                        dt = timestamp
                    
                    # Remove timezone info if present
                    if dt.tzinfo is not None:
                        dt = dt.replace(tzinfo=None)
                    
                    # Create Candle object
                    candle = Candle(
                        symbol=symbol,
                        timestamp=dt,
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=volume,
                        timeframe=timeframe
                    )
                    
                    candles.append(candle)
                    
                except (ValueError, TypeError, KeyError) as e:
                    # Skip rows with invalid data
                    continue
            
            # Sort by timestamp (oldest first)
            candles.sort(key=lambda c: c.timestamp)
            
            return candles
            
        except Exception as e:
            print(f"Error parsing dataframe: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_daily_data(self, symbol: str) -> List[Candle]:
        """Fetch daily forex data"""
        try:
            yf_symbol = f"{symbol}=X"
            
            print(f"Fetching {symbol} daily data from yfinance...")
            
            data = yf.download(
                yf_symbol,
                period="1y",
                interval="1d",
                progress=False
            )
            
            if data.empty:
                raise ValueError(f"No daily data returned for {symbol}")
            
            candles = self._parse_dataframe(data, symbol, "daily")
            
            print(f"Successfully fetched {len(candles)} daily candles for {symbol}")
            return candles
            
        except Exception as e:
            print(f"Error fetching daily data: {e}")
            raise


# Create global instance
fetcher = DataFetcher()