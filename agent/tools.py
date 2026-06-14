import json
from data.market_data import get_price_history, get_current_price, get_company_info, get_news
from data.indicators import add_indicators, get_indicator_summary
from agent.memory import (
    get_portfolio, record_trade, get_trade_history,
    get_performance_summary, update_balance
)
from config import PAPER_BALANCE, MAX_POSITION_SIZE, STOP_LOSS_PCT, TAKE_PROFIT_PCT


TOOLS = [
    {
        "name": "analyse_markt",
        "description": (
            "Analysiert einen Markt/Aktie mit technischen Indikatoren (RSI, MACD, Bollinger Bänder, SMA). "
            "Gibt aktuelle Kursdaten und Handelssignale zurück."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Ticker-Symbol (z.B. AAPL, TSLA, BTC-USD, ETH-USD)"
                },
                "zeitraum": {
                    "type": "string",
                    "description": "Analysezeitraum: 1mo, 3mo, 6mo, 1y",
                    "default": "3mo"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "aktie_info",
        "description": "Gibt Unternehmensinformationen, Analysten-Empfehlungen und Kursziele zurück.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Ticker-Symbol"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "nachrichten",
        "description": "Holt aktuelle Nachrichten zu einem Symbol für Sentiment-Analyse.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "anzahl": {"type": "integer", "default": 5}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "kaufen",
        "description": (
            "Kauft eine Aktie (Paper Trading). Berechnet automatisch die optimale Positionsgröße "
            "basierend auf Risikomanagement-Regeln (max 20% des Portfolios)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "begruendung": {
                    "type": "string",
                    "description": "Warum wird gekauft? (wird gespeichert für Lernzwecke)"
                },
                "risiko_level": {
                    "type": "string",
                    "enum": ["konservativ", "normal", "aggressiv"],
                    "description": "Bestimmt Positionsgröße: konservativ=5%, normal=10%, aggressiv=20%"
                }
            },
            "required": ["symbol", "begruendung"]
        }
    },
    {
        "name": "verkaufen",
        "description": "Verkauft eine gehaltene Position (Paper Trading).",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "anteil": {
                    "type": "number",
                    "description": "Anteil der Position zu verkaufen (0.0 bis 1.0). Default: 1.0 = alles"
                },
                "begruendung": {"type": "string"}
            },
            "required": ["symbol", "begruendung"]
        }
    },
    {
        "name": "portfolio",
        "description": "Zeigt aktuelles Portfolio, Cash-Balance, offene Positionen und Trade-Historie.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "performance",
        "description": "Gibt eine detaillierte Performance-Auswertung aller bisherigen Trades zurück.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Optional: Nur Performance für dieses Symbol"
                }
            }
        }
    }
]


def execute_tool(name: str, inputs: dict) -> str:
    try:
        if name == "analyse_markt":
            return _analyse_markt(inputs)
        elif name == "aktie_info":
            return _aktie_info(inputs)
        elif name == "nachrichten":
            return _nachrichten(inputs)
        elif name == "kaufen":
            return _kaufen(inputs)
        elif name == "verkaufen":
            return _verkaufen(inputs)
        elif name == "portfolio":
            return _portfolio(inputs)
        elif name == "performance":
            return _performance(inputs)
        else:
            return f"Unbekanntes Tool: {name}"
    except Exception as e:
        return f"Fehler bei Tool '{name}': {str(e)}"


def _analyse_markt(inputs: dict) -> str:
    symbol = inputs["symbol"].upper()
    zeitraum = inputs.get("zeitraum", "3mo")
    df = get_price_history(symbol, period=zeitraum)
    df = add_indicators(df)
    summary = get_indicator_summary(df)

    preis_vortag = df["Close"].iloc[-2] if len(df) >= 2 else df["Close"].iloc[-1]
    veraenderung = ((summary["preis"] - preis_vortag) / preis_vortag) * 100

    result = {
        "symbol": symbol,
        "aktueller_preis": summary["preis"],
        "veraenderung_pct": round(veraenderung, 2),
        "indikatoren": {
            "RSI": summary.get("rsi"),
            "MACD": summary.get("macd"),
            "MACD_Signal": summary.get("macd_signal"),
            "BB_Oben": summary.get("bb_upper"),
            "BB_Unten": summary.get("bb_lower"),
            "SMA_20": summary.get("sma_20"),
            "SMA_50": summary.get("sma_50"),
        },
        "volumen": summary.get("volumen"),
        "volumen_durchschnitt": summary.get("volumen_avg"),
        "signale": summary.get("signale", []),
        "datenpunkte": len(df),
    }
    return json.dumps(result, ensure_ascii=False, indent=2)


