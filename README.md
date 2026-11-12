# Cripta

Estado actual de funcionalidad, evidencia y pendientes:
[revisión de entrega de Parte II](documentacion/ESTADO_ENTREGA_P2.md).
[Corrida conjunta y cierre documental independiente de K](documentacion/CIERRE_MEDICIONES_P2.md).

Proyecto de Estructuras de Datos II de Andrey, Juan y Kendall. Juego de consola con reloj virtual, eventos, inventario, efectos, retroceso, guardado y replay. Los datos de las criptas proceden del servicio o de un paquete offline compatible.

La primera capacidad de Parte II ya incluye terreno ponderado y cazadores: los movimientos
usan el costo de la salida y los cazadores persiguen por costo mínimo dentro de su rango.
La segunda capacidad incluye niebla de guerra, memoria de puertas, antorcha y viaje
«ir a» por el mapa conocido, con retroceso, guardado y replay. La tercera capacidad
verifica resolubilidad antes de iniciar, con consulta sin vista e informes de
bloqueos/ciclos. La línea de tiempo ya permite consultar historia, configurar
puntos y conservarlos al guardar/cargar. La corrida conjunta de mediciones ya
está ejecutada; quedan pendientes cumplir los límites de tiempo y elegir K.

Proceso SDD: **spec-kit 1.3.2** con dos integraciones instaladas sobre la misma
configuración compartida en `.specify/`: **Codex** (habilidades en `.agents/skills/`) y
**Claude Code** (habilidades en `.claude/skills/`). Ambos agentes leen la misma constitución,
plantillas y scripts; cada integrante usa el suyo. Los artefactos de la primera capacidad están en
[specs/001-terreno-cazadores](specs/001-terreno-cazadores/plan.md); la segunda está en
[specs/002-niebla-viaje](specs/002-niebla-viaje/plan.md).
La especificación de resolubilidad está en
[specs/003-verificar-resolubilidad](specs/003-verificar-resolubilidad/spec.md),
con [planificación completada](specs/003-verificar-resolubilidad/plan.md) y
[guía de validación](specs/003-verificar-resolubilidad/quickstart.md).
Las [tareas de resolubilidad](specs/003-verificar-resolubilidad/tasks.md) están
completadas: `--verificar` y `--forzar` están implementados y verificados.

## Instalación

Python 3.11 o superior; probado con **Python 3.14.6**. Desde la raíz, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r documentacion/requirements.txt
```

En los comandos siguientes usa el Python de ese entorno, o sustituye `python` por `.\.venv\Scripts\python.exe`.

## Ejecutar

```powershell
python main.py --listar
python main.py --cripta cripta-06 --semilla 2026
python main.py --verificar cripta-06
python main.py --cripta cripta-05 --forzar
python main.py --help
```

Elige un ID devuelto por `--listar`; la disponibilidad y versiones dependen del
servicio. En la validación de 2026-11-09, cripta-06 fue resoluble y cripta-05 no.
`--verificar` no crea vista ni partida: devuelve 0 para resoluble, 1 para no
resoluble y 2 para error. No se combina con otros modos ni `--forzar`.
Un inicio normal imprime el informe y bloquea una cripta no resoluble;
`--forzar` permite jugarla, sin cambiar las reglas ni saltar errores de datos.
Cargar y replay mantienen sus validaciones sin repetir esta verificación.

| Comando | Acción |
| --- | --- |
| `w`, `a`, `s`, `d` | Moverse al norte, oeste, sur y este. |
| `ver mapa` | Ver únicamente salas exploradas, avistadas y puertas recordadas. |
| `ir a <ID o nombre>` | Viajar por exploradas y salidas recordadas abiertas. Nombre completo sensible a mayúsculas; repetidos requieren ID. |
| `atacar 1`, `recoger 1` | Actuar sobre el enemigo u objeto indicado. |
| `inv`, `sig`, `ant` | Consultar el inventario y seleccionar objetos. |
| `orden peso`, `orden valor`, `orden nombre` | Mostrar una vista ordenada. |
| `equipar`, `usar`, `soltar` | Actuar sobre el objeto seleccionado. |
| `abrir n`, `esperar` | Abrir con la llave correspondiente o esperar. |
| `retroceder` | Consumir un pergamino y deshacer el último intervalo; hasta cinco disponibles. |
| `historia <t>`, `historia #k` | Consultar el estado pasado por instante o antes de la acción k, sin modificar la partida. |
| `guardar`, `cargar` | Guardar o restaurar la sesión. |
| `ayuda`, `salir` | Mostrar comandos o terminar la sesión. |

