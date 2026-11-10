# Tareas: Línea de tiempo y puntos de control

**Fecha**: 2026-11-09. **Estado**: 23/37 tareas ejecutadas (fases 1 a 6). T018 y T020 no requirieron cambios de código: la interrupción existente y el diseño de D-LT-05 ya cubrían los casos.
**Entrada**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [contrato](contracts/linea-tiempo.md) y
[quickstart.md](quickstart.md). Rama real: `main`.

D-LT-01 a D-LT-06 están aprobadas: reconstrucción hacia adelante; puntos en un
arreglo creciente con búsqueda binaria propia; arreglo de órdenes ejecutadas y
arreglo de acciones vigentes por k; copiador de grafo propio con tabla de
identidades propia; persistencia de todos los puntos en el formato 6. No elegir
otras estructuras. Prohibidos para estos problemas: `dict`/`set` como índice,
`bisect`, `heapq`, `collections`, `copy.deepcopy` y bibliotecas de grafos.
D-LT-07 (K por defecto) la decide el usuario en T034 con las mediciones de T032.
Mientras tanto se usa la constante provisional `K_POR_DEFECTO = 25`, marcada como
pendiente de decisión.

Formato: `- [ ] Tnnn [P opcional] [USn en historias] acción, archivos, dependencias y requisitos`.
[P] indica que la tarea puede hacerse en archivos distintos una vez completas sus
dependencias. Las pruebas son obligatorias por SC-LT-001 y la constitución VIII:
escribirlas antes del comportamiento, comprobar que fallan sin él y citar los
FR/AC en cada prueba. No marcar una tarea solo por crear archivos.

## Fase 1 — Preparación compartida

Objetivo: partidas sintéticas reproducibles para comparar el estado en vivo con
el reconstruido, sin red ni datos oficiales en el código de la aplicación.

- [X] T001 Crear en Pruebas/datos_linea_tiempo.py constructores de partidas sintéticas deterministas (semilla, salas con salidas y costos, guardián, errante, cazador, trampa, veneno, antorcha, pergaminos en suelo e inventario) y un ejecutor que aplica una lista de órdenes por `ejecutar_accion_replay` y captura un «resumen en vivo» antes de cada decisión y en instantes intermedios elegidos. Sin red; preparar_sala local. Dep.: ninguna. Requisitos: FR-LT-002, FR-LT-003, FR-LT-014; SC-LT-001, SC-LT-002.

## Fase 2 — Fundamentos (bloquean todas las historias)

Objetivo: copiar el estado, registrar órdenes y re-simular en una copia, sin
cambiar todavía la interfaz.

