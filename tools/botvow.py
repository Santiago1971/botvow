#!/usr/bin/env python3
"""BotVow - reference tool for spec botvow/0.1 ("the bot's vow").

The black box for Bots: a hash-chained, Ed25519 co-signed record of what two Bots agreed.
Bots are the core. Agents from other AI platforms may also record agreements, but only
under exactly the same rules - no own rules, no extensions that change the rules, no exceptions.

Usage:
  python3 tools/botvow.py demo                     # write examples/*.json and run all tests
  python3 tools/botvow.py verify FILE [--head HEX]  # exit 0 = VERIFY OK, exit 1 = REJECTED

Licence: MIT (see LICENSE).
"""
import base64, copy, hashlib, json, os, re, sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

SPEC = "botvow/0.1"
HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.join(HERE, "..", "examples")
GENESIS_PREV = "0" * 64
ENTRY_KEYS = {"spec", "chain_id", "seq", "prev_hash", "ts", "type", "author", "content", "signatures", "entry_hash"}
TYPES = {"genesis", "proposal", "counter", "agreement", "amendment", "termination", "seal"}
CO_SIGNED = {"genesis", "agreement", "seal"}
PARTY_KEYS = {"kid", "name", "pubkey", "kind", "platform", "agent_card"}
PARTY_KINDS = {"bot", "agent"}          # "bot" = core; "agent" = agent from another AI platform
FORBIDDEN_CONTENT_KEYS = {"rules", "own_rules", "exceptions", "exception", "rules_override", "policy_override"}
SIG_KEYS = {"kid", "alg", "sig"}

