import type { PricePoint } from "./types.js";

export function pctChange(from: number, to: number): number {
  if (from === 0) return 0;
  return ((to - from) / Math.abs(from)) * 100;
}

export function lastN(history: PricePoint[], n: number): PricePoint[] {
  return history.slice(-n);
}

export function sma(history: PricePoint[], period: number): number {
  const slice = lastN(history, period);
  if (slice.length === 0) return 0;
  const sum = slice.reduce((acc, p) => acc + p.close, 0);
  return sum / slice.length;
}

export function annualizedVolatility(history: PricePoint[]): number {
  if (history.length < 2) return 0;
  const returns: number[] = [];
  for (let i = 1; i < history.length; i++) {
    const prev = history[i - 1];
    const curr = history[i];
    if (prev && curr && prev.close > 0) {
      returns.push(Math.log(curr.close / prev.close));
    }
  }
  if (returns.length === 0) return 0;
  const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
  const variance = returns.reduce((a, r) => a + (r - mean) ** 2, 0) / returns.length;
  return Math.sqrt(variance * 252) * 100;
}

export function high52w(history: PricePoint[]): number {
  const slice = lastN(history, 252);
  if (slice.length === 0) return 0;
  return Math.max(...slice.map((p) => p.close));
}

export function low52w(history: PricePoint[]): number {
  const slice = lastN(history, 252);
  if (slice.length === 0) return 0;
  return Math.min(...slice.map((p) => p.close));
}

export function change1d(history: PricePoint[]): number {
  if (history.length < 2) return 0;
  const prev = history[history.length - 2];
  const curr = history[history.length - 1];
  if (!prev || !curr) return 0;
  return pctChange(prev.close, curr.close);
}

export function change7d(history: PricePoint[]): number {
  if (history.length < 8) return 0;
  const prev = history[history.length - 8];
  const curr = history[history.length - 1];
  if (!prev || !curr) return 0;
  return pctChange(prev.close, curr.close);
}

export function change30d(history: PricePoint[]): number {
  if (history.length < 31) return 0;
  const prev = history[history.length - 31];
  const curr = history[history.length - 1];
  if (!prev || !curr) return 0;
  return pctChange(prev.close, curr.close);
}
