import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


def get_price_history(symbol: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"Keine Daten für {symbol} gefunden")
    df.index = df.index.tz_localize(None)
    return df


def get_current_price(symbol: str) -> float:
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info
    return float(info.last_price)


def get_company_info(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return {
        "name": info.get("longName", symbol),
        "sector": info.get("sector", "Unbekannt"),
        "industry": info.get("industry", "Unbekannt"),
        "market_cap": info.get("marketCap", 0),
        "pe_ratio": info.get("trailingPE", None),
        "52w_high": info.get("fiftyTwoWeekHigh", None),
        "52w_low": info.get("fiftyTwoWeekLow", None),
        "analyst_target": info.get("targetMeanPrice", None),
        "recommendation": info.get("recommendationKey", "none"),
    }


def get_news(symbol: str, limit: int = 5) -> list[dict]:
    ticker = yf.Ticker(symbol)
    news = ticker.news or []
    result = []
    for item in news[:limit]:
        content = item.get("content", {})
        result.append({
            "title": content.get("title", item.get("title", "")),
            "summary": content.get("summary", ""),
            "published": content.get("pubDate", ""),
        })
    return result
