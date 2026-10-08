# English → German coverage & quality study: method

A reproducible, small-scale evaluation of how well the candidate sources cover
the English → German product goal. This document defines the **method only**.

> **Status: measurements pending.** No dataset was downloaded and no coverage
> number below has been measured. Per the milestone constraints, full
> datasets are not downloaded without approval, and **no result is
> fabricated**. Where a value is unknown it is written `pending`.

Sources and their facts: [`source-register.md`](source-register.md).
Product goal and schema decisions: [`plan.md`](plan.md).

## 1. What is measured

For a fixed sample of English headwords, and for the German equivalents found
for them:

- **Headword coverage** — share of sampled English entries the source
  represents at all, and with the expected POS.
- **Translation coverage** — share of sampled English entries that have
  **≥ 1 German equivalent**; and the number of **distinct German
  equivalents** per entry.
- **Sense→translation association coverage** — share of English senses whose
  German equivalents are attached to the *correct* sense (vs only
  headword-level).
- **German inflection coverage** — share of German equivalents for which the
  German source provides declension/conjugation/plural forms.
- **German grammatical labels** — share of German equivalents with a
  source-provided gender/grammatical/usage label (never inferred).
- **Example coverage** — share of entries with ≥ 1 example, and with an
  example translation.
- **Definition coverage** — share of entries with an English definition
  (supplementary) and, separately, a German-language definition.
- **Field-fidelity** — share of source fields that map to our model
  **without lossy conversion**; anything unmappable is counted and listed.
- **Defects** — counts of missing records, ambiguous/duplicated
  translations, and conflicting records across sources.

## 2. Sample selection (documented, not cherry-picked)

Target sample size: **100–500 English headwords**. The set is drawn to cover
the case classes below, using a documented, repeatable rule (e.g. an
alphabetically-spread or frequency-slot selection from an independent English
word list), **not** a list of words already known to work.

| case class | why | example |
|---|---|---|
| common nouns | German gender + plural | house → Haus (das, Häuser) |
| common verbs | sense splits, multiple equivalents | go → gehen / fahren |
| irregular English verbs | English inflected forms | sing / sang / sung |
| adjectives | comparison forms | fast / faster / fastest |
| multi-sense words | sense separation | bank, run |
| several German equivalents | multiple `translations` rows | put → setzen/stellen/legen |
| words with grammatical/usage labels | label capture | colloquial/regional tags |
| words with **no** German translation | missing stays missing | — |
| German equivalents enriched in de.wiktionary | complementary merge | gender + plural + examples |
| words with/without an English definition | supplementary field | — |

The chosen sample and the selection rule must be committed alongside the
results so the study can be re-run.

## 3. Procedure (to run in a later, approved milestone)

Stages 1–2 touch the network and require explicit approval; 3–5 run locally.

1. **Obtain artefacts** into `data/raw/<source>/` (never committed): en
   Wiktextract JSONL, de Wiktextract JSONL, FreeDict eng-deu `.src.tar.xz`.
   Record URL, size and checksum for each.
2. **Verify** sizes/checksums and record extraction/dump dates.
3. **Extract the sample**: for each sampled English headword, locate the
   `lang_code == "en"` record(s) and collect `senses`, `translations`
   (`code: de`), `forms`; then locate the corresponding `lang_code == "de"`
   records and de.wiktionary records for the German equivalents.
4. **Score** each metric in §1; tally defects in §2.
5. **Write results** to this file (or a sibling `coverage-study-results.md`)
   as a table, with the command(s) used, source versions and dates, and the
   sample file path — so any number can be reproduced.

## 4. Metrics table (fill in when run)

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

## 5. Interpretation rules

- **Missing is not zero.** A blank cell means the source does not model that
  content, not that coverage is 0%.
- **Never infer.** If a source lacks a grammatical feature, it is recorded as
  missing; it is never derived to make a number look better.
- **Provenance stays attached** in every result, so a merged coverage number
  can always be decomposed per source.
- **Headline counts are not coverage.** FreeDict's 460,315 headwords are an
  entry count, not a measure of usable English→German sense pairs, and are
  not used to rank sources.
