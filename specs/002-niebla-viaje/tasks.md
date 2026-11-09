# Tareas: Niebla y viaje «ir a»

**Entrada**: spec.md, plan.md, research.md, data-model.md y contracts/.
**Estado**: 30/30 tareas verificadas; implementacion y evidencia completadas. Evidencia por escenario exigida por
constitución/P2 §2.5; pruebas antes de los cambios que verifican.
Sin cambios de estructuras respecto de las decisiones aprobadas.

## Fase 1 — Preparación

- [X] T001 Ejecutar regresiones existentes y guardar línea base en documentacion/evidencia/pruebas_niebla.txt (FR-NV-015/017).
- [X] T002 Verificar ignorados y registrar entorno/flujo en documentacion/PROMPTS_LLM.md y documentacion/evidencia/pruebas_niebla.txt (PR-NV-003, FR-NV-015).

## Fase 2 — Fundamentos

- [X] T003 Escribir pruebas de índice estático, estados y recuerdos compartidos en Pruebas/prueba_conocimiento.py antes de implementar (FR-NV-001/002/003/005, PR-NV-002).
- [X] T004 Crear modelo/conocimiento.py: arreglo compacto, hash estático doble, menor potencia C≥2 con 10·S≤7·C, salto impar 1..C−1 y máximo C sondeos; desconocidas sin nombre ni salidas; recuerdo inicialmente None; integrar campos básicos y formato 5 en adaptadores/estado_binario.py para mantener guardado válido (FR-NV-001/002/003/005/017, PR-NV-002).

## Fase 3 — US1: Conocer lo explorado (P1, MVP)

**Objetivo y prueba independiente**: t=0, entradas y observaciones distinguen
estados y memoria sin filtrar datos por precarga (AC-NV-001 a 005).

- [X] T005 [US1] Añadir pruebas de inicialización/entradas, observación remota/local y consultas sin mutación en Pruebas/prueba_niebla_partida.py (FR-NV-001/002/003/004/005/015).
- [X] T006 [US1] Conectar conocimiento inicial t=0 sin delta y observaciones durante acciones/eventos en modelo/motor_eventos.py y controlador/cargar_partida.py, sin escanear el mapa por revelación (FR-NV-001/002/003/005, PR-NV-002).
- [X] T007 [US1] Filtrar estado y mensajes en controlador/partida.py: desconocidas/avistadas sin nombres ni contenido oculto; no observar al renderizar (FR-NV-002/003/005/015).
- [X] T008 [US1] Incorporar ver mapa en controlador/comandos.py, controlador/controlador.py y vista/vista_consola.py sin acción ni azar (FR-NV-004/005/015).

## Fase 4 — US2: Antorcha (P1)

**Objetivo y prueba independiente**: vecinas abiertas/cerradas exploradas sin
contenido ni activación, sin propagación recursiva (AC-NV-006 a 008).

- [X] T009 [US2] Escribir pruebas de antorcha y revelación local en Pruebas/prueba_conocimiento.py y Pruebas/prueba_niebla_partida.py (FR-NV-001/003/006/007).
- [X] T010 [US2] Integrar revelación al entrar con antorcha en modelo/conocimiento.py y modelo/motor_eventos.py; no descargar contenido remoto ni activar enemigos/trampas vecinos (FR-NV-006/007, PR-NV-002).

## Fase 5 — US3: Viaje conocido (P1)

**Objetivo y prueba independiente**: rutas mínimas conocidas, eventos y paradas,
nombres exactos, movimientos registrados y replay (AC-NV-009 a 018).

- [X] T011 [US3] Crear pruebas ponderadas/desempate/puerta recordada/generaciones en Pruebas/prueba_rutas_conocidas.py antes del núcleo (FR-NV-005/009/010/012/015).
- [X] T012 [US3] Extraer núcleo Dijkstra compartido en modelo/rutas.py conservando wrapper, rango y auxiliares de cazadores (FR-NV-009/010/012/015).
- [X] T013 [US3] Añadir registros por posición y generaciones en modelo/conocimiento.py, reutilizando HeapRutas con instancia separada por búsqueda; contar preparación/liberación de candidatos (FR-NV-009/010/012, PR-NV-001).
- [X] T014 [US3] Escribir pruebas de ID/nombre completo sensible a mayúsculas, duplicados, destino actual y cada parada en Pruebas/prueba_niebla_partida.py y Pruebas/prueba_controlador.py (FR-NV-008/011/013).
- [X] T015 [US3] Implementar resolución una vez por orden y ciclo de pasos ordinarios en controlador/partida.py y controlador/controlador.py; capturar enemigos al entrar y daño aunque se cure; preservar argumento completo en controlador/comandos.py (FR-NV-008/009/011/012/013/015).
- [X] T016 [US3] Añadir interrupción opcional entre pasos y presentación de motivos en vista/vista_consola.py y controlador/controlador.py, sin confirmación por paso ni vista en replay (FR-NV-011/013/016).
- [X] T017 [US3] Registrar comentario de viaje y movimientos individuales en adaptadores/bitacora_partida.py y controlador/controlador.py; ignorar comentarios al reproducir sin ejecutarlos (FR-NV-014/015).
- [X] T018 [US3] Verificar equivalencia manual/viaje/replay sin vista y sin cambios de azar por consulta en Pruebas/prueba_bitacora_partida.py y Pruebas/prueba_niebla_partida.py (FR-NV-014/015).

