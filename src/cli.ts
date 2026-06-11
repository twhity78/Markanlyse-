import { loadConfig } from "./config.js";
import { fetchStocks } from "./sources/stocks.js";
import { fetchCrypto } from "./sources/crypto.js";
import { fetchRealEstate } from "./sources/realEstate.js";
import { fetchIndustry } from "./sources/industry.js";
import { renderMarkdown } from "./render/markdown.js";
import { renderHtml } from "./render/html.js";
import { writeReports } from "./write.js";
import type { Report } from "./types.js";

async function main() {
  console.log("Marktanalyse — Bericht wird erstellt …");
  const config = loadConfig();

  const [stocksResult, cryptoResult] = await Promise.all([
    fetchStocks(config.stocks),
    fetchCrypto(config.crypto),
  ]);

  const realEstateSection = fetchRealEstate(config.realEstate.regions);
  const industrySection = fetchIndustry(config.industry);

  const generatedAt = new Date().toISOString();
  const report: Report = {
    generatedAt,
    stocks: {
      title: "Aktienmärkte",
      meta: stocksResult.meta,
      data: stocksResult.quotes,
    },
    crypto: {
      title: "Kryptomärkte",
      meta: cryptoResult.meta,
      data: cryptoResult.quotes,
    },
    realEstate: realEstateSection,
    industry: industrySection,
  };

  const markdown = renderMarkdown(report);
  const html = renderHtml(report);

  const dateStr = generatedAt.slice(0, 10);
  writeReports(dateStr, markdown, html);

  const sources = [
    `Aktien: ${report.stocks.meta.source}`,
    `Krypto: ${report.crypto.meta.source}`,
    `Immobilien: ${report.realEstate.meta.source}`,
    `Branche: ${report.industry.meta.source}`,
  ].join(" | ");
  console.log(`Datenquellen — ${sources}`);
  console.log("Fertig.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
