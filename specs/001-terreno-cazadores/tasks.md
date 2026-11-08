# Tasks: Terreno y cazadores

**Input**: documentos de `specs/001-terreno-cazadores/`.
**Prerequisites**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [contratos](contracts/terreno-cazadores.md) y
[quickstart.md](quickstart.md).
**Fecha**: 2026-11-08.

**Estado**: tareas generadas; ninguna ejecutada. Antes de implementar, ejecutar
`$speckit-analyze` y confirmar la especificación en Git antes del código correspondiente.
**Tests**: la especificación exige evidencia por escenario. Se planifican pruebas
funcionales y de invariantes; cada caso cita sus requisitos. Los archivos futuros que
aparecen aquí son destinos de tareas, no archivos de prueba ya creados.
**Organization**: tareas por historia en orden de prioridad; no se cambia ninguna de las
estructuras elegidas por el usuario. La capacidad completa no se declara terminada hasta
completar sus escenarios e informar la evidencia de rendimiento pertinente.

## Format: `[ID] [P?] [Story] Description`

- Una tarea usa `- [ ] Tnnn`, marcador opcional `[P]`, historia `[USn]` cuando corresponde,
  descripción, rutas, requisitos y dependencias.
- `[P]` permite trabajar junto a otras tareas del mismo grupo cuyos prerrequisitos ya
  terminaron y cuyos archivos son distintos; no elimina las dependencias indicadas.
- La generación de esta lista no ejecuta sus tareas ni confirma archivos en Git.

## Path Conventions

Rutas desde la raíz: `modelo/`, `controlador/`, `adaptadores/`, `vista/`, `Pruebas/` y
`documentacion/`. La evidencia de ejecuciones se conservará en
`documentacion/evidencia/pruebas_terreno_cazadores.txt` y las mediciones en
`documentacion/evidencia/mediciones_terreno_cazadores.json`; no se crean resultados vacíos
ni cifras inventadas. No hay despliegue ni cambios de arquitectura fuera del plan.

## Phase 1: Setup — revisión y línea base

**Propósito**: disponer de antecedentes comprobables antes de modificar la aplicación.

- [ ] T001 Verificar en Git la precedencia de `specs/001-terreno-cazadores/spec.md` respecto del código; si aún no está confirmada, confirmar la documentación necesaria antes de cualquier cambio de implementación, sin incluir archivos ajenos. Registrar la referencia en `specs/001-terreno-cazadores/quickstart.md`. Requisitos: FR-TC-013, FR-TC-014 y constitución VII–VIII. Dependencias: análisis de consistencia completado.
- [ ] T002 Ejecutar la suite existente desde la raíz y registrar comando, entorno, commit y resultado real en `documentacion/evidencia/pruebas_terreno_cazadores.txt`; distinguir fallos previos de regresiones, sin sustituirlos por los 437 resultados históricos. Requisitos: FR-TC-013, FR-TC-014. Dependencias: T001.

## Phase 2: Foundational — estructuras aprobadas

**Propósito**: implementar la base de búsqueda sin conectarla todavía al turno del juego.
**Prerrequisitos**: T001–T002. Los ensayos sintéticos no contienen datos de criptas oficiales.

