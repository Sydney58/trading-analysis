"""
app/instruments.py

One place for per-instrument settings: data ticker, pip size, contract size,
and how pip value converts to the account currency.
"""

INSTRUMENTS = {
    "EURUSD": {
        "ticker": "EURUSD=X",
        "pip_size": 0.0001,
        "contract_size": 100_000,   # units per standard lot
        "quote": "USD",             # quote currency = account currency, no conversion
        "news_tags": ["EUR", "USD"],
    },
    "GBPUSD": {
        "ticker": "GBPUSD=X",
        "pip_size": 0.0001,
        "contract_size": 100_000,
        "quote": "USD",
        "news_tags": ["GBP", "USD"],
    },
    "USDJPY": {
        "ticker": "JPY=X",
        "pip_size": 0.01,
        "contract_size": 100_000,
        "quote": "JPY",            # pip value is in JPY, must be converted to USD
        "news_tags": ["USD", "JPY"],
    },
    "XAUUSD": {
        "ticker": "GC=F",          # gold futures on yfinance
        "pip_size": 0.10,          # 1 "pip" = $0.10 move (common broker convention)
        "contract_size": 100,      # 100 troy oz per standard lot
        "quote": "USD",
        "news_tags": ["USD", "XAU"],
    },
}


def pip_value_per_lot(symbol, quote_to_usd=None):
    """
    Value in USD of one pip for one standard lot.
    quote_to_usd: rate converting the quote currency to USD.
                  Needed only when quote != USD (e.g. USDJPY: 1 / USDJPY rate).
    """
    cfg = INSTRUMENTS[symbol]
    value_in_quote = cfg["pip_size"] * cfg["contract_size"]
    if cfg["quote"] == "USD":
        return value_in_quote
    if quote_to_usd is None:
        raise ValueError(f"{symbol} needs quote_to_usd to convert {cfg['quote']} to USD")
    return value_in_quote * quote_to_usd


def position_size_lots(symbol, account, risk_pct, stop_pips, quote_to_usd=None):
    """Lots = (account x risk%) / (stop pips x pip value per lot)."""
    risk_amount = account * risk_pct / 100
    per_lot_risk = stop_pips * pip_value_per_lot(symbol, quote_to_usd)
    if per_lot_risk <= 0:
        raise ValueError("stop_pips must be positive")
    return round(risk_amount / per_lot_risk, 2)


if __name__ == "__main__":
    # Sanity checks
    assert abs(pip_value_per_lot("EURUSD") - 10.0) < 1e-9        # $10 per pip per lot
    assert abs(pip_value_per_lot("XAUUSD") - 10.0) < 1e-9        # $10 per $0.10 move per lot
    print("EURUSD 0.5% risk, 20 pips, $500:", position_size_lots("EURUSD", 500, 0.5, 20))
    print("XAUUSD 0.5% risk, 50 pips, $500:", position_size_lots("XAUUSD", 500, 0.5, 50))
    print("USDJPY 0.5% risk, 20 pips, $500 (rate 150):", position_size_lots("USDJPY", 500, 0.5, 20, quote_to_usd=1/150))
    print("checks passed")