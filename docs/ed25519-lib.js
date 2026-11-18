/**
 * Browser helpers for the BotVow Ed25519 demo.
 * kid and canonical JSON follow SPEC.md and tools/botvow.py — do not invent other rules.
 */
import * as ed from "./vendor/noble-ed25519/index.js";
import { sha256, sha512 } from "./vendor/noble-hashes/sha2.js";

ed.hashes.sha512 = sha512;
ed.hashes.sha512Async = async (message) => sha512(message);

export { ed, sha256, sha512 };

export function bytesToHex(bytes) {
  let out = "";
  for (let i = 0; i < bytes.length; i++) out += bytes[i].toString(16).padStart(2, "0");
  return out;
}

export function bytesToB64u(bytes) {
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function b64uToBytes(s) {
  const pad = "=".repeat((4 - (s.length % 4)) % 4);
  const b64 = s.replace(/-/g, "+").replace(/_/g, "/") + pad;
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export function utf8(text) {
  return new TextEncoder().encode(text);
}

export function sha256Hex(bytes) {
  return bytesToHex(sha256(bytes));
}

/** kid = "ed25519:" + hex(SHA-256(raw public key))[0:16]  (SPEC.md §2, tools/botvow.py kid_of) */
export function kidOf(pubBytes) {
  return "ed25519:" + sha256Hex(pubBytes).slice(0, 16);
}

/**
 * Canonical JSON: keys sorted lexicographically, no insignificant whitespace,
 * UTF-8, no floating-point numbers. Strict subset of RFC 8785 (SPEC.md §3, tools/botvow.py canon).
 */
export function sortKeys(value) {
  if (value === null) return null;
  const t = typeof value;
  if (t === "number") {
    if (!Number.isInteger(value)) throw new Error("floating-point numbers are not allowed (canonical form)");
    return value;
  }
  if (t === "string" || t === "boolean") return value;
  if (Array.isArray(value)) return value.map(sortKeys);
  if (t === "object") {
    const out = {};
    const keys = Object.keys(value).sort();
    for (const k of keys) out[k] = sortKeys(value[k]);
    return out;
  }
  throw new Error("unsupported type in canonical JSON");
}

export function canonicalJson(obj) {
  return JSON.stringify(sortKeys(obj));
}

export function canonicalBytes(obj) {
  return utf8(canonicalJson(obj));
}

export function chainIdFor(pubBytes) {
  const label = utf8("ed25519-page");
  const joined = new Uint8Array(pubBytes.length + label.length);
  joined.set(pubBytes, 0);
  joined.set(label, pubBytes.length);
  return "demo-" + sha256Hex(joined).slice(0, 12);
}

export function utcTimestamp(date = new Date()) {
  return date.toISOString().replace(/\.\d+Z$/, "Z");
}

/** Sample entry body (no signatures, no entry_hash) — the bytes BotVow signs. Not a valid log. */
export function buildSampleBody({ kid, message, ts, chainId }) {
  return {
    spec: "botvow/0.1",
    chain_id: chainId,
    seq: 1,
    prev_hash: "0".repeat(64),
    ts,
    type: "proposal",
    author: kid,
    content: {
      note: "Demo sample only. Not a real BotVow chain.",
      payload_sha256: sha256Hex(utf8(message)),
    },
  };
}

export function signatureRecord(kid, sigBytes) {
  return { kid, alg: "Ed25519", sig: bytesToB64u(sigBytes) };
}

export function keygen(seed) {
  return ed.keygen(seed);
}

export function sign(messageBytes, secretKey) {
  return ed.sign(messageBytes, secretKey);
}

export function verify(signature, messageBytes, publicKey) {
  try {
    return ed.verify(signature, messageBytes, publicKey);
  } catch {
    return false;
  }
}