## Fase 6 — US4: Conservar y revertir (P1)

**Objetivo y prueba independiente**: restaurar antorcha, estados/listas y memoria,
último paso sin continuar; cargar conserva deltas e identidad (AC-NV-019 a 022).

- [X] T019 [US4] Escribir pruebas de pergamino tras entrada con antorcha y viaje en Pruebas/prueba_niebla_partida.py (FR-NV-011/016).
- [X] T020 [US4] Completar registro de atributos/referencias en modelo/conocimiento.py y cancelación tras retroceder en controlador/partida.py usando modelo/retroceso.py existente, sin copias globales (FR-NV-016, PR-NV-002).
- [X] T021 [US4] Añadir pruebas de guardar/cargar/retroceder, referencias compartidas y rechazo de formato anterior en Pruebas/prueba_niebla_partida.py y Pruebas/prueba_estado_binario.py (FR-NV-003/017).
- [X] T022 [US4] Completar validación de esquema 5 en adaptadores/estado_binario.py: IDs/posiciones únicos, conocimiento, referencias compartidas, deltas/listas anteriores; no regenerar memoria desde puerta física (FR-NV-003/016/017).
- [X] T023 [US4] Reconstruir índices/auxiliares derivados y transferir conocimiento al reanudar en controlador/cargar_partida.py y adaptadores/estado_binario.py sin observaciones nuevas (FR-NV-015/017).

## Fase 7 — Medición y cierre

- [X] T024 Escribir comprobación funcional del bench en Pruebas/prueba_bench_adaptadores.py, independiente del rendimiento del equipo (PR-NV-003).
- [X] T025 Incorporar modelo/bench_conocimiento.py a --bench en modelo/bench_modelo.py: consultas, revelación por región, rutas y deltas con cargas deterministas, incluyendo alternativas de capacidad aprobadas para comparación (PR-NV-001/002/003).
- [X] T026 Medir paso sobre mapa completo de referencia, verificar versiones y ausencia de HTTP/vista en cronómetro y conservar resultados/huellas en documentacion/evidencia/mediciones_niebla.json; reportar máximos y límite <5 ms (PR-NV-001/002/003).
- [X] T027 Ejecutar aceptación y regresiones completas y guardar resultados en documentacion/evidencia/pruebas_niebla.txt (FR-NV-001/002/003/004/005/006/007/008/009/010/011/012/013/014/015/016/017).
- [X] T028 Actualizar README.md, documentacion/DOCUMENTO_DECISIONES.md y specs/002-niebla-viaje/quickstart.md con comandos reales, decisiones, resultados y límites (PR-NV-001/002/003, FR-NV-004/008/014/017).
- [X] T029 Completar cadena FR → AC → tarea → código → prueba en specs/002-niebla-viaje/tasks.md y documentacion/PROMPTS_LLM.md sin presentar pendientes como ejecutados (FR-NV-001/002/003/004/005/006/007/008/009/010/011/012/013/014/015/016/017).
- [X] T030 Auditar restricciones, coherencia y estado final en modelo/conocimiento.py, modelo/rutas.py y specs/002-niebla-viaje/plan.md; confirmar cambios en Git tras verificarlos (PR-NV-002/003, FR-NV-005/015).

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

La cobertura anterior era prevista al generar las tareas. La siguiente tabla
registra la cadena ejecutada: requisitos con prefijo FR-NV-, escenarios AC-NV-,
tareas y archivos de código y pruebas relativos a la raíz. Cada prueba cita FR
en comentario o docstring. Las pruebas son funciones reales ejecutadas.

