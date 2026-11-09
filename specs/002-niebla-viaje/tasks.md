# Tareas: Niebla y viaje «ir a»

**Entrada**: spec.md, plan.md, research.md, data-model.md y contracts/.
**Estado inicial**: 30 tareas pendientes. Evidencia por escenario exigida por
constitución/P2 §2.5; pruebas antes de los cambios que verifican.
Sin cambios de estructuras respecto de las decisiones aprobadas.

## Fase 1 — Preparación

- [ ] T001 Ejecutar regresiones existentes y guardar línea base en documentacion/evidencia/pruebas_niebla.txt (FR-NV-015/017).
- [ ] T002 Verificar ignorados y registrar entorno/flujo en documentacion/PROMPTS_LLM.md y documentacion/evidencia/pruebas_niebla.txt (PR-NV-003, FR-NV-015).

## Fase 2 — Fundamentos

- [ ] T003 Escribir pruebas de índice estático, estados y recuerdos compartidos en Pruebas/prueba_conocimiento.py antes de implementar (FR-NV-001/002/003/005, PR-NV-002).
- [ ] T004 Crear modelo/conocimiento.py: arreglo compacto, hash estático doble, menor potencia C≥2 con 10·S≤7·C, salto impar 1..C−1 y máximo C sondeos; desconocidas sin nombre ni salidas; recuerdo inicialmente None; integrar campos básicos y formato 5 en adaptadores/estado_binario.py para mantener guardado válido (FR-NV-001/002/003/005/017, PR-NV-002).

## Fase 3 — US1: Conocer lo explorado (P1, MVP)

**Objetivo y prueba independiente**: t=0, entradas y observaciones distinguen
estados y memoria sin filtrar datos por precarga (AC-NV-001 a 005).

- [ ] T005 [US1] Añadir pruebas de inicialización/entradas, observación remota/local y consultas sin mutación en Pruebas/prueba_niebla_partida.py (FR-NV-001/002/003/004/005/015).
- [ ] T006 [US1] Conectar conocimiento inicial t=0 sin delta y observaciones durante acciones/eventos en modelo/motor_eventos.py y controlador/cargar_partida.py, sin escanear el mapa por revelación (FR-NV-001/002/003/005, PR-NV-002).
- [ ] T007 [US1] Filtrar estado y mensajes en controlador/partida.py: desconocidas/avistadas sin nombres ni contenido oculto; no observar al renderizar (FR-NV-002/003/005/015).
- [ ] T008 [US1] Incorporar ver mapa en controlador/comandos.py, controlador/controlador.py y vista/vista_consola.py sin acción ni azar (FR-NV-004/005/015).

## Fase 4 — US2: Antorcha (P1)

**Objetivo y prueba independiente**: vecinas abiertas/cerradas exploradas sin
contenido ni activación, sin propagación recursiva (AC-NV-006 a 008).

- [ ] T009 [US2] Escribir pruebas de antorcha y revelación local en Pruebas/prueba_conocimiento.py y Pruebas/prueba_niebla_partida.py (FR-NV-001/003/006/007).
- [ ] T010 [US2] Integrar revelación al entrar con antorcha en modelo/conocimiento.py y modelo/motor_eventos.py; no descargar contenido remoto ni activar enemigos/trampas vecinos (FR-NV-006/007, PR-NV-002).

## Fase 5 — US3: Viaje conocido (P1)

**Objetivo y prueba independiente**: rutas mínimas conocidas, eventos y paradas,
nombres exactos, movimientos registrados y replay (AC-NV-009 a 018).

- [ ] T011 [US3] Crear pruebas ponderadas/desempate/puerta recordada/generaciones en Pruebas/prueba_rutas_conocidas.py antes del núcleo (FR-NV-005/009/010/012/015).
- [ ] T012 [US3] Extraer núcleo Dijkstra compartido en modelo/rutas.py conservando wrapper, rango y auxiliares de cazadores (FR-NV-009/010/012/015).
- [ ] T013 [US3] Añadir registros por posición y generaciones en modelo/conocimiento.py, reutilizando HeapRutas con instancia separada por búsqueda; contar preparación/liberación de candidatos (FR-NV-009/010/012, PR-NV-001).
- [ ] T014 [US3] Escribir pruebas de ID/nombre completo sensible a mayúsculas, duplicados, destino actual y cada parada en Pruebas/prueba_niebla_partida.py y Pruebas/prueba_controlador.py (FR-NV-008/011/013).
- [ ] T015 [US3] Implementar resolución una vez por orden y ciclo de pasos ordinarios en controlador/partida.py y controlador/controlador.py; capturar enemigos al entrar y daño aunque se cure; preservar argumento completo en controlador/comandos.py (FR-NV-008/009/011/012/013/015).
- [ ] T016 [US3] Añadir interrupción opcional entre pasos y presentación de motivos en vista/vista_consola.py y controlador/controlador.py, sin confirmación por paso ni vista en replay (FR-NV-011/013/016).
- [ ] T017 [US3] Registrar comentario de viaje y movimientos individuales en adaptadores/bitacora_partida.py y controlador/controlador.py; ignorar comentarios al reproducir sin ejecutarlos (FR-NV-014/015).
- [ ] T018 [US3] Verificar equivalencia manual/viaje/replay sin vista y sin cambios de azar por consulta en Pruebas/prueba_bitacora_partida.py y Pruebas/prueba_niebla_partida.py (FR-NV-014/015).