- [X] T002 [P] Escribir en Pruebas/prueba_copia_estado.py pruebas de la tabla de identidades (claves ausentes, crecimiento al superar 70 %, capacidad potencia de dos, colisiones) y del copiador: la copia no comparte objetos mutables con el original, conserva referencias compartidas y ciclos (anillo de 1 000 salas sin `RecursionError`), copia `random.Random` por estado, excluye enlaces (preparar_sala, fuente, gestor) e índices derivados, y mutar la copia no altera el original. Dep.: T001. Requisitos: FR-LT-013, FR-LT-014. Escenarios: AC-LT-019, AC-LT-021.
- [X] T003 Implementar en adaptadores/copia_estado.py (junto al esquema, para que el modelo no dependa de adaptadores; analyze C1) la tabla de identidades «Direccionamiento abierto propio; clave = identidad del objeto original, valor = copia; capacidad potencia de dos con crecimiento al 70 %» y el copiador iterativo con pila propia que recorre los campos obligatorios y opcionales del esquema explícito de adaptadores/estado_binario.py (exponer una función de lectura del esquema sin duplicarlo y sin importaciones circulares), comparte inmutables, reconstruye tuplas, copia `dict` de fichas/contenido como datos y `random.Random` con getstate/setstate. Tras copiar, reconstruir los auxiliares igual que la carga (p. ej. `conocimiento.reconstruir()`). Hacer pasar T002. Dep.: T002. Requisitos: FR-LT-013, FR-LT-014; PR-LT-003.
- [X] T004 [P] Escribir en Pruebas/prueba_linea_tiempo.py pruebas de la estructura sin partida: agregar órdenes de tipo acción/pergamino/navegación; acciones vigentes con «Instantes estrictamente crecientes»; recorte por pergamino en O(revertidas) sin tocar las órdenes; el pergamino no suma al tramo y las acciones luego revertidas sí (FR-LT-013, aclaración); búsqueda binaria t → k y de puntos por posición (primero, último, entre puntos, exactos); «Dos puntos consecutivos están separados por exactamente K acciones ejecutadas del tramo»; los puntos nunca se borran; tramos con K distinto. Dep.: T001. Requisitos: FR-LT-004, FR-LT-008, FR-LT-012, FR-LT-013; PR-LT-002, PR-LT-004. Escenarios: AC-LT-012, AC-LT-013, AC-LT-019, AC-LT-020.
- [X] T005 Implementar en modelo/linea_tiempo.py los registros Orden ejecutada, Acción vigente, Punto de control y Tramo de K, y la clase de la línea con los tres arreglos, el contador del tramo, el instante pendiente, la búsqueda binaria propia (sin `bisect`), el recorte y el cálculo del objetivo de consulta (`#k` → posición exclusiva; t → última acción con instante ≤ t, exclusiva si coincide e inclusiva con límite t si no). Solo las órdenes de tipo acción suman al tramo; el pergamino no. Recibir la función de copia por parámetro: modelo/linea_tiempo.py no importa adaptadores. Hacer pasar T004. Dep.: T003, T004. Requisitos: FR-LT-003, FR-LT-004, FR-LT-008, FR-LT-012, FR-LT-013; PR-LT-002, PR-LT-003, PR-LT-004.
- [X] T006 [P] Escribir en Pruebas/prueba_motor_retroceso.py (o un archivo nuevo Pruebas/prueba_limite_tiempo.py) pruebas del límite de tiempo del motor: sin límite el comportamiento es idéntico al actual; con límite t se ejecutan todos los eventos ≤ t (varios en el mismo t), ninguno > t, el reloj queda en t y la acción pendiente del jugador no se ejecuta. Dep.: T001. Requisitos: FR-LT-003. Escenarios: AC-LT-004, AC-LT-005.
- [X] T007 Implementar en modelo/motor_eventos.py el atributo opcional de límite de tiempo (inactivo por defecto, no persistido) respetado por `avanzar_hasta_jugador` y por el avance de eventos, que marca si el límite se alcanzó. Verificar con T006 y con la regresión completa que la partida real no cambia. Dep.: T006. Requisitos: FR-LT-003; PR-LT-007.
- [X] T008 Implementar en controlador/cargar_partida.py un preparador de salas de solo lectura para copias: construye el contenido desde el contenido ya descargado del servicio y las fichas de la caché/disco, sin solicitudes, sin precarga y sin insertar ni desalojar en la caché viva; y un gestor de guardado inerte para `preparar_retroceso`/`preparar_botin`. Si falta un dato, lanza un error de reconstrucción con mensaje. Añadir pruebas en Pruebas/prueba_historia_partida.py con una fuente que falla ante cualquier solicitud. Dep.: T003. Requisitos: FR-LT-006, FR-LT-013; constitución V.
- [X] T009 Integrar en controlador/partida.py la línea por partida: crearla al iniciar con el punto 0 en el instante 0; exponer `registrar_orden(texto)`, que clasifica comparando `acciones_ejecutadas` antes y después (+1 acción, −1 pergamino, 0 navegación), actualiza el instante pendiente y crea un punto cuando el tramo llega a K. Exponer la re-simulación: copia de trabajo del punto, enlace al preparador y al gestor de T008, re-ejecución de las órdenes con `ejecutar_accion_replay` y límite de tiempo en la última acción si corresponde. Dep.: T005, T007, T008. Requisitos: FR-LT-001, FR-LT-003, FR-LT-008, FR-LT-013, FR-LT-014.
- [X] T010 Conectar el registro en controlador/controlador.py: llamar a `partida.registrar_orden` donde hoy se llama a `_registrar` para órdenes aceptadas (incluidos los pasos de «ir a» y la navegación sig/ant), y no para comentarios `#`, consultas, guardar ni cargar, haya o no bitácora. Pruebas en Pruebas/prueba_controlador.py. Dep.: T009. Requisitos: FR-LT-006, FR-LT-013.
- [X] T011 Escribir y pasar en Pruebas/prueba_historia_partida.py la prueba central de equivalencia del modelo: para partidas de T001 con K = 1, 3 y 10, el estado re-simulado en cada decisión y en instantes intermedios coincide con el resumen en vivo (reloj, sala, vida, estadísticas, inventario y cursor, efectos, enemigos, mapa conocido). Dep.: T009, T010. Requisitos: FR-LT-003, FR-LT-013, FR-LT-014; SC-LT-002. Escenarios: AC-LT-001, AC-LT-003, AC-LT-004, AC-LT-005, AC-LT-021.

