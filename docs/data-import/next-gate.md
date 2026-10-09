# Next gate: license decision & approval path

**Status:** decisión operativa requerida. Solo diseño con datos sintéticos autorizado; importación real/redistribución bloqueados.

## 1. Estado

- Cobertura piloto (Marco A, n=997): en.wiktionary 79,54%; FreeDict 86,76%; al menos una 91,47%; ninguna 8,53%. Muestra piloto, no cobertura total.
- Bloqueos: L1=UNVERIFIED, L3=UNVERIFIED, L4=UNVERIFIED.

## 2. Medición vs autorización

Medición solo lectura permitida. Importación/redistribución requieren los tres bloqueos verificables.

## 3. Bloqueos

| Bloqueo | Estado | Pendiente | Responsable | Cierre |
|---|---|---|---|---|
| L1 | UNVERIFIED | Manifiesto dump concreto (url, licence/licence_url, attribution_text, source_version, retrieved_at, checksum, README/LICENSE del .jsonl.gz) | Producto/Legal | Manifiesto completo validado (nunca commiteado). |
| L3 | UNVERIFIED | Opinión jurídica por escenarios (separados vs fusionados, BD distribuida/export, servicio red/AGPLv3, jurisdicción) | Legal | Opinión cubre escenarios; si no, NO-GO permanente para combinar/distribuir FreeDict. |
| L4 | UNVERIFIED | Validar textos por superficies (README, Sources, ficha, exports), export gate | Producto+Legal | Textos aprobados; export deshabilitado por defecto. Exports requieren revalidación. |

## 4. Matriz GO/NO-GO

| Escenario | Ahora | Condiciones |
|---|---|---|
| Mediciones solo lectura | GO | Ninguna. |
| Diseño datos sintéticos | GO | Ninguna. |
| Import Wiktionary/Wiktextract BD desarrollo | NO-GO | L1 VERIFICADO + L4 mínimo aprobado. |
| Incorporar FreeDict | NO-GO | L3 VERIFICADO. |
| Combinar textos distintas fuentes | NO-GO | L3 validado para ese escenario. |
| Distribuir exports/dumps | NO-GO | L1,L3,L4 VERIFICADOS + gate explícito. |
| Desplegar con datos reales | NO-GO | Según inclusión FreeDict (L3). |

## 5. Próximos pasos

1. Diseño sintético (sin migraciones). 2. Obtener manifiesto L1. 3. Solicitar opinión jurídica L3. 4. Validar L4 y export gate. 5. Re-evaluar tras cumplimiento.

## 6. Decisión

Autorizado: solo mediciones solo lectura y diseño con datos sintéticos. No autorizado: import real, incorporar FreeDict, combinar fuentes con licencias distintas, distribuir exports/dumps. Bloqueos permanecen mientras L1/L3/L4 UNVERIFIED.

## 7. Requisitos por escenario (detalle)

### S1: Mediciones locales solo lectura
- **Bloqueos aplicables:** ninguno nuevo
- **Evidencia necesaria:** artefactos externos verificados (ya existentes)
- **Autorizado:** sí (ya realizado)

### S2: Diseño con datos sintéticos
- **Bloqueos aplicables:** ninguno
- **Evidencia necesaria:** fixtures sintéticas sin texto real
- **Autorizado:** sí (interfaces, esquema lógico, pruebas)

### S3: Importar Wiktionary/Wiktextract a BD desarrollo (exclusivamente)
- **Incluye FreeDict:** NO
- **Bloqueos aplicables:** L1, L4 (mínimo)
- **Evidencia necesaria L1:** manifiesto dump concreto completo
- **Evidencia necesaria L4:** textos aprobados (README, Sources, ficha, panel) + export gate
- **Condición:** L1 VERIFICADO, L4 superficies mínimas aprobadas. **No requiere** L3.

### S4: Incorporar FreeDict
- **Bloqueos aplicables:** L3 (y L4 si se expone)
- **Evidencia necesaria L3:** opinión jurídica por escenarios (separados vs fusionados, BD distribuida/export, servicio red/AGPLv3, jurisdicción)
- **Condición:** L3 VERIFICADO explícitamente. Nunca asumir por separación arquitectónica.

### S5: Combinar textos de fuentes distintas
- **Bloqueos aplicables:** L3 si alguna es FreeDict; revisar según fuentes
- **Evidencia necesaria:** validación para ese escenario concreto
- **Condición:** solo si compatible; por defecto NO-GO si FreeDict involucrado

### S6: Distribuir exportaciones/dumps
- **Bloqueos aplicables:** L1, L3 (si incluye FreeDict), L4
- **Evidencia necesaria:** todos verificados + NOTICE + atribución completa + export gate explícito
- **Condición:** **NO-GO** mientras cualquiera UNVERIFIED

### S7: Desplegar servicio con datos reales
- **Subcaso 7a:** solo Wiktionary/Wiktextract → requiere L1 + L4 mínimo; **no requiere L3**
- **Subcaso 7b:** incluye FreeDict → requiere L1 + L3 + L4
- **Evidencia necesaria:** según subcaso
- **Condición:** explícita por subcaso; nunca autorizar implícitamente por inclusión/exclusión cruzada
