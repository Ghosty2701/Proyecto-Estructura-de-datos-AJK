# Cripta — Parte II

## Inicio rápido (clonar y ejecutar)

Verificado el 2026-11-14 en un clon limpio desde GitHub, en Windows, con
PowerShell y desde la raíz del repositorio.

1. **Juego en consola y pruebas** (Python 3.11 o superior; probado con 3.13 y 3.14):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r documentacion/requirements.txt
   .\.venv\Scripts\python.exe -m pytest -q
   .\.venv\Scripts\python.exe main.py --listar
   .\.venv\Scripts\python.exe main.py --cripta cripta-02 --semilla 2026
   ```

   Sin Pygame pasan 819 pruebas y se omiten 5 módulos gráficos. El juego usa el
   servicio web del curso; `--listar` muestra las criptas disponibles.

2. **Interfaz gráfica opcional** (Pygame 2.6.1 requiere **Python 3.11 a 3.13**;
   no se instala en 3.14):

   ```powershell
   py -3.13 -m venv .venv313
   .\.venv313\Scripts\python.exe -m pip install -r documentacion/requirements-pygame.txt
   .\.venv313\Scripts\python.exe main.py --interfaz pygame
   ```

   Con Pygame pasan 866 pruebas.

3. **Sin red:** `--offline CARPETA` lee un paquete local con el mismo contrato del servicio.
   Para generar una cripta sintética de prueba:

   ```powershell
   .\.venv\Scripts\python.exe -c "from Pruebas.datos_graficos import paquete_grafico; paquete_grafico('resultados/manual/datos')"
   .\.venv\Scripts\python.exe main.py --offline resultados/manual/datos --cripta lt --semilla 2026
   ```


**Interfaz opcional Pygame (integrada en `main` el 2026-11-14):** RPG con estética
de 16 bits, habitación pixelada, personaje, enemigos, minimapa y combate animado
por turnos. [Seguimiento de la escena visual](specs/006-salas-combate-visual/README.md).
La consola sigue siendo la interfaz predeterminada y la entrega de Parte II no
cambia; el estado que sigue abajo no representa el avance de esta ampliación.

**Pygame: alcance actual completado (100 % estimado)**, con funcionalidades y arte
integrados; **866 pruebas aprobadas** con Pygame y **819 sin él** (cinco módulos
gráficos omitidos). Mediciones separadas, revisión interactiva de escritorio y
auditoría completadas; [evidencia y límites](documentacion/evidencia/exploracion_revision.md).
Es una ampliación personal,
independiente de la nota del proyecto. La base anterior de mapa se registra en
[005](specs/005-interfaz-pygame/README.md).

Para probar la versión local (pygame 2.6.1 no publica wheel para Python 3.14;
usar Python 3.13 en el entorno virtual):

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r documentacion/requirements-pygame.txt
```

```powershell
.\.venv\Scripts\python.exe main.py --interfaz pygame
```

Clic en sprites o puertas para seleccionar: aparece «Atacar», «Recoger»,
«Entrar» o «Abrir puerta». La vista normal tiene cuatro o cinco comandos;
inventario, mapa y menú agrupan las demás funciones. WASD cambia de sala,
espacio espera o salta el efecto activo; Esc abre/cierra el menú. Guardar,
cargar e historia están en Menú; animaciones en Menú → Opciones y ayuda.

Inicio separa Nueva partida y Cargar partida. Buscar criptas muestra una lista:
la elegida queda resaltada y se confirma por nombre/ID antes de Empezar partida.
Cargar permite buscar un `.bin` y confirmar; al cargar se recuperan nombre,
semilla y progreso. En pausa, Reanudar guardado actual abre el guardado de esa
sesión; Cargar otro archivo abre el selector. Una barra animada, descripción y
segundos transcurridos indican las operaciones pendientes. Inventario explica
el ordenamiento y muestra peso/valor. Los sprites de enemigos se eligen por
especie observable, independientemente del comportamiento.

