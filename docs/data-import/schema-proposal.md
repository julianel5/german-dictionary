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

## 9. Integridad, índices, cardinalidades y referencias

### Cardinalidades

- lexemes (1:N) senses, word_forms, translations (cuando lexeme_id no nulo), examples
- senses (1:N) word_forms? (no forzado), (1:N) translations (cuando sense_id no nulo), (1:N) examples
- translations (N:1) lexeme, (N:1) sense (nullable), (N:1) data_source
- todas las entidades (N:1) data_sources vía tablas unión

### Índices candidatos (propuestos, no implementados)

- lexemes: (language, normalized_lemma, part_of_speech, etymology_number)
- lexemes: (normalized_lemma)
- senses: (lexeme_id, source_sense_index)
- translations: (lexeme_id, language), (sense_id, language) cuando no nulo
- word_forms: (lexeme_id, form_norm)
- fuentes unión: (record_id, data_source_id, external_id) + (data_source_id, external_id)

### Restricciones / integridad

- etymology_number nullable; nunca asumir único sin él cuando hay homónimos
- sense_id nullable en translations (headword-level). No crear FKs forzosas que impidan este caso
- data_source_id obligatorio en todas las filas de contenido con procedencia
- external_id: si el origen no proporciona un identificador estable, **no** tratar los valores ausentes como iguales entre sí. Usar una clave determinista de importación (p.ej. hash estable basado en dataset+fuente+lemma/forma+contexto) y registrar explícitamente `external_id_missing=true` en `notes` del enlace de procedencia. Nunca usar cadena vacía como comodín para fusionar registros distintos.
- evitar unicidad global que fusione homónimos o textos multi-origen
- colisiones homónimas: si no existe etymology_number, usar identidad + external_id + data_source_id para desambiguar; documentar caso

### Identificadores externos y ausentes

- external_id preserva id original del dump (Wiktextract) para idempotencia
- si external_id falta: generar clave determinista de importación (hash estable de contenido+fuente+contexto+índice) y registrarlo en el enlace de procedencia (`notes` o campo `external_id_deterministic`), marcando `external_id_missing=true`. Mantener explícito que el id de origen no existe; nunca mapear ausencias como idénticas.
- no usar external_id para fusionar entre fuentes distintas

### Idempotencia, validación, rollback

- Idempotente: match por (data_source_id, external_id); actualizar campos no-provenance sin borrar filas unión existentes
- Validación: chequear cardinalidades, no colapsar homónimos, sense_id nullable respetado, presencia de data_source para cada registro con procedencia
- Rollback: import por lotes con transacciones por dataset/version; poder revertir lote sin afectar otros datasets
- Informes: resumen (insertados/actualizados/omitidos), conflictos, homónimos detectados, traducciones sin sentido

### Decisiones propuestas vs pendientes

- **Propuestas:** unión por join tables, inclusión etymology_number, sense_id nullable, gate FreeDict OFF.
- **Pendientes:** is_primary regla (conflicto texto), confidence semantics, tags_hash formato, política external_id vacío, juicio legal L3.
