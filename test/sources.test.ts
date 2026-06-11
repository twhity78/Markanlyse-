import { describe, it, expect } from "vitest";
import { loadFixture } from "../src/sources/fetchWithFallback.js";
import { fetchRealEstate } from "../src/sources/realEstate.js";
import { fetchIndustry } from "../src/sources/industry.js";
import type { RealEstateRegion } from "../src/types.js";

describe("loadFixture", () => {
  it("lädt stocks-Fixture", () => {
    const stocks = loadFixture<unknown[]>("stocks");
    expect(Array.isArray(stocks)).toBe(true);
    expect(stocks.length).toBeGreaterThan(0);
  });

  it("lädt crypto-Fixture", () => {
    const crypto = loadFixture<unknown[]>("crypto");
    expect(Array.isArray(crypto)).toBe(true);
    expect(crypto.length).toBeGreaterThan(0);
  });

  it("lädt real-estate-Fixture", () => {
    const re = loadFixture<RealEstateRegion[]>("real-estate");
    expect(Array.isArray(re)).toBe(true);
    expect(re[0]).toHaveProperty("region");
    expect(re[0]).toHaveProperty("pricePerSqm");
  });
});

describe("fetchRealEstate", () => {
  it("gibt alle Regionen zurück", () => {
    const section = fetchRealEstate(["Berlin", "München"]);
    expect(section.data.length).toBe(2);
    expect(section.meta.source).toBe("sample");
  });

  it("gibt alle Fixture-Daten zurück bei unbekannten Regionen", () => {
    const section = fetchRealEstate(["UnbekannteStadt"]);
    expect(section.data.length).toBeGreaterThan(0);
  });
});

describe("fetchIndustry", () => {
  it("gibt Sektor und Wettbewerber zurück", () => {
    const section = fetchIndustry({
      sector: "Software & Cloud",
      competitors: [
        { name: "SAP", ticker: "sap.de", notes: "Testnotiz" },
      ],
    });
    expect(section.data.sector).toBe("Software & Cloud");
    expect(section.data.competitors.length).toBe(1);
    expect(section.meta.source).toBe("sample");
  });
});
