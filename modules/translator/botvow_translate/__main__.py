"""CLI:  python3 -m botvow_translate --to a2a|mcp|email [--a2a-version 0.3|1.0] [--catalog FILE] [--estanoir] FILE|-"""
import argparse, json, sys
from . import translate, TranslationError


def main(argv=None):
    ap = argparse.ArgumentParser(prog="botvow_translate", description="Translate (never execute) agent messages between MCP, A2A and email.")
    ap.add_argument("--to", required=True, choices=["mcp", "a2a", "email"])
    ap.add_argument("--a2a-version", default="1.0", choices=["1.0", "0.3"])
    ap.add_argument("--catalog", help="MCP tools/list JSON of the target (local file)")
    ap.add_argument("--estanoir", action="store_true", help="use the Está no Ir text extractor")
    ap.add_argument("--raw", action="store_true", help="print only the translated output")
    ap.add_argument("input")
    a = ap.parse_args(argv)
    raw = sys.stdin.read() if a.input == "-" else open(a.input, encoding="utf-8").read()
    cat = json.load(open(a.catalog)) if a.catalog else None
    ext = None
    if a.estanoir:
        from .estanoir import extract as ext
    try:
        res = translate(raw, a.to, catalog=cat, extractor=ext, a2a_version=a.a2a_version)
    except TranslationError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        return 2
    if a.raw:
        print(res["output"] if isinstance(res["output"], str) else json.dumps(res["output"], indent=2, ensure_ascii=False))
    else:
        res.pop("envelope")
        print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
