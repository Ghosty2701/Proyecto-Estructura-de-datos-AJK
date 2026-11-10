# Cripta

Proyecto de Estructuras de Datos II de Andrey, Juan y Kendall. Juego de consola con reloj virtual, eventos, inventario, efectos, retroceso, guardado y replay. Los datos de las criptas proceden del servicio o de un paquete offline compatible.

La primera capacidad de Parte II ya incluye terreno ponderado y cazadores: los movimientos
usan el costo de la salida y los cazadores persiguen por costo mínimo dentro de su rango.
La segunda capacidad incluye niebla de guerra, memoria de puertas, antorcha y viaje
«ir a» por el mapa conocido, con retroceso, guardado y replay. La tercera capacidad
verifica resolubilidad antes de iniciar, con consulta sin vista e informes de
bloqueos/ciclos. La línea de tiempo sigue pendiente.

Proceso SDD: **spec-kit 1.3.2**, agente **Codex**, configuración compartida en `.specify/`
y habilidades en `.agents/skills/`. Los artefactos de la primera capacidad están en
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
python main.py --ver-puntajes --orden-puntajes tiempo
```

El log debe ser nuevo y conservar versiones compatibles. Replay funciona sin interfaz ni interacción. Puedes guardar mientras grabas, pero para cargar debes iniciar otra ejecución sin grabación.

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

Se verificaron **492 pruebas** el 2026-11-09. El benchmark sin cripta usa cargas locales;
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

El esquema binario del modelo ahora es **5**; los guardados anteriores se rechazan
explícitamente. Conserva conocimiento, memoria de puertas y deltas; los índices y
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