- [ ] T003 [P] Escribir en `Pruebas/prueba_tabla_hash.py` pruebas de igualdad de clave bajo colisiones, ID existente que no aumenta cantidad, redimensionamiento antes de superar 70 %, sondeo con salto impar y conservación de referencias; citar los parámetros de `specs/001-terreno-cazadores/data-model.md` y comprobar el fallo esperado antes de implementar. Requisitos: FR-TC-006, FR-TC-009, PR-TC-002. Dependencias: T002.
- [ ] T004 [P] Escribir en `Pruebas/prueba_heap_rutas.py` pruebas de mínimo lexicográfico, disminución de costo, mejora de primer salto con igual costo, extracción, unicidad de sala y actualización de todas las posiciones desplazadas, con registros simples de prueba. Requisitos: FR-TC-006, FR-TC-009, PR-TC-002. Dependencias: T002.
- [ ] T005 Implementar RegistroBusqueda y TablaDistancias en `modelo/tabla_hash.py`: claves "IDs enteros de sala", "Arreglo inicial de 32 casillas", doble dispersión propia determinista, salto `(h2(id) & (M - 1)) | 1`, máximo M sondeos, ampliación si `(cantidad + 1) * 10 > M * 7` y duplicación; actualizar sin insertar otra clave y redistribuir las mismas referencias. No introducir dict/set ni borrado por clave innecesario. Requisitos: FR-TC-006, FR-TC-009, PR-TC-002. Dependencias: T003.
- [ ] T006 Implementar HeapRutas en `modelo/heap_rutas.py` sobre referencias a RegistroBusqueda, con una entrada pendiente por sala, orden `(distancia, primer_salto_id, sala_id)` y campo "Índice actual o -1 si no está en el heap"; actualizar los índices en cada desplazamiento y preservar identidad al crecer la hash. Mantenerlo separado de AgendaEventos. Requisitos: FR-TC-006, FR-TC-009, PR-TC-002. Dependencias: T004, T005.
- [ ] T007 Ejecutar las pruebas de `Pruebas/prueba_tabla_hash.py` y `Pruebas/prueba_heap_rutas.py`, añadir el caso integrado crecimiento-hash/mejora-heap y registrar los resultados reales en `documentacion/evidencia/pruebas_terreno_cazadores.txt`. Requisitos: FR-TC-006, FR-TC-009, PR-TC-002. Dependencias: T005, T006.

**Checkpoint**: estructuras verificadas por invariantes; aún no hay un cazador integrado.

## Phase 3: User Story 1 — Movimiento según el terreno (Priority: P1) — MVP

**Goal**: incorporar costos de salida al reloj virtual conservando comportamientos de P1.
**Independent Test**: con actores existentes, costo omitido 100, costo250/velocidad125 → 200,
costo1/velocidad500 → 1 y reajuste del tiempo restante de AC-TC-004. La variante cazador
de AC-TC-002 se completa en T018 después de introducir ese comportamiento; el MVP de
terreno no se presenta como capacidad completa de cazadores.

### Tests for User Story 1

- [ ] T008 [US1] Crear en `Pruebas/prueba_terreno.py` los casos AC-TC-001, AC-TC-003, AC-TC-004, AC-TC-005 y las variantes de actores existentes de AC-TC-002; incluir costo inválido, simetría de tránsito y puerta abierta/cerrada desde ambos extremos. Citar requisitos y verificar fallos esperados de la capacidad nueva. Requisitos: FR-TC-001, FR-TC-002, FR-TC-003, FR-TC-004. Dependencias: T007.

### Implementation for User Story 1

- [ ] T009 [US1] Añadir costo a SalidaRastro en `modelo/rastro.py`, conservando las listas existentes y la restricción "costo entero ≥ 1; ausencia en datos equivale a 100; mismo costo en ambos sentidos"; no añadir matriz ni otro índice de mapa. Requisitos: FR-TC-001. Dependencias: T008.
- [ ] T010 [US1] Normalizar costos y validar coherencia de conexiones en `controlador/cargar_partida.py`; asegurar estado de puerta coherente en ambos sentidos también en cierres automáticos y restauración, sin usar el JSON inicial como estado actual ni introducir datos de una cripta concreta. Requisitos: FR-TC-001, FR-TC-010, FR-TC-014. Dependencias: T009.
- [ ] T011 [US1] Sustituir el costo fijo solo al mover jugador, errante o rastreador en `modelo/motor_eventos.py` por el de la salida atravesada; conservar `max(1, costo_salida * 100 // velocidad)`, el reajuste de P1 y los costos de ataque/espera, sin modificar las decisiones de errante/rastreador ni el consumo de azar. Requisitos: FR-TC-002, FR-TC-003, FR-TC-004. Dependencias: T009, T010.
- [ ] T012 [US1] Ejecutar `Pruebas/prueba_terreno.py` y las regresiones pertinentes de `Pruebas/prueba_motor_eventos.py` y `Pruebas/prueba_azar_reversible.py`; registrar resultados y diferir explícitamente la variante cazador de AC-TC-002 hasta T018 en `documentacion/evidencia/pruebas_terreno_cazadores.txt`. Requisitos: FR-TC-001, FR-TC-002, FR-TC-003, FR-TC-004. Dependencias: T011.

