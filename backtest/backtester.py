import pandas as pd
import talib
from data.market_data import get_price_history
from config import PAPER_BALANCE, STOP_LOSS_PCT, TAKE_PROFIT_PCT


def run_rsi_strategy_backtest(
    symbol: str,
    period: str = "1y",
    initial_capital: float = PAPER_BALANCE,
    rsi_buy: float = 35,
    rsi_sell: float = 65,
) -> dict:
    """Backtestet eine einfache RSI-Strategie: Kauf wenn RSI < rsi_buy, Verkauf wenn RSI > rsi_sell."""
    df = get_price_history(symbol, period=period)
    close = df["Close"].values
    rsi_values = talib.RSI(close, timeperiod=14)
    df["RSI"] = rsi_values

    df = df.dropna(subset=["RSI"])

    capital = initial_capital
    shares = 0.0
    trades = []
    buy_price = 0.0

    for date, row in df.iterrows():
        price = float(row["Close"])
        rsi = float(row["RSI"])

        if shares == 0 and rsi < rsi_buy:
            invest = capital * 0.95
            shares = invest / price
            buy_price = price
            capital -= invest
            trades.append({
                "date": str(date.date()),
                "action": "buy",
                "price": round(price, 2),
                "shares": round(shares, 4),
                "rsi": round(rsi, 2),
            })

        elif shares > 0:
            pnl_pct = (price - buy_price) / buy_price
            if rsi > rsi_sell or pnl_pct <= -STOP_LOSS_PCT or pnl_pct >= TAKE_PROFIT_PCT:
                erlös = shares * price
                capital += erlös
                pnl = (price - buy_price) * shares
                reason = "RSI Signal" if rsi > rsi_sell else ("Stop-Loss" if pnl_pct <= -STOP_LOSS_PCT else "Take-Profit")
                trades.append({
                    "date": str(date.date()),
                    "action": "sell",
                    "price": round(price, 2),
                    "pnl": round(pnl, 2),
                    "pnl_pct": round(pnl_pct * 100, 2),
                    "grund": reason,
                })
                shares = 0.0

    if shares > 0:
        final_price = float(df["Close"].iloc[-1])
        capital += shares * final_price

    total_return = ((capital - initial_capital) / initial_capital) * 100
    sell_trades = [t for t in trades if t["action"] == "sell"]
    winning = [t for t in sell_trades if t.get("pnl", 0) > 0]

    return {
        "symbol": symbol,
        "zeitraum": period,
        "startkapital": initial_capital,
        "endkapital": round(capital, 2),
        "gesamtrendite_pct": round(total_return, 2),
        "total_trades": len(sell_trades),
        "gewinn_trades": len(winning),
        "verlust_trades": len(sell_trades) - len(winning),
        "win_rate_pct": round(len(winning) / len(sell_trades) * 100, 1) if sell_trades else 0,
        "strategie": f"RSI Kauf<{rsi_buy} / Verkauf>{rsi_sell}",
        "trades": trades[-10:],
    }
