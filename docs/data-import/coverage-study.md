# English → German coverage & quality study: executable plan

A reproducible, small-scale evaluation of how well the candidate sources cover
the English → German product goal. This document is an **evaluation plan**:
it fixes the inputs, checksums, commands, sample rule, metrics and report
format so the experiment can be re-run and its results trusted.

> **Status: planned, not run.** No dataset has been downloaded and no coverage
> number has been measured. Per the milestone constraints, datasets are not
> downloaded without approval, and **no result is fabricated**. Every value is
> written `pending` until the experiment runs.

Companion documents: source facts in [`source-register.md`](source-register.md);
readiness decision in [`pilot-readiness.md`](pilot-readiness.md); product goal
and schema decisions in [`plan.md`](plan.md).

## 0. Scope

- **Question.** For a fixed, non-cherry-picked sample of English headwords, how
  completely and how faithfully can en.wiktionary (via Wiktextract), with de.wiktionary
  as complement, populate: English headword + POS, English definition, **German
  translation equivalents** (primary), sense→translation association, German
  inflection/gender/labels, examples, and provenance?
- **Out of scope.** Full import; schema/migration; API/UI behaviour; frequency
  (no source; see plan §9).
- **Guardrails.** Small sample (100–500 headwords); read-only analysis; raw
  artefacts never committed; missing data recorded as missing.

## 1. Inputs (exact artefacts)

| # | artefact | expected size | source date | download |
|---|---|---|---|---|
| I1 | `raw-wiktextract-data.jsonl.gz` (English edition) | 2.8 GB (uncompressed 23.9 GB) | extract 2026-10-03 from enwiktionary dump 2026-09-02 | `https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz` |
| I2 | `raw-wiktextract-data.jsonl.gz` (German edition) | 294.3 MB (uncompressed 2.9 GB) | extract 2026-10-02 from dewiktionary dump 2026-09-01 | `https://kaikki.org/dewiktionary/raw-wiktextract-data.jsonl.gz` |
| I3 | `freedict-eng-deu-1.9-fd1.src.tar.xz` | 16,742,600 B | dict version 1.9-fd1, dated 2022-04-15 | `https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/freedict-eng-deu-1.9-fd1.src.tar.xz` |

Generator provenance (record verbatim): Wiktextract commit `1a05e46`,
wikitextprocessor commit `e3d6d4e` (from the kaikki landing pages).

Place downloaded files under `data/raw/<source>/` (never committed; see
`data/raw/README.md`). Names must match the table above so the commands run
unchanged.

## 2. Checksums and integrity

**FreeDict publishes checksums** (`.sha512`). Expected SHA-512 for I3:

```
e44d3a3697d2bfe93cadef70284355bdd9d41cae818722d26e9eda8e4268ce63c37cee4d623c4be8028467fc212d49b388fdb395c0a253d285aed1bd424f80a9
```

**kaikki does not publish per-file checksums.** Therefore we compute our own
and record them (this is a reproducibility record, not an upstream guarantee).

Commands (run from the repo root after the artefacts are in `data/raw/`):

```
# I3: verify against the published checksum
sha512sum -c freedict-eng-deu-1.9-fd1.src.tar.xz.sha512

# I1, I2: no upstream checksum -> record our own + verify gzip integrity
gzip -t data/raw/en/raw-wiktextract-data.jsonl.gz
gzip -t data/raw/de/raw-wiktextract-data.jsonl.gz
sha256sum data/raw/en/raw-wiktextract-data.jsonl.gz > data/raw/SHA256SUMS.txt
sha256sum data/raw/de/raw-wiktextract-data.jsonl.gz >> data/raw/SHA256SUMS.txt
```

**Expected output:** `sha512sum -c` prints `...: OK`; `gzip -t` prints nothing
(success) and a non-zero exit on corruption; `SHA256SUMS.txt` gains two lines.
If any check fails, **stop** — do not measure.

We also record for each artefact: URL, byte size, the date it was fetched, and
the source/extraction dates from §1.

## 3. Sample selection (documented, reproducible, not cherry-picked)

Target: **120 core + up to ~60 stratified = 100–500 English headwords**. Two
parts, both deterministic and both stored to a file so the exact sample can be
re-derived and audited.

### 3.1 Core sample (generalises; ~120)

1. Stream I1 once and collect every record with `lang_code == "en"` and
   `pos ∈ {noun, verb, adj, adv}`.
2. Build the list of `(word, pos, etymology_number)` tuples (Wiktextract uses
   `etymology_number` to separate numbered etymologies; missing ⇒ treat as
   `"0"`). Sort lexicographically.
3. Let `N` be the list length and `k = max(1, N // 120)`. Starting at offset
   `seed mod k` with `seed = 20261008`, take every `k`-th tuple until 120 are
   collected.

This is an alphabetically-spread deterministic sample: it is **not** derived
from whether an entry has a German translation, so it measures coverage
honestly (including zero-translation entries).

### 3.2 Stratified sample (exercises hard cases; up to ~60)

For each class below, select the **first M entries in sorted order** that
satisfy the *source-side* predicate. The predicate is about the source
structure, never about whether our importer succeeds.

| class | source-side predicate | M |
|---|---|---|
| irregular English verbs | an `en` verb whose `forms` include a `past`/`participle` tag | 10 |
| polysemy | an `en` entry with `len(senses) >= 3` | 10 |
| multiple German equivalents | a sense with `>= 2` translations where `code == "de"` | 10 |
| grammatical/usage labels | a sense with non-empty `tags` | 10 |
| examples | a sense with `>= 1` example (`senses[].examples`) | 10 |
| zero German translations | an `en` entry whose record has **no** `code == "de"` translation | 10 |

