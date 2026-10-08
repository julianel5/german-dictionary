# English → German pilot readiness

Validation and design deliverable for the English Wiktionary pilot.
**Status: design only.** No dataset was downloaded, no external data was
imported, no schema was changed, no migration was created, and no API/UI
behaviour was modified. This document resolves the technical questions that
could invalidate the data model or pilot, and records an explicit GO / NO-GO.

Direction: an **English → German** dictionary — English headword, **German
translation equivalents primary**, English definitions supplementary, German
inflections/definitions complementary. Spanish is optional/secondary.
Companion documents: [`plan.md`](plan.md),
[`source-register.md`](source-register.md), [`coverage-study.md`](coverage-study.md).

## 1. Verified facts and unresolved questions

### 1.1 English Wiktionary via Wiktextract — verified (page)

| field | value | status |
|---|---|---|
| landing page | `https://kaikki.org/dictionary/rawdata.html` | verified (page) |
| raw artefact | `raw-wiktextract-data.jsonl` 23.9 GB / `.jsonl.gz` 2.8 GB | verified (page) |
| error artefact | `wiktextract-error-data.json` 859.4 MB / `.gz` 39.1 MB | verified (page) |
| source dump | enwiktionary dump **2026-09-02** | verified (page) |
| extraction date | **2026-10-03** | verified (page) |
| generator | wiktextract `1a05e46` + wikitextprocessor `e3d6d4e` | verified (page) |
| per-file manifest | **none found** on the landing page | verified (absence) |
| licence/attribution | cite Ylonen (*Wiktextract*, LREC 2022) + link kaikki.org | verified (page) |
| underlying text licence | en.wiktionary is **CC BY-SA 4.0** | verified (page, wiki footer) |
| licence of the downloadable JSONL | not stated on the download page | **unverified** |
| software licence | MIT (repo `LICENSE`); tests subset CC-BY-SA/GFDL | verified (file) |

Nothing on the raw-data page grants or names a licence for the **data**; it only
asks for citation. The MIT `LICENSE` governs the *tool*, not the extracted text.

### 1.2 Wiktextract schema — verified (README + field index)

Word object keys relevant to the product (all confirmed): `word`, `pos`,
`lang`, `lang_code`, `senses`, `forms`, `sounds`, `translations`,
`etymology_number`, `etymology_text`, `source`, `wikidata`, `wikipedia`, and
linkage arrays (`synonyms`, `antonyms`, `hypernyms`, `derived`, `related`, …).

- **Senses** (`senses[]`): `glosses`, `raw_glosses`, `tags`, `translations`
  (sense-disambiguated), `examples`, `senseid`, `wikidata`, `form_of`,
  `alt_of`.
- **Translations** (top-level and/or per sense): `word` (may be **absent when
  `note` is present**), `lang`, `code`, `alt`, `english`, `note`, `roman`,
  `sense` (**free text; may not match any gloss**), `tags` (e.g. gender),
  `raw_tags`, `topics`, `taxonomic`.
- **Forms** (`forms[]`): `form`, `tags` (e.g. `past`, `participle`, `plural`,
  `comparative`, `superlative`), `ipa`, `roman`, `source`; `form` may be `"-"`
  meaning the word explicitly lacks that form.
- **Etymology**: `etymology_number` is present for words with **multiple
  numbered etymologies** — the source's own homonym/etymology discriminator.

Capture config: `capture_language_codes` defaults to `["en","mul"]`; the kaikki
raw dumps are produced with all languages, so **filtering by `lang_code` is
mandatory**. English edition entries for German words exist too
(`lang_code == "de"`) but carry **English** glosses; German-language definitions
come only from the de edition.

### 1.3 German Wiktionary via Wiktextract — verified (page)

`https://kaikki.org/dewiktionary/rawdata.html`; extracted 2026-10-02 from
dewiktionary dump 2026-09-01; 2.9 GB / 294.3 MB gz. Supplies German-language
definitions, gender, declension/conjugation, examples. Licence CC BY-SA 4.0
(page-verified at the wiki footer; **not** verified for the file).

