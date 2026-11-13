"""Validate a request against a target's MCP tools/list (local snapshot; never fetched here)."""

TYPES = {"string": str, "integer": int, "boolean": bool, "number": (int, float), "object": dict, "array": list}


def tools_of(catalog):
    if "result" in catalog: catalog = catalog["result"]
    return {t["name"]: t for t in catalog.get("tools", [])}


def check(env, catalog):
    notes, tools = [], tools_of(catalog)
    if env.tool not in tools:
        return [f"tool '{env.tool}' is not offered by the target (known: {sorted(tools)})"]
    schema = tools[env.tool].get("inputSchema", {})
    props = schema.get("properties", {})
    for k in list(env.arguments):
        if k not in props and schema.get("additionalProperties") is False:
            notes.append(f"argument '{k}' removed: not accepted by {env.tool}")
            env.arguments.pop(k)
            continue
        t = props.get(k, {}).get("type")
        if t in TYPES and not (isinstance(env.arguments[k], TYPES[t]) and not (t == "integer" and isinstance(env.arguments[k], bool))):
            notes.append(f"argument '{k}' should be {t}")
        lo, hi = props.get(k, {}).get("minimum"), props.get(k, {}).get("maximum")
        v = env.arguments[k]
        if isinstance(v, (int, float)) and not isinstance(v, bool) and ((lo is not None and v < lo) or (hi is not None and v > hi)):
            notes.append(f"argument '{k}'={v} outside [{lo}, {hi}]")
    for r in schema.get("required", []):
        if r not in env.arguments:
            notes.append(f"missing required argument '{r}'")
    return notes