El minimapa es más alto; clic para ampliarlo. La leyenda tenue WASD/H permite
consultar controles sin botones extra. El juego usa un indicador pequeño de
actividad en una esquina; el inicio conserva el aviso detallado. Las transiciones
de movimiento duran hasta 160/80 ms en modo normal/reducido. No se eliminan las
esperas inevitables de la fuente de datos. Integrada en `main` con aprobación
explícita del usuario; sin Pygame instalado, el juego y las pruebas base funcionan igual.

[Revisión nativa](documentacion/evidencia/exploracion_escritorio.md),
[inicio](documentacion/evidencia/inicio_claro.png),
[carga](documentacion/evidencia/carga_clara.png) y
[criaturas](documentacion/evidencia/criaturas_claras.png): renders de prueba.

[Captura del render actual](documentacion/evidencia/retro_jugable.png),
producida con vídeo de pruebas; no sustituye la revisión nativa completa.

Proyecto de Andrey, Juan y Kendall. Juego de consola con terreno ponderado,
cazadores, niebla y viaje automático, resolubilidad y consultas históricas.
Los datos proceden del servicio o de un paquete offline compatible.

**Estado:** cuatro capacidades implementadas; **K predeterminado 10**, elegido
por el grupo. **759 pruebas pasan**. El alcance funcional queda cerrado con
**excepcion de latencia EX-01**, autorizada por el usuario tras revisar los
intentos fallidos. La nueva corrida incumple 20 ms en 255/5 000 ciclos y
50 ms en 2/36 consultas; esos limites del enunciado no se declaran cumplidos.
[Estado y evidencia](documentacion/ESTADO_ENTREGA_P2.md),
[diagnostico y cierre](documentacion/REVISION_SESION_BLOQUEADA.md).

- [Decisiones de diseño](DECISIONES.md).
- [Prompts del equipo](PROMPTS_LLM.md).
- [Reanálisis de pendientes y trazabilidad del apéndice B](documentacion/REANALISIS_ENTREGA_P2.md).

## Instalación

Python **3.11 o superior**; regresión vigente con **Python 3.13.2**.
Desde la raíz, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r documentacion/requirements.txt
```

Usa el Python de ese entorno en los comandos siguientes.

## Jugar y verificar

```powershell
python main.py --listar
python main.py --cripta cripta-06 --semilla 2026
python main.py --verificar cripta-06
python main.py --cripta cripta-05 --forzar
python main.py --offline datos_offline --listar
python main.py --help
```

IDs, versiones y resolubilidad dependen del servicio. `--verificar` no crea
vista/partida: devuelve 0 para resoluble, 1 para no resoluble y 2 para error.
El inicio normal muestra el reporte y bloquea criptas no resolubles;
`--forzar` permite jugarlas sin omitir errores de datos. Cargar y replay
conservan sus validaciones sin repetir la verificación inicial.

| Comando | Acción |
|---|---|
| `w`, `a`, `s`, `d` | Moverse norte, oeste, sur y este pagando el costo de la salida. |
| `ver mapa` | Ver exploradas, avistadas y puertas recordadas. |
| `ir a <ID o nombre>` | Viajar por exploradas y salidas recordadas abiertas. |
| `atacar 1`, `recoger 1` | Actuar sobre enemigo u objeto indicado. |
| `inv`, `sig`, `ant` | Consultar inventario y seleccionar objetos. |
| `orden peso`, `orden valor`, `orden nombre` | Mostrar inventario ordenado. |
| `equipar`, `usar`, `soltar` | Actuar sobre el objeto seleccionado. |
| `abrir n`, `esperar` | Abrir con llave o esperar. |
| `retroceder` | Consumir pergamino y deshacer el último intervalo, hasta cinco acciones. |
| `historia <t>`, `historia #k` | Consultar el pasado sin modificar la partida. |
| `guardar`, `cargar` | Guardar/restaurar la sesión. |
| `ayuda`, `salir` | Mostrar ayuda o salir; salir no guarda automáticamente. |

Cada paso de viaje recalcula ruta y es una acción ordinaria. Se detiene al
llegar, entrar con enemigos, recibir daño o perder la ruta; no abre puertas.
Los nombres completos distinguen mayúsculas; repetidos requieren ID.
En Windows se permite interrumpir entre pasos y usar pergamino: revierte solo
el último y no reanuda el viaje. El teclado está probado con entrada inyectada;
no se certifica una sesión de teclado físico durante esta revisión.

