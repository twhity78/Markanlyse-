#!/usr/bin/env python3
"""
Markanlyse Trading Agent
Ein KI-gestützter Trading Agent powered by Claude
"""

import sys
import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table
from rich import print as rprint

console = Console()


def show_banner():
    banner = Text()
    banner.append("  MARKANLYSE TRADING AGENT  ", style="bold white on blue")
    console.print(Panel(banner, expand=False))
    console.print("[dim]Powered by Claude AI | Paper Trading Modus[/dim]\n")


def show_help():
    table = Table(title="Verfügbare Befehle", show_header=True)
    table.add_column("Befehl", style="cyan")
    table.add_column("Beschreibung")

    commands = [
        ("analysiere AAPL", "Marktanalyse für AAPL mit Indikatoren"),
        ("kaufe TSLA", "KI entscheidet ob und wie viel zu kaufen"),
        ("verkaufe AAPL", "Position schließen"),
        ("portfolio", "Aktuelles Portfolio anzeigen"),
        ("backtest AAPL", "RSI-Strategie auf historischen Daten testen"),
        ("nachrichten MSFT", "Aktuelle News abrufen"),
        ("hilfe", "Diese Hilfe anzeigen"),
        ("exit / quit", "Programm beenden"),
    ]
    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print(table)
    console.print()


def run_backtest(symbol: str):
    from backtest.backtester import run_rsi_strategy_backtest
    console.print(f"[yellow]Backteste RSI-Strategie für {symbol} (1 Jahr)...[/yellow]")
    result = run_rsi_strategy_backtest(symbol.upper(), period="1y")

    if "fehler" in result:
        console.print(f"[red]Fehler: {result['fehler']}[/red]")
        return

    table = Table(title=f"Backtest Ergebnis: {result['symbol']}")
    table.add_column("Metrik", style="cyan")
    table.add_column("Wert", style="bold")

    rendite_color = "green" if result["gesamtrendite_pct"] > 0 else "red"
    table.add_row("Startkapital", f"${result['startkapital']:,.2f}")
    table.add_row("Endkapital", f"${result['endkapital']:,.2f}")
    table.add_row("Gesamtrendite", f"[{rendite_color}]{result['gesamtrendite_pct']}%[/{rendite_color}]")
    table.add_row("Total Trades", str(result["total_trades"]))
    table.add_row("Gewinn-Trades", f"[green]{result['gewinn_trades']}[/green]")
    table.add_row("Verlust-Trades", f"[red]{result['verlust_trades']}[/red]")
    table.add_row("Win-Rate", f"{result['win_rate_pct']}%")
    table.add_row("Strategie", result["strategie"])
    console.print(table)


def main():
    show_banner()

    try:
        from agent.trading_agent import TradingAgent
        agent = TradingAgent()
    except ValueError as e:
        console.print(f"[bold red]Konfigurationsfehler:[/bold red] {e}")
        console.print("\n[yellow]Setup:[/yellow]")
        console.print("  1. cp .env.example .env")
        console.print("  2. Trage deinen Anthropic API Key in .env ein")
        console.print("  3. Starte das Programm erneut")
        sys.exit(1)

    show_help()
    console.print("[green]Trading Agent bereit. Starte eine Analyse oder gib einen Befehl ein.[/green]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]Du[/bold cyan]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Auf Wiedersehen![/yellow]")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in ("exit", "quit", "beenden", "q"):
            console.print("[yellow]Auf Wiedersehen![/yellow]")
            break

        if lower in ("hilfe", "help", "?"):
            show_help()
            continue

        if lower.startswith("backtest "):
            symbol = lower.replace("backtest ", "").strip().upper()
            run_backtest(symbol)
            continue

        console.print("[dim]Agent denkt...[/dim]")
        try:
            response = agent.run(user_input)
            console.print(Panel(
                response,
                title="[bold green]Trading Agent[/bold green]",
                border_style="green"
            ))
        except Exception as e:
            console.print(f"[bold red]Fehler:[/bold red] {e}")

        console.print()


if __name__ == "__main__":
    main()
