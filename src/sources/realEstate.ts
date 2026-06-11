import { loadFixture } from "./fetchWithFallback.js";
import type { RealEstateRegion, DomainSection } from "../types.js";

interface RealEstateFixture extends RealEstateRegion {
  notes?: string;
}

export function fetchRealEstate(regions: string[]): DomainSection<RealEstateRegion[]> {
  const all = loadFixture<RealEstateFixture[]>("real-estate");
  const data = regions
    .map((r) => all.find((f) => f.region === r))
    .filter((f): f is RealEstateRegion => f !== undefined);

  // If requested regions aren't in fixtures, include all fixture data
  const result = data.length > 0 ? data : (all as RealEstateRegion[]);

  return {
    title: "Immobilienmarkt",
    meta: { source: "sample", fetchedAt: new Date().toISOString() },
    data: result,
  };
}