La antorcha explora vecinas al entrar incluso tras puertas cerradas, sin
cargar contenido ni activarlas. El grupo eligió recordar sus puertas al
revelarlas; cambios remotos no se conocen hasta observar de nuevo.

## Guardado, replay e historia

```powershell
python main.py --cripta cripta-01 --semilla 2026 --bitacora partida.log
python main.py --cargar partida.bin
python main.py --replay partida.log
python main.py --replay partida.log --hasta 500
python main.py --cargar partida.bin --checkpoint-cada 25
python main.py --ver-puntajes --orden-puntajes tiempo
```

Formato **6**: conserva estado, retroceso, conocimiento e historia completa.
Formatos anteriores se rechazan explícitamente. El log debe ser nuevo y sus
versiones compatibles. Se puede guardar mientras se graba; cargar requiere
otra ejecución sin grabación. Predeterminados: `partida.bin`, `.cache_cripta/`
y `puntajes.json`; configurables con `--archivo-guardado`, `--cache-dir`,
`--cache-size` y `--puntajes`.

`--checkpoint-cada K` acepta enteros positivos. Sin opción, nuevas partidas y
replay usan **10**. Al cargar sin opción se conserva el K guardado; con otra
elección los puntos previos permanecen y el nuevo K rige desde la carga. Cada
tramo conserva su cota según la aclaración del grupo en el spec. `--hasta T`
requiere replay y un entero no negativo; muestra el resumen sin vista y avisa
si el registro/partida terminó antes.

## Pruebas y mediciones

```powershell
python -m pytest -q
python main.py --bench --repeticiones 1
python main.py --bench --repeticiones 1 --salida-bench resultados/defensa
python main.py --bench --cripta cripta-06 --repeticiones 1
```

`--bench` incluye por defecto los bloques de P2 §6.3: rutas, reutilización e
invalidación, mapa/viaje, resolubilidad, historia con varios K y solo punto
inicial, agenda/retroceso y reconstrucción/persistencia. Puede tardar varios
minutos. `--bench-linea-tiempo` permanece como alias compatible; no se necesita.

Los sintéticos no crean vista ni usan red. `--cripta` añade datos oficiales,
precargados fuera del cronómetro. Memoria y tiempos se miden por separado.
El cierre histórico exporta entorno, parámetros y resúmenes a
`resultados/bench/mediciones_linea_tiempo.json` y `bench_linea_tiempo.txt`, o
la carpeta indicada. Esa salida se ignora en Git y no sobrescribe evidencia
versionada por defecto. Un fallo de medición/exportación devuelve 1; terminar
una corrida sintética no certifica automáticamente sus límites.

Aceptación funcional de historia, carga y replay:

```powershell
python -m pytest -q Pruebas/prueba_linea_tiempo.py Pruebas/prueba_historia_partida.py Pruebas/prueba_limite_tiempo.py Pruebas/prueba_estado_binario.py Pruebas/prueba_bitacora_partida.py
```

[Estado actual](documentacion/ESTADO_ENTREGA_P2.md). Las corridas históricas se
conservan fechadas; los prototipos rechazados no forman parte de producción.

## Especificaciones y organización

**spec-kit 1.3.2**, con **Codex** (`.agents/skills/`) y **Claude Code**
(`.claude/skills/`), comparten `.specify/`. Constitución, comandos y artefactos
están versionados. Cada capacidad conserva spec, plan, tareas y trazabilidad:

- [Terreno y cazadores](specs/001-terreno-cazadores/tasks.md).
- [Niebla y viaje](specs/002-niebla-viaje/tasks.md).
- [Resolubilidad](specs/003-verificar-resolubilidad/tasks.md).
- [Línea de tiempo](specs/004-linea-tiempo/tasks.md).

`modelo/`: reglas y estructuras; `controlador/`: coordinación; `vista/`:
consola; `adaptadores/`: servicio y persistencia; `comun/`: ordenamientos;
`Pruebas/`: verificación automatizada. No se codifican criptas concretas en las reglas.
