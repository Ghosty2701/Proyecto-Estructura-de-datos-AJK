# Tareas: Línea de tiempo y puntos de control

## Cierre de entrega priorizado (2026-11-13)

- [X] ENT-009 Evaluar y descartar mantenimiento GC después de punto en siguiente acción
  sin punto, dentro de registro/cronometrado y respetando GC deshabilitado por
  el llamador. No cambiar umbrales/estado del juego/persistencia. Validar costo
  completo, K1, undo/navegación y ciclos oficiales K10. PR-LT-007/PR-TC-001.
  Tres pruebas dirigidas pasan, pero 53/5 000 ciclos oficiales exceden 20 ms;
  sin mejora. Código y pruebas específicos retirados; GC productivo sin cambios.
  Evidencia: `validacion_k10_gc_descartado.json`. No cierra el presupuesto.

- [X] ENT-008 Codificar tuplas escalares planas en el campo con marca inequívoca,
  manteniendo IDs para tuplas con descendientes y lectura de puntos previos.
  Misma estructura/codec v6; verificar tipos, alias, ciclos, todos los puntos
  en v6, memoria y ciclo oficial completo. FR-LT-013/014/015, PR-LT-003/007.
  759 pruebas; ABBA K10: 501 puntos por historia, cuatro historias y mismos
  bytes v6. Medianas de captura: control 13,754/13,403 ms, actual 13,316/11,827;
  ciclos lentos 27/24 frente a 18/9. Mejora parcial, sin aceptación de 20 ms.

- [X] ENT-005 Evaluar y descartar eliminación de tuplas auxiliares de pendientes en el capturador de
  producción reutilizando sus arreglos; verificar originales no retenidos,
  estado/bytes idénticos, regresión y ciclos completos K10 con GC habilitado.
  PR-LT-007, FR-LT-013/014/015. Referencia previa de producción: `4d61ebd`.
  Ensayo terminado sin ventaja en picos; código descartado. No marca cumplido 20 ms.
- [X] ENT-006 Evitar recodificar el contenido de tuplas de escalares exactos,
  conservando su registro/ID y sin compartir descendientes mutables. Validar
  tipos/bits, subclases, alias, v6, memoria y ciclos completos. FR-LT-013/014/015,
  PR-LT-003/007. Mismas estructuras y formato; sin otro prototipo de arquitectura.
  Sustituido por ENT-008: el registro individual se omite para tuplas planas.
- [X] ENT-007 Corregir medición oficial: registrar órdenes dentro del ciclo,
  punto inicial posterior a preparación, y medir ciclos en las 5 000 acciones
  oficiales ya usadas para consultas, con/sin punto. PR-LT-007/PR-TC-001.

Las tareas de investigación CI al final son históricas/experimentales y no
condiciones adicionales del enunciado. No se continuará su ampliación como
dependencia de entrega. Los únicos bloqueos funcionales/documentales pendientes
se siguen aquí y en `documentacion/REANALISIS_ENTREGA_P2.md`.

- [X] ENT-001 Corregir `main.py --bench` para incluir línea de tiempo por defecto,
  conservar alias, configurar carpeta de salida, informar fallos y entorno.
  Pruebas de CLI sin vista/red y ejecución real pequeña. PR-LT-005/008; P2 §6.3.
- [X] ENT-002 Incorporar entradas raíz DECISIONES.md/PROMPTS_LLM.md, corregir
  README/estado actual y distinguir cifras vigentes de históricas. P2 §7.1/7.2.
- [X] ENT-003 Reconciliar los 23 casos del apéndice B con especificaciones,
  tareas, código y funciones de prueba, y verificar regresión. P2 §2.5/7.4.
- [X] ENT-004 Cierre funcional con EX-01: K elegido y presupuestos medidos;
  límites incumplidos exceptuados del alcance solicitado por el usuario.
  Texto original: cerrar K por elección del usuario y validar presupuestos sobre
  producción. No activar ni medir más prototipos rechazados. FR-LT-012,
  PR-LT-001/007, PR-TC-001. Dep.: evidencia de producción y decisión de K.
  - [X] K=10 elegido y aplicado; sin alterar K guardado al cargar sin opción.
  - [X] 5 000 acciones oficiales, 36 consultas, máximo 31,9232 ms, cero excedidos.
  - [ ] Ciclo <20 ms: incumplido, omitida su optimización por EX-01.
    Corrida nueva: 255/5 000 excedidos, máximo 92,0115 ms; consultas: 2/36 ≥50 ms.
    Las cifras anteriores de esta sección son históricas. No se marca satisfecho.
  - [X] EX-01 Registrar la excepción autorizada, verificar producción y cerrar
    optimizaciones sin mejora: documentacion/REVISION_SESION_BLOQUEADA.md.

