import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TRADING_MODE = os.getenv("TRADING_MODE", "paper")
DEFAULT_SYMBOL = os.getenv("DEFAULT_SYMBOL", "AAPL")
PAPER_BALANCE = float(os.getenv("PAPER_BALANCE", "10000"))

CLAUDE_MODEL = "claude-sonnet-4-6"

# Technische Indikatoren Einstellungen
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2.0

# Risikomanagement
MAX_POSITION_SIZE = 0.20   # max 20% des Portfolios pro Trade
STOP_LOSS_PCT = 0.05       # 5% Stop-Loss
TAKE_PROFIT_PCT = 0.10     # 10% Take-Profit
