"""Debug yfinance to see what data it returns"""

import yfinance as yf
import pandas as pd

print("\n" + "="*60)
print("DEBUGGING YFINANCE")
print("="*60)

# Try different ways to get forex data
print("\n1. Trying EURUSD=X with 60m interval...")
try:
    data = yf.download("EURUSD=X", period="30d", interval="60m", progress=False)
    print(f"   Shape: {data.shape}")
    print(f"   Empty: {data.empty}")
    if not data.empty:
        print(f"   First row:\n{data.head()}")
    else:
        print("   ❌ No data returned")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n2. Trying EURUSD=X with 1h interval...")
try:
    data = yf.download("EURUSD=X", period="30d", interval="1h", progress=False)
    print(f"   Shape: {data.shape}")
    print(f"   Empty: {data.empty}")
    if not data.empty:
        print(f"   First row:\n{data.head()}")
    else:
        print("   ❌ No data returned")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n3. Trying daily data (always works)...")
try:
    data = yf.download("EURUSD=X", period="1y", interval="1d", progress=False)
    print(f"   Shape: {data.shape}")
    print(f"   Empty: {data.empty}")
    if not data.empty:
        print(f"   ✅ Got {len(data)} rows")
        print(f"   First row:\n{data.head()}")
        print(f"   Last row:\n{data.tail()}")
    else:
        print("   ❌ No data returned")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n4. Checking ticker info...")
try:
    ticker = yf.Ticker("EURUSD=X")
    print(f"   ✅ Ticker loaded: {ticker}")
except Exception as e:
    print(f"   ❌ Error: {e}")