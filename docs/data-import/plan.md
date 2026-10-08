# Real English → German dictionary data import: plan

Design document for importing real lexical data into the dictionary.
**Status: design only.** No dataset was downloaded, no external data was
imported, no schema was changed, no migration was created, and no
production behaviour was modified in producing this plan. Candidate-source
facts live in [`source-register.md`](source-register.md); the proposed
measurement method lives in [`coverage-study.md`](coverage-study.md).

The product goal driving this plan: **the dictionary is English → German.**
The entry headword is the **English** word; **German translation
equivalents are the primary lexical content**; English definitions are
supplementary; German-language definitions and German inflections/examples
are complementary enrichment; Spanish is optional/secondary.

> **Direction correction (read first).** An earlier revision of this plan
> and of [`source-register.md`](source-register.md) was written for a
> **Spanish-primary** product: German headword, Spanish translations primary,
> German monolingual definitions complementary, `kaikki de.wiktionary` +
> `FreeDict deu-spa` as the pilot sources. **Those recommendations are
> void.** Specifically the following earlier choices are superseded:
> - *"Spanish translations are the primary entry-page content"* — replaced by
>   **German translation equivalents are primary**.
> - *"kaikki de.wiktionary as the primary headword source"* — replaced by
>   **kaikki en.wiktionary (English headwords)** as primary; de.wiktionary is
>   now *complementary*.
> - *"FreeDict deu-spa as the primary translation source"* — replaced by
>   **FreeDict eng-deu** as an *optional supplementary* translation source.
> - Any Spanish-coverage risk (old R4) is downgraded: Spanish is no longer a
>   completeness requirement.

---

## 1. Existing data-model findings

The schema (`apps/api/app/orm/models.py`, migration
`4ba08e47a971_initial_schema.py`) was audited together with the import
contract (`scripts/normalized.py`), the loader (`scripts/dbload.py`), the
raw→processed pipeline (`scripts/import/pipeline.py`) and the fixture set
(`data/fixtures/`). Summary:

| area | today | implication for real data |
|---|---|---|
| headword | `lexemes.lemma`, `normalized_lemma`, `part_of_speech`, `gender`, `register`, `domain`, **`language` default `"de"`** | the **English** headword becomes the lexeme; the `language` default of `"de"` must become `"en"` for these rows (or be set explicitly per record) |
| definitions (English) | `senses.definition` (single text column), `sense_index`, `register`, `domain` | can hold en.wiktionary English glosses (supplementary) |
| **German translations** | **no dedicated field/table** — the fixture only encodes a `"<english gloss> — <german explanation>"` convention inside `definition` | **gap**: the primary bilingual content has nowhere first-class to live |
| surface forms / inflection | `word_forms` + `morphological_features` (case/number/gender/person/tense/mood/degree/voice/verb_form/adjective_form + JSON `extra`) | fine; German inflections (of the German equivalents) and English inflected forms both need mapping to these enums, with a language distinction |
| examples | `example_sentences` + `example_words` (offsets), optional `translation`, `source` free-text | `source` is the **only** provenance-like field, and only on examples |
| synonyms / relations | `lexical_relations(source, target, relation_type)`; unique `(source,target,type)` | usable, but targets must resolve to imported lexemes |
| frequency | `frequencies(corpus, rank, count, word_form_id?)`; unique `(corpus, lexeme, word_form)` | no candidate source provides this yet |
| **provenance** | **none** on `lexemes`/`senses`/`word_forms`; `examples.source` is free text | **gap**: no dataset id, source url, external id, retrieval date, or confidence |
| licensing / attribution | `data/raw/README.md` describes a `MANIFEST.json`, but nothing validates it; no dataset-level attribution file | **gap**: cannot store required notices |
| identity / dedupe | loader ids are deterministic `uuid5`; **no DB uniqueness** on `(language, normalized_lemma, part_of_speech)` | cross-source merging needs a stable key + a constraint |
| search/morphology language | `MORPHOLOGY_ENGINE` uses a **German** model (`de_core_news_sm`) and German `normalize()` rules | the searchable surface is now **English**; this is a compatibility finding (§8), **not changed here** |
| missing data | fields nullable where optional; "missing stays missing" | keep — never fabricate translations/inflections/frequency |

Import contract (`scripts/normalized.py`) currently models a **single,
unattributed** `NormalizedDictionary` (lexemes → senses/forms/relations/
examples) plus `NormalizedFrequency`. It validates shapes but carries **no
source identity** and **no language** field on lexemes. Real imports will
need the contract extended (a later, separate milestone).

