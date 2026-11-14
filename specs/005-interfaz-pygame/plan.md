# Plan de implementación: Interfaz gráfica con Pygame

**Rama**: `005-interfaz-pygame` | **Fecha**: 2026-11-13 | **Spec**: [spec.md](spec.md).
**Entrada**: Capacidad adicional de escritorio, independiente de la entrega académica.
**Estado**: planificación técnica completada. Elecciones del usuario registradas;
modelo de datos, contratos y guía de validación preparados. Listo para descomponer
en tareas; código y pruebas gráficas todavía no implementados.

## Resumen

Agregar una presentación de mapa, sprites y paneles al motor existente. Conservar
la consola, los modos sin vista, el determinismo y el reloj por acciones. Separar
el ciclo de ventana de la ejecución serializada de una sola sesión; compartir
validación, órdenes, registro y cada paso del viaje. Mostrar solo conocimiento
permitido y observaciones presenciales, con deshacer visual acotado.

Las alternativas y sus fuentes están en [research.md](research.md). El usuario
eligió índice propio con vectores y cambios por turno, recuerdos opcionales
dentro del `.bin` v6 y croquis por N/S/E/O con conflictos señalados.

## Contexto técnico

- **Lenguaje**: Python 3.11+; referencia local de validación Python 3.13.2.
- **Dependencias**: base existente; Pygame 2.6.1 opcional, sin otra biblioteca de widgets.
- **Plataforma**: Windows x86-64; ventana redimensionable, 1280 × 800 inicial y mínimo útil 1024 × 768.
- **Tipo de aplicación**: escritorio con motor MVC y alternativa de consola.
- **Datos de juego**: servicio actual o paquete offline compatible; no incluir criptas concretas en producción.
- **Persistencia**: guardado v6 con clave visual opcional en `datos_extra`, sin archivo compañero (D-IG-06).
- **Auxiliares del mapa/recuerdos**: `IndiceSalas` propio, vectores y hasta cinco deltas visuales (D-IG-05).
- **Disposición del mapa**: croquis cardinal determinista; ocupación en vectores y enlaces conflictivos marcados (D-IG-07).
- **Pruebas**: pytest existente, comparaciones consola/GUI y pruebas gráficas controladas; revisión visual de escritorio independiente.
- **Escala**: 300 salas conocidas, siete historias y 23 escenarios; cinco acciones reversibles y registro histórico existente.
- **Objetivo de presentación**: límite de dibujo de 60 cuadros/s para no ocupar CPU innecesariamente; objetivo técnico, no promesa medida ni temporizador de turnos.
- **Restricciones**: sin segunda simulación, sin revelar mundo remoto, sin índices `dict`/`set`, sin `heapq`/`bisect`/bibliotecas de grafos. EX-01 permanece declarada.

## Comprobación constitucional

| Regla | Comprobación previa al diseño | Estado |
|---|---|---|
| I: estructuras manuales | D-IG-05 elegida; índice propio y vectores, sin índices de bibliotecas; transporte de primitivas no sustituye estructuras evaluadas | Conforme al diseño aprobado |
| II: determinismo | Un propietario del modelo; órdenes y azar canónicos; tiempo gráfico sin efecto de juego | Conforme al diseño estándar |
| III: MVC y modos sin vista | Pygame solo en presentación; importar únicamente al elegir gráficos | Conforme al diseño estándar |
| IV: datos externos | No mapas precalculados ni colocación basada en información oculta | Conforme al diseño estándar |
| V: presupuesto, versiones y guardado | D-IG-06 elegida; mantener v6, presupuestos/caché y lectura con/sin recuerdos | Conforme al contrato; pruebas completas futuras |
| VI: rendimiento respaldado | Medir acción y presentación por separado; ninguna afirmación nueva de latencia | Conforme; medición futura |
| VII: especificar antes de implementar | Spec publicado en `560ae0d`; este plan y sus contratos preceden al código | Conforme |
| VIII: trazabilidad | Los 23 escenarios tienen evidencia propuesta en la matriz; tareas detalladas en la fase siguiente | Conforme al diseño |
| IX: prompts y proceso | Solicitud, elecciones y uso de `$speckit-plan` registrados en la bitácora | Conforme |
| AGENTS.md | Elecciones explícitas del usuario en D-IG-05/06/07; avance exclusivo de Pygame | Conforme |

**Puerta previa**: completada tras resolver las tres elecciones; ninguna
aclaración técnica pendiente ni excepción constitucional nueva.
**Puerta posterior**: modelo y contratos revisados contra las reglas anteriores;
sin desviaciones de diseño. Esto no acredita pruebas de la implementación futura.

## Arquitectura estándar propuesta

### Aplicación y sesiones

