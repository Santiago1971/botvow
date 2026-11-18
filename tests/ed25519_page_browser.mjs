#!/usr/bin/env node
/**
 * Headless check of docs/ed25519.html: sign/verify/tamper, and no requests outside the local origin.
 * Run from the repo root: node tests/ed25519_page_browser.mjs
 */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

async function loadPlaywright() {
  const require = createRequire(import.meta.url);
  const candidates = [];
  try { candidates.push(require.resolve("playwright")); } catch {}
  candidates.push(
    "/home/box/.npm/_npx/e41f203b7505f1fb/node_modules/playwright/index.js",
    "/usr/local/lib/pnpm/5/.pnpm/playwright@1.63.0-alpha-2026-08-31/node_modules/playwright/index.js",
  );
  for (const c of candidates) {
    if (!c) continue;
    try {
      return await import(c.startsWith("/") ? pathToFileURL(c).href : c);
    } catch {}
  }
  throw new Error("playwright is not installed");
}
const pw = await loadPlaywright();
const chromium = pw.chromium || pw.default?.chromium;
if (!chromium) throw new Error('playwright has no chromium export');


const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const DOCS = path.join(ROOT, "docs");
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".md": "text/markdown; charset=utf-8",
  ".json": "application/json; charset=utf-8",
};

function startServer() {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, "http://127.0.0.1");
    let rel = decodeURIComponent(url.pathname);
    if (rel.endsWith("/")) rel += "index.html";
    const file = path.normalize(path.join(DOCS, rel));
    if (!file.startsWith(DOCS)) {
      res.writeHead(403).end();
      return;
    }
    fs.readFile(file, (err, data) => {
      if (err) {
        res.writeHead(404).end("not found");
        return;
      }
      res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream" });
      res.end(data);
    });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

const external = [];
const server = await startServer();
const port = server.address().port;
const origin = `http://127.0.0.1:${port}`;

const browser = await chromium.launch({
  executablePath: "/usr/bin/google-chrome",
  headless: true,
  args: ["--headless=new", "--no-sandbox", "--disable-gpu"],
});
const context = await browser.newContext();
context.on("request", (req) => {
  const url = req.url();
  if (!url.startsWith(origin) && !url.startsWith("data:") && !url.startsWith("blob:") && !url.startsWith("about:")) {
    external.push(url);
  }
});

const page = await context.newPage();
await page.goto(`${origin}/ed25519.html`, { waitUntil: "networkidle" });

// Home page has the CTA and nav item.
const home = await context.newPage();
await home.goto(`${origin}/`, { waitUntil: "networkidle" });
const cta = await home.locator("a.cta").getAttribute("href");
const navHas = await home.locator("nav").locator("a[href='ed25519.html']").count();
if (cta !== "ed25519.html" || navHas < 1) {
  throw new Error(`home page missing Explore Ed25519 CTA or nav item (cta=${cta}, nav=${navHas})`);
}
await home.close();

await page.waitForFunction(() => window.__botvowEd25519 && window.__botvowEd25519.kid);

const afterLoad = await page.evaluate(() => {
  const api = window.__botvowEd25519;
  return {
    kid: api.kid,
    textOk: api.verifyText(),
    jsonOk: api.verifyJson(),
    textResult: document.getElementById("result-text").textContent,
    jsonResult: document.getElementById("result-json").textContent,
  };
});
if (afterLoad.textOk !== true || afterLoad.jsonOk !== true) {
  throw new Error("expected auto-signed sentence and JSON to verify OK: " + JSON.stringify(afterLoad));
}

const textTamper = await page.evaluate(() => {
  const api = window.__botvowEd25519;
  api.setMessage(document.getElementById("message").value.replace("page.", "page!"));
  return { ok: api.verifyText(), result: document.getElementById("result-text").textContent };
});
if (textTamper.ok !== false) {
  throw new Error("expected sentence tamper to fail verify: " + JSON.stringify(textTamper));
}

const resignText = await page.evaluate(() => {
  const api = window.__botvowEd25519;
  api.signText();
  return api.verifyText();
});
if (resignText !== true) throw new Error("expected re-signed sentence to verify OK");

const jsonTamper = await page.evaluate(() => {
  const api = window.__botvowEd25519;
  api.tamperJson();
  return {
    ok: document.getElementById("result-json").classList.contains("bad"),
    verify: api.verifyJson(),
    text: document.getElementById("canon").value,
  };
});
if (jsonTamper.verify !== false) {
  throw new Error("expected JSON tamper to fail verify: " + JSON.stringify(jsonTamper));
}

const resignJson = await page.evaluate(() => {
  const api = window.__botvowEd25519;
  api.signJson();
  return api.verifyJson();
});
if (resignJson !== true) throw new Error("expected re-signed JSON to verify OK");

// Known seed must match the Python/spec vectors.
const vectors = await page.evaluate(() => {
  const api = window.__botvowEd25519;
  api.loadSeed("scBJVUTblj3P9UqWHsnhULxyJ64ZnoE4VO9CpLZPI94");
  api.setMessage("This is a throwaway demo sentence for the BotVow Ed25519 page.");
  document.getElementById("canon-ts").value = "2026-11-18T17:00:00Z";
  // setMessage already refreshed canon with a new ts; force the fixture timestamp and re-sign.
  const current = JSON.parse(document.getElementById("canon").value);
  current.ts = "2026-11-18T17:00:00Z";
  document.getElementById("canon").value = JSON.stringify(current);
  api.signText();
  api.signJson();
  return {
    kid: api.kid,
    pubkey: api.pubkey,
    textSig: api.textSig,
    jsonSig: api.jsonSig,
    canon: document.getElementById("canon").value,
    textOk: api.verifyText(),
    jsonOk: api.verifyJson(),
  };
});
if (vectors.kid !== "ed25519:2bcf49eb6d012606") throw new Error("kid mismatch: " + vectors.kid);
if (vectors.pubkey !== "gEpJ9Iv2AFMFPXhp3n20qeSm5I4bVGb2g3g8dEGoqFI") throw new Error("pubkey mismatch");
if (vectors.textSig !== "e1W6J1ZipfZkm1_XS9J3bYGsJM0inv6q1Bhj4S5WFgpVd3-wTI5Wp59swZX7smnTVo72nm2u8QeftWzNbuiRBA") {
  throw new Error("text sig mismatch: " + vectors.textSig);
}
if (vectors.jsonSig !== "Qtzv-pODnBvOCYSKLumexUuMiDfwP6KtmlkVGOZNt5sDfFZHzidvUMmGCQSlguJfs-IZk4xmgpS6gXf8LJC6Ag") {
  throw new Error("json sig mismatch: " + vectors.jsonSig);
}
if (vectors.textOk !== true || vectors.jsonOk !== true) throw new Error("fixture should verify OK");

if (external.length) {
  throw new Error("unexpected external requests: " + external.join(", "));
}

await browser.close();
server.close();
console.log("ed25519_page_browser.mjs: sign->OK, tamper->fail (sentence and JSON), no external requests");