**Traslado al repositorio original:** el trabajo posterior a T028 se realizó
en una copia descargada sin `.git` y se trasladó sobre la base `4c34c88` del
repositorio original. Las referencias históricas a ausencia de Git describen
esa copia; no describen el repositorio actual. Los commits del traslado son
nuevos y no reconstruyen el historial perdido de la copia.

**Revisión**: 2026-11-13. **Estado**: T001–T036 ejecutadas; T037 cerrada
funcional y documentalmente con EX-01. Regresión nueva: 759 pruebas pasan;
K=10 elegido. Los presupuestos 20/50 ms no cumplen en la corrida nueva.
T018/T020 ya estaban cubiertas por el comportamiento existente.
**Entrada**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [contrato](contracts/linea-tiempo.md) y
[quickstart.md](quickstart.md). Rama real: `main`.

D-LT-01 a D-LT-06 están aprobadas: reconstrucción hacia adelante; puntos en un
arreglo creciente con búsqueda binaria propia; arreglo de órdenes ejecutadas y
arreglo de acciones vigentes por k; copiador de grafo propio con tabla de
identidades propia; persistencia de todos los puntos en el formato 6. No elegir
otras estructuras. Prohibidos para estos problemas: `dict`/`set` como índice,
`bisect`, `heapq`, `collections`, `copy.deepcopy` y bibliotecas de grafos.
D-LT-07 cerrada: Juan eligió `K_POR_DEFECTO = 10` con las comparaciones de
consultas/memoria; decisión y límites en research.md. Las menciones posteriores
a 25 provisional pertenecen al registro histórico de las etapas anteriores.

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

- [X] T024 [P] [US5] Escribir en Pruebas/prueba_historia_partida.py y Pruebas/prueba_partida.py: con K = 1, 2, 5 y 25 nunca hay más de un punto cada K acciones ejecutadas, ninguna consulta re-simula más de K acciones (contador instrumentado), los resúmenes son idénticos entre K y K no entero, cero o negativo es error de uso. Dep.: T016. Requisitos: FR-LT-012, FR-LT-013, FR-LT-014; PR-LT-002. Escenarios: AC-LT-019, AC-LT-020, AC-LT-021, AC-LT-022.
- [X] T025 [US5] Implementar en main.py `--checkpoint-cada K` (entero ≥ 1, válido con `--cripta`, `--cargar` y `--replay`) y pasarlo a la línea de la partida en controlador/cargar_partida.py; sin la opción usar `K_POR_DEFECTO` de modelo/linea_tiempo.py. Hacer pasar T024. Dep.: T024. Requisitos: FR-LT-012, FR-LT-013. Escenarios: AC-LT-019, AC-LT-022.

## Fase 8 — US6: Guardar y cargar con historia (P1)

Objetivo: persistir la línea completa y rechazar formatos anteriores.
Prueba independiente: guardar, cargar en otra ejecución y comparar consultas.

- [X] T026 [P] [US6] Escribir en Pruebas/prueba_estado_binario.py: guardar y cargar conserva órdenes, acciones, tramos y puntos; `historia` da los mismos resúmenes antes y después para todos los instantes desde 0; la línea sigue registrando; cargar con otro `--checkpoint-cada` empieza un tramo nuevo sin alterar los puntos previos, y sin la opción conserva el K guardado; un archivo de versión 5 o de la primera parte se rechaza con «formato de guardado incompatible (versión X; se requiere 6)» sin cargar nada. Dep.: T016, T025. Requisitos: FR-LT-015, FR-LT-016. Escenarios: AC-LT-023, AC-LT-024, AC-LT-025.
- [X] T027 [US6] Ampliar en adaptadores/estado_binario.py el esquema a la versión 6 con los registros de la línea (orden, acción vigente, punto, tramo, línea) y la copia de cada punto como raíz adicional; actualizar `VERSION_MODELO`, la validación del modelo y el mensaje de rechazo. Dep.: T026. Requisitos: FR-LT-015, FR-LT-016.
- [X] T028 [US6] Conectar la persistencia en controlador/cargar_partida.py (`guardar_sesion`, `leer_sesion`, `aplicar_sesion`, `reanudar`) incluyendo la línea en la sesión, el nuevo tramo si cambia K y el reenlace de los puntos cargados. Hacer pasar T026 y la regresión de guardado. Dep.: T027. Requisitos: FR-LT-015, FR-LT-016. Escenarios: AC-LT-023, AC-LT-024, AC-LT-025.

