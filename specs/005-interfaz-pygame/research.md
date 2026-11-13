# Investigación técnica acotada — Interfaz con Pygame

**Fecha**: 2026-11-13. **Rama**: `005-interfaz-pygame`.
**Estado**: decisiones estándar revisadas; las elecciones D-IG-05/06/07 esperan
respuesta explícita del usuario. Las recomendaciones no se registran como aprobadas.
La investigación combina lectura de código/documentación y una sonda temporal
de serialización existente; no implementa la interfaz.

## D-IG-01 — Conservar una sola simulación y ejecución compartida

**Decisión técnica estándar**: mantener el modelo existente. La ventana no
ejecutará un segundo motor, ni calculará rutas propias, ni alterará el reloj
mediante tiempo real. `Controlador.procesar()` es la referencia para una
ejecución compartida, con registro canónico único. Su envoltorio público debe
seguir funcionando con `VistaConsola`.

**Evidencia local**: `controlador/controlador.py`, `Controlador._registrar`,
`procesar` y `_navegar_inventario`; `controlador/partida.py`, `estado`, `mapa`
e `historia`. El bucle `Controlador.ejecutar()` espera entrada textual: se
conserva para consola y no se utiliza como bucle de la ventana.

**Motivo**: reutilizar reglas y registros comprobados, conservando determinismo.
**Alternativas descartadas**: ejecutar directamente `Partida` desde botones
duplica validación/registro; hacer una vista que bloquee en `leer_comando()`
impide atender la ventana de forma continua.

**Detalle de inventario**: `sig`/`ant` no consumen turno, pero se registran para
replay. Un clic en un objeto debe emitir la navegación canónica correspondiente,
no asignar el cursor directamente. Ordenar cambia la vista, no el orden real.

## D-IG-02 — Dependencia gráfica opcional y versión de referencia

**Decisión técnica estándar**: planificar `pygame==2.6.1` en un archivo opcional
de requisitos, con importación diferida al elegir la interfaz gráfica. Usar
Python 3.13.2 y Windows x86-64 como entorno de referencia; conservar la
compatibilidad base de Python 3.11+ en los modos existentes.