Las consultas no consumen tiempo virtual. Al ganar o morir se registra un resultado; salir no guarda automáticamente. La vista conserva los últimos 20 mensajes.

Cada paso del viaje es un movimiento ordinario y recalcula la ruta. Se detiene
al llegar, entrar con enemigos, recibir daño o perder la ruta conocida; no abre
puertas. En consola Windows, empezar a escribir interrumpe entre pasos y permite
dar otro comando, incluido `retroceder`: revierte solo el último paso y no reanuda
el viaje. No hay confirmaciones obligatorias por paso. La detección de teclado
se prueba mediante entrada inyectada; no se ha verificado manualmente una sesión
de teclado físico durante esta ejecución.

La antorcha revela vecinas al entrar incluso tras puertas cerradas, sin contenido
ni activación remota. Según la interpretación elegida por el equipo, registra
también el estado de sus puertas reveladas. Un cierre remoto posterior no cambia
el recuerdo hasta una nueva observación. El conocimiento se revierte con pergamino.

## Guardado y replay

```powershell
python main.py --cargar partida.bin
python main.py --cripta cripta-01 --semilla 2026 --bitacora partida.log
python main.py --replay partida.log
python main.py --replay partida.log --hasta 500
python main.py --cargar partida.bin --checkpoint-cada 50
python main.py --ver-puntajes --orden-puntajes tiempo
```

El log debe ser nuevo y conservar versiones compatibles. Replay funciona sin interfaz ni interacción. Puedes guardar mientras grabas, pero para cargar debes iniciar otra ejecución sin grabación.

`--checkpoint-cada K` admite enteros positivos al iniciar, cargar o reproducir.
El valor actual **25 es provisional**; no se presenta como una decisión final.
Al cargar sin esa opción se conserva el K guardado; con otro K, los puntos
anteriores permanecen y el nuevo valor rige desde la carga. `--hasta T` requiere
`--replay` y un entero no negativo. Imprime el resumen histórico sin crear la
vista y avisa si el registro o la partida terminaron antes de T.

Rutas predeterminadas: `partida.bin` para guardados, `puntajes.json` para resultados y `.cache_cripta/` para fichas. Se cambian con `--archivo-guardado`, `--puntajes` y `--cache-dir`. `--nombre` define el nombre del jugador y `--cache-size` el tope estricto de fichas residentes (25 por defecto). Si una acción necesita más fichas protegidas de las que caben, se rechaza antes de avanzar el reloj e indica la capacidad necesaria; puedes guardar y reanudar con un tope mayor.

`--ver-puntajes` consulta el archivo local sin conexión. `--orden-puntajes` acepta `tiempo`, `acciones`, `enemigos` o `nombre`; agrupa por cripta, versión y resultado, conserva los empates y no reescribe el historial. La reserva de solicitudes orienta la precarga; todas las consultas y reintentos comparten el presupuesto real del servidor.

## Offline

```powershell
python main.py --offline datos_offline --listar
python main.py --offline datos_offline --cripta cripta-01
```

El paquete oficial se proporciona aparte. Debe contener `criptas.json`, `catalogo_version.json`, fichas en `catalogo/ID.json` y, por cripta, `criptas/ID/general.json`, `version.json`, páginas `salas_N.json` y entradas `contenido/ID_SALA.json`. Verificar/iniciar requiere además `criptas/ID/llaves.json`, con la respuesta equivalente del servicio; no se infiere descargando contenido. También puede combinarse con `--cargar`, `--replay` y `--bench`. La caché de fichas no sustituye ese paquete.

## Pruebas y mediciones

```powershell
python -m pytest -q
python main.py --bench
python main.py --bench --cripta cripta-01 --repeticiones 5
```