### 1.4 FreeDict English–German — verified (page) / unverified (licence)

Version **1.9-fd1**, dated 2022-04-15, status `stable`, **460,315 headwords**,
maintainer Einhard Leichtfuß, source `https://dict.tu-chemnitz.de/`. Artefacts
under `https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/`:
`.src.tar.xz` 16,742,600 B, `.dictd.tar.xz` 19,145,688 B, `.stardict.tar.xz`
26,877,184 B, `.slob` 39,437,035 B (each with a published SHA-512). The
metadata API `https://freedict.org/freedict-database.json` has **no licence
field** (verified). Translations only: no senses, no inflection, no frequency.

### 1.5 FreeDict licence-verification procedure (exact)

FreeDict states each dictionary's terms live in its **TEI header**, and that the
majority are GPL. Verification, when approved:

1. Download `freedict-eng-deu-1.9-fd1.src.tar.xz` (16.7 MB) and verify its
   SHA-512 against the published `.sha512`.
2. Extract; open the `.tei` file (UTF-8 XML).
3. Read the header: `<teiHeader> → <fileDesc> → <publicationStmt> →
   <availability>` and any `<licence>` element (and `<sourceDesc>` for the
   upstream source/attribution).
4. Record the **verbatim** licence identifier, attribution string, and any
   redistribution constraint; also check the upstream `dict.tu-chemnitz.de`
   terms because the FreeDict entry is imported.
5. Only then may the eng-deu licence be marked `verified (dataset)`.

This was **not** done in this milestone (constraint: no dataset downloads), so
the eng-deu licence remains **unverified**.

### 1.6 Verified vs assumed (summary)

| statement | status |
|---|---|
| kaikki en/de artefact sizes, dates, generator commits | verified (page) |
| kaikki translation/sense/form field names and semantics | verified (README) |
| `etymology_number` discriminates numbered etymologies | verified (README) |
| kaikki raw page publishes no per-file licence/manifest | verified (absence) |
| en/de Wiktionary text licensed CC BY-SA 4.0 | verified (page); **not** for the JSONL files |
| Wiktextract **software** licence is MIT | verified (LICENSE file) |
| FreeDict eng-deu version/size/headwords/artefacts | verified (page/API) |
| FreeDict eng-deu **data licence** | **unverified** |
| FreeDict metadata API exposes no licence | verified (API payload) |

### 1.7 Unresolved questions

1. Does the kaikki JSONL ship (or link) a licence/attribution manifest and
   inherit only CC BY-SA 4.0, or add terms?
2. What is the exact FreeDict eng-deu licence (GPL or other) and upstream
   Chemnitz terms?
3. Share-alike reach: can CC BY-SA Wiktionary text be combined in one derived
   database with GPL FreeDict data under our MIT code? (Legal review.)
4. Are en/de translation `sense` strings reliably matchable to `glosses`, or
   must many remain headword-level? (To measure — see `coverage-study.md`.)
5. Which attribution strings must be surfaced, and where?
6. Does `mul`/Translingual content need filtering for an English→German product?

## 2. Proposed sample and reproducible evaluation procedure

Fully specified in [`coverage-study.md`](coverage-study.md). In brief:

- **Inputs:** en rawdata `.jsonl.gz`, de rawdata `.jsonl.gz`, FreeDict eng-deu
  `.src.tar.xz`; sizes/dates/URLs fixed; FreeDict verified by published
  SHA-512, kaikki checksums computed and recorded (none published).
- **Sample:** 120 core English headwords chosen by a deterministic
  alphabetically-spread stride (seed `20261008`) over `lang_code == "en"` with
  POS ∈ {noun, verb, adj, adv}, plus up to 60 stratified entries (irregular
  verbs, polysemy ≥ 3 senses, ≥ 2 German equivalents, tagged senses, examples,
  zero-German-translation). The chosen keys are persisted to
  `data/processed/pilot-sample.json` before scoring, so the sample is auditable
  and the selection is **not** based on whether an entry works.