## Fase 9 — Mediciones, decisión de K y cierre

Objetivo: evidencia de §5.5, §5.6, §6.1 y §6.3, el K por defecto elegido por el
usuario y la documentación y trazabilidad finales.

- [X] T029 [P] Crear en modelo/bench_linea_tiempo.py una partida sintética determinista de ≥ 5 000 acciones (con y sin decenas de cazadores, con pergaminos) y medir, para K = 10, 25, 50 y 100 y la alternativa sin puntos: memoria total (tracemalloc), tiempo de consulta (mínimo, mediana, p95, máximo) sobre instantes repartidos, costo de crear un punto y ciclo máximo con registro activo. Medir también, por K, el tamaño del archivo de guardado y el tiempo de guardar y cargar con todos los puntos (riesgo de D-LT-06; analyze G1), para informarlo como límite conocido. Dep.: T028. Requisitos: PR-LT-001, PR-LT-003, PR-LT-005, PR-LT-007; FR-LT-015.
- [X] T030 [P] Añadir a modelo/bench_linea_tiempo.py las comparaciones adelante frente a atrás (costo por acción re-simulada frente a deshecha y memoria de deltas registrados) y copiador propio frente al serializador binario, con las cargas de research.md. Dep.: T028. Requisitos: PR-LT-006; D-LT-01, D-LT-04.
- [X] T031 Repetir en el bench existente (modelo/bench_modelo.py, adaptadores/bench_adaptadores.py) las mediciones de agenda de eventos e historial de retroceso de P1 con la carga nueva (cazadores, costos variables y registro de la línea) y comparar con la evidencia de P1. Dep.: T028. Requisitos: PR-LT-007; §5.6.
- [X] T032 Integrar T029–T031 en `python main.py --bench` (sin vista) y guardar las salidas en documentacion/evidencia/bench_linea_tiempo.txt y documentacion/evidencia/mediciones_linea_tiempo.json, con entorno, semilla y repeticiones. Dep.: T029, T030, T031. Requisitos: PR-LT-001 a PR-LT-007; SC-LT-004, SC-LT-005.
- [X] T033 Ejecutar la consulta con el K elegido en la cripta de referencia o en la mayor disponible, con ≥ 5 000 acciones, y registrar si el 100 % de las consultas termina en < 50 ms. Para obtener esas acciones, reutilizar la estrategia de `medir_cripta_cargada` (modelo/bench_modelo.py): datos precargados sin red dentro del cronómetro, un jugador con vida suficiente que alterna esperar y moverse por salidas abiertas sin entrar a la sala de salida, y cazadores activos con sus estadísticas originales como carga experimental declarada; si la partida termina antes, informarlo con la cantidad alcanzada. Si no se cumple, informarlo sin ocultarlo. Dep.: T032. Requisitos: PR-LT-001; SC-LT-004.
- [X] T034 Presentar al usuario la tabla de T032/T033 (memoria, consulta y creación de punto por K) con una recomendación justificada, y esperar su elección del K por defecto (D-LT-07). Fijarlo en modelo/linea_tiempo.py y registrar la decisión en research.md. Dep.: T033. Requisitos: FR-LT-012; PR-LT-005.
- [X] T035 Actualizar documentacion/DOCUMENTO_DECISIONES.md con la sección de §5.5 (problema, alternativas, decisión, complejidad, evidencia y límites; enlaces a spec.md y plan.md; diferencias respecto del plan y la medición que las motivó) y la de §5.6 (antes y después, o la evidencia de que las decisiones de P1 siguen siendo adecuadas). Dep.: T034. Requisitos: PR-LT-005, PR-LT-006, PR-LT-007; P2 §7.1.
- [X] T036 Actualizar README.md (comandos `historia`, `--checkpoint-cada`, `--replay … --hasta`, K por defecto, formato 6, cómo ejecutar las pruebas de aceptación de la línea de tiempo) y registrar las entradas en documentacion/PROMPTS_LLM.md. Dep.: T034. Requisitos: P2 §2.6, §7.2.
- [X] T037 Cierre funcional/documental con EX-01; 759 pruebas pasan, matriz revisada y evidencia nueva en `documentacion/evidencia/revision_sesion_*`. No acredita los presupuestos incumplidos. La regresión completa previa a los commits está en `revision_sesion_pruebas_completas_2026-11-13.txt` (759 pruebas, 29,32 s); la primera ejecución se conserva como resumen en `revision_sesion_pruebas_2026-11-13.txt` y la salida histórica permanece en `pruebas_linea_tiempo.txt`. Texto original: ejecutar `python -m pytest -q` completo y guardar la salida en documentacion/evidencia/pruebas_linea_tiempo.txt; completar en este archivo la matriz requisito → escenario → tarea → código → prueba para FR-LT-001 a 016 y PR-LT-001 a 007; marcar el estado de spec.md como implementado. Dep.: T035, T036. Requisitos: SC-LT-001 a SC-LT-005; constitución VIII.

