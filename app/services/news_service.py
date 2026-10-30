"""
app/services/news_service.py

Fetches headlines + sentiment (Alpha Vantage) and the economic calendar
(Forex Factory weekly JSON feed), and builds one payload for the dashboard.

Needs:  pip install requests
Config: ALPHA_VANTAGE_API_KEY in your .env / config.py
"""
import time
from datetime import datetime, timedelta, timezone

import requests

from app.config import Config  # expects Config.ALPHA_VANTAGE_API_KEY

CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
ALPHA_URL = "https://www.alphavantage.co/query"

# How long to reuse results. Alpha Vantage free tier is ~25 calls/day,
# so keep this generous.
NEWS_TTL = 60 * 60       # 1 hour
CALENDAR_TTL = 30 * 60   # 30 minutes

# Minutes before/after a high-impact event when we advise caution.
CAUTION_WINDOW_MIN = 60

# Finnhub (free tier allows ~60 calls/min), so it can refresh much faster
# than Alpha Vantage and gives us fresher headlines.
FINNHUB_URL = "https://finnhub.io/api/v1/news"
FINNHUB_TTL = 5 * 60     # 5 minutes

# Alpha Vantage NEWS_SENTIMENT requires a premium plan, so it is off by default.
USE_ALPHA_VANTAGE = False

# Alpha Vantage only understands real currencies.
AV_CURRENCIES = {"USD", "EUR", "GBP", "JPY"}

# How much each source counts when both have a score for a currency.
AV_WEIGHT, FH_WEIGHT = 0.6, 0.4

# Used to work out which currency a Finnhub headline is about.
KEYWORDS = {
    "USD": ["dollar", "usd", "greenback", "federal reserve", "fed ", "powell", "treasury yield"],
    "EUR": ["euro ", "eur/", "eurusd", "ecb", "lagarde", "eurozone"],
    "GBP": ["pound", "sterling", "gbp", "bank of england", "boe"],
    "JPY": ["yen", "jpy", "bank of japan", "boj"],
    "XAU": ["gold", "xau", "bullion"],
}

# Very simple headline scoring. Crude on purpose: it only nudges the
# score, and Alpha Vantage's scoring carries more weight.
POSITIVE = ["rise", "rises", "rose", "jump", "jumps", "gain", "gains", "surge", "surges",
            "rally", "rallies", "climb", "climbs", "strengthen", "strengthens", "hawkish",
            "beat", "beats", "higher", "record high", "advance", "advances"]
NEGATIVE = ["fall", "falls", "fell", "slip", "slips", "drop", "drops", "slide", "slides",
            "slump", "slumps", "weaken", "weakens", "dovish", "miss", "misses", "lower",
            "decline", "declines", "tumble", "tumbles", "sink", "sinks", "pressure"]

# Which currencies matter for each instrument.
INSTRUMENTS = {
    "EURUSD": {"base": "EUR", "quote": "USD", "currencies": ["EUR", "USD"]},
    "GBPUSD": {"base": "GBP", "quote": "USD", "currencies": ["GBP", "USD"]},
    "USDJPY": {"base": "USD", "quote": "JPY", "currencies": ["USD", "JPY"]},
    # Gold is priced in USD, so USD news is what moves it.
    "XAUUSD": {"base": "XAU", "quote": "USD", "currencies": ["USD"],
               "news_tags": ["USD", "XAU"]},
}

_cache = {}


def _cached(key, ttl, loader):
    """Tiny in-memory cache. Returns stale data if the refresh fails."""
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit["at"] < ttl:
        return hit["data"]
    try:
        data = loader()
        _cache[key] = {"at": now, "data": data}
        return data
    except Exception:
        if hit:
            return hit["data"]
        raise


# ---------- Economic calendar ----------

def _load_calendar():
    r = requests.get(CALENDAR_URL, timeout=10)
    r.raise_for_status()
    events = []
    for e in r.json():
        if e.get("impact") not in ("High", "Medium"):
            continue
        events.append({
            "title": e.get("title"),
            "currency": e.get("country"),
            "impact": e.get("impact").lower(),
            "time": datetime.fromisoformat(e["date"]).astimezone(timezone.utc).isoformat(),
            "forecast": e.get("forecast") or "",
            "previous": e.get("previous") or "",
        })
    return events


def get_events(currencies):
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=3)
    out = []
    for e in _cached("calendar", CALENDAR_TTL, _load_calendar):
        t = datetime.fromisoformat(e["time"])
        if e["currency"] in currencies and now - timedelta(hours=2) <= t <= horizon:
            out.append(e)
    return sorted(out, key=lambda e: e["time"])


def get_caution(events):
    """Active when a high-impact event is within the caution window."""
    now = datetime.now(timezone.utc)
    window = timedelta(minutes=CAUTION_WINDOW_MIN)
    for e in events:
        if e["impact"] != "high":
            continue
        t = datetime.fromisoformat(e["time"])
        if abs(t - now) <= window:
            return {"active": True,
                    "reason": f'{e["currency"]} {e["title"]} at {t.strftime("%H:%M")} UTC'}
    return {"active": False, "reason": ""}


# ---------- Headlines + sentiment ----------

