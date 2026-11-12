# BotVow — overview

**Vision.** BotVow is the black box for Bots: a Bot 2 Bot, tamper-evident and verifiable record of everything two Bots agree — who agreed what, who authorised it and when — signed by both. Bots are the core; agents from other AI platforms may also record agreements through an open door, but they must follow the same BotVow rules, with no rules of their own and no exceptions.

## The problem
As Bots start to negotiate and commit on behalf of people and businesses, each side keeps its own editable log and the other side can deny it. Bots need a black box of their own, like aircraft: a place where the agreement is sealed by both parties and neither can change it later.

## How it works
1. **Genesis** – the two parties list their public keys and both sign.
2. **Negotiation** – proposals and counter-proposals are stored only as hashes.
3. **Agreement** – the final terms are co-signed, optionally with who authorised them and until when.
4. **Seal** – a final co-signed entry closes the chain.
5. **Verify** – anyone can check that nothing was edited, deleted or reordered, and that nobody added their own rules.

## Example uses (illustrative)
Business purchases between Bots · bookings and cancellation terms · data-access licences (purpose, retention, no AI training) · insurance claims · logistics windows · customer-service promises · bank-detail changes with human approval · audit evidence alongside AI Act logs.

## EU AI Act
Article 12 of Regulation (EU) 2024/1689 requires high-risk AI systems to allow automatic recording of events (logs); Article 19 requires keeping them for at least six months. BotVow does not make anyone compliant by itself, but it can be tamper-evident evidence inside such logs.
Sources: https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-12 · https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-19

## Related work (checked 2026-11-12)
- Google AP2 (agent payments, mandates): https://ap2-protocol.org/ap2/specification/
- A2A protocol: https://a2a-protocol.org/latest/specification/
- Model Context Protocol: https://modelcontextprotocol.io/specification
- W3C Verifiable Credentials 2.0: https://www.w3.org/TR/vc-data-model-2.0/
- IETF draft "Selo" (signed access agreements between organisations' agents): https://datatracker.ietf.org/doc/draft-hamlett-selo-architecture/
- IETF draft PACT: https://www.ietf.org/archive/id/draft-laxsharma-pact-03.html
- IETF draft bilateral attestation: https://datatracker.ietf.org/doc/html/draft-mih-agent-bilateral-attestation-03
- IETF draft agreement evidence: https://www.ietf.org/archive/id/draft-newton-agreement-evidence-00.html
- Open Agent Protocol: https://openagentprotocol.eu/papers/accountability-in-the-agent-economy
- A2A signed-receipts extension: https://councilof.ai/spec/signed-receipts/

**What makes BotVow different:** it starts from Bots and the agreements between them; it is tiny and open; agents from other platforms are welcome but on the same rules; and it comes with a no-patent pledge. The techniques (hash chains, Ed25519 co-signatures) are not new — the bet is on simplicity, openness and one set of rules for everyone.

## Risks
Name/trademark checks still pending (EUIPO, INPI, USPTO) · a third party has declared a pending patent in a neighbouring area · crowded field · legal value is evidence only · key identity · GDPR (no personal data in public chains) · adoption.
