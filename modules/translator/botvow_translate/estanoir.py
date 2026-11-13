"""Example text->intent extractor for the Está no Ir MCP server (rule-based, no AI, PT/EN).
Other targets plug in their own extractor with the same signature: text -> (tool, args, why)."""
import re

CITIES = ["Porto", "Lisboa", "Lisbon", "Coimbra", "Braga", "Aveiro", "Faro", "Vigo", "Madrid"]


def extract(text):
    t = text.lower()
    m = re.search(r"\b(?:get_trip|viagem|trip)\s*(?:id)?\s*[:#]\s*([a-z0-9][a-z0-9-]{2,})", t)
    if m:
        return "get_trip", {"id": m.group(1)}, "trip id found"
    if re.search(r"como (pedir|peço)|how (do i|to) (ask|request)|pedir um plano", t):
        return "how_to_request", {}, "asks how to request"
    args = {}
    for c in CITIES:
        if re.search(rf"\b(de|from|desde|saindo d[eo]|a partir d[eo])\s+{c.lower()}\b", t):
            args["origin_contains"] = c
            break
    m = re.search(r"(\d+)\s*(dias?|days?)", t)
    if m:
        args["max_days"] = int(m.group(1))
    if re.search(r"sem carro|no car|without (a )?car", t): args["no_car"] = True
    if re.search(r"\b(espanha|spain)\b", t): args["country"] = "ES"
    elif re.search(r"\bportugal\b", t): args["country"] = "PT"
    if args or re.search(r"viage|trip|roteiro|escapad|fim de semana|weekend", t):
        return "search_trips", args, "trip keywords"
    return None, {}, "no rule matched"
