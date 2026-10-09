# English → German coverage & quality study: executed report

Reproducible, small-scale evaluation of how well the candidate sources cover the
English → German product goal.

> **Status: RUN (read-only pilot executed 2026-10-08).** The three artefacts were
> downloaded outside the versioned tree, integrity was verified, and the metrics
> below are **measured** (not estimated). No data was imported, no schema or
> migration was changed, no API/UI behaviour was touched. Every number carries
> its numerator and denominator, and structural limits are stated. Values that
> cannot be measured are marked `N/A`, never guessed.

Executed by `scripts/import.pilot_coverage` (procedure `pilot-coverage/1.0`).
Companion documents: source facts in [`source-register.md`](source-register.md);
readiness and licence findings in [`pilot-readiness.md`](pilot-readiness.md);
product goal and schema decisions in [`plan.md`](plan.md).

## 0. Scope

- **Question.** For a fixed, non-cherry-picked sample of English headwords, how
  completely and how faithfully can en.wiktionary (via Wiktextract), with
  de.wiktionary as complement, populate: English headword + POS, English
  definition, **German translation equivalents** (primary), sense→translation
  association, German inflection/gender/labels, examples, and provenance?
- **Out of scope.** Full import; schema/migration; API/UI behaviour; frequency
  (no source; see plan §9).
- **Guardrails.** Read-only analysis; raw artefacts never committed; missing data
  recorded as missing.

## 1. Inputs (exact artefacts, as downloaded)

| # | artefact | bytes (expected = actual) | sha256 (computed locally) | source date |
|---|---|---|---|---|
| I1 | en `raw-wiktextract-data.jsonl.gz` | 2,981,058,381 | `3dac8a09e57827bef493e2e6b552fe917bf3b1fc55dee05c4e4a3702aff5dbdb` | extracted 2026-10-03 from enwiktionary dump 2026-09-02 |
| I2 | de `raw-wiktextract-data.jsonl.gz` | 308,579,949 | `ccd0fb5ee317426e7396f4dfba2ab210376e4779fd7609ebf09b605a140421fc` | extracted 2026-10-02 from dewiktionary dump 2026-09-01 |
| I3 | FreeDict `freedict-eng-deu-1.9-fd1.src.tar.xz` | 16,742,600 | `83a02d8eace3fbb460fa96c32c2d964a9bc1e1a63ea754021ac33042ee2d1d5f` | dict version 1.9-fd1, dated 2022-04-15 |

URLs: I1 `https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz`; I2
`https://kaikki.org/dewiktionary/raw-wiktextract-data.jsonl.gz`; I3
`https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/freedict-eng-deu-1.9-fd1.src.tar.xz`.

Generator provenance (verbatim from the kaikki pages): Wiktextract commit
`1a05e46`, wikitextprocessor commit `e3d6d4e`.

**Where the files were placed.** Because `.gitignore` does *not* exclude
`data/raw/` large files, the datasets were downloaded to an **external working
directory outside the versioned tree** (a local temp directory). Nothing under it
is committed. The FreeDict source was extracted only after inspecting its member
list (`tar -tJf`) and verifying the published SHA-512.

## 2. Checksums and integrity (results)

| check | command | result |
|---|---|---|
| I1 gzip integrity | `gzip -t en/raw-wiktextract-data.jsonl.gz` | **OK** |
| I2 gzip integrity | `gzip -t de/raw-wiktextract-data.jsonl.gz` | **OK** |
| I3 published checksum | `sha512sum -c freedict-eng-deu-1.9-fd1.src.tar.xz.sha512` | **OK** (matches the documented `e44d3a36…f80a9`) |
| I3 xz integrity | `xz -t freedict-eng-deu-1.9-fd1.src.tar.xz` | **OK** |
| I1 sha256 | `sha256sum` | `3dac8a09…` (our fingerprint; kaikki publishes none) |
| I2 sha256 | `sha256sum` | `ccd0fb5e…` (our fingerprint) |

