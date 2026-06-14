# Markanlyse Trading Agent

Ein KI-gestützter Trading Agent powered by **Claude (Anthropic)**.

## Features

- **KI-Analyse** mit Claude: Technische Indikatoren + Nachrichten-Sentiment
- **Paper Trading**: Teste Strategien ohne echtes Geld zu riskieren
- **Technische Indikatoren**: RSI, MACD, Bollinger Bänder, SMA/EMA
- **Risikomanagement**: Automatische Stop-Loss und Take-Profit Level
- **Backtesting**: Teste Strategien auf historischen Daten
- **Portfolio-Tracking**: Verfolge alle Trades und Performance

## Setup

```bash
# 1. Dependencies installieren
pip install -r requirements.txt

# 2. Konfiguration
cp .env.example .env
# Trage deinen Anthropic API Key in .env ein
# API Key holen: https://console.anthropic.com

# 3. Starten
python main.py
```

## Nutzung

```
analysiere AAPL          → Marktanalyse mit Indikatoren
kaufe TSLA               → KI entscheidet Kauf-Strategie
verkaufe AAPL            → Position schließen
portfolio                → Portfolio-Übersicht
backtest AAPL            → RSI-Strategie backtesten
nachrichten MSFT         → Aktuelle News
```

## Architektur

```
agent/
├── trading_agent.py    # Claude-powered Agent (Tool Use)
├── tools.py            # Trading-Tools die Claude nutzen kann
└── memory.py           # Trade-Gedächtnis (JSON)
data/
├── market_data.py      # Marktdaten via yfinance
└── indicators.py       # Technische Indikatoren via pandas-ta
backtest/
└── backtester.py       # Strategie-Backtesting
main.py                 # CLI Einstiegspunkt
```

## Hinweis

Dies ist ein **Paper Trading** System — kein echtes Geld wird bewegt.
Für Live-Trading müsste eine Broker-API (z.B. Alpaca, Interactive Brokers) integriert werden.
