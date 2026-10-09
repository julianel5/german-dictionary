# Pilot authorization template (Wiktionary-only, 10–20 lemmas)

## Manifest (required)
- Dataset: Wiktionary/Wiktextract (exact source)
- URL: 
- source_version: 
- retrieved_at (UTC): 
- sha256: 
- licence: 
- licence_url: 
- README/LICENSE path/distributed terms: 
- attribution_text: 

## Approvals
- [ ] L1 (license/dump) approved (documented)
- [ ] L4 Stage 1 approved
- [ ] L3: N/A (FreeDict not included)
- [ ] L4 Stage 2 verification planned

## Execution
- Dry-run first (simulation)
- Batch size: <= 20, validated
- Block real import enforced; idempotent + transaction + rollback
- Provenance: deterministic key if external_id missing; external_id_missing=true; nullable sense_id preserved

Evidence to attach: manifest, approval notes, dry-run report, run report, hashes.
