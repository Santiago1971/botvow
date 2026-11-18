import {
  bytesToB64u,
  b64uToBytes,
  utf8,
  kidOf,
  canonicalJson,
  chainIdFor,
  utcTimestamp,
  buildSampleBody,
  signatureRecord,
  keygen,
  sign,
  verify,
} from "./ed25519-lib.js";

const DEFAULT_MESSAGE = "This is a throwaway demo sentence for the BotVow Ed25519 page.";

const $ = (id) => document.getElementById(id);

const state = {
  secretKey: null,
  publicKey: null,
  kid: null,
  textSig: null,
  jsonSig: null,
};

function setResult(id, ok, text) {
  const el = $(id);
  el.textContent = text;
  el.className = "result " + (ok === true ? "ok" : ok === false ? "bad" : "");
}

function currentMessage() {
  return $("message").value;
}

function refreshCanon({ keepEdits = false } = {}) {
  if (keepEdits) return;
  const body = buildSampleBody({
    kid: state.kid,
    message: currentMessage(),
    ts: $("canon-ts").value || utcTimestamp(),
    chainId: chainIdFor(state.publicKey),
  });
  $("canon").value = canonicalJson(body);
  $("canon-ts").value = body.ts;
}

function fillKeys() {
  $("pubkey").textContent = bytesToB64u(state.publicKey);
  $("kid").textContent = state.kid;
  $("privkey").textContent = bytesToB64u(state.secretKey);
}

function newKey(seed) {
  const kp = keygen(seed);
  state.secretKey = kp.secretKey;
  state.publicKey = kp.publicKey;
  state.kid = kidOf(kp.publicKey);
  $("canon-ts").value = utcTimestamp();
  $("privwrap").hidden = true;
  $("reveal").textContent = "Show private key";
  $("reveal").setAttribute("aria-expanded", "false");
  fillKeys();
  refreshCanon();
  autoSign();
}

function autoSign() {
  signText();
  signJson();
}

function signText() {
  const sig = sign(utf8(currentMessage()), state.secretKey);
  state.textSig = sig;
  $("sig-text").textContent = bytesToB64u(sig);
  setResult("result-text", true, "Signed. Verify should read OK until you change the sentence.");
}

function verifyText() {
  if (!state.textSig) {
    setResult("result-text", false, "No signature yet. Sign the sentence first.");
    return false;
  }
  const ok = verify(state.textSig, utf8(currentMessage()), state.publicKey);
  setResult("result-text", ok, ok ? "OK — the signature matches this sentence." : "Failed — the sentence no longer matches the signature.");
  return ok;
}

function signJson() {
  let body;
  try {
    body = JSON.parse($("canon").value);
  } catch {
    setResult("result-json", false, "The box is not valid JSON, so it was not signed.");
    return;
  }
  try {
    const canon = canonicalJson(body);
    $("canon").value = canon;
    const sig = sign(utf8(canon), state.secretKey);
    state.jsonSig = sig;
    $("sig-json").textContent = canonicalJson(signatureRecord(state.kid, sig));
    setResult("result-json", true, "Signed over canonical(body). Verify should read OK until you change a character.");
  } catch (err) {
    setResult("result-json", false, String(err.message || err));
  }
}

function verifyJson() {
  if (!state.jsonSig) {
    setResult("result-json", false, "No signature yet. Sign the canonical JSON first.");
    return false;
  }
  const bytes = utf8($("canon").value);
  const ok = verify(state.jsonSig, bytes, state.publicKey);
  setResult("result-json", ok, ok ? "OK — the signature matches this canonical JSON." : "Failed — the canonical JSON no longer matches the signature.");
  return ok;
}

function tamperJson() {
  const text = $("canon").value;
  const idx = text.indexOf("proposal");
  if (idx === -1) {
    setResult("result-json", false, "Could not find a character to change. Edit the JSON yourself, then verify.");
    return;
  }
  $("canon").value = text.slice(0, idx) + "Proposal" + text.slice(idx + "proposal".length);
  verifyJson();
}

function revealPrivate() {
  const wrap = $("privwrap");
  const willShow = wrap.hidden;
  wrap.hidden = !willShow;
  $("reveal").textContent = willShow ? "Hide private key" : "Show private key";
  $("reveal").setAttribute("aria-expanded", willShow ? "true" : "false");
}

function onMessageInput() {
  refreshCanon();
}

$("reveal").addEventListener("click", revealPrivate);
$("newkey").addEventListener("click", () => newKey());
$("sign-text").addEventListener("click", signText);
$("verify-text").addEventListener("click", verifyText);
$("sign-json").addEventListener("click", signJson);
$("verify-json").addEventListener("click", verifyJson);
$("tamper-json").addEventListener("click", tamperJson);
$("message").addEventListener("input", onMessageInput);

$("message").value = DEFAULT_MESSAGE;
newKey();

// Expose for headless tests.
window.__botvowEd25519 = {
  get kid() { return state.kid; },
  get pubkey() { return bytesToB64u(state.publicKey); },
  get textSig() { return state.textSig ? bytesToB64u(state.textSig) : null; },
  get jsonSig() { return state.jsonSig ? bytesToB64u(state.jsonSig) : null; },
  signText,
  verifyText,
  signJson,
  verifyJson,
  tamperJson,
  setMessage(text) {
    $("message").value = text;
    onMessageInput();
  },
  loadSeed(b64u) {
    newKey(b64uToBytes(b64u));
  },
};
