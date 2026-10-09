# Attribution proposal (draft, pending validation) — L4

**Status:** BORRADOR PENDIENTE DE VALIDACIÓN. This is a technical proposal, not a legal conclusion. It reflects the pilot findings (997-lemma study, frame A approved) and the separation principle (no automatic merge of sources with incompatible licences).

## 1. Objetivo y alcance

El objetivo es establecer cómo se atribuirá y rastreará la procedencia de los datos en un diccionario inglés→alemán, preservando las obligaciones de las licencias de cada fuente. Esto cubre:

- Separación entre código (MIT) y datos (licencias propias por fuente).
- Atribución por fuente, versión y registro concreto.
- Trazabilidad por registro para que la atribución sobreviva a fusiones.
- Tratamiento de Wiktionary/Wiktextract y FreeDict con estados `UNVERIFIED` para L1/L3/L4.

**Alcance:** diseño previo a importación real. **Exclusiones:** migraciones, cambios a API/UI/búsqueda.

## 2. Código vs datos

- **Código:** MIT (`LICENSE`). No implica licencia sobre datos importados.
- **Datos:** cada conjunto tiene licencia propia. Las obligaciones aplican a datos derivados de esa fuente.
- **Distribución vs contenido:** licencia del contenido (CC BY-SA 4.0) no garantiza términos del dump concreto (JSONL). Ahí radica L1.

## 3. Fuentes

| Fuente | Licencia conocida | Estado | Tratamiento |
|---|---|---|---|
| Wiktionary (en/de) vía Wiktextract | CC BY-SA 4.0 (contenido). Términos del dump concreto desconocidos. | L1/L4 UNVERIFIED | Primaria. Requiere manifiesto por dump (URL, licencia/licence_url, attribution_text, source_version, retrieved_at, checksum). |
| FreeDict eng-deu (TEI) | GPLv3 + AGPLv3 (cabecera TEI) | L3/L4 UNVERIFIED | Solo medición hasta opinión jurídica. No fusionar con Wiktionary; si se incorporara tras validación, mantener separados con su propio `data_source_id`. |

## 4. Manifiesto (requerido antes de ingestión real)

Campos mínimos: `id`, `source_id`, `name`, `url`, `licence`, `licence_url`, `attribution_text`, `source_version`, `retrieved_at`, `checksum`, `processed_at`, `notes`. El `attribution_text` es borrador hasta validación.

## 5. Superficies de atribución (borrador)

| Superficie | Texto propuesto (borrador) | Notas |
|---|---|---|
| README | "Data sources: English/German Wiktionary (CC BY-SA 4.0), processed via Wiktextract. FreeDict eng-deu (GPLv3+AGPLv3) used only for read-only measurement; not incorporated pending legal review." | Actualizar con versiones al ingerir. |
| "Sources"/About (UI) | Listar fuente, URL, licencia+URL, versión, "Modifications noted in provenance". | Vincular a licencia completa. |
| Ficha de traducción | "Source: <nombre> · Licence: <corto> · Show provenance". Expandir con external_id/version. | Mostrar todas las fuentes. |
| Panel de procedencia | Listar filas en tablas unión; indicar `sense_id: nullable` cuando corresponda. | Sobrevive a merges. |
| Exportaciones/dumps | Deshabilitado por defecto. Requiere validación L1/L3/L4 antes de habilitar. | Bloqueado. |

## 6. Procedencia multi-origen

Usar tablas unión: `lexeme_sources`, `sense_sources`, `word_form_sources`, `translation_sources` con `(record_id, data_source_id, external_id)`, `is_primary`, `confidence`, `notes`. Traducciones con orígenes distintos → registros separados (nunca colapsar). Homónimos preservados.

## 7. Transformaciones a documentar

Normalización, filtrado, enriquecimiento (de.wiktionary: género/formas/glosas) y cambios relevantes en `notes`/provenance.

## 8. Pendientes y cierre

L1: manifiesto del dump concreto. L3: opinión jurídica por escenarios. L4: validación de textos por superficies y export gate. L4 solo pasa a VERIFICADO cuando todos aplicables estén aprobados.

## 10. Revisión y cierre detallados (criterios verificables)

### Responsables de revisión

- **Legal**: validación de manifiesto del dump, compatibilidad L3 (por escenarios), suficiencia de textos por superficie.
- **Producto**: superficies UI, política de exportación, qué mostrar en ficha de traducción/panel de procedencia.
- **Técnico**: implementación de tablas unión, trazabilidad, gates, idempotencia (sin cambios en este hito).

### Checklist verificable para cierre de L4

1. [ ] **Manifiesto completo**: `url`, `licence`, `licence_url`, `attribution_text` (aprobado), `source_version`, `retrieved_at`, `checksum`, `processed_at`, `notes` presentes y validados (vinculado a L1).
2. [ ] **Textos aprobados por superficie**: README, "Sources"/About, ficha de traducción, panel de procedencia. Cada uno con texto aprobado por legal+producto.
3. [ ] **Multi-origen**: tablas unión implementadas contractualmente; `is_primary` y visibilidad de todas las fuentes probados.
4. [ ] **sense_id nullable**: reflejado en UI copy ("sense: not specified (headword-level)") cuando aplica.
5. [ ] **Transformaciones registradas**: normalización/filtrado/enriquecimiento + "notice of changes" registrable en `notes`/provenance.
6. [ ] **Export gate**: deshabilitado por defecto; activación requiere revalidación explícita de L1/L3/L4.
7. [ ] **Diferenciación de licencias**: FreeDict nunca fusionado con Wiktionary sin ambos enlaces; gate para incorporación existe.
8. [ ] **No se autoriza distribución**: política explícita de "sin export/dump público" vigente hasta que todos los puntos se cumplan.

**Importante:** redactar esta propuesta no resuelve L4. L4 permanece `UNVERIFIED` hasta que legal+producto aprueben los ítems anteriores con evidencia concreta.
