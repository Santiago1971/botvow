"""Core: a neutral Envelope plus parsers/renderers for each format.

Formats
  mcp          JSON-RPC 2.0 `tools/call` request, or its response (result/error)
  a2a          JSON-RPC 2.0 `SendMessage` (A2A 1.0) or `message/send` (A2A 0.3), or their responses
  email        RFC 5322 message (plain text). Structured data travels in a fenced block:
                 ---agent-data---  {json}  ---end-agent-data---
"""
from __future__ import annotations

import email
import email.policy
import json
import re
import uuid
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Any

MAX_BYTES = 64 * 1024
FENCE_START, FENCE_END = "---agent-data---", "---end-agent-data---"
A2A_STATES_10 = {"completed": "TASK_STATE_COMPLETED", "failed": "TASK_STATE_FAILED",
                 "input-required": "TASK_STATE_INPUT_REQUIRED", "working": "TASK_STATE_WORKING",
                 "rejected": "TASK_STATE_REJECTED", "canceled": "TASK_STATE_CANCELED",
                 "submitted": "TASK_STATE_SUBMITTED", "auth-required": "TASK_STATE_AUTH_REQUIRED"}
A2A_STATES_03 = {v: k for k, v in A2A_STATES_10.items()}


class TranslationError(ValueError):
    pass


@dataclass
class Envelope:
    """Format-neutral view of one agent message."""
    kind: str                                  # "request" | "response"
    tool: str | None = None                    # requested operation (MCP tool / A2A data.tool)
    arguments: dict = field(default_factory=dict)
    text: str | None = None                    # human-readable text
    data: Any = None                           # structured result (responses)
    status: str = "completed"                  # responses: completed | failed | input-required | ...
    error: dict | None = None                  # {"code": int, "message": str}
    id: Any = None                             # JSON-RPC id / Message-ID
    reply_to: str | None = None                # correlation (In-Reply-To / taskId)
    context_id: str | None = None
    sender: str | None = None
    recipient: str | None = None
    subject: str | None = None
    notes: list = field(default_factory=list)  # what was guessed or dropped


# ----------------------------------------------------------------- detection
def _load(raw):
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if len(raw.encode("utf-8")) > MAX_BYTES:
        raise TranslationError(f"input larger than {MAX_BYTES} bytes")
    s = raw.strip()
    if s.startswith("{"):
        try:
            return json.loads(s)
        except ValueError as e:
            raise TranslationError(f"invalid JSON: {e}") from None
    return raw


def detect(raw) -> str:
    obj = _load(raw)
    if isinstance(obj, str):
        return "email"
    m = obj.get("method")
    if m == "tools/call":
        return "mcp"
    if m in ("SendMessage", "message/send"):
        return "a2a"
    if "result" in obj or "error" in obj:
        r = obj.get("result")
        if isinstance(r, dict) and ("task" in r or "message" in r or r.get("kind") in ("task", "message")):
            return "a2a"
        return "mcp"
    raise TranslationError("unrecognised JSON: expected MCP tools/call, A2A SendMessage/message/send, or a JSON-RPC response")


# ----------------------------------------------------------------- MCP
def parse_mcp(o) -> Envelope:
    if o.get("method") == "tools/call":
        p = o.get("params") or {}
        if not isinstance(p.get("name"), str):
            raise TranslationError("MCP tools/call without params.name")
        return Envelope("request", tool=p["name"], arguments=p.get("arguments") or {}, id=o.get("id"))
    if "error" in o:
        e = o["error"]
        return Envelope("response", status="failed", error={"code": e.get("code"), "message": e.get("message")},
                        text=e.get("message"), id=o.get("id"))
    r = o.get("result") or {}
    texts = [c.get("text", "") for c in r.get("content", []) if c.get("type") == "text"]
    other = [c.get("type") for c in r.get("content", []) if c.get("type") != "text"]
    env = Envelope("response", text="\n".join(texts) or None, data=r.get("structuredContent"),
                   status="failed" if r.get("isError") else "completed", id=o.get("id"))
    if other:
        env.notes.append(f"non-text MCP content dropped: {other}")
    return env