**Evidencia externa**: [distribución oficial](https://pypi.org/project/pygame/2.6.1/).
El catálogo JSON de PyPI consultado el 2026-11-13 contiene
`pygame-2.6.1-cp313-cp313-win_amd64.whl`, SHA256
`813af4fba5d0b2cb8e58f5d95f7910295c34067dcc290d34f1be59c48bd1ea6a`.
Se comprobó la disponibilidad de metadatos, no una instalación ni una prueba gráfica.

**Alternativas**: hacer obligatoria la biblioteca rompe el propósito de los
modos sin gráficos. Cambiar a otro framework o a otra distribución no es necesario
para el entorno de referencia verificado. No se incorpora una biblioteca adicional
de widgets para esta primera versión.

## D-IG-03 — Ventana principal y propietario único de la sesión

**Decisión técnica estándar**: eventos y dibujo en el hilo que inicializa la
pantalla. Un único trabajador serializado posee la sesión, ejecuta operaciones
y publica presentaciones inmutables; la ventana no lee objetos vivos mientras
se modifican. Solo una operación en curso, sin cola de acciones acumuladas.
La sincronización usa primitivas estándar de `threading`, no un nuevo índice
de datos del juego. Las colecciones auxiliares se supeditan a D-IG-05.

**Motivo**: el cliente HTTP actual puede esperar diez segundos por intento y
respetar esperas 429. Bloquear el hilo de dibujo durante esas operaciones impide
atender el cierre. La documentación de [eventos](https://www.pygame.org/docs/ref/event.html)
exige atenderlos regularmente y liga su procesamiento al hilo de pantalla.

**Alternativas**: ejecutar todo en el hilo de pantalla es más sencillo pero
bloquea la ventana durante red/IO; varios trabajadores sobre la misma partida
introducen carreras. Una infraestructura de colas ilimitadas contradice el
requisito de no acumular órdenes.

**Cierre**: solicitar parada, cancelar esperas de red entre intentos, dejar
terminar una operación ya aceptada y liberar log/sesión. No matar un hilo mientras
escribe ni iniciar acciones nuevas al cerrar. La espera cancelable del cliente
será opcional y mantendrá el comportamiento actual por defecto.

## D-IG-04 — Viaje incremental y proyección permitida

**Decisión técnica estándar**: extraer una operación compartida de un paso de
`Partida.viajar()`. La consola seguirá consumiendo el viaje hasta terminar;
la aplicación gráfica solicitará un solo paso y atenderá eventos antes del
siguiente. No duplicar Dijkstra, costos ni condiciones de parada.

Preservar el orden: resolver ruta → mover → registrar el movimiento → publicar
observación/presentación → comprobar las paradas actuales. La orden de viaje
puede dejar un comentario; cada paso se registra una sola vez como `ir DIRECCIÓN`.

La vista recibirá `Partida.mapa()`/`ConocimientoMapa.proyeccion()`, nunca todas
las salas o actores físicos. Una proyección explícita de enemigos presentes
debe incluir identidad de objetivo y comportamiento, sin interpretar sufijos
de nombres para elegir sprites. La cámara y sus límites dependen solo del mapa
conocido; el tamaño del mundo oculto no se filtra mediante la distribución.

## D-IG-05 — Datos por sala y retroceso visual

**Estado**: PENDIENTE DE ELECCIÓN DEL USUARIO.

| Alternativa presentada | Ventaja | Costo o límite |
|---|---|---|
| Índice propio de salas + vectores por posición + cambios de cinco acciones | Consulta directa; reutilización de utilidades y retirada acotada de cambios | Reserva proporcional a salas y requiere reconstrucción/validación al cargar |
| Listas con búsqueda lineal + cambios de cinco acciones | Menos lógica y sin índice adicional | Consultas/búsquedas lineales al crecer el mapa |

**Recomendación, no decisión**: primera alternativa. Los IDs externos no son
posiciones contiguas; `IndiceSalas`, en `modelo/conocimiento.py`, ya ofrece la
traducción a posiciones densas. La selección deberá cubrir también los vectores
auxiliares de controles, disposición y sprites; no autoriza índices de `dict`/`set`.

**Contrato independiente de la elección**: conservar valores de observaciones,
no referencias a actores; registrar solo la sala actual al iniciar y tras
acciones aceptadas. No observar desde el dibujo ni desde la antorcha. Mantener
como máximo cinco deltas visuales, asociados a las acciones realmente reversibles,
no solo a su reloj. Tras cargar sin historial visual, un retroceso que cruce
su origen descarta observaciones inciertas y vuelve a observar solo la sala actual.

La consulta `historia` usa su propio resumen y mapa, sin superponer recuerdos
remotos del presente. No se necesita otro historial gráfico de 5 000 acciones.

## D-IG-06 — Persistencia compatible de recuerdos

**Estado**: PENDIENTE DE ELECCIÓN DEL USUARIO.

| Alternativa presentada | Ventaja | Costo o límite |
|---|---|---|
| Carga visual opcional de valores básicos en `datos_extra` del mismo v6 | Un archivo y sin versión nueva del modelo | Validar el contenido opcional; un re-guardado desde consola antigua pierde los recuerdos |
| Archivo `.gui.json` compañero | Separación total del binario | Vincularlo al guardado y gestionar archivos faltantes, copiados u obsoletos |

**Recomendación, no decisión**: primera alternativa. `estado_binario.py` ya
serializa datos adicionales básicos. `CargadorPartida.leer_sesion()` exige sus
campos conocidos pero no prohíbe una clave extra. `guardar_sesion()` reconstruye
los datos extra: la consola de la base ignoraría la clave y la eliminaría al
re-guardar. Una sonda temporal confirmó que el lector actual de sesión acepta
una clave primitiva adicional, y que el re-guardado de consola la descarta sin
alterar el estado básico. Todavía se debe probar la futura carga visual completa
contra el lector real de `main` antes de integrar.

No añadir clases o atributos gráficos a `Partida`, actores, conocimiento o
puntos históricos: el serializador rechaza campos sin esquema. Un contenido
visual semánticamente inválido se descarta sin rechazar el juego válido; eso
no garantiza recuperar un binario físicamente corrupto o truncado.

## D-IG-07 — Disposición de salas sin coordenadas

**Estado**: PENDIENTE DE ELECCIÓN DEL USUARIO.

| Alternativa presentada | Ventaja | Costo o límite |
|---|---|---|
| Croquis por N/S/E/O con conflictos señalados | Orientación más cercana al recorrido | Resolver ocupaciones y enlaces incompatibles; geometría esquemática |
| Cuadrícula por ID y conexiones explícitas | Más simple y estable | La vecindad visual no expresa necesariamente conectividad |

**Recomendación, no decisión**: croquis direccional. Ni `SalaRastro` ni el
esqueleto normalizado contienen coordenadas. Cualquiera de las dos opciones
solo usará salas/conexiones ya conocidas, sin revelar tamaños o zonas ocultas.

## D-IG-08 — Controles y presentación inicial

**Decisiones estándar**: ventana redimensionable, tamaño inicial 1280 × 800 y
mínimo útil 1024 × 768; mapa central, estado/objetivos e inventario en paneles,
acciones y mensajes visibles. Pan con arrastre y zoom de presentación sin turnos.
Botones para todas las operaciones; WASD/flechas para movimientos, espacio para
esperar, I inventario, M mapa, H historia, R retroceder, F5 guardar, F9 cargar
y F1 ayuda. Los campos de texto capturan sus teclas; no disparan acciones del juego.

Sprites originales sencillos, legibles a escala de casilla, con leyenda de
tipo/cantidad. Se crearán con las herramientas de dibujo de Pygame y no exigirán
descargar un paquete de arte. Los recuerdos se diferenciarán por marca textual
y estilo, además del color. No audio ni animación obligatoria.

## D-IG-09 — Validación proporcionada y continuidad

Conservar las 759 pruebas de base; crear pruebas de lógica sin inicializar
Pygame y de eventos/dibujo con controlador de vídeo de pruebas, más una revisión
visual real separada. El controlador de pruebas no demuestra legibilidad,
foco, teclado físico ni redimensionamiento en un escritorio real.

Comparar secuencias idénticas de consola/GUI, contador de registro, reloj,
azar y guardado/continuación. Cubrir permisos de niebla, antorcha, recuerdos,
cinco undo, bifurcación tras retroceso y carga antigua. Medir presentación y
acción por separado. La sincronización de cuadros limita dibujo, no programa
turnos: [reloj de presentación](https://www.pygame.org/docs/ref/time.html#pygame.time.Clock.tick).
EX-01 no se reabre ni se declara resuelta por esta ampliación.

## Fuentes y límites

- Código de la rama desde `4e20990`, leído el 2026-11-13.
- Documentación oficial de eventos, pantalla y reloj; distribución oficial de PyPI citadas arriba.
- Revisión de código y fuentes en paralelo según la fase de investigación de `$speckit-plan`; sin modificaciones de los revisores.
- No se han ejecutado pruebas de interfaz, instalado dependencias ni medido rendimiento gráfico. Las elecciones pendientes impiden declarar terminada la planificación.
