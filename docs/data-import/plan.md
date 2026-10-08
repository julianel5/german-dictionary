# Real German dictionary data import: plan

Design document for importing real lexical data into the dictionary.
**Status: design only.** No dataset was downloaded, no external data was
imported, no schema was changed, no migration was created, and no
production behaviour was modified in producing this plan. Candidate-source
facts live in [`source-register.md`](source-register.md).

The product goal driving this plan: **Spanish translations are the primary
entry-page content; German monolingual definitions are complementary.**

---

## 1. Existing data-model findings

The schema (`apps/api/app/orm/models.py`, migration
`4ba08e47a971_initial_schema.py`) was audited together with the import
contract (`scripts/normalized.py`), the loader (`scripts/dbload.py`), the
raw→processed pipeline (`scripts/import/pipeline.py`) and the fixture set
(`data/fixtures/`). Summary:

| area | today | implication for real data |
|---|---|---|
| German headword | `lexemes.lemma`, `normalized_lemma`, `part_of_speech`, `gender`, `register`, `domain` | maps cleanly onto Wiktextract entries |
| German definitions | `senses.definition` (single text column), `sense_index`, `register`, `domain` | can hold German Wiktionary definitions |
| **Spanish translations** | **no dedicated field/table** — only the convention that a definition may read `"<english gloss> — <german explanation>"` | **gap**: bilingual equivalents have nowhere first-class to live |
| surface forms / inflection | `word_forms` + `morphological_features` (case/number/gender/person/tense/mood/degree/voice/verb_form/adjective_form + JSON `extra`) | fine; German Wiktionary inflections need mapping to these enums |
| examples | `example_sentences` + `example_words` (offsets), optional `translation`, `source` free-text | `source` is the **only** provenance-like field, and only on examples |
| synonyms / relations | `lexical_relations(source, target, relation_type)`; unique `(source,target,type)` | usable, but targets must resolve to imported lexemes |
| frequency | `frequencies(corpus, rank, count, word_form_id?)`; unique `(corpus, lexeme, word_form)` | no candidate source provides this yet |
| **provenance** | **none** on `lexemes`/`senses`/`word_forms`; `examples.source` is free text | **gap**: no dataset id, source url, external id, retrieval date, or confidence |
| licensing / attribution | `data/raw/README.md` describes a `MANIFEST.json`, but nothing validates it; no dataset-level attribution file | **gap**: cannot store required notices |
| identity / dedupe | loader ids are deterministic `uuid5`; **no DB uniqueness** on `(language, normalized_lemma, part_of_speech)` | cross-source merging needs a stable key + a constraint |
| missing data | fields nullable where optional; "missing stays missing" | keep — never fabricate translations/inflections/frequency |

Import contract (`scripts/normalized.py`) currently models a **single,
unattributed** `NormalizedDictionary` (lexemes → senses/forms/relations/
examples) plus `NormalizedFrequency`. It validates shapes but carries **no
source identity**. Real imports will need the contract extended (a later,
separate milestone).

**Bottom line:** the schema supports German headwords, definitions,
inflection, examples, relations and frequency, but has **no home for
Spanish translations and no provenance at all**. Both are prerequisites for
a real bilingual import, and both require a migration that this milestone
does **not** create.

---

## 2. Candidate-source comparison

Details and citations: [`source-register.md`](source-register.md).
Licensing statuses from that register, verified only against landing pages.

| source | gives | format | size | de-inflection | es-translations | de-definitions | licence status |
|---|---|---|---|---|---|---|---|
| kaikki **de.wiktionary** (Wiktextract) | German headwords, German definitions, inflections, gender, examples, relations | JSONL | 2.9 GB raw / 294 MB gz | **yes** (needs mapping) | no | **yes (German)** | CC BY-SA 4.0 (page-verified) |
| kaikki **es.wiktionary** (Wiktextract) | Spanish-language glosses/translations (for all languages) | JSONL | 1.1 GB raw / 98 MB gz | partial/unclear | **possible** (coverage unknown) | no | CC BY-SA 4.0 (page-verified) |
| **FreeDict deu-spa** | German→Spanish translation equivalents | TEI XML (source), StarDict/dictd | 36,744 headwords | no | **yes** | no | **unverified** (per-dictionary; "majority GPL") |
| FreeDict deu-eng + eng-spa | pivot to widen Spanish coverage | TEI XML | 517,534 / 64,258 | no | indirect | no | unverified |
| corpus frequency (not selected) | frequency ranks | — | — | — | — | — | open gap |

Notes that shape the recommendation:

- **No single source satisfies the product goal.** Spanish translations and
  German monolingual definitions come from different places.
- Wiktextract JSONL is *raw* and multilingual within each edition; the
  importer must filter to the German-language sections and map the
  Wiktextract object model to our relational one.
- FreeDict is **translations only** (no definitions, inflection or
  frequency) and its licence is unverified — it is complementary, not a
  drop-in replacement for Wiktionary, and vice versa.
- These sources are **complementary, not interchangeable**; treating them
  as one is a design error.

---

## 3. Licensing and attribution

Verified statements (from the landing pages only):

- **de.wiktionary.org** and **es.wiktionary.org** both display **CC BY-SA
  4.0** in their site footers; de.wiktionary also documents historical
  **GFDL** contributions. Attribution **and share-alike** apply to reused
  text.
- **kaikki.org** asks users to **cite** Ylonen (Wiktextract, LREC 2022) and
  link to kaikki.org. Wiktextract *software* licensing governs the tool,
  not the extracted text.
- **FreeDict** states each dictionary has its own terms in the TEI header,
  and that "the majority" are **GPL**; bundling GPL data has consequences
  and the deu-spa header was **not** inspected.

Design consequences:

1. **Dataset-level attribution is mandatory.** Keep the existing MIT *code*
   licence separate from a future *data* licence/attribution file. Add a
   machine-readable source manifest (the `data/raw/README.md` idea, but
   enforced) and surface attribution in README and in-app.
2. **Entry-level provenance is needed so notice obligations survive
   merges** (§4): if one sense came from CC BY-SA Wiktionary and another
   from GPL FreeDict, the product must be able to say so.
3. **Share-alike reach is unresolved.** Combining CC BY-SA text with GPL
   data in one derived database may create incompatible obligations.
   Flag for legal review; a possible mitigation is to keep sources in
   separate records/sections rather than merging text within a field, and
   to attribute per record.
4. Do **not** label any dataset's licence "verified" until the artefact's
   own terms are inspected (see register).

---

## 4. Proposed provenance model

Requirement: provenance must **survive merges** and support per-record
attribution, without changing existing columns' meaning.

Proposed (to be delivered in a **future** migration — *not created here*):

### 4.1 `data_sources` (dataset registry)

One row per ingested dataset/version:

`id` (PK), `source_id` (stable slug, e.g. `de-wiktionary-wiktextract`),
`name`, `url`, `licence`, `licence_url`, `attribution_text`,
`retrieved_at`, `source_version` (dump/extract date or dict version),
`checksum`, `processed_at`, `notes`.

### 4.2 Record-level provenance

Link records to sources with a stable external key so re-imports are
idempotent and merges are traceable. Two viable shapes:

- **Join tables** (recommended): `lexeme_sources`, `sense_sources`,
  `word_form_sources`, each `(record_id, data_source_id, external_id,
  confidence, is_primary)` with a unique `(record_id, data_source_id,
  external_id)`. Many-to-many; a record merged from two sources keeps both
  rows; `is_primary` marks the displayed origin.
- **Single polymorphic table** `record_provenance(record_type, record_id,
  data_source_id, external_id, confidence, is_primary)` — fewer tables,
  weaker FKs.

Recommendation: **join tables** for real referential integrity; they can be
added later without touching existing payload columns.

### 4.3 Identity & dedupe key

- Add the DB uniqueness constraint **`(language, normalized_lemma,
  part_of_speech)`** on `lexemes` (already recommended by the MVP audit)
  so cross-source merges have a deterministic key.
- Loader already derives deterministic `uuid5` ids; keep that for
  reproducibility, and store each source's own id in `external_id`.

### 4.4 Modelling Spanish translations

Two options for the **primary** product content:

- **A. `senses` gains a translated-gloss field** (e.g. `gloss_language` +
  `gloss`) reusing the existing `sense` rows. Minimal, but mixes
  monolingual and bilingual senses in one shape.
- **B. New `translations` table** `(lexeme_id? , sense_id?, language,
  text, data_source_id, …)`. Cleaner separation of German definition vs
  Spanish equivalent, and gives provenance a natural home.

