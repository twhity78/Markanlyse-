import { fetchWithTimeout, loadFixture } from "./fetchWithFallback.js";
import type { Quote, PricePoint, SourceMeta } from "../types.js";
import type { CryptoConfig } from "../config.js";
import { change1d, change7d, change30d, high52w, low52w } from "../metrics.js";

interface CoinMarket {
  id: string;
  name: string;
  current_price: number;
  market_cap: number;
  total_volume: number;
}

interface CryptoFixture {
  id: string;
  name: string;
  currency: string;
  marketCap: number;
  volume24h: number;
  history: PricePoint[];
}

function buildQuote(
  fx: CryptoFixture,
  override?: Partial<{ price: number; marketCap: number; volume24h: number }>
): Quote {
  const history = fx.history;
  const price = override?.price ?? history[history.length - 1]?.close ?? 0;
  return {
    symbol: fx.id,
    name: fx.name,
    currency: fx.currency.toUpperCase(),
    price,
    change1d: change1d(history),
    change7d: change7d(history),
    change30d: change30d(history),
    high52w: high52w(history),
    low52w: low52w(history),
    marketCap: override?.marketCap ?? fx.marketCap,
    volume: override?.volume24h ?? fx.volume24h,
    history,
  };
}

async function fetchCoinGeckoMarkets(
  ids: string[],
  vsCurrency: string
): Promise<CoinMarket[]> {
  const url =
    `https://api.coingecko.com/api/v3/coins/markets?vs_currency=${vsCurrency}` +
    `&ids=${ids.join(",")}&per_page=50&page=1`;
  const res = await fetchWithTimeout(url);
  if (!res.ok) throw new Error(`CoinGecko HTTP ${res.status}`);
  return (await res.json()) as CoinMarket[];
}

export async function fetchCrypto(configs: CryptoConfig[]): Promise<{
  quotes: Quote[];
  meta: SourceMeta;
}> {
  const fetchedAt = new Date().toISOString();
  const fixtures = loadFixture<CryptoFixture[]>("crypto");
  let source: "live" | "sample" = "live";
  let liveMarkets: CoinMarket[] = [];

  const vsCurrency = configs[0]?.vsCurrency ?? "eur";
  const ids = configs.map((c) => c.id);

  try {
    liveMarkets = await fetchCoinGeckoMarkets(ids, vsCurrency);
    if (liveMarkets.length === 0) throw new Error("empty response");
  } catch {
    source = "sample";
  }

  const quotes: Quote[] = configs.map((cfg) => {
    const fx =
      fixtures.find((f) => f.id === cfg.id) ??
      ({ id: cfg.id, name: cfg.name, currency: vsCurrency, marketCap: 0, volume24h: 0, history: [] } as CryptoFixture);
    if (source === "live") {
      const live = liveMarkets.find((m) => m.id === cfg.id);
      if (live) {
        return buildQuote(fx, {
          price: live.current_price,
          marketCap: live.market_cap,
          volume24h: live.total_volume,
        });
      }
    }
    return buildQuote(fx);
  });

  return { quotes, meta: { source, fetchedAt } };
}
