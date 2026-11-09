# Cripta

Proyecto de Estructuras de Datos II de Andrey, Juan y Kendall. Juego de consola con reloj virtual, eventos, inventario, efectos, retroceso, guardado y replay. Los datos de las criptas proceden del servicio o de un paquete offline compatible.

La primera capacidad de Parte II ya incluye terreno ponderado y cazadores: los movimientos
usan el costo de la salida y los cazadores persiguen por costo mínimo dentro de su rango.
La consola muestra los costos y distingue a los cazadores. Niebla de guerra, viaje «ir a»,
resolubilidad y línea de tiempo todavía corresponden a capacidades pendientes.

Proceso SDD: **spec-kit 1.3.2**, agente **Codex**, configuración compartida en `.specify/`
y habilidades en `.agents/skills/`. Los artefactos de la primera capacidad están en
[specs/001-terreno-cazadores](specs/001-terreno-cazadores/plan.md).

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
python main.py --cripta cripta-01 --semilla 2026
python main.py --help
```

Elige un ID devuelto por `--listar`; `cripta-01` es un ejemplo cuya disponibilidad depende del servicio.

| Comando | Acción |
| --- | --- |
| `w`, `a`, `s`, `d` | Moverse al norte, oeste, sur y este. |
| `atacar 1`, `recoger 1` | Actuar sobre el enemigo u objeto indicado. |
| `inv`, `sig`, `ant` | Consultar el inventario y seleccionar objetos. |
| `orden peso`, `orden valor`, `orden nombre` | Mostrar una vista ordenada. |
| `equipar`, `usar`, `soltar` | Actuar sobre el objeto seleccionado. |
| `abrir n`, `esperar` | Abrir con la llave correspondiente o esperar. |
| `retroceder` | Consumir un pergamino y deshacer el último intervalo; hasta cinco disponibles. |
| `guardar`, `cargar` | Guardar o restaurar la sesión. |
| `ayuda`, `salir` | Mostrar comandos o terminar la sesión. |

Las consultas no consumen tiempo virtual. Al ganar o morir se registra un resultado; salir no guarda automáticamente. La vista conserva los últimos 20 mensajes.

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

El paquete oficial se proporciona aparte. Debe contener `criptas.json`, `catalogo_version.json`, fichas en `catalogo/ID.json` y, por cripta, `criptas/ID/general.json`, `version.json`, páginas `salas_N.json` y entradas `contenido/ID_SALA.json`. También puede combinarse con `--cargar`, `--replay` y `--bench`. La caché de fichas no sustituye ese paquete.

## Pruebas y mediciones

```powershell
python -m pytest -q
python main.py --bench
python main.py --bench --cripta cripta-01 --repeticiones 5
```

Se verificaron **469 pruebas** el 2026-11-09. El benchmark sin cripta usa cargas locales;
con cripta mide ciclos completos después de precargar datos, sin red ni renderizado
dentro del cronómetro. Devuelve código 1 si un ciclo alcanza 20 ms o la medición falla.
Cuando el mapa contiene cazadores, prepara hasta 32 de ellos activos antes de medir,
con sus posiciones y estadísticas originales; esa activación anticipada es una carga
experimental, no una regla nueva del juego.

En `cripta-06`, versión `f9ed9afa683d`, con 32 cazadores activos al inicio, semilla 2026
y cinco repeticiones, se midieron **225 ciclos**, máximo **15,1171 ms**, sin ciclos de
20 ms o más y usando **38/63 solicitudes**. Son resultados de esa carga y equipo,
no una garantía para cualquier recorrido. El benchmark también compara búsqueda
individual/compartida y reutilización/recálculo con puertas estables e inestables.
La estrategia del juego conserva las elecciones del equipo: Dijkstra individual,
heap indexado propio y tabla hash propia con doble hashing.

Pruebas de aceptación de terreno y cazadores:

```powershell
python -m pytest -q Pruebas/prueba_terreno.py Pruebas/prueba_rutas.py Pruebas/prueba_tabla_hash.py Pruebas/prueba_heap_rutas.py Pruebas/prueba_partida.py Pruebas/prueba_estado_binario.py Pruebas/prueba_bitacora_partida.py Pruebas/prueba_bench_adaptadores.py
```

El esquema binario del modelo pasa de versión 3 a **4**; los guardados anteriores
se rechazan explícitamente. Los costos y rangos se conservan; los resultados de búsqueda
derivados se descartan al cargar. Evidencia actual:
[pruebas](documentacion/evidencia/pruebas_terreno_cazadores.txt),
[comparaciones sintéticas](documentacion/evidencia/mediciones_terreno_cazadores.json) y
[referencia oficial](documentacion/evidencia/referencia_terreno_cazadores.json).
Las mediciones anteriores de P1 permanecen en su documentación histórica.

## Documentación

- [Decisiones de diseño](documentacion/DOCUMENTO_DECISIONES.md): alternativas, complejidades, resultados y límites.
- [Prompts del equipo](documentacion/PROMPTS_LLM.md): relevantes por integrante, con metadatos verificables y datos desconocidos indicados.
- [Pruebas](documentacion/evidencia/pruebas.txt) y [mediciones](documentacion/evidencia/mediciones.json): resultados de las ejecuciones de verificación.

Organización: `modelo/` contiene reglas y estructuras; `controlador/`, acciones y coordinación; `vista/`, consola; `adaptadores/`, red y persistencia; `comun/`, ordenamientos; `Pruebas/`, verificaciones.