Recommendation: **B** (new `translations` table) — it matches the product
goal (Spanish primary, German definition complementary), keeps the two
content types addressable independently, and carries `${data_source_id}`.
This is the main schema decision needing approval (§9).

---

## 5. Recommended initial source combination

For the **pilot** (not the full import):

1. **kaikki de.wiktionary (Wiktextract JSONL)** — primary source of German
   headwords, German definitions, gender/POS, inflections, examples,
   relations.
2. **FreeDict deu-spa (TEI XML)** — source of **Spanish translation
   equivalents**, subject to licence confirmation.
3. **kaikki es.wiktionary** — *optional*, deferred until German-lemma
   coverage is measured; do not depend on it for the pilot.

Rationale: (1) is the only source that supplies German monolingual
definitions **and** inflection; (2) directly supplies the primary Spanish
content for a bilingual dictionary; (3) is uncertain and larger than
needed. Frequency and any English gloss remain out of scope for the pilot.

---

## 6. Pilot: sample and acceptance criteria

Scope: **~100–500 German entries**, hand-selected from the sources' own
data (no full download; per the constraints, this is a design target).

**Mandatory test words** (exercise the hard cases):

| word | case exercised |
|---|---|
| gehen / ging / gegangen | strong verb, principal parts, participle |
| Haus / Häuser / Häusern | noun gender + plural + dative plural |
| Kind / Kinder | noun plural |
| schnell (+ Komparativ/Superlativ) | adjective comparison |
| a separable verb (e.g. aufstehen / steht auf / aufgestanden) | separable verb forms |
| a multi-sense word (e.g. Bank or gehen) | sense separation |
| a word **with** an ES translation | translations table populated |
| a word **without** an ES translation | missing stays missing |
| a word **with** a German mono definition | definitions populated |
| a word **without** a mono definition | missing stays missing |

**Acceptance criteria** (all must hold for the pilot to pass):

- Every entry resolves via `GET /api/entries/{id}` and appears in
  `GET /api/search` with an explicit `queryType`.
- Inflected forms are searchable (`Häusern`, `gegangen`, `ging` → correct
  lemma) with the right `matchType`.
- Spanish translations are present where the source has them and **absent
  where it does not** (no fabrication, no empty-string placeholders).
- German definitions render on the entry page; absence is a clean omission.
- Per-record provenance is recorded: each sense/translation/form can be
  traced to a `data_source` + `external_id`.
- Re-running the importer is **idempotent** (same counts, no duplicates).
- Import produces a **report**: counts created/updated/skipped and a list of
  validation errors.
- The existing fixture dataset still loads and all current tests pass.

---

## 7. Import pipeline design

Ten stages. Stages 1–2 are the only ones that touch the network and are
**gated behind explicit approval**; everything else runs locally.

1. **Download** — fetch the selected artefact to `data/raw/<source>/`.
   Nothing downloads automatically (matches `data/raw/README.md`). Record
   URL + size.
2. **Verify / metadata** — check size/checksum (FreeDict ships `.sha512`);
   record extraction/version dates; write `MANIFEST.json` per source.
3. **Parse** — per adapter: JSONL line reader filtered to
   `lang_code == "de"` for Wiktextract; TEI XML parser for FreeDict.
4. **Normalize** — Unicode **NFC**, whitespace, apostrophes; reuse the
   existing `normalize()`/`_clean` rules so imported data matches search
   behaviour. Reject records that fail validation.
5. **Map entities** — source model → our model (`lexeme`, `senses`,
   `word_forms` + `morphological_features`, `translations`,
   `lexical_relations`, `example_sentences`/`example_words`). Unmappable
   features go to `morphological_features.extra` rather than being dropped.
6. **Dedupe / cross-source match** — key on `(language, normalized_lemma,
   part_of_speech)`; resolve form collisions; the merge must **never lose**
   a source link.
7. **Preserve provenance** — attach `data_source_id` + `external_id` to
   every record and mark `is_primary` (translation source vs definition
   source). Provenance survives the merge from §6.
8. **Validate / report** — schema validation (extend `scripts/normalized.py`
   for source identity), plus counters and a diffable error report.
9. **Idempotent DB import** — extend `scripts/dbload.py` / `DatabaseLoader`
   patterns: deterministic ids, upsert, dry-run mode, single transaction
   per batch.