La aplicación gráfica administra inicio, selección/verificación de cripta,
forzar de forma explícita, carga, juego, historia, ayuda y resultados. `main.py`
conservará su comportamiento por defecto y añadirá `--interfaz pygame` como
entrada explícita. Sin `--cripta` ni `--cargar`, gráficos abre el menú; con esos
argumentos, prepara la sesión indicada. `--interfaz consola` conserva la entrada
actual y sus validaciones. Las combinaciones gráficas con replay, verificar,
listar, puntajes de CLI, `--sin-interfaz` o bench se rechazan antes de inicializar la ventana.
Los puntajes gráficos se consultan desde el menú de la aplicación.

Extraer de `main.py` la preparación/finalización de sesión reutilizable, sin
importaciones gráficas. No iniciar una sesión real antes de verificar sus datos.
Preparar una carga candidata antes de reemplazar la sesión activa y no perder
la sesión válida si la candidata falla. Administrar log y registro único de
resultado por sesión, también cuando se vuelve al inicio sin cerrar la ventana.

### Ventana, trabajador y exclusión de órdenes

La ventana procesa los eventos, dibuja la última presentación confirmada y
traduce botones a intenciones. Un trabajador con propiedad exclusiva del modelo
ejecuta una operación por vez y devuelve valores de presentación sin referencias
a actores, inventario o salas vivas. No leer el modelo desde el dibujo.

Un buzón de capacidad una operación, protegido por sincronización estándar,
es suficiente; no se construye una cola de acciones. Durante trabajo normal se
descartan nuevas acciones y se muestran controles ocupados. Se atienden cierre,
redimensionamiento y navegación de presentación que no requieren consultar el
modelo. El cierre detiene nuevas operaciones y espera la liberación segura de
recursos; la espera cancelable de red no cambia presupuestos ni tiempo virtual.

### Ejecución compartida y selección

Conservar `Controlador.procesar()` como entrada compatible y extraer o exponer
su resultado estructurado: acción, retroceso, consulta, rechazo, carga, salida y mensajes.
Así el trabajador distingue una carga de una acción sin analizar texto de errores.
No registrar desde la vista. Un clic de inventario emite `sig`/`ant` según
corresponda; un orden visual no cambia el cursor ni el orden físico por accidente.

La vista que recibe el controlador dentro del trabajador será un receptor de
valores sin Pygame: recopila mensajes, inventario, mapa e historia. La vista
gráfica real solo dibuja esos resultados en el hilo principal.

La presentación tiene generación de sesión y revisión. Una intención contiene
esa revisión y un objetivo identificado por actor/dirección/destino o posición
real de inventario/suelo. Rechazar revisiones obsoletas para no atacar o usar otro
objeto. No interpretar el texto del nombre para extraer identificadores o tipos.

El retroceso se clasifica por el resultado real de la operación: también `usar`
un pergamino reduce el contador y requiere restaurar memoria. No decidirlo solo
por el nombre `retroceder` del botón. Una carga se distingue explícitamente de
cualquier variación de contadores de una acción.

### Viaje reanudable

Extraer la operación de un paso del viaje existente, sin duplicar búsqueda de
rutas ni costo/condiciones. Consola la ejecuta secuencialmente; gráficos solicita
un paso cuando termina el anterior, publica su resultado y vuelve a procesar
eventos antes de solicitar otro. El comentario de viaje no se convierte en turno.

Permitir una única intención interruptora explícita durante el viaje, además
de detener/cerrar. Se ejecuta una vez después del paso ya aceptado, antes de
cualquier paso nuevo. Su revisión se revalida/rebasa por identidad del objetivo
en la misma generación; no se rechaza automáticamente solo porque el paso haya
publicado otra revisión. No es una cola de acciones ni permite acumular pulsaciones.
Retroceder no reanuda el recorrido. Al perder foco se cancela la programación
del siguiente paso y la intención interruptora aún no ejecutada. Reanudar
requiere una nueva orden de viaje, sin repetir el paso ya aceptado.

### Información gráfica permitida

Un proyector sin Pygame produce el estado actual, inventario y mapa conocido.
La identidad/tipo de enemigos actuales se obtiene de los enemigos presentes;
no se entrega a la vista la lista física de enemigos de toda la cripta.

La memoria visual pertenece a la sesión gráfica y conserva solo observaciones
de la sala actual. El historial de juego continúa independiente. El panel
histórico presenta el `ResumenHistorico` y su mapa, sin reutilizar recuerdos
remotos presentes. La antorcha revela conocimiento de salas/puertas, no
observaciones nuevas de contenido. D-IG-05/06 definen su representación y transporte.

## Estructura del proyecto prevista

### Documentación de la capacidad

```text
specs/005-interfaz-pygame/
  spec.md
  plan.md
  research.md
  data-model.md            # entidades, estructuras y transiciones aprobadas
  contracts/
    interfaz-grafica.md    # ventana, comandos, proyección y viaje
    recuerdos-v6.md        # recuerdos, undo y compatibilidad
  quickstart.md            # guía de validación futura
  checklists/requirements.md
  README.md
```