def _load_news(currency):
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": f"FOREX:{currency}",
        "limit": 30,
        "sort": "LATEST",
        "apikey": Config.ALPHA_VANTAGE_API_KEY,
    }
    r = requests.get(ALPHA_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if "feed" not in data:  # rate limit / error message from Alpha Vantage
        raise RuntimeError(data.get("Note") or data.get("Information") or "No feed")

    articles, weighted, weights = [], 0.0, 0.0
    for item in data["feed"]:
        score = None
        for ts in item.get("ticker_sentiment", []):
            if ts.get("ticker") == f"FOREX:{currency}":
                rel = float(ts.get("relevance_score", 0))
                score = float(ts.get("ticker_sentiment_score", 0))
                weighted += score * rel
                weights += rel
        published = datetime.strptime(item["time_published"], "%Y%m%dT%H%M%S") \
            .replace(tzinfo=timezone.utc)
        articles.append({
            "title": item["title"],
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "time": published.isoformat(),
            "currency": currency,
            "sentiment": score if score is not None else item.get("overall_sentiment_score", 0),
        })
    avg = weighted / weights if weights else 0.0
    return {"score": avg, "articles": articles}


def _load_finnhub():
    key = getattr(Config, "FINNHUB_API_KEY", "")
    if not key:
        raise RuntimeError("FINNHUB_API_KEY not set")
    r = requests.get(FINNHUB_URL, params={"category": "general", "token": key}, timeout=10)
    r.raise_for_status()
    return r.json()


def _subject_currency(text):
    """The currency mentioned first in the headline is treated as its subject."""
    text = text.lower() + " "
    best, best_pos = None, None
    for cur, words in KEYWORDS.items():
        for w in words:
            pos = text.find(w)
            if pos != -1 and (best_pos is None or pos < best_pos):
                best, best_pos = cur, pos
    return best


def _headline_score(headline):
    words = headline.lower().replace(",", " ").replace(".", " ").split()
    pos = sum(1 for w in words if w in POSITIVE)
    neg = sum(1 for w in words if w in NEGATIVE)
    if pos + neg == 0:
        return 0.0
    return 0.5 * (pos - neg) / (pos + neg)   # kept within -0.5 .. +0.5


def get_finnhub_items(tag):
    """Finnhub headlines whose subject is this currency, with a rough score."""
    try:
        raw = _cached("finnhub", FINNHUB_TTL, _load_finnhub)
    except Exception:
        return []
    items = []
    for n in raw:
        text = (n.get("headline") or "") + " " + (n.get("summary") or "")
        if _subject_currency(text) != tag:
            continue
        items.append({
            "title": n.get("headline", ""),
            "source": n.get("source", ""),
            "url": n.get("url", ""),
            "time": datetime.fromtimestamp(n.get("datetime", 0), tz=timezone.utc).isoformat(),
            "currency": tag,
            "sentiment": _headline_score(n.get("headline", "")),
        })
    return items


def _label(score):
    if score >= 0.15:
        return "bullish"
    if score <= -0.15:
        return "bearish"
    return "neutral"


def get_news_payload(symbol):
    symbol = symbol.upper()
    cfg = INSTRUMENTS.get(symbol)
    if not cfg:
        raise ValueError(f"Unsupported symbol: {symbol}")

    per_currency, headlines, sources_used = {}, [], set()
    for cur in cfg.get("news_tags", cfg["currencies"]):
        parts = []  # (score, weight)

        # Source 1: Alpha Vantage. Disabled: NEWS_SENTIMENT is premium-only now.
        # Set USE_ALPHA_VANTAGE = True to turn it back on after upgrading.
        if USE_ALPHA_VANTAGE and cur in AV_CURRENCIES:
            try:
                res = _cached(f"news:{cur}", NEWS_TTL, lambda c=cur: _load_news(c))
                parts.append((res["score"], AV_WEIGHT))
                headlines.extend(res["articles"])
                sources_used.add("alphavantage")
            except Exception:
                pass

        # Source 2: Finnhub (fresher headlines, refreshed every 5 min)
        fh = get_finnhub_items(cur)
        if fh:
            # With Alpha Vantage off, Finnhub is the only source, so it gets full weight.
            fh_weight = FH_WEIGHT if USE_ALPHA_VANTAGE else 1.0
            parts.append((sum(a["sentiment"] for a in fh) / len(fh), fh_weight))
            headlines.extend(fh)
            sources_used.add("finnhub")

        if parts:
            total_w = sum(w for _, w in parts)
            per_currency[cur] = sum(s * w for s, w in parts) / total_w

    # Drop duplicate headlines that both sources returned.
    seen, unique = set(), []
    for h in headlines:
        k = h["title"].strip().lower()
        if k and k not in seen:
            seen.add(k)
            unique.append(h)
    headlines = unique

    # Bias for the instrument: strong base vs weak quote = bullish pair.
    # Gold: gold-specific news counts for it, dollar strength counts against it.
    if symbol == "XAUUSD":
        bias = per_currency.get("XAU", 0.0) - per_currency.get("USD", 0.0)
    else:
        bias = per_currency.get(cfg["base"], 0.0) - per_currency.get(cfg["quote"], 0.0)

    # Coverage: how many of the currencies behind this instrument have news.
    expected = cfg.get("news_tags", cfg["currencies"])
    missing = [c for c in expected if c not in per_currency]
    if not per_currency:
        coverage = "none"
    elif missing:
        coverage = "partial"
    else:
        coverage = "full"

    events = get_events(cfg["currencies"])
    headlines.sort(key=lambda a: a["time"], reverse=True)

    return {
        "symbol": symbol,
        "sentiment": {
            "score": round(max(-1.0, min(1.0, bias)), 3),
            "label": _label(bias),
            "by_currency": {c: round(s, 3) for c, s in per_currency.items()},
        },
        "sources": sorted(sources_used),
        "coverage": {
            "level": coverage,
            "missing": missing,
        },
        # Keyword scoring is rough, so the sentiment is shown as indicative only.
        "indicative": True,
        "caution": get_caution(events),
        "events": events[:10],
        "headlines": headlines[:15],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }