# Plan: Línea de tiempo y puntos de control

## Estado vigente: cierre funcional con EX-01

El 2026-11-13 Juan autorizo omitir el problema de latencia si no habia una
solucion rapida. Se conserva la captura completa productiva y K=10. No se
implementan los contadores de revision, la captura distribuida ni la exclusion
del GC descritos en los intentos siguientes: la sesion anterior retiro ese
codigo a las 14:59:29 de Costa Rica. El cierre nuevo verifica 759 pruebas y
registra los incumplimientos de 20/50 ms, sin alterar los requisitos originales.
[Diagnostico, alcance y evidencia](../../documentacion/REVISION_SESION_BLOQUEADA.md).
No queda un trabajo activo de optimizacion en este encargo.

## Intentos anteriores: historicos, no instrucciones de implementacion

Los parrafos siguientes documentan ensayos y propuestas de la sesion anterior;
solo el codigo vigente y el estado enlazado arriba determinan lo implementado.


**Cierre mínimo de 20 ms (2026-11-13):** el perfil de producción concentra el
trabajo en referencia/registro y codificación completa. Mantener la misma tabla
de identidades y doble hash, formatos, K10 y captura completa. Integrar la
primera casilla y la inserción sin crecimiento en el bucle de referencia para
evitar llamadas repetidas por nodo; conservar la ruta existente de colisiones
y crecimiento. Verificar crecimientos, alias/ciclos y bytes v6, luego ciclos
oficiales completos con GC normal. No añadir índices, prototipos ni dependencias.
Solo conservar modificaciones con ventaja medida; no cerrar por la mediana.

En el bucle final, las tuplas ya leídas solo visitan sus hijos (sus elementos
no pueden cambiar); los contenedores vacíos conocidos se omiten. El mismo
doble hash usa un paso impar de otros bits de identidad, sin mezcla multiplicativa
de 64 bits. La capacidad potencia de dos y el paso impar conservan la cobertura
completa, incluidas colisiones/bajas/crecimientos probados. Random se obtiene por
su método estándar y se rechaza un estado opaco con mutables antes de excluirlo
del GC. No hay cambios de prioridad, afinidad, umbrales o reloj de medición.

Resultado: referencia integrada reduce mediana aislada ~10 %, pero conserva
29/5 000 ciclos oficiales >=20 ms; no integrar ese cambio. El cierre utiliza
la decisión ya aprobada de hash propio + vector inmutable, con IDs locales
reutilizables entre puntos. Capturador por línea: comprobar valores inmediatos
por identidad, reutilizar registro e IDs de hijos si no cambiaron, visitar los
hijos igualmente para detectar cualquier mutación. No depender de marcas ni
interceptar escrituras del motor. List/dict se comprueban por contenido inmediato;
Random se lee siempre. Los registros publicados nunca retienen objetos vivos.
Retirar nodos no alcanzados y liberar sus valores; mantener el mismo hash con
bajas/tumbas ya elegidas, recomponiendo solo al superar el 70 % de ocupación.
Reconstruirlo en cada punto anuló el ahorro y no se conserva. Reutilizar casillas libres solo en puntos
posteriores. Vector congelado independiente por punto, huecos sin enlaces.
Cache solo en el capturador de la línea, nunca persistida ni en el punto. Tras
error descartar cache; guardar/cargar sigue materializando v6. Validar alias,
ciclos, cambios externos, retiro acotado, undo/carga y bytes de todos los puntos.

La lectura repetida de todos los atributos no cumple 20 ms. La integración
requiere un contador derivado de revisión en las clases del esquema: incrementar
en asignación/eliminación ordinaria de atributos, incluidas restauración/undo.
Solo los modelos propios con ese contador pueden omitir releer atributos cuando
la revisión coincide; sus hijos se visitan siempre. List/dict/Random y modelos
sin contador conservan comprobación completa. No hay marcas manuales por acción
ni parcheo dinámico; el contador no se persiste ni pertenece al estado simulado.
La escritura directa en `__dict__` no es una API de mutación de partida. Auditar
que producción no la usa salvo liberación de copias descartadas. Probar cobertura
de todos los tipos del esquema, borrado de opcionales y equivalencia con oráculo.

