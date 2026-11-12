# BotVow — Specification botvow/0.1

Status: v0.1 (draft). Licence: CC BY 4.0. Key words MUST, SHOULD and MAY are used as in RFC 2119.

BotVow ("the bot's vow") is the black box for Bots: a hash-chained, co-signed record of what two
Bots agreed — who agreed what, who authorised it, and when. Bots are the core. Agents from other
AI platforms MAY record agreements too, but MUST follow exactly these rules: there are no
party-specific rules, no extensions that change the rules, and no exceptions.

## 1. Entry
Each entry is a JSON object with exactly these members (no more, no fewer; see `schema/record.schema.json`):
`spec`, `chain_id`, `seq`, `prev_hash`, `ts`, `type`, `author`, `content`, `signatures`, `entry_hash`.

- `spec` MUST be `"botvow/0.1"`.
- `seq` MUST be 0 for the genesis and increase by 1.
- `ts` is an RFC 3339 UTC time (`YYYY-MM-DDTHH:MM:SSZ`) claimed by the author.
- `author` is the key id of the author.
- `type` MUST be one of `genesis`, `proposal`, `counter`, `agreement`, `amendment`, `termination`, `seal`.

## 2. Parties and keys
- Algorithm: Ed25519. Public keys are carried raw, base64url without padding.
- `kid = "ed25519:" + hex(SHA-256(raw public key))[0:16]`.
- The genesis `content.parties` array lists every party with `kid`, `name`, `pubkey`, and optionally
  `kind` (`"bot"` or `"agent"`; default `"bot"`), `platform` and `agent_card` (A2A Agent Card URL).
  No other party fields are allowed. A verifier MUST check that each `kid` matches its `pubkey`.
- `kind` is descriptive only: a party of kind `agent` has exactly the same obligations as a `bot`.

## 3. Canonical form
`canonical(x)` = UTF-8 JSON with keys sorted lexicographically, no insignificant whitespace, no
floating-point numbers. This is a strict subset of RFC 8785 (JCS).

## 4. Signatures and hashes
- `body(e)` = `e` without `signatures` and `entry_hash`.
- Each signature is exactly `{ "kid", "alg": "Ed25519", "sig": base64url(Ed25519(canonical(body(e)))) }`.
- `entry_hash = hex(SHA-256(canonical(e without entry_hash)))`; signatures are included.
- `prev_hash` MUST equal the previous entry's `entry_hash`; for the genesis it is 64 `"0"` characters.

## 5. Signing rules
- The author MUST sign its entry.
- `genesis`, `agreement` and `seal` MUST be signed by every party listed in the genesis.
- `seal.content.entries` MUST equal the number of entries before the seal. Nothing may follow a seal.

## 6. Same rules for everyone
- `content` MUST NOT contain `rules`, `own_rules`, `exceptions`, `exception`, `rules_override` or
  `policy_override`. A chain that tries to add its own rules or exceptions is rejected, **even if every
  party signed it**.
- Unknown entry types, extra entry fields and extra party fields are rejected.

## 7. Privacy
- Raw messages MUST NOT be stored. Use `content.payload_sha256` (hex SHA-256 of the UTF-8 message).
- `content.summary` MAY be present only if `content.consent_to_publish_summary` is `true`;
  `content.summary_sha256` MUST match it.
- Public chains SHOULD NOT contain personal data. For personal matters keep the chain private and
  publish only the head hash.

## 8. Verification
A verifier MUST reject the log if any rule in sections 1–6 is broken. It SHOULD accept an optional
expected head hash and report a mismatch. Result: `VERIFY OK` or `REJECTED` with reasons.

## 9. Out of scope for v0.1
Trusted timestamps (RFC 3161), transparency logs, key rotation and revocation, binding keys to real
organisations, encryption, more than two parties in the reference tool (the format allows it).
