# Reanálisis de entrega — 2026-11-13

Fuente normativa: [Cripta - Parte II](../Cripta%20-%20Parte%20II.pdf), leído
completo, y los cuatro specs contrastados con código/pruebas. Este informe
reemplaza la prioridad anterior de ampliar prototipos. No es otra propuesta
de estructuras ni una declaración de aceptación final.

## Diagnóstico: por qué parecía que no avanzábamos

Las cuatro capacidades del juego ya estaban implementadas. Se dedicaron varios
bloques a reemplazar la captura con prototipos que no superaron a producción.
Esos ensayos generaron contratos FR-CI/PR-CI adicionales y tareas que terminaron
mezcladas con los pendientes del enunciado. Esa prioridad fue incorrecta:
agregar índices al prototipo no cerraba una funcionalidad del juego ni un límite.

Además, K seguía provisional pese a existir una comparación útil, `--bench`
omitía historia sin otra bandera, faltaban los archivos de entrada exigidos
en raíz y el estado principal seguía mostrando 663 pruebas y cifras antiguas.
Por tanto, el avance no era solo el problema de lograr 20 ms: faltaba cerrar
integración, configuración y entrega con la implementación existente.

## Qué exige realmente el proyecto

| Rubro del PDF | Peso | Estado contrastado |
|---|---:|---|
| Especificaciones, constitución, proceso y trazabilidad | 20 % | Cuatro specs, planes y tareas; 62 FR del juego. Matrices existentes y 23 casos obligatorios reconciliados abajo. Historial del traslado tiene una limitación declarada. |
| Terreno, cazador e invalidación | 20 % | Implementados: costos, rango, empate por primer vecino, invalidación y persistencia. |
| Niebla y viaje | 10 % | Implementados: conocimiento, memoria de puertas, antorcha, paradas, undo, log y replay. |
| Resolubilidad | 15 % | Implementados: cierre incremental, orden, frontera, ciclo concreto, arranque, verificar/forzar y presupuesto. |
| Línea de tiempo | 15 % | Implementada: consultas, límite K, undo, replay, v6. K=10 elegido y aplicado en este bloque. |
| Documento de Decisiones | 10 % | Decisiones y comparaciones existentes; entradas raíz y estado vigente corregidos en este bloque. |
| Rendimiento | 10 % | Tres presupuestos tienen evidencia conforme; el ciclo de 20 ms sigue abierto. No se puede declarar entrega aceptada. |

La estimación global revisada es **aproximadamente 95 %**, orientativa, no una
nota calculada ni una estimación del esfuerzo restante. Se apoya en los rubros
del PDF, no en cuántos prototipos/pruebas se agregan. El bloqueo de rendimiento
puede requerir trabajo relevante aunque solo quede un presupuesto numérico.

El PDF **no obliga** a captura incremental, AVL persistente, índice inverso,
empaquetado de tuplas, catálogo adicional ni otro formato binario nuevo. Exige
los comportamientos, las restricciones de memoria/K, las comparaciones y los
límites. FR-CI/PR-CI se conservan en `specs/004-linea-tiempo/incremental.md`
como contrato histórico del experimento rechazado, fuera del spec del juego.

## Implementaciones y cierres hechos durante esta revisión

1. **K=10 definitivo**, elegido explícitamente por Juan y aplicado en
   `modelo/linea_tiempo.py`. Nuevas partidas/replay lo usan; cargar sin opción
   conserva el K guardado. Se corrigieron pruebas que suponían 25 provisional.
2. **`main.py --bench` completo por defecto**: incluye memoria/consultas de
   historia con varios K y solo punto inicial; no requiere otra bandera.
   Reutiliza decisiones ya medidas y mantiene el alias anterior sin duplicar.
3. **Exportación utilizable**: `--salida-bench`, salida predeterminada ignorada
   por Git, entorno/K/fecha en JSON y errores de medición/exportación con código 1.
   No sobrescribe evidencia versionada por defecto. Se verificó el comando
   con los bloques reales en escala pequeña, sin vista ni HTTP.
4. **Entrega navegable**: `DECISIONES.md` y `PROMPTS_LLM.md` en raíz; README,
   estado, plan y trazabilidad reconciliados. No se duplican bitácoras enormes.
5. **Validación de producción con K elegido** y regresión completa de
   **751 pruebas**, sin activar los capturadores experimentales.

## Presupuestos: hechos, condiciones y pendientes