## Fase 6 — US4: Conservar y revertir (P1)

**Objetivo y prueba independiente**: restaurar antorcha, estados/listas y memoria,
último paso sin continuar; cargar conserva deltas e identidad (AC-NV-019 a 022).

- [ ] T019 [US4] Escribir pruebas de pergamino tras entrada con antorcha y viaje en Pruebas/prueba_niebla_partida.py (FR-NV-011/016).
- [ ] T020 [US4] Completar registro de atributos/referencias en modelo/conocimiento.py y cancelación tras retroceder en controlador/partida.py usando modelo/retroceso.py existente, sin copias globales (FR-NV-016, PR-NV-002).
- [ ] T021 [US4] Añadir pruebas de guardar/cargar/retroceder, referencias compartidas y rechazo de formato anterior en Pruebas/prueba_estado_binario.py (FR-NV-003/017).
- [ ] T022 [US4] Completar validación de esquema 5 en adaptadores/estado_binario.py: IDs/posiciones únicos, conocimiento, referencias compartidas, deltas/listas anteriores; no regenerar memoria desde puerta física (FR-NV-003/016/017).
- [ ] T023 [US4] Reconstruir índices/auxiliares derivados y transferir conocimiento al reanudar en controlador/cargar_partida.py y adaptadores/estado_binario.py sin observaciones nuevas (FR-NV-015/017).

## Fase 7 — Medición y cierre

- [ ] T024 Escribir comprobación funcional del bench en Pruebas/prueba_bench_adaptadores.py, independiente del rendimiento del equipo (PR-NV-003).
- [ ] T025 Incorporar modelo/bench_conocimiento.py a --bench en modelo/bench_modelo.py: consultas, revelación por región, rutas y deltas con cargas deterministas, incluyendo alternativas de capacidad aprobadas para comparación (PR-NV-001/002/003).
- [ ] T026 Medir paso sobre mapa completo de referencia, verificar versiones y ausencia de HTTP/vista en cronómetro y conservar resultados/huellas en documentacion/evidencia/mediciones_niebla.json; reportar máximos y límite <5 ms (PR-NV-001/002/003).
- [ ] T027 Ejecutar aceptación y regresiones completas y guardar resultados en documentacion/evidencia/pruebas_niebla.txt (FR-NV-001/002/003/004/005/006/007/008/009/010/011/012/013/014/015/016/017).
- [ ] T028 Actualizar README.md, documentacion/DOCUMENTO_DECISIONES.md y specs/002-niebla-viaje/quickstart.md con comandos reales, decisiones, resultados y límites (PR-NV-001/002/003, FR-NV-004/008/014/017).
- [ ] T029 Completar cadena FR → AC → tarea → código → prueba en specs/002-niebla-viaje/tasks.md y documentacion/PROMPTS_LLM.md sin presentar pendientes como ejecutados (FR-NV-001/002/003/004/005/006/007/008/009/010/011/012/013/014/015/016/017).
- [ ] T030 Auditar restricciones, coherencia y estado final en modelo/conocimiento.py, modelo/rutas.py y specs/002-niebla-viaje/plan.md; confirmar cambios en Git tras verificarlos (PR-NV-002/003, FR-NV-005/015).

## Dependencias y estrategia

Ejecutar T001–004 antes de historias. US1 → US2 → US3 → US4 → cierre.
Los T dependen del anterior salvo pruebas que pueden escribirse antes sobre
contratos aprobados. Persistencia básica va en T004 porque el esquema estricto
rechaza campos nuevos; validación profunda y reanudación corresponden a US4.
T011 precede a T012/013; T014 precede a T015/016; T019/021 preceden a correcciones
de integración; T024 precede al bench. Corregir fallos antes de marcar [X].
MVP: US1 funcionando; continuar al resto dentro de la autorización de implementar.

No se marcan [P]: hay archivos compartidos entre tareas. Ejemplos de trabajo
independiente, si un equipo humano lo coordina: redactar casos de parser mientras
se revisa estado inicial (US1); preparar datos de antorcha (US2); preparar logs
de viaje (US3); diseñar cargas binarias corruptas (US4). Esto no autoriza agentes
paralelos ni ejecución de tareas con dependencias incompletas.

## Mapa de escenarios a tareas

| AC-NV | Tareas previstas |
| --- | --- |
| 001/002/003/004/005 | T003–008 |
| 006/007/008 | T009–010 |
| 009 | T014–015 |
| 010/011 | T011–013 |
| 012/013 | T011–016 |
| 014/015/016/017 | T014–016 |
| 018 | T017–018 |
| 019/020 | T019–020 |
| 021 | T021–023 |
| 022 | T018, T021–023 |

La cobertura anterior es prevista: los resultados reales se añadirán al terminar.
