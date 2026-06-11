import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

export interface StockConfig {
  symbol: string;
  name: string;
  currency: string;
}

export interface CryptoConfig {
  id: string;
  name: string;
  vsCurrency: string;
}

export interface CompetitorConfig {
  name: string;
  ticker?: string;
  notes: string;
}

export interface MarketConfig {
  stocks: StockConfig[];
  crypto: CryptoConfig[];
  realEstate: { regions: string[] };
  industry: { sector: string; competitors: CompetitorConfig[] };
}

export function loadConfig(): MarketConfig {
  const configPath = resolve(__dirname, "../market-config.json");
  const raw = readFileSync(configPath, "utf-8");
  return JSON.parse(raw) as MarketConfig;
}