def _aktie_info(inputs: dict) -> str:
    symbol = inputs["symbol"].upper()
    info = get_company_info(symbol)
    return json.dumps(info, ensure_ascii=False, indent=2)


def _nachrichten(inputs: dict) -> str:
    symbol = inputs["symbol"].upper()
    anzahl = inputs.get("anzahl", 5)
    news = get_news(symbol, limit=anzahl)
    return json.dumps({"symbol": symbol, "nachrichten": news}, ensure_ascii=False, indent=2)


def _kaufen(inputs: dict) -> str:
    symbol = inputs["symbol"].upper()
    begruendung = inputs["begruendung"]
    risiko = inputs.get("risiko_level", "normal")

    portfolio = get_portfolio()
    balance = portfolio.get("balance")
    if balance is None:
        balance = PAPER_BALANCE
        update_balance(balance)

    # Positionsgröße basierend auf Risiko
    risiko_map = {"konservativ": 0.05, "normal": 0.10, "aggressiv": 0.20}
    position_pct = risiko_map.get(risiko, 0.10)

    preis = get_current_price(symbol)
    invest_betrag = balance * position_pct
    shares = invest_betrag / preis

    if invest_betrag > balance:
        return json.dumps({"fehler": f"Nicht genug Kapital. Verfügbar: ${balance:.2f}"})

    trade = record_trade(symbol, "buy", round(shares, 6), preis, begruendung)

    stop_loss = round(preis * (1 - STOP_LOSS_PCT), 2)
    take_profit = round(preis * (1 + TAKE_PROFIT_PCT), 2)

    return json.dumps({
        "status": "GEKAUFT",
        "symbol": symbol,
        "shares": round(shares, 4),
        "preis": preis,
        "investiert": round(invest_betrag, 2),
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "verbleibendes_kapital": round(balance - invest_betrag, 2),
    }, ensure_ascii=False, indent=2)


def _verkaufen(inputs: dict) -> str:
    symbol = inputs["symbol"].upper()
    anteil = inputs.get("anteil", 1.0)
    begruendung = inputs["begruendung"]

    portfolio = get_portfolio()
    pos = portfolio.get("positions", {}).get(symbol)

    if not pos or pos.get("shares", 0) <= 0:
        return json.dumps({"fehler": f"Keine offene Position in {symbol}"})

    shares_to_sell = pos["shares"] * anteil
    preis = get_current_price(symbol)
    trade = record_trade(symbol, "sell", round(shares_to_sell, 6), preis, begruendung)

    avg_price = pos.get("avg_price", preis)
    pnl = (preis - avg_price) * shares_to_sell
    pnl_pct = ((preis - avg_price) / avg_price) * 100

    return json.dumps({
        "status": "VERKAUFT",
        "symbol": symbol,
        "shares": round(shares_to_sell, 4),
        "preis": preis,
        "erlös": round(shares_to_sell * preis, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
    }, ensure_ascii=False, indent=2)


def _portfolio(inputs: dict) -> str:
    portfolio = get_portfolio()
    balance = portfolio.get("balance", PAPER_BALANCE)

    positions_detail = {}
    for sym, pos in portfolio.get("positions", {}).items():
        if pos.get("shares", 0) > 0:
            try:
                current = get_current_price(sym)
                value = pos["shares"] * current
                pnl = (current - pos["avg_price"]) * pos["shares"]
                positions_detail[sym] = {
                    "shares": round(pos["shares"], 4),
                    "kaufpreis_avg": round(pos["avg_price"], 2),
                    "aktuell": current,
                    "wert": round(value, 2),
                    "pnl": round(pnl, 2),
                }
            except Exception:
                positions_detail[sym] = pos

    total_value = balance + sum(p.get("wert", 0) for p in positions_detail.values())

    return json.dumps({
        "cash": round(balance, 2),
        "positionen": positions_detail,
        "portfolio_gesamtwert": round(total_value, 2),
        "startkapital": PAPER_BALANCE,
        "gesamtrendite_pct": round(((total_value - PAPER_BALANCE) / PAPER_BALANCE) * 100, 2),
    }, ensure_ascii=False, indent=2)


def _performance(inputs: dict) -> str:
    symbol = inputs.get("symbol")
    history = get_trade_history(symbol=symbol, limit=50)
    summary = get_performance_summary()
    return json.dumps({
        "zusammenfassung": summary,
        "letzte_trades": history,
    }, ensure_ascii=False, indent=2)