**Bottom line:** the schema supports headwords, definitions, inflection,
examples, relations and frequency, but has **no home for the German
translation equivalents and no provenance at all**, and it assumes
German-language headwords/morphology. All three are prerequisites for a real
English → German import and require a migration this milestone does **not**
create.

---

## 2. Candidate-source comparison

Details and citations: [`source-register.md`](source-register.md).
Licensing statuses are verified only against landing pages.

| source | gives | format | size | English headwords | **German translations** | German inflections | German-language defs | licence status |
|---|---|---|---|---|---|---|---|---|
| kaikki **en.wiktionary** (Wiktextract) | English headwords, English definitions, translations into all languages, English forms, examples, relations, pronunciation; German (`de`) entries too | JSONL | 23.9 GB raw / 2.8 GB gz | **yes** | **yes** (`translations`, incl. `de`) | via `de` entries (captured) | no (its `de` entries gloss in English) | CC BY-SA 4.0 (page-verified) |
| kaikki **de.wiktionary** (Wiktextract) | German headwords, **German definitions**, gender, declension/conjugation, examples, relations | JSONL | 2.9 GB raw / 294 MB gz | no | no | **yes** | **yes (German)** | CC BY-SA 4.0 (page-verified) |
| **FreeDict eng-deu** | English→German translation equivalents | TEI XML (source), StarDict/dictd | 460,315 headwords | **yes** | **yes** | no | no | **unverified** (per-dictionary; "majority GPL") |
| kaikki **es.wiktionary** | Spanish-language glosses/translations (optional) | JSONL | 1.1 GB raw / 98 MB gz | — | — | — | — | CC BY-SA 4.0 (page-verified) |
| corpus frequency (not selected) | frequency ranks | — | — | — | — | — | — | open gap |

Source-derived vs mappable vs inferred vs missing (English → German):

| needed content | en.wiktionary | de.wiktionary | FreeDict eng-deu |
|---|---|---|---|
| English headword + POS | **provided** (`lang_code == "en"`) | missing | provided (headword) |
| English definitions | **provided** (glosses) | missing | missing |
| German translation equivalents | **provided** (`translations[]`, `code: de`) | missing | **provided** |
| sense→translation association | **provided** (per-sense `translations`) + top-level; association reliable but not always 1:1 | missing | coarse (headword-level; senses not encoded) |
| German gender/grammatical labels | on `de` entries + `tags` in translations | **provided** | missing |
| German inflections (declension/conjugation) | mappable via `de` entries | **provided** (native) | missing |
| German-language definitions | missing (gloss is English) | **provided** | missing |
| English inflected forms | **provided** (`forms`) | missing | missing |
| examples (+ translations) | **provided** (`senses[].examples`) | provided (German) | missing |
| synonyms/lexical relations | provided | provided | missing |
| pronunciation/IPA/audio | provided | partial | missing |
| corpus frequency | missing | missing | missing |

Notes that shape the recommendation:

- **No single source satisfies the product goal.** German translation
  equivalents come from en.wiktionary (or FreeDict eng-deu); German-language
  definitions come from de.wiktionary; the two must be merged carefully.
- Wiktextract JSONL is *raw* and multilingual within each edition; the
  importer must filter to the relevant `lang_code` sections (`en` for
  headwords, `de` for German-side enrichment) and map the Wiktextract object
  model to our relational one.
- FreeDict eng-deu is **translations only** (no definitions, inflection or
  frequency), its licence is unverified, and it does not encode sense
  distinctions — so it is *supplementary*, never the primary source, and must
  not be merged merely because a string matches.
- **The source must not be asked to supply data it does not have.** German
  grammatical features/definitions absent from a source stay absent; they are
  never inferred.

---

## 3. Licensing and attribution

Verified statements (from the landing pages only):

- **en.wiktionary.org**, **de.wiktionary.org** and **es.wiktionary.org** all
  display **CC BY-SA 4.0** in their site footers; de.wiktionary also
  documents historical **GFDL** contributions. Attribution **and
  share-alike** apply to reused text.
- **kaikki.org** asks users to **cite** Ylonen (Wiktextract, LREC 2022) and
  link to kaikki.org. Wiktextract *software* licensing governs the tool, not
  the extracted text.
- **FreeDict** states each dictionary has its own terms in the TEI header,
  and that "the majority" are **GPL**; bundling GPL data has consequences
  and the eng-deu header was **not** inspected (the metadata API exposes no
  licence field).

