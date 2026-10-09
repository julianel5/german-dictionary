# License review (blockers L1, L3, L4) — status as of 2026-10-08

## 1. L1 — Wiktextract/Kaikki (Wiktionary JSONL) 

### What is verifiably documented

- **Wiktionary content**: en.wiktionary, de.wiktionary use **CC BY-SA 4.0** (site footers). Content reuse requires attribution, share-alike, and notice of changes.
- **Wiktextract** (YLÖNEN, Niklas & TIEDER, Z. Wiktextract: Wiktionary as Machine-Readable Structured Data. LREC 2022) is a tool; tool licensing does **not** automatically license the extracted dataset. Kaikki.org cites Wiktextract and directs to raw Wiktextract dumps as the canonical source.
- **Repository state**: the raw en/de Wiktextract JSONL artefacts used in the pilot are external (`data/raw/*` never holds the pilot corpus; `data/processed/*` are gitignored). No dataset licence manifest is present in the repo for those files.
- **Pilot reality**: we know the source origin (Wiktextract dump), we do not know if the exact `*.jsonl.gz` distribution had an additional file-level licence/notice file (e.g. `LICENSE`, `README`, `METADATA`) attached to that dump.

### Known gaps (cannot be filled by code inspection alone)

| item | evidence in repo | status |
|---|---|---|
| Software licence (Wiktextract) | tool paper/citation referenced | known (tool, not data) |
| Content licence (Wiktionary CC BY-SA 4.0) | referenced in register/plan | known for wiki content, **does not prove file distribution terms** |
| Licence attached to the **specific JSONL files** consumed | none (no manifest in `data/raw`, files are external) | **UNVERIFIED** (L1) |
| Redistribution notice requirements for the extracted text dump | none explicit to the file set | unknown |
| Attribution text mandated for that dump (if different from generic wiki attribution) | none | unknown |

### Assessment

- **L1 classification:** `UNVERIFIED` (and must remain so). 
- **Cannot change without:** obtaining the dump's distribution terms (the README/LICENSE that accompanied the exact Wiktextract/Kaikki distribution we would ingest, or the upstream page stating licence for that dump), recording a `MANIFEST.json` per dataset per version (source, URL, checksum, licence, licence URL, attribution, retrieved_at), and storing it with the raw artefact (never committed). 
- **Blocking:** importing/committing any derived data (especially aggregated translation maps) would rely on unverified terms. The pilot measurement did **not** commit data and respected this.

## 2. L3 — FreeDict (CC BY-SA? vs GPLv3/AGPLv3)

### What is verifiably documented

- **FreeDict project**: publishes dictionaries as TEI P4/P5; headers typically state terms per dictionary. The pilot TEI `eng-deu.tei` header states **GPLv3 + AGPLv3** dual licensing (dataset terms as distributed). This is recorded in the pilot outputs/licence gates.
- **Wiktionary content used for en-side primary translations**: CC BY-SA 4.0.
- **Code**: MIT (repo `LICENSE`).

### Unresolved scenarios

| scenario | data involved | evidence | risk | provisional | review needed |
|---|---|---|---|---|---|
| keep separate sources (records tagged by `data_source_id`, no text merge) | CC BY-SA (en.wiktionary records) + GPLv3/AGPLv3 (FreeDict eng-deu records) in DB, displayed separately | TEI header GPLv3/AGPLv3; wiki CC BY-SA 4.0; no court precedent examined | uncertain (jurisdiction-dependent; combining in one executable/DB raises questions about derivative works and reach of copyleft) | **CAUTION** — architectural separation helps, but distribution of the combined DB/export may still be affected | legal review (copyleft reach: linked vs combined, distribution of derivatives, AGPLv3 trigger) |
| merge translation text into the same table fields (collapse into shared `text` columns) | both | as above | **high** — likely increases risk of creating a derivative that must satisfy both licences; cannot assume compatibility | **NO-GO** | legal review before any merge |
| distribute a full dump (SQL export, JSON export) | both | as above | **high** — redistribution obligations differ (CC BY-SA: SA; GPLv3/AGPLv3: copyleft + source availability) | **NO-GO** | legal review |
| offer as a network service only (no public data dump) | both | as above | different (AGPLv3 is triggered by network interaction in some interpretations; GPLv3 by distribution) — jurisdiction/interpretation varies | **PENDING** — not assumed safe | legal review |
| process FreeDict into an intermediate, source-preserving form (never replacing CC BY-SA text, provenance intact) | FreeDict only | GPLv3/AGPLv3 header present | GPLv3/AGPLv3 still apply to that processed form if distributed | **NO-GO for distribution/commit**; read-only measurement is the only safe action now | legal review |

