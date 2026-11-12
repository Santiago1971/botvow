# BotVow roadmap

No dates are promised. Each phase is done when its checks pass.

## Phase 1 — Prototype (this repository, v0.1)
- [x] Format botvow/0.1, JSON Schema, reference verifier in Python
- [x] Bot 2 Bot sample and open-door sample (Bot + agent of another AI, same rules)
- [x] Tamper tests and same-rules tests (own rules / exceptions rejected, even co-signed)
- [ ] JavaScript verifier (browser and Node)
- [ ] A2A binding (chain as task metadata) and a small MCP server with two tools: `seal` and `verify`

## Phase 2 — Test
- [ ] RFC 8785 conformance tests for the canonical form
- [ ] Optional trusted timestamp (RFC 3161) and optional head-hash anchoring in a transparency log
- [ ] Key binding to a domain or signed A2A Agent Card
- [ ] External review by independent developers

## Phase 3 — Open launch
- [ ] Project page and documentation in English and Portuguese
- [ ] Trademark check (EUIPO, INPI, USPTO) and legal opinion before any wider launch
- [ ] Invite Bot builders and agent platforms to implement the same rules
- [ ] No fees: the goal is adoption