**Punto de control**: con T011 aprobada, la reconstrucción es correcta antes de
exponerla al jugador.

## Fase 3 — US1: Consultar un instante pasado (P1, MVP)

Objetivo: `historia <t>` e `historia #k` en la consola con el resumen completo.
Prueba independiente: jugar una secuencia conocida, consultar y comparar con el
estado capturado en vivo.

- [X] T012 [P] [US1] Escribir en Pruebas/prueba_comandos.py el análisis de `historia <t>` e `historia #k` (mayúsculas indistintas; enteros base 10 sin `+`; `historia` sin argumento, t negativo, `#0`, `#` sin número y texto no numérico devuelven un comando de error de uso). Dep.: T011. Requisitos: FR-LT-001, FR-LT-007. Escenarios: AC-LT-009.
- [X] T013 [US1] Implementar en controlador/comandos.py el comando `historia` según el contrato, sin afectar `ir`, `ver mapa` ni los comandos existentes. Hacer pasar T012. Dep.: T012. Requisitos: FR-LT-001, FR-LT-007.
- [X] T014 [US1] Implementar en controlador/partida.py `historia(argumento)` y el resumen histórico: «reloj; sala (ID y nombre); vida/máxima, ataque y defensa; inventario en orden real con equipados y cursor; efectos activos; enemigos vivos de la sala con vida/máxima, dormido o activo y marca de cazador; mapa conocido», derivado solo de la copia. t = reloj actual y k = N + 1 usan el estado actual sin copiar; t > reloj se rechaza. Dep.: T011, T013. Requisitos: FR-LT-001, FR-LT-002, FR-LT-003, FR-LT-004, FR-LT-005, FR-LT-007. Escenarios: AC-LT-001, AC-LT-002, AC-LT-003, AC-LT-006, AC-LT-008.
- [X] T015 [US1] Presentar el resumen en vista/vista_consola.py con el formato del contrato (reutilizar la presentación de `ver mapa`) y enrutar la consulta en controlador/controlador.py como consulta sin registro; añadir `historia` a la ayuda. Dep.: T014. Requisitos: FR-LT-001, FR-LT-002.
- [X] T016 [US1] Escribir y pasar en Pruebas/prueba_historia_partida.py la aceptación de US1 por controlador: AC-LT-001 a 006, incluidos `historia 0`, `historia #1`, una partida sin acciones (rechaza `#2`), el mapa conocido de entonces con memoria de puertas distinta del estado real y la sala inicial explorada en el instante 0. Dep.: T015. Requisitos: FR-LT-001 a FR-LT-005. Escenarios: AC-LT-001, AC-LT-002, AC-LT-003, AC-LT-004, AC-LT-005, AC-LT-006.

## Fase 4 — US2: Consultar sin alterar nada (P1)

Objetivo: demostrar que las consultas no dejan rastro.
Prueba independiente: comparar reloj, estado, historial de retroceso, log y azar
antes y después de consultas repetidas.

- [X] T017 [US2] Escribir y pasar en Pruebas/prueba_historia_partida.py: tras varias consultas válidas y rechazadas, reloj, `motor.azar.getstate()`, historial de retroceso, línea de tiempo, contenido de `partida.log` (no contiene `historia`), caché de fichas y contador de solicitudes son idénticos, y la continuación es igual a una ejecución sin consultas. Dep.: T016. Requisitos: FR-LT-006, FR-LT-007; SC-LT-003. Escenarios: AC-LT-007, AC-LT-008, AC-LT-009.
- [X] T018 [US2] Verificar en controlador/controlador.py y en Pruebas/prueba_niebla_partida.py que escribir `historia` durante «ir a» detiene el viaje como cualquier orden, la consulta no consume tiempo y el viaje no se reanuda solo; corregir la interrupción si hace falta. Dep.: T017. Requisitos: FR-LT-006. Escenarios: AC-LT-010.

