# data/raw/

Raw source files for the import pipeline.

## Rules

- **Files in this directory are read-only input.** Importers never modify,
  move or delete raw files. All output goes to `data/processed/`.
- Nothing is downloaded automatically. Place source files here yourself,
  then run the corresponding importer, e.g.:

  ```
  python -m scripts.import.import_dictionary --source data/raw/dictionary.json
  python -m scripts.import.import_frequency  --source data/raw/frequency.json
  ```

## Licensing / attribution (required when adding real sources)

Every raw dataset must be accompanied by a manifest entry documenting:

1. **Source name and URL** — where the data was obtained.
2. **License** — the exact license (e.g. CC BY-SA 4.0, CC BY 3.0,
   GNU FDL) and a link to its text.
3. **Attribution text** — the copyright/attribution notice that must be
   shown in the product and in `README.md`.
4. **Redistribution terms** — whether the license permits redistribution
   of the derived/processed data, and under which conditions.
5. **Transformation notes** — what the importer changes (normalization,
   filtering, merging) relative to the original.

Datasets whose license does not allow redistribution of derived data must
not be committed to this repository, in raw or processed form.

## Placeholder for real sources

When real sources are added, keep one subdirectory per source, e.g.
`data/raw/creativecommons-de/`, each containing the raw files plus a
`MANIFEST.json` with the fields above. The dictionary and frequency
importers accept a `--source` path pointing at any of these files.