### 3.3 Persisted sample file

Write the chosen keys to `data/processed/pilot-sample.json` **before** scoring:

```
{ "seed": 20261008, "core_size": 120, "stratified_per_class": 10,
  "entries": [ {"word": "...", "pos": "...", "etymology_number": "0",
                "class": "core|irregular_verb|polysemy|multi_de|labels|examples|no_de"} ] }
```

Committing this file (small, factual, no external text) makes the study
auditable. If a future run changes the sample, the file changes and the diff is
visible.

## 4. Scoring procedure (read-only; no import)

For each sampled key:

1. Locate the `en` record(s) in I1; record `word`, `pos`, `etymology_number`,
   `senses` (`glosses`, `raw_glosses`, `tags`), top-level and per-sense
   `translations`, `forms`, `sounds`, `etymology_text`, `source`, `wikidata`.
2. Extract **German equivalents** = translation objects with `code == "de"`
   (fields: `word`, `tags` (gender), `note`, `sense`, `english`, `roman`;
   `word` may be absent when `note` is present).
3. Locate the corresponding `de` records in I1/I2 for the German equivalents
   (by normalized lemma + `pos`) to measure German inflection/gender/definitions.
4. Read I3 (FreeDict TEI XML) for the English headword and record its
   German equivalents (headword-level; no senses).
5. Emit one JSON row per key and aggregate the metrics in §5.

### 4.1 Planned driver command (next milestone; not written yet)

A read-only script `scripts/import/pilot_coverage.py` will implement §3–§5.
Its interface is fixed now so the later implementation is verifiable:

```
python -m scripts.import.pilot_coverage \
  --en data/raw/en/raw-wiktextract-data.jsonl.gz \
  --de data/raw/de/raw-wiktextract-data.jsonl.gz \
  --freedict data/raw/freedict/eng-deu.tei \
  --sample data/processed/pilot-sample.json \
  --report data/processed/pilot-coverage.json
```

No such script exists in this milestone; the command is a contract, not a claim
that it has been run.

## 5. Metrics and expected report shape

Metrics (all per source; `pending` until run):

- Headword coverage; POS agreement.
- **German translation coverage**: % sampled entries with ≥ 1 `code == "de"`
  equivalent; distribution of the number of distinct equivalents.
- **Sense→translation association**: % of senses whose German equivalents are
  attached at sense level (`senses[].translations`) vs only headword level
  (top-level `translations`); count of unmatched/free-text `sense` values.
- **German inflection coverage**: % of German equivalents for which de data
  provides plural/conjugation/declension forms.
- **German label coverage**: % with a source-provided gender/usage label.
- **Example coverage**: % with ≥ 1 example; % of examples with an English
  translation field.
- **Definition coverage**: % with an English `glosses` definition; % with a
  German-language definition (from de data).
- **Field-fidelity**: count of source fields with no lossless target; list
  each unmapped field.
- **Defects**: missing records, duplicated equivalents, conflicting records
  across sources, and per-source retrieval counts.

Expected report shape (`data/processed/pilot-coverage.json`):

```
{ "sample": "data/processed/pilot-sample.json",
  "inputs": { "en": {"sha256": "...", "date": "2026-..."}, "de": {...}, "freedict": {"sha512": "..."} },
  "aggregate": { "<metric>": {"en": <number|"pending">, "de": ..., "freedict": ...} },
  "per_entry": [ { "word": "...", "pos": "...", "german_equivalents": [...], "flags": [...] } ],
  "errors": [ { "class": "...", "word": "...", "detail": "..." } ] }
```

## 6. Error reporting

Every anomaly is recorded, never silently dropped. Error classes:

| class | meaning |
|---|---|
| `missing_record` | sampled key absent from the source |
| `no_german_translation` | record exists but has no `code == "de"` translation |
| `sense_unmapped` | translations only at headword level, or `sense` text matching no gloss |
| `duplicate_translation` | the same German surface repeated for one sense |
| `conflicting_translation` | sources disagree on the German equivalent for a sense |
| `lossy_field` | a source field has no faithful target in the proposed model |
| `invalid_record` | record fails the candidate normalizer/validation |
| `word_field_absent` | a translation object has `note` but no `word` |

The report prints a per-class count and the first N examples, and the process
exits non-zero only on integrity failures (§2), not on data-quality findings.

## 7. Results (fill in when run)

| metric | en.wiktionary | de.wiktionary | FreeDict eng-deu |
|---|---|---|---|
| headword coverage | pending | n/a | pending |
| entries with ≥ 1 German equivalent | pending | n/a | pending |
| mean distinct German equivalents | pending | n/a | pending |
| sense→translation association coverage | pending | n/a | n/a |
| German inflection coverage | pending | pending | n/a |
| German grammatical-label coverage | pending | pending | n/a |
| example coverage (with translation) | pending | pending | n/a |
| English-definition coverage | pending | n/a | n/a |
| German-language-definition coverage | n/a | pending | n/a |
| fields mapped without lossy conversion | pending | pending | pending |
| missing/ambiguous/duplicated/conflicting records | pending | pending | pending |

## 8. Interpretation rules

- **Planned ≠ done.** Until §7 is filled from an actual run, nothing here is a
  measurement. This document must never be read as results.
- **Missing is not zero.** A blank cell means the source does not model that
  content, not that coverage is 0%.
- **Never infer.** If a source lacks a grammatical feature it is recorded as
  missing; it is not derived to improve a number.
- **Provenance stays attached**, so any merged figure can be decomposed per
  source.
- **Headline counts are not coverage.** FreeDict's 460,315 headwords are an
  entry count, not usable English→German sense pairs, and are not used to rank
  sources.
