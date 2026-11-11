# Plan: Línea de tiempo y puntos de control

**Fecha**: 2026-11-09. **Rama real**: `main`.
**Capacidad activa de spec-kit**: `004-linea-tiempo`.
**Entrada**: [spec.md](spec.md). **Estado**: diseño implementado; mediciones y documentación en cierre, con presupuestos incumplidos y K pendiente.
**Decisiones**: D-LT-01 a D-LT-06 elegidas por el usuario. D-LT-07 (K por
defecto) se elegirá con mediciones. Alternativas, mediciones previas y descartes
en [research.md](research.md).

## Resumen

Consultar sin modificar la partida el estado en cualquier instante de la
historia vigente. Cada K acciones ejecutadas se guarda una copia completa en
memoria del estado (punto de control). Entre puntos solo se registran las
órdenes reproducibles. Una consulta copia el punto más cercano anterior, re-simula
como máximo K acciones sin red ni vista y presenta el resumen. `--replay … --hasta`
reconstruye la misma línea desde el log y usa la misma consulta. El guardado
conserva toda la línea en un formato nuevo.

## Contexto técnico

| Aspecto | Diseño |
| --- | --- |
| Lenguaje y entorno | Python 3.11+ (probado en 3.14), CLI/MVC existentes; Windows local de referencia. |
| Dependencias | Ninguna nueva en producción; pytest como herramienta de pruebas. |
| Reconstrucción | Hacia adelante desde el punto anterior más cercano, re-simulando órdenes, D-LT-01. |
| Puntos de control | Arreglo creciente y búsqueda binaria propia por posición de orden, D-LT-02. |
| Registro | Arreglo de órdenes ejecutadas (solo crece) y arreglo de acciones vigentes por k, D-LT-03/05. |
| Copia | Copiador de grafo iterativo propio guiado por el esquema del guardado, con tabla de identidades propia, D-LT-04. |
| Persistencia | Formato del modelo versión 6 con órdenes, acciones, tramos de K y todos los puntos, D-LT-06. |
| K por defecto | Pendiente; candidatos 10, 25, 50 y 100, D-LT-07. |
| Objetivos | PR-LT-001: < 50 ms por consulta con ≥ 5 000 acciones y K por defecto. PR-LT-007: ciclo < 20 ms sin degradarse. |
| Escala | A acciones ejecutadas, O órdenes, P = ⌈A / K⌉ puntos, S tamaño del estado copiado. |

## Algoritmo

**Registro durante la partida**

1. Al iniciar, crear el punto 0 con la copia del estado en el instante 0 y fijar
   el instante de decisión pendiente en 0.
2. Tras cada orden aceptada y reproducible (las mismas que van a `partida.log`),
   agregarla al arreglo de órdenes. Se clasifica comparando el contador de
   acciones antes y después:
   - **+1, acción**: agregar (instante de decisión, posición) a las acciones
     vigentes y sumar una acción al tramo.
   - **−1, pergamino**: truncar las acciones vigentes al contador restaurado.
     No suma al tramo: el pergamino no es una acción (FR-LT-013). La acción que
     revierte ya se contó al ejecutarse, así que re-simular su `retroceder` no
     amplía el límite de K acciones por consulta.
   - **0, navegación**: solo queda en el arreglo de órdenes.
3. Actualizar el instante de decisión pendiente con el reloj actual.
4. Si el tramo llegó a K, crear un punto con la posición, la acción y el instante
   actuales, y reiniciar el tramo.
5. Las consultas, `ver mapa`, `inv`, `orden`, `guardar` y `cargar` no se
   registran; el comentario `# ir a` tampoco.

**Consulta**

1. Validar el argumento. t debe estar entre 0 y el reloj actual; k entre 1 y
   N + 1.
2. Si t es el reloj actual o k = N + 1, resumir el estado actual sin copiar.
3. Calcular el objetivo:
   - **`#k`**: la posición de la orden de la acción k, sin incluirla.
   - **`t`**: búsqueda binaria de la última acción vigente j con instante ≤ t. Si
     su instante es t, el objetivo es su posición, sin incluirla. Si no, el
     objetivo la incluye, con límite de tiempo t.
4. Buscar el último punto cuya posición sea ≤ al objetivo (búsqueda binaria).
5. Hacer una copia de trabajo del punto, conectarla a un preparador de salas de
   solo lectura y a un gestor de guardado inerte, y re-ejecutar las órdenes
   entre ambas posiciones con el mismo ejecutor que usa el replay. Por
   construcción son ≤ K acciones.