- **Scoring:** read-only; per-entry metrics and an error-classed report
  (`data/processed/pilot-coverage.json`). Planned driver:
  `python -m scripts.import.pilot_coverage ...` (script **not yet written**).
- **Guardrail:** all results stay `pending` until actually run; no fabricated
  numbers; missing data recorded as missing.

## 3. Identity and deduplication recommendations

### 3.1 Current behaviour (audited)

- `scripts/dbload.py` derives the lexeme id as
  `id_for("lexeme", language, lemma, part_of_speech)` — so any two records that
  share `(language, lemma, part_of_speech)` map to the **same** row.
- `NormalizedDictionary` rejects a duplicate `(lemma, part_of_speech)` pair
  (it does not include language, so it is stricter than the id key in one
  dimension and looser in another).
- `_resolve_lexeme_id` matches on `(language, lemma)` ignoring POS;
  `_find_lexeme_id` (frequency) matches on normalized lemma alone, ignoring
  language and POS.

### 3.2 The risk

`(language, normalized_lemma, part_of_speech)` **silently collapses distinct
lexical entries**. English is rich in homonyms with distinct etymologies —
e.g. `bank` (river) vs `bank` (finance), `bass`, `bow`, `lead`, `bear` —
which Wiktionary shows as separate entries, disambiguated by
`etymology_number`. Keying on the 3-tuple (or, worse, lemma alone) merges them
and would produce a wrong German translation set. Cross-language spelling
collisions (English `gift` vs German `Gift`) are a second, related hazard
because search is not language-scoped (§5).

### 3.3 Options and trade-offs

| option | identity key | preserves distinct etymologies? | cross-source | cost |
|---|---|---|---|---|
| A. extend with etymology number | `(language, normalized_lemma, pos, etymology_number)` | **yes**, when the source numbers them | numbering is source-local; may not align | add a column; medium |
| B. source-scoped identity | deterministic id from `(data_source_id, external_id)` (+ fallback tuple); separate non-unique **match key** | yes (each source record survives) | explicit merge step, no silent collapse | needs provenance first; medium/large |
| C. etymology entity | `etymology` rows; lexemes FK to etymology | yes, explicitly modelled | clean but a bigger schema change | large |
| D. keep 3-tuple as unique | `(language, normalized_lemma, pos)` unique | **no — loses homonyms** | n/a | cheapest, incorrect |

### 3.4 Recommendation

- **Do not add a uniqueness constraint on `(language, normalized_lemma,
  part_of_speech)`.** It would silently collapse homonyms.
- Add `etymology_number` (nullable, default `"0"`) to `lexemes`, carried from
  the source, and use `(language, normalized_lemma, part_of_speech,
  etymology_number)` as a **non-unique matching index** — not a global unique
  constraint.
- Make identity **source-scoped**: derive deterministic ids from
  `(data_source_id, external_id)` when the source provides an id, else from
  `(data_source_id, language, normalized_lemma, pos, etymology_number)`. This
  keeps re-imports **idempotent per source** without collapsing across sources.
- Cross-source merging is an **explicit, auditable step** that links records
  (provenance join tables, §4) and must **never** destroy a source link. Where a
  source lacks etymology numbers (FreeDict) it is a *translation contributor*,
  not a competing lexeme: attach to the matched English lexeme at lexeme level
  (unassigned sense) rather than minting a new identity.
- Multiple senses are already preserved by `senses.sense_index`; keep them
  distinct and never merge two senses because their text looks similar.

## 4. Translation and language-aware form modelling recommendations

### 4.1 Translation equivalents

Smallest robust model: **one new `translations` table**, provider-agnostic.

