import React from "react";
import type { Report, Quote, RealEstateRegion } from "../types.js";
import type { IndustryData } from "../sources/industry.js";

function fmt(n: number, decimals = 2): string {
  return n.toLocaleString("de-DE", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function fmtLarge(n: number): string {
  if (n >= 1e12) return `${(n / 1e12).toFixed(2).replace(".", ",")} Bio.`;
  if (n >= 1e9) return `${(n / 1e9).toFixed(2).replace(".", ",")} Mrd.`;
  if (n >= 1e6) return `${(n / 1e6).toFixed(2).replace(".", ",")} Mio.`;
  return fmt(n, 0);
}

interface PctProps { value: number }
function Pct({ value }: PctProps) {
  const sign = value >= 0 ? "+" : "";
  const color = value >= 0 ? "#16a34a" : "#dc2626";
  return <span style={{ color }}>{sign}{fmt(value)}%</span>;
}

interface SparklineProps { values: number[]; width?: number; height?: number }
function Sparkline({ values, width = 120, height = 32 }: SparklineProps) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = width / (values.length - 1);
  const pts = values
    .map((v, i) => `${(i * step).toFixed(1)},${(height - ((v - min) / range) * height).toFixed(1)}`)
    .join(" ");
  const last = values[values.length - 1] ?? 0;
  const color = last >= (values[0] ?? 0) ? "#16a34a" : "#dc2626";
  return (
    <svg width={width} height={height} style={{ display: "block" }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" />
    </svg>
  );
}

interface SampleBadgeProps { source: "live" | "sample" }
function SampleBadge({ source }: SampleBadgeProps) {
  if (source === "live") return null;
  return (
    <span style={{ fontSize: "0.75em", background: "#fef3c7", color: "#92400e", padding: "2px 6px", borderRadius: 4, marginLeft: 8 }}>
      Beispieldaten
    </span>
  );
}

interface SectionProps { title: string; emoji: string; source: "live" | "sample"; children: React.ReactNode }
function Section({ title, emoji, source, children }: SectionProps) {
  return (
    <section style={{ marginBottom: 40 }}>
      <h2 style={{ borderBottom: "2px solid #e5e7eb", paddingBottom: 8, display: "flex", alignItems: "center", gap: 8 }}>
        <span>{emoji}</span> {title} <SampleBadge source={source} />
      </h2>
      {children}
    </section>
  );
}

function QuoteTable({ quotes }: { quotes: Quote[] }) {
  return (
    <table style={{ borderCollapse: "collapse", width: "100%", fontSize: "0.9em" }}>
      <thead>
        <tr style={{ background: "#f9fafb" }}>
          {["Symbol", "Name", "Kurs", "1T", "7T", "30T", "52W-H", "52W-T", "Verlauf"].map((h) => (
            <th key={h} style={{ padding: "8px 12px", textAlign: h === "Verlauf" ? "center" : "right", borderBottom: "1px solid #e5e7eb", ...(h === "Symbol" || h === "Name" ? { textAlign: "left" } : {}) }}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {quotes.map((q, i) => (
          <tr key={q.symbol} style={{ background: i % 2 === 0 ? "#fff" : "#f9fafb" }}>
            <td style={{ padding: "8px 12px", fontFamily: "monospace" }}>{q.symbol}</td>
            <td style={{ padding: "8px 12px" }}>{q.name}</td>
            <td style={{ padding: "8px 12px", textAlign: "right" }}>{fmt(q.price)} {q.currency}</td>
            <td style={{ padding: "8px 12px", textAlign: "right" }}><Pct value={q.change1d} /></td>
            <td style={{ padding: "8px 12px", textAlign: "right" }}><Pct value={q.change7d} /></td>
            <td style={{ padding: "8px 12px", textAlign: "right" }}><Pct value={q.change30d} /></td>
            <td style={{ padding: "8px 12px", textAlign: "right" }}>{fmt(q.high52w)}</td>
            <td style={{ padding: "8px 12px", textAlign: "right" }}>{fmt(q.low52w)}</td>
            <td style={{ padding: "8px 12px", textAlign: "center" }}>
              <Sparkline values={q.history.map((p) => p.close)} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function RealEstateTable({ regions }: { regions: RealEstateRegion[] }) {
  return (
    <table style={{ borderCollapse: "collapse", width: "100%", fontSize: "0.9em" }}>
      <thead>
        <tr style={{ background: "#f9fafb" }}>
          {["Region", "€/m²", "Δ YoY", "Δ 5 Jahre"].map((h) => (
            <th key={h} style={{ padding: "8px 12px", textAlign: h === "Region" ? "left" : "right", borderBottom: "1px solid #e5e7eb" }}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {regions.map((r, i) => (
          <tr key={r.region} style={{ background: i % 2 === 0 ? "#fff" : "#f9fafb" }}>
            <td style={{ padding: "8px 12px" }}>{r.region}</td>
            <td style={{ padding: "8px 12px", textAlign: "right" }}>{fmt(r.pricePerSqm, 0)}</td>
            <td style={{ padding: "8px 12px", textAlign: "right" }}><Pct value={r.changeYoY} /></td>
            <td style={{ padding: "8px 12px", textAlign: "right" }}><Pct value={r.change5y} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function ReportHtml({ report }: { report: Report }) {
  const date = new Date(report.generatedAt).toLocaleDateString("de-DE", {
    weekday: "long", year: "numeric", month: "long", day: "numeric",
  });
  const indData = report.industry.data as IndustryData;
  const ss = indData.sectorStats;

  return (
    <html lang="de">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{`Marktbericht — ${date}`}</title>
        <style>{`
          * { box-sizing: border-box; }
          body { font-family: system-ui, -apple-system, sans-serif; max-width: 1100px; margin: 0 auto; padding: 24px; color: #111827; }
          h1 { font-size: 1.8em; margin-bottom: 4px; }
          .meta { color: #6b7280; font-size: 0.85em; margin-bottom: 32px; }
          table { border-collapse: collapse; width: 100%; font-size: 0.9em; }
          th, td { padding: 8px 12px; }
          th { border-bottom: 1px solid #e5e7eb; }
          .trend-pill { display: inline-block; background: #eff6ff; color: #1d4ed8; padding: 3px 10px; border-radius: 99px; font-size: 0.82em; margin: 2px; }
          .comp-card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; }
          .comp-name { font-weight: 600; font-size: 1.05em; }
          .comp-ticker { font-family: monospace; color: #6b7280; margin-left: 6px; font-size: 0.9em; }
          footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 0.8em; }
        `}</style>
      </head>
      <body>
        <h1>Marktbericht</h1>
        <div className="meta">Erstellt am {date} · {report.generatedAt}</div>

        <Section title="Aktienmärkte" emoji="📈" source={report.stocks.meta.source}>
          <QuoteTable quotes={report.stocks.data} />
        </Section>

        <Section title="Kryptomärkte" emoji="🪙" source={report.crypto.meta.source}>
          <QuoteTable quotes={report.crypto.data} />
        </Section>

        <Section title="Immobilienmarkt" emoji="🏠" source={report.realEstate.meta.source}>
          <RealEstateTable regions={report.realEstate.data} />
          <p style={{ color: "#6b7280", fontSize: "0.82em", marginTop: 8 }}>
            Quelle: Statistische Schätzungen auf Basis von Destatis-Daten. Stand: {report.realEstate.data[0]?.year ?? ""}.
          </p>
        </Section>

        <Section title={`Branchen- & Wettbewerbsanalyse — ${indData.sector}`} emoji="🏭" source={report.industry.meta.source}>
          <p>
            <strong>Globaler Markt:</strong> {fmtLarge(ss.globalMarketSizeUsdBn * 1e9)} USD &nbsp;|&nbsp;
            <strong>Wachstum:</strong> <Pct value={ss.yoyGrowthPct} /> YoY
          </p>
          <div style={{ marginBottom: 16 }}>
            <strong>Trends:</strong>{" "}
            {ss.topTrends.map((t) => <span key={t} className="trend-pill">{t}</span>)}
          </div>
          {indData.competitors.map((c) => (
            <div key={c.name} className="comp-card">
              <span className="comp-name">{c.name}</span>
              {c.ticker && <span className="comp-ticker">({c.ticker})</span>}
              <p style={{ margin: "6px 0 0", color: "#374151" }}>{c.notes}</p>
            </div>
          ))}
        </Section>

        <footer>
          Datenquellen: stooq.com (Aktien), CoinGecko (Krypto), Destatis-Schätzungen (Immobilien).
          {report.stocks.meta.source === "sample" && " ⚠️ Beispieldaten: Live-Daten werden via GitHub Actions abgerufen."}
        </footer>
      </body>
    </html>
  );
}
