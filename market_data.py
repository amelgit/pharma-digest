import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

INSTRUMENTS = [
    {"ticker": "BAYN.DE", "name": "Bayer AG",        "decimals": 2, "prefix": "€"},
    {"ticker": "MRK.DE",  "name": "Merck KGaA",      "decimals": 2, "prefix": "€"},
    {"ticker": "FRE.DE",  "name": "Fresenius SE",     "decimals": 2, "prefix": "€"},
    {"ticker": "NVS",     "name": "Novartis",         "decimals": 2, "prefix": "$"},
    {"ticker": "PFE",     "name": "Pfizer",           "decimals": 2, "prefix": "$"},
    {"ticker": "AZN",     "name": "AstraZeneca",      "decimals": 2, "prefix": "$"},
    {"ticker": "IBB",     "name": "iShares Biotech",  "decimals": 2, "prefix": "$"},
]


def _market_state(info: dict) -> str:
    state = info.get("marketState", "CLOSED").upper()
    if state == "REGULAR":
        return "open"
    if state in ("PRE", "PREPRE"):
        return "pre"
    if state in ("POST", "POSTPOST"):
        return "post"
    return "closed"


def fetch_market_data() -> list[dict]:
    try:
        import yfinance as yf
    except ImportError:
        logger.warning("yfinance not installed – skipping market data")
        return []

    results = []
    for instr in INSTRUMENTS:
        try:
            ticker = yf.Ticker(instr["ticker"])
            hist = ticker.history(period="1y")
            if hist.empty:
                logger.warning(f"No data for {instr['ticker']}")
                continue

            info = {}
            try:
                info = ticker.info or {}
            except Exception:
                pass

            last_close = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else None

            day_abs = round(last_close - prev_close, instr["decimals"]) if prev_close else None
            day_pct = round((last_close - prev_close) / prev_close * 100, 2) if prev_close else None

            week_ago = hist["Close"].iloc[-6] if len(hist) >= 6 else None
            month_ago = hist["Close"].iloc[-22] if len(hist) >= 22 else None
            ytd_start = hist[hist.index.year == hist.index[-1].year]["Close"].iloc[0] if not hist.empty else None

            week_pct  = round((last_close - float(week_ago)) / float(week_ago) * 100, 2) if week_ago is not None else None
            month_pct = round((last_close - float(month_ago)) / float(month_ago) * 100, 2) if month_ago is not None else None
            ytd_pct   = round((last_close - float(ytd_start)) / float(ytd_start) * 100, 2) if ytd_start is not None else None

            week52_high = float(hist["Close"].max())
            week52_low  = float(hist["Close"].min())
            last_date   = hist.index[-1].strftime("%d.%m.%Y")

            results.append({
                "ticker":      instr["ticker"],
                "name":        instr["name"],
                "decimals":    instr["decimals"],
                "prefix":      instr["prefix"],
                "last_close":  round(last_close, instr["decimals"]),
                "last_date":   last_date,
                "day_abs":     day_abs,
                "day_pct":     day_pct,
                "week_pct":    week_pct,
                "month_pct":   month_pct,
                "ytd_pct":     ytd_pct,
                "week52_high": round(week52_high, instr["decimals"]),
                "week52_low":  round(week52_low,  instr["decimals"]),
                "market_state": _market_state(info),
                "url": f"https://finance.yahoo.com/quote/{instr['ticker']}",
            })
            logger.info(f"  {instr['name']}: {last_close:.{instr['decimals']}f} ({'+' if day_pct and day_pct >= 0 else ''}{day_pct:.2f}% )" if day_pct else f"  {instr['name']}: {last_close:.{instr['decimals']}f}")
        except Exception as e:
            logger.warning(f"Fehler bei {instr['ticker']}: {e}")

    return results