La regresión actual del 2026-11-11 aprobó **663 pruebas**
([salida](documentacion/evidencia/pruebas_linea_tiempo.txt)). La aceptación
histórica de niebla registró 492 pruebas el 2026-11-09.
El benchmark sin cripta usa cargas locales;
con cripta mide ciclos completos después de precargar datos, sin red ni renderizado
dentro del cronómetro. Con cripta devuelve código 1 si un ciclo alcanza 20 ms,
un cálculo de «ir a» alcanza 5 ms o la medición falla.
Cuando el mapa contiene cazadores, prepara hasta 32 de ellos activos antes de medir,
con sus posiciones y estadísticas originales; esa activación anticipada es una carga
experimental, no una regla nueva del juego.

En `cripta-06`, versión `f9ed9afa683d`, con 32 cazadores activos al inicio, semilla 2026
y cinco repeticiones, la corrida final midió **225 ciclos**, máximo **18,6757 ms**,
sin ciclos de 20 ms o más y usando **39/63 solicitudes**. Son resultados de esa carga y equipo,
no una garantía para cualquier recorrido. El benchmark también compara búsqueda
individual/compartida y reutilización/recálculo con puertas estables e inestables.
La estrategia del juego conserva las elecciones del equipo: Dijkstra individual,
heap indexado propio y tabla hash propia con doble hashing.

Niebla añade **3 000 cálculos** sobre el mapa conocido completo (300 salas):
máximo **2,1130 ms**, ninguno ≥5 ms. Se distinguen puertas observadas y una carga
de estrés con recuerdos abiertos y puertas físicas intactas; la primera no tenía
rutas entre los destinos ensayados y por eso se añadió la segunda. La revelación
local produjo ocho actualizaciones tanto con 80 como con 8 000 salas. En otra
corrida sintética de 500 ciclos de cazadores hubo un máximo **21,7271 ms**, con un
ciclo ≥20 ms; se conserva como límite observado, sin ocultarlo tras la referencia.

Pruebas de aceptación de terreno y cazadores:

```powershell
python -m pytest -q Pruebas/prueba_terreno.py Pruebas/prueba_rutas.py Pruebas/prueba_tabla_hash.py Pruebas/prueba_heap_rutas.py Pruebas/prueba_partida.py Pruebas/prueba_estado_binario.py Pruebas/prueba_bitacora_partida.py Pruebas/prueba_bench_adaptadores.py
```

Aceptación de niebla y viaje:

```powershell
python -m pytest -q Pruebas/prueba_conocimiento.py Pruebas/prueba_rutas_conocidas.py Pruebas/prueba_niebla_partida.py Pruebas/prueba_bitacora_partida.py Pruebas/prueba_estado_binario.py Pruebas/prueba_bench_adaptadores.py
```

El esquema binario del modelo ahora es **6**; los guardados anteriores se rechazan
explícitamente. Conserva la línea completa (órdenes, acciones, tramos y todos los
puntos), conocimiento, memoria de puertas y deltas; los índices y
auxiliares de búsqueda se reconstruyen al cargar. El log registra `# ir a ...`
como comentario y cada paso como movimiento; replay ignora el comentario.
Evidencia actual de niebla: [pruebas](documentacion/evidencia/pruebas_niebla.txt),
[mediciones](documentacion/evidencia/mediciones_niebla.json) y
[salidas de bench](documentacion/evidencia/bench_niebla.txt).
Evidencia histórica de terreno, antes de niebla:
[pruebas](documentacion/evidencia/pruebas_terreno_cazadores.txt),
[comparaciones sintéticas](documentacion/evidencia/mediciones_terreno_cazadores.json) y
[referencia oficial](documentacion/evidencia/referencia_terreno_cazadores.json).
Las mediciones anteriores de P1 permanecen en su documentación histórica.

Mediciones de persistencia de Juan (T029/T030 de `004-linea-tiempo`):

```powershell
python -m adaptadores.bench_adaptadores --solo persistencia --acciones 5000 --salas 200 --rondas 3 --semilla 2026 --salida-json documentacion/evidencia/mediciones_persistencia_juan.json
python -m pytest -q Pruebas/prueba_bench_persistencia.py Pruebas/prueba_estado_binario.py Pruebas/prueba_bitacora_partida.py
```