**Distribuir el trabajo sin sacar costo del ciclo:** la mayoría de altas son
tuplas del historial de cinco acciones. Incorporarlas solo cada K concentra
miles de altas y bajas. Actualizar el cache en cada acción dentro de `registrar`,
comprobando revisiones y contenedores, y retirando bajas. La variante que solo
incorpora altas deja todas las bajas para el punto y no cumple; no se conserva.
Cada K, congelar/publicar el vector. No guardar
puntos por acción ni retener vectores intermedios. El trabajo normal, altas,
bajas y mantenimiento se cobra en el ciclo completo, sin hilos ni tareas
diferidas. Medir todos los ciclos, no solo la publicación. Durante reconstrucción
rellenar campos con `object.__setattr__` e inicializar revisión una vez: son
objetos nuevos, no mutaciones de un modelo ya observado.

La distribución deja publicaciones <20 ms, pero aparecen pausas del GC en
ciclos intermedios. Las recolecciones forzadas no se conservan: empeoran el costo.
En CPython, excluir únicamente registros, datos
y vector inmutables ya codificados mediante la API estable `PyObject_GC_UnTrack`:
https://docs.python.org/3.13/c-api/gcsupport.html#c.PyObject_GC_UnTrack
La exclusión abarca cada tupla del dato congelado: tokens (None, escalares),
referencias (ID,), pares de dict, estado interno de Random, registros y vector.
No basta excluir los contenedores exteriores; una prueba recursiva lo verifica.
El vector solo enlaza registros de tuplas/escalares y referencias numéricas;
no puede participar en ciclos ni contener modelos vivos. Se mantiene el GIL
(`ctypes.pythonapi`/PyDLL). Ningún umbral, modo GC, modelo ni contenedor mutable
cambia su seguimiento. Otros intérpretes mantienen GC normal. Verificar que
el original/copia mutable sigue siendo recolectable, bytes v6, liberación de
puntos y medición de todos los ciclos con el costo de esta llamada incluido.

**Mantenimiento de memoria dentro del ciclo (descartado):** tras crear un punto, solicitar
una recolección completa en la siguiente acción positiva que no cree otro punto.
No ejecutarla en consultas/navegación/undo, ni fuera del cronómetro de acción+
registro. Solo si GC está habilitado; no cambiar umbrales, deshabilitarlo ni
congelar generaciones. Esto evita acumular la pasada completa y la captura en
el mismo ciclo. El costo se paga y se mide íntegro en un ciclo sin punto.
Una marca booleana derivada en LineaTiempo no se guarda ni es estado del juego;
la carga inicia su propio mantenimiento. Para K=1 no hay ciclo sin punto y se
mantiene la recolección automática, sin afirmar que ese K cumpla el presupuesto.
Verificar determinismo, GC habilitado/umbrales intactos, costo medido, v6 y
todos los ciclos oficiales K10; no aprobar por medir solo ciclos con punto.

Resultado: las pruebas dirigidas pasaron, pero se midieron 53/5 000 ciclos
oficiales >=20 ms (52 con punto y uno sin punto). No hubo ventaja: retirado
el cambio, sin alterar GC productivo ni mantener otra variante experimental.

**Codificación directa de tuplas escalares:** continuar con registros/tuplas
elegidos, sin otro índice. Una tupla plana de tipos escalares exactos puede
codificarse como `(None, tupla_original)` dentro del campo; las referencias a
nodos siguen siendo `(ID,)`. Ningún ID es None: no hay ambigüedad aun si la
tupla del juego contiene None o enteros. Se evita registrar, encolar y reconstruir
nodos que solo contienen datos inmutables. Tuplas con modelos, listas, dict,
subclases u otras tuplas mantienen su nodo. Se conserva alias de tuplas puras
al compartir el mismo valor inmutable; no se comparte descendiente mutable.
El reconstructor admite ambos formatos en memoria. Guardar materializa el
modelo y conserva v6/bytes normalizados. Verificar tipos/bits, independencia,
alias/ciclos, ausencia de modelos retenidos, memoria y ciclos completos reales.

**Optimización de producción (2026-11-13, PR-LT-007):** conservar IDs locales,
tabla de identidades y los dos arreglos existentes. Durante captura, el vector
de registros conserva temporalmente el objeto original hasta codificar su
casilla; la pila guarda solo el ordinal, evitando una tupla auxiliar por nodo.
Cada casilla debe quedar codificada antes de congelar el punto, sin originales
retenidos. No cambia esquema, orden de IDs, compartición, v6 ni K=10. Validar
regresión y ABBA de ciclos completos, pasando el punto anterior a ambas versiones
que lo admitan y comparando los bytes v6 de todos los puntos fuera del cronómetro.