Design consequences:

1. **Dataset-level attribution is mandatory.** Keep the existing MIT *code*
   licence separate from a future *data* licence/attribution file. Add a
   machine-readable source manifest (the `data/raw/README.md` idea, but
   enforced) and surface attribution in README and in-app.
2. **Entry-level provenance is needed so notice obligations survive
   merges** (§4): if the German equivalent came from CC BY-SA Wiktionary and
   the German inflection from another CC BY-SA edition, or a translation from
   GPL FreeDict, the product must be able to say so.
3. **Share-alike reach is unresolved.** Combining CC BY-SA text with GPL
   data in one derived database may create incompatible obligations. Flag for
   legal review; a possible mitigation is to keep sources in separate
   records/sections rather than merging text within a field, and to attribute
   per record.
4. Do **not** label any dataset's licence "verified" until the artefact's
   own terms are inspected (see register).

---

## 4. Proposed provenance model

Requirement: provenance must **survive merges** and support per-record
attribution, without changing existing columns' meaning.

Proposed (to be delivered in a **future** migration — *not created here*):

### 4.1 `data_sources` (dataset registry)

One row per ingested dataset/version:

`id` (PK), `source_id` (stable slug, e.g. `en-wiktionary-wiktextract`),
`name`, `url`, `licence`, `licence_url`, `attribution_text`,
`retrieved_at`, `source_version` (dump/extract date or dict version),
`checksum`, `processed_at`, `notes`.

### 4.2 Record-level provenance

Link records to sources with a stable external key so re-imports are
idempotent and merges are traceable. Two viable shapes:

- **Join tables** (recommended): `lexeme_sources`, `sense_sources`,
  `word_form_sources`, `translation_sources`, each `(record_id,
  data_source_id, external_id, confidence, is_primary)` with a unique
  `(record_id, data_source_id, external_id)`. Many-to-many; a record merged
  from two sources keeps both rows; `is_primary` marks the displayed origin.
- **Single polymorphic table** `record_provenance(record_type, record_id,
  data_source_id, external_id, confidence, is_primary)` — fewer tables,
  weaker FKs.

Recommendation: **join tables** for real referential integrity; they can be
added later without touching existing payload columns.

### 4.3 Identity & dedupe key

- Add the DB uniqueness constraint **`(language, normalized_lemma,
  part_of_speech)`** on `lexemes` (already recommended by the MVP audit)
  so cross-source merges have a deterministic key. With English headwords,
  `language` is `"en"` for these rows.
- Loader already derives deterministic `uuid5` ids; keep that for
  reproducibility, and store each source's own id in `external_id`.

### 4.4 Modelling German translation equivalents

Two options for the **primary** product content:

- **A. `senses` gains a translated-gloss field** (e.g. `gloss_language` +
  `gloss`) reusing the existing `sense` rows. Minimal, but mixes English
  definitions and German equivalents in one shape.
- **B. New `translations` table** `(lexeme_id?, sense_id?, language, text,
  gender?, data_source_id, …)`. Cleaner separation of the English definition
  (supplementary) from the German equivalent (primary), and gives provenance
  and grammatical labels a natural home.

Recommendation: **B** (new `translations` table) — it matches the product
goal (German equivalents primary, English definition supplementary), keeps
the two content types addressable independently, supports **multiple German
equivalents per sense**, and carries `${data_source_id}`. The table must not
be coupled to a single provider: it should store `language` (target
language), an optional `sense_id`, an optional grammatical `gender`/`tags`
payload, and provenance. This is the main schema decision needing approval
(§9).

---

## 5. Recommended initial source combination

For the **pilot** (not the full import):

1. **kaikki en.wiktionary (Wiktextract JSONL)** — **primary** source of
   English headwords, English definitions (supplementary), German
   translation equivalents (primary), English inflected forms, examples and
   relations.
2. **kaikki de.wiktionary (Wiktextract JSONL)** — **complementary** source of
   German-language definitions, German gender, declension/conjugation and
   examples for the German equivalents, subject to matching (never merged on
   string similarity alone).
3. **FreeDict eng-deu (TEI XML)** — **optional supplementary** German
   equivalents, subject to licence confirmation; adds coverage but no senses
   or inflection.
4. **Spanish sources** — deferred; Spanish is not required for completeness.

Rationale: (1) is the only source that supplies **English headwords and their
German translations together with sense associations**; (2) adds the
German-language definition/inflection content that (1) cannot provide; (3) is
optional additional translation coverage. Frequency remains out of scope for
the pilot.