## Fase 5 — US3: Coherencia con el pergamino (P1)

Objetivo: la línea describe la historia vigente tras los pergaminos.
Prueba independiente: consultar, retroceder y repetir consultas.

- [X] T019 [US3] Escribir en Pruebas/prueba_historia_partida.py: tras un pergamino, consultar un instante posterior al reloj restaurado se rechaza; las acciones nuevas toman los números k siguientes; el pergamino no ocupa un k; los efectos que no se deshacen (pergamino consumido, pergamino recogido en la acción revertida) aparecen en los instantes vigentes posteriores y no en los anteriores; dos pergaminos seguidos; un punto creado justo antes del pergamino. Comparar con el resumen en vivo. Dep.: T016. Requisitos: FR-LT-004, FR-LT-007, FR-LT-008, FR-LT-009, FR-LT-014. Escenarios: AC-LT-011, AC-LT-012, AC-LT-014.
- [X] T020 [US3] Corregir en modelo/linea_tiempo.py y controlador/partida.py lo que T019 detecte, manteniendo «Los puntos nunca se invalidan» y el recorte en O(acciones revertidas). Añadir una prueba con contador de trabajo que muestre que el recorte no depende de la longitud de la historia. Dep.: T019. Requisitos: FR-LT-008, FR-LT-009; PR-LT-004. Escenarios: AC-LT-011, AC-LT-012, AC-LT-013, AC-LT-014.

## Fase 6 — US4: Reproducir hasta un instante (P1)

Objetivo: `--replay LOG --hasta T` imprime el mismo resumen sin vista.
Prueba independiente: grabar, reproducir con varios T y comparar con `historia`.

- [X] T021 [P] [US4] Escribir en Pruebas/prueba_bitacora_partida.py y Pruebas/prueba_partida.py: el resumen de `--hasta T` es idéntico al de `historia T` en la partida original (también con pergaminos en el log); T posterior al final muestra el estado final y «la partida terminó en t=R, antes de T» o «el registro termina en t=R»; no se instancia la vista; `--hasta` sin `--replay` y T inválido son errores de uso de argparse (código 2). Dep.: T016. Requisitos: FR-LT-008, FR-LT-010, FR-LT-011. Escenarios: AC-LT-015, AC-LT-016, AC-LT-017, AC-LT-018.
- [X] T022 [US4] Hacer que adaptadores/bitacora_partida.py registre cada orden reproducida en la línea de la partida (mismo `registrar_orden`, ignorando comentarios) sin cambiar su contrato de errores. Dep.: T021, T009. Requisitos: FR-LT-010, FR-LT-014.
- [X] T023 [US4] Implementar en main.py `--hasta T` (solo con `--replay`, T entero ≥ 0) que, tras el replay completo, imprime el resumen de T con la misma rutina que `historia` y el aviso de fin anticipado, sin instanciar la vista; validar combinaciones con `parser.error`. Hacer pasar T021. Dep.: T022, T014. Requisitos: FR-LT-010, FR-LT-011. Escenarios: AC-LT-015, AC-LT-016, AC-LT-017, AC-LT-018.

## Fase 7 — US5: Configurar los puntos de control (P2)

Objetivo: `--checkpoint-cada K` controla la frecuencia sin cambiar resultados.
Prueba independiente: misma partida con varios K.

- [ ] T024 [P] [US5] Escribir en Pruebas/prueba_historia_partida.py y Pruebas/prueba_partida.py: con K = 1, 2, 5 y 25 nunca hay más de un punto cada K acciones ejecutadas, ninguna consulta re-simula más de K acciones (contador instrumentado), los resúmenes son idénticos entre K y K no entero, cero o negativo es error de uso. Dep.: T016. Requisitos: FR-LT-012, FR-LT-013, FR-LT-014; PR-LT-002. Escenarios: AC-LT-019, AC-LT-020, AC-LT-021, AC-LT-022.
- [ ] T025 [US5] Implementar en main.py `--checkpoint-cada K` (entero ≥ 1, válido con `--cripta`, `--cargar` y `--replay`) y pasarlo a la línea de la partida en controlador/cargar_partida.py; sin la opción usar `K_POR_DEFECTO` de modelo/linea_tiempo.py. Hacer pasar T024. Dep.: T024. Requisitos: FR-LT-012, FR-LT-013. Escenarios: AC-LT-019, AC-LT-022.