Resultado: la pila de ordinales no redujo excedidos en ABBA (13/15 ciclos
lentos del control frente a 22/15). Se descartó el cambio de código. El siguiente
ajuste conserva la misma captura: para una tupla cuyos elementos son todos None
o escalares de tipo exacto permitido, conservarla como datos de su registro en
vez de generar otra tupla mediante referencia por elemento. Mantener su registro
e ID para alias/ciclos; nunca compartir una tupla que contenga modelos, listas,
dict u otras tuplas. Rechazar subclases sin esquema, conservar tipos/bits y
validar equivalencia/independencia y ciclos completos antes de conservarlo.
En el mismo capturador, los registros de listas/dict vacíos pueden usar una
constante inmutable por tipo, manteniendo IDs distintos y reconstrucciones
independientes. Evita comprensión vacía y comparación posterior por cada nodo.
Reservar 256 casillas en el índice fijo de esquemas ya existente reduce sondeos
sin cambiar su estructura; contabilizar su pequeño espacio fijo adicional.

**Corrección de aceptación de ciclos (PR-LT-007):** el medidor oficial de
`bench_modelo.medir_ciclos_partida` debe registrar la orden dentro del cronómetro,
como la consola. Tras preparar contenido/cazadores, iniciar el punto base antes
de guardar el estado del benchmark. Además, en las mismas 5 000 acciones oficiales
de `medir_cripta_consultas`, medir acción+registro y separar ciclos con/sin punto.
Conservar máximos/excedidos, número de puntos, GC habilitado y cero HTTP. No
considerar la medición antigua sin registro como aceptación de PR-LT-007.

**D-LT-07 cerrada (2026-11-13):** Juan eligió K=10 para nuevas partidas/replay;
la carga conserva el K guardado salvo opción explícita. Justificación en
`research.md`, con mediciones de producción. Esta decisión no activa prototipos
ni cierra automáticamente los presupuestos de procesamiento.

**Corrección de entrega (2026-11-13):** `main.py --bench` ejecutará también
`modelo/bench_cierre.py` por defecto, reutilizando las decisiones ya medidas
por `bench_modelo`. `--bench-linea-tiempo` queda como alias compatible, sin
doble ejecución; `--salida-bench` selecciona carpeta y por defecto usa
`resultados/bench`, ignorada por Git. El cierre conserva entorno y parámetros
y publica el JSON al terminar. Errores de medición/exportación devuelven 1.
No cambia reglas, K, estructuras ni algoritmos. PR-LT-005/008.

**Fecha**: 2026-11-09. **Rama real**: `main`.
**Capacidad activa de spec-kit**: `004-linea-tiempo`.

**Ensayo archivado 2026-11-13:** ruta incremental versionada evaluada. Su contrato
FR-CI/PR-CI, auditoría y decisiones se conservan en [incremental.md](incremental.md),
fuera del alcance obligatorio del juego.
El usuario eligió hash propio con vector inmutable. Están implementados el índice,
el registro de identidad con retiro, el capturador experimental y un observador
explícito por orden. El piloto verifica alias/ciclos, errores, marcas omitidas,
trazas reales, cinco undo, v6 y continuación. Evaluación cerrada con rechazo para
integración: producción conserva captura completa y K=10 elegido.
Índice inverso ID → entrada elegido e implementado; bajas con tumbas y copias
atómicas. Se optimizaron primer sondeo y observación de deltas; reserva privada
por salas medida separadamente. Evaluación en [el informe](../../documentacion/INDICE_INVERSO_JUAN.md).
**Entrada**: [spec.md](spec.md). **Estado**: implementado; K10 elegido y consulta
oficial conforme. Solo queda el cierre de 20 ms y la aceptación dependiente.
**Decisiones**: D-LT-01 a D-LT-06 elegidas por el usuario. D-LT-08 extiende los
puntos a registros inmutables por ID (elección explícita del 2026-11-12), con
reconstrucción del modelo y conversión al formato v6 al guardar/cargar.
El usuario eligió después compartir tokens de ID mediante catálogo inmutable
acotado de 16 384 entradas, con fallback a tokens propios y estado independiente
por punto. Su costo fijo se contabiliza aparte de la memoria marginal.
D-LT-07 fija K=10 por elección de Juan. Alternativas, mediciones previas y descartes
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
