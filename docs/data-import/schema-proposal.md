# Schema proposal (pre-import architecture) — no migration/model changes

**Status:** proposal only (not implemented). No schema/migration/API/UI/búsqueda changes in this hito.

## 1. Objetivo y restricciones

- Preservar homónimos (no fusionar). 
- Soportar `sense_id` nullable (traducciones headword-level estructurales en Wiktextract).
- Trazabilidad por dataset y registro (tablas unión). 
- Separación entre fuentes (CC BY-SA vs GPLv3/AGPLv3) arquitectónica.
- Import idempotente, sin fabricar datos.

## 2. Identidad

| Entidad | Clave candidata | Notas |
|---|---|---|
| Lexema | `(language, normalized_lemma, part_of_speech, etymology_number)` | Incluye `etymology_number` para evitar colapsar homónimos. |
| Sentido | `(lexeme_id, source_sense_index, data_source_id)` o external_id | Numeración origen. |
| Forma | `(lexeme_id, form_norm, tags_hash, data_source_id)` | Evita unicidad global. |
| Traducción | `(language_target, text_norm, lexeme_id?, sense_id?, gender?, data_source_id, external_id)` | Permite multi-origen/multi-equivalente. |

## 3. Entidades lógicas

| Tabla | Campos | Notas |
|---|---|---|
| `lexemes` | id PK, language, lemma, normalized_lemma, part_of_speech, etymology_number, tags JSON | etymology_number nullable. |
| `senses` | id PK, lexeme_id FK, sense_index, gloss, gloss_language, tags JSON | Glosas inglesas suplementarias. |
| `word_forms` | id PK, lexeme_id FK, form, form_norm, tags JSON | Formas; enriquecimiento de.de via procedencia. |
| `translations` | id PK, lexeme_id? FK nullable, sense_id? FK nullable, language, text, text_norm, gender?, tags JSON, notes JSON | sense_id nullable. |
| `examples` | id PK, sense_id? FK, lexeme_id? FK, text, translation_text?, language, translation_language? | Traducciones pueden faltar. |

## 4. Procedencia

Tablas unión: `lexeme_sources`, `sense_sources`, `word_form_sources`, `translation_sources` con `(record_id,data_source_id,external_id) PK`, `is_primary`, `confidence`, `notes`. `data_sources` registra dataset/version/licencia.

## 5. Diseño importación

Idempotente (match por data_source_id+external_id), homónimo-safe, sin inferir sense_id, transformaciones explícitas, gate para FreeDict (OFF hasta L3 validado). Esquema no garantiza compatibilidad de licencias.

## 6. Decisiones abiertas

is_primary/confidence, tags_hash, tratamiento de external_id ausente. Incorporación FreeDict bloqueada por L3.