The FreeDict `.sha512` is provider-published and matched. The kaikki sha256
values are **our own reproducibility fingerprints**, not proof of authenticity
(kaikki publishes no per-file checksum).

## 3. Sample selection (executed)

Implemented in `scripts/import.pilot_coverage` exactly per the documented rule
(seed `20261008`, POS ∈ {noun, verb, adj, adv}, grammar categories from §3 of the
plan). Record counts actually observed:

| quantity | value |
|---|---|
| en records streamed (whole file) | **10,913,997** (0 parse errors) |
| de records streamed (whole file) | **1,329,116** (0 parse errors) |
| en core population (`lang_code == "en"`, POS ∈ scope) | **1,266,442** |
| core stride `k = max(1, N // 120)` | **10,553** |
| core offset `seed mod k` | **9,801** |
| core entries selected | **120** |
| stratified population: irregular_verb / polysemy / multi_de / labels / examples / no_de | 58,839 / 51,807 / **0** / 1,093,953 / 290,140 / 1,417,722 |
| stratified entries selected (10 per class) | 10 / 10 / **0** / 10 / 10 / 10 = **50** |
| total sampled keys | **170** (159 unique; core/stratified overlap) |

Persisted sample keys: `data/processed/pilot-sample.json` (gitignored; not
committed). Every sampled key was located during scoring: **0 missing records,
0 parse errors**.

### 3.1 Protocol ambiguity recorded (not silently changed)

The plan defines the `multi_de` hard-case as *“a sense with ≥2 translations where
`code == "de"`”* (sense-level). The raw Wiktextract data stores **all**
translations at the **record (headword) level**; **no** record in the whole en
file has `senses[].translations`. Under the literal sense-level definition the
population is therefore **0** — the class is empty, and this report does not
fabricate entries for it. The same property, measured at headword level, is
reported instead (§5, metric *entries with ≥2 German equivalents*; core: 2/120).
No protocol was changed; the literal definition was kept and its emptiness is
disclosed.

## 4. Scoring procedure (implemented, read-only)

The driver now exists and was run. Exact command (paths point at the external
working directory; run from the repo root):

```
python -m scripts.import.pilot_coverage \
  --en       <external>/en/raw-wiktextract-data.jsonl.gz \
  --de       <external>/de/raw-wiktextract-data.jsonl.gz \
  --freedict <external>/freedict/extracted/eng-deu/eng-deu.tei \
  --sample   data/processed/pilot-sample.json \
  --report   data/processed/pilot-coverage.json
```

The script streams each JSONL once to build the sample, then once more (plus one
live pass over the de edition) to score, and streams the FreeDict TEI
(`xml.etree.ElementTree.iterparse`) for the headwords in the sample. It filters
strictly by `lang_code` (`"en"` for headwords, `"de"` for enrichment), never by
the artefact's edition, and writes `data/processed/pilot-coverage.json`.

## 5. Metrics (measured)

### 5.1 Core sample (120 entries; generalises over raw en entries)

| metric | sample/source | numerator | denominator | pct | status | limitations |
|---|---|---|---|---|---|---|
| entries scored | en | 120 | 120 | 100% | MEASURED | all sampled keys located |
| **German translation coverage** | en | 7 | 120 | **5.83%** | MEASURED | uniform over *all* raw en entries incl. rare/form-of words; **not usage-weighted** |
| entries with ≥2 German equivalents | en | 2 | 120 | 1.67% | MEASURED | distinct casefolded surfaces, headword level |
| definition coverage | en | 120 | 120 | 100% | MEASURED | ≥1 non-empty `glosses` |
| sense→translation association (any language) | en | 0 | 129 | 0% | MEASURED | **structural**: raw data has no sense-level translations |
| sense→German association | en | 0 | 129 | 0% | MEASURED | same structural cause |
| gender label on en German equivalents | en | 3 | 11 | 27.27% | MEASURED | gender tag in the translation object |
| German enrichment: gender | de | 2 | 6 | 33.33% | MEASURED | matched de-edition records with a top-level gender tag |
| English inflection coverage | en | 41 | 120 | 34.17% | MEASURED | ≥1 form differing from the headword |
| German enrichment: forms | de | 6 | 6 | 100% | MEASURED | matched de-edition records carrying ≥1 form |
| example coverage | en | 23 | 120 | 19.17% | MEASURED | ≥1 sense example |
| example translation coverage | en | 0 | 57 | 0% | MEASURED | no `translation` field exists on example objects |
| sense tag coverage | en | 109 | 129 | 84.5% | MEASURED | senses with non-empty tags |
| German equivalent matched in de edition | de | 6 | 10 | 60% | MEASURED | exact casefold lemma match |