## Avance de Juan — persistencia y copiado (2026-11-11)

Tramo de T029/T030, reutilizando D-LT-04/06, sin una capacidad ni estructura nueva:

- `adaptadores/bench_persistencia.py`: carga offline con 5 000 acciones vigentes,
  costos variables y un pergamino; K = 10/25/50/100. Registra todas las muestras
  de guardar/cargar la sesión completa y el tamaño del archivo; compara copia
  propia con codificación/decodificación binaria del mismo estado base.
- `adaptadores/bench_adaptadores.py --solo persistencia`: ejecución optativa y
  salida JSON para reutilizar en T032. La carga se prepara fuera del cronómetro;
  la carga medida incluye validación y reenlace, sin red ni vista.
- `Pruebas/prueba_bench_persistencia.py`: equivalencia de registro, consultas,
  azar y continuación, carga idéntica entre K y rechazo de entradas inválidas.
  Incluye una carga alterada intencionalmente para comprobar que el benchmark
  detecta la pérdida del registro. Pruebas creadas antes de implementar el módulo.
- README actualizado con historia, formato 6 y opciones de replay/guardado.

Ejecución verificada: 200 salas, 5 000 acciones vigentes, semilla 2026, tres
rondas por K; sin cazadores. Archivos de 62,60/25,34/12,93/6,72 MB para
K = 10/25/50/100; carga máxima de 25,484/11,207/4,771/3,092 s. Evidencia en
[JSON](../../documentacion/evidencia/mediciones_persistencia_juan.json),
[salida](../../documentacion/evidencia/bench_persistencia_juan.txt) y
[641 pruebas aprobadas](../../documentacion/evidencia/pruebas_persistencia_juan.txt).
Resultados y límites incorporados al Documento de Decisiones; no se cambia K.

T029 y T030 permanecen abiertas: faltan memoria, creación de puntos/ciclos con
registro y comparación adelante/atrás. Las consultas se detallan a continuación.
T031–T037 también conservan
su estado: estos resultados parciales no sustituyen sus dependencias ni fijan K.
No se pueden crear commits en esta copia descargada porque no contiene `.git`.

## Avance de Juan — consultas (2026-11-11)

- T029 (tramo ejecutado): `modelo/bench_linea_tiempo.py` mide consultas completas
  en cargas sintéticas de 5 000 acciones, 200 salas, K = 10/25/50/100 y solo
  el punto inicial, con 0/32 cazadores. Tres rondas × 12 destinos por escenario;
  360 consultas. Capturas de decisiones en vivo; intermedios contrastados entre K
  y con la alternativa inicial. Todas las muestras y mínimo/mediana/p95/máximo,
  excedidos de 50 ms, cota K, búsqueda logarítmica y firma de estado intacta.
- T033 (ensayo anticipado, integración T032 pendiente): `cripta-06`, 300 salas,
  versión `f9ed9afa683d`, catálogo `4b9e75a42be5`, K provisional 25, 32 cazadores
  activados con datos originales, vida experimental del jugador 10^9. Se
  completaron 5 000 acciones y 36 consultas: 27 ≥50 ms, máximo 195,992 ms.
  No cumple PR-LT-001 en esta carga; no se modifica K ni se declara cerrada la
  aceptación. Se usaron 46/63 solicitudes al preparar, cero al consultar.
