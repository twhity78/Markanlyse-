import { renderToStaticMarkup } from "react-dom/server";
import { createElement } from "react";
import { ReportHtml } from "./ReportHtml.js";
import type { Report } from "../types.js";

export function renderHtml(report: Report): string {
  const markup = renderToStaticMarkup(createElement(ReportHtml, { report }));
  return `<!DOCTYPE html>\n${markup}`;
}