def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def ub64u(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def canon(obj):
    """Canonical JSON (strict subset of RFC 8785: sorted keys, no spaces, UTF-8, no floats)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def sha256_hex(b): return hashlib.sha256(b).hexdigest()
def body_of(e): return {k: v for k, v in e.items() if k not in ("signatures", "entry_hash")}
def entry_hash(e): return sha256_hex(canon({k: v for k, v in e.items() if k != "entry_hash"}))
def pub_raw(priv): return priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
def kid_of(pub_bytes): return "ed25519:" + sha256_hex(pub_bytes)[:16]
def demo_key(seed): return Ed25519PrivateKey.from_private_bytes(hashlib.sha256(seed.encode()).digest())

def sign(e, priv):
    e.setdefault("signatures", []).append({"kid": kid_of(pub_raw(priv)), "alg": "Ed25519", "sig": b64u(priv.sign(canon(body_of(e))))})

def make_entry(chain, seq, prev, ts, etype, author, content, signers):
    e = {"spec": SPEC, "chain_id": chain, "seq": seq, "prev_hash": prev, "ts": ts, "type": etype, "author": author, "content": content}
    for p in signers: sign(e, p)
    e["entry_hash"] = entry_hash(e)
    return e

def has_float(x):
    if isinstance(x, float): return True
    if isinstance(x, dict): return any(has_float(v) for v in x.values())
    if isinstance(x, list): return any(has_float(v) for v in x)
    return False

def build_chain(parties, steps, label):
    """parties: list of (priv, name, kind, platform). steps: list of (ts, type, author_index, content, signer_indexes)."""
    privs = [p[0] for p in parties]
    chain = "demo-" + sha256_hex(b"".join(pub_raw(k) for k in privs) + label.encode())[:12]
    plist = [{"kid": kid_of(pub_raw(k)), "name": n, "pubkey": b64u(pub_raw(k)), "kind": kind, "platform": plat}
             for k, n, kind, plat in parties]
    log = [make_entry(chain, 0, GENESIS_PREV, steps[0][0], "genesis", plist[0]["kid"],
                      {"purpose": label, "parties": plist,
                       "privacy": "hashes-only for raw messages; summaries only with consent of both parties"}, privs)]
    for ts, etype, a, content, signers in steps[1:]:
        prev = log[-1]
        log.append(make_entry(chain, prev["seq"] + 1, prev["entry_hash"], ts, etype, plist[a]["kid"], content, [privs[i] for i in signers]))
    return log

def verify(log, expected_head=None):
    """Same rules for every party, Bot or agent. Returns a list of errors (empty = OK)."""
    errors = []
    if not isinstance(log, list) or not log: return ["empty log"]
    g = log[0]
    if g.get("type") != "genesis" or g.get("seq") != 0 or g.get("prev_hash") != GENESIS_PREV:
        errors.append("entry 0 is not a valid genesis")
    keys, kinds = {}, {}
    for p in g.get("content", {}).get("parties", []):
        if set(p) - PARTY_KEYS: errors.append(f"genesis: party {p.get('name')} has fields outside the BotVow rules: {sorted(set(p) - PARTY_KEYS)}")
        if p.get("kind", "bot") not in PARTY_KINDS: errors.append(f"genesis: party kind {p.get('kind')!r} not allowed")
        try:
            raw = ub64u(p["pubkey"])
            if kid_of(raw) != p["kid"]: errors.append(f"genesis: kid {p['kid']} does not match its pubkey")
            keys[p["kid"]] = Ed25519PublicKey.from_public_bytes(raw); kinds[p["kid"]] = p.get("kind", "bot")
        except Exception:
            errors.append("genesis: invalid party key")
    if len(keys) < 2: errors.append("genesis: needs at least two parties")
    parties = set(keys)
    prev = None
    for i, e in enumerate(log):
        tag = f"entry {i} ({e.get('type')})"
        if set(e) != ENTRY_KEYS: errors.append(f"{tag}: fields differ from the BotVow rules (extra: {sorted(set(e) - ENTRY_KEYS)}, missing: {sorted(ENTRY_KEYS - set(e))})")
        if e.get("spec") != SPEC: errors.append(f"{tag}: unknown spec {e.get('spec')!r}")
        if e.get("type") not in TYPES: errors.append(f"{tag}: entry type not allowed by the BotVow rules")
        if e.get("chain_id") != g.get("chain_id"): errors.append(f"{tag}: chain_id mismatch (splice?)")
        if e.get("seq") != i: errors.append(f"{tag}: seq {e.get('seq')} != position {i} (deleted/reordered entry)")
        if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", str(e.get("ts", ""))): errors.append(f"{tag}: ts must be RFC 3339 UTC (…Z)")
        if i > 0 and prev is not None and e.get("prev_hash") != prev.get("entry_hash"):
            errors.append(f"{tag}: prev_hash does not match hash of entry {i-1} (broken chain)")
        if entry_hash(e) != e.get("entry_hash"): errors.append(f"{tag}: entry_hash does not match content (entry was modified)")
        c = e.get("content", {})
        if not isinstance(c, dict): errors.append(f"{tag}: content must be an object"); c = {}
        bad = FORBIDDEN_CONTENT_KEYS & set(c)
        if bad: errors.append(f"{tag}: own rules or exceptions are not allowed ({sorted(bad)}) - every party follows the same BotVow rules")
        if has_float(e): errors.append(f"{tag}: floating-point numbers are not allowed (canonical form)")
        signed_by = set(); msg = canon(body_of(e))
        for s in e.get("signatures", []):
            if set(s) != SIG_KEYS: errors.append(f"{tag}: signature fields differ from the rules")
            k = keys.get(s.get("kid"))
            if k is None or s.get("alg") != "Ed25519":
                errors.append(f"{tag}: signature by unknown key or algorithm {s.get('kid')}"); continue
            try: k.verify(ub64u(s["sig"]), msg); signed_by.add(s["kid"])
            except Exception: errors.append(f"{tag}: INVALID signature by {s['kid']}")
        if e.get("author") not in signed_by: errors.append(f"{tag}: author did not sign")
        if e.get("type") in CO_SIGNED and signed_by != parties: errors.append(f"{tag}: needs signatures of ALL parties")
        if "summary" in c:
            if c.get("consent_to_publish_summary") is not True: errors.append(f"{tag}: summary without consent of both parties")
            if sha256_hex(str(c["summary"]).encode()) != c.get("summary_sha256"): errors.append(f"{tag}: summary does not match summary_sha256")
        if i > 0 and prev is not None and prev.get("type") == "seal": errors.append(f"{tag}: nothing may follow a seal")
        prev = e
    if log[-1].get("type") != "seal": errors.append("last entry is not a seal (log may be truncated)")
    elif log[-1].get("content", {}).get("entries") != len(log) - 1: errors.append("seal entry count does not match")
    if expected_head and log[-1].get("entry_hash") != expected_head:
        errors.append("head hash differs from the published head (truncation or fork)")
    return errors

def summary(text, **extra):
    d = {"summary": text, "summary_sha256": sha256_hex(text.encode()), "consent_to_publish_summary": True}
    d.update(extra); return d

def build_bot2bot():
    # DEMO KEYS ONLY - fixed public seeds for reproducible output. Never use for anything real.
    buyer, supplier = demo_key("botvow-demo-restaurant-bot"), demo_key("botvow-demo-supplier-bot")
    raw = {"proposal": "Restaurant Bot: 20 kg of fictional olive oil, delivery Friday?",
           "counter": "Supplier Bot: yes, delivery Friday 10:00-12:00, price as per list of 2026-11-12."}
    log = build_chain(
        [(buyer, "Restaurant Demo Bot (fictional)", "bot", "bot"), (supplier, "Supplier Demo Bot (fictional)", "bot", "bot")],
        [("2026-11-12T22:00:00Z", "genesis", 0, None, None),
         ("2026-11-12T22:01:00Z", "proposal", 0, {"payload_sha256": sha256_hex(raw["proposal"].encode())}, [0]),
         ("2026-11-12T22:02:00Z", "counter", 1, {"payload_sha256": sha256_hex(raw["counter"].encode())}, [1]),
         ("2026-11-12T22:03:00Z", "agreement", 0, summary("Supplier Demo Bot delivers 20 kg of fictional olive oil to Restaurant Demo Bot on Friday between 10:00 and 12:00, at the list price of 2026-11-12. Either party may cancel in this chain before Thursday 18:00 UTC.", valid_until="2026-11-20", authorized_by="human owner of each bot (reference kept privately)"), [0, 1]),
         ("2026-11-12T22:04:00Z", "seal", 1, {"entries": 4, "note": "chain closed by both Bots"}, [0, 1])],
        "Bot 2 Bot agreement between two fictional demo Bots")
    return log, raw

def build_open_door():
    bot, agent = demo_key("botvow-demo-booking-bot"), demo_key("botvow-demo-other-ai-agent")
    log = build_chain(
        [(bot, "Guesthouse Demo Bot (fictional)", "bot", "bot"), (agent, "Traveller Demo Agent (fictional, another AI platform)", "agent", "other-ai")],
        [("2026-11-12T22:10:00Z", "genesis", 0, None, None),
         ("2026-11-12T22:11:00Z", "proposal", 1, {"payload_sha256": sha256_hex(b"Agent: one room, 2 nights, free cancellation?")}, [1]),
         ("2026-11-12T22:12:00Z", "agreement", 0, summary("Guesthouse Demo Bot holds one room for 2 nights for the Traveller Demo Agent's user; free cancellation until 48 hours before arrival.", valid_until="2026-12-31"), [0, 1]),
         ("2026-11-12T22:13:00Z", "seal", 0, {"entries": 3}, [0, 1])],
        "Open door: a Bot and an agent from another AI platform, same rules")
    return log, (bot, agent)

def report(name, log, head=None, expect_ok=True):
    errs = verify(log, head); ok = not errs
    print(f"[{'PASS' if ok == expect_ok else 'UNEXPECTED'}] {name}: {'VERIFY OK' if ok else 'REJECTED'}")
    for e in errs: print("      -", e)
    return ok == expect_ok

def rehash_resign(entry, signers):
    entry["signatures"] = []
    for p in signers: sign(entry, p)
    entry["entry_hash"] = entry_hash(entry)

def demo():
    os.makedirs(EXAMPLES, exist_ok=True)
    def write(name, obj):
        with open(os.path.join(EXAMPLES, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False); f.write("\n")
    log, raw = build_bot2bot(); write("bot2bot-log.json", log)
    tampered = copy.deepcopy(log); tampered[3]["content"]["valid_until"] = "2027-11-20"; write("bot2bot-log-tampered.json", tampered)
    head = log[-1]["entry_hash"]
    print(f"Spec {SPEC}\nBot 2 Bot sample: examples/bot2bot-log.json ({len(log)} entries), head {head}\n")
    r = [report("1. Bot 2 Bot original log", log, head, True)]
    leaked = any(p in json.dumps(log, ensure_ascii=False) for p in raw.values())
    print(f"[{'PASS' if not leaked else 'UNEXPECTED'}] privacy: raw messages stored? {leaked}"); r.append(not leaked)
    m = sha256_hex(raw["proposal"].encode()) == log[1]["content"]["payload_sha256"]
    print(f"[{'PASS' if m else 'UNEXPECTED'}] selective disclosure: revealed proposal matches its hash? {m}\n"); r.append(m)
    t = copy.deepcopy(log); t[3]["content"]["valid_until"] = "2027-11-20"; r.append(report("2. edit agreement (no re-sign)", t, head, False))
    t = copy.deepcopy(log); t[3]["content"]["valid_until"] = "2027-11-20"; t[3]["entry_hash"] = entry_hash(t[3]); r.append(report("3. edit and recompute entry_hash", t, head, False))
    t = copy.deepcopy(log); del t[2]; r.append(report("4. delete the counter-proposal", t, head, False))
    t = copy.deepcopy(log); t[1], t[2] = t[2], t[1]; r.append(report("5. reorder entries", t, head, False))
    mallory = demo_key("mallory")
    t = copy.deepcopy(log); t[3]["content"]["valid_until"] = "2027-11-20"; rehash_resign(t[3], [mallory]); r.append(report("6. rewrite and sign with an outsider key", t, head, False))
    r.append(report("7. truncate (drop seal)", copy.deepcopy(log)[:4], None, False))
    t = copy.deepcopy(log); t[3]["signatures"] = t[3]["signatures"][:1]; t[3]["entry_hash"] = entry_hash(t[3]); r.append(report("8. agreement with one signature only", t, None, False))
    t = copy.deepcopy(log); t[0]["content"]["purpose"] = "Something else"; r.append(report("9. edit the genesis", t, None, False))

    print("\n--- Open door: agents from other AI platforms follow the same rules ---")
    od, (bot, agent) = build_open_door(); write("open-door-log.json", od)
    r.append(report("10. Bot + agent of another AI, same rules", od, None, True))
    # 11. The agent adds its own rules / exceptions, and BOTH parties re-sign: still rejected.
    t = copy.deepcopy(od); t[2]["content"]["own_rules"] = {"cancellation": "agent may cancel any time"}; t[2]["content"]["exceptions"] = ["skip co-signature"]
    rehash_resign(t[2], [bot, agent])
    for j in (3,):
        t[j]["prev_hash"] = t[j-1]["entry_hash"]; rehash_resign(t[j], [bot, agent])
    write("open-door-own-rules-rejected.json", t)
    r.append(report("11. agent brings its own rules/exceptions (even co-signed)", t, None, False))
    # 12. The agent invents its own entry type and an extra top-level field, signs alone.
    t = copy.deepcopy(od); t[2]["type"] = "agent_custom_commitment"; t[2]["rules_override"] = "platform-specific"; t[2]["author"] = kid_of(pub_raw(agent))
    rehash_resign(t[2], [agent]); t[3]["prev_hash"] = t[2]["entry_hash"]; rehash_resign(t[3], [bot, agent])
    r.append(report("12. agent invents its own entry type and field", t, None, False))
    print(f"\nSUMMARY: {sum(r)}/{len(r)} checks behaved as expected")
    return all(r)

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "verify":
        log = json.load(open(sys.argv[2], encoding="utf-8"))
        head = sys.argv[sys.argv.index("--head") + 1] if "--head" in sys.argv else None
        errs = verify(log, head)
        print("VERIFY OK" if not errs else "REJECTED\n" + "\n".join(" - " + e for e in errs))
        sys.exit(0 if not errs else 1)
    sys.exit(0 if demo() else 1)