`translations(id, lexeme_id → lexemes, sense_id → senses NULL,
language, text, gender NULL, tags JSON, note NULL, source_sense NULL,
source_english NULL, roman NULL, target_lexeme_id → lexemes NULL)`

- **Multiple German equivalents** → many rows for one `(lexeme_id, sense_id)`.
- **Sense association** → `sense_id` set when the source attaches translations
  to a sense (`senses[].translations`).
- **Unassignable translations** → `sense_id = NULL`, with the source's free-text
  `sense` preserved in `source_sense` and `english` in `source_english`. These
  are shown as "not tied to one sense" — never force-fitted onto a sense.
- **Labels** → `gender` first-class; remaining qualifiers (`tags`, `raw_tags`,
  region, register) preserved verbatim in `tags` JSON; `note` kept as text.
- **Provider neutrality** → the table stores `language` (target) and optional
  `target_lexeme_id`; it never encodes a Wiktextract- or FreeDict-specific
  column.

### 4.2 English forms vs German forms

- Forms stay owned by a lexeme (`word_forms.lexeme_id`), and **language is
  implied by the owning lexeme's `language`** — no per-form language column is
  needed. English inflections are the `word_forms` of the `en` lexeme; German
  inflections are the `word_forms` of a `de` lexeme.
- German equivalents are enriched **only when a German lexeme is imported**
  (from en `de` sections and/or de.wiktionary) and linked via
  `translations.target_lexeme_id`. FreeDict-only equivalents have translation
  rows but no forms — that is correct, not a defect.
- Wiktextract form `form == "-"` (explicitly no such form) is **dropped**, not
  stored as a surface.
- Map Wiktextract form `tags` to the existing `FormType` enum where faithful;
  anything unmapped goes to `morphological_features.extra` (never dropped).

### 4.3 Provenance (survives merges)

- `data_sources(id, source_id, name, url, licence, licence_url,
  attribution_text, retrieved_at, source_version, checksum, processed_at,
  notes)`.
- Join tables `lexeme_sources`, `sense_sources`, `word_form_sources`,
  `translation_sources`: `(record_id, data_source_id, external_id, confidence,
  is_primary)` with a unique `(record_id, data_source_id, external_id)`.
- Every imported record is attributable; merging keeps **all** links and marks
  `is_primary` for display.

### 4.4 Sense tags (minimal addition)

Wiktextract sense `tags` (usage/grammar labels) have no home today. Add an
optional `tags JSON` column to `senses` (mirroring `MorphologicalFeatures.extra`)
rather than a new table.

### 4.5 Not recommended

- A translated-gloss column on `senses` (mixes English definition and German
  equivalent; no room for multiple equivalents or provenance).
- A `language` column on `word_forms` (redundant; derive from the lexeme).
- Any column named after a provider (e.g. `wiktextract_sense`).

## 5. English search requirements — acceptance criteria

### 5.1 Findings in the current implementation

- `NormalizeStage` uses `german_morphology.normalize()` = NFC + whitespace
  collapse + `str.lower()`. It is case-insensitive and Unicode-normalising but
  uses `lower()` (not `casefold()`) and is German-oriented.
- **No stage filters by language**: `LexemeRepository.by_normalized_lemma`,
  `LookupRepository.surface_candidates`/`form_for_lexeme`, and
  `DatabaseLoader._find_lexeme_id` all ignore `lexeme.language`. With English
  and German lexemes co-resident, queries would mix languages.
- `MorphologyStage` runs the **German** engine on every query
  (`de_core_news_sm`), so an English query could yield spurious German lemmas.
- The response cache key (`search.service.cache_key`) includes the query, limit
  and engine token but **not** a language scope or normalization version.

### 5.2 Acceptance criteria (to implement in a later milestone)

- **AC-S1 Headword lookup.** Searching an exact English headword returns the
  English lexeme through `GET /api/search`, with an explicit `queryType`, and
  `GET /api/entries/{id}` resolves it.