**Checkpoint**: MVP de terreno para los actores anteriores; no equivale al cierre de US2.

## Phase 4: User Story 2 — Persecución por costo mínimo y rango (Priority: P1)

**Goal**: el cazador ataca, espera o da un paso mínimo con desempate correcto.
**Independent Test**: mapas sintéticos con resultados conocidos y casos AC-TC-006 a 011,
sin depender de contenidos descargados ni de la niebla del jugador.

### Tests for User Story 2

- [ ] T013 [US2] Crear en `Pruebas/prueba_rutas.py` AC-TC-006 a AC-TC-011: sin ruta, rango599/600, camino de menos salas pero mayor costo, empate por primer vecino e independencia de contenido; probar que descubrir el objetivo no finaliza prematuramente y que la búsqueda no avanza reloj ni azar. Requisitos: FR-TC-005, FR-TC-006, FR-TC-007, FR-TC-008, FR-TC-009, FR-TC-010. Dependencias: T012.

### Implementation for User Story 2

- [ ] T014 [US2] Implementar `buscar_ruta(origen, objetivo, rango)` y ResultadoRuta en `modelo/rutas.py` con Dijkstra individual, TablaDistancias y HeapRutas aprobados; explorar solo salidas abiertas y candidatos dentro de rango, actualizar por menor distancia o menor primer salto con igual distancia y terminar al extraer objetivo/agotar rango; no ejecutar IO, azar ni acciones del juego. Requisitos: FR-TC-006, FR-TC-007, FR-TC-008, FR-TC-009, FR-TC-010, PR-TC-002. Dependencias: T013, T007, T010.
- [ ] T015 [US2] Añadir comportamiento cazador y campo rango a ActorTurnos en `modelo/motor_eventos.py` conservando "rango entero del catálogo, sin valor inventado por defecto; velocidad positiva"; revisar todas las validaciones de activación, preparación y ejecución sin cambiar los otros comportamientos. Requisitos: FR-TC-005, FR-TC-007, FR-TC-010. Dependencias: T013.
- [ ] T016 [US2] Incorporar rango desde fichas resueltas en `controlador/cargar_partida.py`, conservar versión y límite de fichas, y preparar cazadores sin descargar contenidos de salas de su ruta para decidir. Requisitos: FR-TC-007, FR-TC-010, FR-TC-014. Dependencias: T015, T010.
- [ ] T017 [US2] Integrar el turno del cazador en `modelo/motor_eventos.py`: atacar primero si comparte sala, esperar con costo100 sin ruta en rango, o dar exactamente un paso pagando la salida; conservar activación, muerte y agenda, sin abrir puertas ni ejecutar rutas completas. Requisitos: FR-TC-002, FR-TC-005, FR-TC-006, FR-TC-007, FR-TC-008, FR-TC-009, FR-TC-010. Dependencias: T014, T015, T016.
- [ ] T018 [US2] Completar la variante cazador de AC-TC-002 en `Pruebas/prueba_terreno.py` y la integración de AC-TC-006 a 011 en `Pruebas/prueba_partida.py`, bloqueando solicitudes de contenido durante el cálculo y alterando el orden de salidas para comprobar el desempate. Requisitos: FR-TC-001, FR-TC-002, FR-TC-005, FR-TC-006, FR-TC-007, FR-TC-008, FR-TC-009, FR-TC-010. Dependencias: T017.
- [ ] T019 [US2] Ejecutar las pruebas de US1/US2 y comparar en `Pruebas/prueba_rutas.py` la decisión contra resultados independientes conocidos, incluidos empates de distinto número de pasos; registrar evidencia en `documentacion/evidencia/pruebas_terreno_cazadores.txt`. Requisitos: FR-TC-001, FR-TC-002, FR-TC-005, FR-TC-006, FR-TC-007, FR-TC-008, FR-TC-009, FR-TC-010. Dependencias: T018.