### Assessment

- **L3 classification:** `UNVERIFIED` (no compatibility conclusion possible from evidence). 
- **Default rule:** **NO-GO to incorporate FreeDict into the application database, to merge it with Wiktionary-derived records, or to distribute any derived artefacts that include FreeDict data.** The measured `freedict_only = 11.94%` is additive value, but does not override licence risk. 
- **Evidence required:** written legal opinion or authoritative guidance covering the specific scenarios above for the jurisdiction(s) of distribution/hosting.

## 3. L4 — Attribution proposal (DRAFT, not validated)

Attribution must be **per-source and per-version**, preserve provenance, and distinguish content/code. All text below is **BORRADOR PENDIENTE DE VALIDACIÓN**.

### Required surfaces

| surface | requirement | notes |
|---|---|---|
| README (project root) | dataset attribution block per source | include licence, URL, version/date, notice of changes |
| In-app "Sources" / "About" page | visible attribution | human-readable; link to licences |
| Record provenance panel (when showing a translation) | show which source(s) contributed each equivalent/gender/form | must survive merges (join tables) |
| Exports/dumps (if ever allowed) | include full attribution + NOTICE + provenance | **not planned**; would require L1/L3 clearance |
| Data manifest (`data/sources/MANIFEST.json` or per raw dir) | machine-readable | required per ingested dataset/version |

### Draft attribution text (example)

```
English→German dictionary data sources:
- Wiktionary (en.wiktionary.org, de.wiktionary.org) content licensed under CC BY-SA 4.0. 
  Translations/equivalents and definitions derived from Wiktextract-processed dumps; 
  see source manifest for exact dump version, retrieved date, and checksum.
- FreeDict eng-deu — licensed under GPLv3 + AGPLv3 (per TEI header); used only in 
  read-only measurement. Not incorporated into the application database pending 
  legal review (see license-review.md L3).
Code: MIT License (see LICENSE).

Modifications/transformations: normalized lemmas, filtered to curated common-word lists 
for measurement only; no text copied into fixtures/seeds. Provenance tracked per record.
```

### Provenance requirements (to satisfy attribution/share-alike)

- **Dataset registry**: `data_sources(id, source_id, name, url, licence, licence_url, attribution_text, source_version, retrieved_at, checksum, processed_at, notes)`.
- **Per-record links**: join tables (`lexeme_sources`, `sense_sources`, `word_form_sources`, `translation_sources`) carrying `data_source_id`, `external_id` (source key), `confidence`, `is_primary`. A single record/translation may have multiple sources.
- **German equivalents**: store in `translations` with `language='de'`, optional `sense_id` (nullable), `gender`/tags, and mandatory provenance (`data_source_id`, `external_id`). **Do not** collapse FreeDict and Wiktionary into identical `text` if they differ; keep separate source rows.
- **De-edition enrichment**: when we attach de.wiktionary data (forms/gender/gloss), record provenance to de.wiktionary dataset.
- **Null-sense translations**: `sense_id` must remain nullable (structural fact from Wiktextract). The UI must not fabricate a sense link; provenance must still be present.
- **Notice of changes**: transformations (normalization, filtering, casefolding, merging of forms) must be recorded in dataset `notes` and/or transformation log (separating "derived" from "verbatim").

**Status:** L4 remains `UNVERIFIED` — the proposal above is coherent with the pilot findings, but its legal sufficiency for each surface/export scenario must be validated by a human reviewer.

## 4. Cross-cutting conclusions

- **L1:** `UNVERIFIED` — need dump-specific licence manifest (URL, licence, attribution, checksum). Cannot mark resolved.
- **L3:** `UNVERIFIED` — no compatibility conclusion; default **NO-GO** for combining/distributing FreeDict data. Architectural separation is necessary but not sufficient for distribution. 
- **L4:** `UNVERIFIED` — proposal exists; requires legal validation of required strings/surfaces (especially exports). 

All three blockers require **human/legal review** before authorizing any production import or data distribution. Measurement-only work is acceptable under current guardrails (no commit of corpus data).