6. Si el objetivo tiene límite de tiempo, el ciclo procesa solo los eventos con
   tiempo ≤ t y deja el reloj de la copia en t.
7. Construir el resumen histórico con la copia y descartarla. La partida real, su
   historial de retroceso, el log y su azar no cambian.

**Cambio de K al cargar**: los puntos existentes se conservan y el nuevo K rige
desde la carga. Se guarda el K de cada tramo; la cota por consulta es el K del
tramo consultado (AC-LT-025).

## Complejidad prevista y límites

| Operación | Costo esperado |
| --- | --- |
| Registrar una orden | O(1) amortizado. Cada K acciones se suma O(S) por la copia. |
| Recortar por pergamino | O(acciones revertidas), ≤ 5, sin recorrer la historia (PR-LT-004). |
| `#k` → objetivo | O(1). |
| t → objetivo | O(log A). |
| Ubicar el punto | O(log P) (PR-LT-002). |
| Consulta | O(S) por la copia de trabajo, más el costo de re-simular ≤ K acciones y el resumen. |
| Memoria | O(O + A + P · S). Crece con lo ocurrido más una copia cada K acciones, nunca con A · S (PR-LT-003). |

La medición previa sugiere unos 6 ms de copia con 300 salas y unos 1 ms por
acción re-simulada con 32 cazadores (con picos de 26 ms). Con K grande una
consulta con cazadores puede pasar de 50 ms, y con K pequeño la memoria crece
(research.md). La creación del punto ocurre una vez cada K acciones; se medirá
aparte y dentro del ciclo para comprobar PR-LT-007. No se garantiza el peor
caso de cualquier carga.

## Integración y estructura del proyecto

| Archivo o área prevista | Responsabilidad | Requisitos |
| --- | --- | --- |
| `modelo/linea_tiempo.py` (nuevo) | Arreglos de órdenes, acciones y puntos; búsquedas binarias; recorte; tramos de K; cálculo de objetivo. | FR-LT-001/003/004/007/008/009/012/013; PR-LT-002/003/004 |
| `adaptadores/copia_estado.py` (nuevo) | Tabla de identidades propia y copiador iterativo guiado por el esquema de `estado_binario.py`; reconstrucción de auxiliares; copia de `random.Random`. Vive junto al esquema para que el modelo no dependa de adaptadores; la línea recibe la función de copia por parámetro. | FR-LT-013/014; PR-LT-003 |
| `modelo/motor_eventos.py` | Límite de tiempo opcional en el avance de eventos, inactivo en la partida real. | FR-LT-003 |
| `controlador/partida.py` | Línea por partida, registro tras cada orden, consulta y resumen histórico (enemigos vivos con estado). | FR-LT-001/002/004/005/006 |
| `controlador/comandos.py`, `controlador/controlador.py` | Analizar `historia <t>`/`historia #k`, consulta sin registro, interrupción de «ir a». | FR-LT-001/006/007 |
| `controlador/cargar_partida.py` | Preparador de salas de solo lectura sin red ni precarga y gestor inerte para copias; persistencia de la línea. | FR-LT-006/013/015 |
| `adaptadores/estado_binario.py` | Esquema versión 6 con línea, puntos y tramos; rechazo de versiones anteriores; esquema reutilizable por el copiador. | FR-LT-015/016 |
| `adaptadores/bitacora_partida.py`, `main.py` | `--hasta`, `--checkpoint-cada`, validación de combinaciones, impresión sin vista. | FR-LT-010/011/012 |
| `vista/vista_consola.py` | Presentar el resumen histórico y los rechazos. | FR-LT-002/007 |
| `modelo/bench_linea_tiempo.py` (nuevo), bench existente | K = 10/25/50/100 y sin puntos; adelante frente a atrás; copia propia frente a serializador; repetición de mediciones de P1. | PR-LT-001 a 007 |
| `modelo/bench_linea_tiempo.py`, `adaptadores/bench_adaptadores.py --solo consultas` | Tramo ejecutado de T029: tiempos completos para K = 10/25/50/100 y solo punto inicial, con 0/32 cazadores; resúmenes capturados en vivo, equivalencia y cota K. Tramo de T033 con `--cripta`: datos reales precargados y K provisional. Sin cambiar reglas/estructuras; integración general aún en T032. | FR-LT-003/006/013/014; PR-LT-001/002/005 |
| `adaptadores/bench_persistencia.py`, `adaptadores/bench_adaptadores.py` | Tramo de Juan en T029/T030: sesión completa de 5 000 acciones para K = 10/25/50/100, tamaño y tiempos de guardar/cargar, equivalencia y copiador frente a ida y vuelta binaria. Carga sin cazadores, optativa hasta T032. No incorpora estructuras nuevas ni cambia reglas. | FR-LT-015; PR-LT-005/006 |
| `Pruebas/` | Aceptación AC-LT-001 a 025 y regresión de partida, replay, guardado, niebla y retroceso. | SC-LT-001 a 005 |