10. **Stats / error report** — machine-readable summary (per source, per
    stage) written to `data/processed/` and printed.

New adapters live under `scripts/import/sources/` (one module per source)
implementing a common interface, so additional sources are additive. The
existing fixture path (`scripts/fixtures.py` → `scripts/dbload.py`) stays
untouched.

---

## 8. API / frontend compatibility findings

Current contract (`apps/api/app/schemas/entries.py`,
`packages/shared-types/index.d.ts`, entry page `apps/web/app/pages/entries/[id].vue`):

- `EntryDetailResponse` has **no translations field** and **no provenance
  field**. `SenseDTO.definition` is a single string rendered as
  "Bedeutungen".
- The **frontend already supports** a bilingual-ish display: examples have
  an optional `translation`, and the entry page renders it. There is no
  dedicated Spanish-translation block for a lexeme/sense.
- `search` results expose a single `definition: string | null`; adding
  translations/provenance is therefore **additive** and backward-compatible.

Required contract changes (additive, in the implementing milestone):

1. Add `translations` to `EntryDetailResponse` and to the shared types.
2. Add an optional `provenance`/`source` object (dataset name + licence +
   attribution) at entry level and/or per sense.
3. Surface a "Quellen / Sources" attribution area (entry-level or global).

Rendering rule for the new UI: **Spanish translation is primary**, the
German definition is shown as the complementary explanation. Copy the
existing camelCase-on-the-wire convention and `populate_by_name=True`.

No existing field changes meaning, so current clients keep working.

---

## 9. Risks, unknowns, decisions needing approval

| # | item | type | note |
|---|---|---|---|
| R1 | FreeDict **deu-spa licence** unverified (TEI header) | unknown | may be GPL; blocks committing derived data |
| R2 | CC BY-SA **share-alike** vs GPL compatibility when merging | risk | possibly needs legal review |
| R3 | kaikki JSONL **per-file licence/manifest** unclear | unknown | confirm before import |
| R4 | **Spanish coverage** for German lemmas in es.wiktionary unmeasured | unknown | don't depend on it for the pilot |
| R5 | **Frequency** source absent | gap | fixture corpus is synthetic; product frequency stays fake/deferred |
| R6 | Wiktextract schema is rich/free-form; mapping to our enums is lossy | risk | use `extra` JSON; document unmapped features |
| R7 | French/other-language entries inside a "German" edition | risk | filter to `lang_code == "de"` |
| D1 | **New `translations` table** (option A vs B, §4.4) | decision | recommended: B |
| D2 | **Provenance shape** (join tables vs polymorphic) | decision | recommended: join tables |
| D3 | **Data licence** for the repo (separate from MIT code) | decision | required before committing any real data |
| D4 | Whether to add the **identity uniqueness constraint** | decision | recommended: yes |
| D5 | Whether to ship **any** derived data in-repo at all | decision | depends on R1/R2 |
| D6 | Attribution UX (entry-level vs global "Sources" page) | decision | affects API shape |

None of these decisions are made by this document; they are inputs to the
next milestone.

---

## 10. Prioritized next-milestone plan

Ordered so each step unblocks trustworthy work on real data. **No code
changes are implied by this document.**

1. **Resolve licensing** (R1–R3): inspect the FreeDict deu-spa TEI header
   and the kaikki file manifest; get a decision on R2/D3. **Blocker.**
2. **Measure coverage** (R4): scan (not fully import) the de/es Wiktextract
   JSONL and FreeDict for the mandatory pilot words; record hit rates.
3. **Extend the schema** (D1–D4): `translations` table, provenance
   (join tables), identity uniqueness constraint — delivered as an Alembic
   migration in that milestone.
4. **Extend the import contract & adapters**: source identity in
   `scripts/normalized.py`; `scripts/import/sources/` adapters for
   Wiktextract and FreeDict.
5. **Run the pilot** (§6) with the acceptance criteria; produce the report.
6. **Expose it**: additive API fields (`translations`, `provenance`) +
   shared types + entry-page UI with Spanish primary / German complementary
   + a "Quellen" attribution area.
7. **Attribution & manifest**: enforced `MANIFEST.json`, dataset-level
   attribution file, README/in-app notices.

Each step should land as a small, reviewable unit with tests, following the
repository's existing workflow. Nothing in steps 1–7 should break the
current fixture-based demonstration, which remains the default data set
until a real import is explicitly approved.
