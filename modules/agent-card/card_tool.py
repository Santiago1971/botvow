#!/usr/bin/env python3
"""Local Agent Card tool (draft, local only).

  python3 card_tool.py validate cards/*.json
  python3 card_tool.py export cards/X.json out/          # A2A Agent Card draft + schema.org JSON-LD + llms.txt
  python3 card_tool.py ask cards/X.json open 2026-12-08T10:00
  python3 card_tool.py ask cards/X.json faq groups
  python3 card_tool.py ask cards/X.json booking

Holidays come from the bundled snapshot of the Está no Ir dated official facts calendar
(data/feriados-pt-2026-2027.json), so "open on 8 December?" is answered from a dated, calculated
national-holiday list instead of a guess. The snapshot is clearly marked as calculated, not an official gazette.
"""
import datetime as dt, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = json.load(open(os.path.join(HERE, "schema", "local-agent-card.schema.json")))
ZONES = {z["id"] for z in json.load(open(os.path.join(HERE, "schema", "estanoir-zones-snapshot.json")))["zones"]}
CAL_PATH = os.path.join(HERE, "data", "feriados-pt-2026-2027.json")
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def holidays():
    cal = json.load(open(CAL_PATH))
    return {h["date"]: h for y in cal["years"].values() for h in y if h["type"] == "mandatory"}


def validate(card, today=None):
    today = today or dt.date.today()
    errs = []
    try:
        import jsonschema
        for e in jsonschema.Draft202012Validator(SCHEMA).iter_errors(card):
            errs.append(f"schema {'/'.join(map(str, e.path))}: {e.message}")
    except ImportError:
        errs.append("jsonschema missing")
    for s in card.get("opening_hours", {}).get("weekly", []):
        if s["opens"] >= s["closes"]:
            errs.append(f"slot {s['days']}: closes before opens (overnight slots not supported in v0.1)")
    seen = [d for s in card.get("opening_hours", {}).get("weekly", []) for d in s["days"]]
    if len(seen) != len(set(seen)):
        errs.append("a weekday appears in more than one slot")
    for z in card.get("zones", []):
        if z["id"] not in ZONES:
            errs.append(f"zone '{z['id']}' is not an Está no Ir trip id")
    v = card.get("verification", {})
    if v.get("valid_until") and dt.date.fromisoformat(v["valid_until"]) < today:
        errs.append("card expired (verification.valid_until in the past): must not be served")
    for o in card.get("offers", []):
        if "price_eur" in o and "price_checked_on" not in o:
            errs.append(f"offer '{o['name']}': price without price_checked_on")
    if not card.get("demo") and any("example.invalid" in str(x) for x in card.get("contact", {}).values()):
        errs.append("non-demo card with placeholder contacts")
    return errs


def slots_for(card, d):
    oh = card["opening_hours"]
    for ex in oh.get("exceptions", []):
        if ex["date"] == d.isoformat():
            return [] if ex["closed"] else ex.get("slots", []), f"exception: {ex.get('note', '')}".strip()
    if oh.get("always_open"):
        return [{"opens": "00:00", "closes": "23:59"}], "always open"
    hol = holidays().get(d.isoformat())
    day = DAYS[d.weekday()]
    why = ""
    if hol:
        rule = oh.get("public_holidays", "ask")
        why = f"public holiday ({hol['name_pt']}), rule={rule}"
        if rule == "closed": return [], why
        if rule == "ask": return None, why
        if rule == "open_as_sunday": day = "sun"
    return [{"opens": s["opens"], "closes": s["closes"]} for s in oh["weekly"] if day in s["days"]], why or f"weekly ({day})"


def answer(card, question, arg=None):
    base = {"business": card["name"], "demo": card["demo"], "source": "self-declared card", "last_updated": card["verification"]["last_updated"]}
    if question == "open":
        t = dt.datetime.fromisoformat(arg)
        slots, why = slots_for(card, t.date())
        if slots is None:
            return {**base, "answer": "unknown", "why": why, "advice": "ask the business"}
        hm = t.strftime("%H:%M")
        is_open = any(s["opens"] <= hm < s["closes"] for s in slots)
        return {**base, "answer": "open" if is_open else "closed", "at": arg, "slots_that_day": slots, "why": why}
    if question == "faq":
        hits = [f for f in card.get("facts_for_bots", []) if f.get("topic") == arg]
        return {**base, "answer": hits or "no answer in card; ask the business"}
    if question == "booking":
        return {**base, "answer": card["booking"], "warning": "a card never confirms a booking; the business must confirm"}
    if question == "offers":
        return {**base, "answer": card.get("offers", []), "warning": "indicative prices with the date they were checked"}
    raise SystemExit(f"unknown question {question}")


