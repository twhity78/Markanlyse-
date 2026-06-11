import { describe, it, expect } from "vitest";
import {
  pctChange,
  sma,
  change1d,
  change7d,
  change30d,
  high52w,
  low52w,
  annualizedVolatility,
} from "../src/metrics.js";
import type { PricePoint } from "../src/types.js";

function pts(closes: number[]): PricePoint[] {
  return closes.map((close, i) => ({ date: `2026-01-${String(i + 1).padStart(2, "0")}`, close }));
}

describe("pctChange", () => {
  it("berechnet positive Veränderung", () => {
    expect(pctChange(100, 110)).toBeCloseTo(10);
  });
  it("berechnet negative Veränderung", () => {
    expect(pctChange(100, 90)).toBeCloseTo(-10);
  });
  it("gibt 0 zurück wenn Basis 0", () => {
    expect(pctChange(0, 100)).toBe(0);
  });
});

describe("sma", () => {
  it("berechnet Durchschnitt korrekt", () => {
    expect(sma(pts([100, 110, 120]), 3)).toBeCloseTo(110);
  });
  it("verwendet nur die letzten N Werte", () => {
    expect(sma(pts([100, 50, 110, 120]), 2)).toBeCloseTo(115);
  });
  it("gibt 0 für leere History zurück", () => {
    expect(sma([], 5)).toBe(0);
  });
});

describe("change1d/7d/30d", () => {
  it("change1d gibt 0 bei < 2 Punkten", () => {
    expect(change1d(pts([100]))).toBe(0);
  });
  it("change1d korrekt", () => {
    expect(change1d(pts([100, 105]))).toBeCloseTo(5);
  });
  it("change7d gibt 0 bei < 8 Punkten", () => {
    expect(change7d(pts([100, 102, 103]))).toBe(0);
  });
  it("change7d korrekt", () => {
    const h = pts([100, 101, 102, 103, 104, 105, 106, 110]);
    expect(change7d(h)).toBeCloseTo(10);
  });
  it("change30d gibt 0 bei < 31 Punkten", () => {
    expect(change30d(pts(Array(30).fill(100)))).toBe(0);
  });
});

describe("high52w / low52w", () => {
  it("findet Hoch korrekt", () => {
    expect(high52w(pts([100, 200, 150]))).toBe(200);
  });
  it("findet Tief korrekt", () => {
    expect(low52w(pts([100, 200, 50]))).toBe(50);
  });
  it("gibt 0 für leere History zurück", () => {
    expect(high52w([])).toBe(0);
    expect(low52w([])).toBe(0);
  });
});

describe("annualizedVolatility", () => {
  it("gibt 0 bei < 2 Punkten zurück", () => {
    expect(annualizedVolatility(pts([100]))).toBe(0);
  });
  it("gibt positive Zahl für volatile History zurück", () => {
    const v = annualizedVolatility(pts([100, 110, 95, 115, 105]));
    expect(v).toBeGreaterThan(0);
  });
});