## Fase 8 — US6: Guardar y cargar con historia (P1)

Objetivo: persistir la línea completa y rechazar formatos anteriores.
Prueba independiente: guardar, cargar en otra ejecución y comparar consultas.

- [ ] T026 [P] [US6] Escribir en Pruebas/prueba_estado_binario.py: guardar y cargar conserva órdenes, acciones, tramos y puntos; `historia` da los mismos resúmenes antes y después para todos los instantes desde 0; la línea sigue registrando; cargar con otro `--checkpoint-cada` empieza un tramo nuevo sin alterar los puntos previos, y sin la opción conserva el K guardado; un archivo de versión 5 o de la primera parte se rechaza con «formato de guardado incompatible (versión X; se requiere 6)» sin cargar nada. Dep.: T016, T025. Requisitos: FR-LT-015, FR-LT-016. Escenarios: AC-LT-023, AC-LT-024, AC-LT-025.
- [ ] T027 [US6] Ampliar en adaptadores/estado_binario.py el esquema a la versión 6 con los registros de la línea (orden, acción vigente, punto, tramo, línea) y la copia de cada punto como raíz adicional; actualizar `VERSION_MODELO`, la validación del modelo y el mensaje de rechazo. Dep.: T026. Requisitos: FR-LT-015, FR-LT-016.
- [ ] T028 [US6] Conectar la persistencia en controlador/cargar_partida.py (`guardar_sesion`, `leer_sesion`, `aplicar_sesion`, `reanudar`) incluyendo la línea en la sesión, el nuevo tramo si cambia K y el reenlace de los puntos cargados. Hacer pasar T026 y la regresión de guardado. Dep.: T027. Requisitos: FR-LT-015, FR-LT-016. Escenarios: AC-LT-023, AC-LT-024, AC-LT-025.

## Fase 9 — Mediciones, decisión de K y cierre

Objetivo: evidencia de §5.5, §5.6, §6.1 y §6.3, el K por defecto elegido por el
usuario y la documentación y trazabilidad finales.

