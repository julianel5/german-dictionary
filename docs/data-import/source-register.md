# Data import: source register

Provisional registry of candidate datasets for the **English → German**
dictionary. This register is a **planning artefact**: no dataset listed here
has been downloaded, imported or committed. Nothing was retrieved beyond the
public landing/metadata pages cited below.

> **Direction correction.** An earlier revision of this register and of
> [`plan.md`](plan.md) assumed a **Spanish-primary** product (German headword,
> Spanish translations). That assumption is **void**. The product goal is now
> an English → German dictionary: **English headword, German translation
> equivalents primary, English definitions supplementary, German-language
> definition/inflection content complementary.** Spanish sources are demoted
> to optional/secondary.

## Verification legend

- **verified (page)** — the cited landing/documentation page was read for
  this register; the statement comes directly from it.
- **verified (dataset)** — the licence/identity text shipped *inside* the
  specific downloadable artefact (TEI header, dump manifest) was inspected.
- **unverified** — reported elsewhere or assumed; must be confirmed before
  any import. In particular, a licence is only ever `verified (dataset)`
  once the **exact dataset's own terms** (not the host project's general
  statement) have been inspected.

No licence below is marked `verified (dataset)` — that status requires
inspecting the licence text shipped inside the specific downloadable
artefact (TEI header, dump manifest), which was **not** done in this
milestone. Only public landing/metadata pages were read.

## Registry

### SRC-EN-WIKTIONARY — English Wiktionary via Wiktextract (kaikki.org) — **PRIMARY**

| field | value |
|---|---|
| source id | `en-wiktionary-wiktextract` |
| name | English-language Wiktionary raw extraction (en.wiktionary) |
| landing page | https://kaikki.org/dictionary/rawdata.html |
| download | `raw-wiktextract-data.jsonl` (23.9 GB) / `.jsonl.gz` (2.8 GB) |
| format | JSONL — one Wiktextract object per line |
| format docs | https://github.com/tatuylonen/wiktextract |
| extraction date | 2026-10-03 |
| source dump | enwiktionary dump dated 2026-09-02 |
| content | "data for hundreds of languages"; for **English** entries: English headwords, POS, English glosses/definitions, **translations into all languages (incl. German)**, English inflected forms, examples, relations, pronunciation; also entries for German (`lang_code == "de"`) with declension/conjugation captured |
| retrieval | **not downloaded** (landing page inspected only) |
| licence (source wiki) | CC BY-SA 4.0 |
| licence status | **verified (page)** for en.wiktionary.org footer/terms; **unverified** for the kaikki-derived file itself |
| attribution | required (CC BY-SA): credit en.wiktionary + link; Wiktextract/kaikki citation requested |
| citation | Ylonen, *Wiktextract*, LREC 2022 |
| redistribution | likely permitted under CC BY-SA 4.0 share-alike with attribution — **to confirm against the file's own manifest** |
| outstanding | per-file manifest/licence; whether the extract inherits CC BY-SA 4.0 only; share-alike obligations for our derived data |

Language-edition scope: an English-language Wiktionary entry may describe a
word of *any* language. For this project the **English** sections
(`lang_code == "en"`) are the headword/sense source, and their `translations`
arrays are the German-equivalent source. German sections
(`lang_code == "de"`) supply German-side inflection/enrichment. All other
languages are a filtering concern (see plan §7).

### SRC-EN-WIKTIONARY-PP — kaikki **post-processed** English dictionary — **DEPRECATED**

| field | value |
|---|---|
| source id | `en-wiktionary-postprocessed` |
| landing page | https://kaikki.org/dictionary/English/ |
| download | `kaikki.org-dictionary-English.jsonl` (3.1 GB) |
| content | English-lemma-only extraction; **1,390,507 distinct word forms**. Sense counts by POS: Noun 967,338; Verb ~263,101; Adjective 219,499; Adverb 30,929 |
| licence status | same host/wiki chain as above — **unverified** for the file |
| status | **marked DEPRECATED on kaikki.org** in favour of the raw Wiktextract data; listed only to explain why it is *not* selected |

### SRC-DE-WIKTIONARY — German Wiktionary via Wiktextract (kaikki.org) — **COMPLEMENTARY**

| field | value |
|---|---|
| source id | `de-wiktionary-wiktextract` |
| name | German-language Wiktionary raw extraction (de.wiktionary) |
| landing page | https://kaikki.org/dewiktionary/rawdata.html |
| download | `raw-wiktextract-data.jsonl` (2.9 GB) / `.jsonl.gz` (294.3 MB) |
| format | JSONL — one Wiktextract object per line |
| format docs | https://github.com/tatuylonen/wiktextract |
| extraction date | 2026-10-02 |
| source dump | dewiktionary dump dated 2026-09-01 |
| content | German-language glosses/metadata **in German**: German-language definitions, gender, declension/conjugation, inflections/alt forms, examples, relations |
| retrieval | **not downloaded** (landing page inspected only) |
| licence (source wiki) | CC BY-SA 4.0; historically also GFDL (dual-licensed contributions) |
| licence status | **verified (page)** for de.wiktionary.org footer; **unverified** for the kaikki-derived file itself |
| attribution | required (CC BY-SA): credit de.wiktionary + link; Wiktextract/kaikki citation requested |
| citation | Ylonen, *Wiktextract*, LREC 2022 |
| redistribution | likely permitted under CC BY-SA 4.0 share-alike with attribution — **to confirm against the file's own manifest** |
| outstanding | per-file manifest/licence; share-alike obligations for our derived data; **does not supply English headwords or German translations of English words** |