def render_mcp(env: Envelope) -> dict:
    rid = env.id if env.id is not None else 1
    if env.kind == "request":
        if not env.tool:
            raise TranslationError("cannot build MCP tools/call: no tool identified (try --catalog, or target a2a/email)")
        return {"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                "params": {"name": env.tool, "arguments": env.arguments}}
    if env.error and env.status == "failed" and env.data is None and env.error.get("code") is not None:
        return {"jsonrpc": "2.0", "id": rid, "error": env.error}
    res = {"content": [{"type": "text", "text": env.text or (json.dumps(env.data, ensure_ascii=False) if env.data is not None else "")}],
           "isError": env.status == "failed"}
    if env.data is not None:
        res["structuredContent"] = env.data
    if env.status not in ("completed", "failed"):
        env.notes.append(f"MCP has no '{env.status}' state: sent as a normal result text")
    return {"jsonrpc": "2.0", "id": rid, "result": res}


# ----------------------------------------------------------------- A2A
def _parts_in(parts):
    texts, datas = [], []
    for p in parts or []:
        k = p.get("kind")
        if "text" in p and (k in (None, "text")):
            texts.append(p["text"])
        elif "data" in p and (k in (None, "data")):
            datas.append(p["data"])
    return "\n".join(texts) or None, datas


def parse_a2a(o) -> Envelope:
    if o.get("method") in ("SendMessage", "message/send"):
        msg = (o.get("params") or {}).get("message") or {}
        text, datas = _parts_in(msg.get("parts"))
        intent = next((d for d in datas if isinstance(d, dict) and "tool" in d), None)
        env = Envelope("request", text=text, id=o.get("id"), reply_to=msg.get("taskId"), context_id=msg.get("contextId"))
        if intent:
            env.tool, env.arguments = intent["tool"], intent.get("arguments") or {}
        env.notes.append(f"a2a version: {'1.0' if o['method'] == 'SendMessage' else '0.3'}")
        return env
    if "error" in o:
        e = o["error"]
        return Envelope("response", status="failed", error={"code": e.get("code"), "message": e.get("message")},
                        text=e.get("message"), id=o.get("id"))
    r = o.get("result") or {}
    task = r.get("task") if "task" in r else (r if r.get("kind") == "task" else None)
    msg = r.get("message") if "message" in r else (r if r.get("kind") == "message" else None)
    env = Envelope("response", id=o.get("id"))
    if task:
        st = task.get("status") or {}
        state = st.get("state", "completed")
        env.status = A2A_STATES_03.get(state, state)
        env.reply_to, env.context_id = task.get("id"), task.get("contextId")
        parts = [p for a in task.get("artifacts") or [] for p in a.get("parts", [])]
        if st.get("message"):
            parts = (st["message"].get("parts") or []) + parts
        env.text, datas = _parts_in(parts)
    else:
        env.text, datas = _parts_in((msg or {}).get("parts"))
    if datas:
        env.data = datas[0] if len(datas) == 1 else datas
    return env


def render_a2a(env: Envelope, version="1.0") -> dict:
    v10 = version.startswith("1")
    rid = env.id if env.id is not None else 1

    def part_text(t): return {"text": t} if v10 else {"kind": "text", "text": t}
    def part_data(d): return {"data": d, "mediaType": "application/json"} if v10 else {"kind": "data", "data": d}

    if env.kind == "request":
        parts = [part_text(env.text or describe(env))]
        if env.tool:
            parts.append(part_data({"tool": env.tool, "arguments": env.arguments}))
        msg = {"role": "ROLE_USER" if v10 else "user", "messageId": str(uuid.uuid5(uuid.NAMESPACE_URL, json.dumps([env.tool, env.arguments, env.text], sort_keys=True))), "parts": parts}
        if not v10:
            msg["kind"] = "message"
        if env.reply_to: msg["taskId"] = env.reply_to
        if env.context_id: msg["contextId"] = env.context_id
        return {"jsonrpc": "2.0", "id": rid, "method": "SendMessage" if v10 else "message/send", "params": {"message": msg}}
    if env.error and env.data is None and env.status == "failed" and env.error.get("code") is not None and env.error["code"] < 0:
        return {"jsonrpc": "2.0", "id": rid, "error": env.error}
    parts = []
    if env.text: parts.append(part_text(env.text))
    if env.data is not None: parts.append(part_data(env.data))
    state = A2A_STATES_10.get(env.status, env.status) if v10 else env.status
    task = {"id": env.reply_to or "task-" + str(rid), "status": {"state": state}, "artifacts": [{"artifactId": "result", "parts": parts}]}
    if env.context_id: task["contextId"] = env.context_id
    if v10:
        return {"jsonrpc": "2.0", "id": rid, "result": {"task": task}}
    task["kind"] = "task"
    return {"jsonrpc": "2.0", "id": rid, "result": task}


# ----------------------------------------------------------------- email
_FENCE_RE = re.compile(re.escape(FENCE_START) + r"\s*(\{.*?\})\s*" + re.escape(FENCE_END), re.S)


def parse_email(raw: str) -> Envelope:
    if not re.match(r"^[A-Za-z-]+:", raw.lstrip()):
        raw = "Subject: (no subject)\n\n" + raw          # bare text body is accepted too
    msg = email.message_from_string(raw, policy=email.policy.default)
    body_part = msg.get_body(preferencelist=("plain",)) if msg.is_multipart() else msg
    body = body_part.get_content() if body_part is not None else ""
    m = _FENCE_RE.search(body)
    data = None
    if m:
        try:
            data = json.loads(m.group(1))
        except ValueError:
            raise TranslationError("agent-data block is not valid JSON") from None
        body = (body[:m.start()] + body[m.end():]).strip()
    subject = str(msg.get("Subject", "") or "") or None
    is_reply = bool(msg.get("In-Reply-To")) or (subject or "").lower().startswith("re:")
    kind = (data or {}).get("kind") or ("response" if is_reply else "request")
    env = Envelope(kind, text=body.strip() or None, subject=subject, sender=msg.get("From"), recipient=msg.get("To"),
                   id=(data or {}).get("id", msg.get("Message-ID")), reply_to=msg.get("In-Reply-To"))
    if msg.is_multipart() and list(msg.iter_attachments()):
        env.notes.append("email attachments dropped (not translated)")
    if data:
        env.tool, env.arguments = data.get("tool"), data.get("arguments") or {}
        if kind == "response":
            env.data, env.status, env.error = data.get("data"), data.get("status", "completed"), data.get("error")
    return env


def render_email(env: Envelope, sender="translator@localhost", recipient="agent@localhost") -> str:
    m = EmailMessage()
    m["From"] = env.sender or sender
    m["To"] = env.recipient or recipient
    subj = env.subject or (f"Request: {env.tool}" if env.kind == "request" else f"Re: {env.reply_to or 'your request'} [{env.status}]")
    m["Subject"] = subj
    if env.reply_to:
        m["In-Reply-To"] = str(env.reply_to)
    m["X-Translated-By"] = "botvow-translate/0.1 (not executed)"
    block = {"kind": env.kind, "id": env.id}
    if env.kind == "request":
        block.update(tool=env.tool, arguments=env.arguments)
    else:
        block.update(status=env.status, data=env.data, error=env.error)
    human = env.text or describe(env)
    m.set_content(f"{human}\n\n{FENCE_START}\n{json.dumps(block, ensure_ascii=False, sort_keys=True)}\n{FENCE_END}\n")
    return m.as_string()


# ----------------------------------------------------------------- helpers
def describe(env: Envelope) -> str:
    if env.kind == "request":
        if not env.tool:
            return "(empty request)"
        args = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in env.arguments.items())
        return f"Please run '{env.tool}'" + (f" with {args}." if args else ".")
    if env.status == "failed":
        return "The request failed: " + ((env.error or {}).get("message") or "no reason given")
    return "Result attached." if env.data is not None else "Done."