- [ ] T029 [P] Crear en modelo/bench_linea_tiempo.py una partida sintética determinista de ≥ 5 000 acciones (con y sin decenas de cazadores, con pergaminos) y medir, para K = 10, 25, 50 y 100 y la alternativa sin puntos: memoria total (tracemalloc), tiempo de consulta (mínimo, mediana, p95, máximo) sobre instantes repartidos, costo de crear un punto y ciclo máximo con registro activo. Medir también, por K, el tamaño del archivo de guardado y el tiempo de guardar y cargar con todos los puntos (riesgo de D-LT-06; analyze G1), para informarlo como límite conocido. Dep.: T028. Requisitos: PR-LT-001, PR-LT-003, PR-LT-005, PR-LT-007; FR-LT-015.
- [ ] T030 [P] Añadir a modelo/bench_linea_tiempo.py las comparaciones adelante frente a atrás (costo por acción re-simulada frente a deshecha y memoria de deltas registrados) y copiador propio frente al serializador binario, con las cargas de research.md. Dep.: T028. Requisitos: PR-LT-006; D-LT-01, D-LT-04.
- [ ] T031 Repetir en el bench existente (modelo/bench_modelo.py, adaptadores/bench_adaptadores.py) las mediciones de agenda de eventos e historial de retroceso de P1 con la carga nueva (cazadores, costos variables y registro de la línea) y comparar con la evidencia de P1. Dep.: T028. Requisitos: PR-LT-007; §5.6.
- [ ] T032 Integrar T029–T031 en `python main.py --bench` (sin vista) y guardar las salidas en documentacion/evidencia/bench_linea_tiempo.txt y documentacion/evidencia/mediciones_linea_tiempo.json, con entorno, semilla y repeticiones. Dep.: T029, T030, T031. Requisitos: PR-LT-001 a PR-LT-007; SC-LT-004, SC-LT-005.
- [ ] T033 Ejecutar la consulta con el K provisional en la cripta de referencia o en la mayor disponible, con ≥ 5 000 acciones, y registrar si el 100 % de las consultas termina en < 50 ms. Para obtener esas acciones, reutilizar la estrategia de `medir_cripta_cargada` (modelo/bench_modelo.py): datos precargados sin red dentro del cronómetro, un jugador con vida suficiente que alterna esperar y moverse por salidas abiertas sin entrar a la sala de salida, y cazadores activos con sus estadísticas originales como carga experimental declarada; si la partida termina antes, informarlo con la cantidad alcanzada. Si no se cumple, informarlo sin ocultarlo. Dep.: T032. Requisitos: PR-LT-001; SC-LT-004.
- [ ] T034 Presentar al usuario la tabla de T032/T033 (memoria, consulta y creación de punto por K) con una recomendación justificada, y esperar su elección del K por defecto (D-LT-07). Fijarlo en modelo/linea_tiempo.py y registrar la decisión en research.md. Dep.: T033. Requisitos: FR-LT-012; PR-LT-005.
- [ ] T035 Actualizar documentacion/DOCUMENTO_DECISIONES.md con la sección de §5.5 (problema, alternativas, decisión, complejidad, evidencia y límites; enlaces a spec.md y plan.md; diferencias respecto del plan y la medición que las motivó) y la de §5.6 (antes y después, o la evidencia de que las decisiones de P1 siguen siendo adecuadas). Dep.: T034. Requisitos: PR-LT-005, PR-LT-006, PR-LT-007; P2 §7.1.
- [ ] T036 Actualizar README.md (comandos `historia`, `--checkpoint-cada`, `--replay … --hasta`, K por defecto, formato 6, cómo ejecutar las pruebas de aceptación de la línea de tiempo) y registrar las entradas en documentacion/PROMPTS_LLM.md. Dep.: T034. Requisitos: P2 §2.6, §7.2.
- [ ] T037 Ejecutar `python -m pytest -q` completo y guardar la salida en documentacion/evidencia/pruebas_linea_tiempo.txt; completar en este archivo la matriz requisito → escenario → tarea → código → prueba para FR-LT-001 a 016 y PR-LT-001 a 007; marcar el estado de spec.md como implementado. Dep.: T035, T036. Requisitos: SC-LT-001 a SC-LT-005; constitución VIII.

## Dependencias y orden

```text
T001 ─┬─ T002 → T003 ─┬─ T005 ─┐
      ├─ T004 ────────┘        ├─ T009 → T010 → T011 ─┐
      └─ T006 → T007 ──────────┤                      │
             T003 → T008 ──────┘                      │
                                                      ▼
US1: T012 → T013 → T014 → T015 → T016 ─┬─ US2: T017 → T018
                                       ├─ US3: T019 → T020
                                       ├─ US4: T021 → T022 → T023
                                       └─ US5: T024 → T025 → US6: T026 → T027 → T028
Cierre: T028 → T029, T030, T031 → T032 → T033 → T034 → T035, T036 → T037
```

- Las fases 1 y 2 bloquean todas las historias. US1 es el MVP y bloquea las demás
  porque aporta la consulta y el resumen.
- US2, US3, US4 y US5 son independientes entre sí una vez terminada US1.
- US6 depende de US5 porque persiste los tramos de K.
- El cierre requiere todas las historias. T034 requiere la elección del usuario.

## Oportunidades de trabajo en paralelo

- **Fase 2**: T002, T004 y T006 (pruebas en archivos distintos) después de T001.
- **Tras US1**: US2 (controlador/vista), US3 (línea), US4 (bitácora/main) y US5
  (main/cargador) tocan archivos mayormente distintos. Coordinar main.py entre
  T023 y T025.
- **Mediciones**: T029, T030 y T031.

## Estrategia de implementación

1. **MVP**: fases 1–3 (T001–T016). Con ellas `historia` funciona y la equivalencia
   está verificada.
2. **Incremento**: US2 y US3 (garantías de no alteración y pergamino) y luego US4
   (replay).
3. **Configuración y persistencia**: US5 y US6.
4. **Cierre**: mediciones, decisión del K por el usuario, documentación y
   trazabilidad.

Confirmar cada fase en Git por separado. Si durante la implementación la
especificación resulta incorrecta, corregir y confirmar primero spec.md y después
el código (P2 §2.6).