### 5.2 By part of speech (core)

| POS | entries | German coverage | definition coverage |
|---|---|---|---|
| noun | 85 | 3 (3.53%) | 85 (100%) |
| verb | 17 | 1 (5.88%) | 17 (100%) |
| adj | 16 | 3 (18.75%) | 16 (100%) |
| adv | 2 | 0 (0%) | 2 (100%) |

Descriptive only: the noun/adv cells are dominated by rare words; the numbers
must not be read as a per-POS quality ranking.

### 5.3 Stratified hard cases (separate from core — never pooled)

| class | entries | German coverage | note |
|---|---|---|---|
| irregular verb | 10 | 0 (0%) | first 10 sorted entries satisfying the source predicate |
| polysemy (≥3 senses) | 10 | 4 (40%) | includes suffixes like `-able`, `-age`; raw dump is not lemma-clean |
| multiple German equivalents | 0 | N/A | sense-level predicate unfillable in this data (§3.1) |
| grammatical/usage labels | 10 | 0 (0%) | |
| examples | 10 | 0 (0%) | includes symbols/phrases like `!`, `$$$`, `$2 shop` |
| zero German translations | 10 | 0 (0%) | by construction (`no_de`) |

## 6. Defects and field-fidelity

Error classes observed (never silently dropped; counts over all 159 captured
entries):

| class | count | meaning |
|---|---|---|
| `no_german_translation` | 148 | record exists but carries no `code == "de"` translation |
| `sense_unmapped` | 11 | German equivalents present, but only at headword level (all German in this data) |
| `sense_text_unmatched` | 19 | translation `sense` free text matching no gloss (e.g. `dictator` → “authoritarian leader of a dictatorship”) |
| `word_field_absent` | 2 | translation object has `note` but no `word` |
| `duplicate_translation` | 1 | same German surface repeated for one level |
| `missing_record` | 0 | all sampled keys located |

Field-fidelity (fields with no faithful target in the proposed model, counted in
the sample): `senses` → `senseid`, `wikidata`, `form_of`, `alt_of` (**96**
occurrences); record → `sounds` (**25**); `forms` → `ipa`, `roman`, `source`
(**0** in the sample). These are recorded, not dropped.

## 7. FreeDict eng-deu vs Wiktextract (diagnostic only)

| metric | numerator | denominator | pct | note |
|---|---|---|---|---|
| FreeDict entries scanned | 460,315 | 460,315 | 100% | entry count, **not** English→German pair count |
| core headwords present in FreeDict | 11 | 120 | 9.17% | exact headword match |
| FreeDict German equivalents for matched headwords | 23 | — | — | |
| FreeDict equivalents carrying `gen` | 5 | 23 | 21.74% | |
| exact set agreement with Wiktextract | 0 | — | — | of the 11 matched |
| partial agreement with Wiktextract | 3 | — | — | |
| FreeDict-only German (Wiktextract had none) | 8 | — | — | additive for those headwords |