`tasks.md` corresponde a `$speckit-tasks`, después de este plan. No se crean
tareas de implementación ni se marca código inexistente como completado.

### Código futuro, no creado por este plan

```text
main.py                              # selección opcional e importación diferida
controlador/controlador.py           # ejecución/registro compartidos y resultado
controlador/partida.py                # paso de viaje compartido y proyección actual
controlador/sesion.py                 # preparar/finalizar sesión sin vista
controlador/controlador_grafico.py    # coordinación serializada y ciclo de sesión
controlador/proyeccion_grafica.py     # valores observables y revisión de selección
controlador/disposicion_mapa.py       # croquis puro sobre conocimiento, sin Pygame
controlador/memoria_visual.py         # observaciones y deshacer visual, tras D-IG-05
adaptadores/estado_grafico.py         # validación/transporte, tras D-IG-06
controlador/cargar_partida.py         # extensión opcional del cargador existente
adaptadores/cliente_http.py           # cancelación opcional de espera, defaults iguales
vista/pygame_ui/
  aplicacion.py                       # eventos y escenas de ventana
  componentes.py                      # paneles, botones, listas y campos
  mapa.py                             # dibujo/cámara y disposición aprobada
  sprites.py                          # imágenes originales y leyenda
documentacion/requirements-pygame.txt  # instalación gráfica opcional
Pruebas/prueba_sesion_grafica.py
Pruebas/prueba_memoria_visual.py
Pruebas/prueba_guardado_grafico.py
Pruebas/prueba_mapa_grafico.py
Pruebas/prueba_eventos_pygame.py
Pruebas/prueba_cli_pygame.py
Pruebas/datos_graficos.py             # cargas sintéticas reutilizables, sin HTTP
```

Los nombres anticipan responsabilidades, no implican implementación. No se
creará un paquete alternativo de motor, inventario, rutas ni guardado completo.

## Complejidad y riesgos

Sin desviaciones constitucionales justificadas. Mantener un trabajador y
presentaciones copiadas limita concurrencia; no introduce simulaciones paralelas.
Las estructuras y costos están en [data-model.md](data-model.md): observaciones
O(V + T), cinco deltas y croquis O(S² + E) esperado al construir. Se contemplan
ocupaciones conflictivas, IDs dispersos y cinco undo tras cargar. La carga v6
visual usa primitivas opcionales, no tipos nuevos en el modelo. Su matriz de
lectura cruzada es obligatoria antes de integrar código.

## Cobertura prevista antes de descomponer en tareas

| Escenarios | Evidencia a implementar | Responsabilidad |
|---|---|---|
| AC-IG-001/002/003/021/023 | Inicio, verificación/forzar, carga candidata, modo offline, resultado único y errores | `prueba_sesion_grafica.py` |
| AC-IG-004/005/006/008/020 | Proyección permitida, objetivos/sprites, antorcha, ocupaciones, IDs dispersos y mapa de 300 salas | `prueba_mapa_grafico.py` |
| AC-IG-007/008/015/016 | Recuerdos remotos, consulta sin futuro, cinco undo y nueva rama tras retroceder | `prueba_memoria_visual.py` |
| AC-IG-009/010/011/012/013/014 | Acciones, navegación de inventario, repetición, viaje, interrupción y registro único | `prueba_eventos_pygame.py` |
| AC-IG-017/018/019 | Guardados antiguos, carga opcional, lector de main, re-guardado de consola y bitácora | `prueba_guardado_grafico.py` |
| AC-IG-022 | Dependencia opcional, importación diferida y selección de modo antes de iniciar ventana/red | `prueba_cli_pygame.py` |

Las pruebas lógicas no requieren pantalla. Los escenarios de eventos se podrán
ejecutar con vídeo de pruebas; legibilidad, teclado/foco, cierre y
redimensionamiento requieren además revisión visual de escritorio. Los
contratos definitivos especificarán los casos y su preparación reproducible.

## Validación de investigación realizada

- Plantilla de plan resuelta mediante el script de spec-kit de esta rama.
- Leídos los puntos de integración, modelos, serializador y cliente HTTP.
- Consultadas fuentes oficiales de Pygame y metadatos de su wheel de referencia.
- Sonda temporal con el lector de sesión existente: acepta una clave opcional
  primitiva v6; al re-guardar desde consola la descarta y conserva el estado básico.
  No es una prueba de la futura memoria gráfica ni de compatibilidad completa.
- Elecciones D-IG-05/06/07 confirmadas por el usuario; investigación cerrada.
- Diseño disponible en [data-model.md](data-model.md), contratos de
  [interfaz](contracts/interfaz-grafica.md) y [recuerdos](contracts/recuerdos-v6.md),
  y [quickstart.md](quickstart.md). Revisión de coherencia documental completada.
- Implementación gráfica y pruebas nuevas: no iniciadas. Listo para
  `$speckit-tasks`; la planificación no acredita los escenarios futuros.