- CLI optativa: `adaptadores.bench_adaptadores --solo consultas`; `--cripta`
  selecciona datos externos y K provisional. Falta integrarlo al modo general
  `main.py --bench` junto con las mediciones restantes de T032.
- `Pruebas/prueba_bench_linea_tiempo.py` (creadas antes del módulo): PR-LT-001/002/005,
  FR-LT-003/006/013/014; equivalencia, no vista, cota K, estadísticas, CLI,
  parámetros y fallo ante modificación deliberada del azar. Regresión: 654 pasan.

Evidencia: [sintética](../../documentacion/evidencia/mediciones_consultas_juan.json),
[referencia](../../documentacion/evidencia/mediciones_consultas_referencia_juan.json)
y [pruebas](../../documentacion/evidencia/pruebas_consultas_juan.txt).
El Documento de Decisiones registra el incumplimiento y los límites. No se
necesitó un spec nuevo ni se eligieron estructuras o K por defecto.

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


## Juan: cierre de mediciones de T029 (2026-11-11)

Memoria/creación en `modelo/bench_memoria.py`, modo optativo `--solo memoria`.
5 000 acciones, 200 salas, 0/32 cazadores, cuatro K y solo inicial. Memoria
mitad/final/pico separada de tiempos; equivalencia verificada. Junto con los
ensayos de consultas y persistencia cubre T029, distribuida entre los módulos
de benchmark. Resultados y límites en el Documento de Decisiones y evidencia
`mediciones_memoria_juan.json`. Los presupuestos de tiempo no se cumplen en
las cargas medidas: completar la medición no equivale a cumplir PR-LT-001/007.
T030/T031/T032 y la selección de K siguen pendientes. Las menciones anteriores
a memoria pendiente describen avances históricos y quedan superadas aqu?.


## Investigación elegida por el usuario: plantilla compartida

Prototipo aislado en `adaptadores/estado_compartido.py`, con investigación y
resultados en research.md y Documento de Decisiones. Tres pruebas nuevas;
regresión 658/658. Ahorro exploratorio 13,7 % de memoria, sin mejora suficiente
de latencia. No se marca cerrada la aceptación ni se integra sin validar
replay/persistencia y medir 5 000 acciones. K y formato 6 no cambian.


### Investigación compartida: ensayo completo

Validación directa, tipos precalculados y reserva de tabla existente; tuplas
inmutables sin registro redundante. Historia experimental de 5 000 acciones,
300 salas, 32 cazadores y K=25: normal 16/36 consultas >=50 ms, compartido 17/36;
no demuestra mejora suficiente. Continúa aislado; no se marca aceptación ni
se cambia K. Evidencia `historia_compartida_5000_juan.json` y regresión en
`pruebas_compartido_optimizado_juan.txt`. Los documentos previos son históricos.


## Prioridad indicada por Juan (2026-11-11)

Se pospone optimizar los 50 ms hasta terminar el resto. T030/T031 medidas y
verificadas en nueve escenarios (200/300/1000 salas; 0/8/32 cazadores), tres
rondas. Re-simulación/deshacer de 1/3/5 esperas, memoria real de contenedores
de deltas (no proceso total), copiador/codec y reproducción de trazas reales de
agenda con registro histórico activo. Se conservan estructuras aprobadas.
T032: ruta conjunta `main.py --bench --bench-linea-tiempo` implementada y
verificada con pruebas de exportación. No ejecutada la corrida conjunta larga
para respetar la prioridad; siguen disponibles todas las evidencias individuales.
T035/T036: documentos y comandos actualizados parcialmente; K definitivo pendiente.
T037: matriz de trazabilidad en [trazabilidad.md](trazabilidad.md); no se declara
aceptación final mientras K y los presupuestos sigan pendientes. El historial
Git no es verificable en esta copia descargada.


## Cierre solicitado de los dos primeros apartados (2026-11-11)

