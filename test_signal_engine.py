"""
Test Signal Engine
Complete workflow: Fetch Data → Analyze → Generate Signal
"""

print("\n" + "="*70)
print("TESTING SIGNAL ENGINE - COMPLETE TRADING WORKFLOW")
print("="*70)

print("\nStep 1: Import all services")
try:
    from app.services import DataFetcher, TechnicalAnalysis, SignalEngine
    print("SUCCESS: Imported all services")
except Exception as e:
    print(f"FAILED: {e}")
    exit()

print("\nStep 2: Create service instances")
try:
    fetcher = DataFetcher()
    analyzer = TechnicalAnalysis()
    engine = SignalEngine()
    print("SUCCESS: Created all instances")
except Exception as e:
    print(f"FAILED: {e}")
    exit()

print("\nStep 3: Fetch forex data (714 candles)")
try:
    candles = fetcher.get_intraday_data("EURUSD", "60min")
    print(f"SUCCESS: Got {len(candles)} candles")
except Exception as e:
    print(f"FAILED: {e}")
    exit()

print("\nStep 4: Analyze indicators")
try:
    indicators = analyzer.analyze(candles)
    print("SUCCESS: Calculated all indicators")
except Exception as e:
    print(f"FAILED: {e}")
    exit()

print("\nStep 5: Generate trading signal")
try:
    signal = engine.generate_signal(candles, indicators, "EURUSD", "60min")
    print("SUCCESS: Generated trading signal")
except Exception as e:
    print(f"FAILED: {e}")
    exit()

# Display the signal
print("\n" + "="*70)
print("TRADING SIGNAL")
print("="*70)

print(f"\nSymbol: {signal.symbol}")
print(f"Timeframe: {signal.timeframe}")
print(f"Timestamp: {signal.timestamp}")

print(f"\nSignal Type: {signal.signal_type}")
print(f"Confidence: {signal.confidence * 100:.0f}%")

if signal.signal_type == "LONG":
    print("Action: BUY")
elif signal.signal_type == "SHORT":
    print("Action: SELL")
else:
    print("Action: WAIT (no clear signal)")

print(f"\nEntry Price: {signal.entry_price:.6f}")

print(f"\nReasons for this signal:")
for i, reason in enumerate(signal.reasons, 1):
    print(f"  {i}. {reason}")

# Show indicator values
print(f"\nIndicator Values:")
print(f"  RSI (14): {indicators.rsi:.2f}")
print(f"  MACD: {indicators.macd:.6f} (Signal: {indicators.macd_signal:.6f})")
print(f"  EMA 9: {indicators.ema_short:.6f}")
print(f"  EMA 21: {indicators.ema_long:.6f}")
print(f"  SMA 50: {indicators.sma_short:.6f}")
print(f"  SMA 200: {indicators.sma_long:.6f}")
print(f"  ATR (14): {indicators.atr:.6f}")

# Show interpretation
print(f"\n" + "="*70)
print("SIGNAL INTERPRETATION")
print("="*70)

if signal.confidence >= 0.80:
    confidence_text = "VERY STRONG"
elif signal.confidence >= 0.60:
    confidence_text = "STRONG"
elif signal.confidence >= 0.40:
    confidence_text = "MODERATE"
else:
    confidence_text = "WEAK"

print(f"\nSignal Strength: {confidence_text}")
print(f"Confidence: {signal.confidence * 100:.0f}%")

if signal.signal_type == "WAIT":
    print("\nRecommendation: WAIT for clearer signals")
    print("The indicators are not in strong agreement.")
    print("Consider waiting for more confluence before trading.")
elif signal.signal_type == "LONG":
    print(f"\nRecommendation: Consider BUYING {signal.symbol}")
    print(f"Signal is based on {len(signal.reasons)} indicator(s) agreeing on uptrend.")
    if signal.confidence >= 0.80:
        print("This is a strong buy signal - good risk/reward.")
    elif signal.confidence >= 0.60:
        print("This is a decent buy signal - wait for confirmation if uncertain.")
    else:
        print("This is a weak buy signal - requires confirmation.")
elif signal.signal_type == "SHORT":
    print(f"\nRecommendation: Consider SELLING {signal.symbol}")
    print(f"Signal is based on {len(signal.reasons)} indicator(s) agreeing on downtrend.")
    if signal.confidence >= 0.80:
        print("This is a strong sell signal - good risk/reward.")
    elif signal.confidence >= 0.60:
        print("This is a decent sell signal - wait for confirmation if uncertain.")
    else:
        print("This is a weak sell signal - requires confirmation.")

print("\n" + "="*70)
print("SUCCESS: Signal Engine working perfectly!")
print("="*70)

print("""
Next Steps:
1. Risk Engine - Calculate entry, stop loss, take profit, position size
2. API Routes - Expose signals via HTTP endpoints
3. Dashboard - Visualize signals in real-time
4. Backtesting - Test strategy on historical data
""")