import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

const TIMEOUT_MS = 8000;

export async function fetchWithTimeout(url: string): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, { signal: controller.signal });
    return res;
  } finally {
    clearTimeout(timer);
  }
}

export function loadFixture<T>(name: string): T {
  const fixturePath = resolve(__dirname, "../../data/fixtures", `${name}.json`);
  const raw = readFileSync(fixturePath, "utf-8");
  return JSON.parse(raw) as T;
}

export async function fetchJsonOrFixture<T>(
  url: string,
  fixtureName: string
): Promise<{ data: T; source: "live" | "sample" }> {
  try {
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = (await res.json()) as T;
    return { data, source: "live" };
  } catch {
    const data = loadFixture<T>(fixtureName);
    return { data, source: "sample" };
  }
}
