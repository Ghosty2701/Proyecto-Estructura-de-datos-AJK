# Specification Quality Checklist: Terreno y cazadores

**Purpose**: Revisar calidad y completitud de la especificación antes de planificar.
**Created**: 2026-11-07
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] CHK001 No se eligen estructuras, algoritmos, clases, módulos o dependencias.
- [x] CHK002 Se explica el valor para el jugador de terreno y persecución.
- [x] CHK003 Las historias y ejemplos expresan comportamientos observables del juego.
- [x] CHK004 Todas las secciones obligatorias de la plantilla están completas.

## Requirement Completeness

- [x] CHK005 No quedan marcadores de aclaración sin resolver en las reglas de la capacidad.
- [x] CHK006 Los requisitos funcionales son verificables y tienen identificadores estables.
- [x] CHK007 Los criterios de éxito incluyen cobertura, igualdad observable y límite de tiempo.
- [x] CHK008 Los criterios de éxito no prescriben herramientas o implementaciones concretas.
- [x] CHK009 Los siete casos obligatorios aplicables del apéndice B tienen escenarios explícitos.
- [x] CHK010 Se definen bordes de costo, rango, empate, puertas, velocidad y datos disponibles.
- [x] CHK011 El alcance separa esta capacidad de las otras tres de P2.
- [x] CHK012 Las dependencias y limitaciones de evidencia están identificadas en Assumptions.

## Feature Readiness

- [x] CHK013 Los 14 requisitos funcionales se enlazan desde escenarios de aceptación.
- [x] CHK014 Las cuatro historias cubren movimiento, persecución, cambios e integración observable.
- [x] CHK015 Los resultados medibles corresponden a reglas y condiciones del enunciado.
- [x] CHK016 La especificación deja las decisiones de implementación para el plan.

## Notes

- Revisión documental completada el 2026-11-07. Las marcas confirman calidad del documento,
  no implementación, pruebas ejecutadas ni mediciones de rendimiento.
- Cobertura del apéndice B, bloque terreno y cazador, en su orden original:

  | Caso | Escenario | Requisitos |
  | --- | --- | --- |
  | Sin ruta abierta | AC-TC-007 | FR-TC-006, FR-TC-007 |
  | Ruta fuera de rango | AC-TC-008 | FR-TC-007, FR-TC-008 |
  | Menos salas y mayor costo | AC-TC-009 | FR-TC-006, FR-TC-008 |
  | Empate entre primeras vecinas | AC-TC-010 | FR-TC-009 |
  | Puerta se cierra entre turnos | AC-TC-012 | FR-TC-011 |
  | Costo 1 y velocidad alta | AC-TC-003 | FR-TC-002 |
  | Cambio de velocidad en salida costosa | AC-TC-004 | FR-TC-003 |

- PR-TC-001 se acepta mediante SC-TC-004; PR-TC-002 y PR-TC-003 mediante SC-TC-005.
  La carga y las mediciones se concretarán en el plan; no se inventa un resultado empírico.
- Falta el enunciado original de P1 y falta identificar la cripta de referencia y la carga
  oficial de cazadores. Estas limitaciones están declaradas y no se convierten en reglas nuevas.
- No hay aclaraciones imprescindibles para redactar esta especificación: las reglas principales
  proceden de P2. La siguiente fase del flujo es `$speckit-clarify`, antes de `$speckit-plan`.
- No se requiere rama nueva según la habilidad sin hooks. La rama actual es `main`.
- La especificación deberá confirmarse en Git antes de los cambios de código que la implementen.
