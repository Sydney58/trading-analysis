"""
Test Technical Analysis Service
Shows how to calculate and use indicators
"""

print("\n" + "="*60)
print("TESTING TECHNICAL ANALYSIS")
print("="*60)

print("\nStep 1: Import services")
try:
    from app.services import DataFetcher, TechnicalAnalysis
    print("SUCCESS: Imported DataFetcher and TechnicalAnalysis")
except Exception as e:
    print(f"FAILED: {e}")
    exit()

print("\nStep 2: Create instances")
try:
    fetcher = DataFetcher()
    analyzer = TechnicalAnalysis()
    print("SUCCESS: Created instances")
except Exception as e:
    print(f"FAILED: {e}")
    exit()

print("\nStep 3: Fetch forex data")
try:
    print("Fetching 714 candles of EUR/USD...")
    candles = fetcher.get_intraday_data("EURUSD", "60min")
    print(f"SUCCESS: Got {len(candles)} candles")
except Exception as e:
    print(f"FAILED: {e}")
    exit()

print("\nStep 4: Analyze the data")
try:
    print("Calculating indicators...")
    indicators = analyzer.analyze(candles)
    print("SUCCESS: Calculated all indicators")
except Exception as e:
    print(f"FAILED: {e}")
    exit()

print("\n" + "="*60)
print("INDICATOR VALUES")
print("="*60)

print(f"\nMomentum (RSI):")
print(f"  RSI (14): {indicators.rsi:.2f}")
if indicators.rsi > 70:
    print(f"  Status: OVERBOUGHT (potential sell)")
elif indicators.rsi < 30:
    print(f"  Status: OVERSOLD (potential buy)")
else:
    print(f"  Status: Neutral")

print(f"\nTrend (MACD):")
print(f"  MACD: {indicators.macd:.6f}")
print(f"  Signal: {indicators.macd_signal:.6f}")
print(f"  Histogram: {indicators.macd_histogram:.6f}")
if indicators.macd > indicators.macd_signal:
    print(f"  Status: BULLISH (MACD above signal line)")
else:
    print(f"  Status: BEARISH (MACD below signal line)")

print(f"\nMoving Averages:")
latest_candle = candles[-1]
current_price = latest_candle.close
print(f"  Current Price: {current_price:.6f}")
print(f"  EMA 9 (short): {indicators.ema_short:.6f}")
print(f"  EMA 21 (long): {indicators.ema_long:.6f}")
print(f"  SMA 50: {indicators.sma_short:.6f}")
print(f"  SMA 200: {indicators.sma_long:.6f}")

# Check if price is above or below key EMAs
if current_price > indicators.ema_short:
    print(f"  Price is ABOVE EMA9 (bullish short-term)")
else:
    print(f"  Price is BELOW EMA9 (bearish short-term)")

if current_price > indicators.sma_long:
    print(f"  Price is ABOVE SMA200 (bullish long-term)")
else:
    print(f"  Price is BELOW SMA200 (bearish long-term)")

print(f"\nVolatility (ATR):")
print(f"  ATR (14): {indicators.atr:.6f}")
print(f"  Status: This is the average price swing")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)

signals = 0

# Count bullish signals
if indicators.rsi < 30:
    print("+ RSI oversold (buy signal)")
    signals += 1
if indicators.macd > indicators.macd_signal:
    print("+ MACD bullish (buy signal)")
    signals += 1
if current_price > indicators.ema_short:
    print("+ Price above EMA9 (bullish)")
    signals += 1
if current_price > indicators.sma_long:
    print("+ Price above SMA200 (bullish)")
    signals += 1

# Count bearish signals
if indicators.rsi > 70:
    print("- RSI overbought (sell signal)")
    signals -= 1
if indicators.macd < indicators.macd_signal:
    print("- MACD bearish (sell signal)")
    signals -= 1
if current_price < indicators.ema_short:
    print("- Price below EMA9 (bearish)")
    signals -= 1
if current_price < indicators.sma_long:
    print("- Price below SMA200 (bearish)")
    signals -= 1

print(f"\nNet Signal Score: {signals}")
if signals > 2:
    print("STRONG BUY signal")
elif signals > 0:
    print("BUY signal (weak)")
elif signals < -2:
    print("STRONG SELL signal")
elif signals < 0:
    print("SELL signal (weak)")
else:
    print("NEUTRAL - wait for clearer signal")

print("\nSUCCESS: All technical analysis working!")