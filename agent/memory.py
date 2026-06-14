import json
import os
from datetime import datetime

MEMORY_FILE = "trades/memory.json"


def _load() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {"trades": [], "performance": [], "balance": None, "positions": {}}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def _save(data: dict):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def get_portfolio() -> dict:
    return _load()


def update_balance(balance: float):
    data = _load()
    data["balance"] = balance
    _save(data)


def record_trade(symbol: str, action: str, shares: float, price: float, reason: str):
    data = _load()
    trade = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "action": action,
        "shares": shares,
        "price": price,
        "total": round(shares * price, 2),
        "reason": reason,
    }
    data["trades"].append(trade)

    # Position aktualisieren
    pos = data["positions"].get(symbol, {"shares": 0, "avg_price": 0})
    if action == "buy":
        total_shares = pos["shares"] + shares
        total_cost = (pos["shares"] * pos["avg_price"]) + (shares * price)
        pos["shares"] = total_shares
        pos["avg_price"] = total_cost / total_shares if total_shares > 0 else 0
        data["balance"] = (data["balance"] or 0) - trade["total"]
    elif action == "sell":
        pos["shares"] = max(0, pos["shares"] - shares)
        data["balance"] = (data["balance"] or 0) + trade["total"]
        if pos["shares"] == 0:
            pos["avg_price"] = 0

    data["positions"][symbol] = pos
    _save(data)
    return trade


def get_trade_history(symbol: str = None, limit: int = 20) -> list:
    data = _load()
    trades = data["trades"]
    if symbol:
        trades = [t for t in trades if t["symbol"] == symbol]
    return trades[-limit:]


def get_performance_summary() -> dict:
    data = _load()
    trades = data["trades"]
    if not trades:
        return {"total_trades": 0, "balance": data.get("balance"), "positions": {}}

    buys = [t for t in trades if t["action"] == "buy"]
    sells = [t for t in trades if t["action"] == "sell"]

    return {
        "total_trades": len(trades),
        "total_buys": len(buys),
        "total_sells": len(sells),
        "balance": data.get("balance"),
        "positions": data.get("positions", {}),
        "last_trade": trades[-1] if trades else None,
    }