T032 ejecutada con `python main.py --bench --bench-linea-tiempo --repeticiones 1`:
JSON, log y entorno nuevos. Se verificaron 10 escenarios de consultas, 10 de
memoria, 4 de persistencia y 9 de decisiones; semilla 2026 y una ronda general.
Regresion posterior: 663 pruebas aprobadas, salida en `pruebas_linea_tiempo.txt`.
En `documentacion/CIERRE_MEDICIONES_P2.md` consta el cierre de ejecucion y de la
documentacion independiente de K. Las menciones anteriores a corrida conjunta
pendiente son historicas y quedan superadas por este registro.
T035/T036: parte independiente de K completa; falta incorporar K definitivo.
T037: matriz revisada y regresion ejecutada; declaracion final de aceptacion
pendiente por los presupuestos y K. No se certifica 20/50 ms ni se modifica K.

## Juan: registros inmutables por ID (2026-11-12)

D-LT-08 elegida expresamente por el usuario e implementada. Captura sin
retener modelos, reconstrucción de alias/ciclos y conversión compatible con
guardado v6. Corregidas retenciones del copiador y de consultas temporales.
Medidos 5 000 pasos con tres K en el mismo ensayo de ciclos/consultas.
Resultado sintético: 0/36 consultas >=50 ms para cada K=5/10/25. Referencia
oficial K=25: 23/36 excedidos; creación de puntos sigue excediendo 20 ms.
Perfil diagnóstico: domina el replay de cazadores, en particular sus rutas.
No se cierran PR-LT-001/007, T034 ni aceptación; memoria nueva pendiente.
Detalles y comandos en `documentacion/REGISTROS_INMUTABLES_JUAN.md`.

## Optimizaciones conservadoras de costos (2026-11-12)

Segundo hash diferido en la tabla ya aprobada: comparación oficial ABBA sobre
los mismos puntos y consultas. Compactación de campos de registros por ID:
9,7 % menos memoria por punto en el ensayo controlado; bytes v6 equivalentes.
Regresión: 674 pruebas. Corrida conjunta posterior de K=5/10/25 conserva picos
superiores a 20/50 ms y no prueba mejora de latencia. Resultados y comandos en
`documentacion/OPTIMIZACION_COSTOS_JUAN.md`. T034/aceptación siguen pendientes.

Cache compartida D-TC-09 elegida e implementada: regresión 684 pruebas;
43,1 % menos búsquedas Dijkstra en el ensayo oficial ABBA, con resultados
equivalentes. Aún hay excedidos oficiales a 50 ms. Sintético K=5/10/25:
0/36 consultas excedidas por K, pero ciclos siguen excediendo 20 ms.
Ver `documentacion/CACHE_RUTAS_JUAN.md`. K definitivo sigue pendiente.

Comparación oficial con K experimental configurable: K=5/10/25, procesos
independientes, 5 000 acciones, 36 consultas por K y observador externo de RSS.
Pico residente 1 833/941/407 MiB y 1/9/16 consultas >=50 ms, respectivamente.
Regresión 686 pruebas. Detalles en `documentacion/K_OFICIAL_JUAN.md`.
Ningún K cierra todos los límites: T034 y aceptación siguen pendientes.
El usuario eligió después conservar tuplas y optimizar captura; no se empaqueta.

## Captura conservando tuplas (2026-11-12)

Eliminadas búsquedas de esquema de contenedores, reducidos generadores/listas
temporales y precalculados lectores de campos. Misma representación, raíz,
registros completos y bytes v6 en comparación intercalada contra versiones previas.
Regresión tras cada cambio: 686 pruebas. Comparación acumulada: mediana
38,125 -> 29,979 ms, sin cumplir 20 ms. Sintético K=5/10/25: 482/101/27 ciclos
>=20 ms y 0/36 consultas >=50 ms por K. K=25: todos los excedidos crearon punto.
Detalles y comandos en `documentacion/CAPTURA_TUPLAS_JUAN.md`.
No se cierran PR-LT-001/007, elección definitiva de K ni aceptación final.

Contraste oficial posterior K=25: 5 000 acciones, 36 consultas, mediana
59,345 ms, máximo 97,483 ms y 21 excedidos; partida intacta y cero HTTP.
La mejora aislada de captura no demuestra mejora de consulta oficial completa.

## Continuación de captura: primitivos y reserva (2026-11-12)

