import type { Report } from "../types.js";
import type { IndustryData } from "../sources/industry.js";

function fmt(n: number, decimals = 2): string {
  return n.toLocaleString("de-DE", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function fmtPct(n: number): string {
  const sign = n >= 0 ? "+" : "";
  return `${sign}${fmt(n)}%`;
}

function fmtLarge(n: number): string {
  if (n >= 1e12) return `${fmt(n / 1e12, 2)} Bio.`;
  if (n >= 1e9) return `${fmt(n / 1e9, 2)} Mrd.`;
  if (n >= 1e6) return `${fmt(n / 1e6, 2)} Mio.`;
  return fmt(n, 0);
}

function sampleNote(source: "live" | "sample"): string {
  return source === "sample" ? " _(Beispieldaten — Live-Daten via GitHub Actions)_" : "";
}

export function renderMarkdown(report: Report): string {
  const lines: string[] = [];
  const date = new Date(report.generatedAt).toLocaleDateString("de-DE", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  lines.push(`# Marktbericht — ${date}`, "");
  lines.push(`_Erstellt am ${report.generatedAt}_`, "");
  lines.push("---", "");

  // Stocks
  const s = report.stocks;
  lines.push(`## 📈 Aktienmärkte${sampleNote(s.meta.source)}`, "");
  lines.push("| Symbol | Name | Kurs | 1T | 7T | 30T | 52W-H | 52W-T |");
  lines.push("|--------|------|-----:|----:|----:|----:|------:|------:|");
  for (const q of s.data) {
    lines.push(
      `| ${q.symbol} | ${q.name} | ${fmt(q.price)} ${q.currency} | ${fmtPct(q.change1d)} | ${fmtPct(q.change7d)} | ${fmtPct(q.change30d)} | ${fmt(q.high52w)} | ${fmt(q.low52w)} |`
    );
  }
  lines.push("");

  // Crypto
  const c = report.crypto;
  lines.push(`## 🪙 Kryptomärkte${sampleNote(c.meta.source)}`, "");
  lines.push("| Coin | Kurs (EUR) | 1T | 7T | 30T | Marktkapitalisierung |");
  lines.push("|------|----------:|----:|----:|----:|---------------------|");
  for (const q of c.data) {
    const mcap = q.marketCap ? fmtLarge(q.marketCap) : "–";
    lines.push(
      `| ${q.name} | ${fmt(q.price, 0)} | ${fmtPct(q.change1d)} | ${fmtPct(q.change7d)} | ${fmtPct(q.change30d)} | ${mcap} |`
    );
  }
  lines.push("");

  // Real estate
  const re = report.realEstate;
  lines.push(`## 🏠 Immobilienmarkt${sampleNote(re.meta.source)}`, "");
  lines.push("| Region | €/m² | Δ YoY | Δ 5 Jahre |");
  lines.push("|--------|-----:|------:|----------:|");
  for (const r of re.data) {
    lines.push(
      `| ${r.region} | ${fmt(r.pricePerSqm, 0)} | ${fmtPct(r.changeYoY)} | ${fmtPct(r.change5y)} |`
    );
  }
  lines.push("");

  // Industry
  const ind = report.industry;
  const indData = ind.data as IndustryData;
  lines.push(`## 🏭 Branchen- & Wettbewerbsanalyse — ${indData.sector}${sampleNote(ind.meta.source)}`, "");
  const ss = indData.sectorStats;
  lines.push(
    `**Globaler Markt:** ${fmtLarge(ss.globalMarketSizeUsdBn * 1e9)} USD | **Wachstum:** ${fmtPct(ss.yoyGrowthPct)} YoY`, ""
  );
  lines.push("**Trends:**");
  for (const t of ss.topTrends) lines.push(`- ${t}`);
  lines.push("");
  lines.push("### Wettbewerber", "");
  for (const comp of indData.competitors) {
    const ticker = comp.ticker ? ` _(${comp.ticker})_` : "";
    lines.push(`**${comp.name}**${ticker}: ${comp.notes}`, "");
  }

  lines.push("---");
  lines.push("_Datenquellen: stooq.com (Aktien), CoinGecko (Krypto), Destatis-Schätzungen (Immobilien)_");

  return lines.join("\n");
}