| Operación exigida por §6.1 | Evidencia | Resultado |
|---|---|---|
| Historia <50 ms, ≥5 000 acciones, K por defecto | Nueva corrida oficial K10: cripta-06, 300 salas, 32 cazadores iniciales, semilla 2026, 36 consultas; GC habilitado, sin trazado/perfilador, cero HTTP al consultar | **0/36 excedidas; máxima 35,9904 ms**, RSS observado 400,14 MiB; partida intacta |
| Ciclo <20 ms, decenas de cazadores | Nueva regresión sintética de producción K10: 300 salas, 32 cazadores, 5 000 acciones vigentes, 5 001 ciclos con registro incluido | **14/5 001 excedidos**, todos con punto; máximo 40,3269 ms. No cumple esta carga; falta cierre oficial final |
| Resolubilidad <200 ms, mayor cripta publicada | Evidencia oficial previa, misma referencia de 300 salas; no repetida en esta revisión porque su algoritmo no cambió | Máximo registrado 7,5888 ms; evidencia conforme, no cifra nueva |
| Paso de viaje <5 ms, mapa completo de referencia | Evidencia oficial previa de niebla/viaje; algoritmo no modificado en esta revisión | Máximo registrado 2,1130 ms; evidencia conforme, no cifra nueva |

Fuentes: [consultas oficiales nuevas](evidencia/validacion_k10_entrega.json),
[ciclos nuevos](evidencia/ciclos_k10_entrega.json),
[regresión](evidencia/pruebas_entrega_p2.txt),
[resolubilidad](evidencia/mediciones_resolubilidad.json) y
[auditoría de referencia y límites previos](evidencia/auditoria_integridad_2026-11-09.md).
No se garantiza el máximo para cualquier equipo, orden de acciones o ejecución.

## Lo que falta ahora, en orden y con criterio de terminación

### 1. Corregir el costo de puntos del código de producción

Es el pendiente de implementación. Los **4 501 ciclos sin punto** dieron máximo
**1,1315 ms**, ninguno excedido. Los 14 ciclos lentos están entre los 500 que
crearon punto; la captura mediana fue 13,0834 ms y su máximo 39,9700 ms.
Esto acota la próxima tarea a `adaptadores/instantanea_inmutable.py` y su
publicación desde `CargadorPartida._capturar_punto`, no a reemplazar resolubilidad,
inventario o la búsqueda del cazador ni a agregar otro índice al prototipo.

Contrato que debe conservarse: estado completo, alias/ciclos, tipos/bits,
independencia, azar, v6 y máximo K acciones. La implementación se debe aceptar
por equivalencia de registros/bytes y costo del ciclo completo, no solo por
mediana aislada. No se cambia el umbral, no se deshabilita GC ni se mueve el
costo fuera del cronómetro. El PDF exige 20 ms; PR-LT-007 ya incluye el registro
de historia en esa responsabilidad y no se rebaja silenciosamente.

### 2. Validar la corrección terminada sobre la referencia

Repetir únicamente la aceptación afectada: ciclos de referencia con decenas de
cazadores y consultas K10/5 000 acciones; mantener controles de estado y red.
La comparación memoria/consulta de tres K y sin puntos **ya existe**; no es
necesario reinventarla o repetir cada experimento descartado por otro cambio.
Un resultado ≥20 ms deja abierto ese requisito; no se borra ni promedia para aprobar.

### 3. Cerrar aceptación y actualizar las cifras finales

T037 y PR-LT-007 siguen abiertos por 20 ms; SC-LT-004 cumple en la corrida K10.
Tras una corrección válida,
actualizar solo evidencia afectada, estado, matriz y decisión. No hacen falta
otra capacidad, otra familia de specs ni más experimentos CI para entregar.

## Apéndice B: 23 casos con implementación y prueba

Numeración B01–B23 local, en el orden del PDF. Los enlaces a tareas contienen
la cadena FR → AC → T → código; las funciones citadas existen en `Pruebas/`.
La regresión ejecuta estos casos junto con sus comprobaciones de integración.