---

## 6. Pilot: sample and acceptance criteria

Scope: **~100–500 English entries**, hand-selected across the case classes in
[`coverage-study.md`](coverage-study.md) (no full download; per the
constraints, this is a design target). The sample-selection method must be
documented and must not only include entries known to work.

**Mandatory test words** (exercise the hard cases):

| word | case exercised |
|---|---|
| a common noun (e.g. `house`) + German equivalent incl. gender | noun + German gender label |
| a common verb (e.g. `go`) | verb senses + multiple German equivalents |
| an irregular English verb (e.g. `sing` / `sang` / `sung`) | English inflected forms |
| an adjective (e.g. `fast`) | comparison forms |
| a multi-sense word (e.g. `bank` or `run`) | sense separation and per-sense translations |
| a word with **several** German equivalents | multiple `translations` rows per sense |
| a word with a German grammatical/usage label | label capture (no inference) |
| a word/word-sense **with no** German translation | missing stays missing |
| a German equivalent that has extra de.wiktionary info (gender, plural, conjugation) | complementary enrichment, correctly attributed |
| a word **with** an English definition | supplementary definition populated |
| a word **without** an English definition | missing stays missing |

**Acceptance criteria** (all must hold for the pilot to pass):

- Every entry resolves via `GET /api/entries/{id}` and appears in
  `GET /api/search` with an explicit `queryType`, searched via the **English**
  headword.
- German translation equivalents are present where the source has them and
  **absent where it does not** (no fabrication, no empty-string placeholders).
- Multiple German equivalents per sense are preserved as separate rows.
- German inflections are modelled where the German source provides them; no
  feature is inferred.
- English definitions render on the entry page; absence is a clean omission.
- Per-record provenance is recorded: each sense/translation/form can be
  traced to a `data_source` + `external_id`.
- Sources are **not** merged purely on string similarity: sense distinctions
  and provenance are preserved.
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
2. **Verify / metadata** — check size/checksum (FreeDict ships `.sha512`;
   kaikki publishes sizes/checksums on its landing pages); record
   extraction/version dates; write `MANIFEST.json` per source.
3. **Parse** — per adapter: JSONL line reader filtered to
   `lang_code == "en"` (headwords/translations) and `lang_code == "de"`
   (German-side enrichment) for Wiktextract; TEI XML parser for FreeDict.
4. **Normalize** — Unicode **NFC**, whitespace, apostrophes; the existing
   German `normalize()`/`_clean` rules are **German-specific** and must not be
   blindly applied to English headwords (an English-appropriate normalization
   path is part of the implementing milestone).
5. **Map entities** — source model → our model (`lexeme`, `senses`,
   `translations`, `word_forms` + `morphological_features`,
   `lexical_relations`, `example_sentences`/`example_words`). Unmappable
   features go to `morphological_features.extra` rather than being dropped.
6. **Dedupe / cross-source match** — key on `(language, normalized_lemma,
   part_of_speech)`; resolve form collisions; the merge must **never lose**
   a source link, and must preserve sense distinctions.
7. **Preserve provenance** — attach `data_source_id` + `external_id` to
   every record and mark `is_primary` (translation source vs definition
   source). Provenance survives the merge.
8. **Validate / report** — schema validation (extend `scripts/normalized.py`
   for source identity and language), plus counters and a diffable error
   report.
9. **Idempotent DB import** — extend `scripts/dbload.py` / `DatabaseLoader`
   patterns: deterministic ids, upsert, dry-run mode, single transaction per
   batch.
10. **Stats / error report** — machine-readable summary (per source, per
    stage) written to `data/processed/` and printed.

New adapters live under `scripts/import/sources/` (one module per source)
implementing a common interface, so additional sources are additive. The
existing fixture path (`scripts/fixtures.py` → `scripts/dbload.py`) stays
untouched.

---

## 8. API / frontend compatibility findings

Current contract (`apps/api/app/schemas/entries.py`,
`packages/shared-types/index.d.ts`, entry page
`apps/web/app/pages/entries/[id].vue`):

- `EntryDetailResponse` has **no translations field** and **no provenance
  field**. `SenseDTO.definition` is a single string rendered as
  "Bedeutungen".
- The **frontend already supports** a bilingual-ish display: examples have an
  optional `translation`, and the entry page renders it. There is no
  dedicated German-translation block for a lexeme/sense.
