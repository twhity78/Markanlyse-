import { fetchWithTimeout, loadFixture } from "./fetchWithFallback.js";
import type { Quote, PricePoint, SourceMeta } from "../types.js";
import type { StockConfig } from "../config.js";
import {
  change1d,
  change7d,
  change30d,
  high52w,
  low52w,
} from "../metrics.js";

interface StockFixture {
  symbol: string;
  name: string;
  currency: string;
  history: PricePoint[];
}

function buildQuote(fixture: StockFixture, source: "live" | "sample"): Quote {
  const { symbol, name, currency, history } = fixture;
  const last = history[history.length - 1];
  const price = last?.close ?? 0;
  return {
    symbol,
    name,
    currency,
    price,
    change1d: change1d(history),
    change7d: change7d(history),
    change30d: change30d(history),
    high52w: high52w(history),
    low52w: low52w(history),
    history,
  };
  void source;
}

async function fetchStooqCsv(symbol: string): Promise<PricePoint[]> {
  const url = `https://stooq.com/q/d/l/?s=${encodeURIComponent(symbol)}&i=d`;
  const res = await fetchWithTimeout(url);
  if (!res.ok) throw new Error(`stooq HTTP ${res.status}`);
  const text = await res.text();
  const lines = text.trim().split("\n").slice(1);
  return lines
    .map((line) => {
      const cols = line.split(",");
      const date = cols[0] ?? "";
      const close = parseFloat(cols[4] ?? "");
      return { date, close };
    })
    .filter((p) => p.date && !isNaN(p.close));
}

export async function fetchStocks(configs: StockConfig[]): Promise<{
  quotes: Quote[];
  meta: SourceMeta;
}> {
  const fetchedAt = new Date().toISOString();
  const quotes: Quote[] = [];
  let source: "live" | "sample" = "live";

  const fixtures = loadFixture<StockFixture[]>("stocks");

  for (const cfg of configs) {
    const fixture = fixtures.find((f) => f.symbol === cfg.symbol) ?? {
      symbol: cfg.symbol,
      name: cfg.name,
      currency: cfg.currency,
      history: [],
    };
    try {
      const history = await fetchStooqCsv(cfg.symbol);
      if (history.length < 5) throw new Error("too few data points");
      quotes.push(buildQuote({ ...fixture, history }, "live"));
    } catch {
      source = "sample";
      quotes.push(buildQuote(fixture, "sample"));
    }
  }

  return { quotes, meta: { source, fetchedAt } };
}
