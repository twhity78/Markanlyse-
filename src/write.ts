import { mkdirSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const reportsDir = resolve(__dirname, "../reports");

export function writeReports(date: string, markdown: string, html: string): void {
  const dayDir = resolve(reportsDir, date);
  mkdirSync(dayDir, { recursive: true });

  writeFileSync(resolve(dayDir, "report.md"), markdown, "utf-8");
  writeFileSync(resolve(dayDir, "report.html"), html, "utf-8");

  writeFileSync(resolve(reportsDir, "latest.md"), markdown, "utf-8");
  writeFileSync(resolve(reportsDir, "latest.html"), html, "utf-8");

  console.log(`Berichte geschrieben nach: ${dayDir}`);
  console.log(`Aktuell: ${reportsDir}/latest.{md,html}`);
}