Inserción directa descartada por falta de beneficio. Implementados clasificación
rápida de None/primitivos y reserva temporal de 64 posiciones estimadas por sala.
Registros completos y bytes v6 iguales en comparaciones intercaladas; 688 pruebas
tras cada cambio, incluyendo crecimientos, alias/ciclos y tipos exactos.
Reserva 64: 256 KiB temporales más, sin aumentar memoria retenida del punto.
ABBA de historias completas K=25: 166/57/74/61 ciclos >=20 ms en A/B/B/A;
0/36 consultas >=50 ms por bloque. No cierra presupuestos ni elección de K.
Reproducción y resultados en `documentacion/CAPTURA_TUPLAS_JUAN.md`.
Catálogo acotado de tuplas de ID propuesto y pendiente de elección; no implementado.

## Catálogo de tuplas de ID elegido e implementado (2026-11-12)

La propuesta anterior fue elegida explícitamente por el usuario. Catálogo
inmutable de 16 384 tokens, fallback propio y ámbito local de IDs por punto.
691 pruebas; independencia entre puntos, concurrencia, límite, liberación de
modelos y bytes v6. Memoria marginal 1 405 512 -> 898 948 bytes en el estado
medido (36,0 % menos), más costo fijo estimado 1 433 608 bytes por proceso.
ABBA de historias K=25: 16/9/12/15 ciclos >=20 ms en A/B/B/A; sigue pendiente.
Sintético K=5/10/25: 219/40/11 ciclos excedidos. Oficial: 24/0/9 consultas
>=50 ms, RSS observado 1 252/652/291 MiB. K=10 cumple solo la muestra oficial;
K definitivo, presupuestos completos y aceptación siguen pendientes.
Método y comandos en `documentacion/CATALOGO_ID_JUAN.md`.
Reutilización de registros completos iguales propuesta, aún sin elección.

## Registros completos elegidos e implementados (2026-11-13)

Propuesta anterior elegida explícitamente. Captura con antecesor opcional,
índice existente y comparación de código/datos/tipos/bits; arreglo propio sin
retener al antecesor. Línea y carga v6 reutilizan entre puntos. 697 pruebas:
independencia, IDs reasignados, tamaños, ciclos, liberación, bytes v6 y tipos.
ABBA K=25: 9/5/8/9 ciclos excedidos para A/B/B/A, con mayor mediana de captura
por el costo de comparar. Sintético K=5/10/25: 94/22/21 ciclos >=20 ms.
Oficial: 0/0/2 consultas >=50 ms, RSS observado 757/399/192 MiB. K definitivo
y aceptación pendientes. Datos en `documentacion/REGISTROS_IGUALES_JUAN.md`.

## Diagnóstico dirigido de picos (2026-11-13)

Sin cambios al motor. Instrumentación con GC habilitado: K=10/25, 52/19
ciclos lentos; todos crean punto. Captura: 98,0/97,6 % del tiempo lento; GC:
14,7/16,6 %. El prototipo de plantilla heredado es más lento en captura aislada
y no se integra. 699 pruebas, incluidos efectos sobre callbacks/umbrales y error.
Resultados en `documentacion/DIAGNOSTICO_PICOS_JUAN.md`. Se propone captura
incremental versionada frente a separación estático/mutable especializada;
elección y ampliación del diseño pendientes antes de implementar. PR-LT-001/007,
K definitivo y aceptación no se cierran con un diagnóstico instrumentado.

## Ruta incremental elegida: especificación (2026-11-13)

**Registro histórico de un experimento rechazado.** Cerrado el 2026-11-14: las
casillas que quedaban abiertas se marcan como cerradas sin ejecutar, porque
dependían de integrar una variante que los datos rechazaron; cada una indica
su motivo y no declara trabajo realizado. Ver EX-01 al comienzo de este archivo.

- [X] CI-001 Ampliar requisitos de captura, versiones, identidad, ciclo de vida,
  mutaciones, undo, publicación, carga y medición (FR-CI/PR-CI).
- [X] CI-002 Revisar fronteras: motor, agenda, inventario, conocimiento, carga y
  undo; documentar ventana de cinco acciones y escrituras fuera de `_cambiar`.
