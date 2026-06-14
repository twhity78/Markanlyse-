import pandas as pd
import talib
from config import RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL, BB_PERIOD, BB_STD


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = df["Close"].values
    volume = df["Volume"].values

    df["RSI"] = talib.RSI(close, timeperiod=RSI_PERIOD)
    df["MACD"], df["MACD_signal"], df["MACD_hist"] = talib.MACD(
        close, fastperiod=MACD_FAST, slowperiod=MACD_SLOW, signalperiod=MACD_SIGNAL
    )
    df["BB_upper"], df["BB_mid"], df["BB_lower"] = talib.BBANDS(
        close, timeperiod=BB_PERIOD, nbdevup=BB_STD, nbdevdn=BB_STD
    )
    df["SMA_20"] = talib.SMA(close, timeperiod=20)
    df["SMA_50"] = talib.SMA(close, timeperiod=50)
    df["EMA_12"] = talib.EMA(close, timeperiod=12)

    return df


def get_indicator_summary(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 2:
        return {}

    latest = df.iloc[-1]
    prev_close = df["Close"].iloc[-2]
    close = float(latest["Close"])

    summary = {
        "preis": round(close, 2),
        "rsi": round(float(latest["RSI"]), 2) if pd.notna(latest.get("RSI")) else None,
        "macd": round(float(latest["MACD"]), 4) if pd.notna(latest.get("MACD")) else None,
        "macd_signal": round(float(latest["MACD_signal"]), 4) if pd.notna(latest.get("MACD_signal")) else None,
        "macd_histogram": round(float(latest["MACD_hist"]), 4) if pd.notna(latest.get("MACD_hist")) else None,
        "bb_upper": round(float(latest["BB_upper"]), 2) if pd.notna(latest.get("BB_upper")) else None,
        "bb_lower": round(float(latest["BB_lower"]), 2) if pd.notna(latest.get("BB_lower")) else None,
        "bb_mid": round(float(latest["BB_mid"]), 2) if pd.notna(latest.get("BB_mid")) else None,
        "sma_20": round(float(latest["SMA_20"]), 2) if pd.notna(latest.get("SMA_20")) else None,
        "sma_50": round(float(latest["SMA_50"]), 2) if pd.notna(latest.get("SMA_50")) else None,
        "volumen": int(latest.get("Volume", 0)),
        "volumen_avg": int(df["Volume"].tail(20).mean()),
    }

    signals = []
    if summary["rsi"] is not None:
        if summary["rsi"] < 30:
            signals.append("RSI überverkauft (bullish)")
        elif summary["rsi"] > 70:
            signals.append("RSI überkauft (bearish)")

    if summary["macd"] is not None and summary["macd_signal"] is not None:
        if summary["macd"] > summary["macd_signal"]:
            signals.append("MACD bullish Crossover")
        else:
            signals.append("MACD bearish Crossover")

    if summary["bb_upper"] and summary["bb_lower"]:
        if close > summary["bb_upper"]:
            signals.append("Preis über oberem Bollinger Band (überkauft)")
        elif close < summary["bb_lower"]:
            signals.append("Preis unter unterem Bollinger Band (überverkauft)")

    if summary["sma_20"] and summary["sma_50"]:
        if summary["sma_20"] > summary["sma_50"]:
            signals.append("Goldenes Kreuz: SMA20 über SMA50 (bullish)")
        else:
            signals.append("Todeskreuz: SMA20 unter SMA50 (bearish)")

    summary["signale"] = signals
    return summary