**Checkpoint**: persecución correcta desde cero, todavía sin certificar rendimiento oficial.

## Phase 5: User Story 3 — Persecución coherente con los cambios (Priority: P1)

**Goal**: reutilizar solo el último resultado compatible y decidir como desde cero.
**Independent Test**: AC-TC-012 a 015, puerta abierta fuera de la ruta anterior y consulta
idéntica repetida; la igualdad se contrasta con una búsqueda nueva sobre el mismo estado.

### Tests for User Story 3

- [ ] T020 [US3] Añadir en `Pruebas/prueba_rutas.py` AC-TC-012 a AC-TC-015, consulta idéntica repetida y apertura lejana que crea una ruta mejor; comprobar cambios de origen/objetivo/rango, costo y cierre automático, sin exigir invalidar por cambios que no afectan la regla de rutas. Requisitos: FR-TC-005, FR-TC-009, FR-TC-011. Dependencias: T019.

### Implementation for User Story 3

- [ ] T021 [US3] Concretar en `modelo/rutas.py` el único último resultado por cazador con "origen / objetivo", "rango", "revision_conexiones", "primer_paso", "costo_total" y "encontrada"; reutilizar solo si coinciden las condiciones y no retener tablas/heaps anteriores ni crear otra caché. Requisitos: FR-TC-007, FR-TC-008, FR-TC-011, PR-TC-002. Dependencias: T020.
- [ ] T022 [US3] Conectar revisión escalar monotónica en `modelo/motor_eventos.py` y las operaciones de puerta de `modelo/efectos.py` donde corresponda: cambiarla por apertura/cierre/costo y después de retroceso, sin restaurar un identificador viejo que revalide otra historia ni recorrer el mapa por turno. Requisitos: FR-TC-011, FR-TC-013, FR-TC-014, PR-TC-002. Dependencias: T021, T010.
- [ ] T023 [US3] Comparar resultados reutilizados y frescos en `Pruebas/prueba_rutas.py` y `Pruebas/prueba_motor_retroceso.py`, tras daño, velocidad, movimiento/muerte de otros actores y restauración de puertas; comprobar que la invalidación no consume azar o tiempo virtual ni cambia la excepción del pergamino. Requisitos: FR-TC-011, FR-TC-013, FR-TC-014. Dependencias: T022.
- [ ] T024 [US3] Ejecutar el grupo de pruebas de US3 y registrar en `documentacion/evidencia/pruebas_terreno_cazadores.txt` AC-TC-012 a 015 y la parte de AC-TC-019 de retroceso; la parte de carga queda pendiente hasta T031. Requisitos: FR-TC-011, FR-TC-013, FR-TC-014. Dependencias: T023.

**Checkpoint**: validez conservadora comprobada en ejecución; restauración binaria pendiente de US4.

## Phase 6: User Story 4 — Información visible y partida reproducible (Priority: P2)

**Goal**: mostrar los datos nuevos y preservar equivalencia de replay, guardado y pergamino.
**Independent Test**: AC-TC-016 a 019: presentación, igualdad de dos ejecuciones/replay,
continuación con guardado/carga y estado tras retroceso.

### Tests for User Story 4

- [ ] T025 [P] [US4] Añadir AC-TC-016 en `Pruebas/prueba_partida.py` verificando costo de cada salida de la sala actual y distinción del cazador sin revelar salas desconocidas; no exigir todavía una implementación de niebla de guerra. Requisitos: FR-TC-012. Dependencias: T024.
- [ ] T026 [P] [US4] Añadir AC-TC-018 y la restauración de AC-TC-019 en `Pruebas/prueba_estado_binario.py`: costo/rango en esquema y lectura selectiva, referencias coherentes, guardado antiguo rechazado y resultados derivados descartados; conservar reloj, azar y acciones pendientes. Requisitos: FR-TC-011, FR-TC-014. Dependencias: T024.
- [ ] T027 [P] [US4] Añadir AC-TC-017 en `Pruebas/prueba_bitacora_partida.py`: dos ejecuciones y replay con iguales datos/semilla/acciones coinciden en tiempos, decisiones y estado; hacer fallar la creación de vista durante replay y comprobar esperas de red sin avance virtual. Requisitos: FR-TC-013. Dependencias: T024.

