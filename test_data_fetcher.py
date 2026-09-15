"""Simple test for Data Fetcher"""

print("\nStep 1: Import DataFetcher")
try:
    from app.services import DataFetcher
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit()

print("\nStep 2: Create instance")
try:
    fetcher = DataFetcher()
    print("✅ Instance created")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit()

print("\nStep 3: Fetch EUR/USD data")
try:
    print("📡 Fetching data (wait 5-10 seconds)...")
    candles = fetcher.get_intraday_data("EURUSD", "60min")
    print(f"✅ Got {len(candles)} candles")
except Exception as e:
    print(f"❌ Failed: {e}")
    exit()

print("\nStep 4: Show latest candle")
latest = candles[-1]
print(f"Latest: {latest}")
print(f"Close Price: {latest.close}")

print("\n✅ ALL TESTS PASSED!")