- [X] CI-003 Definir oráculo completo y piloto acotado con criterios de descarte.
- [X] CI-004 Elegir índices: usuario elige hash propio/vector inmutable (2026-11-13).
- [X] CI-005 Concretar IDs/retirada, contenedores no weakref y cobertura por frontera.
  Cerrada 2026-11-14 con CI-005a/b; la parte c se cierra por descarte (abajo).
  - [X] CI-005a IDs monótonos, índice fuerte acotado, retiro de ciclos, publicación
    atómica y cierre documentados y probados para modelos/list/dict/tuple.
  - [X] CI-005b Observador explícito por orden: deltas antes/después, inventario,
    suelo, agenda, azar, navegación y undo; trazas sintéticas con oráculo.
  - [X] CI-005c Cobertura ampliada en datos oficiales y escrituras externas al
    contrato; no afirmar que el envoltorio intercepta cualquier mutación.
    **Cerrada sin ejecutar por descarte (2026-11-14):** solo era necesaria para
    integrar el capturador; CI-008 y CI-011 lo rechazaron. No se afirma cobertura.
- [X] CI-006 Implementar y verificar estructuras aisladas y capturador experimental.
  - [X] CI-006a Índice hash de versiones aislado: 709 pruebas y benchmark separado.
  - [X] CI-006b Registro de identidad/cambios con ciclo de vida documentado.
  - [X] CI-006c Capturador experimental con marcas explícitas y oráculo por defecto.
  - [X] CI-006d Envoltorio de órdenes reales sin parchear clases productivas.
- [X] CI-007 Validar cada orden/undo/carga contra captura completa y bytes v6.
  Cerrada 2026-11-14 con CI-007a y la parte sintética de CI-007b.
  - [X] CI-007a Modelo completo tras cada orden de traza pequeña, cinco undo,
    recarga v6, continuación contra captura completa y controles negativos.
  - [X] CI-007b Evaluación larga de todos los puntos y datos oficiales.
    - [X] Seis historias sintéticas de 5 000 acciones: bytes v6 de todos los
      puntos K25 iguales entre variantes, consultas equivalentes y estado intacto.
    - [X] Validación oficial; no priorizar integración de una variante más lenta.
      **Cerrada sin ejecutar por descarte (2026-11-14):** la variante es más lenta
      (CI-008) y no se integra; validarla con la cripta oficial gastaría
      presupuesto de solicitudes sin cambiar la decisión. No hay validación oficial.
- [X] CI-008 Medir registro/captura/consulta/RSS con GC y crecimiento incluidos;
  decidir integración solo con equivalencia y ventaja demostradas.
  - [X] Costos sintéticos completos, GC, mantenimiento y perfil: no activar
    variante actual porque aumenta captura de ~13,7 a ~50–54 ms para K25.
  - [X] RSS/oficial de una variante que primero demuestre ventaja.
    **Cerrada por su propia condición (2026-11-14):** ninguna variante demostró
    ventaja (CI-008: ~13,7 → ~50–54 ms; CI-011: índice inverso sin ventaja), así
    que no existe variante que medir. Decisión final: no integrar; producción usa
    el copiador completo con registros inmutables por ID (D-LT-08).
- [X] CI-009 Elegir siguiente ensayo: índice inverso hash ID → entrada con
  bajas/tumbas frente a conservar barrido y reducir marcas. Propuesta y costos
  en `documentacion/CAPTURA_INCREMENTAL_JUAN.md`; usuario eligió índice inverso.
- [X] CI-010 Implementar índice inverso, bajas/tumbas transaccionales, reducción,
  liberación y pruebas negativas. Añadidos primer sondeo rápido, observación
  de sufijos modificados y reserva privada por salas; 744 pruebas.
- [X] CI-011 Cerrar ABBA antes/después con puntos v6 completos, costos de
  mantenimiento, espacio adicional y decisión de integración.
  Ocho historias largas / 40 000 acciones vigentes, 744 pruebas. Índice inverso
  inicial más lento; con ajustes queda en ~46–47 ms, sin ventaja clara sobre
  control ~46 ms y con ~754 KiB privados adicionales. Todas las capturas del
  ensayo ajustado exceden 20 ms. **No integrar esta variante**. Datos y límites
  en `documentacion/INDICE_INVERSO_JUAN.md`; K/presupuestos siguen abiertos.

Ruta e índices del piloto elegidos por el usuario. La existencia del prototipo
no activa producción ni cierra presupuestos o K. Contratos y etapas en
`incremental.md`; integración y aceptación siguen pendientes.