PARSERS = {"mcp": parse_mcp, "a2a": parse_a2a, "email": lambda s: parse_email(s)}


def parse(raw, fmt: str | None = None) -> Envelope:
    obj = _load(raw)
    fmt = fmt or detect(obj)
    if fmt == "email":
        if not isinstance(obj, str):
            raise TranslationError("email input must be text")
        return parse_email(obj)
    if not isinstance(obj, dict):
        raise TranslationError(f"{fmt} input must be a JSON object")
    return PARSERS[fmt](obj)


def render(env: Envelope, to: str, a2a_version="1.0"):
    if to == "mcp": return render_mcp(env)
    if to == "a2a": return render_a2a(env, a2a_version)
    if to == "email": return render_email(env)
    raise TranslationError(f"unknown target format '{to}' (use mcp, a2a or email)")


def translate(raw, to: str, catalog=None, extractor=None, a2a_version="1.0") -> dict:
    """Translate `raw` into format `to`. Optional `catalog` = MCP tools/list result used to
    (a) infer a tool from free text via `extractor`, and (b) validate tool/arguments.
    Returns {"from","to","executed":False,"output","notes","envelope"}."""
    src = detect(raw)
    env = parse(raw, src)
    if env.kind == "request" and not env.tool and env.text and extractor:
        tool, args, why = extractor(env.text)
        if tool:
            env.tool, env.arguments = tool, args
            env.notes.append(f"tool inferred from text ({why}); please confirm")
    if catalog and env.kind == "request" and env.tool:
        from .catalog import check
        env.notes.extend(check(env, catalog))
    out = render(env, to, a2a_version)
    return {"from": src, "to": to, "executed": False, "output": out, "notes": env.notes,
            "envelope": {k: v for k, v in env.__dict__.items() if k != "notes"}}