| AC-NV | FR-NV | Tareas | Código | Pruebas ejecutadas en Pruebas/ |
| --- | --- | --- | --- | --- |
| 001 | 001/002/004 | T003–008 | modelo/conocimiento.py, controlador/partida.py | prueba_conocimiento.py:test_ac001_002_003_inicio_y_precarga_no_revelan; prueba_niebla_partida.py:test_ac001_003_005_proyeccion_no_revela_ni_observa |
| 002 | 001/002 | T005–007 | modelo/motor_eventos.py | prueba_niebla_partida.py:test_ac002_004_observacion_dentro_de_accion_y_ambos_extremos |
| 003 | 002/005 | T003–007 | controlador/partida.py | prueba_conocimiento.py:test_ac001_002_003_inicio_y_precarga_no_revelan; prueba_niebla_partida.py:test_ac001_003_005_proyeccion_no_revela_ni_observa |
| 004 | 003/004 | T003–008 | modelo/conocimiento.py, modelo/motor_eventos.py | prueba_conocimiento.py:test_ac004_005_memoria_compartida_y_cierre_remoto; prueba_niebla_partida.py:test_ac002_004_observacion_dentro_de_accion_y_ambos_extremos |
| 005 | 003/004/015 | T005–008 | controlador/partida.py, vista/vista_consola.py | prueba_niebla_partida.py:test_ac001_003_005_proyeccion_no_revela_ni_observa; prueba_niebla_partida.py:test_ver_mapa_y_parser_preservan_nombre |
| 006 | 001/003/006 | T009–010 | modelo/conocimiento.py | prueba_conocimiento.py:test_ac006_007_008_019_antorcha_no_recursiva_y_retroceso |
| 007 | 006/007 | T009–010 | modelo/motor_eventos.py | prueba_niebla_partida.py:test_ac006_007_antorcha_no_carga_ni_activa |
| 008 | 001/006 | T009–010 | modelo/conocimiento.py | prueba_conocimiento.py:test_ac006_007_008_019_antorcha_no_recursiva_y_retroceso; prueba_conocimiento.py:test_ac001_002_003_inicio_y_precarga_no_revelan |
| 009 | 008 | T014–015 | modelo/conocimiento.py, controlador/comandos.py | prueba_conocimiento.py:test_ac009_nombre_exacto_duplicados_y_ocultos; prueba_niebla_partida.py:test_ac009_012_017_viaje_y_destino_actual_sin_accion |
| 010 | 005/009/010 | T011–013 | modelo/rutas.py | prueba_rutas_conocidas.py:test_ac010_011_ponderacion_y_mejora_de_primer_salto |
| 011 | 010 | T011–013 | modelo/rutas.py, modelo/heap_rutas.py | prueba_rutas_conocidas.py:test_ac010_011_ponderacion_y_mejora_de_primer_salto |
| 012 | 011/012 | T011–016 | controlador/partida.py, modelo/conocimiento.py | prueba_niebla_partida.py:test_ac009_012_017_viaje_y_destino_actual_sin_accion; prueba_rutas_conocidas.py:test_ac009_012_generaciones_y_salas_no_exploradas |
| 013 | 003/009/012/013 | T011–016 | modelo/motor_eventos.py, controlador/partida.py | prueba_niebla_partida.py:test_ac013_016_no_abre_puertas_y_recalcula |
| 014 | 007/011/013 | T014–016 | modelo/motor_eventos.py, controlador/partida.py | prueba_niebla_partida.py:test_ac014_015_enemigos_al_entrar_y_dano_aunque_cure; prueba_niebla_partida.py:test_ac014_enemigo_presente_al_entrar_aunque_despues_salga |
| 015 | 011/013 | T014–016 | modelo/motor_eventos.py | prueba_niebla_partida.py:test_ac014_015_enemigos_al_entrar_y_dano_aunque_cure |
| 016 | 009/013 | T014–016 | controlador/partida.py | prueba_niebla_partida.py:test_ac013_016_no_abre_puertas_y_recalcula |
| 017 | 005/013 | T014–016 | controlador/partida.py | prueba_niebla_partida.py:test_ac009_012_017_viaje_y_destino_actual_sin_accion |
| 018 | 014/015 | T017–018 | controlador/controlador.py, adaptadores/bitacora_partida.py | prueba_bitacora_partida.py:test_ac018_022_viaje_registrado_equivale_a_movimientos_y_replay |
| 019 | 016 | T019–020 | modelo/conocimiento.py, modelo/retroceso.py | prueba_niebla_partida.py:test_ac019_020_interrumpir_retrocede_ultimo_paso_y_no_continua; prueba_conocimiento.py:test_ac006_007_008_019_antorcha_no_recursiva_y_retroceso |
| 020 | 011/016 | T019–020 | controlador/controlador.py, controlador/partida.py | prueba_niebla_partida.py:test_ac019_020_interrumpir_retrocede_ultimo_paso_y_no_continua |
| 021 | 003/017 | T021–023 | adaptadores/estado_binario.py, controlador/cargar_partida.py | prueba_niebla_partida.py:test_ac018_021_022_guardado_y_retroceso_restauran_memoria; prueba_estado_binario.py:test_guardado_de_modelo_anterior_se_rechaza |
| 022 | 014/015/017 | T018, T021–023 | adaptadores/bitacora_partida.py, adaptadores/estado_binario.py | prueba_bitacora_partida.py:test_ac018_022_viaje_registrado_equivale_a_movimientos_y_replay; prueba_bitacora_partida.py:test_ac017_replay_terreno_cazador_sin_instanciar_vista |

PR-NV-001/002/003: T024–026 y prueba_bench_adaptadores.py:test_bench_niebla_verifica_regiones_e_indices.
Evidencia: [pruebas](../../documentacion/evidencia/pruebas_niebla.txt),
[medición final](../../documentacion/evidencia/mediciones_niebla.json),
[primera corrida](../../documentacion/evidencia/mediciones_niebla_inicial.json) y
[salidas completas](../../documentacion/evidencia/bench_niebla.txt).
492 pruebas aprobadas; 3 000 rutas de referencia, máximo 2,1130 ms.
La corrida sintética tuvo un ciclo ≥20 ms; límites descritos en el Documento de
Decisiones. Resolubilidad y línea de tiempo siguen fuera de esta capacidad.
