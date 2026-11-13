#!/usr/bin/env sh
# One command: build the samples, verify them, run tamper and same-rules tests, unit tests, schema check.
set -e
cd "$(dirname "$0")"
python3 tools/botvow.py demo
echo
echo "--- CLI verify: Bot 2 Bot original ---"
python3 tools/botvow.py verify examples/bot2bot-log.json
echo "--- CLI verify: open door (Bot + agent of another AI) ---"
python3 tools/botvow.py verify examples/open-door-log.json
for f in examples/bot2bot-log-tampered.json examples/open-door-own-rules-rejected.json; do
  echo "--- CLI verify: $f (expected to be rejected) ---"
  if python3 tools/botvow.py verify "$f"; then echo "ERROR: not rejected"; exit 1; else echo "(exit 1 as expected)"; fi
done
echo "--- unit tests ---"
python3 -m unittest discover -s tests
echo "--- module tests: translator ---"
python3 modules/translator/tests/test_translate.py
echo "--- module tests: agent-card ---"
python3 modules/agent-card/tests/test_cards.py
if python3 -c "import jsonschema" 2>/dev/null; then
  echo "--- schema ---"
  python3 tools/check_schema.py examples/bot2bot-log.json
  python3 tools/check_schema.py examples/open-door-log.json
fi
