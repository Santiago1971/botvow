#!/usr/bin/env node
/**
 * Cross-check the demo library against tools/botvow.py and exercise sign/verify/tamper.
 * Run from the repo root: node tests/ed25519_page_test.mjs
 */
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  bytesToB64u,
  b64uToBytes,
  utf8,
  kidOf,
  canonicalJson,
  chainIdFor,
  buildSampleBody,
  signatureRecord,
  keygen,
  sign,
  verify,
  sha256Hex,
} from "../docs/ed25519-lib.js";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const SEED_B64U = "scBJVUTblj3P9UqWHsnhULxyJ64ZnoE4VO9CpLZPI94";
const MSG = "This is a throwaway demo sentence for the BotVow Ed25519 page.";
const TS = "2026-11-18T17:00:00Z";

const seed = b64uToBytes(SEED_B64U);
const { secretKey, publicKey } = keygen(seed);
const kid = kidOf(publicKey);

assert.equal(bytesToB64u(secretKey), SEED_B64U);
assert.equal(bytesToB64u(publicKey), "gEpJ9Iv2AFMFPXhp3n20qeSm5I4bVGb2g3g8dEGoqFI");
assert.equal(kid, "ed25519:2bcf49eb6d012606");

const textSig = sign(utf8(MSG), secretKey);
assert.equal(bytesToB64u(textSig), "e1W6J1ZipfZkm1_XS9J3bYGsJM0inv6q1Bhj4S5WFgpVd3-wTI5Wp59swZX7smnTVo72nm2u8QeftWzNbuiRBA");
assert.equal(verify(textSig, utf8(MSG), publicKey), true);
assert.equal(verify(textSig, utf8(MSG.replace("page.", "page!")), publicKey), false);

const body = buildSampleBody({ kid, message: MSG, ts: TS, chainId: chainIdFor(publicKey) });
const canon = canonicalJson(body);
assert.equal(body.chain_id, "demo-f3e950503d84");
assert.equal(body.content.payload_sha256, "57c7182b270bf093b4ca951fb380dda07d8148aa075f85cfb4a50ad5ecc9493a");
assert.equal(
  canon,
  '{"author":"ed25519:2bcf49eb6d012606","chain_id":"demo-f3e950503d84","content":{"note":"Demo sample only. Not a real BotVow chain.","payload_sha256":"57c7182b270bf093b4ca951fb380dda07d8148aa075f85cfb4a50ad5ecc9493a"},"prev_hash":"0000000000000000000000000000000000000000000000000000000000000000","seq":1,"spec":"botvow/0.1","ts":"2026-11-18T17:00:00Z","type":"proposal"}',
);

const jsonSig = sign(utf8(canon), secretKey);
assert.equal(bytesToB64u(jsonSig), "Qtzv-pODnBvOCYSKLumexUuMiDfwP6KtmlkVGOZNt5sDfFZHzidvUMmGCQSlguJfs-IZk4xmgpS6gXf8LJC6Ag");
assert.equal(verify(jsonSig, utf8(canon), publicKey), true);
assert.equal(verify(jsonSig, utf8(canon.replace("proposal", "Proposal")), publicKey), false);

const rec = signatureRecord(kid, jsonSig);
assert.equal(rec.alg, "Ed25519");
assert.equal(rec.kid, kid);
assert.deepEqual(Object.keys(canonicalJson(rec) && JSON.parse(canonicalJson(rec))), ["alg", "kid", "sig"]);

// Independent check: Python's canon() and kid_of() and Ed25519 must match.
const py = spawnSync("python3", ["-c", `
import base64, hashlib, json, sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def ub64u(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
def canon(obj): return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
seed = ub64u(sys.argv[1])
priv = Ed25519PrivateKey.from_private_bytes(seed)
pub = priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
kid = "ed25519:" + hashlib.sha256(pub).hexdigest()[:16]
body = json.loads(sys.argv[2])
c = canon(body)
sig = b64u(priv.sign(c.encode()))
print(kid)
print(c)
print(sig)
print(b64u(pub))
`, SEED_B64U, canon], { cwd: ROOT, encoding: "utf8" });
if (py.status !== 0) {
  process.stderr.write(py.stderr);
  throw new Error("python cross-check failed to run");
}
const [pyKid, pyCanon, pySig, pyPub] = py.stdout.trim().split("\n");
assert.equal(pyKid, kid);
assert.equal(pyPub, bytesToB64u(publicKey));
assert.equal(pyCanon, canon);
assert.equal(pySig, bytesToB64u(jsonSig));

console.log("ed25519_page_test.mjs: all checks passed (sentence, canonical JSON, tamper, python cross-check)");