## Comprobación de la constitución antes y después del diseño

| Principio | Comprobación |
| --- | --- |
| I. Estructuras manuales | Arreglos con búsqueda binaria propia y tabla de identidades propia. Sin `dict`/`set` como índice, sin `bisect`, `heapq`, `collections` ni `copy.deepcopy`. Los `dict` de fichas son datos, no índices. |
| II. Determinismo | El punto incluye `random.Random`. La re-simulación usa las mismas órdenes y el mismo ejecutor que replay. K no cambia resultados (FR-LT-014). Bench determinista por semilla. |
| III. MVC y modos sin vista | Línea en el modelo, sin importar adaptadores; copiador junto al esquema en adaptadores; órdenes en el controlador; presentación en la vista. `--replay --hasta` no instancia la vista. |
| IV. Datos externos | Sin datos de criptas en el código; la re-simulación usa los datos ya descargados de la cripta en curso. |
| V. Presupuesto y versiones | Las consultas no hacen solicitudes. Formato 6 y rechazo explícito de formatos anteriores. |
| VI. Rendimiento medido | El K por defecto se elige con `--bench`. Se miden adelante/atrás, copias y P1 con la carga nueva. |
| VII. Especificación previa | Spec 5f51f60 y aclaraciones a5a1b96 confirmadas antes del plan; el código vendrá tras tasks y analyze. |
| VIII. Trazabilidad | Cobertura FR/PR → AC en la tabla siguiente; tasks.md la completará con código y pruebas. |
| IX. Prompts | Decisiones registradas en PROMPTS_LLM.md con el mensaje literal. |

**Resultado**: sin violaciones ni excepciones. Pendiente D-LT-07, que no bloquea
las tareas: el valor se fija al final con mediciones. No hay `extensions.yml`.

## Cobertura para la descomposición en tareas

| Trabajo | Requisitos | Escenarios |
| --- | --- | --- |
| Copiador y tabla de identidades | FR-LT-013/014 | AC-LT-019/020/021 |
| Registro, recorte y puntos | FR-LT-008/009/012/013; PR-LT-002/003/004 | AC-LT-011 a 014, 019, 020, 022 |
| Consulta, límite de tiempo y resumen | FR-LT-001 a 007 | AC-LT-001 a 010 |
| Replay `--hasta` y CLI | FR-LT-010/011/012 | AC-LT-015 a 018, 022 |
| Persistencia y K al cargar | FR-LT-015/016 | AC-LT-023/024/025 |
| Mediciones y elección de K | PR-LT-001 a 007 | SC-LT-004/005 |

## Validación y mediciones previstas

La prueba central de equivalencia: grabar una partida sintética, capturar el
resumen en vivo en cada decisión y entre eventos, y comparar con `historia`,
con `--replay --hasta` y con varios K, incluidas partidas con pergaminos y
antorcha. También se comprueba que tras consultar no cambian reloj, log,
historial de retroceso, azar ni continuación (SC-LT-003). Bench con ≥ 5 000
acciones y K = 10/25/50/100 y sin puntos, con y sin cazadores, midiendo
consulta, creación de punto, memoria y ciclo; adelante frente a atrás con los
datos de research.md; copiador frente a serializador. Repetir agenda e
historial de retroceso de P1 con la carga nueva (§5.6).

## Artefactos y siguiente paso

Diseño: [data-model.md](data-model.md). Interfaces: [contrato](contracts/linea-tiempo.md).
Validación: [quickstart.md](quickstart.md). El plan termina aquí. Sigue
`/speckit-tasks`, después `/speckit-analyze` y luego la implementación.


Medición de memoria/puntos de T029: `modelo/bench_memoria.py`, accesible con
`adaptadores.bench_adaptadores --solo memoria`, reutiliza la carga de consultas.
Separa trazado de asignaciones Python y tiempos para evitar contaminar estos;
registra mitad/final/pico, copias periídicas y ciclos con registro en ejecuciones
que deben producir el mismo estado. No introduce decisiones de estructuras.
