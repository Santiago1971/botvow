# Local Agent Card (local-agent-card/0.1)

A tiny, open profile so a shop, café or local lodging can answer other bots: hours (with official public holidays), offer (prices always dated), how to book (always confirmed by a person), and which Está no Ir trip it is near.

Exports to existing formats instead of inventing a protocol: A2A Agent Card (draft), schema.org JSON-LD, llms.txt.

```bash
cd modules/agent-card
python3 card_tool.py validate cards/*.json
python3 card_tool.py export cards/cafe-exemplo-do-cais.json out
python3 card_tool.py ask cards/cafe-exemplo-do-cais.json open 2026-12-08T19:30   # holiday -> Sunday hours
python3 tests/test_cards.py   # 10 tests
```

Both example cards — a café in Peso da Régua and a lodging in Sintra — are **FICTIONAL**. They are labelled `demo: true` and their names contain **FICTÍCIO** / **FICTIONAL**. They do not describe real businesses. Do not contact anyone about them.

Public holidays come from `data/feriados-pt-2026-2027.json`, a bundled snapshot of the Está no Ir dated official facts calendar (calculated from the Portuguese Labour Code rules, not an official gazette). The calendar file itself says the dates are calculated.

Schema and examples: CC BY 4.0. Code: MIT.
