# Protocol translator (MCP ↔ A2A ↔ email)

Translate — never execute — agent messages between **MCP** (`tools/call` + results), **A2A 1.0** (`SendMessage`) / **A2A 0.3** (`message/send`) (requests, tasks, failures) and plain **email** (RFC 5322 with an `---agent-data---` block).

Standard library only. No network calls, nothing stored. This module is a public dictionary of formats, not a gateway: it never runs the request.

```bash
cd modules/translator
python3 -m botvow_translate --to a2a examples/01-mcp-request.json
python3 -m botvow_translate --to mcp --catalog catalog/mcp-tools-list.json --estanoir examples/04-email-request.eml
python3 -m botvow_translate --to email --raw examples/06-a2a-1.0-failed-task.json
python3 tests/test_translate.py          # 18 tests
python3 serve_local.py 8787              # local only: POST http://127.0.0.1:8787/translate?to=a2a
```

Output: `{"from", "to", "executed": false, "output", "notes"}` — `notes` lists anything guessed, removed or lost.

| MCP | A2A 1.0 | A2A 0.3 | Email |
|---|---|---|---|
| `tools/call` `{name, arguments}` | `SendMessage`, part `{data:{tool, arguments}}` + `{text}` | `message/send`, `{kind:"data"}` | Subject `Request: <tool>`, body + `---agent-data---` |
| `result.content[].text` / `structuredContent` | `task.artifacts[].parts` | same, `kind:"task"` | body + data block |
| `isError: true` | `TASK_STATE_FAILED` | `failed` | `[failed]` in subject |
| JSON-RPC `error` | JSON-RPC `error` | JSON-RPC `error` | data block `error` |
| id | id / `taskId` | id / `taskId` | `Message-ID` / `In-Reply-To` |

`catalog/` holds a local snapshot (11/11/2026) of the Está no Ir MCP `tools/list` and A2A Agent Card, used for validation only.

Licence: MIT (code), same as the rest of this repository.