def export(card, outdir):
    os.makedirs(outdir, exist_ok=True)
    cid = card["id"]
    desc = card.get("description", {})
    skills = [
        {"id": "opening-hours", "name": "Opening hours", "description": "Is the place open on a given date/time (holidays included)?", "tags": ["hours"]},
        {"id": "faq", "name": "Questions for bots", "description": "Short answers written by the business.", "tags": ["faq"]},
        {"id": "booking-info", "name": "How to book", "description": "How to request a booking; always confirmed by a human.", "tags": ["booking"]},
    ]
    a2a = {"name": card["name"], "description": desc.get("en") or next(iter(desc.values()), card["name"]),
           "version": "0.1.0", "defaultInputModes": ["text/plain"], "defaultOutputModes": ["application/json"],
           "capabilities": {"streaming": False, "pushNotifications": False}, "skills": skills,
           "supportedInterfaces": [{"url": f"https://example.invalid/agents/{cid}/a2a", "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}],
           "_draft_note": "Placeholder interface URL: no endpoint exists. Static card only (local-agent-card/0.1)."}
    t = {"cafe_restaurant": "CafeOrCoffeeShop", "local_lodging": "LodgingBusiness", "shop": "Store"}.get(card["kind"], "LocalBusiness")
    oh = [{"@type": "OpeningHoursSpecification", "dayOfWeek": [f"https://schema.org/{['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][DAYS.index(d)]}" for d in s["days"]],
           "opens": s["opens"], "closes": s["closes"]} for s in card["opening_hours"]["weekly"]]
    ld = {"@context": "https://schema.org", "@type": t, "name": card["name"], "description": desc.get("pt") or desc.get("en"),
          "address": {"@type": "PostalAddress", "addressLocality": card["address"]["locality"], "addressRegion": card["address"]["municipality"], "addressCountry": "PT"},
          "openingHoursSpecification": oh, "knowsLanguage": card["languages"], "paymentAccepted": ", ".join(card.get("payment_methods", []))}
    if card["contact"].get("phone"): ld["telephone"] = card["contact"]["phone"]
    if card["contact"].get("email"): ld["email"] = card["contact"]["email"]
    if card["kind"] == "local_lodging":
        ld["checkinTime"], ld["checkoutTime"] = card["lodging"].get("check_in_from"), card["lodging"].get("check_out_until")
    lines = [f"# {card['name']}", "", f"> {desc.get('en') or desc.get('pt', '')}", "",
             f"- Kind: {card['kind']}" + (" (FICTIONAL DEMO)" if card["demo"] else ""),
             f"- Where: {card['address']['locality']}, {card['address']['municipality']}, Portugal",
             "- Hours: " + "; ".join(f"{','.join(s['days'])} {s['opens']}-{s['closes']}" for s in card["opening_hours"]["weekly"]),
             f"- Public holidays: {card['opening_hours'].get('public_holidays', 'ask')}",
             f"- Booking: {card['booking']['method']} ({card['booking'].get('target', '')}), always confirmed by a person",
             f"- Card: local-agent-card.json (local-agent-card/0.1), last updated {card['verification']['last_updated']}"]
    for z in card.get("zones", []):
        lines.append(f"- Near Está no Ir trip: {z.get('url', z['id'])}")
    files = {"local-agent-card.json": card, "agent-card.draft.json": a2a, "localbusiness.jsonld": ld}
    for n, o in files.items():
        json.dump(o, open(os.path.join(outdir, n), "w"), ensure_ascii=False, indent=2)
    open(os.path.join(outdir, "llms.txt"), "w").write("\n".join(lines) + "\n")
    return sorted(list(files) + ["llms.txt"])


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "validate":
        bad = 0
        for p in sys.argv[2:]:
            e = validate(json.load(open(p)))
            print(("VALID   " if not e else "INVALID ") + p); [print("   -", x) for x in e]; bad += bool(e)
        sys.exit(1 if bad else 0)
    if cmd == "export":
        card = json.load(open(sys.argv[2])); print(export(card, os.path.join(sys.argv[3], card["id"])))
    if cmd == "ask":
        print(json.dumps(answer(json.load(open(sys.argv[2])), sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None), ensure_ascii=False, indent=2))