Compara K = 10, 25, 50 y 100: tamaño del archivo, tiempos completos de guardado
y carga con todos los puntos, y copia propia frente a ida y vuelta binaria en
memoria. Verifica registro histórico, consultas y continuación fuera del
cronómetro. La carga usa costos variables y un pergamino, sin cazadores ni HTTP;
no certifica el límite de 50 ms por consulta o de 20 ms por ciclo. Conserva las
estadísticas resumidas y declara los límites del ensayo. Es un modo optativo;
su integración con el benchmark completo de línea de tiempo corresponde a T032.
Evidencia: [resultados](documentacion/evidencia/mediciones_persistencia_juan.json)
y [salida](documentacion/evidencia/bench_persistencia_juan.txt).

Mediciones de consultas históricas de Juan (tramo de T029/T033):

```powershell
python -m adaptadores.bench_adaptadores --solo consultas --acciones 5000 --salas 200 --rondas 3 --semilla 2026 --muestras 12 --cazadores 0 32 --salida-json documentacion/evidencia/mediciones_consultas_juan.json
python -m adaptadores.bench_adaptadores --solo consultas --cripta cripta-06 --acciones 5000 --rondas 3 --semilla 2026 --muestras 12 --salida-json documentacion/evidencia/mediciones_consultas_referencia_juan.json
python -m pytest -q Pruebas/prueba_bench_linea_tiempo.py
```

El primer comando compara K = 10/25/50/100 con conservar únicamente el punto
inicial, con 0 y 32 cazadores sintéticos activos. Alterna `historia #k`, instantes
exactos e intermedios repartidos por la historia; incluye consultas cercanas al
límite K y al estado actual. Guarda cantidad de muestras, mínimo, mediana, p95
(rango más cercano), máximo y cantidad de consultas ≥50 ms. El cronómetro incluye
copia, re-simulación y construcción del resumen; excluye validaciones extra,
preparación, red y renderizado. El recolector de basura permanece habilitado.

El segundo comando consume solicitudes del servicio al precargar los datos.
Usa el K provisional, conserva estadísticas/posiciones originales de enemigos
y prepara hasta 32 cazadores activos, con vida experimental del jugador de
10^9 para completar 5 000 acciones. No entra a la sala de salida. Si la partida
termina antes, lo informa con la cantidad alcanzada. Las consultas se miden
después de precargar y se comprueba que no generen solicitudes.

En la carga sintética con 32 cazadores, K = 25 registró **6/36 consultas ≥50 ms**
(máximo 63,502 ms). K = 10 no excedió el límite en esa corrida; esto no justifica
su elección sin medir memoria/ciclo y la referencia. **K no se cambió.** La
alternativa sin puntos periódicos alcanzó 3 121,560 ms. Ver
[muestras sintéticas](documentacion/evidencia/mediciones_consultas_juan.json) y
[salida](documentacion/evidencia/bench_consultas_juan.txt).
En `cripta-06` (300 salas, versión `f9ed9afa683d`, 32 cazadores activos al
inicio) se completaron 5 000 acciones con K = 25: **27/36 consultas ≥50 ms**,
mediana 90,112 ms y máximo 195,992 ms. Preparación: 46/63 solicitudes;
consultas: cero solicitudes, partida intacta. **El límite de 50 ms sigue sin
cumplirse en esa carga.** Evidencia de
[referencia](documentacion/evidencia/mediciones_consultas_referencia_juan.json)
y [salida](documentacion/evidencia/bench_consultas_referencia_juan.txt).
Estos modos siguen siendo optativos hasta completar la integración de T032.

Resolubilidad: **556 pruebas** en la regresión completa. En la mayor cripta
publicada al medir (cripta-06, 300 salas, versión `f9ed9afa683d`), 25 verificaciones
locales dieron un máximo **7,5888 ms**, ninguna ≥200 ms, con **10/63 solicitudes**.
Incluye preparación, cierre, diagnóstico cuando aplica y construcción del texto;
excluye red e impresión/vista. No se descargó contenido ni catálogo de entidades.
La consulta publicada de cripta-05 devolvió código 1 con grupo y ciclo concreto.
Las cargas sintéticas incluyen cadenas, muchos grupos y alternativas; los
contadores de cierre crecen linealmente y la cadena de 640 salas compara
**2 557 operaciones** incrementales con **1 229 438** del cierre repetido.
La referencia lenta solo mide cierre/veredicto, sin certificados; no se afirma
que sea más rápida para toda carga ni se garantiza el tiempo en cualquier equipo.
Evidencia: [pruebas](documentacion/evidencia/pruebas_resolubilidad.txt),
[mediciones](documentacion/evidencia/mediciones_resolubilidad.json),
[salidas de bench](documentacion/evidencia/bench_resolubilidad.txt) y
[entrada oficial capturada](documentacion/evidencia/entrada_resolubilidad_oficial.json).