Language-edition scope: only the **German (`lang_code == "de")** sections
are in scope. Its distinguishing value for this product is the
**German-language** definition/inflection/flexion content that en.wiktionary
does not carry (en.wiktionary's German entries define German words in
English).

### SRC-FREEDICT-ENG-DEU — FreeDict English → German — **OPTIONAL SUPPLEMENTARY**

| field | value |
|---|---|
| source id | `freedict-eng-deu` |
| name | FreeDict English → German dictionary |
| landing page | https://freedict.org/downloads/ |
| version | **1.9-fd1** |
| date / status | 2022-04-15 / `stable` |
| headwords | **460,315** (as listed) |
| maintainer | Einhard Leichtfuß |
| source URL | https://dict.tu-chemnitz.de/ (free English–German dictionary by TU Chemnitz) |
| artefacts | `.src.tar.xz` 16,742,600 B (`e44d3a36…`); `.dictd.tar.xz` 19,145,688 B (`5b410a61…`); `.stardict.tar.xz` 26,877,184 B (`2dda62c6…`); `.slob` 39,437,035 B (`693b6541…`) |
| download base | https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/ (+ `.sha512` per artefact) |
| formats | StarDict and dictd (dictzip) builds; canonical **source is TEI XML** |
| metadata API | https://freedict.org/freedict-database.json (CORS-enabled; **no licence field** in the API payload) |
| repo | https://github.com/freedict/fd-dictionaries |
| content | bilingual translation equivalents (English headword → German); no definitions, no inflection tables, no frequency |
| retrieval | **not downloaded** |
| licence | per-dictionary, stated in the TEI header; project docs say "the majority … is licenced under GPL" |
| licence status | **unverified** — the eng-deu TEI header was **not** inspected; the metadata API does not expose a licence |
| attribution | licence-dependent; must be read from the TEI header |
| redistribution | GPL (if applicable) has implications for bundling derived data — **must be confirmed** |
| outstanding | inspect eng-deu TEI header licence; confirm whether the 460,315 headline count reflects usable *English→German* pairs; decide whether GPL data is acceptable for the intended distribution |

### Optional / secondary sources (Spanish demoted)

| source id | name | facts | role now |
|---|---|---|---|
| `es-wiktionary-wiktextract` | Spanish Wiktionary via Wiktextract | https://kaikki.org/eswiktionary/rawdata.html; `raw-wiktextract-data.jsonl` 1.1 GB / 98.4 MB gz; extracted 2026-10-02 from eswiktionary dump 2026-10-01; glosses/metadata in Spanish; CC BY-SA 4.0 (page-verified) | optional second/third-language glosses only; **not required for completeness** |
| `freedict-deu-spa` | FreeDict German → Spanish | https://freedict.org/downloads/; version 2025.11.23; 36,744 headwords; TEI XML source, StarDict/dictd; licence **unverified** (per-dictionary, "majority GPL") | optional; German-side pivot only, not English→German |
| `freedict-deu-eng` | FreeDict German → English | version 1.9-fd1; 517,534 headwords | optional reverse-pivot only |
| `freedict-eng-spa` | FreeDict English → Spanish | version 2025.11.23; 64,258 headwords | optional pivot; not German |

## Explicit non-sources / rejected for now

| candidate | why not (now) |
|---|---|
| kaikki **post-processed** dictionaries (e.g. `kaikki.org/dictionary/English/`) | marked DEPRECATED on kaikki.org in favour of the raw Wiktextract data |
| Corpus **frequency** data | none of the above provides corpus frequency; the fixture's `fixture-de-2026` corpus is synthetic. Real frequency is an **open gap** (plan §9) |
| DWDS / other reference dictionaries | terms not inspected; not free/open by default; out of scope for the pilot |

## Open licensing questions (carry into plan §3/§9)

1. Does the kaikki.org JSONL file ship its own licence/attribution manifest,
   or does it rely on the source wiki's CC BY-SA 4.0?
2. Exact licence of the FreeDict **eng-deu** dictionary (TEI header) — GPL or
   otherwise — and what that means for distributing processed derivatives.
3. Share-alike reach: does combining CC BY-SA Wiktionary text with GPL
   FreeDict data (and our MIT code) impose incompatible obligations on the
   merged database? Legal review may be required.
4. Required attribution strings and where to surface them (README, an
   in-app "Sources" page, and/or per-entry provenance).
