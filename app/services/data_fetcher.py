"""
Data Fetcher Service - Fetches forex price data from yfinance
"""

import yfinance as yf
import pandas as pd
from app.models.candle import Candle


OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]
PRICE_COLUMNS = ["Open", "High", "Low", "Close"]

# Max history Yahoo allows per interval (enough candles for SMA200)
INTERVAL_PERIODS = {
    "1m": "7d",
    "2m": "60d",
    "5m": "60d",
    "15m": "60d",
    "30m": "60d",
    "60m": "730d",
    "90m": "60d",
    "1h": "730d",
    "1d": "2y",
    "5d": "5y",
    "1wk": "10y",
    "1mo": "max",
    "3mo": "max",
}

# Intervals Yahoo doesn't provide: built by resampling a finer source interval
RESAMPLED_INTERVALS = {
    "4h": "1h",
}


class DataFetcher:
    def __init__(self):
        print("DataFetcher initialized (yfinance - no API key needed)")

    def get_intraday_data(self, symbol, timeframe, limit=250):
        """Fetch intraday candle data"""
        try:
            yf_symbol = f"{symbol}=X"
            source_interval = RESAMPLED_INTERVALS.get(timeframe, timeframe)
            period = INTERVAL_PERIODS.get(source_interval, "1mo")

            print(f"Fetching {symbol} {timeframe} ({source_interval}, {period}) data from yfinance...")
            df = yf.download(
                yf_symbol,
                period=period,
                interval=source_interval,
                progress=False,
                auto_adjust=True,
                multi_level_index=False,
            )

            if df is None or df.empty:
                raise ValueError(f"No data returned for {symbol} ({timeframe})")

            df = self._normalize_columns(df)
            df = df.dropna(subset=PRICE_COLUMNS)

            if source_interval != timeframe:
                df = self._resample(df, timeframe)

            df = df.tail(limit)

            # Remove timezone if exists
            if getattr(df.index, "tz", None) is not None:
                df.index = df.index.tz_localize(None)

            candles = [
                Candle(
                    symbol=symbol,
                    timestamp=timestamp.to_pydatetime(),
                    open=float(o),
                    high=float(h),
                    low=float(l),
                    close=float(c),
                    volume=int(v) if pd.notna(v) else 0,
                    timeframe=timeframe,
                )
                for timestamp, o, h, l, c, v in df[OHLCV_COLUMNS].itertuples(name=None)
            ]

            if not candles:
                raise ValueError(f"No valid candles parsed for {symbol}")

            print(f"✅ Successfully fetched {len(candles)} candles for {symbol}")
            return candles

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            raise ValueError(f"Failed to fetch data for {symbol}: {e}") from e

    def get_daily_data(self, symbol, limit=250):
        """Fetch daily candle data"""
        return self.get_intraday_data(symbol, "1d", limit=limit)

    @staticmethod
    def _resample(df, timeframe):
        """Aggregate candles into a coarser timeframe (e.g. 1h -> 4h)"""
        resampled = df[OHLCV_COLUMNS].resample(timeframe).agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum",
        })
        # Drop empty buckets (weekends / market closures)
        return resampled.dropna(subset=PRICE_COLUMNS)

    @staticmethod
    def _normalize_columns(df):
        """Flatten yfinance MultiIndex columns ('Open', 'EURUSD=X') -> 'Open'"""
        if isinstance(df.columns, pd.MultiIndex):
            df = df.copy()
            df.columns = df.columns.get_level_values(0)
        df = df.loc[:, ~df.columns.duplicated()]

        if "Volume" not in df.columns:
            df["Volume"] = 0

        missing = [col for col in PRICE_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns from yfinance: {missing}")
        return df