### Implementation for User Story 4

- [ ] T028 [US4] Incorporar costos y distinción de cazadores al estado presentado en `controlador/partida.py` y `vista/vista_consola.py`, conservando comandos y límites de mensajes de P1. Requisitos: FR-TC-012. Dependencias: T025.
- [ ] T029 [US4] Ampliar `adaptadores/estado_binario.py` y la restauración de `controlador/cargar_partida.py` para costo/rango, validación de cazador y lectura selectiva; usar versión nueva frente a la actual3, rechazar anteriores incompatibles y no serializar hash, heap, revisión derivada ni último resultado; invalidar derivados en carga. Requisitos: FR-TC-011, FR-TC-014. Dependencias: T026, T022.
- [ ] T030 [US4] Revisar y ajustar donde sea necesario `adaptadores/bitacora_partida.py` y el enrutamiento de `main.py` para que replay use el ejecutor común sin vista, con versiones compatibles y sin alterar secuencia de azar o costos por el modo de ejecución. Requisitos: FR-TC-013. Dependencias: T027, T017, T022.
- [ ] T031 [US4] Ejecutar AC-TC-016 a 019 y las regresiones pertinentes de `Pruebas/prueba_partida.py`, `Pruebas/prueba_estado_binario.py`, `Pruebas/prueba_bitacora_partida.py` y `Pruebas/prueba_integracion_pergamino.py`; registrar resultados reales y cualquier cobertura pendiente en `documentacion/evidencia/pruebas_terreno_cazadores.txt`. Requisitos: FR-TC-011, FR-TC-012, FR-TC-013, FR-TC-014. Dependencias: T028, T029, T030.

**Checkpoint**: funcionalidad integrada con evidencia de los 19 escenarios; rendimiento aún por medir.

## Phase 7: Polish & Cross-Cutting Concerns — rendimiento y cierre