| Caso | Escenario/tareas | Implementación | Prueba concreta |
|---|---|---|---|
| B01 Cazador sin ruta espera | [001 AC-TC-007](../specs/001-terreno-cazadores/tasks.md) | rutas.py / motor_eventos.py | `prueba_rutas.py::test_ac007_008_rango_y_sin_ruta` |
| B02 Ruta fuera de rango espera | [001 AC-TC-008](../specs/001-terreno-cazadores/tasks.md) | rutas.py / motor_eventos.py | `prueba_rutas.py::test_ac006_008_turno_cazador_mueve_espera_ataca` |
| B03 Menor costo frente a menos salas | [001 AC-TC-009](../specs/001-terreno-cazadores/tasks.md) | rutas.py | `prueba_rutas.py::test_ac009_ruta_mas_barata_no_es_la_de_menos_salas` |
| B04 Empate por vecino de menor ID | [001 AC-TC-010](../specs/001-terreno-cazadores/tasks.md) | rutas.py / heap_rutas.py | `prueba_rutas.py::test_ac010_mejorar_primer_salto_con_igual_costo` |
| B05 Cierre invalida ruta | [001 AC-TC-012](../specs/001-terreno-cazadores/tasks.md) | motor_eventos.py | `prueba_rutas.py::test_ac012_013_puertas_reutilizacion_y_cierre_automatico` |
| B06 Intervalo mínimo 1 | [001 AC-TC-003](../specs/001-terreno-cazadores/tasks.md) | motor_eventos.py | `prueba_terreno.py::test_ac001_003_movimiento_programa_el_intervalo_de_la_salida` |
| B07 Velocidad reescala restante | [001 AC-TC-004](../specs/001-terreno-cazadores/tasks.md) | agenda_eventos.py | `prueba_terreno.py::test_ac004_velocidad_reescala_solo_tiempo_restante` |
| B08 Viajar a no explorada se rechaza | [002 AC-NV-009](../specs/002-niebla-viaje/tasks.md) | conocimiento.py | `prueba_conocimiento.py::test_ac009_nombre_exacto_duplicados_y_ocultos` |
| B09 Puerta recordada abierta, real cerrada | [002 AC-NV-013](../specs/002-niebla-viaje/tasks.md) | partida.py / motor_eventos.py | `prueba_niebla_partida.py::test_ac013_016_no_abre_puertas_y_recalcula` |
| B10 Enemigos dormidos detienen viaje | [002 AC-NV-014](../specs/002-niebla-viaje/tasks.md) | partida.py | `prueba_niebla_partida.py::test_ac014_015_enemigos_al_entrar_y_dano_aunque_cure` |
| B11 Antorcha revela sin activar | [002 AC-NV-006/007](../specs/002-niebla-viaje/tasks.md) | conocimiento.py / motor_eventos.py | `prueba_niebla_partida.py::test_ac006_007_antorcha_no_carga_ni_activa` |
| B12 Pergamino revierte revelación | [002 AC-NV-019](../specs/002-niebla-viaje/tasks.md) | retroceso.py | `prueba_conocimiento.py::test_ac006_007_008_019_antorcha_no_recursiva_y_retroceso` |
| B13 Pergamino detiene viaje | [002 AC-NV-020](../specs/002-niebla-viaje/tasks.md) | controlador.py / partida.py | `prueba_niebla_partida.py::test_ac019_020_interrumpir_retrocede_ultimo_paso_y_no_continua` |
| B14 Llave se bloquea a sí misma | [003 AC-RS-008/009](../specs/003-verificar-resolubilidad/tasks.md) | verificacion.py | `prueba_certificados_resolubilidad.py::test_ac008_009_autobloqueo_concreto_y_frontera_unica` |
| B15 Botín se ubica al inicio | [003 AC-RS-007](../specs/003-verificar-resolubilidad/tasks.md) | verificacion.py | `prueba_resolubilidad.py::test_ac006_007_016_repetible_sin_mutar_datos_y_botin_inicial` |
| B16 Orden de llaves determinista | [003 AC-RS-006](../specs/003-verificar-resolubilidad/tasks.md) | verificacion.py | `prueba_resolubilidad.py::test_ac006_007_016_repetible_sin_mutar_datos_y_botin_inicial` |
| B17 No inicia sin forzar | [003 AC-RS-013](../specs/003-verificar-resolubilidad/tasks.md) | main.py | `prueba_cli_resolubilidad.py::test_ac013_no_inicia_sin_forzar` |
| B18 Historia futura se rechaza | [004 AC-LT-011](../specs/004-linea-tiempo/tasks.md) | linea_tiempo.py | `prueba_historia_partida.py::test_ac011_012_rechazo_posterior_y_numeracion_tras_pergamino` |
| B19 Historia no muestra lo revertido | [004 AC-LT-012/014](../specs/004-linea-tiempo/tasks.md) | linea_tiempo.py / partida.py | `prueba_historia_partida.py::test_ac011_012_014_historia_vigente_tras_pergaminos` |
| B20 Todos los eventos simultáneos | [004 AC-LT-004/005](../specs/004-linea-tiempo/tasks.md) | motor_eventos.py / partida.py | `prueba_limite_tiempo.py::test_limite_ejecuta_eventos_hasta_t_y_se_detiene_antes_de_la_decision` |
| B21 Consulta no altera tiempo/log/undo | [004 AC-LT-007/008/009](../specs/004-linea-tiempo/tasks.md) | partida.py / controlador.py | `prueba_historia_partida.py::test_ac007_008_009_consultas_no_cambian_nada_ni_el_log` |
| B22 Replay posterior al final | [004 AC-LT-016](../specs/004-linea-tiempo/tasks.md) | main.py | `prueba_bitacora_partida.py::test_ac016_partida_terminada_antes_de_t` |
| B23 Guardado anterior incompatible | [004 AC-LT-024](../specs/004-linea-tiempo/tasks.md) | estado_binario.py | `prueba_estado_binario.py::test_ac024_formatos_anteriores_se_rechazan_sin_cargar` |

## Límites documentales que no se arreglan escribiendo otro prototipo

Parte de 004 se desarrolló en una copia sin Git y luego se trasladó: no se
puede recrear honestamente ese historial. Se conserva la explicación del traslado.
El enunciado original de P1 no está en el repositorio. Las interpretaciones
del grupo sobre antorcha y K por tramo permanecen explícitas, separadas del
texto literal de P2. La defensa debe explicar estas decisiones, sin inventar
enmiendas oficiales ni cambiar reglas para aprobar un benchmark.