- **AC-S2 Case-insensitive, Unicode-safe.** `house`, `House`, `HOUSE` all
  resolve; NFC-composed and decomposed inputs compare equal; the displayed form
  is the source's, not the normalized form. Normalization must be
  language-appropriate (English path uses NFC + whitespace + `casefold`;
  German path unchanged) and versioned.
- **AC-S3 Exact before fallback.** Priority order
  `lemma > form > normalized > morphology > definition > fuzzy` is preserved;
  an exact surface hit is never beaten by fuzzy/definition.
- **AC-S4 English inflected forms.** `houses`, `went`, `singing` resolve to
  their lemma when the source supplied the form (matchType `form`/`normalized`);
  when the source did not, the query yields no fabricated candidate.
- **AC-S5 No German morphology on English queries.** The German engine must not
  produce candidates for an English-scope query; a valid English word that
  German analysis would mis-lemmatise must not surface a German lemma.
- **AC-S6 Language-scoped results.** Results for the English→German product
  include only the configured headword language(s) (e.g. `en`); German lexemes
  used for enrichment are not returned as headword hits.
- **AC-S7 Fixture demo preserved.** With the German fixture dataset loaded, the
  current behaviour and all existing tests are unchanged (default scope keeps
  today's semantics); the new language dimension defaults compatibly.
- **AC-S8 Cache correctness.** The cache key includes the language scope and a
  normalization version; bump `_CACHE_VERSION`; `Haus` vs `haus` still never
  share an entry (case remains part of the contract).
- **AC-S9 Contract stability.** `SearchResultItem`/`EntryDetailResponse` remain
  backward compatible; any translation/provenance fields are additive.

**Not implemented in this milestone** — no search code, config or schema is
changed here.

## 6. Licence blockers

| id | blocker | status | impact |
|---|---|---|---|
| L1 | kaikki en/de JSONL per-file licence/manifest unfound; only CC BY-SA 4.0 at the wiki, MIT for the tool | **open** | cannot assert the *file's* licence; blocks committing derived data |
| L2 | FreeDict eng-deu TEI-header licence unverified (procedure §1.5) | **open** | eng-deu stays optional until verified |
| L3 | CC BY-SA 4.0 share-alike vs GPL FreeDict in one merged database | **open** | may force separation or legal review |
| L4 | Required attribution strings and their surfacing (README/in-app) | **open** | must exist before shipping any derived data |
| L5 | en.wiktionary historical GFDL dual-licensing | **noted** | does not change CC BY-SA 4.0 reuse, but must be documented |

None of these block a **local, read-only** coverage experiment; all of them
block **committing or shipping** derived data.

## 7. GO / NO-GO recommendation

**GO — conditional — for the small, read-only coverage pilot.**
The next step is a *local evaluation*, not an import: it reads the artefacts,
measures coverage/quality, and writes a report. It requires no schema change, no
API change, and commits no external text. Conditions:

1. **Explicit approval to download** the three artefacts (I1–I3) into
   `data/raw/` (nothing is committed; `data/raw/README.md` rules apply).
2. Verify integrity first (§2 of the coverage plan); stop on failure.
3. Keep the persisted sample and computed checksums auditable; keep every result
   **pending** until actually measured.

**NO-GO — for committing derived data, changing the schema, or implementing the
import** until licence blockers **L1–L3** are resolved and L4 is specified.
Specifically, do **not** create the `translations`/provenance migration or wire
new API fields until the licence position is settled.

Rationale: the design questions that could invalidate the model are now
resolved (identity must not collapse etymologies; translations need a
provider-neutral table; forms inherit language from the lexeme; search must be
language-scoped and must not run German morphology on English). The remaining
unknowns are empirical (coverage) and legal (licence), both of which the
read-only pilot and a licence check address **without** touching the schema or
shipping data.

**Stop here.** No import, schema migration, or search change is made in this
milestone.