- [ ] T032 Incorporar en `modelo/bench_modelo.py` cargas deterministas de uno/muchos cazadores, rangos pequeños/grandes, mapa ampliado fuera de rango, colisiones y ampliaciones de hash; comparar individual/compartido y reutilización/recálculo siempre con puertas estables/inestables, usando las estructuras elegidas también en la alternativa de medición y verificando igualdad de decisiones. Requisitos: FR-TC-006, FR-TC-009, FR-TC-011, PR-TC-002, PR-TC-003. Dependencias: T031.
- [ ] T033 Conectar la medición de ciclo completo en `adaptadores/bench_adaptadores.py` y `main.py`, incluyendo preparación/liberación de búsqueda, máximo del ciclo, ausencia de HTTP/vista dentro del cronómetro y repetición de agenda/retroceso con carga nueva; verificar el contrato en `Pruebas/prueba_bench_adaptadores.py`. Requisitos: FR-TC-013, PR-TC-001, PR-TC-002, PR-TC-003. Dependencias: T032.
- [ ] T034 Ejecutar los benchmarks y conservar parámetros, máximos, sondeos, operaciones, equipo, commit y versiones en `documentacion/evidencia/mediciones_terreno_cazadores.json`; identificar la cripta/carga oficial con decenas de cazadores y comprobar 20 ms. Si no está disponible, distinguir evidencia sintética y mantener pendiente la aceptación oficial, sin marcar esta tarea terminada. Si no cumple, consultar al usuario antes de cambiar estructuras. Requisitos: PR-TC-001, PR-TC-002, PR-TC-003. Dependencias: T033.
- [ ] T035 Ejecutar la suite completa y los recorridos de `specs/001-terreno-cazadores/quickstart.md` con datos compatibles disponibles; completar `documentacion/evidencia/pruebas_terreno_cazadores.txt` sin presentar comandos no ejecutados como resultados. Requisitos: FR-TC-001, FR-TC-002, FR-TC-003, FR-TC-004, FR-TC-005, FR-TC-006, FR-TC-007, FR-TC-008, FR-TC-009, FR-TC-010, FR-TC-011, FR-TC-012, FR-TC-013, FR-TC-014. Dependencias: T033.
- [ ] T036 Actualizar `documentacion/DOCUMENTO_DECISIONES.md` con problema, alternativas, elección del usuario, complejidad, mediciones y límites; enlazar spec/plan, conservar el cambio matriz→listas y explicar cualquier diferencia final autorizada, incluido el antes/después de P1. Requisitos: PR-TC-001, PR-TC-002, PR-TC-003; constitución VI. Dependencias: T034, T035.
- [ ] T037 Actualizar `README.md` y `specs/001-terreno-cazadores/quickstart.md` con spec-kit1.3.2, agente Codex, comandos reales y pruebas de aceptación de esta capacidad; corregir ejemplos futuros a funcionamiento verificado, sin anunciar --verificar, historia o ir a como implementados. Mantener `documentacion/PROMPTS_LLM.md` al día. Requisitos: FR-TC-012, FR-TC-013, FR-TC-014; constitución VII, IX. Dependencias: T035.
- [ ] T038 Revisar la tabla de trazabilidad de `specs/001-terreno-cazadores/tasks.md` frente a código, pruebas/logs y referencias de Git; confirmar cobertura real de todos los requisitos y escenarios antes de cerrar la capacidad, y dejar visibles las tareas/evidencias pendientes. Requisitos: FR-TC-001, FR-TC-002, FR-TC-003, FR-TC-004, FR-TC-005, FR-TC-006, FR-TC-007, FR-TC-008, FR-TC-009, FR-TC-010, FR-TC-011, FR-TC-012, FR-TC-013, FR-TC-014, PR-TC-001, PR-TC-002, PR-TC-003; constitución VIII. Dependencias: T036, T037.

## Dependencies & Execution Order

### Phase Dependencies

`Análisis de consistencia → Setup → Foundation → US1 → US2 → US3 → US4 → Cierre`.
No se presentan como independientes historias que modifican los mismos módulos centrales.
Cada grupo tiene un criterio de verificación propio sobre la base ya implementada.
T034 pendiente de datos oficiales no impide avanzar en T035/T037, pero impide certificar
rendimiento y cerrar T036/T038 como completos.

### User Story Dependencies

| Historia | Prerrequisitos | Criterio de aceptación del incremento |
| --- | --- | --- |
| US1, T008–T012 | T001–T007 | Terreno de actores existentes; AC-TC-002 completo después de US2 |
| US2, T013–T019 | US1 | Persecución desde cero y cierre de AC-TC-002 para cazador |
| US3, T020–T024 | US2 | Decisiones vigentes ante cambios y retroceso en ejecución |
| US4, T025–T031 | US3 | Presentación y equivalencia de reproducción/guardado/retroceso |

### Within Each User Story

Escribir las pruebas pertinentes y comprobar el fallo atribuible al requisito nuevo antes
de su implementación; un fallo previo del entorno no demuestra que el caso sea correcto.
Implementar modelo antes de integración y validar el incremento antes del siguiente grupo.
No modificar estructuras elegidas por conveniencia sin consultar al usuario.

### Parallel Opportunities

T003 y T004 pueden prepararse juntos después de T002. T025, T026 y T027 usan archivos
distintos y pueden prepararse juntos después de T024. Los demás grupos requieren la
secuencia indicada o revisión expresa de conflictos de archivos antes de trabajar en paralelo.
Los marcadores no ordenan iniciar agentes ni reparten responsabilidades entre integrantes.

## Parallel Example: User Story 1

No se propone paralelizar T009–T011: modelo, cargador y motor tienen dependencias.
Después de T011 pueden ejecutarse por separado los grupos de pruebas de terreno y las
regresiones de azar de T012, consolidando la evidencia una vez terminen ambos.

## Parallel Example: User Story 2

