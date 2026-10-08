# Data import: source register

Provisional registry of candidate datasets for the German dictionary.
This register is a **planning artefact**: no dataset listed here has been
downloaded, imported or committed. Nothing was retrieved beyond the public
landing/metadata pages cited below.

## Verification legend

- **verified (page)** — the cited landing/documentation page was read for
  this register; the statement comes directly from it.
- **unverified** — reported elsewhere or assumed; must be confirmed before
  any import. In particular, a licence is only ever `verified` once the
  **exact dataset's own terms** (not the host project's general statement)
  have been inspected.

No licence below is marked `verified (dataset)` — that status requires
inspecting the licence text shipped *inside* the specific downloadable
artefact (TEI header, dump manifest), which was not done in this milestone.

## Registry

### SRC-DE-WIKTIONARY — German Wiktionary via Wiktextract (kaikki.org)

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
| content | "data for hundreds of languages, glosses and other metadata **in German**" |
| retrieval | **not downloaded** (landing page inspected only) |
| licence (source wiki) | CC BY-SA 4.0; historically also GFDL (dual-licensed contributions) |
| licence status | **verified (page)** for de.wiktionary.org footer; **unverified** for the kaikki-derived file itself |
| attribution | required (CC BY-SA): credit de.wiktionary + link; Wiktextract/kaikki citation requested |
| citation | Ylonen, *Wiktextract*, LREC 2022 |
| redistribution | likely permitted under CC BY-SA 4.0 share-alike with attribution — **to confirm against the file's own manifest** |
| outstanding | per-file manifest/licence; whether the extract inherits CC BY-SA 4.0 only; share-alike obligations for our derived data |

Language-edition scope: a German-language Wiktionary entry may describe a
word of *any* language. For this project only the **German (language = de)**
sections are in scope; everything else is a filtering concern (see plan §7).

### SRC-ES-WIKTIONARY — Spanish Wiktionary via Wiktextract (kaikki.org)

| field | value |
|---|---|
| source id | `es-wiktionary-wiktextract` |
| name | Spanish-language Wiktionary raw extraction (es.wiktionary) |
| landing page | https://kaikki.org/eswiktionary/rawdata.html |
| download | `raw-wiktextract-data.jsonl` (1.1 GB) / `.jsonl.gz` (98.4 MB) |
| format | JSONL — one Wiktextract object per line |
| format docs | https://github.com/tatuylonen/wiktextract |
| extraction date | 2026-10-02 |
| source dump | eswiktionary dump dated 2026-10-01 |
| content | "data for hundreds of languages, glosses and other metadata **in Spanish**" |
| retrieval | **not downloaded** (landing page inspected only) |
| licence (source wiki) | CC BY-SA 4.0 |
| licence status | **verified (page)** for es.wiktionary.org footer; **unverified** for the kaikki-derived file itself |
| attribution | required (CC BY-SA) |
| redistribution | likely permitted under CC BY-SA 4.0 share-alike with attribution — **to confirm** |
| outstanding | same as SRC-DE-WIKTIONARY; also **Spanish coverage of German lemmas is unknown** and must be measured before relying on it |

This edition is relevant only as a possible source of **Spanish-language
glosses/translations for German entries**; it is explicitly "work in
progress" per kaikki.org and may contain errors/omissions.

### SRC-FREEDICT-DEU-SPA — FreeDict German–Spanish

| field | value |
|---|---|
| source id | `freedict-deu-spa` |
| name | FreeDict German → Spanish dictionary |
| landing page | https://freedict.org/downloads/ |
| download | https://download.freedict.org/dictionaries/deu-spa/2025.11.23/freedict-deu-spa-2025.11.23.stardict.tar.xz (+ `.sha512`) |
| version | 2025.11.23 |
| size | 36,744 headwords (as listed) |
| formats | StarDict and dictd (dictzip) builds; canonical **source is TEI XML** |
| metadata API | https://freedict.org/freedict-database.json (CORS-enabled) |
| repo | https://github.com/freedict/fd-dictionaries |
| content | bilingual translation equivalents (German headword → Spanish); no definitions, no inflection tables, no frequency |
| retrieval | **not downloaded** |
| licence | per-dictionary, stated in the TEI header; project docs say "the majority … is licenced under GPL" |
| licence status | **unverified** — the deu-spa TEI header was **not** inspected |
| attribution | licence-dependent; must be read from the TEI header |
| redistribution | GPL (if applicable) has implications for bundling derived data — **must be confirmed** |
| outstanding | inspect deu-spa TEI header licence; decide whether GPL data is acceptable for the intended distribution |

### (Optional) SRC-FREEDICT-DEU-ENG / ENG-SPA — pivots

| field | value |
|---|---|
| source id | `freedict-deu-eng`, `freedict-eng-spa` |
| version / size | deu-eng 1.9-fd1, 517,534 headwords; eng-spa 2025.11.23, 64,258 headwords |
| role | possible German→English→Spanish **pivot** to widen Spanish coverage |
| status | listed for completeness; **not recommended for the pilot** (adds two hops, ambiguity, licence surface) |

## Explicit non-sources / rejected for now

| candidate | why not (now) |
|---|---|
| kaikki **post-processed** dictionaries (`kaikki.org/dictionary/German/`) | marked DEPRECATED on kaikki.org in favour of the raw Wiktextract data |
| Corpus **frequency** data | none of the above provides corpus frequency; the fixture's `fixture-de-2026` corpus is synthetic. Real frequency is an **open gap** (plan §9) |
| DWDS / other reference dictionaries | terms not inspected; not free/open by default; out of scope for the pilot |

## Open licensing questions (carry into plan §3/§9)

1. Does the kaikki.org JSONL file ship its own licence/attribution manifest,
   or does it rely on the source wiki's CC BY-SA 4.0?
2. Exact licence of the FreeDict **deu-spa** dictionary (TEI header) — GPL or
   otherwise — and what that means for distributing processed derivatives.
3. Share-alike reach: does combining CC BY-SA Wiktionary text with GPL
   FreeDict data (and our MIT code) impose incompatible obligations on the
   merged database? Legal review may be required.
4. Required attribution strings and where to surface them (README, an
   in-app "Sources" page, and/or per-entry provenance).
