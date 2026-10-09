# Wiktionary-only MVP (consolidated)

## Decision
- Sole source: Wiktionary/Wiktextract.
- FreeDict: out of MVP scope (coverage history retained).
- L3 blocks only if FreeDict is reintroduced.

## Requirements (pre-pilot)
- Exact dump manifest (URL, source_version, retrieved_at UTC, sha256, licence/licence_url, README/LICENSE, attribution_text). Never commit dump.
- Importer: blocking real-data by default; dry-run/simulation; idempotent; transactions per batch; rollback; homonyms; sense_id nullable; external_id missing -> deterministic key + external_id_missing=true; validation; conflicts; report.
- Small batch: 10–20 lemmas max, validated (no dupes, non-empty), only after documented authorization.
- No real import/export redistribution; no migrations/schema changes.

## Gates
- L1: UNVERIFIED until manifest complete (no inference).
- L4: Stage 1 doc + Stage 2 impl validation required per proposal.
- L3: not applicable for Wiktionary-only.

## Next step
Authorize only after manifest + approvals; run small synthetic/simulated batch under gate.