## Documentación

- [Decisiones de diseño](documentacion/DOCUMENTO_DECISIONES.md): alternativas, complejidades, resultados y límites.
- [Prompts del equipo](documentacion/PROMPTS_LLM.md): relevantes por integrante, con metadatos verificables y datos desconocidos indicados.
- [Auditoría de integridad](documentacion/evidencia/auditoria_integridad_2026-11-09.md): estado revisado, correcciones y límites de la verificación.
- [Pruebas](documentacion/evidencia/pruebas.txt) y [mediciones](documentacion/evidencia/mediciones.json): resultados de las ejecuciones de verificación.

Organización: `modelo/` contiene reglas y estructuras; `controlador/`, acciones y coordinación; `vista/`, consola; `adaptadores/`, red y persistencia; `comun/`, ordenamientos; `Pruebas/`, verificaciones.

Medición separada de memoria y creación de puntos (T029):

```powershell
python -m adaptadores.bench_adaptadores --solo memoria --acciones 5000 --salas 200 --rondas 1 --semilla 2026 --cazadores 0 32 --salida-json documentacion/evidencia/mediciones_memoria_juan.json
```

Usa los mismos K y cargas que consultas, más solo el punto inicial. La memoria
se mide una vez con `tracemalloc`, desde antes de construir el cargador, y se
registra a mitad/final tras GC y como pico. Incluye infraestructura y puntos;
son asignaciones Python, no RSS del proceso. Los tiempos se miden en otra
partida equivalente sin trazado: copias periídicas (sin el punto inicial) y
ciclos que incluyen acción, registro y copia cuando corresponde. Se conservan
las estadísticas y la cantidad de ciclos ≥20 ms. No elige K ni certifica la referencia oficial.
Resultados: [JSON](documentacion/evidencia/mediciones_memoria_juan.json) y
[salida](documentacion/evidencia/bench_memoria_juan.txt).


Comparaciones pendientes de diseño, ahora medidas (T030/T031):

```powershell
python -m modelo.bench_decisiones --salida-json documentacion/evidencia/mediciones_decisiones_juan.json
python main.py --bench --repeticiones 1
```

`--bench` incluye agenda/retroceso de P2 y las alternativas de reconstrucción.
Para ejecutar y exportar conjuntamente los bloques de medición de la línea de tiempo (puede
tardar bastantes minutos, incluidos memoria, consultas y persistencia):

```powershell
python main.py --bench --bench-linea-tiempo --repeticiones 1
```

Genera `documentacion/evidencia/bench_linea_tiempo.txt` y
`mediciones_linea_tiempo.json` con mediciones nuevas. La ruta conjunta está
probada y la corrida conjunta terminó: resultados y entorno en el
[informe de cierre](documentacion/CIERRE_MEDICIONES_P2.md). Por indicación de Juan, la
optimización de consultas de 50 ms se atiende al final. También siguen
pendientes el presupuesto de 20 ms y la elección justificada de K.
Trazabilidad para defensa: [matriz](specs/004-linea-tiempo/trazabilidad.md).

Pruebas de aceptación de línea de tiempo, guardado y replay:

```powershell
python -m pytest -q Pruebas/prueba_linea_tiempo.py Pruebas/prueba_copia_estado.py Pruebas/prueba_historia_partida.py Pruebas/prueba_limite_tiempo.py Pruebas/prueba_estado_binario.py Pruebas/prueba_bitacora_partida.py Pruebas/prueba_partida.py
```

La regresión completa se ejecuta con `python -m pytest -q`. Los resultados
funcionales aprobados no significan que se cumplan los límites de 20/50 ms.
