export interface SourceMeta {
  source: "live" | "sample";
  fetchedAt: string;
}

export interface PricePoint {
  date: string;
  close: number;
}

export interface Quote {
  symbol: string;
  name: string;
  currency: string;
  price: number;
  change1d: number;
  change7d: number;
  change30d: number;
  high52w: number;
  low52w: number;
  volume?: number;
  marketCap?: number;
  history: PricePoint[];
}

export interface RealEstateRegion {
  region: string;
  pricePerSqm: number;
  changeYoY: number;
  change5y: number;
  year: number;
}

export interface Competitor {
  name: string;
  ticker?: string;
  notes: string;
  quote?: Quote;
}

export interface DomainSection<T> {
  title: string;
  meta: SourceMeta;
  data: T;
}

export interface Report {
  generatedAt: string;
  stocks: DomainSection<Quote[]>;
  crypto: DomainSection<Quote[]>;
  realEstate: DomainSection<RealEstateRegion[]>;
  industry: DomainSection<{ sector: string; competitors: Competitor[] }>;
}
