import anthropic
from agent.tools import TOOLS, execute_tool
from agent.memory import get_performance_summary
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, PAPER_BALANCE

SYSTEM_PROMPT = """Du bist ein erfahrener Quantitative Trading Agent. Deine Aufgabe ist es:

1. **Marktanalyse**: Analysiere Aktien und Kryptowährungen mit technischen Indikatoren
2. **Handelsentscheidungen**: Treffe fundierte Kauf/Verkauf-Entscheidungen basierend auf:
   - Technische Analyse (RSI, MACD, Bollinger Bänder, Moving Averages)
   - Markt-Sentiment (Nachrichten)
   - Risikomanagement (Stop-Loss, Take-Profit, Positionsgröße)
3. **Portfolio-Management**: Überwache und optimiere das Portfolio
4. **Lernen**: Analysiere vergangene Trades und verbessere deine Strategie

## Handelsprinzipien:
- Kaufe NIE auf FOMO (Fear of Missing Out) - warte auf klare Signale
- Setze immer Stop-Loss und Take-Profit Level
- Diversifiziere - max 20% des Portfolios in einer Position
- Bei Unsicherheit: NICHT handeln (cash is king)
- Analysiere IMMER zuerst Indikatoren UND Nachrichten vor einer Entscheidung

## Risikomanagement-Regeln:
- Stop-Loss: 5% unter Kaufpreis
- Take-Profit: 10% über Kaufpreis
- Positionsgröße: konservativ=5%, normal=10%, aggressiv=20% des Portfolios
- Niemals mehr als 3 offene Positionen gleichzeitig

## Antwortformat:
Erkläre deine Analyse und Entscheidung KLAR auf Deutsch. Zeige dein Reasoning."""


class TradingAgent:
    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY nicht gesetzt. Kopiere .env.example nach .env und trage deinen API Key ein."
            )
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.conversation_history = []

    def _build_context(self) -> str:
        perf = get_performance_summary()
        balance = perf.get("balance", PAPER_BALANCE)
        positions = perf.get("positions", {})
        active = {s: p for s, p in positions.items() if p.get("shares", 0) > 0}

        context = f"\n[Aktueller Kontext]\n"
        context += f"Modus: Paper Trading (kein echtes Geld)\n"
        context += f"Cash: ${balance:,.2f}\n"
        context += f"Startkapital: ${PAPER_BALANCE:,.2f}\n"
        context += f"Offene Positionen: {len(active)}\n"
        if active:
            context += f"Positionen: {', '.join(active.keys())}\n"
        context += f"Gesamte Trades: {perf.get('total_trades', 0)}\n"
        return context

    def run(self, user_input: str) -> str:
        context = self._build_context()
        enriched_input = user_input + context

        self.conversation_history.append({
            "role": "user",
            "content": enriched_input
        })

        while True:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.conversation_history,
            )

            # Tool-Aufrufe verarbeiten
            if response.stop_reason == "tool_use":
                assistant_message = {"role": "assistant", "content": response.content}
                self.conversation_history.append(assistant_message)

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = execute_tool(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })
                continue

            # Finale Antwort
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            self.conversation_history.append({
                "role": "assistant",
                "content": final_text
            })

            # Konversationshistorie begrenzen (letzte 20 Nachrichten)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            return final_text