Interpretation: for the rare words that dominate the uniform core sample,
FreeDict rarely has an entry, and where it does, it often adds German equivalents
the raw Wiktextract record lacks. **No cross-source entries are treated as
equivalent**; this is a diagnostic overlap, not a merge.

## 8. Key structural findings

1. **Translations are headword-level, not sense-linked** in the kaikki raw
   Wiktextract data (0/129 senses carry `translations`). Consequence for the
   proposed model: `translations.sense_id` will almost always be `NULL` for this
   source; the free-text `sense` field must be preserved as `source_sense`.
2. **A uniform sample of raw en entries is dominated by rare/technical/nonce and
   form-of entries** (`anthracobunid`, `deparochialize`, `strikebroken`,
   `grandfathers`, plus symbols/suffixes). German coverage over this population
   is 5.83%, but polysemous suffix entries reached 40%. Coverage figures must be
   presented as *raw-entry* coverage, with common-word coverage measured
   separately (a curated lemma list or frequency-weighted subset) in a later
   step. This is the single most important caveat for planning.
3. **No example translations** exist in the raw extract (`examples[].translation`
   absent); example translations cannot be sourced from here.
4. **German enrichment works**: the de edition supplies German-language
   definitions, gender and inflected forms; matched German equivalents all had
   forms (6/6) and 2/6 carried a top-level gender tag.
5. **FreeDict is complementary for common headwords**, not a primary source, and
   its licence is copyleft (see `pilot-readiness.md` §6).

## 9. Execution record

- **Date (UTC):** 2026-10-08, report generated 2026-10-08T23:08:01Z.
- **Artefacts examined:** I1, I2 (streamed in full), I3 TEI (streamed).
- **Records processed:** en 10,913,997; de 1,329,116; FreeDict 460,315 entries.
- **Records selected:** 170 sample keys (159 unique); 159 captured; 0 missing.
- **Parse errors:** 0 (en), 0 (de).
- **Sample limitations:** deterministic alphabetical stride over the raw en entry
  set → uniform over the lexicon, therefore dominated by rare entries; core and
  stratified results are reported separately and never pooled into a single
  coverage estimate; the stratified class `multi_de` is empty (protocol §3.1).
- **Outputs:** `data/processed/pilot-sample.json`, `data/processed/pilot-coverage.json`
  (both gitignored; not committed).
- **Licence evidence:** kaikki en/de pages expose no per-file data licence
  (citation request only) → JSONL **UNVERIFIED**; FreeDict eng-deu TEI header
  states **GPLv3 + AGPLv3** dual licensing → **VERIFIED (dataset)**.
- **Decisions requiring humans:** (a) whether the product should measure coverage
  over a curated/frequency-weighted lemma set instead of raw entries; (b) how the
  null `sense_id` policy is surfaced in the UI; (c) L1 (kaikki file licence) and
  L3 (share-alike vs GPL/AGPL compatibility) legal review.

## 10. Interpretation rules

- **Measured ≠ general.** These figures describe the sampled raw-entry
  population; the rare-word bias is explicit and must travel with every quote.
- **Missing is not zero.** A blank/0% cell can mean the source does not model the
  content (e.g. example translations), not that quality is poor.
- **Never infer.** Absent grammatical features/translations are recorded absent.
  Translations are **not** associated to senses unless the source says so; no
  text-similarity matching is used.
- **Provenance stays attached**, so any figure can be decomposed per source.
- **Headline counts are not coverage.** FreeDict's 460,315 entries are a count of
  entries, not usable English→German pairs, and are not used to rank sources.

## 11. Recommendation

- **Pilot: CONDITIONAL GO (completed).** The read-only experiment ran without
  touching the product; the design questions it could answer are answered.
- **Production import / schema / search changes: NO-GO** until licence blockers
  **L1** (kaikki file licence) and **L3** (CC BY-SA vs GPLv3/AGPLv3 compatibility)
  are resolved, and until coverage is re-measured on a curated lemma set
  (finding 2). See `pilot-readiness.md` §6–§7.