Después de T013, T014 (modelo/rutas.py) y T015 (modelo/motor_eventos.py) pueden desarrollarse
por separado con los contratos acordados; T017 espera ambos y el cargador de T016.
No se marca T016 paralelo con T015 porque requiere sus campos.

## Parallel Example: User Story 3

No se propone paralelizar T021–T023: prueba, almacenamiento e invalidación comparten
rutas.py y el contrato de revisión. Tras T023 pueden ejecutarse grupos separados de
pruebas de rutas y retroceso dentro de T024, sin escribir simultáneamente la evidencia.

## Parallel Example: User Story 4

T025, T026 y T027 pueden prepararse en paralelo tras T024. T028 puede implementarse
separado de T029/T030 si sus pruebas previas están listas, porque no modifica los archivos
de guardado ni del ejecutor de replay; T031 espera las tres integraciones.

## Implementation Strategy

### MVP First — User Story 1

Completar Setup/Foundation y terreno para actores existentes, validando costos y velocidad.
No presentar ese MVP como una versión completa de P2: cazador, invalidación y persistencia
se incorporan en las historias siguientes; el caso AC-TC-002 del cazador se cierra con US2.

### Incremental Delivery

Integrar US1, luego US2, US3 y US4, validando cada una sobre la base anterior. Medir después
sin sustituir requisitos de localidad por tiempos favorables de una sola carga pequeña.
Tasks prepara la ejecución; `$speckit-analyze` debe preceder a `$speckit-implement`.

## Trazabilidad prevista de escenarios

| Escenario | Requisitos | Implementación | Evidencia prevista |
| --- | --- | --- | --- |
| AC-TC-001 | FR-TC-001, FR-TC-002 | T009, T010, T011 | T008, T012 |
| AC-TC-002 | FR-TC-001, FR-TC-002, FR-TC-004 | T009, T010, T011, T017 | T008, T018, T019 |
| AC-TC-003 | FR-TC-002 | T011 | T008, T012 |
| AC-TC-004 | FR-TC-003 | T011 | T008, T012 |
| AC-TC-005 | FR-TC-004 | T011 | T008, T012 |
| AC-TC-006 | FR-TC-005 | T015, T017 | T013, T018, T019 |
| AC-TC-007 | FR-TC-006, FR-TC-007 | T014, T017 | T013, T018, T019 |
| AC-TC-008 | FR-TC-007, FR-TC-008 | T014, T017 | T013, T018, T019 |
| AC-TC-009 | FR-TC-006, FR-TC-008 | T014, T017 | T013, T018, T019 |
| AC-TC-010 | FR-TC-009 | T005, T006, T014 | T004, T013, T018, T019 |
| AC-TC-011 | FR-TC-010 | T010, T014, T016 | T013, T018, T019 |
| AC-TC-012 | FR-TC-011 | T021, T022 | T020, T023, T024 |
| AC-TC-013 | FR-TC-009, FR-TC-011 | T014, T021, T022 | T020, T023, T024 |
| AC-TC-014 | FR-TC-005, FR-TC-011 | T017, T021 | T020, T023, T024 |
| AC-TC-015 | FR-TC-011 | T021, T022 | T020, T023, T024 |
| AC-TC-016 | FR-TC-012 | T028 | T025, T031 |
| AC-TC-017 | FR-TC-013 | T030 | T027, T031 |
| AC-TC-018 | FR-TC-014 | T029 | T026, T031 |
| AC-TC-019 | FR-TC-011, FR-TC-014 | T022, T029 | T023, T024, T026, T031 |

PR-TC-001 se mide con T033/T034; PR-TC-002 con T032/T033/T034; PR-TC-003 con
T032/T033/T034/T036. La tabla expresa cobertura planificada, no evidencia ya ejecutada.

## Notes

Todas las tareas comienzan sin marcar. Solo la ejecución y verificación posteriores
permiten completarlas. Registrar prompts de cada fase con fecha y metadatos conocidos.
Los cambios de enunciado se reflejan primero en spec y luego en código, en commits distintos.
No generar todavía las otras tres capacidades ni implementar una estructura no aprobada.