- `search` results expose a single `definition: string | null`, and the
  search pipeline is **German-centric** (`MORPHOLOGY_ENGINE=auto` →
  `de_core_news_sm`, German `normalize()`); searching **English** headwords is
  a behavioural change that this milestone does **not** make. It must be
  planned with the implementing milestone (engine/locale selection, query
  normalization) and covered by tests.
- Adding translations/provenance is otherwise **additive** and
  backward-compatible.

Required contract changes (additive, in the implementing milestone):

1. Add `translations` to `EntryDetailResponse` and to the shared types.
2. Add an optional `provenance`/`source` object (dataset name + licence +
   attribution) at entry level and/or per sense/translation.
3. Surface a "Quellen / Sources" attribution area (entry-level or global).

Rendering rule for the new UI: **German translation equivalents are primary**,
the English definition is shown as the complementary explanation. Copy the
existing camelCase-on-the-wire convention and `populate_by_name=True`.

No existing field changes meaning, so current clients keep working; the
search-language change (§8) must be delivered separately with its own tests.

---

## 9. Risks, unknowns, decisions needing approval

| # | item | type | note |
|---|---|---|---|
| R1 | FreeDict **eng-deu licence** unverified (TEI header; API has no licence field) | unknown | may be GPL; blocks committing derived data |
| R2 | CC BY-SA **share-alike** vs GPL compatibility when merging | risk | possibly needs legal review |
| R3 | kaikki JSONL **per-file licence/manifest** unclear | unknown | confirm before import |
| R4 | **Search-language mismatch**: pipeline is German-only; headwords are now English | risk | requires engine/locale/normalization work + tests in a later milestone |
| R5 | **Frequency** source absent | gap | fixture corpus is synthetic; product frequency stays fake/deferred |
| R6 | Wiktextract schema is rich/free-form; mapping to our enums is lossy | risk | use `extra` JSON; document unmapped features |
| R7 | Sense→translation association is not always 1:1 in the source | risk | never fabricate; keep source sense granularity |
| R8 | Cross-source merge on string similarity could conflate distinct senses | risk | match on `(language, lemma, POS)` + sense, keep provenance |
| D1 | **New `translations` table** (option A vs B, §4.4) | decision | recommended: B |
| D2 | **Provenance shape** (join tables vs polymorphic) | decision | recommended: join tables |
| D3 | **Data licence** for the repo (separate from MIT code) | decision | required before committing any real data |
| D4 | Whether to add the **identity uniqueness constraint** | decision | recommended: yes |
| D5 | Whether to ship **any** derived data in-repo at all | decision | depends on R1/R2 |
| D6 | Attribution UX (entry-level vs global "Sources" page) | decision | affects API shape |
| D7 | How to represent English vs German forms in `word_forms` | decision | needs a language discriminator or per-lexeme convention |

None of these decisions are made by this document; they are inputs to the
next milestone.

---

## 10. Prioritized next-milestone plan

Ordered so each step unblocks trustworthy work on real data. **No code
changes are implied by this document.**

1. **Resolve licensing** (R1–R3): inspect the FreeDict eng-deu TEI header
   and the kaikki file manifest; get a decision on R2/D3. **Blocker.**
2. **Measure coverage** (see [`coverage-study.md`](coverage-study.md)): scan
   (not fully import) the en/de Wiktextract JSONL and FreeDict eng-deu for the
   documented sample; record hit rates and field-fidelity. **All measurements
   are currently pending.**
3. **Extend the schema** (D1–D4, D7): `translations` table, provenance
   (join tables), identity uniqueness constraint, form-language handling —
   delivered as an Alembic migration in that milestone.
4. **Extend the import contract & adapters**: source identity + language in
   `scripts/normalized.py`; `scripts/import/sources/` adapters for
   Wiktextract (en + de editions) and FreeDict.
5. **Run the pilot** (§6) with the acceptance criteria; produce the report.
6. **Expose it**: additive API fields (`translations`, `provenance`) +
   shared types + entry-page UI with German primary / English complementary
   + a "Quellen" attribution area.
7. **Search-language support** (R4): English query normalization and engine
   selection, with tests, so English headwords are searchable.
8. **Attribution & manifest**: enforced `MANIFEST.json`, dataset-level
   attribution file, README/in-app notices.

Each step should land as a small, reviewable unit with tests, following the
repository's existing workflow. Nothing in steps 1–8 should break the
current fixture-based demonstration, which remains the default data set
until a real import is explicitly approved.
