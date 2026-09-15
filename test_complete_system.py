"""
COMPLETE TRADING SYSTEM TEST
End-to-end workflow: Fetch → Analyze → Signal → Risk Management
"""

print("\n" + "="*80)
print("COMPLETE FOREX TRADING SYSTEM - END-TO-END TEST")
print("="*80)

print("\n[1/6] Importing all services...")
try:
    from app.services import DataFetcher, TechnicalAnalysis, SignalEngine, RiskEngine
    print("✅ SUCCESS: All services imported")
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit()

print("\n[2/6] Initializing services...")
try:
    fetcher = DataFetcher()
    analyzer = TechnicalAnalysis()
    engine = SignalEngine()
    risk_engine = RiskEngine(account_balance=10000)  # $10,000 account
    print("✅ SUCCESS: All services initialized")
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit()

print("\n[3/6] Fetching EUR/USD market data...")
try:
    candles = fetcher.get_intraday_data("EURUSD", "60min")
    print(f"✅ SUCCESS: Fetched {len(candles)} candles")
    
    # Show price range
    prices = [c.close for c in candles]
    print(f"   Price range: {min(prices):.6f} - {max(prices):.6f}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit()

print("\n[4/6] Analyzing technical indicators...")
try:
    indicators = analyzer.analyze(candles)
    print("✅ SUCCESS: Calculated all indicators")
    print(f"   RSI: {indicators.rsi:.2f}")
    print(f"   MACD: {indicators.macd:.6f}")
    print(f"   ATR: {indicators.atr:.6f}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit()

print("\n[5/6] Generating trading signal...")
try:
    signal = engine.generate_signal(candles, indicators, "EURUSD", "60min")
    print(f"✅ SUCCESS: Signal generated")
    print(f"   Type: {signal.signal_type}")
    print(f"   Confidence: {signal.confidence * 100:.0f}%")
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit()

print("\n[6/6] Calculating risk management...")
try:
    signal = risk_engine.calculate_risk(signal, candles, indicators.atr)
    print("✅ SUCCESS: Risk parameters calculated")
except Exception as e:
    print(f"❌ FAILED: {e}")
    exit()

# ============================================================================
# DISPLAY COMPLETE TRADING PLAN
# ============================================================================

print("\n" + "="*80)
print("COMPLETE TRADING PLAN")
print("="*80)

print(f"\n{'MARKET ANALYSIS':-^80}")
print(f"Pair: {signal.symbol}")
print(f"Timeframe: {signal.timeframe}")
print(f"Current Price: {signal.entry_price:.6f}")

print(f"\n{'SIGNAL ANALYSIS':-^80}")
print(f"Signal Type: {signal.signal_type}")
print(f"Confidence: {signal.confidence * 100:.0f}%")

if signal.confidence >= 0.80:
    strength = "VERY STRONG"
elif signal.confidence >= 0.60:
    strength = "STRONG"
elif signal.confidence >= 0.40:
    strength = "MODERATE"
else:
    strength = "WEAK"

print(f"Signal Strength: {strength}")

print(f"\nIndicators Supporting This Signal:")
for reason in signal.reasons:
    print(f"  • {reason}")

print(f"\n{'RISK MANAGEMENT PLAN':-^80}")
print(f"Entry Price: {signal.entry_price:.6f}")
print(f"Stop Loss: {signal.stop_loss:.6f}")
print(f"Take Profit: {signal.take_profit:.6f}")

# Calculate risk in pips
if signal.signal_type == "LONG":
    risk_pips = (signal.entry_price - signal.stop_loss) * 10000
    profit_pips = (signal.take_profit - signal.entry_price) * 10000
else:
    risk_pips = (signal.stop_loss - signal.entry_price) * 10000
    profit_pips = (signal.entry_price - signal.take_profit) * 10000

print(f"\nRisk: {risk_pips:.1f} pips")
print(f"Profit Potential: {profit_pips:.1f} pips")
print(f"Risk:Reward Ratio: 1:{signal.risk_reward_ratio:.2f}")

# Position sizing
position_size = risk_engine.get_position_size(signal)
print(f"\nRecommended Position Size: {position_size:.2f} micro lots")
print(f"(Risking 2% of $10,000 account = $200)")

print(f"\n{'TRADE VALIDITY':-^80}")
is_valid = risk_engine.validate_trade(signal)
if is_valid:
    print("✅ Trade is VALID and meets all criteria")
    print(f"   • Confidence >= 50%: {signal.confidence * 100:.0f}% ✅")
    print(f"   • Risk:Reward >= 1:1: 1:{signal.risk_reward_ratio:.2f} ✅")
    print(f"   • Stop loss properly set: ✅")
else:
    print("❌ Trade REJECTED - does not meet criteria")

print(f"\n{'RECOMMENDATION':-^80}")

if not is_valid:
    print("DO NOT TRADE")
    print("This signal does not meet minimum quality standards.")
elif signal.confidence >= 0.80:
    action = "BUY" if signal.signal_type == "LONG" else "SELL"
    print(f"STRONG {action} SIGNAL - Good risk:reward ratio")
    print(f"Enter: {signal.entry_price:.6f}")
    print(f"Stop Loss: {signal.stop_loss:.6f}")
    print(f"Take Profit: {signal.take_profit:.6f}")
    print(f"Position Size: {position_size:.2f} micro lots")
elif signal.confidence >= 0.60:
    action = "BUY" if signal.signal_type == "LONG" else "SELL"
    print(f"MODERATE {action} SIGNAL - Consider only with confirmation")
    print(f"Wait for price to reach entry level or additional confirmation")
elif signal.confidence >= 0.40:
    print("WEAK SIGNAL - Requires strong confirmation")
    print("Consider waiting for a clearer signal")
else:
    print("NO CLEAR SIGNAL - WAIT")
    print("Indicators are conflicting. Do not trade.")

# ============================================================================
# INDICATOR VALUES TABLE
# ============================================================================

print(f"\n{'INDICATOR VALUES':-^80}")
print(f"{'Indicator':<20} {'Value':<20} {'Interpretation':<40}")
print("-" * 80)

# RSI
rsi_status = "Overbought" if indicators.rsi > 70 else "Oversold" if indicators.rsi < 30 else "Neutral"
print(f"{'RSI (14)':<20} {indicators.rsi:<20.2f} {rsi_status:<40}")

# MACD
macd_status = "Bullish" if indicators.macd > indicators.macd_signal else "Bearish"
print(f"{'MACD':<20} {indicators.macd:<20.6f} {macd_status:<40}")

# EMA
if signal.entry_price > indicators.ema_short:
    ema_status = "Above (Bullish)"
else:
    ema_status = "Below (Bearish)"
print(f"{'EMA 9':<20} {indicators.ema_short:<20.6f} {ema_status:<40}")

# SMA
if signal.entry_price > indicators.sma_long:
    sma_status = "Above (Long-term uptrend)"
else:
    sma_status = "Below (Long-term downtrend)"
print(f"{'SMA 200':<20} {indicators.sma_long:<20.6f} {sma_status:<40}")

# ATR
atr_status = "High" if indicators.atr > 0.002 else "Low" if indicators.atr < 0.0005 else "Normal"
print(f"{'ATR (14)':<20} {indicators.atr:<20.6f} {atr_status:<40}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("SYSTEM STATUS")
print("="*80)

print(f"""
✅ Data Fetcher: WORKING (fetched {len(candles)} candles)
✅ Technical Analysis: WORKING (calculated 5 indicators)
✅ Signal Engine: WORKING (generated {signal.signal_type} signal)
✅ Risk Engine: WORKING (calculated entry/stop/profit)

YOUR TRADING SYSTEM IS COMPLETE AND OPERATIONAL!

Next Steps:
1. ✅ Data Layer (DONE)
2. ✅ Analysis Layer (DONE)
3. ✅ Signal Layer (DONE)
4. ✅ Risk Management (DONE)
5. → API Routes (fetch signals via HTTP)
6. → Dashboard (visualize in real-time)
7. → Backtesting (test on historical data)
8. → Live Trading (paper/real account)
""")

print("="*80)